#!/usr/bin/env python3
""""I Am an Ocean": a lyric reel set to the song, built from the artworks in artworks/ocean.

The idea: the song is about an artist who refuses to stay in one style, so the reel
dives through the sketchbook like a swimmer going deeper. It starts at the pale grey
surface with the black-and-white ink work ("You change too much / make familiar"),
floods into colour on the first big hit ("I paint, but my niche is me"), sinks on
"I won't be boxed up", and every chorus ("at every depth, a different me") cuts on
the beat through the different styles until they settle into a mosaic of all of them.

Karaoke-style lyrics are burned in, word by word, timed to the vocal.

Usage:  python3 make_ocean.py                    # renders output/i_am_an_ocean.mp4
        python3 make_ocean.py --preview 3 17 50  # stills at those seconds -> output/preview/
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(ROOT, "artworks", "ocean")
FONTS = os.path.join(ROOT, "fonts")
OUT = os.path.join(ROOT, "output")
SONG = os.path.join(ROOT, "music", "I_Am_an_Ocean.mp3")

W, H = 1080, 1920
FPS = 30
SONG_LEN = 87.6
TAIL = 2.4                      # silent end card after the song
DURATION = SONG_LEN + TAIL

BEAT0, BEAT = 0.065, 0.5495     # measured from the track (~109 bpm)
CARD_CY = 800                   # vertical centre of the artwork
LYRIC_CY = 1500                 # vertical centre of the lyric block

PAPER = (250, 246, 238)


def beat(k):
    return BEAT0 + k * BEAT


def beat_after(t):
    return beat(math.ceil((t - BEAT0) / BEAT - 1e-6))


# --------------------------------------------------------------------------- lyrics
# (line end, [(word, start), ...]); timings from a Whisper transcription of the track.
LYRICS = [
    (3.10, [("You", 0.0), ("change", 0.9), ("too", 1.7), ("much", 2.2)]),
    (7.04, [("Make", 4.7), ("familiar", 6.1)]),
    (12.66, [("So", 8.6), ("people", 10.0), ("know", 10.8), ("what", 11.6)]),
    (16.38, [("they", 12.7), ("can", 14.2), ("expect", 15.0), ("here", 15.6)]),
    (20.62, [("I", 17.0), ("paint,", 17.9), ("but", 18.7), ("my", 19.6), ("niche", 19.8), ("is", 20.1), ("me", 20.3)]),
    (25.22, [("And", 20.6), ("I", 21.9), ("evolve,", 22.3), ("I", 23.4), ("change", 24.3)]),
    (29.00, [("My", 25.2), ("reasons", 25.8), ("change", 26.5), ("as", 27.3), ("the", 27.7), ("seasons", 27.9), ("change", 28.7)]),
    (33.78, [("As", 30.2), ("the", 31.0), ("moon", 31.2), ("waxes", 31.6), ("and", 32.7), ("wanes", 33.1)]),
    (38.40, [("My", 35.5), ("art", 36.2), ("changes", 36.6), ("when", 37.2), ("I", 37.6), ("change", 37.8)]),
    (42.42, [("I", 39.6), ("was", 40.3), ("never", 40.6), ("meant", 40.9), ("to", 41.3), ("stay", 41.7), ("the", 42.0), ("same", 42.2)]),
    (47.06, [("Don't", 43.7), ("hate", 44.4), ("me", 44.7), ("'cause", 45.0), ("I", 45.3), ("don't", 45.5), ("fit", 46.0), ("your", 46.2), ("cup", 46.6)]),
    (51.46, [("I", 47.1), ("am", 48.1), ("an", 48.5), ("ocean,", 48.9), ("I", 49.6), ("won't", 50.0), ("be", 50.4), ("boxed", 50.5), ("up", 51.3)]),
    (55.90, [("Different", 53.4), ("depths,", 54.2), ("different", 55.0), ("views", 55.3)]),
    (60.28, [("Dive", 57.1), ("a", 58.1), ("little,", 58.3), ("find", 58.9), ("someone", 59.1), ("new", 59.7)]),
    (64.62, [("I", 60.9), ("am", 61.4), ("an", 61.8), ("ocean,", 62.1), ("wild", 62.9), ("and", 63.6), ("free", 64.1)]),
    (68.72, [("At", 64.6), ("every", 65.4), ("depth,", 66.0), ("a", 67.1), ("different", 67.6), ("me", 68.0)]),
    (73.50, [("I", 68.7), ("am", 70.1), ("an", 70.5), ("ocean,", 70.9), ("wild", 71.8), ("and", 72.4), ("free", 72.9)]),
    (77.50, [("At", 73.5), ("every", 74.2), ("depth,", 74.7), ("a", 75.9), ("different", 76.3), ("me", 76.8)]),
    (82.20, [("I", 77.5), ("am", 78.9), ("an", 79.3), ("ocean,", 79.7), ("wild", 80.6), ("and", 81.2), ("free", 81.7)]),
    (86.60, [("At", 82.2), ("every", 83.0), ("depth,", 83.6), ("a", 84.4), ("different", 85.2), ("me", 85.7)]),
]

# --------------------------------------------------------------------------- artworks
# name -> crop box as fractions of the photo (removes phone borders, desk, bedsheet)
ARTWORKS = {
    "birds": ("ink_birds_spread.jpg", (0.015, 0.0, 0.998, 0.925)),
    "fish": ("chartreuse_fish.jpg", (0.047, 0.044, 0.953, 0.946)),
    "inkflower": ("ink_flower_blue.jpg", (0.065, 0.065, 0.935, 0.924)),
    "man": ("pencil_portrait_man.jpg", (0.025, 0.016, 0.975, 0.982)),
    "dragonflies": ("ink_dragonflies.jpg", (0.102, 0.075, 0.925, 0.925)),
    "moka": ("charcoal_moka_pot.jpg", (0.045, 0.033, 0.965, 0.97)),
    "woman": ("mosaic_woman_flower.jpg", (0.042, 0.036, 0.978, 0.975)),
    "winter": ("winter_cozy_things.jpg", (0.045, 0.042, 0.955, 0.972)),
    "fireplace": ("fireplace_cat.jpg", (0.025, 0.025, 0.975, 0.975)),
    "self": ("mosaic_self_portrait_hibiscus.jpg", (0.08, 0.068, 0.92, 0.93)),
    "blueflowers": ("blue_flowers_canvas.jpg", (0.048, 0.046, 0.954, 0.982)),
    "garlic": ("madhubani_garlic.jpg", (0.046, 0.235, 0.96, 0.795)),
    "diya": ("madhubani_diya.webp", (0.067, 0.15, 0.91, 0.79)),
    "scooter": ("madhubani_scooter.jpg", (0.05, 0.118, 0.95, 0.795)),
    "architecture": ("ink_architecture.jpg", (0.053, 0.07, 0.99, 0.93)),
    "nook": ("reading_nook.jpg", (0.05, 0.065, 0.96, 0.95)),
}

# colour of the word being sung, picked from each painting
ACCENT = {
    "birds": (236, 236, 236), "dragonflies": (236, 236, 236), "inkflower": (190, 222, 240),
    "man": (236, 236, 236), "self": (255, 112, 136), "moka": (240, 240, 240),
    "fish": (214, 238, 70), "winter": (255, 176, 128), "fireplace": (255, 202, 70),
    "blueflowers": (255, 214, 72), "woman": (255, 150, 118), "garlic": (255, 220, 64),
    "diya": (255, 184, 88), "architecture": (246, 206, 160), "nook": (124, 232, 214),
    "scooter": (255, 160, 170), "grid": (124, 236, 236),
}

# --------------------------------------------------------------------------- story
# (art, start, end, entrance, exit, extra)
SCENES = [
    ("birds", -0.2, 4.6, "rise", "drift", {"pan": True}),
    ("dragonflies", 4.6, 8.6, "rise", "drift", {}),
    ("inkflower", 8.6, 12.6, "rise", "drift", {}),
    ("man", 12.6, 16.3, "rise", "drop", {}),
    ("self", 16.45, 20.6, "splash", "drift", {}),            # the hit: colour floods in
    ("moka", 20.6, 23.3, "rise", "drift", {}),
    ("fish", 23.3, 25.2, "rise", "drift", {}),               # "I evolve, I change"
    ("winter", 25.2, 30.2, "rise", "drift", {}),             # seasons
    ("fireplace", 30.2, 35.4, "rise", "drift", {"moon": True}),
    ("blueflowers", 35.4, 39.5, "rise", "drift", {}),
    ("woman", 39.5, 43.6, "rise", "drift", {}),
    ("garlic", 43.6, 47.0, "rise", "drift", {"box": True}),  # "don't fit your cup"
    ("diya", 47.0, 51.6, "splash", "sink", {"box": True}),   # "I won't be boxed up" -> dive
    ("architecture", 53.25, 57.0, "tilt", "drift", {}),      # "different views"
    ("nook", 57.0, 60.85, "rise", "drift", {}),
    ("scooter", 60.95, beat(118), "splash", "cut", {}),      # chorus 1
]
CHORUS_CUTS = ["fish", "dragonflies", "moka", "woman", "fireplace", "inkflower",
               "blueflowers", "man", "winter", "garlic", "architecture", "nook"]
for i, name in enumerate(CHORUS_CUTS):
    SCENES.append((name, beat(118 + 2 * i), beat(120 + 2 * i), "cut", "cut", {"chorus": True}))
GRID_START = beat(141)                       # 77.54: the mosaic of every style
GRID_ORDER = ["woman", "birds", "fireplace", "garlic",
              "inkflower", "self", "scooter", "dragonflies",
              "nook", "blueflowers", "man", "fish",
              "diya", "moka", "architecture", "winter"]
GRID_POP = [5, 0, 10, 15, 3, 12, 6, 9, 1, 14, 4, 11, 7, 2, 13, 8]   # order tiles appear
ZOOM_START, ZOOM_END = 84.35, 85.55          # the self-portrait comes forward: "a different me"
END_CARD = 86.7

RIPPLES = [16.45, 48.9, 60.95, GRID_START]
DIVE = (51.0, 53.4)


# --------------------------------------------------------------------------- helpers

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out_back(x, s=1.7):
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_col(a, b, t):
    return tuple(lerp(x, y, t) for x, y in zip(a, b))


def keyframes(kf, t):
    if t <= kf[0][0]:
        return np.asarray(kf[0][1], float)
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            u = ease_in_out((t - t0) / (t1 - t0))
            return np.asarray(v0, float) + (np.asarray(v1, float) - np.asarray(v0, float)) * u
    return np.asarray(kf[-1][1], float)


def caveat(size, weight="Bold"):
    f = ImageFont.truetype(os.path.join(FONTS, "Caveat.ttf"), size)
    f.set_variation_by_name(weight)
    return f


def typewriter(size):
    return ImageFont.truetype(os.path.join(FONTS, "SpecialElite-Regular.ttf"), size)


# --------------------------------------------------------------------------- art cache

_cache = {}


def art_image(name):
    key = ("img", name)
    if key not in _cache:
        fn, (l, t, r, b) = ARTWORKS[name]
        im = Image.open(os.path.join(ART, fn)).convert("RGB")
        w, h = im.size
        _cache[key] = im.crop((int(l * w), int(t * h), int(r * w), int(b * h)))
    return _cache[key]


def card(name, max_w, max_h, border=16):
    """Artwork on a paper mount with a soft drop shadow, as one RGBA sprite."""
    key = ("card", name, max_w, max_h)
    if key in _cache:
        return _cache[key]
    im = art_image(name)
    s = min((max_w - 2 * border) / im.width, (max_h - 2 * border) / im.height)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    cw, ch = im.width + 2 * border, im.height + 2 * border
    pad = 60
    sprite = Image.new("RGBA", (cw + 2 * pad, ch + 2 * pad), (0, 0, 0, 0))
    shadow = Image.new("L", sprite.size, 0)
    ImageDraw.Draw(shadow).rectangle([pad + 6, pad + 22, pad + cw + 6, pad + ch + 22], fill=150)
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    sprite.paste((0, 8, 24, 255), (0, 0), shadow)
    mount = Image.new("RGBA", (cw, ch), PAPER + (255,))
    mount.paste(im, (border, border))
    sprite.alpha_composite(mount, (pad, pad))
    _cache[key] = sprite
    return sprite


def tile(name, size=228, border=7):
    key = ("tile", name, size)
    if key in _cache:
        return _cache[key]
    im = art_image(name)
    inner = size - 2 * border
    s = inner / min(im.width, im.height)
    im = im.resize((max(inner, round(im.width * s)), max(inner, round(im.height * s))), Image.LANCZOS)
    l, t = (im.width - inner) // 2, (im.height - inner) // 2
    im = im.crop((l, t, l + inner, t + inner))
    pad = 24
    spr = Image.new("RGBA", (size + 2 * pad, size + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("L", spr.size, 0)
    ImageDraw.Draw(sh).rectangle([pad + 3, pad + 10, pad + size + 3, pad + size + 10], fill=140)
    spr.paste((0, 8, 24, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(9)))
    m = Image.new("RGBA", (size, size), PAPER + (255,))
    m.paste(im, (border, border))
    spr.alpha_composite(m, (pad, pad))
    _cache[key] = spr
    return spr


def transform(sprite, scale=1.0, rot=0.0, alpha=1.0, wave=0.0, t=0.0):
    """Scale / rotate / fade a sprite; `wave` ripples it like it's seen through water."""
    im = sprite
    if wave > 0.5:
        a = np.asarray(im)
        hgt, wid = a.shape[:2]
        ys = np.arange(hgt)
        shift = (wave * np.sin(ys / 38.0 + t * 9.0)).astype(np.int32)
        cols = (np.arange(wid)[None, :] - shift[:, None]) % wid
        im = Image.fromarray(a[ys[:, None], cols], "RGBA")
    if abs(scale - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if abs(rot) > 0.05:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.999:
        r, g, b, a = im.split()
        a = a.point(lambda v: int(v * alpha))
        im = Image.merge("RGBA", (r, g, b, a))
    return im


def paste_center(frame, im, cx, cy):
    x, y = int(round(cx - im.width / 2)), int(round(cy - im.height / 2))
    # crop to the frame so alpha_composite never sees negative offsets
    l, t = max(0, -x), max(0, -y)
    r, b = min(im.width, W - x), min(im.height, H - y)
    if r <= l or b <= t:
        return
    frame.alpha_composite(im.crop((l, t, r, b)), (x + l, y + t))


# --------------------------------------------------------------------------- background

LW, LH = 120, 214
_gx, _gy = np.meshgrid(np.linspace(0, 1, LW, dtype=np.float32), np.linspace(0, 1, LH, dtype=np.float32))
_yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
_vx = np.linspace(-1, 1, W, dtype=np.float32)[None, :]
_vy = np.linspace(-1, 1, H, dtype=np.float32)[:, None]
VIGNETTE = (1 - 0.32 * np.clip(_vx ** 2 * 0.8 + _vy ** 2 * 0.55, 0, 1))[..., None].astype(np.float32)

BG_KF = [  # (time, (top colour, bottom colour))
    (0.0, ((200, 207, 210), (118, 128, 136))),
    (16.2, ((190, 198, 202), (104, 114, 122))),
    (16.9, ((96, 196, 210), (20, 96, 140))),
    (35.0, ((66, 162, 202), (14, 72, 124))),
    (50.6, ((44, 126, 180), (8, 50, 104))),
    (53.2, ((12, 42, 92), (2, 9, 32))),
    (60.6, ((18, 62, 118), (3, 14, 46))),
    (77.0, ((22, 72, 130), (4, 18, 54))),
    (86.5, ((14, 46, 94), (2, 9, 32))),
    (DURATION, ((10, 32, 70), (1, 6, 22))),
]


def light_map(t):
    X, Y = _gx, _gy * (LH / LW)          # square units so the pattern isn't stretched
    wx = X + 0.06 * np.sin(Y * 4.1 + t * 0.6) + 0.04 * np.sin(X * 7.3 - t * 0.4)
    wy = Y + 0.06 * np.sin(X * 3.7 - t * 0.5) + 0.04 * np.sin(Y * 6.1 + t * 0.7)
    caustic = np.zeros_like(X)
    for ang, fq, sp in ((0.3, 13.0, 0.9), (1.4, 11.0, -0.7), (2.5, 15.0, 0.6)):
        d = wx * math.cos(ang) + wy * math.sin(ang)
        e = -wx * math.sin(ang) + wy * math.cos(ang)
        caustic += np.sin(d * fq + 1.5 * np.sin(e * fq * 0.55 + t * 0.8) + t * sp)
    caustic = np.clip(1 - np.abs(caustic) / 1.3, 0, 1) ** 5
    Y = _gy
    caustic *= np.clip(1 - Y * 1.25, 0, 1) ** 1.6
    rays = np.zeros_like(X)
    for k, x0 in enumerate((0.12, 0.38, 0.61, 0.86)):
        cx = x0 + 0.32 * Y + 0.04 * math.sin(t * 0.35 + k * 1.7)
        rays += np.exp(-((X - cx) / (0.035 + 0.02 * (k % 2))) ** 2) * (0.6 + 0.4 * math.sin(t * 0.5 + k))
    rays *= np.clip(1 - Y, 0, 1) ** 2
    L = caustic * 0.55 + rays * 0.35
    return np.asarray(Image.fromarray(L.astype(np.float32), "F").resize((W, H), Image.BILINEAR))


def beat_flash(t):
    if t < 60.95 or t > 86.5:
        return 0.0
    k = math.floor((t - BEAT0) / BEAT)
    return math.exp(-(t - beat(k)) / 0.13)


def background(t):
    top, bot = keyframes(BG_KF, t)
    top = np.array(top, np.float32)
    bot = np.array(bot, np.float32)
    grad = top[None, None, :] + (bot - top)[None, None, :] * _yy
    colour = clamp((t - 16.2) / 0.7)
    light_col = np.array(lerp_col((255, 255, 255), (190, 245, 255), colour), np.float32)
    strength = 0.16 + 0.16 * colour
    if DIVE[0] < t < DIVE[1] + 1.5:
        strength *= 1 - 0.6 * math.sin(math.pi * clamp((t - DIVE[0]) / (DIVE[1] + 1.5 - DIVE[0])))
    L = light_map(t)[..., None] * strength
    img = grad * (1 + 0.10 * beat_flash(t)) + L * light_col
    img = img * VIGNETTE
    return np.clip(img, 0, 255).astype(np.uint8)


# --------------------------------------------------------------------------- particles

_rng = np.random.default_rng(7)
N_BUB = 46
BUB_X = _rng.uniform(30, W - 30, N_BUB)
BUB_R = _rng.uniform(3, 15, N_BUB) ** 1.0
BUB_SPEED = _rng.uniform(40, 120, N_BUB)
BUB_OFF = _rng.uniform(0, H + 200, N_BUB)
BUB_PH = _rng.uniform(0, 6.28, N_BUB)


def bubble_travel(t):
    """Distance travelled: speeds up hugely during the dive."""
    base = t
    a, b = DIVE
    if t > a:
        u = clamp((t - a) / (b - a))
        base += 9.0 * (u - math.sin(2 * math.pi * u) / (2 * math.pi)) * (b - a) / 1.0
    return base


def draw_bubbles(draw, t):
    d = bubble_travel(t)
    vis = 0.55 + 0.45 * clamp((t - 16.3) / 0.8)
    for i in range(N_BUB):
        y = H + 100 - ((d * BUB_SPEED[i] + BUB_OFF[i]) % (H + 200))
        x = BUB_X[i] + 16 * math.sin(t * 1.3 + BUB_PH[i])
        r = BUB_R[i]
        a = int(110 * vis * (0.5 + 0.5 * (y / H)))
        draw.ellipse([x - r, y - r, x + r, y + r], outline=(235, 250, 255, a), width=2)
        hr = r * 0.32
        draw.ellipse([x - r * 0.45 - hr, y - r * 0.45 - hr, x - r * 0.45 + hr, y - r * 0.45 + hr],
                     fill=(255, 255, 255, int(a * 1.2)))


def draw_ripples(draw, t):
    for t0 in RIPPLES:
        for j in range(3):
            u = (t - t0 - j * 0.16) / 1.3
            if 0 < u < 1:
                r = 80 + 900 * ease_out(u)
                a = int(150 * (1 - u) ** 1.5)
                w = max(1, int(7 * (1 - u)) + 1)
                draw.ellipse([540 - r, CARD_CY - r * 0.9, 540 + r, CARD_CY + r * 0.9],
                             outline=(235, 252, 255, a), width=w)


DEPTH_KF = [(0, 0.0), (16.3, 1.0), (16.9, 4.0), (50.8, 22.0), (53.4, 160.0), (60.9, 190.0),
            (77.5, 320.0), (86.5, 420.0)]


def draw_depth(draw, t, font):
    a = int(170 * clamp(t / 1.0) * clamp((END_CARD + 0.3 - t) / 0.6))
    if a <= 0:
        return
    x, y0, y1 = 44, 320, 1300
    for y in range(y0, y1 + 1, 49):
        draw.line([x - (7 if (y - y0) % 245 == 0 else 3), y, x, y], fill=(235, 250, 255, a // 2), width=2)
    draw.line([x, y0, x, y1], fill=(235, 250, 255, a // 2), width=2)
    d = keyframes(DEPTH_KF, t)
    if DIVE[0] < t < DIVE[1]:   # numbers tumble while diving
        d += 3 * math.sin(t * 40)
    py = y0 + (y1 - y0) * (1 - math.exp(-d / 140))
    draw.ellipse([x - 7, py - 7, x + 7, py + 7], fill=(255, 255, 255, a))
    draw.text((x + 14, py), f"{int(d)} m", font=font, fill=(240, 252, 255, a), anchor="lm")


# --------------------------------------------------------------------------- lyric layout

def layout_line(words, font, max_w=930):
    space = font.getlength(" ")
    items = [(i, w, font.getlength(w)) for i, (w, _) in enumerate(words)]

    def width(row):
        return sum(x[2] for x in row) + space * (len(row) - 1)

    if width(items) <= max_w:
        rows = [(items, width(items))]
    else:   # two rows, split where they are most even
        k = min(range(1, len(items)), key=lambda k: max(width(items[:k]), width(items[k:])))
        rows = [(items[:k], width(items[:k])), (items[k:], width(items[k:]))]
    lh = 104
    top = LYRIC_CY - lh * (len(rows) - 1) / 2
    out = []
    for r, (row, rw) in enumerate(rows):
        x = 540 - rw / 2
        for i, w, wl in row:
            out.append((i, w, x, top + r * lh))
            x += wl + space
    return out


def accent_at(t):
    if t >= GRID_START:
        return ACCENT["grid"]
    name = "birds"
    for s in SCENES:
        if s[1] <= t + 0.05:
            name = s[0]
    return ACCENT[name]


def draw_lyrics(frame, t, font):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dl, ds = ImageDraw.Draw(layer), ImageDraw.Draw(shadow)
    acc = accent_at(t)
    drew = False
    for n, (end, words) in enumerate(LYRICS):
        start = words[0][1]
        nxt = LYRICS[n + 1][1][0][1] if n + 1 < len(LYRICS) else end + 1.0
        show_from, hide_at = start - 0.35, min(end + 0.45, nxt - 0.05)
        if not (show_from <= t <= hide_at + 0.3):
            continue
        line_a = clamp((t - show_from) / 0.3) * clamp((hide_at + 0.3 - t) / 0.3)
        for i, w, x, y in layout_line(words, font):
            ws = words[i][1]
            we = words[i + 1][1] if i + 1 < len(words) else end
            sung = clamp((t - ws) / 0.12)
            lift = 10 * (1 - ease_out((t - ws) / 0.25)) if t >= ws else 10
            current = ws <= t < we + 0.05
            if current:
                col = acc
            else:
                col = (255, 255, 255)
            a = line_a * (0.38 + 0.62 * sung)
            ds.text((x + 3, y + 5 + lift), w, font=font, fill=(0, 10, 30, int(170 * a)), anchor="lm")
            dl.text((x, y + lift), w, font=font, fill=col + (int(255 * a),), anchor="lm")
            drew = True
    if drew:
        frame.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(6)))
        frame.alpha_composite(layer)


# --------------------------------------------------------------------------- the artwork layer

def float_motion(t, seed):
    return (1.3 * math.sin(2 * math.pi * t / 5.5 + seed),
            11 * math.sin(2 * math.pi * t / 4.3 + seed * 1.7))


def draw_scene(frame, t, idx, scene):
    name, t0, t1, enter, leave, extra = scene
    chorus = extra.get("chorus")
    max_w, max_h = (2400, 880) if extra.get("pan") else (860, 1020)
    if extra.get("box"):
        max_w, max_h = 800, 960
    sprite = card(name, max_w, max_h)

    rot_f, bob = float_motion(t, idx * 1.9)
    cx, cy, scale, rot, alpha, wave = 540.0, CARD_CY + bob, 1.0, rot_f, 1.0, 0.0
    if extra.get("pan"):
        cx = 540 + (sprite.width / 2 - 520) * (1 - 2 * ease_in_out((t - t0) / (t1 - t0)))

    # entrances
    u = t - t0
    if enter == "rise":
        e = ease_out(u / 0.8)
        cy += 300 * (1 - e)
        alpha *= clamp(u / 0.45)
        wave = max(wave, 34 * (1 - e))
    elif enter == "splash":
        scale *= lerp(0.55, 1.0, ease_out_back(u / 0.7))
        alpha *= clamp(u / 0.2)
        wave = max(wave, 26 * (1 - ease_out(u / 0.9)))
    elif enter == "tilt":
        e = ease_out(u / 1.0)
        rot += lerp(-16, -2.5, e) - rot_f * (1 - e)
        cy += 260 * (1 - e)
        alpha *= clamp(u / 0.4)
    elif enter == "cut":
        k = idx % 2 * 2 - 1
        e = ease_out(u / 0.22)
        scale *= lerp(1.09, 1.0, e)
        cx += k * 70 * (1 - e)
        rot = k * 2.2 + rot_f * 0.4

    if chorus or (enter == "splash" and t0 > 60):
        # punch on every beat in the chorus
        kb = math.floor((t - BEAT0) / BEAT)
        scale *= 1 + 0.028 * math.exp(-(t - beat(kb)) / 0.12)

    # exits
    v = t - t1
    if leave == "drift" and v > -0.35:
        e = ease_in_out((v + 0.35) / 0.7)
        cy -= 220 * e
        alpha *= 1 - e
        wave = max(wave, 30 * e)
    elif leave == "drop" and v > -0.3:          # falls away into the silence before the hit
        e = clamp((v + 0.3) / 0.45) ** 2
        cy += 500 * e
        scale *= 1 - 0.25 * e
        alpha *= 1 - e
    elif leave == "sink" and v > -0.6:          # "won't be boxed up" -> dive down
        e = ease_in_out((v + 0.6) / 1.6)
        cy += 900 * e
        scale *= 1 - 0.55 * e
        rot += 18 * e
        alpha *= 1 - e
        wave = max(wave, 40 * e)

    if alpha <= 0.01:
        return
    paste_center(frame, transform(sprite, scale, rot, alpha, wave, t), cx, cy)


def draw_box(draw, t, scene):
    """A dashed 'box' around the framed Madhubani pieces that bursts on 'boxed up'."""
    name, t0, t1 = scene[0], scene[1], scene[2]
    if name == "garlic":
        a = clamp((t - t0 - 0.6) / 0.5) * clamp((t1 + 0.1 - t) / 0.4)
        burst = 0
    else:
        a = clamp((t - t0) / 0.4) * clamp((50.9 - t) / 0.25)
        burst = ease_out((t - 50.45) / 0.45) if t > 50.45 else 0
    if a <= 0:
        return
    half_w, half_h = 470 + 400 * burst, 560 + 400 * burst
    col = (255, 255, 255, int(200 * a * (1 - burst)))
    x0, y0, x1, y1 = 540 - half_w, CARD_CY - half_h, 540 + half_w, CARD_CY + half_h
    for (ax, ay, bx, by) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        length = math.hypot(bx - ax, by - ay)
        n = int(length // 34)
        for k in range(n):
            s, e = k / n, (k + 0.55) / n
            draw.line([lerp(ax, bx, s), lerp(ay, by, s), lerp(ax, bx, e), lerp(ay, by, e)], fill=col, width=4)


def draw_moon(frame, t, scene):
    t0, t1 = scene[1], scene[2]
    a = clamp((t - t0) / 0.5) * clamp((t1 - t) / 0.5)
    if a <= 0:
        return
    r, cx, cy = 50, 948, 200
    size = 2 * r + 8
    disc = Image.new("L", (size, size), 0)
    ImageDraw.Draw(disc).ellipse([4, 4, 4 + 2 * r, 4 + 2 * r], fill=255)
    off = lerp(-2.1 * r, 2.1 * r, clamp((t - t0) / (t1 - t0)))  # waxes, full, wanes
    shade = Image.new("L", (size, size), 0)
    ImageDraw.Draw(shade).ellipse([4 + off, 4, 4 + off + 2 * r, 4 + 2 * r], fill=255)
    m = ImageChops.subtract(disc, shade).point(lambda v: int(v * a))
    glow = m.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.6))
    moon = Image.new("RGBA", (size, size), (255, 244, 214, 0))
    moon.putalpha(m)
    g = Image.new("RGBA", (size, size), (255, 236, 190, 0))
    g.putalpha(glow)
    frame.alpha_composite(g, (cx - size // 2, cy - size // 2))
    frame.alpha_composite(moon, (cx - size // 2, cy - size // 2))


# --------------------------------------------------------------------------- the mosaic finale

TILE, GAP = 228, 14
GRID_X0 = (W - (4 * TILE + 3 * GAP)) // 2
GRID_Y0 = CARD_CY - (4 * TILE + 3 * GAP) // 2
_trng = np.random.default_rng(11)
TILE_ROT = _trng.uniform(-3.5, 3.5, 16)


def draw_grid(frame, t):
    self_i = GRID_ORDER.index("self")
    z = ease_in_out((t - ZOOM_START) / (ZOOM_END - ZOOM_START))
    kb = math.floor((t - BEAT0) / BEAT)
    pulse = 1 + 0.03 * math.exp(-(t - beat(kb)) / 0.12)
    for i, name in enumerate(GRID_ORDER):
        if i == self_i:
            continue
        appear = GRID_START + GRID_POP.index(i) * BEAT / 2
        u = t - appear
        if u < 0:
            continue
        col, row = i % 4, i // 4
        tx = GRID_X0 + col * (TILE + GAP) + TILE / 2
        ty = GRID_Y0 + row * (TILE + GAP) + TILE / 2
        s = ease_out_back(u / 0.35) * pulse
        # scatter outwards when the self-portrait comes forward
        tx = lerp(tx, 540 + (tx - 540) * 2.6, z)
        ty = lerp(ty, CARD_CY + (ty - CARD_CY) * 2.6, z)
        a = clamp(u / 0.12) * (1 - z)
        if a <= 0.01 or s <= 0.02:
            continue
        paste_center(frame, transform(tile(name), s, TILE_ROT[i] * (1 - 0.5 * clamp(u / 0.4)), a), tx, ty)

    # the self-portrait tile grows into the full card
    u = t - (GRID_START + GRID_POP.index(self_i) * BEAT / 2)
    if u < 0:
        return
    col, row = self_i % 4, self_i // 4
    tx = GRID_X0 + col * (TILE + GAP) + TILE / 2
    ty = GRID_Y0 + row * (TILE + GAP) + TILE / 2
    if z <= 0:
        s = ease_out_back(u / 0.35) * pulse
        paste_center(frame, transform(tile("self"), s, TILE_ROT[self_i], clamp(u / 0.12)), tx, ty)
        return
    big = card("self", 860, 1020)
    s_start = (TILE + 40) / big.width
    s = lerp(s_start, 1.0, z) * (1 + 0.02 * math.exp(-(t - beat(kb)) / 0.12) * (z >= 1))
    rot_f, bob = float_motion(t, 3.0)
    paste_center(frame, transform(big, s, lerp(TILE_ROT[self_i], rot_f, z)),
                 lerp(tx, 540, z), lerp(ty, CARD_CY + bob, z))


# --------------------------------------------------------------------------- titles

def draw_titles(frame, t, fonts):
    d = ImageDraw.Draw(frame)
    a = clamp((t - 0.3) / 0.6) * clamp((4.3 - t) / 0.6)
    if a > 0:
        d.text((540, 176), "I   A M   A N   O C E A N", font=fonts["type"], fill=(40, 52, 60, int(220 * a)), anchor="mm")
        d.line([440, 214, 640, 214], fill=(40, 52, 60, int(150 * a)), width=2)
    # end card
    a = clamp((t - END_CARD) / 0.7)
    if a > 0:
        veil = Image.new("RGBA", (W, H), (2, 10, 30, int(170 * a)))
        frame.alpha_composite(veil)
        d = ImageDraw.Draw(frame)
        lift = 30 * (1 - ease_out((t - END_CARD) / 0.9))
        d.text((540, 860 + lift), "I am an ocean.", font=fonts["end"], fill=(255, 255, 255, int(255 * a)), anchor="mm")
        b = clamp((t - END_CARD - 0.5) / 0.6)
        d.text((540, 990 + lift), "a different me at every depth", font=fonts["type"],
               fill=(170, 236, 236, int(235 * b)), anchor="mm")


# --------------------------------------------------------------------------- frame

_fonts = {}


def fonts():
    if not _fonts:
        _fonts["lyric"] = caveat(96)
        _fonts["end"] = caveat(150)
        _fonts["type"] = typewriter(38)
        _fonts["depth"] = typewriter(30)
    return _fonts


def render(t):
    f = fonts()
    frame = Image.fromarray(background(t)).convert("RGBA")
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    draw_bubbles(od, t)
    draw_ripples(od, t)
    draw_depth(od, t, f["depth"])
    frame.alpha_composite(over)

    for idx, sc in enumerate(SCENES):
        if sc[5].get("moon") and sc[1] - 0.2 < t < sc[2] + 0.2:
            draw_moon(frame, t, sc)
    for idx, sc in enumerate(SCENES):
        name, t0, t1, enter, leave = sc[:5]
        tail = {"drift": 0.4, "drop": 0.2, "sink": 1.1, "cut": 0.0}[leave]
        if t0 <= t < t1 + tail:
            if sc[5].get("box"):
                box = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                draw_box(ImageDraw.Draw(box), t, sc)
                frame.alpha_composite(box)
            draw_scene(frame, t, idx, sc)
    if t >= GRID_START:
        draw_grid(frame, t)

    # white flash on the hit at 16.45
    fl = math.exp(-(t - 16.45) / 0.18) if t >= 16.45 else 0
    if fl > 0.01:
        frame.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(150 * fl))))

    draw_lyrics(frame, t, f["lyric"])
    draw_titles(frame, t, f)
    return frame.convert("RGB")


def render_bytes(i):
    return render(i / FPS).tobytes()


# --------------------------------------------------------------------------- main

def main():
    os.makedirs(OUT, exist_ok=True)
    if "--preview" in sys.argv:
        pdir = os.path.join(OUT, "preview")
        os.makedirs(pdir, exist_ok=True)
        times = [float(x) for x in sys.argv[sys.argv.index("--preview") + 1:]] or [2, 17.5, 31, 49.5, 52.3, 55, 66, 81, 85.8, 88.5]
        for t in times:
            render(t).save(os.path.join(pdir, f"ocean_{t:06.2f}.jpg"), quality=88)
            print("preview", t)
        return

    n = int(round(DURATION * FPS))
    out = os.path.join(OUT, "i_am_an_ocean.mp4")
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", SONG,
           "-filter_complex", f"[1:a]apad,atrim=0:{DURATION:.3f}[a]",
           "-map", "0:v", "-map", "[a]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(max(1, os.cpu_count() or 1)) as pool:
        for i, buf in enumerate(pool.imap(render_bytes, range(n), chunksize=8)):
            proc.stdin.write(buf)
            if i % 150 == 0:
                print(f"frame {i}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()
    render(85.9).save(os.path.join(OUT, "ocean_cover.jpg"), quality=92)
    print("wrote", out)


if __name__ == "__main__":
    main()
