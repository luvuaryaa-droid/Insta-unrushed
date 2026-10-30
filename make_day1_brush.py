#!/usr/bin/env python3
""""Painting my way back to Myself - Day 1", brush-reveal version.

Same seven graded progress photos as make_day1.py, but each stage is painted on
over the last one with back-and-forth brush strokes, the painting runs the full
width of the frame, and the title writes itself on by hand.

Usage:  python3 make_day1_brush.py            # renders output/day1_brush.mp4 + output/day1_brush_cover.jpg
        python3 make_day1_brush.py --preview  # writes a few stills to output/preview/
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from make_day1 import (BUTTER, CREAM, OUT, PLUM, SNOW, STAGES, H, W, background,
                       caveat, cover, grade, heart, learn_grade, load_crop)

FPS = 30
SIZE = W                 # painting is full width, square
TOP = 560                # y of the painting's top edge
INTRO = 1.6              # title writes on before the first stage
BRUSH = 1.25             # time to paint one stage on
HOLD = 1.15              # time each stage sits finished
FINAL_HOLD = 4.2


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


# --------------------------------------------------------------------------- brush strokes

class BrushPath:
    """A back-and-forth zigzag of fat, ragged strokes that covers the square."""
    LO = 270  # masks are drawn small, then scaled up and softened

    def __init__(self, seed):
        rng = np.random.default_rng(seed)
        s = self.LO
        rows = 4
        pts = []
        for r in range(rows):
            y = (r + 0.5) * s / rows + rng.uniform(-6, 6)
            xs = np.linspace(-20, s + 20, 40)
            if r % 2:
                xs = xs[::-1]
            tilt = rng.uniform(-10, 10)
            for i, x in enumerate(xs):
                pts.append((x, y + tilt * (x / s - 0.5) + math.sin(i * 0.5 + r) * 3))
        self.pts = pts
        self.radius = s / rows * 0.78
        self.jitter = rng.uniform(0.82, 1.08, len(pts))
        # a few bristle tracks offset from the stroke centre
        self.bristles = [(rng.uniform(-1, 1) * self.radius * 0.95, rng.uniform(0.10, 0.22))
                         for _ in range(10)]

    def mask(self, p):
        """L-mode mask (SIZE x SIZE) with fraction p of the path painted."""
        if p <= 0:
            return Image.new("L", (SIZE, SIZE), 0)
        if p >= 1:
            return Image.new("L", (SIZE, SIZE), 255)
        s = self.LO
        m = Image.new("L", (s, s), 0)
        d = ImageDraw.Draw(m)
        n = max(1, int(len(self.pts) * p))
        for i in range(n):
            x, y = self.pts[i]
            r = self.radius * self.jitter[i] * (0.55 if i == n - 1 else 1.0)
            d.ellipse((x - r, y - r * 0.72, x + r, y + r * 0.72), fill=255)
            for off, br in self.bristles:  # ragged bristle edges
                rr = self.radius * br
                d.ellipse((x - rr, y + off * 0.9 - rr, x + rr, y + off * 0.9 + rr), fill=255)
        m = m.resize((SIZE, SIZE), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5))
        return m


def dry_brush(seed):
    """Streaky texture used to make the wet stroke edge look like bristles."""
    rng = np.random.default_rng(seed)
    t = rng.normal(0, 1, (SIZE // 3, 12)).astype(np.float32)
    t = np.array(Image.fromarray(t).resize((SIZE, SIZE), Image.BICUBIC).rotate(90))
    return np.clip(t * 60 + 128, 0, 255)


# --------------------------------------------------------------------------- title

def title_parts():
    """Title lines as separate layers so they can be written on left to right."""
    font = caveat(118)
    lines = [("Painting my way", 92), ("back to Myself", 212)]
    layers = []
    for text, y in lines:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        w = d.textlength(text, font=font)
        x0 = (W - w) / 2
        d.text((x0 + 4, y + 5), text, font=font, fill=PLUM + (90,))   # soft drop
        d.text((x0, y), text, font=font, fill=SNOW, stroke_width=4, stroke_fill=PLUM)
        layers.append((lay, x0, x0 + w))
    return layers


def write_on(layer, x0, x1, p):
    """Reveal a text layer from x0 to x1 with a soft pen edge."""
    if p <= 0:
        return None
    if p >= 1:
        return layer
    x = x0 + (x1 - x0 + 30) * p
    ramp = np.clip((x - np.arange(W)) / 30.0, 0, 1)
    m = Image.fromarray((np.tile(ramp, (H, 1)) * 255).astype(np.uint8))
    a = Image.fromarray((np.asarray(layer.split()[3]) * (np.asarray(m) / 255)).astype(np.uint8))
    out = layer.copy()
    out.putalpha(a)
    return out


def swash(p):
    """Butter-yellow brush swash that 'Day 1' sits on, painted left to right."""
    lay = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
    if p <= 0:
        return lay
    d = ImageDraw.Draw(lay)
    rng = np.random.default_rng(3)
    x0, x1 = 330, 750
    xe = x0 + (x1 - x0) * ease(p)
    for x in np.arange(x0, xe, 4):
        y = 100 + math.sin((x - x0) / 60) * 6
        r = 58 + rng.uniform(-4, 4)
        d.ellipse((x - 36, y - r, x + 36, y + r), fill=BUTTER + (255,))
    for _ in range(26):  # dry bristle streaks at the ends
        yy = 100 + rng.uniform(-55, 55)
        d.line((x0 - rng.uniform(0, 30), yy, x0 + 20, yy), fill=BUTTER + (200,), width=3)
    return lay


# --------------------------------------------------------------------------- render

class Renderer:
    def __init__(self):
        look = learn_grade()
        big = int(SIZE * 1.06)
        self.cards = []
        for i, (name, box) in enumerate(STAGES):
            im = load_crop(name, box)
            if i < len(STAGES) - 1:
                im = grade(im, look)
            self.cards.append(cover(im, big))
        self.brushes = [BrushPath(10 + i) for i in range(len(STAGES))]
        self.texture = dry_brush(5)
        self.bg = background().convert("RGBA")
        # cream "paper" strip the painting sits on, slightly torn look via blur edge
        self.title = title_parts()
        self.day_font = caveat(150)
        self.starts = []
        t = INTRO
        for i in range(len(STAGES)):
            self.starts.append(t)
            t += BRUSH + (HOLD if i < len(STAGES) - 1 else FINAL_HOLD)
        self.duration = t
        self.base = self.bg.copy()
        paper = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(paper).rectangle((0, TOP - 14, W, TOP + SIZE + 14), fill=CREAM + (255,))
        sh = Image.new("RGBA", (W, H), (40, 14, 50, 0))
        sh.putalpha(paper.split()[3].filter(ImageFilter.GaussianBlur(18)).point(lambda v: v * 0.5))
        self.base = Image.alpha_composite(Image.alpha_composite(self.base, sh), paper)

    def stage_img(self, i, t):
        """Stage i with a slow push-in from the moment it starts being painted."""
        p = ease((t - self.starts[i]) / (BRUSH + HOLD + BRUSH))
        if i == len(STAGES) - 1:
            p = ease((t - self.starts[i]) / (BRUSH + FINAL_HOLD))
        big = self.cards[i]
        n = big.size[0]
        crop = int(n - (n - SIZE * 0.96) * p)
        if i == len(STAGES) - 1:   # the finished page eases out to show all of it
            crop = int(SIZE * 0.98 + (n - SIZE * 0.98) * p)
        off = (n - crop) // 2
        return big.crop((off, off, off + crop, off + crop)).resize((SIZE, SIZE), Image.LANCZOS)

    def frame(self, t):
        img = self.base.copy()
        # painting: latest fully-painted stage underneath, the current one brushed on top
        canvas = Image.new("RGB", (SIZE, SIZE), CREAM)
        for i, s in enumerate(self.starts):
            if t < s:
                break
            p = (t - s) / BRUSH
            layer = self.stage_img(i, t)
            if p >= 1:
                canvas = layer
            else:
                m = np.asarray(self.brushes[i].mask(ease(p)), np.float32)
                # bristle streaks only where the stroke edge is partly transparent
                edge = (m > 10) & (m < 245)
                m = np.where(edge, np.clip(m + (self.texture - 128) * 1.4, 0, 255), m)
                canvas = Image.composite(layer, canvas, Image.fromarray(m.astype(np.uint8)))
        img.paste(canvas, (0, TOP))
        # title writes on, line by line
        for k, (lay, x0, x1) in enumerate(self.title):
            part = write_on(lay, x0, x1, (t - 0.1 - k * 0.55) / 0.6)
            if part is not None:
                img.alpha_composite(part)
        # Day 1 on a yellow swash
        sp = (t - 1.15) / 0.45
        if sp > 0:
            img.alpha_composite(swash(sp), (0, 352))
            d = ImageDraw.Draw(img)
            a = int(255 * ease((t - 1.35) / 0.3))
            if a > 0:
                txt = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
                td = ImageDraw.Draw(txt)
                tw = td.textlength("Day 1", font=self.day_font)
                td.text(((W - tw) / 2, 0), "Day 1", font=self.day_font, fill=PLUM + (a,))
                img.alpha_composite(txt, (0, 352))
                for cx in (275, W - 275):
                    heart(d, cx, 457, 18, (196, 52, 62)) if a > 128 else None
        # stage counter, bottom
        cur = sum(1 for s in self.starts if t >= s)
        if cur:
            d = ImageDraw.Draw(img)
            f = caveat(84)
            label = "finished!" if cur == len(STAGES) and t > self.starts[-1] + BRUSH else f"stage {cur} of {len(STAGES)}"
            tw = d.textlength(label, font=f)
            d.text(((W - tw) / 2, TOP + SIZE + 64), label, font=f, fill=SNOW,
                   stroke_width=3, stroke_fill=PLUM)
        return img.convert("RGB")


def render():
    r = Renderer()
    path = os.path.join(OUT, "day1_brush.mp4")
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
    r.frame(r.duration - 0.5).save(os.path.join(OUT, "day1_brush_cover.jpg"), quality=92)
    print(f"wrote {path} ({frames / FPS:.1f}s)")


def preview():
    r = Renderer()
    d = os.path.join(OUT, "preview")
    os.makedirs(d, exist_ok=True)
    for t in [0.5, 1.4, 2.2, 3.4, 8.9, r.duration - 0.5]:
        r.frame(t).save(os.path.join(d, f"brush_{t:05.1f}.jpg"), quality=88)
    print("previews in", d)


if __name__ == "__main__":
    preview() if "--preview" in sys.argv else render()
