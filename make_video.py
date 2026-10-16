#!/usr/bin/env python3
"""Weekly sketchbook tour: a papercut stop-motion reel built from the week's artworks.

Every element (background sheets, artwork cut-outs, caption strips, tape, stars)
is a paper "sprite" that slides, drops or pops into place. The animation runs at
12 fps with a slight per-frame "boil" so it reads as hand-moved paper.

Usage:  python3 make_video.py            # renders output/sketchbook_tour.mp4
        python3 make_video.py --preview  # writes a few still frames to output/preview/
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageSequence

import filters

ROOT = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(ROOT, "artworks")
FONTS = os.path.join(ROOT, "fonts")
OUT = os.path.join(ROOT, "output")

W, H = 1080, 1920
FPS = 12          # stop-motion frame rate
OUT_FPS = 24      # each animation frame is shown twice

# Palette pulled from the paintings
MUSTARD = (226, 179, 66)
SAGE = (143, 160, 128)
TERRACOTTA = (200, 104, 76)
DUSTY_BLUE = (126, 154, 176)
CREAM = (242, 233, 216)
PINK = (222, 182, 176)
COBALT = (47, 79, 160)
CHARCOAL = (40, 40, 42)
CHARTREUSE = (196, 216, 52)
PAPER_WHITE = (251, 248, 240)
INK = (28, 28, 30)
RED_INK = (196, 58, 44)


# --------------------------------------------------------------------------- fonts

def caveat(size, weight="Bold"):
    f = ImageFont.truetype(os.path.join(FONTS, "Caveat.ttf"), size)
    f.set_variation_by_name(weight)
    return f


def marker(size):
    return ImageFont.truetype(os.path.join(FONTS, "PermanentMarker-Regular.ttf"), size)


def typewriter(size):
    return ImageFont.truetype(os.path.join(FONTS, "SpecialElite-Regular.ttf"), size)


# --------------------------------------------------------------------------- paper helpers

def paper_texture(w, h, color, seed, grain=7.0):
    """Flat colour with blotchy fibres and fine grain."""
    rng = np.random.default_rng(seed)
    base = np.empty((h, w, 3), np.float32)
    base[:] = color
    blot = rng.normal(0, 1, (h // 24 + 2, w // 24 + 2)).astype(np.float32)
    blot = np.array(Image.fromarray(blot).resize((w, h), Image.BICUBIC))
    fine = rng.normal(0, 1, (h, w)).astype(np.float32)
    shade = blot * grain * 0.7 + fine * grain * 0.55
    base += shade[..., None]
    return np.clip(base, 0, 255).astype(np.uint8)


def smooth_noise(n, rng, smooth=3):
    v = rng.random(n)
    if smooth > 1:
        k = np.ones(smooth) / smooth
        v = np.convolve(np.concatenate([v[-smooth:], v, v[:smooth]]), k, "same")[smooth:-smooth]
    return v


def edge_polygon(w, h, amp, seed, sides="tblr", step=7, inset=0.0):
    """Polygon around a w x h rectangle; torn sides wobble inward by up to `amp` px."""
    rng = np.random.default_rng(seed)
    pts = []
    segs = [("t", (0, 0), (w, 0), (0, 1)), ("r", (w, 0), (w, h), (-1, 0)),
            ("b", (w, h), (0, h), (0, -1)), ("l", (0, h), (0, 0), (1, 0))]
    for name, (x0, y0), (x1, y1), (nx, ny) in segs:
        length = math.hypot(x1 - x0, y1 - y0)
        n = max(2, int(length / step))
        torn = name in sides
        noise = smooth_noise(n, rng, 2) if torn else rng.random(n) * 0.15
        a = amp if torn else 2.0
        for i in range(n):
            f = i / n
            d = noise[i] * a + inset
            pts.append((x0 + (x1 - x0) * f + nx * d, y0 + (y1 - y0) * f + ny * d))
    return pts


def torn_sheet(w, h, color, seed, sides="tblr", amp=14, rim=True, grain=7.0):
    """Torn paper with a lighter fibrous rim on torn edges."""
    tex = Image.fromarray(paper_texture(w, h, color, seed, grain)).convert("RGBA")
    outer = Image.new("L", (w, h), 0)
    ImageDraw.Draw(outer).polygon(edge_polygon(w, h, amp, seed, sides), fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if rim and sides:
        inner = Image.new("L", (w, h), 0)
        ImageDraw.Draw(inner).polygon(edge_polygon(w, h, amp * 0.9, seed + 1, sides, inset=3), fill=255)
        inner = ImageChops.multiply(inner, outer)
        rim_col = tuple(int(c * 0.25 + 250 * 0.75) for c in color)
        rim_img = Image.new("RGBA", (w, h), rim_col + (255,))
        out.paste(rim_img, (0, 0), outer)
        out.paste(tex, (0, 0), inner)
    else:
        out.paste(tex, (0, 0), outer)
    return out


def add_shadow(img, dx=7, dy=11, blur=9, opacity=0.38):
    pad = blur * 3 + max(abs(dx), abs(dy))
    w, h = img.size
    canvas = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    a = img.getchannel("A").point(lambda v: int(v * opacity))
    sh = Image.new("RGBA", img.size, (20, 16, 12, 0))
    sh.putalpha(a)
    canvas.alpha_composite(sh, (pad + dx, pad + dy))
    canvas = canvas.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(img, (pad, pad))
    return canvas


def tape_strip(w, h, color, seed):
    rng = np.random.default_rng(seed)
    tex = Image.fromarray(paper_texture(w, h, color, seed, 4)).convert("RGBA")
    mask = Image.new("L", (w, h), 0)
    left = [(rng.uniform(0, 6) + (i % 2) * 4, h * i / 8) for i in range(9)]
    right = [(w - rng.uniform(0, 6) - (i % 2) * 4, h * i / 8) for i in range(9)]
    ImageDraw.Draw(mask).polygon(left + right[::-1], fill=205)
    tex.putalpha(mask)
    return tex


def load_art(name):
    im = Image.open(os.path.join(ART, name))
    return im.convert("RGB")


def fit(im, max_w, max_h):
    s = min(max_w / im.width, max_h / im.height)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)


def cutout(im, max_w, max_h, seed, border=16, tape=None, tape_color=None):
    """Art print with a scissor-cut white paper border, optional washi tape, and a shadow."""
    rng = np.random.default_rng(seed)
    art = fit(im, max_w - 2 * border, max_h - 2 * border)
    w, h = art.width + 2 * border, art.height + 2 * border
    tpad = 40 if tape else 0
    card = Image.new("RGBA", (w + 2 * tpad, h + 2 * tpad), (0, 0, 0, 0))
    mask = Image.new("L", (w, h), 0)
    j = lambda: rng.uniform(-3, 3)
    ImageDraw.Draw(mask).polygon([(j() + 2, j() + 2), (w / 2, j() + 1), (w - 2 + j(), j() + 2),
                                  (w - 1 + j(), h / 2), (w - 2 + j(), h - 2 + j()),
                                  (w / 2, h - 1 + j()), (j() + 2, h - 2 + j()), (j() + 1, h / 2)], fill=255)
    paper = Image.fromarray(paper_texture(w, h, PAPER_WHITE, seed, 3)).convert("RGBA")
    paper.paste(art, (border, border))
    paper.putalpha(mask)
    card.alpha_composite(paper, (tpad, tpad))
    tc = tape_color or (235, 214, 150)
    if tape == "top":
        t = tape_strip(int(w * 0.32) + 40, 54, tc, seed + 5).rotate(rng.uniform(-6, 6), Image.BICUBIC, expand=True)
        card.alpha_composite(t, (tpad + w // 2 - t.width // 2, tpad - t.height // 2 + 4))
    elif tape == "corners":
        for cx, cy, ang in ((tpad + 10, tpad + 10, 40), (tpad + w - 10, tpad + 10, -40)):
            t = tape_strip(150, 46, tc, seed + cx).rotate(ang + rng.uniform(-5, 5), Image.BICUBIC, expand=True)
            card.alpha_composite(t, (cx - t.width // 2, cy - t.height // 2))
    return add_shadow(card)


def wrap(text, font, max_w):
    if "\n" in text:
        return [l for part in text.split("\n") for l in wrap(part, font, max_w)]
    lines, cur = [], ""
    for word in text.split(" "):
        test = (cur + " " + word).strip()
        if font.getlength(test) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def text_strip(text, font, paper=PAPER_WHITE, ink=INK, seed=0, max_w=880, pad=(44, 26),
               sides="lr", shadow=True, align="center"):
    lines = wrap(text, font, max_w)
    asc, desc = font.getmetrics()
    lh = int((asc + desc) * 0.92)
    tw = int(max(font.getlength(l) for l in lines))
    w, h = tw + 2 * pad[0], lh * len(lines) + 2 * pad[1]
    sheet = torn_sheet(w, h, paper, seed, sides=sides, amp=12, grain=4)
    d = ImageDraw.Draw(sheet)
    for i, l in enumerate(lines):
        lw = font.getlength(l)
        x = pad[0] + (tw - lw) / 2 if align == "center" else pad[0]
        d.text((x, pad[1] + i * lh - desc * 0.15), l, font=font, fill=ink)
    return add_shadow(sheet, 5, 8, 7, 0.3) if shadow else sheet


def star(size, color, seed, points=5):
    rng = np.random.default_rng(seed)
    s = size
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    pts = []
    for i in range(points * 2):
        r = (s / 2 - 2) * (1 if i % 2 == 0 else 0.45) * rng.uniform(0.92, 1.05)
        a = math.pi * i / points - math.pi / 2
        pts.append((s / 2 + r * math.cos(a), s / 2 + r * math.sin(a)))
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    tex = Image.fromarray(paper_texture(s, s, color, seed, 5)).convert("RGBA")
    tex.putalpha(mask)
    return add_shadow(tex, 4, 6, 5, 0.3)


def paper_circle(size, color, seed):
    mask = Image.new("L", (size, size), 0)
    rng = np.random.default_rng(seed)
    pts = []
    for i in range(36):
        a = 2 * math.pi * i / 36
        r = size / 2 - 3 - rng.uniform(0, 3)
        pts.append((size / 2 + r * math.cos(a), size / 2 + r * math.sin(a)))
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    tex = Image.fromarray(paper_texture(size, size, color, seed, 5)).convert("RGBA")
    tex.putalpha(mask)
    return tex


def strike(w, seed, color=RED_INK, thick=13):
    rng = np.random.default_rng(seed)
    h = 60
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = [(10 + (w - 20) * i / 6, h / 2 + rng.uniform(-9, 9) + (i - 3) * -3) for i in range(7)]
    d.line(pts, fill=color + (235,), width=thick, joint="curve")
    for p in (pts[0], pts[-1]):
        d.ellipse((p[0] - thick / 2, p[1] - thick / 2, p[0] + thick / 2, p[1] + thick / 2), fill=color + (235,))
    return im


def square_thumb(im, size, inset=0.1):
    w, h = im.size
    s = min(w, h) * (1 - 2 * inset)
    l, t = (w - s) / 2, (h - s) / 2
    return im.crop((int(l), int(t), int(l + s), int(t + s))).resize((size, size), Image.LANCZOS)


# --------------------------------------------------------------------------- animation

def ease_out_back(x, s=1.6):
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def ease_out(x):
    return 1 - (1 - x) ** 3


def ease_in(x):
    return x ** 3


def clamp(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


class Sprite:
    _ids = 0

    def __init__(self, img, t0, pos, rot=0.0, z=0, enter="drop", enter_dur=0.5,
                 t1=None, leave=None, leave_dur=0.4, boil=1.0, path=None, reveal=None,
                 frames=None, frame_dur=None, tilt=True):
        Sprite._ids += 1
        self.id = Sprite._ids
        self.img = img
        self.t0, self.t1 = t0, t1
        self.pos, self.rot, self.z = pos, rot, z
        self.enter, self.enter_dur = enter, enter_dur
        self.leave, self.leave_dur = leave, leave_dur
        self.boil = boil
        self.path = path              # callable(t) -> (x, y, rot, scale)
        self.reveal = reveal          # (start, duration): wipe in from the left
        self.frames = frames          # animated sprite frames
        self.frame_dur = frame_dur
        self.tilt = tilt              # rotate a little while sliding in/out

    def active(self, t):
        return t >= self.t0 and (self.t1 is None or t < self.t1)

    def offscreen(self, direction, x, y):
        m = max(self.img.width, self.img.height)
        return {"left": (-m, y), "right": (W + m, y), "up": (x, -m), "down": (x, H + m)}[direction]

    def transform(self, t, frame):
        if self.path:
            x, y, r, s = self.path(t)
        else:
            x, y = self.pos
            r, s = self.rot, 1.0
        a = 1.0
        p = clamp((t - self.t0) / self.enter_dur) if self.enter_dur else 1.0
        e = self.enter
        if p < 1:
            if e == "drop":
                k = ease_out(p)
                s *= 1 + 0.35 * (1 - k)
                r += 8 * (1 - k)
                y -= 60 * (1 - k)
                a = clamp(p * 3)
            elif e == "pop":
                s *= max(0.01, ease_out_back(p))
            elif e.startswith("slide_"):
                ox, oy = self.offscreen(e[6:], x, y)
                k = ease_out(p)
                x, y = ox + (x - ox) * k, oy + (y - oy) * k
                if self.tilt:
                    r += (1 - k) * (6 if e in ("slide_left", "slide_up") else -6)
            elif e == "fade":
                a = p
        if self.leave and self.t1 is not None:
            q = clamp((t - (self.t1 - self.leave_dur)) / self.leave_dur)
            if q > 0:
                if self.leave == "shrink":
                    s *= max(0.01, 1 - ease_in(q))
                elif self.leave.startswith("slide_"):
                    ox, oy = self.offscreen(self.leave[6:], x, y)
                    k = ease_in(q)
                    x, y = x + (ox - x) * k, y + (oy - y) * k
                    if self.tilt:
                        r += k * 8
                elif self.leave == "fade":
                    a *= 1 - q
        if self.boil:
            rng = np.random.default_rng(self.id * 100003 + frame // 2)
            r += rng.uniform(-0.45, 0.45) * self.boil
            x += rng.uniform(-1.6, 1.6) * self.boil
            y += rng.uniform(-1.6, 1.6) * self.boil
        return x, y, r, s, a

    def image(self, t):
        if self.frames:
            i = int((t - self.t0) / self.frame_dur) % len(self.frames)
            return self.frames[i]
        if self.reveal:
            f = clamp((t - self.reveal[0]) / self.reveal[1])
            im = self.img.copy()
            cut = int(im.width * f)
            if cut < im.width:
                alpha = im.getchannel("A")
                ImageDraw.Draw(alpha).rectangle((cut, 0, im.width, im.height), fill=0)
                im.putalpha(alpha)
            return im
        return self.img

    def draw(self, canvas, t, frame):
        x, y, r, s, a = self.transform(t, frame)
        im = self.image(t)
        if s != 1.0:
            im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
        if abs(r) > 0.05:
            im = im.rotate(r, Image.BICUBIC, expand=True)
        if a < 1:
            im = im.copy()
            im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
        px, py = int(round(x - im.width / 2)), int(round(y - im.height / 2))
        if px >= W or py >= H or px + im.width <= 0 or py + im.height <= 0:
            return
        canvas.alpha_composite(im, dest=(max(px, 0), max(py, 0)),
                               source=(max(-px, 0), max(-py, 0)))


# --------------------------------------------------------------------------- story

SPRITES = []
SCENES = []   # (start time, end time) per scene, end = when next sheet fully covers it


def add(sprite):
    SPRITES.append(sprite)
    return sprite


def background(t, color, seed, from_dir, z, dur=0.55):
    """A full-bleed torn sheet that wipes over everything underneath."""
    edge = {"left": "r", "right": "l", "up": "b", "down": "t", None: ""}[from_dir]
    sheet = torn_sheet(W + 60, H + 60, color, seed, sides=edge, amp=26, grain=6)
    if from_dir:
        sheet = add_shadow(sheet, 0, 0, 14, 0.45)
    enter = "slide_" + from_dir if from_dir else "none"
    return add(Sprite(sheet, t, (W / 2, H / 2), z=z, enter=enter, enter_dur=dur if from_dir else 0,
                      boil=0, tilt=False))


def caption(text, t, y, z, size=84, seed=0, rot=None, paper=PAPER_WHITE, ink=INK, font=None,
            enter="pop", t1=None, leave=None, leave_dur=0.4, x=W / 2, max_w=860):
    f = font or caveat(size)
    img = text_strip(text, f, paper=paper, ink=ink, seed=seed, max_w=max_w)
    r = rot if rot is not None else np.random.default_rng(seed).uniform(-2.5, 2.5)
    return add(Sprite(img, t, (x, y), rot=r, z=z, enter=enter, enter_dur=0.45, t1=t1, leave=leave,
                      leave_dur=leave_dur, boil=0.8))


def build():
    arts = {n.split(".")[0]: load_art(n) for n in sorted(os.listdir(ART))}
    cat = Image.open(os.path.join(ART, "cat_neon.gif"))
    cat_frames_raw = [f.convert("RGB") for f in ImageSequence.Iterator(cat)]
    rng = np.random.default_rng(7)

    # ---------------- 0: title (0 - 4.5)
    z = 0
    background(0, MUSTARD, 11, None, z)
    for i, (col, yy, seed) in enumerate(((SAGE, 1500, 21), (TERRACOTTA, 1640, 22), (CREAM, 1780, 23))):
        hill = add_shadow(torn_sheet(W + 120, 600, col, seed, sides="t", amp=40), 0, -6, 10, 0.3)
        add(Sprite(hill, 0.1 + i * 0.25, (W / 2, yy + 300), z=z + 1 + i, enter="slide_down",
                   enter_dur=0.6, boil=0.4))
    add(Sprite(cutout(arts["toast_collage"], 430, 430, 31, tape="top"), 0.0, (250, 520), rot=-9, z=z + 5,
               enter="drop", enter_dur=0.4))
    add(Sprite(cutout(arts["cat_neon"], 400, 400, 32, tape="top", tape_color=(210, 230, 120)), 0.25,
               (830, 470), rot=7, z=z + 6, enter="drop", enter_dur=0.4))
    add(Sprite(cutout(arts["clock_collage"], 330, 330, 33, tape="top", tape_color=(230, 170, 190)), 0.5,
               (300, 1400), rot=-5, z=z + 7, enter="drop", enter_dur=0.4))
    add(Sprite(text_strip("SKETCHBOOK", marker(118), seed=41, sides="lr"), 0.9, (540, 860), rot=-3,
               z=z + 10, enter="slide_left", enter_dur=0.45))
    add(Sprite(text_strip("TOUR", marker(118), paper=COBALT, ink=PAPER_WHITE, seed=42), 1.25, (660, 1015),
               rot=2.5, z=z + 11, enter="slide_right", enter_dur=0.45))
    add(Sprite(text_strip("a week of experiments", caveat(70), paper=CREAM, seed=43), 1.7, (470, 1160),
               rot=-1.5, z=z + 12, enter="pop", enter_dur=0.4))
    for i, (sx, sy, sc, col) in enumerate(((150, 1010, 110, PAPER_WHITE), (930, 790, 90, TERRACOTTA),
                                           (915, 1180, 70, COBALT))):
        add(Sprite(star(sc, col, 50 + i), 2.0 + i * 0.15, (sx, sy), rot=rng.uniform(-20, 20), z=z + 13,
                   enter="pop", enter_dur=0.35))

    # ---------------- 1: happier / in the zone (4.5 - 9.5)
    t = 4.5
    z = 100
    background(t - 0.5, SAGE, 101, "right", z)
    add(Sprite(cutout(arts["portrait_bob"], 690, 760, 111, tape="top"), t + 0.1, (510, 760), rot=-3,
               z=z + 2, enter="drop"))
    add(Sprite(cutout(arts["flowers_vase"], 330, 330, 112, tape="corners", tape_color=(240, 200, 140)),
               t + 0.5, (850, 1120), rot=8, z=z + 3, enter="drop"))
    caption("creating makes me happier.", t + 0.9, 1390, z + 10, size=92, seed=113)
    caption("and once I'm in the zone...\nit gets easier.", t + 2.4, 1570, z + 11, size=72, seed=114,
            paper=CREAM, max_w=800)

    # ---------------- 2: like the gym / excuses (9.5 - 15)
    t = 9.5
    z = 200
    background(t - 0.5, PINK, 201, "down", z)
    caption("it's a lot like the gym.", t + 0.1, 330, z + 10, size=96, seed=211)
    caption("you avoid it. you've got excuses.", t + 0.8, 1520, z + 10, size=76, seed=212)
    excuses = [("too tired", 330, 700, -7), ("no time", 760, 640, 6), ("tomorrow!", 380, 980, 4),
               ("not inspired", 740, 1010, -5), ("it won't be good", 540, 1260, -2)]
    for i, (txt, ex, ey, er) in enumerate(excuses):
        im = text_strip(txt, typewriter(56), paper=PAPER_WHITE if i % 2 else CREAM, seed=220 + i,
                        sides="tblr", max_w=600)
        add(Sprite(im, t + 1.2 + i * 0.35, (ex, ey), rot=er, z=z + 3 + i, enter="pop", enter_dur=0.35))
        sw = int(im.width * 0.85)
        add(Sprite(strike(sw, 230 + i), t + 3.3 + i * 0.3, (ex, ey), rot=er + rng.uniform(-4, 4),
                   z=z + 8, enter="none", enter_dur=0, reveal=(t + 3.3 + i * 0.3, 0.25), boil=0.5))

    # ---------------- 3: day counter / hooked (15 - 21)
    t = 15.0
    z = 300
    background(t - 0.5, DUSTY_BLUE, 301, "left", z)
    cols, rows, box, gap = 5, 2, 164, 14
    cw, ch = cols * box + (cols + 1) * gap + 30, rows * (box + 46) + gap + 70
    card = torn_sheet(cw, ch, CREAM, 302, sides="", amp=0, grain=4)
    d = ImageDraw.Draw(card)
    f_num = caveat(40)
    ox, oy = 15 + gap, 50
    centers = []
    for i in range(10):
        c, rr = i % cols, i // cols
        bx, by = ox + c * (box + gap), oy + rr * (box + 46)
        d.rounded_rectangle((bx, by, bx + box, by + box), 6, outline=INK + (255,), width=3)
        d.text((bx + 6, by - 44), f"day {i + 1}", font=f_num, fill=INK)
        centers.append((bx + box / 2, by + box / 2))
    card = add_shadow(card)
    pad = (card.width - cw) / 2
    card_pos = (540, 940)
    add(Sprite(card, t + 0.1, card_pos, z=z + 2, enter="drop", boil=0.4))
    thumbs = ["portrait_bob", "flowers_vase", "camera_polaroid", "car_awning", "car_front",
              "flowers_mosaic", "portraits_stripes", "cat_neon", "clock_collage", "blue_flowers"]
    times = [1.2, 2.0, 2.6, 2.85, 3.05, 3.2, 3.35, 3.5, 3.65, 3.95]
    for i, (name, tt) in enumerate(zip(thumbs, times)):
        th = square_thumb(arts[name], box - 14)
        th = add_shadow(th.convert("RGBA"), 3, 4, 3, 0.3)
        cx = card_pos[0] - card.width / 2 + pad + centers[i][0]
        cy = card_pos[1] - card.height / 2 + pad + centers[i][1]
        add(Sprite(th, t + tt, (cx, cy), rot=rng.uniform(-4, 4), z=z + 3, enter="pop", enter_dur=0.3,
                   boil=0.6))
    caption("then one day...", t + 0.7, 360, z + 10, size=96, seed=311, t1=t + 2.0, leave="shrink",
            leave_dur=0.2)
    caption("2 days...", t + 2.0, 360, z + 11, size=96, seed=312, t1=t + 3.0, leave="shrink",
            leave_dur=0.2)
    caption("10 days...", t + 3.0, 360, z + 12, size=96, seed=313)
    add(Sprite(text_strip("...and you're hooked.", marker(84), paper=MUSTARD, seed=314), t + 4.3,
               (540, 1480), rot=-2.5, z=z + 13, enter="pop", enter_dur=0.45))

    # ---------------- 4: life revolves around it (21 - 26.5)
    t = 21.0
    z = 400
    background(t - 0.5, TERRACOTTA, 401, "up", z)
    cx, cy = 540, 960
    center = paper_circle(470, CREAM, 402)
    center = add_shadow(center)
    add(Sprite(center, t + 0.1, (cx, cy), z=z + 1, enter="pop", boil=0.3))
    add(Sprite(cutout(arts["spread_cars"], 400, 260, 403), t + 0.3, (cx, cy - 10), rot=-4, z=z + 2,
               enter="drop"))
    orbiters = ["portrait_bob", "cat_neon", "toast_collage", "car_front", "blue_flowers", "flowers_vase",
                "camera_polaroid", "clock_collage"]
    n = len(orbiters)
    t_orb = t + 0.6

    def make_path(k):
        base = 2 * math.pi * k / n

        def path(tt):
            grow = ease_out(clamp((tt - t_orb) / 0.8))
            ang = base + 0.55 * (tt - t_orb)
            return (cx + 400 * grow * math.cos(ang), cy + 560 * grow * math.sin(ang),
                    12 * math.sin(ang * 2 + k), 0.45 + 0.55 * grow)
        return path

    for k, name in enumerate(orbiters):
        add(Sprite(cutout(arts[name], 230, 230, 410 + k, border=10), t_orb, (cx, cy), z=z + 3,
                   enter="none", enter_dur=0, path=make_path(k), boil=0.6))
    caption("you make your whole life", t + 1.2, 300, z + 10, size=86, seed=421)
    add(Sprite(text_strip("revolve around it.", marker(82), paper=COBALT, ink=PAPER_WHITE, seed=422),
               t + 2.0, (540, 1640), rot=2, z=z + 11, enter="pop", enter_dur=0.45))

    # ---------------- 5: this past week = experiments (26.5 - 29.5)
    t = 26.5
    z = 500
    background(t - 0.5, CREAM, 501, "right", z)
    caption("this past week?", t + 0.1, 760, z + 2, size=100, seed=511, paper=PAPER_WHITE)
    add(Sprite(text_strip("a LOT of experiments", marker(70), paper=TERRACOTTA, ink=PAPER_WHITE, seed=512),
               t + 0.8, (540, 950), rot=-2, z=z + 3, enter="slide_left", enter_dur=0.4))
    add(Sprite(text_strip("ink · markers · neon · collage", caveat(70), paper=MUSTARD, seed=513), t + 1.4,
               (540, 1110), rot=1.5, z=z + 4, enter="pop"))
    for i, (sx, sy, sc, col) in enumerate(((200, 560, 120, MUSTARD), (880, 640, 90, COBALT),
                                           (870, 1300, 110, SAGE), (230, 1280, 80, TERRACOTTA))):
        add(Sprite(star(sc, col, 520 + i), t + 1.6 + i * 0.12, (sx, sy), rot=rng.uniform(-20, 20),
                   z=z + 5, enter="pop", enter_dur=0.3))

    # ---------------- 6..10: categories (29.5 - 49.5)
    cats = [
        ("INK", MUSTARD, INK, PAPER_WHITE, "left",
         [("portraits_stripes", 560, 740, (360, 830), -4), ("camera_polaroid", 400, 470, (770, 1270), 6)],
         "pen + ink, lots of hatching"),
        ("MARKERS", SAGE, PAPER_WHITE, INK, "right",
         [("car_awning", 640, 640, (430, 720), -5), ("car_front", 480, 520, (720, 1240), 5)],
         "vintage cars, black + grey"),
        ("NEON", CHARCOAL, INK, CHARTREUSE, "down",
         [("cat_neon", 760, 760, (540, 900), -3)],
         "a little neon never hurt"),
        ("COLLAGE", PINK, PAPER_WHITE, COBALT, "left",
         [("clock_collage", 560, 560, (400, 720), -6), ("toast_collage", 520, 520, (700, 1230), 5)],
         "paper scraps + paint"),
        ("PATTERN PLAY", DUSTY_BLUE, PAPER_WHITE, COBALT, "right",
         [("blue_flowers_spread", 960, 560, (540, 690), -2), ("flowers_mosaic", 470, 470, (380, 1210), 4),
          ("flowers_vase", 400, 400, (790, 1290), -6)],
         "dots, dashes + mosaics"),
    ]
    t = 29.5
    for ci, (label, bg, tag_ink, tag_paper, wipe, pieces, note) in enumerate(cats):
        z = 600 + ci * 100
        dur = 4.0
        background(t - 0.5, bg, 600 + ci, wipe, z)
        tag = text_strip(label, marker(104), paper=tag_paper, ink=tag_ink if label != "NEON" else INK,
                         seed=610 + ci)
        add(Sprite(tag, t + 0.05, (540, 260), rot=rng.uniform(-3, 3), z=z + 20, enter="slide_up",
                   enter_dur=0.4))
        for pi, (name, mw, mh, pos, rot) in enumerate(pieces):
            if name == "cat_neon":
                frames = [cutout(f, mw, mh, 650, tape="top", tape_color=(210, 230, 120))
                          for f in cat_frames_raw]
                add(Sprite(frames[0], t + 0.35, pos, rot=rot, z=z + 2, enter="drop", frames=frames,
                           frame_dur=0.17))
            else:
                add(Sprite(cutout(arts[name], mw, mh, 640 + ci * 10 + pi,
                                  tape="top" if pi % 2 == 0 else "corners"),
                           t + 0.35 + pi * 0.45, pos, rot=rot, z=z + 2 + pi, enter="drop"))
        caption(note, t + 1.4, 1600, z + 21, size=70, seed=660 + ci,
                paper=CREAM if bg != CREAM else PAPER_WHITE)
        t += dur

    # ---------------- 11: outro (49.5 - 56)
    z = 1200
    background(t - 0.5, MUSTARD, 1201, "down", z)
    pile = ["blue_flowers", "car_awning", "portrait_bob", "toast_collage", "flowers_mosaic",
            "camera_polaroid", "cat_neon", "clock_collage", "car_front", "portraits_stripes"]
    spots = [(260, 650), (800, 600), (540, 760), (230, 1050), (850, 1010), (560, 1080), (330, 1330),
             (780, 1330), (560, 520), (540, 1250)]
    for i, (name, pos) in enumerate(zip(pile, spots)):
        add(Sprite(cutout(arts[name], 330, 330, 1210 + i, border=12), t + 0.05 + i * 0.13, pos,
                   rot=rng.uniform(-14, 14), z=z + 2 + i, enter="drop", enter_dur=0.3))
    caption("had an amazing time.", t + 1.6, 300, z + 20, size=96, seed=1221)
    add(Sprite(text_strip("here's to a lot more creativity next week", marker(72), paper=COBALT,
                          ink=PAPER_WHITE, seed=1222, max_w=820), t + 2.4, (540, 1560), rot=-2,
               z=z + 21, enter="slide_up", enter_dur=0.45))
    for i, (sx, sy, sc, col) in enumerate(((140, 420, 100, PAPER_WHITE), (950, 380, 120, TERRACOTTA),
                                           (120, 1500, 80, PAPER_WHITE), (960, 1440, 90, SAGE))):
        add(Sprite(star(sc, col, 1230 + i), t + 3.0 + i * 0.12, (sx, sy), rot=rng.uniform(-20, 20),
                   z=z + 22, enter="pop", enter_dur=0.3))
    return t + 6.5


# --------------------------------------------------------------------------- render

DURATION = None
GRAIN = None
LOOK = None   # filters.Look from --filter / --lut, applied to every finished frame


def setup():
    global DURATION, GRAIN
    DURATION = build()
    SPRITES.sort(key=lambda s: s.z)
    # Cull sprites once a later full-screen sheet has fully covered them.
    sheets = [s for s in SPRITES if s.img.size[0] >= W and s.img.size[1] >= H]
    for s in SPRITES:
        later = [b.t0 + b.enter_dur for b in sheets if b.z > s.z]
        if later:
            end = min(later)
            s.t1 = end if s.t1 is None else min(s.t1, end)
    rng = np.random.default_rng(99)
    GRAIN = []
    yy, xx = np.mgrid[0:H, 0:W]
    vig = 1 - 0.18 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2
    for i in range(3):
        g = rng.normal(0, 2.5, (H, W)).astype(np.float32)
        GRAIN.append((vig.astype(np.float32), g))


def render_frame(frame):
    t = frame / FPS
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    for s in SPRITES:
        if s.active(t):
            s.draw(canvas, t, frame)
    arr = np.asarray(canvas.convert("RGB")).astype(np.float32)
    vig, g = GRAIN[(frame // 2) % 3]
    arr = arr * vig[..., None] + g[..., None]
    out = np.clip(arr, 0, 255).astype(np.uint8)
    if LOOK:
        out = LOOK.apply(out, frame)
    return out.tobytes()


def main():
    global LOOK
    LOOK = filters.from_argv()
    os.makedirs(OUT, exist_ok=True)
    setup()
    if "--preview" in sys.argv:
        pdir = os.path.join(OUT, "preview")
        os.makedirs(pdir, exist_ok=True)
        for ts in [float(a) for a in sys.argv[sys.argv.index("--preview") + 1:]] or [3, 8, 13.5, 19.8, 24, 28.5,
                                                                                     32, 36, 40, 44, 48, 55]:
            f = int(ts * FPS)
            Image.frombytes("RGB", (W, H), render_frame(f)).save(filters.with_suffix(os.path.join(pdir, f"t{ts:05.1f}.jpg"), LOOK),
                                                                 quality=88)
        return
    n = int(DURATION * FPS)
    out = filters.with_suffix(os.path.join(OUT, "sketchbook_tour.mp4"), LOOK)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-r", str(OUT_FPS), "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for i, buf in enumerate(pool.imap(render_frame, range(n), chunksize=4)):
            proc.stdin.write(buf)
            if i % 60 == 0:
                print(f"frame {i}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()
    cover = Image.frombytes("RGB", (W, H), render_frame(int(3.2 * FPS)))
    cover.save(filters.with_suffix(os.path.join(OUT, "cover.jpg"), LOOK), quality=92)
    print("wrote", out)


if __name__ == "__main__":
    main()
