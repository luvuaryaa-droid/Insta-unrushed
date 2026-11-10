#!/usr/bin/env python3
"""Pencil to painting: the 14 progress photos aligned on top of each other so the
card appears to paint itself in place.

1. Alignment (needs opencv-python-headless, run once): every progress photo is matched
   to its neighbour with SIFT features, the homographies are chained onto step 13, and
   the colours are matched so the lighting doesn't flicker between photos. Results are
   cached in artworks/diya_aligned/, so later renders don't need OpenCV.
2. Animation: each step is revealed on top of the previous one through an organic
   "wet paint" mask (a directional sweep mixed with fractal noise), so new colour
   spreads across the card like brush strokes. It ends on a before/after slider.

Usage:  python3 make_transition.py                 # renders output/diya_transition.mp4
        python3 make_transition.py --cover         # just the reel cover (+ grid-crop preview)
        python3 make_transition.py --align         # redo the alignment
        python3 make_transition.py --preview 3 12  # stills -> output/preview/
"""
import math
import os
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from make_diya_reel import (CREAM, INDIGO_DEEP, INK, LABELS, MARIGOLD, TERRACOTTA, backdrop, caveat,
                            draw_bokeh, marker, paste_center, text_img)

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "artworks", "diya_process")
ALIGNED = os.path.join(ROOT, "artworks", "diya_aligned")
OUT = os.path.join(ROOT, "output")

W, H = 1080, 1920
FPS = 30
N = 14
REF = 12                 # step 13 (0-based 12) is the reference frame
CARD = 1000              # card size on screen
CARD_CY = 900

# Timeline (seconds)
T0 = 1.6                 # first transition starts
HOLD = 0.55              # pause on each step
TRANS = 1.25             # paint-in time for one step
T_DONE = T0 + (N - 1) * (HOLD + TRANS)
T_SLIDER = T_DONE + 1.6
SLIDER_DUR = 4.2
DURATION = T_SLIDER + SLIDER_DUR + 2.4


# --------------------------------------------------------------------------- alignment

def align():
    import cv2
    ims = [cv2.imread(os.path.join(SRC, f"step{i + 1:02d}.jpg")) for i in range(N)]
    sift = cv2.SIFT_create(6000)
    kd = [sift.detectAndCompute(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), None) for im in ims]
    bf = cv2.BFMatcher()

    def homography(a, b):
        m = bf.knnMatch(kd[a][1], kd[b][1], k=2)
        good = [x for x, y in m if x.distance < 0.75 * y.distance]
        src = np.float32([kd[a][0][x.queryIdx].pt for x in good])
        dst = np.float32([kd[b][0][x.trainIdx].pt for x in good])
        h, _ = cv2.findHomography(src, dst, cv2.RANSAC, 4.0)
        return h

    hs = {REF: np.eye(3)}
    for i in range(REF - 1, -1, -1):          # chain neighbours: much more robust than direct matches
        hs[i] = hs[i + 1] @ homography(i, i + 1)
    for i in range(REF + 1, N):
        hs[i] = hs[i - 1] @ homography(i, i - 1)

    rh, rw = ims[REF].shape[:2]
    warped = [cv2.warpPerspective(ims[i], hs[i], (rw, rh), flags=cv2.INTER_CUBIC,
                                  borderMode=cv2.BORDER_REPLICATE).astype(np.float32) for i in range(N)]

    # colour-match each photo to its (already matched) neighbour on pixels that didn't change
    def match(img, target):
        diff = np.abs(img - target).sum(2)
        sel = diff < np.percentile(diff, 40)
        out = img.copy()
        for c in range(3):
            a, b = img[..., c][sel], target[..., c][sel]
            g, o = np.polyfit(a, b, 1)
            out[..., c] = img[..., c] * g + o
        return np.clip(out, 0, 255)

    for i in range(REF - 1, -1, -1):
        warped[i] = match(warped[i], warped[i + 1])
    for i in range(REF + 1, N):
        warped[i] = match(warped[i], warped[i - 1])

    # square crop around the card in the reference frame
    m = 16
    s = min(rw, rh) - 2 * m
    x0, y0 = (rw - s) // 2, (rh - s) // 2
    os.makedirs(ALIGNED, exist_ok=True)
    for i, im in enumerate(warped):
        crop = cv2.cvtColor(im[y0:y0 + s, x0:x0 + s].astype(np.uint8), cv2.COLOR_BGR2RGB)
        Image.fromarray(crop).resize((CARD, CARD), Image.LANCZOS).save(
            os.path.join(ALIGNED, f"aligned{i + 1:02d}.jpg"), quality=94)
    print("aligned frames written to", ALIGNED)


