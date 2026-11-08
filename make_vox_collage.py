#!/usr/bin/env python3
"""Shubh Deepawali / Happy Deepavali: an explainer-style paper collage animation made from cut-outs of the
finished diya card.

The diya, fish, lotuses and flower vines are cut out of the finished painting and get
white scissor-cut borders and hard paper shadows. They are layered over torn indigo
paper, a halftone sunburst and newsprint textures. The diya slams in as black-and-white
newsprint and pops into colour, the fish swim in, and the vines and flame sway. The only
text is the greeting ("Shubh Deepawali" by default), made from ransom-note letters. Everything moves at 12 fps with
a small per-frame jitter, so it feels hand-animated.

Usage:  python3 make_vox_collage.py                 # renders output/shubh_deepawali_collage.mp4
        python3 make_vox_collage.py --greeting Happy Deepavali   # any two-word greeting
        python3 make_vox_collage.py --cover           # just the reel cover (+ grid-crop preview)
        python3 make_vox_collage.py --cut           # re-cut the elements (needs opencv)
        python3 make_vox_collage.py --preview 1 3 6 # stills -> output/preview/
"""
import math
import os
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

from make_video import add_shadow, paper_texture, torn_sheet

ROOT = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.join(ROOT, "artworks", "diya_aligned", "aligned14.jpg")
CUTS = os.path.join(ROOT, "artworks", "diya_cutouts")
FONTS = os.path.join(ROOT, "fonts")
OUT = os.path.join(ROOT, "output")

W, H = 1080, 1920
FPS = 12            # stop-motion rate
OUT_FPS = 24
DURATION = 12.0

# Greeting: first word on a typewriter strip, second word as ransom-note letters
GREETING = ["Shubh", "Deepawali"]
if "--greeting" in sys.argv:
    GREETING = sys.argv[sys.argv.index("--greeting") + 1:sys.argv.index("--greeting") + 3]
SLUG = "_".join(w.lower() for w in GREETING)

PAPER = (238, 228, 206)
INDIGO = (36, 52, 120)
INDIGO_DARK = (20, 28, 70)
MARIGOLD = (242, 168, 52)
SAFFRON = (232, 120, 48)
TERRACOTTA = (190, 70, 52)
PINK = (232, 140, 132)
LEAF = (64, 150, 112)
CREAM = (250, 244, 228)
INK = (26, 24, 28)

# Element boxes in the 1000x1000 aligned final painting
PARTS = {
    "diya": (222, 205, 745, 730), "fish_l": (56, 665, 350, 895), "fish_r": (620, 675, 920, 905),
    "lotus": (285, 730, 615, 944), "vine_l": (78, 140, 270, 700), "vine_r": (695, 130, 935, 705),
    "lotus_top": (350, 45, 645, 175),
}
# Bits of neighbouring elements that touch the part in the painting
ERASE = {"fish_l": [(312, 812, 360, 900)], "lotus": [(280, 725, 335, 815), (585, 725, 620, 800)],
         "vine_l": [(235, 580, 280, 710)]}


# --------------------------------------------------------------------------- cutting (one-off)

