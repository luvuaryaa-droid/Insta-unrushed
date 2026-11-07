#!/usr/bin/env python3
"""Vox-style collage explainer: one painting, pencil to paint, in 12 stages.

The 12 progress photos (aligned by prep_process.py into artworks/process/) sit on
one cut-out card. Each stage tears away the previous one, and the frame is dressed
in the explainer-collage style: newsprint grid paper, halftone cut-outs, torn colour
blocks, bold sans headers on highlighter strips, red-marker circles and arrows that
draw themselves on, magnifier call-outs, paint swatches, rubber stamps and a progress
filmstrip. It runs at 12 fps with a slight per-frame "boil" so it feels hand-moved.

Usage:  python3 make_vox_process.py                  # -> output/painting_process_vox.mp4
        python3 make_vox_process.py --preview 2 9 30  # stills at those seconds -> output/preview/
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import make_video as mv
from make_video import (CREAM, INK, MUSTARD, PAPER_WHITE, SAGE, Sprite, add_shadow, caveat, clamp,
                        ease_in, ease_out, paper_circle, paper_texture, star, tape_strip, text_strip,
                        torn_sheet, typewriter)

ROOT = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.join(ROOT, "artworks", "process")
FONTS = os.path.join(ROOT, "fonts")
OUT = os.path.join(ROOT, "output")

W, H = mv.W, mv.H
FPS, OUT_FPS = 12, 24

# Palette pulled from this painting
NEWS = (236, 230, 216)
GRID = (150, 170, 190)
COBALT = (62, 92, 168)
RED = (196, 44, 66)
MARKER = (222, 38, 38)
HILITE = (250, 214, 64)
ORANGE = (236, 160, 52)
LEAF_LIGHT = (172, 208, 84)
LEAF_DARK = (28, 112, 64)
TEAL = (52, 140, 140)

# Card geometry: the aligned 1600 px photo is shown at ART px on screen.
ART = 860
S = ART / 1600
CARD_C = (540, 880)
CARD_ROT = -1.2


def inter(size, black=True):
    return ImageFont.truetype(os.path.join(FONTS, "Inter-Black.otf" if black else "Inter-ExtraBold.otf"), size)


def to_screen(p):
    """1600-space point on the painting -> screen point (follows the card's tilt)."""
    x, y = (p[0] - 800) * S, (p[1] - 800) * S
    a = math.radians(CARD_ROT)
    return (CARD_C[0] + x * math.cos(a) + y * math.sin(a), CARD_C[1] - x * math.sin(a) + y * math.cos(a))


# --------------------------------------------------------------------------- collage pieces

def newsprint():
    bg = paper_texture(W, H, NEWS, 3, grain=5).astype(np.float32)
    g = np.zeros((H, W), np.float32)
    g[:, ::54] = 1
    g[::54, :] = 1
    bg = bg * (1 - 0.22 * g[..., None]) + np.array(GRID, np.float32) * 0.22 * g[..., None]
    return Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert("RGBA")


def halftone(im, width, cell=9, ink=INK, paper=NEWS, contrast=1.15):
    """Newspaper halftone: dot size follows darkness."""
    im = im.convert("L")
    h = int(im.height * width / im.width)
    g = np.asarray(im.resize((width // cell, h // cell), Image.BILINEAR), np.float32) / 255
    g = np.clip((g - 0.5) * contrast + 0.5, 0, 1) ** 0.6  # lift mids so dots stay open
    k = 4  # supersample for smooth dots
    out = Image.new("RGB", (width * k, h * k), paper)
    d = ImageDraw.Draw(out)
    for j in range(g.shape[0]):
        for i in range(g.shape[1]):
            r = math.sqrt(1 - g[j, i]) * cell * 0.62 * k
            if r > 0.6 * k:
                cx, cy = (i + 0.5 + 0.5 * (j % 2)) * cell * k, (j + 0.5) * cell * k
                d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ink)
    return out.resize((width, h), Image.LANCZOS)


def scissor_card(im, seed, border=18, tapes=(), shadow=True):
    """Photo on white paper with a scissor-cut edge, washi tape and a drop shadow."""
    rng = np.random.default_rng(seed)
    w, h = im.width + 2 * border, im.height + 2 * border
    tp = 44
    card = Image.new("RGBA", (w + 2 * tp, h + 2 * tp), (0, 0, 0, 0))
    j = lambda: rng.uniform(-3, 3)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon([(j() + 2, j() + 2), (w / 2, j() + 1), (w - 2 + j(), j() + 2),
                                  (w - 1 + j(), h / 2), (w - 2 + j(), h - 2 + j()), (w / 2, h - 1 + j()),
                                  (j() + 2, h - 2 + j()), (j() + 1, h / 2)], fill=255)
    paper = Image.fromarray(paper_texture(w, h, PAPER_WHITE, seed, 3)).convert("RGBA")
    paper.paste(im.convert("RGB"), (border, border))
    paper.putalpha(mask)
    card.alpha_composite(paper, (tp, tp))
    for (fx, fy, ang, col) in tapes:
        t = tape_strip(170, 50, col, seed + int(fx * 10)).rotate(ang + rng.uniform(-4, 4), Image.BICUBIC,
                                                                 expand=True)
        card.alpha_composite(t, (int(tp + fx * w - t.width / 2), int(tp + fy * h - t.height / 2)))
    return add_shadow(card) if shadow else card


def stamp(text, color=RED, size=92, seed=0):
    f = inter(size)
    tw = int(f.getlength(text))
    asc, desc = f.getmetrics()
    w, h = tw + 80, asc + desc + 50
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, w - 6, h - 6), 14, outline=color + (255,), width=9)
    d.text((40, 22 - desc * 0.2), text, font=f, fill=color + (255,))
    rng = np.random.default_rng(seed)
    a = np.asarray(im.getchannel("A"), np.float32)
    grunge = rng.random((h // 3 + 1, w // 3 + 1))
    grunge = np.array(Image.fromarray((grunge * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)) / 255
    a = a * np.clip(0.55 + grunge * 0.7, 0, 1) * 0.92
    im.putalpha(Image.fromarray(a.astype(np.uint8)))
    return im


def header_strip(text, size, paper, ink, seed, font=None):
    return text_strip(text, font or inter(size), paper=paper, ink=ink, seed=seed, pad=(40, 22), max_w=980)


def swatch(color, seed, size=104):
    return add_shadow(paper_circle(size, color, seed), 4, 6, 5, 0.32)


# --------------------------------------------------------------------------- marker strokes

def ellipse_pts(c, rx, ry, seed, turns=1.12, n=70):
    rng = np.random.default_rng(seed)
    a0 = rng.uniform(0, 2 * math.pi)
    wob = rng.uniform(-0.06, 0.06, 4)
    pts = []
    for i in range(n):
        f = i / (n - 1)
        a = a0 - 2 * math.pi * turns * f
        k = 1 + wob[0] * math.sin(a * 2 + wob[1] * 30) + 0.05 * f
        pts.append((c[0] + rx * k * math.cos(a), c[1] + ry * k * math.sin(a)))
    return pts


def arrow_pts(a, b, bend=0.25, n=40):
    """Curved shaft from a to b; head returned separately."""
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    dx, dy = b[0] - a[0], b[1] - a[1]
    cx, cy = mx - dy * bend, my + dx * bend
    pts = [((1 - f) ** 2 * a[0] + 2 * (1 - f) * f * cx + f * f * b[0],
            (1 - f) ** 2 * a[1] + 2 * (1 - f) * f * cy + f * f * b[1]) for f in np.linspace(0, 1, n)]
    ang = math.atan2(b[1] - pts[-4][1], b[0] - pts[-4][0])
    L = 40
    head = [(b[0] - L * math.cos(ang - 0.5), b[1] - L * math.sin(ang - 0.5)), b,
            (b[0] - L * math.cos(ang + 0.5), b[1] - L * math.sin(ang + 0.5))]
    return pts, head


def draw_stroke(d, pts, prog, width, color, frame, jitter=1.4):
    n = int(len(pts) * clamp(prog))
    if n < 2:
        return
    rng = np.random.default_rng(frame // 2 + 17)
    p = [(x + rng.uniform(-jitter, jitter), y + rng.uniform(-jitter, jitter)) for x, y in pts[:n]]
    d.line(p, fill=color, width=width, joint="curve")
    for q in (p[0], p[-1]):
        d.ellipse((q[0] - width / 2, q[1] - width / 2, q[0] + width / 2, q[1] + width / 2), fill=color)


class Mark:
    """A marker annotation drawn onto the painting (1600-space coords), written on over `dur`."""

    def __init__(self, kind, t0, t1, dur=0.5, **kw):
        self.kind, self.t0, self.t1, self.dur, self.kw = kind, t0, t1, dur, kw

    def draw(self, d, t, frame):
        if not (self.t0 <= t < self.t1):
            return
        p = (t - self.t0) / self.dur
        kw = self.kw
        col = kw.get("color", MARKER) + (240,)
        if self.kind == "circle":
            c = (kw["c"][0] * S, kw["c"][1] * S)
            pts = ellipse_pts(c, kw["r"][0] * S, kw["r"][1] * S, kw.get("seed", 1))
            draw_stroke(d, pts, p, 8, col, frame)
        elif self.kind == "arrow":
            a = (kw["a"][0] * S, kw["a"][1] * S)
            b = (kw["b"][0] * S, kw["b"][1] * S)
            shaft, head = arrow_pts(a, b, kw.get("bend", 0.25))
            draw_stroke(d, shaft, p * 1.4, 8, col, frame)
            if p * 1.4 > 1:
                draw_stroke(d, head, (p * 1.4 - 1) * 3, 8, col, frame)


# --------------------------------------------------------------------------- dynamic layers

class Layer:
    """Same interface as make_video.Sprite, but draws itself with a callback every frame."""

    def __init__(self, t0, t1, z, fn):
        self.t0, self.t1, self.z, self.fn = t0, t1, z, fn

    def active(self, t):
        return self.t0 <= t and (self.t1 is None or t < self.t1)

    def draw(self, canvas, t, frame):
        self.fn(canvas, t, frame)


def paste_center(canvas, im, x, y):
    px, py = int(round(x - im.width / 2)), int(round(y - im.height / 2))
    if px >= W or py >= H or px + im.width <= 0 or py + im.height <= 0:
        return
    canvas.alpha_composite(im, dest=(max(px, 0), max(py, 0)), source=(max(-px, 0), max(-py, 0)))


def torn_profile(n, seed, amp=14):
    rng = np.random.default_rng(seed)
    v = rng.normal(0, 1, n // 6 + 3)
    v = np.interp(np.arange(n), np.arange(len(v)) * 6, v)
    v += rng.normal(0, 0.35, n)
    return v * amp / 2


class PaintingCard:
    """The aligned stage photos on one scissor-cut card; stages tear in, marks draw on top."""

    def __init__(self, stages, schedule, marks, t_in, replay):
        self.arts = [np.asarray(s.resize((ART, ART), Image.LANCZOS)).astype(np.int16) for s in stages]
        self.schedule = schedule        # list of (t_start, stage_index, direction)
        self.marks = marks
        self.t_in = t_in
        self.replay = replay            # (t0, t1, step)
        self.border = 18
        base = scissor_card(Image.new("RGB", (ART, ART), PAPER_WHITE), 901, border=self.border, shadow=False)
        self.tp = 44
        self.base = base
        tapes = Image.new("RGBA", base.size, (0, 0, 0, 0))
        w = ART + 2 * self.border
        rng = np.random.default_rng(5)
        for fx, fy, ang, col in ((0.02, 0.02, -42, (226, 196, 120)), (0.98, 0.02, 40, (180, 210, 170)),
                                 (0.98, 0.98, -40, (226, 196, 120)), (0.02, 0.98, 42, (180, 210, 170))):
            tp = tape_strip(190, 54, col, int(fx * 100 + fy * 10)).rotate(ang + rng.uniform(-4, 4),
                                                                          Image.BICUBIC, expand=True)
            tapes.alpha_composite(tp, (int(self.tp + fx * w - tp.width / 2), int(self.tp + fy * w - tp.height / 2)))
        self.tapes = tapes
        self.profiles = [torn_profile(ART, 300 + i) for i in range(len(schedule))]
        yy, xx = np.mgrid[0:ART, 0:ART]
        self.xx, self.yy = xx.astype(np.float32), yy.astype(np.float32)
        sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
        sh.putalpha(base.getchannel("A").point(lambda v: int(v * 0.4)))
        self.shadow = Image.new("RGBA", (base.width + 80, base.height + 80), (0, 0, 0, 0))
        dark = Image.new("RGBA", base.size, (20, 16, 12, 0))
        dark.putalpha(sh.getchannel("A"))
        self.shadow.alpha_composite(dark, (48, 52))
        self.shadow = self.shadow.filter(ImageFilter.GaussianBlur(10))

    def art_at(self, t):
        r0, r1, step = self.replay
        if r0 <= t < r1:
            return self.arts[min(int((t - r0) / step), len(self.arts) - 1)]
        cur = 0
        for k, (ts, idx, direction) in enumerate(self.schedule):
            if t >= ts:
                cur = k
        ts, idx, direction = self.schedule[cur]
        new = self.arts[idx]
        if cur == 0:
            return new
        old = self.arts[self.schedule[cur - 1][1]]
        p = clamp((t - ts) / 0.5)
        if p >= 1:
            return new
        p = ease_out(p) if direction in ("l", "t") else ease_in(p) * 0.4 + ease_out(p) * 0.6
        prof = self.profiles[cur]
        if direction in ("l", "r"):
            coord = self.xx if direction == "l" else ART - 1 - self.xx
            edge = (-30 + p * (ART + 60)) + prof[:, None]
        else:
            coord = self.yy if direction == "t" else ART - 1 - self.yy
            edge = (-30 + p * (ART + 60)) + prof[None, :]
        d = coord - edge
        shade = 1 - 0.32 * np.clip(1 + d / 18, 0, 1)
        out = np.where((d < 0)[..., None], new * shade[..., None],
                       np.where((d < 9)[..., None], np.array([250, 247, 238], np.float32), old))
        return out

    def draw(self, canvas, t, frame):
        art = Image.fromarray(np.clip(self.art_at(t), 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(art, "RGBA")
        for m in self.marks:
            m.draw(d, t, frame)
        card = self.base.copy()
        card.paste(art, (self.tp + self.border, self.tp + self.border))
        card.alpha_composite(self.tapes)
        full = self.shadow.copy()
        full.alpha_composite(card, (40, 40))
        # entrance: drop in from above with a little spin
        p = clamp((t - self.t_in) / 0.5)
        k = ease_out(p)
        s = 1 + 0.3 * (1 - k)
        rot = CARD_ROT + 7 * (1 - k)
        rng = np.random.default_rng(frame // 2 + 4242)
        rot += rng.uniform(-0.25, 0.25)
        bx, by = rng.uniform(-1.2, 1.2), rng.uniform(-1.2, 1.2)
        if s != 1:
            full = full.resize((int(full.width * s), int(full.height * s)), Image.BILINEAR)
        full = full.rotate(rot, Image.BICUBIC, expand=True)
        if p < 1:
            full.putalpha(full.getchannel("A").point(lambda v: int(v * clamp(p * 3))))
        paste_center(canvas, full, CARD_C[0] + bx + 4, CARD_C[1] - 70 * (1 - k) + by + 6)


def magnifier(stage_img, c, radius=150, zoom=2.1, seed=0):
    """Round call-out showing a zoomed crop of the painting."""
    r_src = radius / (S * zoom)
    crop = stage_img.crop((int(c[0] - r_src), int(c[1] - r_src), int(c[0] + r_src), int(c[1] + r_src)))
    size = radius * 2
    crop = crop.resize((size, size), Image.LANCZOS)
    ring = 12
    full = size + 2 * ring
    im = Image.new("RGBA", (full, full), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, full - 1, full - 1), fill=PAPER_WHITE + (255,))
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse((0, 0, size - 1, size - 1), fill=255)
    im.paste(crop, (ring, ring), m)
    d.ellipse((ring - 2, ring - 2, full - ring + 1, full - ring + 1), outline=INK + (255,), width=4)
    return add_shadow(im, 6, 9, 8, 0.35)


class Connector:
    """Ink line + small ring linking a magnifier to its spot on the painting."""

    def __init__(self, a, b, r_ring, t0, dur=0.35):
        self.a, self.b, self.r, self.t0, self.dur = a, b, r_ring, t0, dur

    def __call__(self, canvas, t, frame):
        p = clamp((t - self.t0) / self.dur)
        if p <= 0:
            return
        d = ImageDraw.Draw(canvas)
        ax, ay = self.a
        bx, by = self.b
        ang = math.atan2(by - ay, bx - ax)
        sx, sy = bx - math.cos(ang) * self.r, by - math.sin(ang) * self.r
        ex, ey = ax + (sx - ax) * p, ay + (sy - ay) * p
        d.line((ax, ay, ex, ey), fill=INK + (255,), width=5)
        if p >= 1:
            d.ellipse((bx - self.r, by - self.r, bx + self.r, by + self.r), outline=INK + (255,), width=5)


class Filmstrip:
    """Progress strip of all 12 stages; done = colour, to come = faded, current = marker box."""

    def __init__(self, stages, schedule, y=1730):
        self.y = y
        self.th = 70
        self.gap = 10
        n = len(stages)
        self.x0 = (W - (n * self.th + (n - 1) * self.gap)) / 2
        self.thumbs, self.faded = [], []
        for s in stages:
            th = s.crop((200, 200, 1400, 1400)).resize((self.th, self.th), Image.LANCZOS).convert("RGBA")
            self.thumbs.append(th)
            g = th.convert("L").point(lambda v: int(v * 0.35 + 165)).convert("RGBA")
            self.faded.append(g)
        self.schedule = schedule
        strip_w = int(n * (self.th + self.gap) + 70)
        self.paper = add_shadow(torn_sheet(strip_w, self.th + 90, PAPER_WHITE, 77, sides="lr", amp=12, grain=4),
                                4, 6, 6, 0.3)
        self.font = typewriter(26)

    def __call__(self, canvas, t, frame):
        cur = max([i for i, (ts, idx, _) in enumerate(self.schedule) if t >= ts] or [0])
        cur_stage = self.schedule[cur][1]
        paste_center(canvas, self.paper, W / 2, self.y + 12)
        d = ImageDraw.Draw(canvas)
        for i in range(len(self.thumbs)):
            x = int(self.x0 + i * (self.th + self.gap))
            y = int(self.y - self.th / 2)
            canvas.alpha_composite(self.thumbs[i] if i <= cur_stage else self.faded[i], (x, y))
            num = f"{i + 1:02d}"
            d.text((x + self.th / 2 - self.font.getlength(num) / 2, y + self.th + 6), num, font=self.font,
                   fill=INK if i <= cur_stage else (150, 145, 135))
        x = self.x0 + cur_stage * (self.th + self.gap)
        rng = np.random.default_rng(frame // 2)
        j = lambda: rng.uniform(-2, 2)
        y = self.y - self.th / 2
        box = [(x - 7 + j(), y - 7 + j()), (x + self.th + 7 + j(), y - 7 + j()),
               (x + self.th + 7 + j(), y + self.th + 7 + j()), (x - 7 + j(), y + self.th + 7 + j()),
               (x - 7 + j(), y - 9 + j())]
        d.line(box, fill=MARKER + (255,), width=6, joint="curve")


# --------------------------------------------------------------------------- story

ITEMS = []
DURATION = 0.0
BG = None
GRAIN = None


def add(x):
    ITEMS.append(x)
    return x


def build():
    stages = [Image.open(os.path.join(PROC, f"stage_{i:02d}.jpg")).convert("RGB") for i in range(1, 13)]
    rng = np.random.default_rng(11)

    # ================= title (0 - 3.6)
    add(Sprite(add_shadow(torn_sheet(820, 1180, COBALT, 12, sides="tblr", amp=22), 8, 12, 12, 0.35), 0.0,
               (600, 930), rot=6, z=1, enter="slide_left", enter_dur=0.45, t1=3.9, boil=0.5))
    add(Sprite(add_shadow(torn_sheet(560, 420, HILITE, 13, sides="tblr", amp=20), 6, 8, 10, 0.3), 0.15,
               (300, 1400), rot=-8, z=2, enter="slide_down", enter_dur=0.45, t1=3.9, boil=0.5))
    ht = halftone(stages[11].crop((60, 60, 1540, 1540)), 640, cell=8, ink=COBALT, paper=PAPER_WHITE)
    add(Sprite(scissor_card(ht, 21, tapes=((0.5, 0.0, 3, (240, 200, 120)),)), 0.35, (560, 930), rot=4,
               z=3, enter="drop", enter_dur=0.45, t1=3.9, boil=1))
    add(Sprite(header_strip("FROM PENCIL", 104, INK, PAPER_WHITE, 31), 0.8, (470, 300), rot=-3, z=10,
               enter="slide_left", enter_dur=0.4, t1=3.9, boil=0.8))
    add(Sprite(header_strip("TO PAINT", 128, HILITE, INK, 32), 1.1, (600, 455), rot=2, z=11,
               enter="slide_right", enter_dur=0.4, t1=3.9, boil=0.8))
    add(Sprite(text_strip("one painting  /  12 stages", typewriter(52), seed=33, pad=(36, 20)), 1.6,
               (540, 1560), rot=-1.5, z=12, enter="pop", enter_dur=0.4, t1=3.9, boil=0.8))
    def title_circle(canvas, t, frame):
        d = ImageDraw.Draw(canvas)
        draw_stroke(d, ellipse_pts((560, 930), 430, 450, 8), (t - 2.0) / 0.55, 10, MARKER + (235,), frame)
        shaft, head = arrow_pts((900, 1720), (860, 1360), 0.35)
        p = (t - 2.4) / 0.4
        draw_stroke(d, shaft, p * 1.4, 10, MARKER + (235,), frame)
        if p * 1.4 > 1:
            draw_stroke(d, head, (p * 1.4 - 1) * 3, 10, MARKER + (235,), frame)
    add(Layer(2.0, 3.9, 13, title_circle))
    for i, (sx, sy, sc) in enumerate(((140, 620, 90), (960, 1290, 110), (150, 1700, 70))):
        add(Sprite(star(sc, (HILITE, RED, PAPER_WHITE)[i], 40 + i), 1.9 + i * 0.12, (sx, sy),
                   rot=rng.uniform(-20, 20), z=14, enter="pop", enter_dur=0.3, t1=3.9))

    # ================= the 12 stages
    T0 = 3.6
    # (duration, header, caption, wipe direction)
    plan = [
        (3.6, "THE SKETCH", "light pencil first: the plant + a patterned pot", None),
        (3.4, "THE FRAME", "mandalas up top, curly vines, two little birds", "l"),
        (2.2, "CLEAN LINES", "tidy up + darken what stays", "t"),
        (2.8, "TINY STARS", "fill the gaps with little crosses", "r"),
        (3.4, "THE LEAVES", "two greens. stripes go on top.", "l"),
        (3.4, "THE POT", "red, mustard + a creamy yellow", "t"),
        (3.0, "THE BIRDS", "two orange birds facing the pot", "r"),
        (3.4, "VINES + BLUE", "vines go in... and a first patch of blue", "l"),
        (3.4, "THE BLUE", "commit to the background", "t"),
        (3.2, "GOLD DOTS", "dot. dot. dot. (so many dots)", "r"),
        (3.2, "MANDALAS", "red + mustard for the mandalas", "l"),
        (4.6, "THE FINISH", "black ink lines, a heart border... and the dots? painted over.", "b"),
    ]
    schedule, starts = [], []
    t = T0
    for i, (dur, *_ , direction) in enumerate(plan):
        schedule.append((t, i, direction))
        starts.append(t)
        t += dur
    t_end = t
    replay = (t_end, t_end + 2.2, 2.2 / 12 * 0.92)
    t_fin = replay[1]

    def mk(i, kind, off, dur=0.5, **kw):
        return Mark(kind, starts[i] + off, starts[i + 1] if i + 1 < len(starts) else t_end, dur, **kw)

    marks = [
        mk(0, "circle", 1.0, c=(820, 1160), r=(330, 320), seed=1),
        mk(1, "circle", 1.0, c=(330, 1300), r=(200, 170), seed=2),
        mk(1, "circle", 1.4, c=(1290, 1300), r=(200, 170), seed=3),
        mk(1, "arrow", 1.9, a=(560, 560), b=(760, 330), bend=-0.3),
        mk(3, "circle", 0.8, 0.35, c=(440, 240), r=(55, 55), seed=4),
        mk(3, "circle", 1.05, 0.35, c=(1080, 350), r=(55, 55), seed=5),
        mk(3, "circle", 1.3, 0.35, c=(200, 480), r=(55, 55), seed=6),
        mk(3, "circle", 1.55, 0.35, c=(1300, 470), r=(55, 55), seed=7),
        mk(6, "circle", 0.9, c=(330, 1300), r=(220, 170), seed=8),
        mk(6, "circle", 1.2, c=(1290, 1300), r=(220, 170), seed=9),
        mk(7, "circle", 1.3, c=(1000, 260), r=(220, 150), seed=10),
        mk(9, "circle", 1.1, c=(330, 600), r=(240, 240), seed=11),
        mk(10, "arrow", 0.9, a=(560, 620), b=(330, 330), bend=0.3),
        mk(10, "arrow", 1.2, a=(1000, 620), b=(1260, 330), bend=-0.3),
        mk(11, "circle", 2.4, c=(330, 600), r=(240, 240), seed=12),
    ]
    card = PaintingCard(stages, schedule, marks, T0, replay)
    add(Layer(T0, t_fin + 0.6, 50, card.draw))

    # torn colour block behind the card, one per chapter
    blocks = [(0, (150, 176, 196), "left"), (4, (232, 190, 80), "right"), (8, (214, 96, 100), "left"),
              (11, (52, 120, 88), "down")]
    for bi, (si, col, wipe) in enumerate(blocks):
        blk = add_shadow(torn_sheet(1000, 1160, col, 60 + bi, sides="tblr", amp=26), 8, 12, 12, 0.35)
        add(Sprite(blk, starts[si] - (0.25 if si else 0), (CARD_C[0] + 24, CARD_C[1] + 30), rot=3 - 2 * bi,
                   z=20 + bi, enter="slide_" + wipe, enter_dur=0.5, t1=t_fin + 0.6, boil=0.4))

    # headers, captions
    for i, (dur, head, cap, _) in enumerate(plan):
        ts = starts[i]
        te = starts[i + 1] if i + 1 < len(plan) else t_end
        num = header_strip(f"STAGE {i + 1:02d}", 48, INK, PAPER_WHITE, 500 + i, font=inter(48, False))
        add(Sprite(num, ts + 0.05, (215, 165), rot=-3, z=200, enter="slide_left", enter_dur=0.35,
                   t1=te, leave="shrink", leave_dur=0.15, boil=0.8))
        add(Sprite(header_strip(head, 92, HILITE, INK, 520 + i), ts + 0.15, (540, 290),
                   rot=rng.uniform(-2.5, 2.5), z=201, enter="slide_right", enter_dur=0.4, t1=te, leave="shrink",
                   leave_dur=0.15, boil=0.8))
        add(Sprite(text_strip(cap, typewriter(44), seed=540 + i, max_w=880, pad=(34, 20)), ts + 0.55,
                   (540, 1490), rot=rng.uniform(-1.5, 1.5), z=202, enter="pop", enter_dur=0.35, t1=te,
                   leave="shrink", leave_dur=0.15, boil=0.8))

    # magnifier call-outs: (stage, 1600-space spot, bubble screen pos, delay)
    mags = [(2, (330, 1290), (900, 600), 0.6), (4, (1010, 560), (905, 560), 0.9),
            (5, (820, 1040), (190, 640), 0.9), (9, (330, 600), (880, 1240), 1.6),
            (10, (840, 210), (870, 1210), 1.6)]
    for si, spot, pos, dl in mags:
        ts = starts[si] + dl
        te = starts[si + 1] if si + 1 < len(starts) else t_end
        bub = magnifier(stages[si], spot, seed=si)
        target = to_screen(spot)
        add(Layer(ts, te, 300, Connector(pos, target, 150 / 2.1, ts)))
        add(Sprite(bub, ts + 0.25, pos, rot=rng.uniform(-4, 4), z=301, enter="pop", enter_dur=0.35, t1=te,
                   leave="shrink", leave_dur=0.15, boil=0.6))

    # paint swatches popping in along the card's bottom-left edge
    sw = {4: [LEAF_LIGHT, LEAF_DARK], 5: [RED, (230, 172, 46), (246, 232, 150)], 6: [ORANGE],
          7: [TEAL, COBALT], 8: [COBALT], 9: [(204, 160, 52)], 10: [RED, (240, 186, 40)]}
    for si, cols in sw.items():
        ts = starts[si] + 0.7
        te = starts[si + 1]
        for k, col in enumerate(cols):
            add(Sprite(swatch(col, 700 + si * 5 + k), ts + k * 0.14, (130 + k * 95, 1330 - (k % 2) * 18),
                       rot=0, z=310, enter="pop", enter_dur=0.3, t1=te, leave="shrink", leave_dur=0.15,
                       boil=0.8))
        lab = text_strip("palette", caveat(46), paper=CREAM, seed=760 + si, pad=(22, 10))
        add(Sprite(lab, ts + 0.1, (150, 1230), rot=-6, z=311, enter="pop", enter_dur=0.3, t1=te,
                   leave="shrink", leave_dur=0.15, boil=0.8))

    # stamps
    add(Sprite(stamp("UH OH.", MARKER, 84, 1), starts[7] + 1.9, (300, 640), rot=12, z=320, enter="drop",
               enter_dur=0.25, t1=starts[8], boil=0.6))
    add(Sprite(stamp("NO GOING BACK", RED, 82, 2), starts[8] + 1.3, (560, 1180), rot=-11, z=320,
               enter="drop", enter_dur=0.25, t1=starts[9], boil=0.6))
    add(Sprite(stamp("~150", INK, 76, 3), starts[9] + 2.1, (840, 1430), rot=8, z=320, enter="drop",
               enter_dur=0.25, t1=starts[10], boil=0.6))
    add(Sprite(stamp("PLOT TWIST", MARKER, 96, 4), starts[11] + 1.7, (560, 640), rot=-9, z=320,
               enter="drop", enter_dur=0.25, t1=t_end, boil=0.6))
    add(Sprite(text_strip("unpeel the tape!", caveat(64), paper=HILITE, seed=801, pad=(26, 12)),
               starts[11] + 0.6, (820, 1190), rot=6, z=321, enter="pop", enter_dur=0.3, t1=starts[11] + 1.7,
               leave="shrink", leave_dur=0.15, boil=0.8))

    fs = Filmstrip(stages, schedule)
    add(Layer(T0 + 0.3, t_end, 400, fs))

    # replay
    add(Sprite(header_strip("THE WHOLE THING", 84, HILITE, INK, 901), t_end, (540, 230), rot=-2, z=410,
               enter="slide_left", enter_dur=0.3, t1=t_fin, boil=0.8))
    add(Sprite(header_strip("IN 2 SECONDS", 84, INK, PAPER_WHITE, 902), t_end + 0.2, (560, 360), rot=2,
               z=411, enter="slide_right", enter_dur=0.3, t1=t_fin, boil=0.8))

    def replay_ticker(canvas, t, frame):
        i = min(int((t - replay[0]) / replay[2]), 11)
        im = header_strip(f"{i + 1:02d} / 12", 72, PAPER_WHITE, INK, 903 + i, font=typewriter(72))
        paste_center(canvas, im.rotate(-2, Image.BICUBIC, expand=True), 540, 1520)
    add(Layer(t_end + 0.1, t_fin, 412, replay_ticker))

    # ================= finale
    z = 1000
    sheet = torn_sheet(W + 60, H + 60, COBALT, 1001, sides="t", amp=30, grain=6)
    add(Sprite(add_shadow(sheet, 0, 0, 14, 0.45), t_fin - 0.45, (W / 2, H / 2), z=z, enter="slide_up",
               enter_dur=0.45, boil=0, tilt=False))
    grid_pos = [(200 + (i % 3) * 340, 520 + (i // 3) * 330) for i in range(12)]
    for i, pos in enumerate(grid_pos):
        th = stages[i].crop((120, 120, 1480, 1480)).resize((250, 250), Image.LANCZOS)
        c = scissor_card(th, 1010 + i, border=10)
        add(Sprite(c, t_fin + 0.05 + i * 0.07, pos, rot=rng.uniform(-6, 6), z=z + 2 + i, enter="drop",
                   enter_dur=0.25, boil=0.7))
        add(Sprite(text_strip(f"{i + 1:02d}", typewriter(34), seed=1030 + i, pad=(12, 6)),
                   t_fin + 0.2 + i * 0.07, (pos[0] - 95, pos[1] - 105), rot=rng.uniform(-8, 8), z=z + 20,
                   enter="pop", enter_dur=0.2, boil=0.7))
    big = scissor_card(stages[11].crop((40, 40, 1560, 1560)).resize((720, 720), Image.LANCZOS), 1050,
                       tapes=((0.5, 0.0, 2, (240, 200, 120)), (0.5, 1.0, -3, (180, 210, 170))))
    add(Sprite(big, t_fin + 2.3, (540, 1020), rot=-2, z=z + 40, enter="drop", enter_dur=0.45, boil=1))
    add(Sprite(header_strip("SLOW ART.", 128, HILITE, INK, 1060), t_fin + 2.8, (520, 290), rot=-3,
               z=z + 50, enter="slide_left", enter_dur=0.4, boil=0.8))
    add(Sprite(text_strip("one stage at a time.", caveat(84), paper=PAPER_WHITE, seed=1061, pad=(34, 14)),
               t_fin + 3.3, (560, 1550), rot=2, z=z + 51, enter="pop", enter_dur=0.4, boil=0.8))
    add(Sprite(text_strip("which stage is your favourite? 01-12", typewriter(40), paper=CREAM, seed=1062,
                          pad=(28, 16)), t_fin + 4.1, (540, 1730), rot=-1.5, z=z + 52, enter="slide_up",
               enter_dur=0.4, boil=0.8))
    for i, (sx, sy, sc, col) in enumerate(((120, 470, 100, HILITE), (970, 430, 120, RED),
                                           (110, 1420, 80, PAPER_WHITE), (975, 1440, 95, HILITE))):
        add(Sprite(star(sc, col, 1070 + i), t_fin + 3.6 + i * 0.1, (sx, sy), rot=rng.uniform(-20, 20),
                   z=z + 53, enter="pop", enter_dur=0.3, boil=0.8))
    return t_fin + 7.0


def setup():
    global DURATION, BG, GRAIN
    DURATION = build()
    ITEMS.sort(key=lambda s: s.z)
    BG = newsprint()
    rng = np.random.default_rng(99)
    yy, xx = np.mgrid[0:H, 0:W]
    vig = (1 - 0.2 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2).astype(np.float32)
    GRAIN = [(vig, rng.normal(0, 3.0, (H, W)).astype(np.float32)) for _ in range(3)]


def render_frame(frame):
    t = frame / FPS
    canvas = BG.copy()
    for s in ITEMS:
        if s.active(t):
            s.draw(canvas, t, frame)
    arr = np.asarray(canvas.convert("RGB")).astype(np.float32)
    vig, g = GRAIN[(frame // 2) % 3]
    arr = arr * vig[..., None] + g[..., None]
    return np.clip(arr, 0, 255).astype(np.uint8).tobytes()


def main():
    os.makedirs(OUT, exist_ok=True)
    setup()
    if "--preview" in sys.argv:
        pdir = os.path.join(OUT, "preview")
        os.makedirs(pdir, exist_ok=True)
        times = [float(a) for a in sys.argv[sys.argv.index("--preview") + 1:]]
        for ts in times or [2.8, 5.5, 9.5, 16.5, 30, 36, 41.5, 44, 51]:
            Image.frombytes("RGB", (W, H), render_frame(int(ts * FPS))).save(
                os.path.join(pdir, f"vox_{ts:05.1f}.jpg"), quality=88)
        print("duration", DURATION)
        return
    n = int(DURATION * FPS)
    out = os.path.join(OUT, "painting_process_vox.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-r", str(OUT_FPS), "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for i, buf in enumerate(pool.imap(render_frame, range(n), chunksize=2)):
            proc.stdin.write(buf)
            if i % 60 == 0:
                print(f"frame {i}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()
    Image.frombytes("RGB", (W, H), render_frame(int((DURATION - 1.0) * FPS))).save(
        os.path.join(OUT, "painting_process_vox_cover.jpg"), quality=92)
    print("wrote", out)


if __name__ == "__main__":
    main()
