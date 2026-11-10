#!/usr/bin/env python3
"""Day 6 process reel: the scooter painting, from pencil sketch to finished border.

Pipeline:  python3 align.py   (photos/ -> aligned/, paper found and flattened)
           python3 refine.py  (aligned/ -> refined/, frames matched to each other)
           python3 make_day6.py            -> output/day6_scooter.mp4 (+ cover)
           python3 make_day6.py --preview 1 8 20   -> output/preview/*.jpg

1080x1920, 30 fps, silent audio track so music can be added in Instagram.
"""
import glob, math, os, subprocess, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONTS = os.path.join(ROOT, "fonts")
OUT = os.path.join(HERE, "output")

W, H, FPS = 1080, 1920, 30
CARD = 940                       # painting size on screen
CX, CY = W // 2, 860             # painting centre

BG = (244, 236, 222)
INK = (34, 38, 36)
GREEN = (31, 104, 84)
MUSTARD = (226, 170, 52)
BRICK = (178, 62, 58)
PINK = (226, 128, 128)

# Caption for each photo (1-based index -> text shown from that photo on)
STAGES = {
    1: "pencil sketch",
    2: "adding motifs: lotus, bird, flowers",
    3: "background green",
    7: "first colours",
    10: "mustard body",
    13: "bird & patterns",
    16: "wheels, flowers & a sun",
    18: "outlines + white details",
    19: "and a border to finish",
}


def font(name, size, var=None):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    if var:
        f.set_variation_by_name(var)
    return f


F_TITLE = font("PermanentMarker-Regular.ttf", 150)
F_SUB = font("Caveat.ttf", 70, "Bold")
F_CAP = font("Caveat.ttf", 76, "Bold")
F_SMALL = font("Caveat.ttf", 54, "Regular")


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def back(t):  # overshoot pop
    t = min(max(t, 0.0), 1.0)
    s = 1.7
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


# --------------------------------------------------------------------------- assets

def load_frames():
    files = sorted(glob.glob(os.path.join(HERE, "refined", "[0-9]*.png")))
    frames = []
    for f in files:
        im = Image.open(f).convert("RGB")
        s = im.size[0]
        m = int(s * 0.012)  # trim edge smear from the perspective warp
        frames.append(im.crop((m, m, s - m, s - m)))
    return frames


