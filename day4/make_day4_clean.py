#!/usr/bin/env python3
"""Day 4, text-free version: just the painting building itself, square 1080x1080.

Same aligned stages and brush-stroke wipes as make_day4.py, but full-bleed with no
captions, titles or progress markers. Ends with a before/after slider and a hold.

Usage:  python3 make_day4_clean.py        # -> output/day4_painting_1x1.mp4
"""
import os
import subprocess
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw

import make_day4 as base

SIZE = 1080
FPS = 30
base.ART = SIZE           # brush_field / load_stages read this at call time

T_FIRST = 1.2             # hold on the sketch
T_WIPE = 0.9
T_HOLD = 1.3
T_FINAL = 1.5             # extra hold once finished
T_SLIDE = 3.2             # before/after slider in and back out
T_END = 2.2

STAGES = FIELDS = SEGS = None
DURATION = 0.0


def setup():
    global STAGES, FIELDS, SEGS, DURATION
    # trim 3% off each edge to hide the stretched border pixels left by the alignment warp
    m = int(SIZE * 0.03)
    STAGES = [np.asarray(Image.fromarray(s.astype(np.uint8)).crop((m, m, SIZE - m, SIZE - m))
                         .resize((SIZE, SIZE), Image.LANCZOS)).astype(np.float32)
              for s in base.load_stages()]
    FIELDS = [base.brush_field(100 + i, n=6 if i % 2 else 7) for i in range(10)]
    segs, t = [], 0.0
    segs.append((t, t + T_FIRST, "hold", 0)); t += T_FIRST
    for i in range(1, 10):
        segs.append((t, t + T_WIPE, "wipe", i)); t += T_WIPE
        hold = T_HOLD + (T_FINAL if i == 9 else 0)
        segs.append((t, t + hold, "hold", i)); t += hold
    segs.append((t, t + T_SLIDE, "slide", 9)); t += T_SLIDE
    segs.append((t, t + T_END, "end", 9)); t += T_END
    SEGS, DURATION = segs, t


def frame_at(t):
    for s, e, kind, i in SEGS:
        if s <= t < e:
            break
    p = (t - s) / (e - s)
    if kind == "wipe":
        m = np.clip((p * 1.12 - FIELDS[i]) / 0.06, 0, 1)[..., None]
        art = STAGES[i - 1] * (1 - m) + STAGES[i] * m
    else:
        art = STAGES[i]
    if kind == "slide":
        # slider sweeps to the middle showing the sketch, pauses, then sweeps back
        k = base.ease(p / 0.35) if p < 0.5 else 1 - base.ease((p - 0.65) / 0.35)
        cut = int(SIZE * 0.5 * k)
        art = art.copy()
        art[:, :cut] = STAGES[0][:, :cut]
    img = Image.fromarray(np.clip(art, 0, 255).astype(np.uint8))
    if kind == "slide" and 0 < cut < SIZE:
        ImageDraw.Draw(img).line((cut, 0, cut, SIZE), fill=(255, 252, 244), width=6)
    if kind == "end":
        z = int(SIZE * (1 + 0.04 * base.ease(p)))
        o = (z - SIZE) // 2
        img = img.resize((z, z), Image.BICUBIC).crop((o, o, o + SIZE, o + SIZE))
    return img


def render(n):
    return np.asarray(frame_at(n / FPS)).tobytes()


def main():
    os.makedirs(base.OUT, exist_ok=True)
    setup()
    n = int(DURATION * FPS)
    out = os.path.join(base.OUT, "day4_painting_1x1.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{SIZE}x{SIZE}", "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for buf in pool.imap(render, range(n), chunksize=4):
            proc.stdin.write(buf)
    proc.stdin.close()
    proc.wait()
    frame_at(DURATION - 0.01).save(os.path.join(base.OUT, "cover_1x1.jpg"), quality=92)
    print("wrote", out, f"({DURATION:.1f}s)")


if __name__ == "__main__":
    main()
