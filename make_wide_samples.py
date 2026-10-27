#!/usr/bin/env python3
"""Horizontal (1920x1080) versions of the three moka pot style samples, each opening on a hook.

The hook (first ~2.8 s) puts the half-finished sketch next to the final drawing with
"I studied finance, not art." Then the sample carries on with the story.

  cinematic : photo on a blurred backdrop, serif captions on the right
  kinetic   : huge words stack on the left, photo punch-ins on the right
  film      : a horizontal 35mm strip rewinds to the start, typewriter captions below

Usage:  python3 make_wide_samples.py [cinematic|kinetic|film ...]   -> output/samples/wide_<style>.mp4
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from make_style_samples import (HILITE, INK, INTER_BLACK, INTER_MED, PAPER, SERIF_IT, TYPEWRITER, contain,
                                cover, ease_out, ease_out_back, font, photo, smooth, text_size)

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "output", "samples")
W, H, FPS = 1920, 1080, 30
DURATION = 12.8
HOOK = "I studied finance, not art."


def fade(t, t0, t1, fin=0.6, fout=0.4):
    return smooth((t - t0) / fin) * (1 - smooth((t - (t1 - fout)) / fout))


# =========================================================================== cinematic

BLUR = {}


def backdrop(idx):
    if idx not in BLUR:
        small = cover(photo(idx), 384, 216, 1.2).filter(ImageFilter.GaussianBlur(9))
        arr = np.asarray(small.resize((W, H), Image.BICUBIC), np.float32) * 0.38
        BLUR[idx] = arr
    return BLUR[idx]


def serif_lines(img, t, lines, align="left"):
    """lines: (start, end, text, x, y, size)."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for l0, l1, txt, x, y, size in lines:
        if not (l0 <= t < l1):
            continue
        a = fade(t, l0, l1, 0.7)
        f = font(SERIF_IT, size)
        tw, th, ox, oy = text_size(d, txt, f)
        dy = 12 * (1 - ease_out((t - l0) / 0.9))
        px = x - ox if align == "left" else x - tw / 2 - ox
        d.text((px, y + dy - oy), txt, font=f, fill=(250, 246, 238, int(255 * a)))
    img.alpha_composite(layer)


def cinematic(t):
    canvas = np.zeros((H, W, 3), np.float32)
    # hook: before | after side by side
    if t < 3.2:
        a = 1 - smooth((t - 2.6) / 0.6)
        frame = np.full((H, W, 3), 10, np.float32)
        z = 1 + 0.03 * smooth(t / 3.2)
        img = Image.fromarray(frame.astype(np.uint8))
        for idx, cx in ((0, 560), (3, 1360)):
            im = contain(photo(idx), int(700 * z), int(780 * z))
            img.paste(im, (int(cx - im.width / 2), int(440 - im.height / 2)))
        d = ImageDraw.Draw(img)
        lab = font(INTER_MED, 40)
        for txt, cx in (("where I started", 560), ("where it ended up", 1360)):
            tw, th, ox, oy = text_size(d, txt, lab)
            d.text((cx - tw / 2 - ox, 848 - oy), txt, font=lab, fill=(170, 165, 158))
        canvas += np.asarray(img, np.float32) * a
    shots = [(2.6, 6.7, 0, 1.0, 1.05), (6.1, 9.9, 2, 1.05, 1.0), (9.3, DURATION, 3, 1.0, 1.04)]
    for s0, s1, idx, z0, z1 in shots:
        if not (s0 <= t < s1):
            continue
        a = smooth((t - s0) / 0.6) * (1 - smooth((t - (s1 - 0.6)) / 0.6)) if s1 < DURATION else smooth((t - s0) / 0.6)
        z = z0 + (z1 - z0) * smooth((t - s0) / (s1 - s0))
        img = Image.fromarray(backdrop(idx).astype(np.uint8))
        im = contain(photo(idx), int(760 * z), int(960 * z))
        img.paste(im, (int(660 - im.width / 2), int(H / 2 - im.height / 2)))
        canvas += np.asarray(img, np.float32) * a
    canvas = canvas * np.array([1.03, 1.0, 0.94], np.float32)
    img = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8)).convert("RGBA")
    serif_lines(img, t, [(0.3, 3.0, HOOK, W / 2, 915, 84)], align="center")
    x = 1170
    serif_lines(img, t, [
        (3.1, 6.5, "You don't need", x, 400, 96), (3.5, 6.5, "to be good", x, 520, 96),
        (4.2, 6.5, "to show your art.", x, 640, 96),
        (6.6, 9.7, "I almost didn't", x, 450, 96), (7.2, 9.7, "share any of this.", x, 570, 96),
        (9.8, DURATION + 1, "Then it", x, 450, 104), (10.3, DURATION + 1, "became this.", x, 575, 104),
    ])
    return img.convert("RGB")


