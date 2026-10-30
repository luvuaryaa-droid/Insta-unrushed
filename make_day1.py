#!/usr/bin/env python3
""""Painting my way back to Myself - Day 1": a progress reel of the cosy-winter page.

The seven progress photos (artworks/day1/stage1..7.jpg) cross-fade from the first
pair of socks to the finished page, under a hand-lettered title. Every photo gets
the same colour grade as the edited final picture (stage7): the grade is learned
by matching the colour distribution of the unedited finished photo (stage6) to
the edited one, so the early stages carry that same warm, saturated look.

Usage:  python3 make_day1.py            # renders output/day1_progress.mp4 + output/day1_cover.jpg
        python3 make_day1.py --preview  # writes a few stills to output/preview/
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "artworks", "day1")
FONTS = os.path.join(ROOT, "fonts")
OUT = os.path.join(ROOT, "output")

W, H = 1080, 1920
FPS = 30

# Colours picked from the graded final painting
LAVENDER = (166, 128, 222)
PLUM = (74, 30, 72)
BUTTER = (247, 214, 120)
SNOW = (250, 244, 236)
CREAM = (252, 240, 214)

# (file, crop box as fractions l, t, r, b) - crops trim desk/table edges
STAGES = [
    ("stage1.jpg", (0.00, 0.12, 0.92, 0.95)),
    ("stage2.jpg", (0.02, 0.30, 0.93, 0.92)),
    ("stage3.jpg", (0.02, 0.24, 0.94, 1.00)),
    ("stage4.jpg", (0.02, 0.03, 0.92, 0.97)),
    ("stage5.jpg", (0.05, 0.05, 0.97, 0.97)),
    ("stage6.jpg", (0.03, 0.02, 0.92, 0.99)),
    ("stage7.jpg", (0.05, 0.05, 0.95, 0.95)),
]

CARD = 940          # painting card size (square)
HOLD = 1.9          # seconds each progress stage is fully visible
FADE = 0.6          # cross-fade length
FINAL_HOLD = 4.5    # the finished page lingers
INTRO = 0.8         # title alone before the first painting


def caveat(size, weight="Bold"):
    f = ImageFont.truetype(os.path.join(FONTS, "Caveat.ttf"), size)
    f.set_variation_by_name(weight)
    return f


# --------------------------------------------------------------------------- colour grade

def learn_grade():
    """Strength of the final edit, measured from the unedited vs edited finished page."""
    raw = np.asarray(load_crop("stage6.jpg", (0.03, 0.02, 0.92, 0.99))).astype(np.float32)
    ref = np.asarray(load_crop("stage7.jpg", (0.06, 0.06, 0.94, 0.94))).astype(np.float32)

    def chroma(a):
        return (a.max(2) - a.min(2)).mean()
    return {"sat": float(np.clip(chroma(ref) / chroma(raw), 1.2, 1.4))}


def grade(img, look):
    """Warm, punchy look of the edited final: clean warm paper, deep inks, rich colour."""
    a = np.asarray(img).astype(np.float32)
    # white balance: the bright paper becomes a warm white
    hi = np.percentile(a.reshape(-1, 3), 96, axis=0)
    a = a * (np.array([248.0, 240.0, 224.0]) / np.maximum(hi, 1))
    a = np.clip(a, 0, 255) / 255
    # S-curve contrast with deeper darks
    a = np.clip((a - 0.06) / 0.94, 0, 1)
    a = a + 0.35 * a * (1 - a) * (2 * a - 1)
    a = a ** 1.25
    # saturation boost, kept off near-white paper so it stays clean
    grey = a.mean(2, keepdims=True)
    chroma = a.max(2, keepdims=True) - a.min(2, keepdims=True)
    paper = np.clip((grey - 0.80) / 0.15, 0, 1) * np.clip(1 - chroma / 0.12, 0, 1)
    boost = 1 + (look["sat"] - 1) * (1 - paper)
    a = grey + (a - grey) * boost
    # the final edit pushes the lavender ground to a deeper violet
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    violet = (np.clip((b - g) / 0.12, 0, 1) * np.clip((r - g + 0.02) / 0.08, 0, 1))[..., None]
    grey = a.mean(2, keepdims=True)
    a = a * (1 - violet) + (grey + (a - grey) * 1.6) * 0.9 * violet
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


# --------------------------------------------------------------------------- images

def load_crop(name, box):
    im = Image.open(os.path.join(SRC, name)).convert("RGB")
    if box:
        w, h = im.size
        im = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
    return im


def cover(im, size):
    w, h = im.size
    s = max(size / w, size / h)
    im = im.resize((max(size, round(w * s)), max(size, round(h * s))), Image.LANCZOS)
    w, h = im.size
    l, t = (w - size) // 2, (h - size) // 2
    return im.crop((l, t, l + size, t + size))


def rounded_mask(size, r):
    m = Image.new("L", (size * 2, size * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size * 2 - 1, size * 2 - 1), r * 2, fill=255)
    return m.resize((size, size), Image.LANCZOS)


def build_cards(look):
    """Each stage as a large square (extra margin so it can slowly zoom)."""
    big = int(CARD * 1.08)
    cards = []
    for i, (name, box) in enumerate(STAGES):
        im = load_crop(name, box)
        if i < len(STAGES) - 1:      # the last one is the edited reference itself
            im = grade(im, look)
        cards.append(cover(im, big))
    return cards


# --------------------------------------------------------------------------- background + title

def background():
    rng = np.random.default_rng(7)
    base = np.empty((H, W, 3), np.float32)
    base[:] = LAVENDER
    # soft marker-stroke blotches like the painted background
    blot = rng.normal(0, 1, (H // 40 + 2, W // 40 + 2)).astype(np.float32)
    blot = np.array(Image.fromarray(blot).resize((W, H), Image.BICUBIC))
    streak = rng.normal(0, 1, (H // 6, 8)).astype(np.float32)
    streak = np.array(Image.fromarray(streak).resize((W, H), Image.BICUBIC))
    base += (blot * 9 + streak * 5)[..., None]
    base += rng.normal(0, 3, (H, W, 1))
    bg = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(bg)
    # butter-yellow flecks above, snow dots below - as on the painting
    for _ in range(420):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        if y < H * 0.62:
            ang = rng.uniform(-0.6, -0.2)
            ln = rng.uniform(5, 9)
            d.line((x, y, x + math.cos(ang) * ln, y + math.sin(ang) * ln), fill=BUTTER, width=4)
    for _ in range(170):
        x, y = rng.uniform(0, W), rng.uniform(H * 0.55, H)
        r = rng.uniform(5, 8)
        d.ellipse((x - r, y - r * 0.8, x + r, y + r * 0.8), fill=SNOW)
    return bg


def title_layer():
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    top = caveat(92)
    day = caveat(150)
    line1, line2, line3 = "Painting my way", "back to Myself", "Day 1"

    def centred(text, font, y, fill, stroke=0, stroke_fill=None):
        w = d.textlength(text, font=font)
        d.text(((W - w) / 2, y), text, font=font, fill=fill,
               stroke_width=stroke, stroke_fill=stroke_fill)

    # cream paper banner behind the title
    banner = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(banner)
    bd.rounded_rectangle((70, 118, W - 70, 382), 46, fill=CREAM + (240,))
    sh = banner.split()[3].filter(ImageFilter.GaussianBlur(14)).point(lambda v: v * 0.35)
    shadow = Image.new("RGBA", (W, H), PLUM + (0,))
    shadow.putalpha(sh)
    layer = Image.alpha_composite(layer, shadow.transform((W, H), Image.AFFINE, (1, 0, -6, 0, 1, -10)))
    layer = Image.alpha_composite(layer, banner)
    d = ImageDraw.Draw(layer)
    centred(line1, top, 128, PLUM)
    centred(line2, top, 230, PLUM)
    # little hearts either side of the second line, like the knit patterns
    for cx in (150, W - 150):
        heart(d, cx, 300, 20, (196, 52, 62))
    return layer, (line3, day)


def heart(d, cx, cy, s, fill):
    d.ellipse((cx - s, cy - s * 0.7, cx, cy + s * 0.3), fill=fill)
    d.ellipse((cx, cy - s * 0.7, cx + s, cy + s * 0.3), fill=fill)
    d.polygon([(cx - s * 0.97, cy - 0.05 * s), (cx + s * 0.97, cy - 0.05 * s), (cx, cy + s * 1.05)], fill=fill)


def day_badge(text, font, scale, alpha):
    """'Day 1' as a plum sticker, popped in with `scale`."""
    tmp = Image.new("RGBA", (520, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    tw = d.textlength(text, font=font)
    d.rounded_rectangle((260 - tw / 2 - 48, 40, 260 + tw / 2 + 48, 220), 80, fill=PLUM + (255,))
    d.text((260 - tw / 2, 14), text, font=font, fill=BUTTER)
    if scale != 1:
        tmp = tmp.resize((max(1, int(520 * scale)), max(1, int(260 * scale))), Image.LANCZOS)
    if alpha < 1:
        tmp.putalpha(tmp.split()[3].point(lambda v: int(v * alpha)))
    return tmp


# --------------------------------------------------------------------------- timeline

def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def back_out(t):
    t = min(max(t, 0.0), 1.0)
    c = 1.9
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def timeline():
    starts = []
    t = INTRO
    for i in range(len(STAGES)):
        starts.append(t)
        t += HOLD + FADE if i < len(STAGES) - 1 else FINAL_HOLD
    return starts, t


class Renderer:
    def __init__(self):
        look = learn_grade()
        self.cards = build_cards(look)
        self.bg = background()
        self.title, (self.day_text, self.day_font) = title_layer()
        self.mask = rounded_mask(CARD, 26)
        self.frame_mask = rounded_mask(CARD + 36, 36)
        self.starts, self.duration = timeline()
        base = self.bg.convert("RGBA")
        # white "mat" under the painting, with a soft shadow
        cx, cy = W // 2, 1000
        self.card_xy = (cx - CARD // 2, cy - CARD // 2)
        mat = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fx, fy = cx - (CARD + 36) // 2, cy - (CARD + 36) // 2
        shadow = Image.new("L", (W, H), 0)
        shadow.paste(self.frame_mask.point(lambda v: v * 0.45), (fx + 10, fy + 18))
        shadow = shadow.filter(ImageFilter.GaussianBlur(22))
        sh = Image.new("RGBA", (W, H), (40, 14, 50, 0))
        sh.putalpha(shadow)
        mat.paste(Image.new("RGBA", (CARD + 36, CARD + 36), SNOW + (255,)), (fx, fy), self.frame_mask)
        self.static = Image.alpha_composite(Image.alpha_composite(base, sh), mat)
        self.static = Image.alpha_composite(self.static, self.title)
        self.dots_y = cy + CARD // 2 + 80

    def card_at(self, i, t):
        """Stage i with a slow push-in that runs over its whole time on screen."""
        start = self.starts[i]
        span = (HOLD + 2 * FADE) if i < len(STAGES) - 1 else FINAL_HOLD + FADE
        p = min(max((t - start + FADE) / span, 0), 1)
        big = self.cards[i]
        n = big.size[0]
        z = 1.08 - 0.08 * p if i < len(STAGES) - 1 else 1.08 - 0.08 * ease(p)
        crop = min(n, int(CARD * 1.08 / z))
        off = (n - crop) // 2
        return big.crop((off, off, off + crop, off + crop)).resize((CARD, CARD), Image.LANCZOS)

    def frame(self, t):
        img = self.static.copy()
        # which stages are visible
        cur = 0
        for i, s in enumerate(self.starts):
            if t >= s:
                cur = i
        a_in = ease((t - INTRO + FADE) / FADE) if cur == 0 else 1.0
        card = self.card_at(cur, t)
        nxt = cur + 1
        if nxt < len(STAGES) and t > self.starts[nxt] - FADE:
            mix = ease((t - (self.starts[nxt] - FADE)) / FADE)
            card = Image.blend(card, self.card_at(nxt, t), mix)
            if mix > 0.5:
                cur = nxt
        if a_in > 0:
            m = self.mask if a_in >= 1 else self.mask.point(lambda v: int(v * a_in))
            img.paste(card, self.card_xy, m)
        # Day 1 badge pops in after the intro
        p = (t - 0.25) / 0.55
        if p > 0:
            badge = day_badge(self.day_text, self.day_font, max(0.05, back_out(p)), min(1, p * 2))
            bw, bh = badge.size
            img.alpha_composite(badge, (W // 2 - bw // 2, 455 - bh // 2))
        # progress dots
        d = ImageDraw.Draw(img)
        n = len(STAGES)
        gap = 46
        x0 = W / 2 - gap * (n - 1) / 2
        for i in range(n):
            x = x0 + gap * i
            r = 13 if i == cur else 9
            fill = PLUM if i <= cur else None
            d.ellipse((x - r, self.dots_y - r, x + r, self.dots_y + r), fill=fill, outline=PLUM, width=4)
        return img.convert("RGB")


def render():
    r = Renderer()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "day1_progress.mp4")
    frames = int(r.duration * FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(frames):
        proc.stdin.write(r.frame(f / FPS).tobytes())
    proc.stdin.close()
    proc.wait()
    r.frame(r.duration - 0.5).save(os.path.join(OUT, "day1_cover.jpg"), quality=92)
    print(f"wrote {path} ({frames / FPS:.1f}s)")


def preview():
    r = Renderer()
    d = os.path.join(OUT, "preview")
    os.makedirs(d, exist_ok=True)
    for t in [0.4, 1.2, 3.0, 5.6, 10.0, r.duration - 0.5]:
        r.frame(t).save(os.path.join(d, f"day1_{t:05.1f}.jpg"), quality=88)
    print("previews in", d)


if __name__ == "__main__":
    preview() if "--preview" in sys.argv else render()