def background():
    rng = np.random.default_rng(6)
    a = np.empty((H, W, 3), np.float32)
    a[:] = BG
    blot = rng.normal(0, 1, (H // 30 + 2, W // 30 + 2)).astype(np.float32)
    blot = np.array(Image.fromarray(blot).resize((W, H), Image.BICUBIC))
    a += (blot * 4 + rng.normal(0, 3, (H, W)))[..., None]
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    # a few confetti dots in the painting's colours, top and bottom
    for i in range(46):
        x = rng.uniform(30, W - 30)
        y = rng.uniform(20, 300) if i % 2 else rng.uniform(H - 330, H - 30)
        r = rng.uniform(5, 11)
        d.ellipse((x - r, y - r, x + r, y + r), fill=[GREEN, MUSTARD, BRICK, PINK][i % 4])
    return img


def shadow(size, radius=28, alpha=110):
    pad = radius * 3
    sh = Image.new("L", (size[0] + pad * 2, size[1] + pad * 2), 0)
    ImageDraw.Draw(sh).rectangle((pad, pad, pad + size[0], pad + size[1]), fill=alpha)
    return sh.filter(ImageFilter.GaussianBlur(radius)), pad


def text_center(d, xy, txt, f, fill, stroke=0, sfill=None):
    d.text(xy, txt, font=f, fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=sfill)


# --------------------------------------------------------------------------- timeline

INTRO = 2.2
HOLD = [1.3] + [0.75] * 16 + [1.1, 1.6]   # seconds each photo stays (19 photos)
XF = 0.28                                  # crossfade
DETAILS = [  # (centre x, centre y, zoom) in 0..1 coords of the final painting
    (0.27, 0.36, 2.6),   # lotus
    (0.72, 0.62, 2.5),   # bird
    (0.20, 0.76, 2.4),   # front wheel
    (0.84, 0.17, 2.1),   # sun
]
DET_T = 1.5
OUTRO = 2.8

T_PROC = INTRO
T_DET = T_PROC + sum(HOLD)
T_OUT = T_DET + DET_T * len(DETAILS)
TOTAL = T_OUT + OUTRO


class Renderer:
    def __init__(self):
        self.frames = load_frames()
        self.cards = [f.resize((CARD, CARD), Image.LANCZOS) for f in self.frames]
        self.bg = background()
        self.sh, self.shpad = shadow((CARD, CARD))
        self.starts = np.cumsum([0] + HOLD[:-1]) + T_PROC

    # paste a square image centred at (CX,CY) with given scale & rotation
    def place(self, canvas, img, scale=1.0, rot=0.0, cy=CY):
        size = int(CARD * scale)
        im = img if img.size[0] == size else img.resize((size, size), Image.LANCZOS)
        sh = self.sh.resize((size + 2 * self.shpad, size + 2 * self.shpad)) if size != CARD else self.sh
        if rot:
            im = im.convert("RGBA").rotate(rot, Image.BICUBIC, expand=True)
            sh = sh.rotate(rot, Image.BICUBIC, expand=True)
        canvas.paste((60, 40, 30), (CX - sh.size[0] // 2 + 6, cy - sh.size[1] // 2 + 14), sh)
        pos = (CX - im.size[0] // 2, cy - im.size[1] // 2)
        canvas.paste(im, pos, im if im.mode == "RGBA" else None)

    def header(self, d, t_in, sub="sketch to finish", alpha=1.0):
        k = back(t_in)
        if k <= 0:
            return
        f = font("PermanentMarker-Regular.ttf", max(10, int(150 * k)))
        text_center(d, (CX, 190), "DAY 6", f, GREEN, 5, (255, 255, 255))
        if t_in > 0.6:
            text_center(d, (CX, 300), sub, F_SUB, INK)

    def caption(self, d, txt, age):
        k = ease(age / 0.25)
        y = 1480 + int((1 - k) * 40)
        col = tuple(int(BG[i] + (INK[i] - BG[i]) * k) for i in range(3))
        text_center(d, (CX, y), txt, F_CAP, col)

    def progress(self, d, p, idx):
        x0, x1, y = 140, W - 140, 1600
        d.rounded_rectangle((x0, y - 9, x1, y + 9), 9, fill=(225, 214, 196))
        d.rounded_rectangle((x0, y - 9, x0 + max(18, int((x1 - x0) * p)), y + 9), 9, fill=MUSTARD)
        text_center(d, (CX, y + 62), f"photo {idx} / {len(self.frames)}", F_SMALL, (120, 110, 98))

    def frame(self, t):
        img = self.bg.copy()
        d = ImageDraw.Draw(img)
        final = self.frames[-1]

        if t < T_PROC:  # ---- intro: finished piece pops in, then flips to the sketch
            k = back(t / 0.6)
            self.place(img, self.cards[-1], 0.6 + 0.4 * k if t < 0.6 else 1.0 - 0.03 * ease((t - 0.6) / 1.6), rot=-4 * (1 - ease(t / 0.8)))
            d = ImageDraw.Draw(img)
            self.header(d, (t - 0.2) / 0.5)
            if t > 0.9:
                self.caption(d, "watch it come together", t - 0.9)
            return img

        if t < T_DET:  # ---- process: photo by photo
            i = int(np.searchsorted(self.starts, t, side="right") - 1)
            age = t - self.starts[i]
            cur = self.cards[i]
            if i > 0 and age < XF:
                cur = Image.blend(self.cards[i - 1], cur, ease(age / XF))
            if t - T_PROC < 0.35:  # quick cut-in from the intro
                cur = Image.blend(self.cards[-1], self.cards[0], ease((t - T_PROC) / 0.35))
            self.place(img, cur, 1.0)
            d = ImageDraw.Draw(img)
            self.header(d, 1.0)
            key = max(k for k in STAGES if k <= i + 1)
            self.caption(d, STAGES[key], t - self.starts[key - 1])
            self.progress(d, (t - T_PROC) / (T_DET - T_PROC), i + 1)
            return img

        if t < T_OUT:  # ---- detail close-ups, panning between them
            u = (t - T_DET) / DET_T
            j = min(int(u), len(DETAILS) - 1)
            fr = u - j
            a = DETAILS[j]
            b = DETAILS[j + 1] if j + 1 < len(DETAILS) else (0.5, 0.5, 1.0)
            k = ease((fr - 0.55) / 0.45)
            if j == 0:  # zoom in from full view
                a0 = (0.5, 0.5, 1.0)
                k0 = ease(fr / 0.4)
                cx, cy, z = [a0[n] + (a[n] - a0[n]) * k0 for n in range(3)]
                if fr > 0.55:
                    cx, cy, z = [a[n] + (b[n] - a[n]) * k for n in range(3)]
            else:
                cx, cy, z = [a[n] + (b[n] - a[n]) * k for n in range(3)]
            s = final.size[0]
            half = s / z / 2
            cx = min(max(cx * s, half), s - half)
            cy = min(max(cy * s, half), s - half)
            crop = final.crop((int(cx - half), int(cy - half), int(cx + half), int(cy + half)))
            self.place(img, crop.resize((CARD, CARD), Image.LANCZOS), 1.0)
            d = ImageDraw.Draw(img)
            self.header(d, 1.0)
            self.caption(d, "the little details", t - T_DET)
            return img

        # ---- outro
        u = t - T_OUT
        self.place(img, self.cards[-1], 1.0 - 0.06 * ease(u / 0.6))
        d = ImageDraw.Draw(img)
        self.header(d, 1.0, sub="done ✓" if False else "done!")
        self.caption(d, f"{len(self.frames)} photos, one happy scooter", u)
        if u > 0.9:
            k = ease((u - 0.9) / 0.4)
            col = tuple(int(BG[i] + (GREEN[i] - BG[i]) * k) for i in range(3))
            text_center(d, (CX, 1610), "see you on Day 7", F_SUB, col)
        return img


def render(preview=None):
    os.makedirs(OUT, exist_ok=True)
    r = Renderer()
    if preview:
        pd = os.path.join(OUT, "preview")
        os.makedirs(pd, exist_ok=True)
        for s in preview:
            r.frame(float(s)).save(os.path.join(pd, f"t{float(s):05.1f}.jpg"), quality=88)
        return
    n = int(round(TOTAL * FPS))
    path = os.path.join(OUT, "day6_scooter.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(n):
        p.stdin.write(r.frame(f / FPS).tobytes())
    p.stdin.close()
    p.wait()
    r.frame(T_OUT + 2.0).save(os.path.join(OUT, "day6_cover.jpg"), quality=92)
    print(f"wrote {path} ({TOTAL:.1f}s, {n} frames)")


if __name__ == "__main__":
    if "--preview" in sys.argv:
        render(sys.argv[sys.argv.index("--preview") + 1:] or ["1", "5", "15", "24", "28"])
    else:
        render()
