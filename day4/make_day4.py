#!/usr/bin/env python3
"""Painting my way back to myself, Day 4: a process reel of the snake-plant folk painting.

The ten progress photos (aligned by align.py so the board never moves) are revealed one
after another with a hand-painted brush-stroke wipe, so it looks like the painting
fills itself in on one canvas. Captions are burned in; the audio track is silent so
music can be added in Instagram.

Usage:  python3 align.py                 # once, writes aligned/
        python3 make_day4.py             # renders output/day4_process.mp4
        python3 make_day4.py --preview 1 5 20   # stills at those seconds -> output/preview/
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "fonts")
ALIGNED = os.path.join(HERE, "aligned")
OUT = os.path.join(HERE, "output")

W, H = 1080, 1920
FPS = 30
ART = 900                 # side of the painting on screen
ART_Y = 420               # top of the painting (keeps clear of the Reels UI)

# palette pulled from the painting
CREAM = (246, 238, 222)
COBALT = (62, 92, 160)
CRIMSON = (178, 40, 62)
MUSTARD = (232, 168, 52)
LEAF = (40, 110, 70)
INK = (34, 30, 30)

STEPS = [
    "pencil sketch first",
    "folk motifs: suns, vines + two little birds",
    "snake plant, stripe by stripe",
    "the pot: crimson + mustard",
    "the birds get their colour",
    "vines... and the first scary patch of blue",
    "committing to the blue",
    "gold dots everywhere",
    "sun motifs in the corners",
    "tape off, heart border + ink outlines",
]

# timeline (seconds)
T_HOOK = 3.2              # finished piece + title
T_WIPE = 0.9              # brush wipe between stages
T_HOLD = 1.55             # hold on each stage
T_FIRST = 1.6             # hold on the sketch before the first wipe


def caveat(size, weight="Bold"):
    f = ImageFont.truetype(os.path.join(FONTS, "Caveat.ttf"), size)
    f.set_variation_by_name(weight)
    return f


def marker(size):
    return ImageFont.truetype(os.path.join(FONTS, "PermanentMarker-Regular.ttf"), size)


def clamp(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out_back(x, s=1.7):
    x = clamp(x) - 1
    return x * x * ((s + 1) * x + s) + 1


# --------------------------------------------------------------------------- assets

def paper_bg(seed=3):
    rng = np.random.default_rng(seed)
    base = np.empty((H, W, 3), np.float32)
    base[:] = CREAM
    blot = rng.normal(0, 1, (H // 30 + 2, W // 30 + 2)).astype(np.float32)
    blot = np.array(Image.fromarray(blot).resize((W, H), Image.BICUBIC))
    fine = rng.normal(0, 1, (H, W)).astype(np.float32)
    base += (blot * 4 + fine * 3)[..., None]
    yy, xx = np.mgrid[0:H, 0:W]
    vig = 1 - 0.10 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    return Image.fromarray(np.clip(base * vig[..., None], 0, 255).astype(np.uint8))


def load_stages():
    return [np.asarray(Image.open(os.path.join(ALIGNED, f"{i:02d}.jpg")).convert("RGB")
                       .resize((ART, ART), Image.LANCZOS)).astype(np.float32) for i in range(1, 11)]


def brush_field(seed, n=7):
    """Per-pixel 'time' at which the brush reaches it, in [0, 1].

    The canvas is split into n overlapping horizontal bands painted one after
    another, alternating direction, each with a ragged bristly leading edge.
    """
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:ART, 0:ART].astype(np.float32)
    band_h = ART / n
    field = np.full((ART, ART), 9.0, np.float32)
    for k in range(n):
        cy = (k + 0.5) * band_h + rng.uniform(-10, 10)
        half = band_h * 0.78
        # wavy band edges
        wav = 14 * np.sin(xx / ART * math.pi * rng.uniform(1.5, 3) + rng.uniform(0, 6))
        inside = np.abs(yy - cy - wav) < half
        # ragged leading edge: bristle streaks
        rows = rng.normal(0, 1, ART).astype(np.float32)
        rows = np.convolve(rows, np.ones(5) / 5, "same") * 0.05
        x = xx / ART if k % 2 == 0 else 1 - xx / ART
        local = x * 0.85 + rows[:, None] + rng.uniform(0, 0.03)
        t = (k + clamp_arr(local)) / n
        field = np.where(inside & (t < field), t, field)
    field = np.where(field > 1, 1.0, field)
    return field


def clamp_arr(a):
    return np.clip(a, 0, 1)


def caption_strip(text, font, paper, ink, seed, pad=(40, 20)):
    asc, desc = font.getmetrics()
    tw = int(font.getlength(text))
    w, h = tw + 2 * pad[0], asc + desc + 2 * pad[1]
    rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    pts = []
    for i in range(24):
        f = i / 24
        pts.append((20 + w * f, 20 + rng.uniform(0, 5)))
    for i in range(10):
        pts.append((20 + w - rng.uniform(0, 6), 20 + h * i / 10))
    for i in range(24):
        f = i / 24
        pts.append((20 + w * (1 - f), 20 + h - rng.uniform(0, 5)))
    for i in range(10):
        pts.append((20 + rng.uniform(0, 6), 20 + h * (1 - i / 10)))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon([(x + 4, y + 7) for x, y in pts], fill=(30, 20, 10, 70))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(im)
    d.polygon(pts, fill=paper + (255,))
    d.text((20 + pad[0], 20 + pad[1] - desc * 0.2), text, font=font, fill=ink)
    return im


def heart(size, color):
    s = size
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = s * 0.27
    d.ellipse((s * 0.5 - 2 * r + 2, s * 0.12, s * 0.5 + 2, s * 0.12 + 2 * r), fill=color)
    d.ellipse((s * 0.5 - 2, s * 0.12, s * 0.5 + 2 * r - 2, s * 0.12 + 2 * r), fill=color)
    d.polygon([(s * 0.5 - 2 * r + 3, s * 0.12 + r * 1.25), (s * 0.5 + 2 * r - 3, s * 0.12 + r * 1.25),
               (s * 0.5, s * 0.92)], fill=color)
    return im


def paste_center(canvas, im, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if abs(rot) > 0.05:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 1:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    canvas.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


# --------------------------------------------------------------------------- timeline

def build_timeline():
    """List of (start, end, kind, data) segments."""
    segs = []
    t = 0.0
    segs.append((t, t + T_HOOK, "hook", None))
    t += T_HOOK
    starts = []
    segs.append((t, t + T_FIRST, "hold", 0))
    starts.append(t)
    t += T_FIRST
    for i in range(1, 10):
        segs.append((t, t + T_WIPE, "wipe", i))
        starts.append(t)
        t += T_WIPE
        hold = T_HOLD + (1.2 if i == 9 else 0)
        segs.append((t, t + hold, "hold", i))
        t += hold
    segs.append((t, t + 4.0, "compare", None))
    t += 4.0
    segs.append((t, t + 3.6, "outro", None))
    t += 3.6
    return segs, starts, t


STAGES = None
FIELDS = None
BG = None
SEGS = None
STEP_STARTS = None
DURATION = None
STRIPS = {}
TITLE = {}


def setup():
    global STAGES, FIELDS, BG, SEGS, STEP_STARTS, DURATION
    STAGES = load_stages()
    FIELDS = [brush_field(100 + i, n=6 if i % 2 else 7) for i in range(10)]
    BG = paper_bg()
    SEGS, STEP_STARTS, DURATION = build_timeline()
    f = caveat(66)
    for i, s in enumerate(STEPS):
        STRIPS[i] = caption_strip(s, f, (255, 252, 244), INK, 50 + i)
    TITLE["series"] = caption_strip("painting my way back to myself", caveat(70), COBALT, (255, 252, 244), 7)
    TITLE["day"] = caption_strip("DAY 4", marker(120), MUSTARD, INK, 8, pad=(46, 8))
    TITLE["how"] = caption_strip("how it came together", caveat(64), (255, 252, 244), INK, 9)
    TITLE["before"] = caption_strip("before", caveat(58), (255, 252, 244), INK, 10, pad=(28, 10))
    TITLE["after"] = caption_strip("after", caveat(58), CRIMSON, (255, 252, 244), 11, pad=(28, 10))
    TITLE["done"] = caption_strip("day 4: done", marker(92), CRIMSON, (255, 252, 244), 12, pad=(46, 10))
    TITLE["tomorrow"] = caption_strip("see you tomorrow for day 5", caveat(70), (255, 252, 244), INK, 13)
    TITLE["heart"] = heart(90, CRIMSON + (255,))
    TITLE["heart_s"] = heart(60, MUSTARD + (255,))


def art_frame(t):
    """Painting pixels (float array) and the active step index."""
    for s, e, kind, data in SEGS:
        if s <= t < e:
            break
    else:
        s, e, kind, data = SEGS[-1]
    if kind in ("hook", "outro"):
        return STAGES[9], 9, kind, (t - s) / (e - s)
    if kind == "compare":
        return STAGES[9], 9, kind, (t - s) / (e - s)
    if kind == "hold":
        return STAGES[data], data, kind, (t - s) / (e - s)
    p = (t - s) / (e - s)
    # soft-edged brush reveal
    m = np.clip((p * 1.12 - FIELDS[data]) / 0.06, 0, 1)[..., None]
    a, b = STAGES[data - 1], STAGES[data]
    return a * (1 - m) + b * m, data, kind, p


def frame_at(t):
    canvas = BG.copy().convert("RGBA")
    art, step, kind, p = art_frame(t)

    # gentle push-in over the whole process section
    zoom = 1.0
    if kind == "hook":
        zoom = 1.06 - 0.06 * ease(p)
    elif kind == "outro":
        zoom = 1.0 + 0.04 * ease(p)
    if kind == "compare":
        # a slider sweeps in from the left, uncovering the sketch underneath
        cut = int(ART * 0.5 * ease(clamp((p - 0.08) / 0.45)))
        art = art.copy()
        art[:, :cut] = STAGES[0][:, :cut]
        art_img = Image.fromarray(art.astype(np.uint8)).convert("RGBA")
        d = ImageDraw.Draw(art_img)
        if cut > 0:
            d.line((cut, 0, cut, ART), fill=(255, 252, 244, 255), width=8)
    else:
        art_img = Image.fromarray(art.astype(np.uint8)).convert("RGBA")
    if zoom != 1.0:
        z = int(ART * zoom)
        art_img = art_img.resize((z, z), Image.BICUBIC)
        o = (z - ART) // 2
        art_img = art_img.crop((o, o, o + ART, o + ART))

    # shadow + white mount
    x0 = (W - ART) // 2
    mount = Image.new("RGBA", (ART + 36, ART + 36), (255, 253, 248, 255))
    sh = Image.new("RGBA", (ART + 140, ART + 140), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((50, 60, 50 + ART + 36, 60 + ART + 36), fill=(40, 25, 10, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    canvas.alpha_composite(sh, (x0 - 18 - 50 + 6, ART_Y - 18 - 50))
    canvas.alpha_composite(mount, (x0 - 18, ART_Y - 18))
    canvas.alpha_composite(art_img, (x0, ART_Y))

    cy_cap = ART_Y + ART + 110

    # header: series title + day badge, always visible after it pops in
    tp = clamp(t / 0.5)
    paste_center(canvas, TITLE["series"], W / 2 + 120, 245, scale=ease_out_back(tp), rot=-1.5)
    dp = clamp((t - 0.35) / 0.5)
    if dp > 0:
        paste_center(canvas, TITLE["day"], 185, 345, scale=ease_out_back(dp), rot=-6)

    if kind == "hook":
        hp = clamp((t - 1.2) / 0.5)
        if hp > 0:
            paste_center(canvas, TITLE["how"], W / 2, cy_cap, scale=ease_out_back(hp), rot=1.5)
            # little bouncing arrow
            ay = cy_cap + 95 + 10 * math.sin(t * 7)
            d = ImageDraw.Draw(canvas)
            d.line((W / 2, ay - 20, W / 2, ay + 22), fill=INK, width=6)
            d.line((W / 2 - 18, ay + 4, W / 2, ay + 24, W / 2 + 18, ay + 4), fill=INK, width=6, joint="curve")
    elif kind in ("hold", "wipe"):
        # caption for the current step pops in as its wipe starts
        st = STEP_STARTS[step]
        cp = clamp((t - st) / 0.35)
        rot = (-1.8, 1.5, -1.0, 2.0, -1.5)[step % 5]
        paste_center(canvas, STRIPS[step], W / 2, cy_cap, scale=ease_out_back(cp), rot=rot)
        # progress: ten dots
        for i in range(10):
            cx = W / 2 + (i - 4.5) * 54
            cy = cy_cap + 115
            d = ImageDraw.Draw(canvas)
            col = (COBALT if i < step else CRIMSON) if i <= step else None
            if col:
                d.ellipse((cx - 13, cy - 13, cx + 13, cy + 13), fill=col)
            else:
                d.ellipse((cx - 13, cy - 13, cx + 13, cy + 13), outline=INK, width=3)
        num = caption_strip(f"step {step + 1}/10", caveat(46, "Regular"), CREAM, INK, 200 + step,
                            pad=(14, 2))
        paste_center(canvas, num, W - 190, ART_Y - 44, rot=3)
    elif kind == "compare":
        bp = clamp((p - 0.35) / 0.15)
        if bp > 0:
            paste_center(canvas, TITLE["before"], x0 + ART * 0.25, cy_cap - 40, scale=ease_out_back(bp), rot=-3)
            paste_center(canvas, TITLE["after"], x0 + ART * 0.75, cy_cap - 40, scale=ease_out_back(bp), rot=3)
    elif kind == "outro":
        op = clamp(p / 0.15)
        paste_center(canvas, TITLE["done"], W / 2, cy_cap - 20, scale=ease_out_back(op), rot=-2)
        tp2 = clamp((p - 0.2) / 0.15)
        if tp2 > 0:
            paste_center(canvas, TITLE["tomorrow"], W / 2, cy_cap + 120, scale=ease_out_back(tp2), rot=1.5)
        for i, (hx, hy, key, d0) in enumerate(((130, 1560, "heart", 0.3), (950, 1530, "heart_s", 0.38),
                                               (960, 340, "heart", 0.45))):
            hp = clamp((p - d0) / 0.12)
            if hp > 0:
                paste_center(canvas, TITLE[key], hx, hy + 6 * math.sin(t * 4 + i),
                             scale=ease_out_back(hp), rot=(-12, 10, 8)[i])
    return canvas.convert("RGB")


def render(i):
    return np.asarray(frame_at(i / FPS)).tobytes()


def main():
    os.makedirs(OUT, exist_ok=True)
    setup()
    if "--preview" in sys.argv:
        pdir = os.path.join(OUT, "preview")
        os.makedirs(pdir, exist_ok=True)
        times = [float(a) for a in sys.argv[sys.argv.index("--preview") + 1:]] or [2.5, 5, 8, 15, 24, 32, 36]
        for ts in times:
            frame_at(ts).save(os.path.join(pdir, f"t{ts:05.1f}.jpg"), quality=88)
        print("duration", DURATION)
        return
    n = int(DURATION * FPS)
    out = os.path.join(OUT, "day4_process.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for i, buf in enumerate(pool.imap(render, range(n), chunksize=4)):
            proc.stdin.write(buf)
            if i % 90 == 0:
                print(f"frame {i}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()
    frame_at(2.6).save(os.path.join(OUT, "cover.jpg"), quality=92)
    print("wrote", out, f"({DURATION:.1f}s)")


if __name__ == "__main__":
    main()