# =========================================================================== kinetic

KIN = [  # (start, words, highlighted, photo, kicker)
    (0.00, ["I STUDIED", "FINANCE.", "NOT ART."], {"NOT ART."}, 3, ""),
    (2.80, ["YOU DON'T", "NEED TO", "BE GOOD"], {"BE GOOD"}, 0, ""),
    (5.00, ["TO SHOW", "YOUR ART."], {"YOUR ART."}, 0, ""),
    (6.60, ["LINES."], set(), 0, "day one"),
    (7.15, ["MARKER."], set(), 1, ""),
    (7.70, ["FILL."], set(), 2, ""),
    (8.25, ["DONE."], {"DONE."}, 3, ""),
    (8.90, ["SHOW UP", "ANYWAY."], {"ANYWAY."}, 4, "that's the whole skill."),
]
BEAT = 0.42


def kinetic(t):
    cur = max(i for i, s in enumerate(KIN) if s[0] <= t)
    s0, words, hot, idx, kicker = KIN[cur]
    lt = t - s0
    img = Image.new("RGB", (W, H), PAPER)
    # right half: photo punch-in with a flash on the cut
    z = 1.16 - 0.14 * ease_out(lt / 0.35)
    if cur == 0:   # hook: before | after
        ph = Image.new("RGB", (960, H))
        ph.paste(cover(photo(0), 480, H, z, (0.5, 0.45)), (0, 0))
        ph.paste(cover(photo(3), 480, H, z, (0.5, 0.5)), (480, 0))
    else:
        ph = cover(photo(idx), 960, H, z, (0.56 if idx == 4 else 0.5, 0.45))
    if lt < 0.05:
        ph = Image.blend(ph, Image.new("RGB", ph.size, (255, 255, 255)), 0.6)
    img.paste(ph, (960, 0))
    d = ImageDraw.Draw(img)
    if cur == 0:
        d.rectangle((1437, 0, 1443, H), fill=PAPER)
        tag = font(INTER_BLACK, 40)
        for txt, cx in (("BEFORE", 1200), ("AFTER", 1680)):
            tw, th, ox, oy = text_size(d, txt, tag)
            d.rectangle((cx - tw / 2 - 18, 950, cx + tw / 2 + 18, 950 + th + 28), fill=HILITE)
            d.text((cx - tw / 2 - ox, 964 - oy), txt, font=tag, fill=INK)
    probe = font(INTER_BLACK, 100)
    widest = max(text_size(d, w, probe)[0] for w in words)
    size = int(min(170, 100 * 780 / widest))
    f = font(INTER_BLACK, size)
    lh = int(size * 1.08)
    top = H / 2 - lh * len(words) / 2 - (30 if kicker else 0)
    x0 = 100
    beat = BEAT if len(words) > 1 else 0.12
    for i in range(min(len(words), int(lt / beat) + 1)):
        w = words[i]
        p = (lt - i * beat) / 0.16
        sc = 1 + 0.35 * (1 - ease_out_back(p, 1.2)) if p < 1 else 1.0
        fs = font(INTER_BLACK, max(10, int(size * min(sc, 1.6))))
        tw, th, ox, oy = text_size(d, w, fs)
        y = top + i * lh + (lh - th) / 2 - oy
        if w in hot:
            hw = text_size(d, w, f)[0]
            grow = ease_out((lt - i * beat) / 0.25)
            d.rectangle((x0 - 20, top + i * lh + lh * 0.06, x0 - 20 + (hw + 40) * grow, top + (i + 1) * lh - lh * 0.02),
                        fill=HILITE)
        d.text((x0 - ox, y), w, font=fs, fill=INK)
    if kicker and lt > beat * len(words):
        small = font(INTER_MED, 56)
        d.text((x0, top + lh * len(words) + 40), kicker, font=small, fill=(90, 90, 90))
    return img


