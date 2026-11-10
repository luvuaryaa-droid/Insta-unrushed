#!/usr/bin/env python3
"""Diwali diya card, pencil to finish: a photo-animation reel built from 14 progress photos.

Each progress photo becomes a printed photo with a white border and a handwritten
label. The prints are tossed one after another onto a pile, with a camera-shutter
flash and a small shake as each one lands. At the end the finished card lifts off the
pile and fills the screen while the flame glows and sparkles twinkle around it.

Usage:  python3 make_diya_reel.py                  # renders output/diya_process.mp4
        python3 make_diya_reel.py --cover            # just the reel cover (+ grid-crop preview)
        python3 make_diya_reel.py --preview 2 9 26  # stills at those seconds -> output/preview/
"""
import math
import os
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "artworks", "diya_process")
FONTS = os.path.join(ROOT, "fonts")
OUT = os.path.join(ROOT, "output")

W, H = 1080, 1920
FPS = 30

INDIGO = (24, 32, 78)
INDIGO_DEEP = (12, 15, 40)
MARIGOLD = (247, 178, 64)
CREAM = (250, 244, 230)
INK = (36, 30, 34)
TERRACOTTA = (196, 84, 64)

LABELS = [
    "pencil sketch",
    "first strokes of blue",
    "outlining with a brush pen",
    "background done",
    "the diya gets its colours",
    "flowers bloom",
    "leaves & vines",
    "two golden fish",
    "shading the fish",
    "a lotus at the bottom",
    "stripes on the fish",
    "ink outlines",
    "dots & rays of light",
    "the border. done!",
]
N = len(LABELS)

# Timeline (seconds)
T_FIRST = 1.4          # first print starts flying in
STEP = 1.55            # gap between prints
FLY = 0.62             # flight time of one print
T_LAST_LAND = T_FIRST + (N - 1) * STEP + FLY
T_HERO = T_LAST_LAND + 1.0     # final print lifts off the pile
HERO_DUR = 1.3
DURATION = T_HERO + HERO_DUR + 5.0

PRINT_W = 860          # photo area width of a print


# --------------------------------------------------------------------------- helpers

def caveat(size, weight="Bold"):
    f = ImageFont.truetype(os.path.join(FONTS, "Caveat.ttf"), size)
    f.set_variation_by_name(weight)
    return f


def marker(size):
    return ImageFont.truetype(os.path.join(FONTS, "PermanentMarker-Regular.ttf"), size)


def clamp(x):
    return max(0.0, min(1.0, x))


def ease_out_back(x, s=1.4):
    x = clamp(x) - 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def ease_out(x):
    return 1 - (1 - clamp(x)) ** 3


