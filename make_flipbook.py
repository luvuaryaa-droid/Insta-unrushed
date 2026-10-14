#!/usr/bin/env python3
"""Weekly sketchbook tour, 3D flip-book version.

An open sketchbook floats in a night street scene and flips through the week's
pages in 3D, with big white hand-lettered captions on top.

Usage:
  python3 make_flipbook.py                    # renders output/sketchbook_flipbook.mp4
  python3 make_flipbook.py --bg my_clip.mp4   # float the book over your own footage
  python3 make_flipbook.py --preview 3 20     # stills at the given seconds -> output/preview/
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageSequence

ROOT = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(ROOT, "artworks")
FONTS = os.path.join(ROOT, "fonts")
OUT = os.path.join(ROOT, "output")

W, H = 1080, 1920
FPS = 30
DURATION = 59.0
SS = 2                       # supersampling for the book layer
REGION = (0, 330, W, 1730)   # screen area the book can occupy (x0, y0, x1, y1)

PAGE_W, PAGE_H = 1.0, 1.04   # page size in world units
TEX_W, TEX_H = 760, 790      # page texture size
ALPHA = math.radians(14)     # open pages tilt toward the viewer (V shape)
STRIPS = 12                  # a turning page is drawn as curved strips
PAPER = (246, 243, 236)
INK = (30, 30, 34)
COVER = (22, 22, 24)
RIBBON = (226, 98, 42)


def font(name, size, variation=None):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    if variation:
        f.set_variation_by_name(variation)
    return f


def ease_io(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ease_out_back(x, s=1.4):
    x = min(max(x, 0.0), 1.0) - 1
    return x * x * ((s + 1) * x + s) + 1


# --------------------------------------------------------------------------- page textures

def load(name):
    return Image.open(os.path.join(ART, name)).convert("RGB")


def cover_crop(im, inset=0.045):
    """Trim the photo-frame border, then crop to the page aspect and resize."""
    w, h = im.size
    im = im.crop((int(w * inset), int(h * inset), int(w * (1 - inset)), int(h * (1 - inset))))
    w, h = im.size
    target = TEX_W / TEX_H
    if w / h > target:
        nw = int(h * target)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / target)
        im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return im.resize((TEX_W, TEX_H), Image.LANCZOS)


def paper_page(seed):
    rng = np.random.default_rng(seed)
    a = np.empty((TEX_H, TEX_W, 3), np.float32)
    a[:] = PAPER
    a += rng.normal(0, 2.2, (TEX_H, TEX_W))[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def text_page(lines, seed):
    page = paper_page(seed)
    d = ImageDraw.Draw(page)
    y = 150
    for text, size in lines:
        f = font("Caveat.ttf", size, "Bold")
        d.text(((TEX_W - f.getlength(text)) / 2, y), text, font=f, fill=INK)
        y += int(size * 1.15)
    return page


def finish(page, side):
    """Gutter shadow on the spine side; left pages are stored mirrored (spine at x=0)."""
    page = page.convert("RGB")
    if side == "L":
        page = ImageOps.mirror(page)
    g = np.ones(TEX_W, np.float32)
    n = int(TEX_W * 0.16)
    g[:n] = 0.78 + 0.22 * np.linspace(0, 1, n) ** 0.6
    a = np.asarray(page).astype(np.float32) * g[None, :, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def build_pages():
    can = load("spread_camera_can.jpg").crop((920, 175, 1680, 900))
    stripes = load("portraits_stripes.jpg")
    blue = load("blue_flowers_spread.jpg")
    bw, bh = blue.size
    blue = blue.crop((int(bw * 0.04), int(bh * 0.07), int(bw * 0.96), int(bh * 0.93)))
    bw = blue.width
    title = text_page([("sketchbook", 120), ("- oct 2026 -", 70), ("", 50), ("ink . markers", 64),
                       ("neon . collage", 64)], 1)
    outro = text_page([("next week:", 96), ("", 30), ("more pages,", 72), ("more colour,", 72),
                       ("more play.", 72)], 2)
    last = text_page([("", 200), ("see you", 96), ("next week", 96)], 3)
    cat = Image.open(os.path.join(ART, "cat_neon.gif"))
    cat_frames = [finish(cover_crop(f.convert("RGB"), 0.0), "L") for f in ImageSequence.Iterator(cat)]
    spreads = [
        (title, load("portrait_bob.jpg")),
        (load("flowers_vase.jpg"), load("flowers_mosaic.jpg")),
        (load("camera_polaroid.png"), can),
        (load("car_awning.jpg"), load("car_front.jpg")),
        (stripes.crop((72, 573, 1520, 2099)), stripes.crop((1520, 573, 3027, 2099))),
        (None, load("blue_flowers.jpg")),           # left page: animated neon cat
        (load("clock_collage.jpg"), load("toast_collage.jpg")),
        (blue.crop((0, 0, bw // 2, blue.height)), blue.crop((bw // 2, 0, bw, blue.height))),
        (outro, last),
    ]
    left, right = [], []
    for i, (l, r) in enumerate(spreads):
        crop = lambda im: im if im.size == (TEX_W, TEX_H) else cover_crop(im, 0.0 if i in (2, 4, 7) else 0.045)
        left.append(cat_frames if l is None else [finish(crop(l), "L")])
        right.append([finish(crop(r), "R")])
    return left, right


# --------------------------------------------------------------------------- 3D

def solve_perspective(dst, src):
    """Coefficients mapping output (dst) points to input (src) points for Image.transform."""
    A, b = [], []
    for (x, y), (X, Y) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -x * X, -y * X]); b.append(X)
        A.append([0, 0, 0, x, y, 1, -x * Y, -y * Y]); b.append(Y)
    return np.linalg.solve(np.array(A, float), np.array(b, float))


class Camera:
    def __init__(self, yaw, pitch, roll, scale, cx, cy):
        cy_, sy_ = math.cos(yaw), math.sin(yaw)
        cp, sp = math.cos(pitch), math.sin(pitch)
        cr, sr = math.cos(roll), math.sin(roll)
        ry = np.array([[cy_, 0, sy_], [0, 1, 0], [-sy_, 0, cy_]])
        rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
        rz = np.array([[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]])
        self.R = rz @ rx @ ry
        self.scale = scale
        self.cx, self.cy = cx, cy
        self.f, self.D = 1680.0 * SS, 3.4

    def project(self, pts):
        p = (np.asarray(pts, float) * self.scale) @ self.R.T
        z = self.D - p[:, 2]
        return np.stack([self.cx + self.f * p[:, 0] / z, self.cy - self.f * p[:, 1] / z], 1)

    def normal_light(self, normal):
        n = self.R @ np.asarray(normal, float)
        light = np.array([-0.35, 0.45, 1.0]); light /= np.linalg.norm(light)
        return abs(float(n @ light))


def signed_area(q):
    x, y = q[:, 0], q[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))


def draw_quad(canvas, tex, quad, tx0, tx1, shade):
    """Map the texture slice [tx0, tx1] onto a screen quad (TL, TR, BR, BL)."""
    x0, y0 = np.floor(quad.min(0)).astype(int) - 1
    x1, y1 = np.ceil(quad.max(0)).astype(int) + 1
    cw, ch = canvas.size
    if x1 <= 0 or y1 <= 0 or x0 >= cw or y0 >= ch or x1 - x0 < 2 or y1 - y0 < 2:
        return
    dst = quad - [x0, y0]
    src = [(tx0, 0), (tx1, 0), (tx1, TEX_H), (tx0, TEX_H)]
    try:
        coeffs = solve_perspective(dst, src)
    except np.linalg.LinAlgError:
        return
    img = tex.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, tuple(coeffs), Image.BICUBIC)
    if shade < 0.995:
        v = int(255 * shade)
        img = ImageChops.multiply(img, Image.new("RGBA", img.size, (v, v, min(255, v + 6), 255)))
    canvas.alpha_composite(img, (x0, y0))


def page_points(theta_fn, u0, u1, n):
    """3D strip corners for a page whose angle varies along its width."""
    us = np.linspace(u0, u1, n + 1)
    pts = [np.array([0.0, 0.0])]
    angles = []
    for i in range(n):
        phi = theta_fn(0.5 * (us[i] + us[i + 1]))
        angles.append(phi)
        du = us[i + 1] - us[i]
        pts.append(pts[-1] + du * np.array([math.cos(phi), math.sin(phi)]))
    return us, pts, angles


def strip_quads(us, pts, angles, overlap=0.004):
    hy = PAGE_H / 2
    out = []
    for i, phi in enumerate(angles):
        a = pts[i]
        b = pts[i + 1] + overlap * np.array([math.cos(phi), math.sin(phi)])
        quad3 = [(a[0], hy, a[1]), (b[0], hy, b[1]), (b[0], -hy, b[1]), (a[0], -hy, a[1])]
        out.append((quad3, us[i], min(PAGE_W, us[i + 1] + overlap), phi))
    return out


# --------------------------------------------------------------------------- timeline

# (leaf, start, direction, duration). Leaf j turns spread j into spread j+1.
FLIPS = [(0, 3.3, 1, 0.95), (1, 7.1, 1, 0.95), (2, 10.9, 1, 0.95), (3, 16.85, 1, 0.8), (4, 18.25, 1, 0.8)]
FLIPS += [(4 - k, 19.75 + k * 0.17, -1, 0.6) for k in range(5)]          # riffle back to the start
FLIPS += [(j, 29.75 + 3.0 * j, 1, 0.95) for j in range(8)]                # the tour proper

CAPTIONS = [
    (0.5, 3.3, "WEEKLY\nSKETCHBOOK\nTOUR"),
    (3.6, 7.1, "CREATING MAKES\nME HAPPIER"),
    (7.4, 10.9, "AND ONCE I'M IN\nTHE ZONE, IT GETS\nEASIER"),
    (11.2, 13.9, "IT'S A LOT LIKE\nTHE GYM"),
    (14.0, 16.8, "YOU AVOID IT.\nYOU'VE GOT\nEXCUSES."),
    (16.9, 18.2, "THEN ONE DAY..."),
    (18.3, 19.7, "2 DAYS..."),
    (19.75, 21.2, "10 DAYS..."),
    (21.3, 23.4, "...AND YOU'RE\nHOOKED."),
    (23.5, 26.9, "YOU MAKE YOUR\nWHOLE LIFE REVOLVE\nAROUND IT"),
    (27.0, 29.8, "THIS PAST WEEK?\nA LOT OF\nEXPERIMENTS"),
    (30.0, 32.8, "PAINT MARKERS\n+ INK"),
    (33.0, 35.8, "PEN + INK"),
    (36.0, 38.8, "BLACK + GREY\nMARKERS"),
    (39.0, 41.8, "MORE INK,\nMORE STRIPES"),
    (42.0, 44.8, "A LITTLE NEON"),
    (45.0, 47.8, "COLLAGE"),
    (48.0, 50.8, "PATTERN PLAY"),
    (51.0, 53.4, "HAD AN AMAZING\nTIME"),
    (53.5, 56.2, "HERE'S TO A LOT\nMORE CREATIVITY\nNEXT WEEK"),
    (56.6, 59.0, "SEE YOU\nNEXT WEEK"),
]
FADE_START, FADE_DUR = 55.9, 1.0
N_LEAVES = 8


def leaf_angles(t):
    """Angle per leaf: ALPHA = lying on the right stack, pi - ALPHA = on the left."""
    ang = [ALPHA] * N_LEAVES
    moving = {}
    for leaf, start, direction, dur in FLIPS:
        if t < start:
            continue
        p = ease_io((t - start) / dur)
        a0, a1 = (ALPHA, math.pi - ALPHA) if direction > 0 else (math.pi - ALPHA, ALPHA)
        ang[leaf] = a0 + (a1 - a0) * p
        if p < 1:
            moving[leaf] = direction
        else:
            moving.pop(leaf, None)
    return ang, moving


def camera_at(t):
    intro = ease_out_back(t / 1.1)
    yaw = math.radians(24 + 5 * math.sin(0.45 * t) + 45 * (1 - intro))
    # "revolve around it": a wider swing of the whole book
    if 23.4 < t < 27.2:
        yaw += math.radians(-38) * math.sin(math.pi * (t - 23.4) / 3.8)
    pitch = math.radians(12 + 2.5 * math.sin(0.33 * t + 1))
    roll = math.radians(-1.5 + 1.2 * math.sin(0.27 * t))
    scale = 0.55 + 0.45 * intro
    cx = (W / 2 - 10 + 6 * math.sin(0.5 * t) - REGION[0]) * SS
    cy = (1040 + 14 * math.sin(0.8 * t) - REGION[1]) * SS
    return Camera(yaw, pitch, roll, scale, cx, cy)


# --------------------------------------------------------------------------- book render

LEFT, RIGHT = None, None


def tex(pages, i, t):
    frames = pages[i]
    return frames[int(t / 0.17) % len(frames)] if len(frames) > 1 else frames[0]


def render_book(t):
    cam = camera_at(t)
    rw, rh = (REGION[2] - REGION[0]) * SS, (REGION[3] - REGION[1]) * SS
    canvas = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    ang, moving = leaf_angles(t)
    on_left = [j for j in range(N_LEAVES) if j not in moving and ang[j] > math.pi / 2]
    on_right = [j for j in range(N_LEAVES) if j not in moving and ang[j] <= math.pi / 2]
    hy = PAGE_H / 2

    def flat(theta, u0, u1, lift=0.0, y0=-hy, y1=hy):
        c, s = math.cos(theta), math.sin(theta)
        nx, nz = -s, c
        return np.array([(u0 * c + nx * lift, y1, u0 * s + nz * lift), (u1 * c + nx * lift, y1, u1 * s + nz * lift),
                         (u1 * c + nx * lift, y0, u1 * s + nz * lift), (u0 * c + nx * lift, y0, u0 * s + nz * lift)])

    # Hard cover, slightly larger than the pages, behind both stacks.
    m = 0.035
    for theta in (ALPHA, math.pi - ALPHA):
        q = cam.project(flat(theta, -0.01, PAGE_W + m, -0.03 - 0.008 * N_LEAVES, -hy - m, hy + m))
        d.polygon([tuple(p) for p in q], fill=COVER + (255,))

    # Page blocks: thickness grows with the number of leaves on that side.
    for theta, count in ((ALPHA, len(on_right) + 4), (math.pi - ALPHA, len(on_left) + 4)):
        for k in range(count, 0, -1):
            q = cam.project(flat(theta, 0, PAGE_W, -0.0075 * k))
            v = 214 - 3 * (k % 3)
            d.polygon([tuple(p) for p in q], fill=(v, v - 3, v - 9, 255))

    # Ribbon bookmark hanging from the bottom of the spine.
    sway = 0.04 * math.sin(1.3 * t)
    rib = [(0.0, -hy + 0.02, 0.01), (0.03 + sway, -hy - 0.18, 0.05), (0.07 + sway * 2, -hy - 0.36, 0.08)]
    rp = cam.project(rib)
    d.line([tuple(p) for p in rp], fill=RIBBON + (255,), width=int(16 * SS * cam.scale), joint="curve")

    # Static top pages.
    k_right = min(on_right) if on_right else N_LEAVES
    k_left = max(on_left) + 1 if on_left else 0
    shade_under = 1.0 - 0.14 * max([math.sin(ang[j]) for j in moving] or [0])
    for theta, page, side in ((ALPHA, tex(RIGHT, k_right, t), 1), (math.pi - ALPHA, tex(LEFT, k_left, t), -1)):
        q = cam.project(flat(theta, 0, PAGE_W))
        sh = (0.80 + 0.20 * cam.normal_light((-math.sin(theta), 0, math.cos(theta)))) * shade_under
        draw_quad(canvas, page, q, 0, TEX_W, sh)

    # Turning leaves, farthest from vertical first.
    ref_sign = signed_area(cam.project(flat(ALPHA, 0, PAGE_W)))
    for j in sorted(moving, key=lambda j: -abs(ang[j] - math.pi / 2)):
        theta, direction = ang[j], moving[j]
        bend = 0.55 * math.sin(theta) * direction

        def theta_fn(u, theta=theta, bend=bend):
            return min(math.pi - ALPHA + 0.05, max(ALPHA - 0.05, theta + bend * (u / PAGE_W) ** 1.6))

        us, pts, angles = page_points(theta_fn, 0, PAGE_W, STRIPS)
        front, back = tex(RIGHT, j, t), tex(LEFT, j + 1, t)
        for quad3, u0, u1, phi in strip_quads(us, pts, angles):
            q = cam.project(quad3)
            facing_front = signed_area(q) * ref_sign > 0
            sh = 0.66 + 0.34 * cam.normal_light((-math.sin(phi), 0, math.cos(phi)))
            draw_quad(canvas, front if facing_front else back, q, u0 / PAGE_W * TEX_W, u1 / PAGE_W * TEX_W, sh)

    return canvas.reduce(SS)


# --------------------------------------------------------------------------- scene

BG = None
TRUNK = None
FLAKES = None
FLAKE_SPRITES = None
CAPTION_IMGS = None
BG_VIDEO = None


def radial(size, color, power=2.0, alpha=255):
    yy, xx = np.mgrid[0:size, 0:size]
    r = np.hypot(xx - size / 2, yy - size / 2) / (size / 2)
    a = np.clip(1 - r, 0, 1) ** power * alpha
    im = np.zeros((size, size, 4), np.uint8)
    im[..., :3] = color
    im[..., 3] = a.astype(np.uint8)
    return Image.fromarray(im, "RGBA")


def build_background():
    """Out-of-focus snowy night street, a little larger than the frame for camera drift."""
    bw, bh = W + 80, H + 80
    rng = np.random.default_rng(5)
    yy = np.linspace(0, 1, bh)[:, None]
    horizon = 0.66
    sky = np.array([10, 14, 26]) + (np.array([44, 50, 66]) - [10, 14, 26]) * (yy / horizon) ** 1.6
    ground = np.array([46, 52, 66]) + (np.array([96, 102, 116]) - [46, 52, 66]) * ((yy - horizon) / (1 - horizon))
    base = np.zeros((bh, bw, 3), np.float32)
    for y in range(bh):
        base[y] = sky[y] if y / bh < horizon else ground[y]
    bg = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(bg)
    hy = int(bh * horizon)
    # distant buildings with a few lit windows
    x = -20
    while x < bw:
        w_ = int(rng.uniform(90, 220)); h_ = int(rng.uniform(120, 420))
        d.rectangle((x, hy - h_, x + w_, hy + 4), fill=(18, 21, 30, 255))
        for _ in range(int(rng.uniform(1, 6))):
            wx = x + rng.uniform(10, w_ - 24); wy = hy - rng.uniform(30, h_ - 20)
            d.rectangle((wx, wy, wx + 14, wy + 20), fill=(250, 196, 120, 255))
        x += w_ + int(rng.uniform(5, 40))
    # path converging to the horizon
    d.polygon([(bw * 0.48, hy), (bw * 0.52, hy), (bw * 0.8, bh), (bw * 0.2, bh)], fill=(92, 98, 112, 255))
    for k in (-1, 1):   # tyre tracks in the snow
        d.line([(bw * 0.5 + k * 6, hy), (bw * 0.5 + k * 190, bh)], fill=(70, 75, 88, 255), width=14)
    # trees in the distance
    for _ in range(14):
        tx = rng.uniform(0, bw); th = rng.uniform(140, 380)
        d.line([(tx, hy + 6), (tx + rng.uniform(-6, 6), hy - th)], fill=(14, 16, 22, 255), width=int(rng.uniform(4, 10)))
    bg = bg.filter(ImageFilter.GaussianBlur(14))
    # street lamps: posts, glows and light pools on the snow
    for lx, scale in ((150, 1.0), (bw * 0.78, 0.8), (bw * 0.42, 0.55), (bw * 0.6, 0.45)):
        top = hy - 520 * scale
        ImageDraw.Draw(bg).line([(lx, hy + 40 * scale), (lx, top)], fill=(12, 12, 16, 255), width=int(10 * scale))
        for size, alpha, power in ((int(900 * scale), 90, 2.2), (int(260 * scale), 210, 1.6), (int(70 * scale), 255, 1.0)):
            g = radial(size, (255, 186, 110), power, alpha)
            bg.alpha_composite(g, (int(lx - size / 2), int(top - size / 2)))
        pool = radial(int(700 * scale), (255, 196, 130), 1.8, 110).resize((int(700 * scale), int(220 * scale)))
        bg.alpha_composite(pool, (int(lx - pool.width / 2), int(hy + 40 * scale - pool.height / 2)))
    # haze on the horizon
    haze = np.zeros((bh, bw, 4), np.uint8)
    haze[..., :3] = (120, 128, 150)
    haze[..., 3] = (np.exp(-((np.arange(bh) - hy) / 160.0) ** 2) * 70).astype(np.uint8)[:, None]
    bg.alpha_composite(Image.fromarray(haze, "RGBA"))
    noise = rng.normal(0, 3, (bh, bw, 1))
    a = np.asarray(bg.convert("RGB")).astype(np.float32) + noise
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def build_trunk():
    """Foreground tree on the right, slightly out of focus, a bit of snow on the bark."""
    tw = 420
    im = Image.new("RGBA", (tw, H + 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(9)
    pts_l, pts_r = [], []
    for i in range(41):
        y = (H + 120) * (1 - i / 40)
        cx = 300 + 25 * math.sin(i / 7) + i * 0.8
        half = 92 - i * 1.1
        pts_l.append((cx - half, y)); pts_r.append((cx + half, y))
    d.polygon(pts_l + pts_r[::-1], fill=(16, 14, 13, 255))
    for (x0, y0), (x1, y1), w_ in (((250, 760), (20, 520), 26), ((270, 420), (60, 120), 18), ((150, 600), (-40, 610), 14),
                                   ((300, 300), (180, -40), 22)):
        d.line([(x0, y0), ((x0 + x1) / 2 + rng.uniform(-30, 30), (y0 + y1) / 2), (x1, y1)], fill=(16, 14, 13, 255),
               width=w_, joint="curve")
    for _ in range(260):   # bark streaks
        x = 230 + rng.uniform(0, 150); y = rng.uniform(0, H + 120)
        d.line([(x, y), (x + rng.uniform(-4, 4), y + rng.uniform(30, 90))], fill=(34, 30, 28, 255), width=2)
    for _ in range(40):    # snow catching on the left edge
        y = rng.uniform(300, H)
        ex = 215 + rng.uniform(0, 20)
        d.ellipse((ex, y, ex + rng.uniform(8, 18), y + rng.uniform(4, 14)),
                  fill=(205, 210, 222, 200))
    return im.filter(ImageFilter.GaussianBlur(3))


def build_snow():
    rng = np.random.default_rng(3)
    flakes = []
    for _ in range(170):
        depth = rng.uniform(0, 1) ** 1.5   # 0 = far, 1 = close to camera
        flakes.append((rng.uniform(0, W), rng.uniform(0, H), depth, rng.uniform(0, 6.28), rng.uniform(0.6, 1.4)))
    sprites = {}
    for k in range(6):
        size = int(6 + k * 7)
        s = radial(size * 2, (235, 240, 250), 1.2 + k * 0.25, 230 - k * 25)
        sprites[k] = s
    return flakes, sprites


def draw_snow(frame, t, near):
    for x0, y0, depth, ph, sp in FLAKES:
        if (depth > 0.75) != near:
            continue
        speed = 40 + 160 * depth
        y = (y0 + t * speed * sp) % (H + 60) - 30
        x = (x0 + 30 * math.sin(t * 0.7 * sp + ph) * (0.3 + depth)) % W
        k = min(5, int(depth * 6))
        s = FLAKE_SPRITES[k]
        frame.alpha_composite(s, (int(x - s.width / 2), int(y - s.height / 2)))


def build_captions():
    out = {}
    for t0, t1, text in CAPTIONS:
        lines = text.split("\n")
        size = 96
        while max(font("PermanentMarker-Regular.ttf", size).getlength(l) for l in lines) > 900:
            size -= 4
        f = font("PermanentMarker-Regular.ttf", size)
        lh = int(size * 1.08)
        tw = int(max(f.getlength(l) for l in lines)) + 80
        th = lh * len(lines) + 70
        layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for i, l in enumerate(lines):
            d.text(((tw - f.getlength(l)) / 2, 30 + i * lh), l, font=f, fill=(255, 255, 255, 255))
        shadow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        shadow.putalpha(layer.getchannel("A").point(lambda v: int(v * 0.55)))
        shadow = shadow.filter(ImageFilter.GaussianBlur(10))
        img = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        img.alpha_composite(shadow, (0, 6))
        img.alpha_composite(layer)
        out[(t0, t1)] = img
    return out


def draw_caption(frame, t):
    for (t0, t1), img in CAPTION_IMGS.items():
        if not t0 <= t < t1:
            continue
        p = min(1.0, (t - t0) / 0.25)
        q = min(1.0, (t1 - t) / 0.18)
        s = 0.86 + 0.14 * ease_out_back(p, 2.2)
        a = min(p, q)
        im = img.resize((int(img.width * s), int(img.height * s)), Image.BILINEAR) if s < 0.999 else img
        if a < 1:
            im = im.copy()
            im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
        cy = 330 if t0 < 56 else 960
        frame.alpha_composite(im, (int(W / 2 - im.width / 2), int(cy - im.height / 2)))


def setup():
    global LEFT, RIGHT, BG, TRUNK, FLAKES, FLAKE_SPRITES, CAPTION_IMGS
    LEFT, RIGHT = build_pages()
    CAPTION_IMGS = build_captions()
    if not BG_VIDEO:
        BG = build_background()
        TRUNK = build_trunk()
        FLAKES, FLAKE_SPRITES = build_snow()


def render_frame(i):
    t = i / FPS
    if BG_VIDEO:
        frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    else:
        ox = 40 + 22 * math.sin(0.31 * t)
        oy = 40 + 14 * math.sin(0.23 * t + 2)
        frame = BG.crop((int(ox), int(oy), int(ox) + W, int(oy) + H)).convert("RGBA")
        draw_snow(frame, t, near=False)
    frame.alpha_composite(render_book(t), (REGION[0], REGION[1]))
    if not BG_VIDEO:
        draw_snow(frame, t, near=True)
        frame.alpha_composite(TRUNK, (W - TRUNK.width + 70 + int(40 * math.sin(0.31 * t)), -60))
    fade = min(1.0, max(0.0, (t - FADE_START) / FADE_DUR))
    if fade > 0:
        frame.alpha_composite(Image.new("RGBA", (W, H), (6, 7, 10, int(215 * fade))))
    draw_caption(frame, t)
    if BG_VIDEO:
        return frame.tobytes()
    return frame.convert("RGB").tobytes()


def main():
    global BG_VIDEO
    if "--bg" in sys.argv:
        BG_VIDEO = sys.argv[sys.argv.index("--bg") + 1]
    os.makedirs(OUT, exist_ok=True)
    setup()
    if "--preview" in sys.argv:
        pdir = os.path.join(OUT, "preview")
        os.makedirs(pdir, exist_ok=True)
        times = [float(a) for a in sys.argv[sys.argv.index("--preview") + 1:]]
        for ts in times or [1.5, 3.8, 9, 17.3, 20.3, 22, 25, 34, 43, 46, 52, 57.5]:
            buf = render_frame(int(ts * FPS))
            Image.frombytes("RGBA" if BG_VIDEO else "RGB", (W, H), buf).convert("RGB").save(
                os.path.join(pdir, f"flip_{ts:05.1f}.jpg"), quality=88)
        return
    n = int(DURATION * FPS)
    out = os.path.join(OUT, "sketchbook_flipbook.mp4")
    enc = ["-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-t", str(DURATION), out]
    raw = ["-f", "rawvideo", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if BG_VIDEO:
        cmd = (["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", BG_VIDEO, "-pix_fmt", "rgba"] + raw +
               ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-filter_complex",
                f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}[bg];"
                "[bg][1:v]overlay=format=auto[v]", "-map", "[v]", "-map", "2:a"] + enc)
    else:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-pix_fmt", "rgb24"] + raw + [
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"] + enc
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for i, buf in enumerate(pool.imap(render_frame, range(n), chunksize=6)):
            proc.stdin.write(buf)
            if i % 150 == 0:
                print(f"frame {i}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()
    Image.frombytes("RGBA" if BG_VIDEO else "RGB", (W, H), render_frame(int(1.6 * FPS))).convert("RGB").save(
        os.path.join(OUT, "flipbook_cover.jpg"), quality=92)
    print("wrote", out)


if __name__ == "__main__":
    main()
