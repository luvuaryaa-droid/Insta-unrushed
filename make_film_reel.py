#!/usr/bin/env python3
"""Moka pot process reel, film-roll style, horizontal (1920x1080).

The five process photos sit on a 35mm film strip. It opens on the finished drawing with
the hook typed out, rewinds to the first sketch, then advances frame by frame with
typewriter captions underneath. It zooms into the final drawing, and ends on a typed
"Save this" list.

Usage:  python3 make_film_reel.py                   # renders output/moka_pot_film.mp4
        python3 make_film_reel.py --preview 2 16 28  # stills -> output/preview/
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw

from make_style_samples import TYPEWRITER, font, smooth, text_size
from make_wide_samples import FH, FPS, FW, H, PITCH, STRIP_H, STRIP_TOP, W, film_frame

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "output")
NAME = "moka_pot_film"

BG = (14, 12, 11)
FILM_BASE = (32, 24, 18)
CREAM = (240, 230, 210)
ORANGE = (232, 140, 50)

# strip moves: (time the move starts, frame it moves to); each move takes MOVE seconds
REWIND = (2.6, 3.5)        # hook sits on frame 4 (index 3), then rewinds to frame 1
MOVE = 0.9
MOVES = [(7.5, 1), (11.0, 2), (14.6, 3), (19.0, 4)]
ZOOM = (15.4, 16.4, 18.6, 19.4)   # zoom into the final drawing: in start, in end, out start, out end
ZOOM_MAX = 1.25
OUTRO = 23.8               # strip slides away, the list starts
DURATION = 33.0

CAPTIONS = [  # (start, end, text)
    (0.2, 2.6, "I studied finance, not art."),
    (3.7, 7.4, "You don't need to be good to show your art."),
    (8.3, 10.9, "Half the page was still just lines."),
    (11.8, 14.5, "I almost didn't share any of this."),
    (15.8, 18.9, "Then it became this."),
    (19.8, 23.6, "Show up anyway. That's the whole skill."),
]

LIST_TITLE = "Save this:"
LIST_SUB = "5 things you can post when your art doesn't feel \"good enough\""
LIST = ["1. The unfinished stage", "2. The messy desk or floor you made it on", "3. One small part you love",
        "4. A before and after", "5. The mistake you decided to keep"]
CTA = "Post your unfinished page this week and tag me."

CPS = 24   # typing speed, characters per second

FILM, LEAK, BAND = None, None, None


def strip_pos(t):
    if t < REWIND[0]:
        return 3.0
    if t < REWIND[1]:
        return 3.0 * (1 - smooth((t - REWIND[0]) / (REWIND[1] - REWIND[0])))
    pos = 0.0
    for st, n in MOVES:
        if t >= st:
            pos = (n - 1) + smooth((t - st) / MOVE)
    return pos


def zoom_at(t):
    a, b, c, d = ZOOM
    if t < a or t >= d:
        return 1.0
    k = smooth((t - a) / (b - a)) if t < c else 1 - smooth((t - c) / (d - c))
    return 1 + (ZOOM_MAX - 1) * k


def draw_strip(img, t, dy):
    d = ImageDraw.Draw(img)
    top = STRIP_TOP + dy
    d.rectangle((0, top, W, top + STRIP_H), fill=FILM_BASE)
    off = -strip_pos(t) * PITCH
    hp = PITCH / 6
    x = -((-off) % hp) - hp
    while x < W + hp:
        for hy in (top + 28, top + STRIP_H - 28 - 40):
            d.rounded_rectangle((x, hy, x + 56, hy + 40), 8, fill=BG)
        x += hp
    lab = font(TYPEWRITER, 26)
    fy = top + (STRIP_H - FH) // 2
    for n in range(5):
        fx = W / 2 - FW / 2 + n * PITCH + off
        if fx > W or fx + FW < 0:
            continue
        img.paste(FILM[n], (int(fx), int(fy)))
        d.text((fx + 4, fy + FH + 14), f"{n + 1}A    ▸    400", font=lab, fill=ORANGE)


def typed(d, t, t0, txt, xy, f, fill, center=True, cursor=True):
    """Type `txt` from t0; returns True once fully typed."""
    if t < t0:
        return False
    n = int((t - t0) * CPS)
    done = n >= len(txt)
    cur = "_" if cursor and (not done or int(t * 3) % 2 == 0) else ""
    tw, th, ox, oy = text_size(d, txt, f)
    x = xy[0] - tw / 2 - ox if center else xy[0] - ox
    d.text((x, xy[1] - oy), txt[:n] + cur, font=f, fill=fill)
    return done


def frame(t):
    img = Image.new("RGB", (W, H), BG)
    # strip slides up and off for the outro
    dy = -1000 * smooth((t - OUTRO) / 0.9) if t >= OUTRO else 0
    if dy > -1000:
        draw_strip(img, t, dy)
    z = zoom_at(t)
    if z > 1.0:
        cx, cy = W / 2, STRIP_TOP + STRIP_H / 2 - 40
        bw, bh = W / z, H / z
        cy = max(cy, bh / 2)
        img = img.resize((W, H), Image.BICUBIC, box=(cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2))
    arr = np.asarray(img, np.float32)
    arr += LEAK * (0.5 + 0.5 * math.sin(t * 1.3))
    if REWIND[0] <= t < REWIND[1]:
        arr *= 1.0 + 0.12 * math.sin(t * 60)
    rng = np.random.default_rng(int(t * FPS))
    arr += rng.normal(0, 7, (H // 2, W // 2)).repeat(2, 0).repeat(2, 1)[..., None]
    arr = arr * BAND[..., None] + np.array(BG, np.float32) * (1 - BAND[..., None])
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)

    f = font(TYPEWRITER, 66)
    for c0, c1, txt in CAPTIONS:
        if c0 <= t < c1:
            typed(d, t, c0, txt, (W / 2, 935), f, CREAM)

    if t >= OUTRO + 0.6:
        t0 = OUTRO + 0.6
        typed(d, t, t0, LIST_TITLE, (W / 2, 120), font(TYPEWRITER, 84), ORANGE, cursor=False)
        t0 += 0.6
        typed(d, t, t0, LIST_SUB, (W / 2, 235), font(TYPEWRITER, 48), CREAM, cursor=False)
        t0 += len(LIST_SUB) / CPS * 0.5 + 0.4
        fl = font(TYPEWRITER, 58)
        left = W / 2 - max(text_size(d, s, fl)[0] for s in LIST) / 2
        for i, item in enumerate(LIST):
            typed(d, t, t0, item, (left, 380 + i * 92), fl, CREAM, center=False, cursor=False)
            t0 += 0.85
        t0 += 0.3
        typed(d, t, t0, CTA, (W / 2, 900), font(TYPEWRITER, 56), ORANGE)
    return img


def init():
    global FILM, LEAK, BAND
    FILM = [film_frame(i) for i in range(5)]
    # keeps the caption area dark even when the zoomed frame reaches down into it
    ys = np.arange(H, dtype=np.float32)[:, None].repeat(W, 1)
    BAND = 1 - 0.92 * np.clip((ys - 850) / 40, 0, 1)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    LEAK = (np.exp(-(((xx - W * 1.02) / 420) ** 2 + ((yy - H * 0.35) / 500) ** 2))[..., None]
            * np.array([90, 40, 0], np.float32))


def render(i):
    return np.asarray(frame(i / FPS)).tobytes()


def main():
    os.makedirs(OUT, exist_ok=True)
    if "--preview" in sys.argv:
        init()
        pdir = os.path.join(OUT, "preview")
        os.makedirs(pdir, exist_ok=True)
        for ts in [float(a) for a in sys.argv[sys.argv.index("--preview") + 1:]] or [2.4, 6, 10, 13.5, 17.5, 22.5, 32]:
            frame(ts).save(os.path.join(pdir, f"film_t{ts:05.1f}.jpg"), quality=88)
        return
    out = os.path.join(OUT, NAME + ".mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-c:v", "libx264", "-preset", "slow", "-crf", "28", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(DURATION * FPS)
    with Pool(os.cpu_count(), initializer=init) as pool:
        for i, buf in enumerate(pool.imap(render, range(n), chunksize=4)):
            proc.stdin.write(buf)
            if i % 150 == 0:
                print(f"frame {i}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()
    init()
    frame(2.5).save(os.path.join(OUT, NAME + "_cover.jpg"), quality=92)
    print("wrote", out)


if __name__ == "__main__":
    main()