def cut():
    """Separate each element from the blue background of the finished painting."""
    import cv2
    im = cv2.imread(FINAL)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    h, s = hsv[..., 0].astype(int), hsv[..., 1].astype(int)
    fg = (~((h >= 93) & (h <= 128) & (s > 60))).astype(np.uint8) * 255   # not blue = painted motif
    os.makedirs(CUTS, exist_ok=True)
    for name, (x0, y0, x1, y1) in PARTS.items():
        fgm = fg.copy()
        for ex0, ey0, ex1, ey1 in ERASE.get(name, []):
            fgm[ey0:ey1, ex0:ex1] = 0
        m = fgm[y0:y1, x0:x1].copy()
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(m)
        big = st[1:, cv2.CC_STAT_AREA].max()
        single = name in ("fish_l", "fish_r", "lotus", "lotus_top")
        keep = np.zeros_like(m)
        for k in range(1, n):
            if st[k, cv2.CC_STAT_AREA] > (big * 0.999 if single else big * 0.10):
                keep[lab == k] = 255
        inv = (keep == 0).astype(np.uint8)          # fill enclosed holes (e.g. blue inside the bowl)
        n2, lab2 = cv2.connectedComponents(inv)
        border = set(np.unique(np.concatenate([lab2[0], lab2[-1], lab2[:, 0], lab2[:, -1]])))
        for k in range(1, n2):
            if k not in border:
                keep[lab2 == k] = 255
        keep = cv2.morphologyEx(keep, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
        keep = cv2.GaussianBlur(cv2.dilate(keep, np.ones((3, 3), np.uint8)), (3, 3), 0)
        rgb = cv2.cvtColor(im[y0:y1, x0:x1], cv2.COLOR_BGR2RGB)
        Image.fromarray(np.dstack([rgb, keep]), "RGBA").save(os.path.join(CUTS, f"{name}.png"))
    print("cut-outs written to", CUTS)


# --------------------------------------------------------------------------- easing

def clamp(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def ease_out_back(x, s=1.7):
    if x <= 0:
        return 0.0
    x = clamp(x) - 1
    return x * x * ((s + 1) * x + s) + 1


def ease_out(x):
    return 1 - (1 - clamp(x)) ** 3


def ease_in_out(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


# --------------------------------------------------------------------------- textures

def halftone(w, h, color, spacing, rmin, rmax, direction=(0, 1), seed=0, angle=30):
    """Dots on a rotated grid whose radius ramps across the sheet (newsprint gradient)."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    diag = int(math.hypot(w, h))
    for gy in range(-diag, diag, spacing):
        for gx in range(-diag, diag, spacing):
            x = w / 2 + gx * ca - gy * sa
            y = h / 2 + gx * sa + gy * ca
            if -spacing < x < w + spacing and -spacing < y < h + spacing:
                f = clamp(((x / w - 0.5) * direction[0] + (y / h - 0.5) * direction[1]) + 0.5)
                r = rmin + (rmax - rmin) * f
                if r > 0.6:
                    d.ellipse((x - r, y - r, x + r, y + r), fill=color + (255,))
    return im


def newsprint(img):
    """Black-and-white newsprint version of an RGBA cut-out (keeps alpha)."""
    a = img.getchannel("A")
    g = ImageOps.autocontrast(img.convert("L"), cutoff=2)
    g = ImageEnhance.Contrast(g).enhance(1.5)
    arr = np.asarray(g).astype(np.float32)
    noise = np.random.default_rng(3).normal(0, 10, arr.shape)
    arr = np.clip(arr * 0.92 + 18 + noise, 0, 255).astype(np.uint8)
    warm = np.array([1.0, 0.97, 0.90], np.float32)          # slightly yellowed newsprint
    rgb = np.clip(arr[..., None].astype(np.float32) * warm, 0, 255).astype(np.uint8)
    out = Image.fromarray(rgb, "RGB").convert("RGBA")
    out.putalpha(a)
    return out


def sticker(img, border=12, seed=0, shadow=(10, 14)):
    """White scissor-cut border + hard-ish paper shadow around a cut-out."""
    pad = border + 4
    w, h = img.width + 2 * pad, img.height + 2 * pad
    a = Image.new("L", (w, h), 0)
    a.paste(img.getchannel("A"), (pad, pad))
    edge = a.filter(ImageFilter.MaxFilter(2 * border + 1))
    # slightly wobbly scissor cut: blur + threshold, then a bit of polygonal roughness
    edge = edge.filter(ImageFilter.GaussianBlur(3)).point(lambda v: 255 if v > 110 else 0)
    paper = Image.fromarray(paper_texture(w, h, CREAM, seed, 5)).convert("RGBA")
    paper.putalpha(edge)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(paper)
    out.alpha_composite(img, (pad, pad))
    return add_shadow(out, dx=shadow[0], dy=shadow[1], blur=5, opacity=0.45)


@lru_cache(None)
def cutout(name, scale):
    im = Image.open(os.path.join(CUTS, f"{name}.png")).convert("RGBA")
    return im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)


# --------------------------------------------------------------------------- assets (built once per process)

@lru_cache(None)
def assets():
    A = {}
    # background: warm paper + big pale halftone + fibres
    bg = Image.fromarray(paper_texture(W, H, PAPER, 11, 8)).convert("RGBA")
    bg.alpha_composite(halftone(W, H, (226, 196, 150), 26, 0, 9, (0.6, -0.8), angle=20))
    A["bg"] = bg

    # torn indigo panel with a darker halftone fade at the bottom
    pw, ph = 980, 1250
    panel = torn_sheet(pw, ph, INDIGO, 21, sides="tblr", amp=20, grain=9)
    ht = halftone(pw, ph, INDIGO_DARK, 18, 0, 8.5, (0, 1), angle=45)
    ht.putalpha(Image.fromarray(np.minimum(np.asarray(ht.getchannel("A")), np.asarray(panel.getchannel("A")))))
    panel.alpha_composite(ht)
    A["panel"] = add_shadow(panel, 12, 18, 10, 0.5)

    # second torn scrap: newsprint-grey strip peeking from behind the panel
    scrap = torn_sheet(1100, 300, (214, 208, 196), 31, sides="tb", amp=16, grain=10)
    scrap.alpha_composite(halftone(1100, 300, (150, 146, 140), 12, 0.5, 4, (1, 0), angle=15))
    A["scrap"] = add_shadow(scrap.rotate(8, Image.BICUBIC, expand=True), 6, 10, 8, 0.35)

    # halftone sunburst disc
    R = 360
    sb = Image.new("RGBA", (2 * R, 2 * R), (0, 0, 0, 0))
    d = ImageDraw.Draw(sb)
    n = 24
    for k in range(n):
        a0, a1 = 360 * k / n, 360 * (k + 1) / n
        d.pieslice((0, 0, 2 * R - 1, 2 * R - 1), a0, a1, fill=(MARIGOLD if k % 2 else SAFFRON) + (255,))
    dots = halftone(2 * R, 2 * R, (255, 214, 120), 16, 0.5, 6, (0, -1), angle=0)
    mask = Image.new("L", (2 * R, 2 * R), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 2 * R - 1, 2 * R - 1), fill=255)
    dots.putalpha(Image.fromarray(np.minimum(np.asarray(dots.getchannel("A")), np.asarray(mask)) // 2))
    sb.alpha_composite(dots)
    rim = Image.new("RGBA", (2 * R + 40, 2 * R + 40), (0, 0, 0, 0))
    rm = Image.new("L", rim.size, 0)
    rng = np.random.default_rng(5)
    pts = [(R + 20 + (R + 14 + rng.uniform(-6, 6)) * math.cos(t), R + 20 + (R + 14 + rng.uniform(-6, 6)) * math.sin(t))
           for t in np.linspace(0, 2 * math.pi, 140, endpoint=False)]
    ImageDraw.Draw(rm).polygon(pts, fill=255)
    rim.paste(Image.fromarray(paper_texture(*rim.size, CREAM, 6, 4)).convert("RGBA"), (0, 0), rm)
    A["sun_rim"] = add_shadow(rim, 10, 14, 8, 0.4)
    A["sun"] = sb

    # terracotta halftone blob (graphic accent behind the fish)
    A["blob"] = halftone(520, 520, TERRACOTTA, 20, 0, 9, (0.7, 0.7), angle=30)
    blob_mask = Image.new("L", (520, 520), 0)
    ImageDraw.Draw(blob_mask).ellipse((0, 0, 519, 519), fill=255)
    A["blob"].putalpha(Image.fromarray(np.minimum(np.asarray(A["blob"].getchannel("A")), np.asarray(blob_mask))))

    # cut-outs
    diya = cutout("diya", 1.18)
    A["diya"] = sticker(diya, 13, 41)
    A["diya_bw"] = sticker(newsprint(diya), 13, 41)
    # flame alone, for the flicker (bottom at the bowl's rim)
    fx0, fy0, fx1, fy1 = [int(v * 1.18) for v in (172, 0, 362, 292)]
    flame = diya.crop((fx0, fy0, fx1, fy1))
    fm = Image.new("L", flame.size, 0)
    ImageDraw.Draw(fm).ellipse((int(0.16 * flame.width), -40, int(0.84 * flame.width), flame.height + 30), fill=255)
    flame.putalpha(Image.fromarray(np.minimum(np.asarray(flame.getchannel("A")), np.asarray(fm.filter(ImageFilter.GaussianBlur(4))))))
    A["flame"] = flame
    A["flame_off"] = (fx0, fy0)
    A["fish_l"] = sticker(cutout("fish_l", 1.05), 11, 42)
    A["fish_r"] = sticker(cutout("fish_r", 1.05), 11, 43)
    A["lotus"] = sticker(cutout("lotus", 1.05), 11, 44)
    A["lotus_top"] = sticker(cutout("lotus_top", 1.3), 11, 45)
    A["vine_l"] = sticker(cutout("vine_l", 1.22), 10, 46)
    A["vine_r"] = sticker(cutout("vine_r", 1.22), 10, 47)

    # paper stars
    A["stars"] = []
    for k, col in enumerate([MARIGOLD, CREAM, PINK, MARIGOLD, CREAM, (255, 210, 110)]):
        s = 54 + 10 * (k % 3)
        st = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        c, pts = s / 2, []
        for j in range(8):
            ang = j * math.pi / 4 - math.pi / 2
            rr = s / 2 - 2 if j % 2 == 0 else s * 0.16
            pts.append((c + rr * math.cos(ang), c + rr * math.sin(ang)))
        ImageDraw.Draw(st).polygon(pts, fill=col + (255,))
        A["stars"].append(add_shadow(st, 3, 4, 2, 0.35))

    A["glow"] = radial_glow(300)
    A["letters"] = ransom_letters()
    A["happy"] = happy_strip()
    return A


def radial_glow(r):
    yy, xx = np.mgrid[0:2 * r, 0:2 * r].astype(np.float32)
    d = np.sqrt((xx - r) ** 2 + (yy - r) ** 2) / r
    a = np.clip(1 - d, 0, 1) ** 2
    arr = np.zeros((2 * r, 2 * r, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = 255, 214, 120
    arr[..., 3] = (a * 200).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def font(path, size):
    return ImageFont.truetype(path, size)


LETTER_FONTS = [
    os.path.join(FONTS, "PermanentMarker-Regular.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf",
    os.path.join(FONTS, "SpecialElite-Regular.ttf"),
]


def ransom_letters():
    """D E E P A V A L I, each on its own scrap of paper, ransom-note style."""
    rng = np.random.default_rng(77)
    papers = [(MARIGOLD, INK), (CREAM, TERRACOTTA), (TERRACOTTA, CREAM), (INK, MARIGOLD),
              (PINK, INK), (LEAF, CREAM), (CREAM, INDIGO), (SAFFRON, CREAM), (CREAM, INK)]
    out = []
    for k, ch in enumerate(GREETING[1].upper()):
        fpath = LETTER_FONTS[(k * 3 + 1) % len(LETTER_FONTS)]
        f = font(fpath, int(rng.uniform(80, 96)))
        bg, fg = papers[k % len(papers)]
        box = f.getbbox(ch)
        tw, th = box[2] - box[0], box[3] - box[1]
        w, h = int(max(tw + 26, 80)), int(th + 34 + rng.uniform(0, 12))
        tile = torn_sheet(w, h, bg, 300 + k, sides="tblr", amp=5, rim=False, grain=6)
        ImageDraw.Draw(tile).text(((w - tw) / 2 - box[0], (h - th) / 2 - box[1]), ch, font=f, fill=fg)
        rot = float(rng.uniform(-9, 9))
        out.append((add_shadow(tile.rotate(rot, Image.BICUBIC, expand=True), 4, 6, 3, 0.45),
                    float(rng.uniform(-10, 10))))
    return out


def happy_strip():
    f = font(os.path.join(FONTS, "SpecialElite-Regular.ttf"), 96)
    text = GREETING[0]
    box = f.getbbox(text)
    w, h = box[2] - box[0] + 90, box[3] - box[1] + 56
    strip = torn_sheet(w, h, CREAM, 401, sides="lr", amp=12, grain=6)
    ImageDraw.Draw(strip).text((45 - box[0], 28 - box[1]), text, font=f, fill=INK)
    return add_shadow(strip.rotate(-4, Image.BICUBIC, expand=True), 5, 8, 4, 0.4)


# --------------------------------------------------------------------------- drawing helpers

def put(canvas, img, cx, cy, rot=0.0, scale=1.0, alpha=1.0, anchor=(0.5, 0.5)):
    """Paste img so that its anchor point lands on (cx, cy), rotated about that point."""
    if alpha <= 0 or scale <= 0.01:
        return
    if scale != 1.0:
        img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.BICUBIC)
    ax, ay = img.width * anchor[0], img.height * anchor[1]
    if rot:
        # pad so the anchor sits at the centre, then rotate about the centre
        pw = int(2 * max(ax, img.width - ax)) + 2
        ph = int(2 * max(ay, img.height - ay)) + 2
        padded = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        padded.paste(img, (int(pw / 2 - ax), int(ph / 2 - ay)))
        img = padded.rotate(rot, Image.BICUBIC, expand=True)
        ax, ay = img.width / 2, img.height / 2
    if alpha < 1:
        img = img.copy()
        img.putalpha(img.getchannel("A").point(lambda v: int(v * alpha)))
    canvas.alpha_composite(img, (int(round(cx - ax)), int(round(cy - ay))))


def jitter(frame, key, amt=1.6, rot=0.35):
    """Stop-motion boil: a tiny random offset that changes every other frame."""
    r = np.random.default_rng(hash((frame // 2, key)) & 0xFFFFFFFF)
    return float(r.uniform(-amt, amt)), float(r.uniform(-amt, amt)), float(r.uniform(-rot, rot))


def scribble_underline(canvas, x0, x1, y, p, seed=9):
    """Hand-drawn highlighter zig-zag under the title, drawing on with progress p."""
    if p <= 0:
        return
    rng = np.random.default_rng(seed)
    pts = []
    n = 26
    for i in range(n + 1):
        f = i / n
        pts.append((x0 + (x1 - x0) * f + rng.uniform(-4, 4), y + (9 if i % 2 else -9) + rng.uniform(-3, 3)))
    k = max(2, int(len(pts) * clamp(p)))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(layer).line(pts[:k], fill=MARIGOLD + (230,), width=16, joint="curve")
    canvas.alpha_composite(layer)


# --------------------------------------------------------------------------- frame

STAR_POS = [(150, 330, 0.0), (930, 300, 1.3), (110, 1120, 2.1), (980, 1090, 0.7), (300, 560, 2.8),
            (800, 560, 1.9), (540, 1480, 3.3), (200, 1450, 0.4), (880, 1440, 2.5)]


def render(frame):
    t = frame / FPS
    A = assets()
    canvas = A["bg"].copy()

    # camera: slow push-in + drift (applied at the end)
    zoom = 1.0 + 0.035 * ease_in_out(t / DURATION)

    # grey newsprint scrap behind everything
    p = ease_out((t - 0.05) / 0.4)
    put(canvas, A["scrap"], W / 2 + 60 + (1 - p) * 900, 1500, alpha=1)

    # torn indigo panel slides up
    p = ease_out_back((t - 0.1) / 0.45, 1.2)
    jx, jy, jr = jitter(frame, "panel", 1.0, 0.15)
    put(canvas, A["panel"], W / 2 + jx, 870 + (1 - p) * 1400 + jy, rot=-1.5 + jr)

    # halftone blob accent
    p = ease_out_back((t - 0.5) / 0.4)
    put(canvas, A["blob"], 840, 1220, scale=p, alpha=0.85)

    # sunburst: pops in and turns slowly, in 12 fps steps
    p = ease_out_back((t - 0.4) / 0.45, 1.5)
    if p > 0:
        put(canvas, A["sun_rim"], W / 2, 790, scale=p)
        put(canvas, A["sun"], W / 2, 790, rot=-t * 9, scale=p)
        g = 0.55 + 0.25 * math.sin(t * 4.0)
        put(canvas, A["glow"], W / 2, 640, scale=1.4 * p, alpha=g * clamp((t - 1.4) / 0.4))

    # vines grow up from their base
    for key, x, side, t0 in (("vine_l", 175, -1, 1.0), ("vine_r", 905, 1, 1.1)):
        p = ease_out_back((t - t0) / 0.5, 1.3)
        if p > 0:
            jx, jy, jr = jitter(frame, key)
            sway = 2.6 * math.sin(t * 1.6 + (0 if side < 0 else 1.7))
            put(canvas, A[key], x + jx, 1270 + jy, rot=side * 70 * (1 - p) + sway + jr, anchor=(0.5, 0.97))

    # top lotus drops in from above
    p = ease_out_back((t - 1.3) / 0.45, 1.6)
    if p > 0:
        jx, jy, jr = jitter(frame, "lotus_top")
        put(canvas, A["lotus_top"], W / 2 + jx, 330 - (1 - p) * 500 + jy,
            rot=3 * math.sin(t * 1.2) + jr)

    # diya: slams in as newsprint, then pops into colour
    p = ease_out_back((t - 0.7) / 0.35, 2.0)
    if p > 0:
        jx, jy, jr = jitter(frame, "diya", 1.2, 0.25)
        sc = 1.6 - 0.6 * p
        colour = t >= 1.55
        img = A["diya"] if colour else A["diya_bw"]
        bounce = 0.04 * math.exp(-(t - 1.55) * 8) if colour else 0
        dx, dy = W / 2 + jx, 830 + jy + 4 * math.sin(t * 1.4)
        put(canvas, img, dx, dy, rot=jr, scale=sc + bounce)
        if colour:
            # flicker the flame (only ever grows, so the painted flame underneath stays hidden)
            fl = A["flame"]
            fs = 1.0 + 0.035 * (1 + math.sin(t * 9.0)) + 0.02 * (1 + math.sin(t * 23.0))
            S = sc + bounce
            ox, oy = A["flame_off"]
            # sticker adds a border pad (13+4) and add_shadow adds its own pad
            spad = 17 + 5 * 3 + max(10, 14)
            base_x = dx + (spad + ox + fl.width / 2 - A["diya"].width / 2) * S
            base_y = dy + (spad + oy + fl.height - A["diya"].height / 2) * S
            put(canvas, fl.resize((int(fl.width * S * fs ** 0.4), int(fl.height * S * fs)), Image.BICUBIC),
                base_x, base_y, rot=1.5 * math.sin(t * 5.3), anchor=(0.5, 1.0))
            # colour-pop flash burst
            fb = clamp(1 - (t - 1.55) / 0.35)
            if fb > 0:
                burst = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                bd = ImageDraw.Draw(burst)
                for k in range(14):
                    a = k * 2 * math.pi / 14
                    r0, r1 = 330 + 60 * (1 - fb), 420 + 90 * (1 - fb)
                    bd.line((dx + r0 * math.cos(a), dy + r0 * math.sin(a), dx + r1 * math.cos(a), dy + r1 * math.sin(a)),
                            fill=CREAM + (int(255 * fb),), width=12)
                canvas.alpha_composite(burst)

    # lotus pops at the bottom
    p = ease_out_back((t - 1.95) / 0.4, 2.2)
    if p > 0:
        jx, jy, jr = jitter(frame, "lotus")
        put(canvas, A["lotus"], W / 2 + jx, 1415 + jy, rot=jr, scale=p * (1 + 0.02 * math.sin(t * 2.0)),
            anchor=(0.5, 0.8))

    # fish swim in from the sides and bob
    for key, x, side, t0 in (("fish_l", 215, -1, 1.6), ("fish_r", 865, 1, 1.75)):
        p = ease_out((t - t0) / 0.6)
        if p > 0:
            jx, jy, jr = jitter(frame, key)
            tt = t - t0
            put(canvas, A[key], x + side * (1 - p) * 700 + jx,
                1320 + 14 * math.sin(tt * 2.4 + (0 if side < 0 else 1.2)) + 60 * (1 - p) * math.sin(p * 6) + jy,
                rot=-side * (5 * math.sin(tt * 2.4 + 0.6) + 18 * (1 - p)) + jr)

    # paper stars twinkle (pop in/out, never all at once)
    for k, (x, y, ph) in enumerate(STAR_POS):
        if t < 2.2 + 0.12 * k:
            continue
        s = math.sin((t - 2.2) * 1.8 + ph * 2.2)
        sc = 0.55 + 0.45 * max(0.0, s)
        pop = ease_out_back((t - 2.2 - 0.12 * k) / 0.3, 2.2)
        jx, jy, jr = jitter(frame, f"star{k}", 1.5, 4)
        put(canvas, A["stars"][k % len(A["stars"])], x + jx, y + jy, rot=t * 25 * (1 if k % 2 else -1) + jr,
            scale=sc * pop)

    # first word slides in on a strip, then the second word letter by letter
    p = ease_out_back((t - 2.5) / 0.4, 1.3)
    if p > 0:
        jx, jy, jr = jitter(frame, "happy")
        put(canvas, A["happy"], 330 - (1 - p) * 800 + jx, 1580 + jy, rot=jr)
    letters = A["letters"]
    widths = [im.width - 22 for im, _ in letters]
    total = sum(widths)
    x = W / 2 - total / 2
    for k, (im, dy) in enumerate(letters):
        t0 = 2.85 + 0.1 * k
        p = ease_out_back((t - t0) / 0.25, 2.4)
        cx = x + widths[k] / 2
        x += widths[k]
        if p <= 0:
            continue
        jx, jy, jr = jitter(frame, f"L{k}", 1.5, 1.2)
        hop = 10 * max(0.0, math.sin((t - 5.0) * 2.0 - k * 0.5)) if t > 5 else 0
        put(canvas, im, cx + jx, 1740 + dy + jy - hop, rot=jr, scale=p)
    scribble_underline(canvas, W / 2 - total / 2 + 10, W / 2 + total / 2 - 10, 1840, (t - 4.0) / 0.6)

    # camera + film finish
    img = canvas.convert("RGB")
    cw, ch = W / zoom, H / zoom
    jx, jy, _ = jitter(frame, "cam", 2.0, 0)
    x0, y0 = (W - cw) / 2 + jx, (H - ch) / 2 + jy
    img = img.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BICUBIC)
    arr = np.asarray(img).astype(np.float32)
    arr = arr * vignette()[..., None] + grain(frame // 2 % 4)[..., None]
    # occasional dust specks
    r = np.random.default_rng(frame)
    for _ in range(int(r.integers(0, 4))):
        sx, sy = int(r.uniform(0, W - 6)), int(r.uniform(0, H - 6))
        arr[sy:sy + int(r.integers(2, 5)), sx:sx + int(r.integers(2, 7))] *= 0.55
    return np.clip(arr, 0, 255).astype(np.uint8)


@lru_cache(None)
def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    return 1 - 0.22 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2


@lru_cache(None)
def grain(k):
    return np.random.default_rng(50 + k).normal(0, 5.0, (H, W)).astype(np.float32)


# --------------------------------------------------------------------------- reel cover

def render_cover():
    """Static cover: the whole collage plus the greeting, fitted inside the middle 3:4 area
    (y 240..1680) that Instagram shows on the profile grid."""
    A = assets()
    c = A["bg"].copy()
    put(c, A["scrap"], W / 2 + 60, 1470)
    put(c, A["panel"], W / 2, 800, rot=-1.5, scale=0.88)
    put(c, A["blob"], 850, 1120, scale=0.8, alpha=0.85)
    put(c, A["sun_rim"], W / 2, 715, scale=0.86)
    put(c, A["sun"], W / 2, 715, rot=-8, scale=0.86)
    put(c, A["glow"], W / 2, 580, scale=1.25, alpha=0.75)
    put(c, A["vine_l"], 205, 1160, rot=1.5, scale=0.86, anchor=(0.5, 0.97))
    put(c, A["vine_r"], 875, 1160, rot=-1.5, scale=0.86, anchor=(0.5, 0.97))
    put(c, A["lotus_top"], W / 2, 345, rot=-2, scale=0.88)
    put(c, A["diya"], W / 2, 745, scale=0.9)
    put(c, A["lotus"], W / 2, 1255, scale=0.88, anchor=(0.5, 0.8))
    put(c, A["fish_l"], 255, 1215, rot=3, scale=0.88)
    put(c, A["fish_r"], 825, 1215, rot=-3, scale=0.88)
    for k, (x, y, sc) in enumerate([(160, 360, 1.0), (925, 330, 0.8), (330, 520, 0.6), (760, 500, 0.9),
                                     (120, 1300, 0.7), (965, 1320, 0.9)]):
        put(c, A["stars"][k % len(A["stars"])], x, y, rot=15 * k, scale=sc)
    put(c, A["happy"], 330, 1425)
    letters = A["letters"]
    widths = [im.width - 22 for im, _ in letters]
    total = sum(widths)
    x = W / 2 - total / 2
    for k, (im, dy) in enumerate(letters):
        put(c, im, x + widths[k] / 2, 1555 + dy)
        x += widths[k]
    scribble_underline(c, W / 2 - total / 2 + 10, W / 2 + total / 2 - 10, 1642, 1.0)
    arr = np.asarray(c.convert("RGB")).astype(np.float32)
    arr = arr * vignette()[..., None] + grain(0)[..., None] * 0.6
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def render_frame(frame):
    return render(frame).tobytes()


def main():
    if "--cut" in sys.argv or not os.path.exists(os.path.join(CUTS, "diya.png")):
        cut()
        if "--cut" in sys.argv:
            return
    os.makedirs(OUT, exist_ok=True)
    if "--cover" in sys.argv:
        cov = render_cover()
        cov.save(os.path.join(OUT, f"{SLUG}_cover.jpg"), quality=94)
        cov.crop((0, 240, W, 1680)).save(os.path.join(OUT, f"{SLUG}_cover_grid_preview.jpg"), quality=90)
        print("wrote", os.path.join(OUT, f"{SLUG}_cover.jpg"))
        return
    if "--preview" in sys.argv:
        pdir = os.path.join(OUT, "preview")
        os.makedirs(pdir, exist_ok=True)
        times = [float(a) for a in sys.argv[sys.argv.index("--preview") + 1:]] or [0.5, 1.2, 1.8, 3.2, 6, 11]
        for ts in times:
            Image.fromarray(render(int(ts * FPS))).save(os.path.join(pdir, f"vox_t{ts:05.1f}.jpg"), quality=88)
        print("previews in", pdir)
        return
    n = int(DURATION * FPS)
    out = os.path.join(OUT, f"{SLUG}_collage.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-r", str(OUT_FPS), "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for i, buf in enumerate(pool.imap(render_frame, range(n), chunksize=2)):
            proc.stdin.write(buf)
            if i % 24 == 0:
                print(f"frame {i}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()
    render_cover().save(os.path.join(OUT, f"{SLUG}_cover.jpg"), quality=94)
    print("wrote", out, f"({DURATION:.1f} s)")


if __name__ == "__main__":
    main()
