#!/usr/bin/env python3
"""Reel for "Painting My Way Back to Myself — Day 1" (self portrait).

A 1080x1920 progress reel built from the colour-corrected photos in
day1_self_portrait/corrected/. Each photo is cropped to the artwork so the
portrait stays in roughly the same place, shown as a white-bordered print on
paper, and crossfades into the next stage with a slow push-in. Captions are
hand-lettered (Permanent Marker / Caveat). It has a silent audio track, so you
can add music in Instagram.

Usage:  python3 make_day1_reel.py                 # renders output/day1_self_portrait_reel.mp4
        python3 make_day1_reel.py --landscape     # 1920x1080 -> output/day1_self_portrait_landscape.mp4
        python3 make_day1_reel.py --landscape --no-captions   # no on-screen text, print centred
                                                  # (both flags also work with --preview)
        python3 make_day1_reel.py --crops         # contact sheet of the crops -> output/preview/
        python3 make_day1_reel.py --preview 1 9.5 # stills at the given seconds -> output/preview/
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "day1_self_portrait", "corrected")
FONTS = os.path.join(ROOT, "fonts")
OUT = os.path.join(ROOT, "output")
PREVIEW = os.path.join(OUT, "preview")

LANDSCAPE = "--landscape" in sys.argv
NO_TEXT = "--no-captions" in sys.argv     # picture and voice-over only, no on-screen text
SUFFIX = ("_landscape" if LANDSCAPE else "") + ("_nocaptions" if NO_TEXT else "")
W, H = (1920, 1080) if LANDSCAPE else (1080, 1920)
FPS = 30

PAPER = (247, 243, 236)
INK = (30, 28, 30)
RED = (196, 30, 52)          # hibiscus red from the painting
TEAL = (22, 120, 130)        # mosaic teal
PURPLE = (130, 80, 190)      # hair purple

# Print layout: photo window (4:5) with a white mount around it.
if LANDSCAPE:
    # print on the left, text column on the right
    PH_W, PH_H = 760, 950
    PH_X, PH_Y = ((W - PH_W) // 2 if NO_TEXT else 170), (H - PH_H) // 2
    TX = (PH_X + PH_W + 22 + W) // 2          # centre of the text column
    POS = dict(title1=250, title2=345, stamp=540, sub=625, dots=395, day_small=430, cap=520,
               out_day=290, out1=450, out2=545, out3=700)
else:
    PH_W, PH_H = 900, 1125
    PH_X, PH_Y = (W - PH_W) // 2, 330
    TX = W // 2
    below = PH_Y + PH_H
    POS = dict(title1=78, title2=170, stamp=below + 100, sub=below + 150, dots=160, day_small=200,
               cap=below + 70, out_day=110, out1=below + 55, out2=below + 150, out3=185)
MOUNT = 22
CROP_SCALE = 1.08            # crops are made this much bigger, for the push-in

# Artwork crop per photo: (centre x, centre y, width) in the coordinates of the
# photo scaled to DISP_W wide. Height follows from the 4:5 window.
DISP_W = {"09": 1500, "15": 1424, "16": 1692, "17": 1692}
VOICEOVER = os.path.join(ROOT, "day1_self_portrait", "voiceover.m4a")
CROPS = {
    "01": (625, 940, 1000), "02": (630, 1025, 1000), "03": (675, 965, 900),
    "04": (700, 895, 880), "05": (757, 975, 900), "06": (690, 895, 1050),
    "07": (700, 1010, 900), "08": (680, 915, 1080), "09": (750, 900, 1400),
    "10": (690, 900, 1040), "11": (740, 850, 1450), "12": (760, 870, 1340),
    "13": (825, 800, 1330), "14": (815, 800, 1350), "15": (725, 900, 1240),
    "16": (857, 1005, 1330), "17": (848, 1020, 1300),
    # close-ups of the finished piece for the voice-over's closing section
    "17:eye": (660, 930, 620), "17:flower": (1010, 1060, 780), "17:bud": (1050, 560, 660),
    "17:tiles": (560, 610, 660), "17:leaves": (880, 1420, 680),
}

# Timeline: (photo, hold seconds, caption). Captions persist across photos
# until the caption text changes. 16 is skipped: it is the same finished piece
# as 17, before editing.
# Timeline, timed to the voice-over. Its pauses fall at ~5.2, 12.2, 34.2, 49.1
# and 67.9 s, and each section of the painting starts on one of them.
# (shot, hold seconds, caption). A caption stays up while consecutive shots
# share it; "" shows none. "NN:part" is a close-up of photo NN (see CROPS).
# 16 is skipped: it is the same finished piece as 17, before editing.
INTRO = 5.2
XFADE = 0.5
STEPS = [
    ("01", 3.5, "it starts with a line"),           # 5.2
    ("02", 3.5, "the first red"),
    ("03", 5.5, "a hibiscus blooms"),               # 12.2
    ("04", 5.5, "a hibiscus blooms"),
    ("05", 5.5, "a hibiscus blooms"),
    ("06", 5.5, "leaves & a bud"),
    ("07", 5.0, "hair, skin, glasses"),             # 34.2
    ("08", 5.0, "hair, skin, glasses"),
    ("09", 4.9, "one eye open"),
    ("10", 3.8, "mosaic, tile by tile"),            # 49.1
    ("11", 3.6, "mosaic, tile by tile"),
    ("12", 3.6, "mosaic, tile by tile"),
    ("13", 3.8, "mosaic, tile by tile"),
    ("14", 4.0, "mosaic, tile by tile"),
    ("15", 4.5, "almost there..."),                 # 67.9
    ("17", 5.0, "me."),
    ("17:eye", 5.0, ""),
    ("17:flower", 5.5, ""),
    ("17:bud", 4.5, ""),
    ("17:tiles", 5.0, ""),
    ("17:leaves", 4.5, ""),
    ("17", 3.6, "me."),
]
OUTRO = 5.0


# --------------------------------------------------------------------------- fonts

def caveat(size, weight="Bold"):
    f = ImageFont.truetype(os.path.join(FONTS, "Caveat.ttf"), size)
    f.set_variation_by_name(weight)
    return f


def marker(size):
    return ImageFont.truetype(os.path.join(FONTS, "PermanentMarker-Regular.ttf"), size)


# --------------------------------------------------------------------------- easing

def clamp(x):
    return max(0.0, min(1.0, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


# --------------------------------------------------------------------------- assets

def crop_photo(key):
    name = key.split(":")[0]
    path = next(os.path.join(SRC, f) for f in os.listdir(SRC) if f.startswith(name + "."))
    im = Image.open(path).convert("RGB")
    s = im.width / DISP_W.get(name, 1500)
    cx, cy, cw = (v * s for v in CROPS[key])
    cw *= CROP_SCALE
    ch = cw * PH_H / PH_W
    # keep the box inside the photo
    if cw > im.width:
        cw, ch = im.width, im.width * PH_H / PH_W
    if ch > im.height:
        ch, cw = im.height, im.height * PH_W / PH_H
    x0 = min(max(cx - cw / 2, 0), im.width - cw)
    y0 = min(max(cy - ch / 2, 0), im.height - ch)
    box = tuple(int(round(v)) for v in (x0, y0, x0 + cw, y0 + ch))
    out_w = int(PH_W * CROP_SCALE)
    return im.crop(box).resize((out_w, int(out_w * PH_H / PH_W)), Image.LANCZOS)


def paper_bg():
    rng = np.random.default_rng(7)
    base = np.empty((H, W, 3), np.float32)
    base[:] = PAPER
    blot = rng.normal(0, 1, (H // 24 + 2, W // 24 + 2)).astype(np.float32)
    blot = np.array(Image.fromarray(blot).resize((W, H), Image.BICUBIC))
    fine = rng.normal(0, 1, (H, W)).astype(np.float32)
    base += (blot * 3.5 + fine * 2.5)[..., None]
    yy, xx = np.mgrid[0:H, 0:W]
    vig = 1 - 0.10 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2
    return Image.fromarray(np.clip(base * vig[..., None], 0, 255).astype(np.uint8))


def mount_shadow():
    """White mount plus soft drop shadow, as one RGBA layer."""
    pad = 60
    w, h = PH_W + 2 * MOUNT, PH_H + 2 * MOUNT
    layer = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("L", layer.size, 0)
    ImageDraw.Draw(sh).rectangle([pad + 6, pad + 16, pad + w + 6, pad + h + 16], fill=95)
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    layer.paste((40, 30, 30, 255), (0, 0), sh)
    ImageDraw.Draw(layer).rectangle([pad, pad, pad + w - 1, pad + h - 1], fill=(255, 255, 255, 255))
    return layer, (PH_X - MOUNT - pad, PH_Y - MOUNT - pad)


def text_layer(text, font, fill, stroke=0, stroke_fill=None):
    l, t, r, b = font.getbbox(text, stroke_width=stroke)
    im = Image.new("RGBA", (r - l + 20, b - t + 20), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10 - l, 10 - t), text, font=font, fill=fill,
                            stroke_width=stroke, stroke_fill=stroke_fill)
    return im


def scribble_underline(width, color, seed, thick=9):
    rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (width + 20, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    xs = np.linspace(10, width + 10, 24)
    ys = 20 + np.cumsum(rng.normal(0, 0.9, xs.size)) + np.sin(np.linspace(0, 3, xs.size)) * 3
    d.line(list(zip(xs, ys)), fill=color, width=thick, joint="curve")
    return im


# --------------------------------------------------------------------------- timeline

class Timeline:
    def __init__(self):
        self.shots = []      # (start, end, name)
        t = INTRO
        for name, hold, cap in STEPS:
            self.shots.append((t, t + hold, name, cap))
            t += hold
        self.reveal = self.shots[-1][0]
        self.duration = t + OUTRO
        # stretch the last hold so the video ends with the voice-over
        vo = voiceover_duration()
        if vo and vo > self.duration:
            a, b, name, cap = self.shots[-1]
            self.shots[-1] = (a, b + vo - self.duration, name, cap)
            self.duration = vo

    def shot_at(self, t):
        for i, (a, b, name, cap) in enumerate(self.shots):
            if a <= t < b:
                return i
        return len(self.shots) - 1 if t >= self.shots[-1][0] else None

    def caption_start(self, i):
        """When the caption shown during shot i first appeared."""
        cap = self.shots[i][3]
        while i > 0 and self.shots[i - 1][3] == cap:
            i -= 1
        return self.shots[i][0]


def voiceover_duration():
    if not os.path.exists(VOICEOVER):
        return None
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          VOICEOVER], capture_output=True, text=True).stdout
    return float(out)


ASSETS = {}


def setup():
    names = list(dict.fromkeys(s[0] for s in STEPS))
    with Pool(min(8, os.cpu_count())) as pool:
        crops = pool.map(crop_photo, names)
    ASSETS["photos"] = dict(zip(names, crops))
    ASSETS["bg"] = paper_bg()
    ASSETS["mount"] = mount_shadow()
    ASSETS["title1"] = text_layer("Painting my way", marker(78), INK)
    ASSETS["title2"] = text_layer("back to myself", marker(78), INK)
    ASSETS["day"] = text_layer("DAY 1", marker(64), RED)
    ASSETS["day_small"] = text_layer("DAY 1  ·  self portrait", caveat(58), INK)
    ASSETS["sub"] = text_layer("a self portrait", caveat(70), INK)
    caps = {}
    for _, _, cap in STEPS:
        if cap and cap not in caps:
            caps[cap] = text_layer(cap, caveat(96 if cap != "me." else 130), INK)
    ASSETS["caps"] = caps
    ASSETS["underline"] = scribble_underline(330, RED, 3)
    ASSETS["outro1"] = text_layer("day 1 of showing up", caveat(84), INK)
    ASSETS["outro2"] = text_layer("for myself", caveat(84), INK)
    ASSETS["outro3"] = text_layer("see you tomorrow  ->", caveat(62), TEAL)
    ASSETS["tl"] = Timeline()


def paste_alpha(canvas, layer, xy, alpha=1.0):
    if alpha <= 0:
        return
    if alpha < 1:
        layer = layer.copy()
        a = layer.getchannel("A").point(lambda v: int(v * alpha))
        layer.putalpha(a)
    canvas.alpha_composite(layer, (int(xy[0]), int(xy[1])))


def centered(layer, y, dx=0):
    return (TX - layer.width // 2 + dx, y)


def photo_frame(name, local_t, hold):
    """Photo with a slow push-in over its hold (plus the crossfade tail)."""
    src = ASSETS["photos"][name]
    p = clamp(local_t / (hold + XFADE))
    z = 1.0 + (CROP_SCALE - 1.0) * p
    cw, ch = src.width / z, src.height / z
    x0, y0 = (src.width - cw) / 2, (src.height - ch) / 2
    return src.resize((PH_W, PH_H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))


def render(frame):
    t = frame / FPS
    tl = ASSETS["tl"]
    canvas = ASSETS["bg"].copy().convert("RGBA")

    # ---- the print (mount + photo)
    final_name = "17"
    mount, mxy = ASSETS["mount"]
    if t < INTRO:
        # hook: the finished piece first, settling into place
        k = ease_out(t / 0.6)
        canvas.alpha_composite(mount, mxy)
        src = ASSETS["photos"][final_name]
        z = CROP_SCALE - (CROP_SCALE - 1.0) * ease_out(t / INTRO)
        cw, ch = src.width / z, src.height / z
        x0, y0 = (src.width - cw) / 2, (src.height - ch) / 2
        img = src.resize((PH_W, PH_H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
        # dip to white just before the line drawing
        if t > INTRO - 0.4:
            img = Image.blend(img, Image.new("RGB", img.size, "white"), ease_in_out((t - (INTRO - 0.4)) / 0.4))
        canvas.paste(img, (PH_X, PH_Y))
        if k < 1:
            # quick fade-in from paper on the very first frames
            canvas = Image.blend(ASSETS["bg"].convert("RGBA"), canvas, k)
    else:
        canvas.alpha_composite(mount, mxy)
        i = tl.shot_at(t)
        a, b, name, cap = tl.shots[i]
        img = photo_frame(name, t - a, b - a)
        if i > 0 and t - a < XFADE:
            pa, pb, pname, _ = tl.shots[i - 1]
            prev = photo_frame(pname, t - pa, pb - pa)
            img = Image.blend(prev, img, ease_in_out((t - a) / XFADE))
        elif i == 0 and t - a < 0.3:
            img = Image.blend(Image.new("RGB", img.size, "white"), img, ease_in_out((t - a) / 0.3))
        canvas.paste(img, (PH_X, PH_Y))

    if NO_TEXT:
        return np.asarray(canvas.convert("RGB")).tobytes()

    # ---- header
    if t < INTRO:
        k1, k2 = ease_out((t - 0.15) / 0.5), ease_out((t - 0.4) / 0.5)
        paste_alpha(canvas, ASSETS["title1"], centered(ASSETS["title1"], POS["title1"] + 30 * (1 - k1)), k1)
        paste_alpha(canvas, ASSETS["title2"], centered(ASSETS["title2"], POS["title2"] + 30 * (1 - k2)), k2)
        kd = ease_out((t - 0.8) / 0.4)
        day = ASSETS["day"].rotate(-6 + 0 * kd, expand=True, resample=Image.BICUBIC)
        sc = 1.6 - 0.6 * kd
        if kd > 0:
            day = day.resize((int(day.width * sc), int(day.height * sc)), Image.BICUBIC)
            paste_alpha(canvas, day, (TX - day.width // 2, POS["stamp"] - day.height // 2), kd)
        ks = ease_out((t - 1.1) / 0.5)
        paste_alpha(canvas, ASSETS["sub"], centered(ASSETS["sub"], POS["sub"]), ks)
    elif t < tl.duration - OUTRO:
        k = ease_out((t - INTRO) / 0.5)
        paste_alpha(canvas, ASSETS["day_small"], centered(ASSETS["day_small"], POS["day_small"] - 20 * (1 - k)), k)
        # progress dots
        i = tl.shot_at(t)
        stages = list(dict.fromkeys(sh[2].split(":")[0] for sh in tl.shots))
        i = stages.index(tl.shots[i][2].split(":")[0])
        n = len(stages)
        gap = 46
        x0 = TX - (n - 1) * gap // 2
        d = ImageDraw.Draw(canvas)
        for j in range(n):
            x, y = x0 + j * gap, POS["dots"]
            r = 9 if j <= i else 7
            col = RED if j <= i else (205, 198, 190)
            if k > 0:
                d.ellipse([x - r, y - r, x + r, y + r], fill=col + (int(255 * k),))

    # ---- step captions
    if INTRO <= t < tl.duration - OUTRO + 0.3:
        i = tl.shot_at(t)
        cap = tl.shots[i][3]
        cs = tl.caption_start(i)
        layer = ASSETS["caps"].get(cap)
        kin = ease_out((t - cs) / 0.35)
        kout = 1 - ease_in_out((t - (tl.duration - OUTRO)) / 0.3) if t >= tl.duration - OUTRO else 1
        y = POS["cap"] + 30 * (1 - kin)
        if layer is not None:
            paste_alpha(canvas, layer, centered(layer, y), kin * kout)
        if cap == "me.":
            ku = clamp((t - cs - 0.4) / 0.5)
            ul = ASSETS["underline"]
            if ku > 0:
                part = ul.crop((0, 0, max(1, int(ul.width * ku)), ul.height))
                paste_alpha(canvas, part, (TX - ul.width // 2, y + layer.height - 18), kout)

    # ---- outro: text over the finished print
    if t >= tl.duration - OUTRO:
        lt = t - (tl.duration - OUTRO)
        k1, k2, k3 = (ease_out((lt - d) / 0.5) for d in (0.2, 0.5, 0.9))
        paste_alpha(canvas, ASSETS["outro1"], centered(ASSETS["outro1"], POS["out1"] + 25 * (1 - k1)), k1)
        paste_alpha(canvas, ASSETS["outro2"], centered(ASSETS["outro2"], POS["out2"] + 25 * (1 - k2)), k2)
        paste_alpha(canvas, ASSETS["outro3"], centered(ASSETS["outro3"], POS["out3"] + 20 * (1 - k3)), k3)
        paste_alpha(canvas, ASSETS["day_small"], centered(ASSETS["day_small"], POS["out_day"]), 1.0)

    return np.asarray(canvas.convert("RGB")).tobytes()


def crops_sheet():
    names = list(CROPS)
    thumbs = [crop_photo(n).resize((240, 300), Image.LANCZOS) for n in names]
    sheet = Image.new("RGB", (6 * 250, ((len(thumbs) + 5) // 6) * 330), "white")
    d = ImageDraw.Draw(sheet)
    for i, (n, th) in enumerate(zip(names, thumbs)):
        x, y = (i % 6) * 250 + 5, (i // 6) * 330 + 25
        sheet.paste(th, (x, y))
        d.text((x, y - 18), n, fill=(0, 0, 0))
    os.makedirs(PREVIEW, exist_ok=True)
    sheet.save(os.path.join(PREVIEW, "day1_crops.jpg"), quality=88)
    print("wrote", os.path.join(PREVIEW, "day1_crops.jpg"))


def main():
    if "--crops" in sys.argv:
        crops_sheet()
        return
    setup()
    tl = ASSETS["tl"]
    if "--preview" in sys.argv:
        os.makedirs(PREVIEW, exist_ok=True)
        times = [float(a) for a in sys.argv[sys.argv.index("--preview") + 1:]] or \
                [0.3, 1.5, 2.9, 5, 9, 13.5, 18, 21.5, 24, tl.duration - 1]
        for ts in times:
            Image.frombytes("RGB", (W, H), render(int(ts * FPS))).save(
                os.path.join(PREVIEW, f"day1{SUFFIX}_t{ts:05.2f}.jpg"), quality=88)
        print("previews in", PREVIEW)
        return
    os.makedirs(OUT, exist_ok=True)
    n = int(round(tl.duration * FPS))
    out = os.path.join(OUT, f"day1_self_portrait{SUFFIX or '_reel'}.mp4")
    if os.path.exists(VOICEOVER):
        # voice-over, levelled for Instagram (-14 LUFS) with a short fade at the end
        audio_in = ["-i", VOICEOVER]
        audio_filter = (f"loudnorm=I=-14:TP=-1.5:LRA=11,"
                        f"afade=t=out:st={tl.duration - 0.6:.2f}:d=0.6,aresample=44100")
    else:
        audio_in = ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
        audio_filter = "anull"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", *audio_in, "-af", audio_filter,
           "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out]
    print(" ".join(cmd[-14:]))
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for i, buf in enumerate(pool.imap(render, range(n), chunksize=4)):
            proc.stdin.write(buf)
            if i % 90 == 0:
                print(f"frame {i}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()
    Image.frombytes("RGB", (W, H), render(int(1.6 * FPS))).save(
        os.path.join(OUT, f"day1{SUFFIX}_cover.jpg"), quality=92)
    print(f"wrote {out} ({tl.duration:.1f}s)")


if __name__ == "__main__":
    main()
