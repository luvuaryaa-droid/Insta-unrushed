#!/usr/bin/env python3
"""Moka pot process reel: "You don't need to be good to show your art."

Five process photos (sketch -> clipboard -> filled in -> final scan -> holding it)
told as a papercut reel. It reuses the paper sprites and renderer from make_video.py:
each photo is a torn-edged sheet that wipes over the last one with a slow push-in,
and the captions are torn paper strips.

Usage:  python3 make_process_reel.py              # renders output/moka_pot_process.mp4
        python3 make_process_reel.py --preview    # a few stills -> output/preview/
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw

import make_video as mv
from make_video import (CREAM, COBALT, INK, MUSTARD, PAPER_WHITE, SAGE, TERRACOTTA, W, H, FPS, OUT_FPS,
                        Sprite, add, add_shadow, background, caption, caveat, clamp, cutout, ease_out,
                        edge_polygon, marker, star, text_strip, torn_sheet)

ROOT = os.path.dirname(os.path.abspath(__file__))
PHOTOS = os.path.join(ROOT, "photos", "moka_pot")
OUT = os.path.join(ROOT, "output")
NAME = "moka_pot_process"


def photo_sheet(name, seed, from_dir, focus=(0.5, 0.5), pad=80):
    """Cover-crop a photo to the frame (plus zoom headroom) with a torn edge on the entering side."""
    im = Image.open(os.path.join(PHOTOS, name)).convert("RGB")
    w, h = W + pad, H + pad
    s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s + 0.5), int(im.height * s + 0.5)), Image.LANCZOS)
    left = int(clamp(focus[0] - w / im.width / 2) * im.width)
    left = min(left, im.width - w)
    top = min(int(clamp(focus[1] - h / im.height / 2) * im.height), im.height - h)
    im = im.crop((left, top, left + w, top + h)).convert("RGBA")
    if not from_dir:
        return im
    edge = {"left": "r", "right": "l", "up": "b", "down": "t"}[from_dir]
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon(edge_polygon(w, h, 26, seed, edge), fill=255)
    rim = torn_sheet(w, h, PAPER_WHITE, seed, sides=edge, amp=26, rim=False, grain=3)
    inner = Image.new("L", (w, h), 0)
    ImageDraw.Draw(inner).polygon(edge_polygon(w, h, 24, seed + 1, edge, inset=9), fill=255)
    rim.paste(im, (0, 0), inner)
    rim.putalpha(mask)
    return add_shadow(rim, 0, 0, 14, 0.45)


def photo(name, t, seed, from_dir, z, focus=(0.5, 0.5), zoom=(1.0, 1.06), hold=5.0, drift=(0, 0)):
    """A full-bleed photo that slides in and slowly pushes in for `hold` seconds."""
    img = photo_sheet(name, seed, from_dir, focus)

    def path(tt):
        k = clamp((tt - t) / hold)
        return (W / 2 + drift[0] * k, H / 2 + drift[1] * k, 0.0, zoom[0] + (zoom[1] - zoom[0]) * k)

    enter = "slide_" + from_dir if from_dir else "none"
    return add(Sprite(img, t, (W / 2, H / 2), z=z, enter=enter, enter_dur=0.55 if from_dir else 0, boil=0,
                      tilt=False, path=path))


def build():
    rng = np.random.default_rng(5)

    # ---------------- 0: hook on the half-finished sketch (0 - 4.5)
    z = 0
    photo("1_sketch.jpg", 0, 11, None, z, focus=(0.5, 0.45), zoom=(1.0, 1.08), drift=(0, 30))
    add(Sprite(text_strip("You don't need to be good", marker(68), seed=12, max_w=980), 0.25, (520, 220),
               rot=-2.5, z=z + 10, enter="slide_left", enter_dur=0.4))
    add(Sprite(text_strip("to show your art.", marker(92), paper=COBALT, ink=PAPER_WHITE, seed=13), 0.75,
               (600, 380), rot=2, z=z + 11, enter="slide_right", enter_dur=0.4))
    add(Sprite(text_strip("wobbly outlines. an empty mug.", caveat(64), paper=CREAM, seed=14,
                          max_w=880), 2.0, (540, 1700), rot=-1.5, z=z + 12, enter="pop", enter_dur=0.4))

    # ---------------- 1: clipboard, first black marker (4.5 - 8.5)
    t, z = 4.5, 100
    photo("2_clipboard.jpg", t - 0.5, 101, "right", z, focus=(0.5, 0.48), zoom=(1.04, 1.12), drift=(0, -20))
    caption("first black marker...", t + 0.1, 250, z + 10, size=80, seed=111, paper=CREAM)
    caption("half the page was still just lines.", t + 1.0, 1690, z + 11, size=76, seed=112, max_w=900)

    # ---------------- 2: spoon + fabric filled in (8.5 - 12.5)
    t, z = 8.5, 200
    photo("3_filled.jpg", t - 0.5, 201, "down", z, focus=(0.5, 0.42), zoom=(1.06, 1.0))
    add(Sprite(text_strip("I almost didn't share", marker(80), seed=211), t + 0.2, (540, 1560), rot=-2,
               z=z + 10, enter="pop", enter_dur=0.45))
    add(Sprite(text_strip("any of this.", marker(88), paper=TERRACOTTA, ink=PAPER_WHITE, seed=212),
               t + 0.8, (620, 1710), rot=2.5, z=z + 11, enter="pop", enter_dur=0.45))

    # ---------------- 3: clean final scan (12.5 - 17)
    t, z = 12.5, 300
    background(t - 0.5, MUSTARD, 301, "left", z)
    scan = Image.open(os.path.join(PHOTOS, "4_final_scan.jpg")).convert("RGB")
    card = cutout(scan, 900, 1230, 302, border=22, tape="corners", tape_color=(240, 225, 190))

    def scan_path(tt, t0=t):
        k = clamp((tt - t0) / 4.5)
        return (540, 1010, -2 + 1.5 * k, 1.0 + 0.04 * k)

    add(Sprite(card, t + 0.1, (540, 1010), z=z + 2, enter="drop", enter_dur=0.5, path=scan_path, boil=0.5))
    add(Sprite(text_strip("then it became this.", marker(88), seed=311), t + 0.9, (540, 230), rot=-2.5,
               z=z + 10, enter="slide_up", enter_dur=0.45))
    for i, (sx, sy, sc, col) in enumerate(((120, 420, 100, PAPER_WHITE), (960, 380, 110, TERRACOTTA),
                                           (110, 1720, 90, COBALT), (970, 1700, 100, PAPER_WHITE))):
        add(Sprite(star(sc, col, 320 + i), t + 1.4 + i * 0.12, (sx, sy), rot=rng.uniform(-20, 20),
                   z=z + 11, enter="pop", enter_dur=0.3))

    # ---------------- 4: holding it (17 - 21.5)
    t, z = 17.0, 400
    photo("5_holding.jpg", t - 0.5, 401, "up", z, focus=(0.58, 0.5), zoom=(1.0, 1.07), drift=(0, 20))
    add(Sprite(text_strip("show up\nanyway.", marker(84), paper=COBALT, ink=PAPER_WHITE, seed=411),
               t + 0.3, (860, 330), rot=-2.5, z=z + 10, enter="slide_left", enter_dur=0.4))
    caption("that's the whole skill.", t + 1.2, 1770, z + 11, size=88, seed=412)

    # ---------------- 5: save this list + CTA (21.5 - 29)
    t, z = 21.5, 500
    background(t - 0.5, CREAM, 501, "right", z)
    add(Sprite(text_strip("SAVE THIS", marker(96), paper=TERRACOTTA, ink=PAPER_WHITE, seed=511), t + 0.1,
               (540, 230), rot=-2, z=z + 2, enter="slide_up", enter_dur=0.4))
    caption("5 things to post when your art doesn't feel \"good enough\"", t + 0.6, 440, z + 3, size=66,
            seed=512, paper=PAPER_WHITE, max_w=860)
    tips = ["the unfinished stage", "the messy desk you made it on", "one small part you love",
            "a before + after", "the mistake you kept"]
    papers = [MUSTARD, SAGE, PAPER_WHITE, MUSTARD, SAGE]
    for i, tip in enumerate(tips):
        im = text_strip(f"{i + 1}.  {tip}", caveat(70), paper=papers[i], seed=520 + i, max_w=900)
        add(Sprite(im, t + 1.3 + i * 0.45, (540 + (-30 if i % 2 else 30), 680 + i * 175),
                   rot=rng.uniform(-2.5, 2.5), z=z + 4 + i, enter="slide_" + ("left" if i % 2 else "right"),
                   enter_dur=0.4))
    add(Sprite(text_strip("post your unfinished page this week + tag me", marker(62), paper=COBALT,
                          ink=PAPER_WHITE, seed=530, max_w=860), t + 4.0, (540, 1660), rot=-1.5,
               z=z + 12, enter="pop", enter_dur=0.45))
    add(Sprite(star(110, MUSTARD, 540), t + 4.5, (930, 1530), rot=12, z=z + 13, enter="pop", enter_dur=0.3))
    return t + 7.5


def main():
    os.makedirs(OUT, exist_ok=True)
    mv.build = build
    mv.setup()
    if "--preview" in sys.argv:
        pdir = os.path.join(OUT, "preview")
        os.makedirs(pdir, exist_ok=True)
        for ts in [float(a) for a in sys.argv[sys.argv.index("--preview") + 1:]] or [2.5, 4.1, 6.5, 10.5, 15,
                                                                                     19.5, 24, 28]:
            f = int(ts * FPS)
            Image.frombytes("RGB", (W, H), mv.render_frame(f)).save(os.path.join(pdir, f"moka_t{ts:05.1f}.jpg"),
                                                                    quality=88)
        return
    n = int(mv.DURATION * FPS)
    out = os.path.join(OUT, NAME + ".mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-r", str(OUT_FPS), "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for i, buf in enumerate(pool.imap(mv.render_frame, range(n), chunksize=4)):
            proc.stdin.write(buf)
            if i % 60 == 0:
                print(f"frame {i}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()
    cover = Image.frombytes("RGB", (W, H), mv.render_frame(int(15.5 * FPS)))
    cover.save(os.path.join(OUT, NAME + "_cover.jpg"), quality=92)
    print("wrote", out)


if __name__ == "__main__":
    main()