# =========================================================================== film

FW, FH, GAP = 450, 600, 70
PITCH = FW + GAP
STRIP_TOP, STRIP_H = 50, 800
FILM, LEAK = None, None


def film_frame(idx):
    arr = np.asarray(cover(photo(idx), FW, FH, 1.0, (0.56 if idx == 4 else 0.5, 0.45)), np.float32)
    arr = (18 + arr * 0.9) * np.array([1.06, 1.0, 0.86], np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def film(t):
    # strip position (index of the frame in the centre): sits on the final drawing, rewinds to the start,
    # then advances frame by frame
    if t < 1.9:
        pos = 3.0
    elif t < 2.8:
        pos = 3.0 - 3.0 * smooth((t - 1.9) / 0.9)
    else:
        pos = 0.0
        for st, n in ((6.0, 1), (9.2, 2)):
            if t >= st:
                pos = (n - 1) + smooth((t - st) / 0.9)
    img = Image.new("RGB", (W, H), (14, 12, 11))
    d = ImageDraw.Draw(img)
    d.rectangle((0, STRIP_TOP, W, STRIP_TOP + STRIP_H), fill=(32, 24, 18))
    off = -pos * PITCH
    hp = PITCH / 6
    x = -((-off) % hp) - hp
    while x < W + hp:
        for hy in (STRIP_TOP + 28, STRIP_TOP + STRIP_H - 28 - 40):
            d.rounded_rectangle((x, hy, x + 56, hy + 40), 8, fill=(14, 12, 11))
        x += hp
    lab = font(INTER_MED, 26)
    fy = STRIP_TOP + (STRIP_H - FH) // 2
    for n in range(5):
        fx = W / 2 - FW / 2 + n * PITCH + off
        if fx > W or fx + FW < 0:
            continue
        img.paste(FILM[n], (int(fx), fy))
        d.text((fx + 4, fy + FH + 14), f"{n + 1}A        400", font=lab, fill=(232, 140, 50))
    arr = np.asarray(img, np.float32)
    arr += LEAK * (0.5 + 0.5 * math.sin(t * 1.3))
    if 1.9 <= t < 2.8:   # rewind: flicker brighter
        arr *= 1.0 + 0.12 * math.sin(t * 60)
    rng = np.random.default_rng(int(t * FPS))
    arr += rng.normal(0, 7, (H // 2, W // 2)).repeat(2, 0).repeat(2, 1)[..., None]
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    caps = [(0.2, 1.9, HOOK),
            (3.1, 6.0, "You don't need to be good to show your art."),
            (6.7, 9.2, "Half the page was still just lines."),
            (9.9, DURATION, "I almost didn't share any of this.")]
    f = font(TYPEWRITER, 66)
    for c0, c1, txt in caps:
        if c0 <= t < c1:
            n = int((t - c0) * 24)
            cursor = "_" if n < len(txt) or int(t * 3) % 2 == 0 else ""
            tw, th, ox, oy = text_size(d, txt, f)
            d.text(((W - tw) / 2 - ox, 935 - oy), txt[:n] + cursor, font=f, fill=(240, 230, 210))
    return img


# =========================================================================== render

STYLES = {"cinematic": cinematic, "kinetic": kinetic, "film": film}
STYLE = None


def init(style):
    global STYLE, FILM, LEAK
    STYLE = style
    FILM = [film_frame(i) for i in range(5)]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    LEAK = (np.exp(-(((xx - W * 1.02) / 420) ** 2 + ((yy - H * 0.35) / 500) ** 2))[..., None]
            * np.array([90, 40, 0], np.float32))


def render(i):
    return np.asarray(STYLES[STYLE](i / FPS).convert("RGB")).tobytes()


def main():
    os.makedirs(OUT, exist_ok=True)
    for style in sys.argv[1:] or list(STYLES):
        out = os.path.join(OUT, f"wide_{style}.mp4")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "21",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        with Pool(os.cpu_count(), initializer=init, initargs=(style,)) as pool:
            for buf in pool.imap(render, range(int(DURATION * FPS)), chunksize=4):
                proc.stdin.write(buf)
        proc.stdin.close()
        proc.wait()
        print("wrote", out, flush=True)


if __name__ == "__main__":
    main()