# --------------------------------------------------------------------------- assets

@lru_cache(None)
def stage(i):
    return np.asarray(Image.open(os.path.join(ALIGNED, f"aligned{i + 1:02d}.jpg")).convert("RGB")).astype(np.float32)


def fbm(n, seed, octaves=5):
    rng = np.random.default_rng(seed)
    out = np.zeros((n, n), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        cells = 3 * 2 ** o
        g = rng.random((cells + 1, cells + 1)).astype(np.float32)
        out += amp * np.asarray(Image.fromarray(g).resize((n, n), Image.BICUBIC))
        tot += amp
        amp *= 0.55
    out /= tot
    return (out - out.min()) / (out.max() - out.min())


@lru_cache(None)
def reveal_field(k):
    """Per-pixel time (0..1) at which step k+1 paints over step k."""
    rng = np.random.default_rng(500 + k)
    yy, xx = np.mgrid[0:CARD, 0:CARD].astype(np.float32) / CARD
    a = rng.uniform(0, 2 * math.pi)
    sweep = (xx - 0.5) * math.cos(a) + (yy - 0.5) * math.sin(a)
    if k % 3 == 2:                                  # every third step spreads out from the middle
        sweep = np.sqrt((xx - 0.5) ** 2 + (yy - 0.45) ** 2)
    sweep = (sweep - sweep.min()) / (sweep.max() - sweep.min())
    f = 0.55 * sweep + 0.45 * fbm(CARD, 900 + k)
    # only where the painting actually changes does the order matter; elsewhere both match
    return (f - f.min()) / (f.max() - f.min())


def blend_stage(k, p):
    """Step k (0-based) painting into step k+1, progress p in 0..1."""
    a, b = stage(k), stage(k + 1)
    if p <= 0:
        return a
    if p >= 1:
        return b
    soft = 0.08
    m = np.clip((p * (1 + soft) - reveal_field(k)) / soft, 0, 1)[..., None]
    out = a * (1 - m) + b * m
    # wet edge: a faint bright rim right at the spreading front
    rim = (m * (1 - m))[..., 0] * 4
    out += (rim * 22)[..., None]
    return out


@lru_cache(None)
def card_frame():
    """Shadow + paper rim the card sits in."""
    pad = 70
    s = CARD + 2 * pad
    sh = Image.new("L", (s, s), 0)
    ImageDraw.Draw(sh).rectangle((pad + 6, pad + 18, pad + CARD + 6, pad + CARD + 18), fill=170)
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    out = Image.new("RGBA", (s, s), (0, 0, 10, 0))
    out.putalpha(sh)
    return out


@lru_cache(None)
def label_img(i):
    num = text_img(f"{i + 1:02d}", marker(70), MARIGOLD, 3, INDIGO_DEEP)
    lab = text_img(LABELS[i], caveat(84), CREAM, 3, INDIGO_DEEP)
    out = Image.new("RGBA", (num.width + 22 + lab.width, max(num.height, lab.height)), (0, 0, 0, 0))
    out.alpha_composite(num, (0, (out.height - num.height) // 2 + 2))
    out.alpha_composite(lab, (num.width + 22, (out.height - lab.height) // 2))
    return out


@lru_cache(None)
def texts():
    return dict(
        t1=text_img("pencil", caveat(150), CREAM, 3, INDIGO_DEEP),
        arrow=text_img("to", caveat(90, "Regular"), CREAM, 2, INDIGO_DEEP),
        t2=text_img("painting", marker(132), MARIGOLD, 4, INDIGO_DEEP),
        before=text_img("before", caveat(80), INK),
        after=text_img("after", caveat(80), INK),
        end=text_img("Happy Diwali", marker(128), MARIGOLD, 5, INDIGO_DEEP),
    )


def dots(canvas, cur, frac):
    """Progress dots under the card."""
    d = ImageDraw.Draw(canvas)
    gap = 54
    x0 = W / 2 - gap * (N - 1) / 2
    y = 1640
    for i in range(N):
        x = x0 + i * gap
        if i < cur or (i == cur and frac >= 1):
            d.ellipse((x - 12, y - 12, x + 12, y + 12), fill=MARIGOLD)
        elif i == cur:
            r = 8 + 4 * frac
            d.ellipse((x - 12, y - 12, x + 12, y + 12), outline=MARIGOLD, width=3)
            d.ellipse((x - r * frac, y - r * frac, x + r * frac, y + r * frac), fill=MARIGOLD)
        else:
            d.ellipse((x - 10, y - 10, x + 10, y + 10), outline=CREAM + (150,), width=3)


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# --------------------------------------------------------------------------- frame

GRAIN = None


def render(t):
    global GRAIN
    if GRAIN is None:
        GRAIN = [np.random.default_rng(5 + i).normal(0, 2.6, (H, W)).astype(np.float32) for i in range(3)]

    canvas = Image.fromarray(backdrop().astype(np.uint8)).convert("RGBA")
    draw_bokeh(canvas, t, 0.8 + 0.6 * smooth((t - T_DONE) / 1.0))
    tx = texts()

    # which step are we on?
    if t < T0:
        k, p = 0, 0.0
    elif t < T_DONE:
        u = t - T0
        k = int(u // (HOLD + TRANS))
        p = smooth((u - k * (HOLD + TRANS) - HOLD) / TRANS)
    else:
        k, p = N - 2, 1.0
    card = blend_stage(k, p)

    if t >= T_SLIDER:
        # before/after slider: pencil on the left, painting on the right
        s = (t - T_SLIDER) / SLIDER_DUR
        # sweep right, then left, then glide off so the painting is left on screen
        x = 0.5 + 0.42 * math.sin(min(s, 0.8) * 2 * math.pi)
        xs = int(CARD * x * (1 - smooth((s - 0.8) / 0.2))) if s < 1 else 0
        out = stage(N - 1).copy()
        if xs > 0:
            out[:, :xs] = stage(0)[:, :xs]
        card = out

    # gentle push-in over the whole piece
    zoom = 1.0 + 0.04 * smooth(t / T_DONE) - 0.04 * smooth((t - T_DONE) / 1.5)
    size = int(CARD * zoom)
    cimg = Image.fromarray(np.clip(card, 0, 255).astype(np.uint8))
    if size != CARD:
        cimg = cimg.resize((size, size), Image.BICUBIC)
    paste_center(canvas, card_frame(), W / 2, CARD_CY + 8)
    canvas.paste(cimg, (W // 2 - size // 2, CARD_CY - size // 2))

    if t >= T_SLIDER and t < T_SLIDER + SLIDER_DUR:
        s = (t - T_SLIDER) / SLIDER_DUR
        if xs > 0:
            lx = W // 2 - size // 2 + int(xs * size / CARD)
            d = ImageDraw.Draw(canvas)
            top, bot = CARD_CY - size // 2, CARD_CY + size // 2
            d.rectangle((lx - 3, top, lx + 3, bot), fill=CREAM)
            d.ellipse((lx - 30, CARD_CY - 30, lx + 30, CARD_CY + 30), fill=CREAM, outline=INK, width=3)
            d.polygon([(lx - 20, CARD_CY), (lx - 8, CARD_CY - 10), (lx - 8, CARD_CY + 10)], fill=INK)
            d.polygon([(lx + 20, CARD_CY), (lx + 8, CARD_CY - 10), (lx + 8, CARD_CY + 10)], fill=INK)
        ka = smooth(s / 0.1) * (1 - smooth((s - 0.82) / 0.1))
        for img, cx in ((tx["before"], W / 2 - 330), (tx["after"], W / 2 + 330)):
            pill = Image.new("RGBA", (img.width + 40, img.height + 10), (0, 0, 0, 0))
            ImageDraw.Draw(pill).rounded_rectangle((0, 0, pill.width - 1, pill.height - 1), 30,
                                                   fill=CREAM + (235,))
            pill.alpha_composite(img, (20, 5))
            paste_center(canvas, pill, cx, CARD_CY + size // 2 - 70, ka)

    # titles
    ki = smooth((t - 0.15) / 0.6)
    ko = 1 - smooth((t - T_DONE - 0.3) / 0.6)
    if ki * ko > 0:
        paste_center(canvas, tx["t1"], W / 2 - 110, 150 - 30 * (1 - ki), ki * ko)
        paste_center(canvas, tx["arrow"], W / 2 + 170, 170 - 30 * (1 - ki), ki * ko)
        paste_center(canvas, tx["t2"], W / 2 + 40, 285 - 30 * (1 - ki), ki * ko)
    ke = smooth((t - T_DONE - 0.6) / 0.7)
    if ke > 0:
        paste_center(canvas, tx["end"], W / 2, 210 + 40 * (1 - ke), ke)

    # label + progress dots
    if t < T_SLIDER:
        cur = k + 1 if p >= 0.5 else k
        if t < T0 + HOLD:
            cur = 0
        fade = 1 - smooth((t - T_SLIDER + 0.6) / 0.5)
        lab = label_img(cur)
        # labels swap with a little lift during each transition
        lift = math.sin(math.pi * p) if 0 < p < 1 else 0
        paste_center(canvas, lab, W / 2, 1520 - 14 * lift, fade * (1 - 0.6 * lift))
        dl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dots(dl, cur, 1.0)
        dl.putalpha(dl.getchannel("A").point(lambda a: int(a * fade)))
        canvas.alpha_composite(dl)

    arr = np.asarray(canvas.convert("RGB")).astype(np.float32)
    arr += GRAIN[int(t * FPS) % 3][..., None]
    return np.clip(arr, 0, 255).astype(np.uint8)


def render_frame(frame):
    return render(frame / FPS).tobytes()


def render_cover():
    """Reel cover: one card, half pencil sketch and half finished painting, split by the same
    wet-paint edge the video uses. Everything sits inside the middle 3:4 area (y 240..1680)
    that the profile grid shows."""
    canvas = Image.fromarray(backdrop().astype(np.uint8)).convert("RGBA")
    draw_bokeh(canvas, 3.0, 1.2)
    tx = texts()
    paste_center(canvas, tx["t1"], W / 2 - 110, 330)
    paste_center(canvas, tx["arrow"], W / 2 + 170, 350)
    paste_center(canvas, tx["t2"], W / 2 + 40, 465)

    # left-to-right sweep (sketch on the left, painting on the right, flame painted), roughened with noise
    yy, xx = np.mgrid[0:CARD, 0:CARD].astype(np.float32) / CARD
    f = 0.66 * (xx + 0.12 * yy) + 0.34 * fbm(CARD, 4242)
    f = (f - f.min()) / (f.max() - f.min())
    m = np.clip((f - 0.31) / 0.035, 0, 1)[..., None]
    card = stage(0) * (1 - m) + stage(N - 1) * m
    card += ((m * (1 - m))[..., 0] * 4 * 26)[..., None]          # bright wet edge on the seam
    size = 860
    cy = 1035
    cimg = Image.fromarray(np.clip(card, 0, 255).astype(np.uint8)).resize((size, size), Image.LANCZOS)
    frame = card_frame()
    frame = frame.resize((int(frame.width * size / CARD), int(frame.height * size / CARD)), Image.LANCZOS)
    paste_center(canvas, frame, W / 2, cy + 7)
    canvas.paste(cimg, (W // 2 - size // 2, cy - size // 2))

    tag = text_img("watch it paint itself", caveat(74), CREAM, 2, INDIGO_DEEP)
    paste_center(canvas, tag, W / 2, 1585)
    arr = np.asarray(canvas.convert("RGB")).astype(np.float32)
    arr += np.random.default_rng(4).normal(0, 2.5, (H, W, 1)).astype(np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def main():
    if "--align" in sys.argv or not os.path.exists(os.path.join(ALIGNED, f"aligned{N:02d}.jpg")):
        align()
        if "--align" in sys.argv:
            return
    os.makedirs(OUT, exist_ok=True)
    if "--cover" in sys.argv:
        cov = render_cover()
        cov.save(os.path.join(OUT, "diya_transition_cover.jpg"), quality=94)
        cov.crop((0, 240, W, 1680)).save(os.path.join(OUT, "diya_transition_cover_grid_preview.jpg"), quality=90)
        print("wrote", os.path.join(OUT, "diya_transition_cover.jpg"))
        return
    if "--preview" in sys.argv:
        pdir = os.path.join(OUT, "preview")
        os.makedirs(pdir, exist_ok=True)
        times = [float(a) for a in sys.argv[sys.argv.index("--preview") + 1:]] or [1, 5, 15, 26, 29, 33]
        for ts in times:
            Image.fromarray(render(ts)).save(os.path.join(pdir, f"trans_t{ts:05.1f}.jpg"), quality=88)
        print("previews in", pdir)
        return
    n = int(DURATION * FPS)
    out = os.path.join(OUT, "diya_transition.mp4")
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
    render_cover().save(os.path.join(OUT, "diya_transition_cover.jpg"), quality=94)
    print("wrote", out, f"({DURATION:.1f} s)")


if __name__ == "__main__":
    main()
