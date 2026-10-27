#!/usr/bin/env python3
"""Moka pot process reel: kinetic type over a film look, horizontal (1920x1080).

A vertical 35mm film strip on the right carries the five process photos (warm faded
grade, grain, light leak). On the left, huge bold words slam in one at a time, with key
words on an orange highlight. Opens on a hook over the finished drawing, rewinds to the
first sketch, runs a fast MESS / CHALLENGE / FEAR / OVERCOMING montage, zooms into the final
drawing, and ends on a "Save this" list.
A "journey" section (creating is a journey / the mess, the challenge, the fear, the
overcoming / without them the becoming is nothing) runs before the final reveal.

Usage:  python3 make_film_kinetic.py                   # renders output/moka_pot_film_kinetic.mp4
        python3 make_film_kinetic.py --preview 2 16 28  # stills -> output/preview/
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw

from make_style_samples import INTER_BLACK, INTER_MED, TYPEWRITER, cover, ease_out, ease_out_back, font, photo, \
    smooth, text_size

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "output")
NAME = "moka_pot_film_kinetic"
W, H, FPS = 1920, 1080, 30
DURATION = 43.0

BG = (20, 16, 13)
FILM_BASE = (34, 25, 18)
CREAM = (242, 232, 212)
ORANGE = (236, 142, 48)
GREY = (170, 158, 140)

# film strip geometry (vertical strip on the right)
FW, FH, GAP = 675, 900, 60
PITCH = FH + GAP
STRIP_W = FW + 2 * 80
STRIP_X = W - STRIP_W - 70

# words: (start, lines, highlighted lines, kicker under the stack)
SEGMENTS = [
    (0.0, ["YOU DON'T NEED", "TO BE GOOD", "TO SHOW", "YOUR ART."], {"YOUR ART."}, ""),   # hook, on screen from frame 1
    (3.0, [], set(), ""),                                   # rewind
    (3.8, ["I STUDIED", "FINANCE.", "NOT ART."], {"NOT ART."}, "day one: wobbly outlines, an empty mug."),
    (7.8, ["HALF THE PAGE", "WAS STILL", "JUST LINES."], {"JUST LINES."}, ""),
    (10.4, ["I ALMOST", "DIDN'T SHARE", "ANY OF THIS."], {"ANY OF THIS."}, ""),
    # the journey: the strip slowly travels back along the path while these play
    (13.0, ["CREATING IS", "A JOURNEY."], {"A JOURNEY."}, ""),
    (15.4, ["YOU GET BETTER", "BY WALKING", "THE PATH.", "NOT BEFORE IT."], {"NOT BEFORE IT."}, ""),
    (18.6, ["WAITING UNTIL IT'S", "\"WORTH SHARING\"", "LEAVES THE MAIN", "STORY BEHIND."], {"STORY BEHIND."}, ""),
    (22.2, ["THE MESS."], set(), ""),
    (22.75, ["THE CHALLENGE."], set(), ""),
    (23.3, ["THE FEAR."], set(), ""),
    (23.85, ["THE OVERCOMING."], {"THE OVERCOMING."}, ""),
    (24.5, ["WITHOUT THEM,", "THE BECOMING", "IS NOTHING."], {"THE BECOMING"}, ""),
    (27.4, ["THEN IT", "BECAME", "THIS."], {"THIS."}, ""),
    (30.6, ["SHOW UP", "ANYWAY."], {"ANYWAY."}, "that's the whole skill."),
    (33.6, [], set(), ""),                                  # outro list takes over
]
BEAT = 0.38

# strip moves: (start, target frame, duration); the strip starts on the final drawing (frame index 3)
STRIP_KEYS = [(3.0, 0, 0.8), (7.8, 1, 0.5), (10.4, 2, 0.5),
              (13.0, 0, 2.2), (15.4, 1, 3.0), (18.6, 2, 3.4),                  # slow walk along the path
              (22.2, 0, 0.25), (22.75, 1, 0.2), (23.3, 2, 0.2), (23.85, 3, 0.2),  # mess / challenge / fear / overcoming
              (30.6, 4, 0.5)]
REWIND = (3.0, 3.8)
ZOOM = (24.5, 25.1, 30.0, 30.6)   # zoom the strip into the final drawing
ZOOM_MAX = 1.18
OUTRO = 33.6

LIST_SUB = "5 things to post when your art doesn't feel \"good enough\""
LIST = ["THE UNFINISHED STAGE", "THE MESSY DESK YOU MADE IT ON", "ONE SMALL PART YOU LOVE",
        "A BEFORE + AFTER", "THE MISTAKE YOU KEPT"]
CTA = "POST YOUR UNFINISHED PAGE THIS WEEK + TAG ME"

FRAMES, LEAK, GRAIN = None, None, None


def film_frame(idx):
    im = cover(photo(idx), FW, FH, 1.0, (0.56 if idx == 4 else 0.5, 0.45))
    arr = (18 + np.asarray(im, np.float32) * 0.9) * np.array([1.06, 1.0, 0.86], np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def strip_pos(t):
    pos = 3.0
    for st, target, dur in STRIP_KEYS:
        if t >= st:
            pos = pos + (target - pos) * smooth((t - st) / dur)
    return pos


def zoom_at(t):
    a, b, c, d = ZOOM
    if t < a or t >= d:
        return 1.0
    k = smooth((t - a) / (b - a)) if t < c else 1 - smooth((t - c) / (d - c))
    return 1 + (ZOOM_MAX - 1) * k


def draw_strip(img, t):
    layer = Image.new("RGBA", (STRIP_W, H), FILM_BASE + (255,))
    d = ImageDraw.Draw(layer)
    off = -strip_pos(t) * PITCH
    hp = PITCH / 6
    y = -((-off) % hp) - hp
    while y < H + hp:
        for hx in (20, STRIP_W - 20 - 40):
            d.rounded_rectangle((hx, y, hx + 40, y + 56), 8, fill=BG + (255,))
        y += hp
    lab = font(TYPEWRITER, 24)
    fx = (STRIP_W - FW) // 2
    for n in range(5):
        fy = H / 2 - FH / 2 + n * PITCH + off
        if fy > H or fy + FH < 0:
            continue
        layer.paste(FRAMES[n], (fx, int(fy)))
        d.text((fx + 4, fy + FH + 16), f"{n + 1}A    ▸    400", font=lab, fill=ORANGE)
    z = zoom_at(t)
    if z > 1.0:
        layer = layer.resize((int(STRIP_W * z), int(H * z)), Image.BICUBIC)
    slide = 1000 * smooth((t - OUTRO) / 0.7) if t >= OUTRO else 0
    cx = STRIP_X + STRIP_W / 2 + slide
    img.paste(layer, (int(cx - layer.width / 2), int(H / 2 - layer.height / 2)))


def slam(d, t, t0, txt, x, y, size, fill, hot=False, center=False):
    """One line that slams in at t0 with an overshoot; `hot` adds an orange highlight bar."""
    if t < t0:
        return
    f = font(INTER_BLACK, size)
    tw, th, ox, oy = text_size(d, txt, f)
    asc, desc = f.getmetrics()
    left = x - tw / 2 if center else x
    if hot:
        grow = ease_out((t - t0) / 0.25)
        pad = size * 0.14
        d.rectangle((left - pad, y - pad * 0.6, left - pad + (tw + 2 * pad) * grow, y + asc * 0.78 + pad * 0.6),
                    fill=ORANGE)
    p = (t - t0) / 0.16
    sc = 1 + 0.35 * (1 - ease_out_back(p, 1.2)) if p < 1 else 1.0
    fs = font(INTER_BLACK, max(10, int(size * min(sc, 1.6))))
    sw, sh, sox, soy = text_size(d, txt, fs)
    cx = left + tw / 2
    cy = y + asc * 0.39
    d.text((cx - sw / 2 - sox, cy - sh / 2 - soy), txt, font=fs, fill=BG if hot else fill)


def draw_words(d, t):
    cur = max(i for i, s in enumerate(SEGMENTS) if s[0] <= t)
    s0, lines, hot, kicker = SEGMENTS[cur]
    if not lines:
        return
    probe = font(INTER_BLACK, 100)
    widest = max(text_size(d, w, probe)[0] for w in lines)
    size = int(min(110, 100 * 760 / widest))
    lh = int(size * 1.12)
    top = H / 2 - lh * len(lines) / 2 - (30 if kicker else 0)
    beat = BEAT if len(lines) > 1 else 0.05
    if s0 == 0:   # the hook is fully on screen from the first frame (it is also the preview image)
        s0, beat = -10.0, 0.0
    for i, line in enumerate(lines):
        slam(d, t, s0 + i * beat, line, 100, top + i * lh + (lh - size) / 2, size, CREAM, hot=line in hot)
    if kicker and t > s0 + beat * len(lines):
        d.text((100, top + lh * len(lines) + 30), kicker, font=font(TYPEWRITER, 36), fill=GREY)


def draw_outro(d, t):
    t0 = OUTRO + 0.5
    if t < t0:
        return
    slam(d, t, t0, "SAVE THIS.", 140, 150, 100, CREAM, hot=True)
    if t > t0 + 0.4:
        d.text((142, 310), LIST_SUB, font=font(TYPEWRITER, 38), fill=GREY)
    for i, item in enumerate(LIST):
        slam(d, t, t0 + 0.9 + i * 0.5, f"{i + 1}  {item}", 140, 400 + i * 84, 54, CREAM)
    slam(d, t, t0 + 0.9 + 5 * 0.5 + 0.5, CTA, 140, 880, 44, CREAM, hot=True)


def frame(t):
    img = Image.new("RGB", (W, H), BG)
    if t < OUTRO + 0.7:
        draw_strip(img, t)
    d = ImageDraw.Draw(img)
    draw_words(d, t)
    draw_outro(d, t)
    arr = np.asarray(img, np.float32)
    arr += LEAK * (0.5 + 0.5 * math.sin(t * 1.3))
    # film-gate flicker on every cut, faster during the rewind
    since = min(t - s[0] for s in SEGMENTS if s[0] <= t)
    if since < 0.07:
        arr *= 1.22
    if REWIND[0] <= t < REWIND[1]:
        arr *= 1.0 + 0.14 * math.sin(t * 60)
    arr += GRAIN[int(t * FPS) % len(GRAIN)][..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def init():
    global FRAMES, LEAK, GRAIN
    FRAMES = [film_frame(i) for i in range(5)]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    LEAK = (np.exp(-(((xx - W * 1.02) / 420) ** 2 + ((yy - H * 0.3) / 500) ** 2))[..., None]
            * np.array([90, 40, 0], np.float32))
    rng = np.random.default_rng(3)
    GRAIN = [rng.normal(0, 6, (H // 2, W // 2)).astype(np.float32).repeat(2, 0).repeat(2, 1) for _ in range(8)]


def render(i):
    return np.asarray(frame(i / FPS)).tobytes()


def main():
    os.makedirs(OUT, exist_ok=True)
    if "--preview" in sys.argv:
        init()
        pdir = os.path.join(OUT, "preview")
        os.makedirs(pdir, exist_ok=True)
        for ts in [float(a) for a in sys.argv[sys.argv.index("--preview") + 1:]] or [0.0, 14.5, 18.0, 21.8, 23.5,
                                                                                     26.5, 29.5, 42]:
            frame(ts).save(os.path.join(pdir, f"fk_t{ts:05.1f}.jpg"), quality=88)
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
    frame(1.0).save(os.path.join(OUT, NAME + "_cover.jpg"), quality=92)
    print("wrote", out)


if __name__ == "__main__":
    main()