def ease_in_out(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def rng_for(i):
    return np.random.default_rng(1000 + i)


def text_img(text, font, fill, stroke=0, stroke_fill=None):
    box = font.getbbox(text, stroke_width=stroke)
    im = Image.new("RGBA", (box[2] - box[0] + 8, box[3] - box[1] + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - box[0], 4 - box[1]), text, font=font, fill=fill,
                            stroke_width=stroke, stroke_fill=stroke_fill)
    return im


def paste_center(canvas, img, cx, cy, alpha=1.0):
    if alpha <= 0:
        return
    if alpha < 1:
        img = img.copy()
        img.putalpha(img.getchannel("A").point(lambda a: int(a * alpha)))
    canvas.alpha_composite(img, (int(round(cx - img.width / 2)), int(round(cy - img.height / 2))))


# --------------------------------------------------------------------------- assets

@lru_cache(None)
def photo(i):
    im = Image.open(os.path.join(SRC, f"step{i + 1:02d}.jpg")).convert("RGB")
    # centre-crop to a 1:1 window so every print has the same shape
    s = min(im.size)
    x0, y0 = (im.width - s) // 2, (im.height - s) // 2
    return im.crop((x0, y0, x0 + s, y0 + s)).resize((PRINT_W, PRINT_W), Image.LANCZOS)


@lru_cache(None)
def print_img(i):
    """A photo print: white border, thicker bottom edge with a handwritten label, soft shadow."""
    b, bottom = 34, 150
    pw, ph = PRINT_W + 2 * b, PRINT_W + b + bottom
    card = Image.new("RGBA", (pw, ph), CREAM + (255,))
    # faint paper grain on the border
    g = rng_for(i).normal(0, 4, (ph, pw)).astype(np.float32)
    arr = np.asarray(card).astype(np.float32)
    arr[..., :3] += g[..., None]
    card = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    card.paste(photo(i), (b, b))
    d = ImageDraw.Draw(card)
    d.rectangle((b, b, b + PRINT_W - 1, b + PRINT_W - 1), outline=(0, 0, 0, 40), width=2)
    num = text_img(f"{i + 1:02d}", marker(64), TERRACOTTA)
    lab = text_img(LABELS[i], caveat(78), INK)
    y = b + PRINT_W + (bottom - lab.height) // 2 + 4
    card.alpha_composite(num, (b + 6, b + PRINT_W + (bottom - num.height) // 2 + 2))
    card.alpha_composite(lab, (b + 6 + num.width + 18, y))
    # drop shadow
    pad = 60
    out = Image.new("RGBA", (pw + 2 * pad, ph + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("L", out.size, 0)
    ImageDraw.Draw(sh).rectangle((pad + 10, pad + 18, pad + pw + 10, pad + ph + 18), fill=150)
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    out.paste(Image.new("RGBA", out.size, (0, 0, 8, 255)), (0, 0), sh)
    out.alpha_composite(card, (pad, pad))
    return out


def rest_pose(i):
    """Where print i ends up on the pile."""
    r = rng_for(i)
    rot = float(r.uniform(-6, 6)) if i < N - 1 else -1.5
    dx = float(r.uniform(-34, 34))
    dy = float(r.uniform(-30, 30))
    return W / 2 + dx, 990 + dy, rot


def pose(i, t):
    """(cx, cy, rot, scale) of print i at time t, or None if not yet visible."""
    t0 = T_FIRST + i * STEP
    if t < t0:
        return None
    cx, cy, rot = rest_pose(i)
    p = (t - t0) / FLY
    if p >= 1:
        return cx, cy, rot, 1.0
    side = -1 if i % 2 == 0 else 1
    r = rng_for(i)
    sx = cx + side * (W * 1.15)
    sy = cy + float(r.uniform(-500, 300))
    srot = rot + side * float(r.uniform(28, 45))
    e = ease_out_back(p, 1.2)
    lift = math.sin(math.pi * clamp(p)) * 0.10       # print rises toward the camera mid-flight
    return sx + (cx - sx) * e, sy + (cy - sy) * e, srot + (rot - srot) * ease_out(p), 1.0 + lift


def draw_print(canvas, i, cx, cy, rot, scale, alpha=1.0):
    img = print_img(i)
    if scale != 1.0:
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.BICUBIC)
    img = img.rotate(rot, Image.BICUBIC, expand=True)
    paste_center(canvas, img, cx, cy, alpha)


# --------------------------------------------------------------------------- background

@lru_cache(None)
def backdrop():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.45) / H) ** 2)
    k = np.clip(d / 0.75, 0, 1)[..., None]
    arr = np.array(INDIGO, np.float32) * (1 - k) + np.array(INDIGO_DEEP, np.float32) * k
    # faint warm glow behind the pile
    glow = np.exp(-(((xx - W / 2) / 520) ** 2 + ((yy - 930) / 620) ** 2))[..., None]
    arr += glow * np.array([70, 40, 10], np.float32) * 0.55
    return arr


BOKEH = [(float(x), float(y), float(r), float(ph), float(sp))
         for x, y, r, ph, sp in zip(*[np.random.default_rng(7).uniform(a, b, 26)
                                      for a, b in [(0, W), (0, H), (14, 46), (0, 6.28), (8, 24)]])]


@lru_cache(None)
def bokeh_dot(r):
    s = int(r * 4)
    im = Image.new("L", (s, s), 0)
    ImageDraw.Draw(im).ellipse((s / 2 - r, s / 2 - r, s / 2 + r, s / 2 + r), fill=255)
    return im.filter(ImageFilter.GaussianBlur(r * 0.35))


def draw_bokeh(canvas, t, strength=1.0):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for k, (x, y, r, ph, sp) in enumerate(BOKEH):
        yy = (y - t * sp) % (H + 200) - 100
        a = (0.30 + 0.25 * math.sin(t * 1.3 + ph)) * strength
        col = MARIGOLD if k % 3 else (255, 214, 140)
        dot = bokeh_dot(int(r))
        tint = Image.new("RGBA", dot.size, col + (0,))
        tint.putalpha(dot.point(lambda v: int(v * a)))
        layer.alpha_composite(tint, (int(x - dot.width / 2), int(yy - dot.height / 2)))
    canvas.alpha_composite(layer)


# --------------------------------------------------------------------------- pile cache

_PILE = {}


def pile(n):
    """The first n prints already settled, cached."""
    if n not in _PILE:
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for i in range(n):
            cx, cy, rot = rest_pose(i)
            draw_print(im, i, cx, cy, rot, 1.0)
        _PILE[n] = im
    return _PILE[n]


# --------------------------------------------------------------------------- finale effects

FLAME = (0.47, 0.37)   # flame position in the final photo (fraction of the photo)


@lru_cache(None)
def glow_img(r):
    s = r * 2
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    d = np.sqrt((xx - r) ** 2 + (yy - r) ** 2) / r
    a = np.clip(1 - d, 0, 1) ** 2.2
    im = np.zeros((s, s, 4), np.uint8)
    im[..., 0], im[..., 1], im[..., 2] = 255, 200, 110
    im[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(im, "RGBA")


@lru_cache(None)
def sparkle(size):
    s = size * 2 + 4
    im = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(im)
    c = s / 2
    pts = []
    for k in range(8):
        a = k * math.pi / 4
        rr = size if k % 2 == 0 else size * 0.22
        pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
    d.polygon(pts, fill=255)
    im = im.filter(ImageFilter.GaussianBlur(0.8))
    out = Image.new("RGBA", (s, s), (255, 236, 170, 0))
    out.putalpha(im)
    return out


SPARKS = [(float(a), float(rr), float(ph), int(sz))
          for a, rr, ph, sz in zip(*[np.random.default_rng(3).uniform(lo, hi, 22)
                                     for lo, hi in [(0, 6.28), (0.12, 0.62), (0, 6.28), (10, 30)]])]


def draw_finale_fx(canvas, t, cx, cy, size, k):
    """Glow over the flame + twinkling sparkles; k fades the whole effect in."""
    fx = cx - size / 2 + FLAME[0] * size
    fy = cy - size / 2 + FLAME[1] * size
    pulse = 0.75 + 0.25 * math.sin(t * 5.2) + 0.08 * math.sin(t * 13.1)
    g = glow_img(260)
    paste_center(canvas, g, fx, fy, 0.55 * k * pulse)
    for a, rr, ph, sz in SPARKS:
        tw = max(0.0, math.sin(t * 3.0 + ph * 2))
        if tw <= 0.05:
            continue
        x = cx + math.cos(a) * rr * size * 0.9
        y = cy + math.sin(a) * rr * size * 0.9
        sp = sparkle(sz).rotate(t * 40 + ph * 30, Image.BICUBIC)
        paste_center(canvas, sp, x, y, tw * k)


# --------------------------------------------------------------------------- text overlays

@lru_cache(None)
def title_parts():
    return (text_img("from pencil", caveat(150), CREAM, 3, INDIGO_DEEP),
            text_img("to diya", marker(150), MARIGOLD, 4, INDIGO_DEEP),
            text_img("a Diwali card, step by step", caveat(64, "Regular"), CREAM))


@lru_cache(None)
def end_parts():
    return (text_img("Happy Diwali", marker(132), MARIGOLD, 5, INDIGO_DEEP),
            text_img("14 photos, one little card", caveat(70), CREAM, 2, INDIGO_DEEP))


@lru_cache(None)
def counter_img(n):
    return text_img(f"step {n} / {N}", caveat(70), CREAM, 2, INDIGO_DEEP)


def draw_titles(canvas, t):
    a, b, c = title_parts()
    # intro title, top of the frame, fades out once a few prints are down
    k_in = ease_out((t - 0.1) / 0.6)
    k_out = 1 - clamp((t - (T_FIRST + 2.2 * STEP)) / 0.6)
    k = k_in * k_out
    if k > 0:
        paste_center(canvas, a, W / 2 - 90, 150 - 30 * (1 - k_in), k)
        paste_center(canvas, b, W / 2 + 130, 275 - 30 * (1 - k_in), k)
    # step counter under the pile
    n = sum(1 for i in range(N) if t >= T_FIRST + i * STEP + FLY * 0.6)
    if n and t < T_HERO:
        paste_center(canvas, counter_img(n), W / 2, 1690, clamp((t - T_FIRST - 0.4) / 0.4)
                     * (1 - clamp((t - T_HERO + 0.4) / 0.4)))
    if 0 < k and t < T_FIRST + STEP:
        paste_center(canvas, c, W / 2, 1690, k_in * (1 - clamp((t - T_FIRST - 0.2) / 0.3)))
    # ending
    e1, e2 = end_parts()
    ke = ease_out((t - (T_HERO + HERO_DUR * 0.6)) / 0.7)
    if ke > 0:
        paste_center(canvas, e1, W / 2, 215 + 40 * (1 - ke), ke)
        paste_center(canvas, e2, W / 2, 1720 - 30 * (1 - ke), ease_out((t - T_HERO - HERO_DUR - 0.4) / 0.7))


# --------------------------------------------------------------------------- frame

GRAIN = None


def render(t):
    global GRAIN
    if GRAIN is None:
        rng = np.random.default_rng(99)
        GRAIN = [rng.normal(0, 3.0, (H, W)).astype(np.float32) for _ in range(3)]

    hero = ease_in_out((t - T_HERO) / HERO_DUR)
    canvas = Image.fromarray(backdrop().astype(np.uint8)).convert("RGBA")
    draw_bokeh(canvas, t, 1.0 + 0.6 * hero)

    settled = sum(1 for i in range(N) if t >= T_FIRST + i * STEP + FLY)
    if hero > 0:
        settled = min(settled, N - 1)
    under = pile(settled)
    if hero > 0:
        under = under.copy()
        under.putalpha(under.getchannel("A").point(lambda a: int(a * (1 - 0.85 * hero))))
    canvas.alpha_composite(under)
    for i in range(settled, N):
        p = pose(i, t)
        if p is None:
            continue
        cx, cy, rot, sc = p
        if i == N - 1 and hero > 0:
            # lift the finished card off the pile and straighten it
            cx, cy = cx + (W / 2 - cx) * hero, cy + (1000 - cy) * hero
            rot *= 1 - hero
            sc = 1 + 0.04 * hero
        draw_print(canvas, i, cx, cy, rot, sc)

    if t > T_HERO:
        k = ease_out((t - T_HERO - HERO_DUR * 0.5) / 0.8)
        size = PRINT_W * 1.04
        # photo centre sits above the print centre because of the thick bottom border
        pcy = 1000 - (150 - 34) / 2 * 1.04
        draw_finale_fx(canvas, t, W / 2, pcy, size, k)

    draw_titles(canvas, t)

    # camera: slow push-in, small shake on each landing, shutter flash
    zoom = 1.0 + 0.05 * clamp(t / T_LAST_LAND) - 0.05 * hero
    shake_x = shake_y = 0.0
    flash = 0.0
    for i in range(N):
        land = T_FIRST + i * STEP + FLY * 0.72
        dt = t - land
        if 0 <= dt < 0.35:
            amp = 9 * math.exp(-dt * 12)
            shake_x += amp * math.sin(dt * 70 + i)
            shake_y += amp * math.cos(dt * 61 + i)
        if 0 <= dt < 0.25:
            flash = max(flash, 0.22 * (1 - dt / 0.25))
    if t > T_HERO + HERO_DUR * 0.45:
        dt = t - (T_HERO + HERO_DUR * 0.45)
        if dt < 0.5:
            flash = max(flash, 0.45 * (1 - dt / 0.5))

    img = canvas.convert("RGB")
    if zoom != 1.0 or shake_x or shake_y:
        cw, ch = W / zoom, H / zoom
        x0 = (W - cw) / 2 + shake_x
        y0 = (H - ch) / 2 + shake_y
        img = img.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BICUBIC)
    arr = np.asarray(img).astype(np.float32)
    if flash:
        arr = arr + (255 - arr) * flash
    arr += GRAIN[int(t * FPS) % 3][..., None]
    return np.clip(arr, 0, 255).astype(np.uint8)


def render_frame(frame):
    return render(frame / FPS).tobytes()


def render_cover():
    """Reel cover: the pencil-sketch print fanned behind the finished print, with the title.
    Everything sits inside the middle 3:4 area (y 240..1680) that the profile grid shows."""
    canvas = Image.fromarray(backdrop().astype(np.uint8)).convert("RGBA")
    draw_bokeh(canvas, 3.0, 1.3)
    a, b, _ = title_parts()
    paste_center(canvas, a, W / 2 - 120, 330)
    paste_center(canvas, b, W / 2 + 150, 465)
    draw_print(canvas, 0, 365, 990, 10, 0.68)
    draw_print(canvas, N - 1, 650, 1115, -5, 0.72)
    for x, y, sz, rot in [(215, 610, 26, 10), (900, 700, 20, 30), (880, 1460, 24, 5), (170, 1430, 16, 40),
                          (600, 560, 18, 20)]:
        paste_center(canvas, sparkle(sz).rotate(rot, Image.BICUBIC), x, y)
    tag = text_img("14 photos, one little card", caveat(70), CREAM, 2, INDIGO_DEEP)
    paste_center(canvas, tag, W / 2, 1625)
    arr = np.asarray(canvas.convert("RGB")).astype(np.float32)
    arr += np.random.default_rng(4).normal(0, 2.5, (H, W, 1)).astype(np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def main():
    os.makedirs(OUT, exist_ok=True)
    if "--cover" in sys.argv:
        cov = render_cover()
        cov.save(os.path.join(OUT, "diya_cover.jpg"), quality=94)
        cov.crop((0, 240, W, 1680)).save(os.path.join(OUT, "diya_cover_grid_preview.jpg"), quality=90)
        print("wrote", os.path.join(OUT, "diya_cover.jpg"))
        return
    if "--preview" in sys.argv:
        pdir = os.path.join(OUT, "preview")
        os.makedirs(pdir, exist_ok=True)
        times = [float(a) for a in sys.argv[sys.argv.index("--preview") + 1:]] or [0.8, 2.4, 9, 20, 25, 29]
        for ts in times:
            Image.fromarray(render(ts)).save(os.path.join(pdir, f"diya_t{ts:05.1f}.jpg"), quality=88)
        print("previews in", pdir)
        return
    n = int(DURATION * FPS)
    out = os.path.join(OUT, "diya_process.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for i, buf in enumerate(pool.imap(render_frame, range(n), chunksize=8)):
            proc.stdin.write(buf)
            if i % 90 == 0:
                print(f"frame {i}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()
    render_cover().save(os.path.join(OUT, "diya_cover.jpg"), quality=94)
    print("wrote", out, f"({DURATION:.1f} s)")


if __name__ == "__main__":
    main()
