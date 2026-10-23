#!/usr/bin/env python3
"""Pencil portrait progress reel: the work-in-progress photos dissolve into one
another like a time-lapse, then the finished drawing is revealed.

Photos live in artworks/pencil_portrait/ (step_01..step_11 in drawing order,
final.jpg is the finished scan).

Usage:  python3 make_pencil_reel.py               # renders output/pencil_portrait_reel.mp4
        python3 make_pencil_reel.py --preview 1 9  # stills at the given seconds -> output/preview/
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "artworks", "pencil_portrait")
FONTS = os.path.join(ROOT, "fonts")
OUT = os.path.join(ROOT, "output")

W, H = 1080, 1920
FPS = 30

PAPER = (236, 234, 230)
GRAPHITE = (52, 52, 56)
SOFT = (120, 120, 126)

PHOTO_W, PHOTO_H = 960, 1280     # 3:4, same as the source photos
PHOTO_Y = 330

INTRO = 1.6       # first photo holds with the title before the steps start moving
HOLD = 1.25       # each step on screen, excluding the dissolve
FADE = 0.55       # dissolve between steps
FINAL_FADE = 1.2
FINAL_HOLD = 5.0

# (start, end, text) for the handwritten caption above the photo
CAPTIONS = []
STEPS = []        # (start, end, image index)
DURATION = None


def caveat(size, weight="Bold"):
    f = ImageFont.truetype(os.path.join(FONTS, "Caveat.ttf"), size)
    f.set_variation_by_name(weight)
    return f


def typewriter(size):
    return ImageFont.truetype(os.path.join(FONTS, "SpecialElite-Regular.ttf"), size)


# the finished scan has a thin white border with rounded corners; keep only the drawing
FINAL_CROP = (50, 40, 1698, 2237)   # 3:4, trimmed from the bottom so the hair bun stays in


def enhance(im, gamma=1.15, depth=1.25, sat=0.85):
    """Lift the dim phone photos without blowing out the paper: stretch levels on
    brightness, brighten the midtones, deepen the graphite lines, calm the warm cast."""
    rgb = np.asarray(im).astype(np.float32)
    lum = rgb @ np.array([0.299, 0.587, 0.114], np.float32)
    lo, hi = np.percentile(lum, (0.5, 99.8))
    x = np.clip((lum - lo) / (hi - lo), 0, 1)
    x = x ** (1 / gamma)                       # brighter midtones, whites stay put
    x = np.where(x < 0.5, 0.5 * (2 * x) ** depth, 1 - 0.5 * (2 * (1 - x)) ** depth)  # gentle S-curve
    out_l = x * 255
    ratio = (out_l / np.maximum(lum, 1))[..., None]
    out = rgb * ratio
    grey = out_l[..., None]
    out = grey + (out - grey) * sat
    im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    return ImageEnhance.Sharpness(im).enhance(1.6)


def load_photo(path):
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    if os.path.basename(path) == "final.jpg":
        im = im.crop(FINAL_CROP)    # already edited, so no auto-enhance
    else:
        im = enhance(im)
    # a little extra resolution so the slow push-in stays sharp
    return ImageOps.fit(im, (int(PHOTO_W * 1.08), int(PHOTO_H * 1.08)), Image.LANCZOS)


def build():
    global DURATION
    names = sorted(f for f in os.listdir(SRC) if f.startswith("step_")) + ["final.jpg"]
    n_steps = len(names) - 1
    t = 0.0
    for i in range(n_steps):
        hold = HOLD + (INTRO if i == 0 else 0)
        STEPS.append((t, t + hold + FADE, i))
        t += hold
    final_start = t
    STEPS.append((t, t + FINAL_FADE + FINAL_HOLD, n_steps))
    DURATION = t + FINAL_FADE + FINAL_HOLD

    def at_step(k):
        return STEPS[k][0]

    CAPTIONS.extend([
        (0.0, at_step(3), "today's sketch practice"),
        (at_step(3), at_step(6), "acrylic markers, oil pastels,\nfineliners... now pencil"),
        (at_step(6), at_step(9), "I'm told to stick to one medium"),
        (at_step(9), final_start, "but I can't resist them all"),
        (final_start + 0.3, DURATION + 1, "today it's pencil."),
    ])
    return names


def paper_background(seed=7):
    rng = np.random.default_rng(seed)
    base = np.empty((H, W, 3), np.float32)
    base[:] = PAPER
    blot = rng.normal(0, 1, (H // 40 + 2, W // 40 + 2)).astype(np.float32)
    blot = np.array(Image.fromarray(blot).resize((W, H), Image.BICUBIC))
    fine = rng.normal(0, 1, (H, W)).astype(np.float32)
    base += (blot * 3.0 + fine * 3.5)[..., None]
    yy, xx = np.mgrid[0:H, 0:W]
    vig = 1 - 0.10 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    return np.clip(base * vig[..., None], 0, 255).astype(np.uint8)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def text_layer(text, font, fill, alpha):
    layer = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.multiline_text((W / 2, 130), text, font=font, fill=fill + (int(255 * alpha),), anchor="mm",
                     align="center", spacing=4)
    return layer


PHOTOS = None
BG = None
SHADOW = None


def setup():
    global PHOTOS, BG, SHADOW
    names = build()
    PHOTOS = [load_photo(os.path.join(SRC, n)) for n in names]
    BG = Image.fromarray(paper_background())
    sh = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sh).rectangle([(W - PHOTO_W) // 2 + 6, PHOTO_Y + 14,
                                  (W + PHOTO_W) // 2 + 6, PHOTO_Y + PHOTO_H + 14], fill=90)
    from PIL import ImageFilter
    SHADOW = sh.filter(ImageFilter.GaussianBlur(18))


def photo_at(idx, local_t, span):
    """Slow push-in over the life of the shot."""
    im = PHOTOS[idx]
    z = 1.08 - 0.06 * min(local_t / span, 1.0)
    cw, ch = int(PHOTO_W * z), int(PHOTO_H * z)
    x0, y0 = (im.width - cw) // 2, (im.height - ch) // 2
    if idx == len(PHOTOS) - 1:
        y0 = 0                      # keep the top of the hair bun in frame
    return im.crop((x0, y0, x0 + cw, y0 + ch)).resize((PHOTO_W, PHOTO_H), Image.BILINEAR)


def render_frame(frame):
    t = frame / FPS
    canvas = BG.copy()
    canvas.paste((0, 0, 0), (0, 0), SHADOW)

    layers = []
    for k, (s, e, idx) in enumerate(STEPS):
        if s <= t < e:
            fade = FINAL_FADE if idx == len(PHOTOS) - 1 else FADE
            a = 1.0 if k == 0 else ease((t - s) / fade)
            layers.append((photo_at(idx, t - s, e - s), a))
    photo = None
    for im, a in layers:
        photo = im if photo is None or a >= 1 else Image.blend(photo, im, a)
    canvas.paste(photo, ((W - PHOTO_W) // 2, PHOTO_Y))

    # handwritten caption, cross-fading between lines
    for s, e, text in CAPTIONS:
        if s <= t < e:
            a = min(ease((t - s) / 0.35), ease((e - t) / 0.35)) if s > 0 else ease((e - t) / 0.35)
            if a > 0:
                lines = text.count("\n") + 1
                lay = text_layer(text, caveat(92 if lines == 1 else 78), GRAPHITE, a)
                canvas.paste(lay, (0, PHOTO_Y - 260 + 10), lay)

    # step counter under the photo
    final_start = STEPS[-1][0]
    n_steps = len(PHOTOS) - 1
    if t < final_start + FINAL_FADE / 2:
        cur = max(k for k, st in enumerate(STEPS[:-1]) if st[0] <= t + FADE / 2)
        label, a = f"step {cur + 1:02d} / {n_steps}", 1.0
    else:
        label, a = "finished", ease((t - final_start - FINAL_FADE / 2) / 0.4)
    lay = text_layer(label, typewriter(40), SOFT, a)
    canvas.paste(lay, (0, PHOTO_Y + PHOTO_H - 60), lay)

    # progress line drawn like a pencil stroke under the counter
    d = ImageDraw.Draw(canvas)
    prog = min(t / (final_start + FINAL_FADE), 1.0)
    x0, x1, y = 180, W - 180, PHOTO_Y + PHOTO_H + 150
    d.line([(x0, y), (x1, y)], fill=(212, 210, 206), width=4)
    d.line([(x0, y), (x0 + (x1 - x0) * prog, y)], fill=GRAPHITE, width=4)

    # fade in from paper / out at the end
    a = min(ease(t / 0.4), ease((DURATION - t) / 0.5))
    if a < 1:
        canvas = Image.blend(BG, canvas, a)
    return canvas.tobytes()


def main():
    os.makedirs(OUT, exist_ok=True)
    setup()
    if "--preview" in sys.argv:
        pdir = os.path.join(OUT, "preview")
        os.makedirs(pdir, exist_ok=True)
        for ts in [float(a) for a in sys.argv[sys.argv.index("--preview") + 1:]] or [1, 5, 9, 13, 17, 22]:
            Image.frombytes("RGB", (W, H), render_frame(int(ts * FPS))).save(
                os.path.join(pdir, f"pencil_t{ts:05.1f}.jpg"), quality=88)
        return
    n = int(DURATION * FPS)
    out = os.path.join(OUT, "pencil_portrait_reel.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for i, buf in enumerate(pool.imap(render_frame, range(n), chunksize=4)):
            proc.stdin.write(buf)
            if i % 90 == 0:
                print(f"frame {i}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()
    Image.frombytes("RGB", (W, H), render_frame(n - int(1.5 * FPS))).save(
        os.path.join(OUT, "pencil_cover.jpg"), quality=92)
    print("wrote", out)


if __name__ == "__main__":
    main()
