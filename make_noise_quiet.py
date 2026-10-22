#!/usr/bin/env python3
""""The noise / what it quietened into": a two-page sketchbook reel.

The left page (neon fish) is shown as racing, shaky punch-in cuts. The motion
slows to a blank sheet, then the right page (ink flower) is drawn on from the
centre outwards and toured with slow, calm close-ups on its loops, dashes and
circles. It ends on the photo of the open spread and a closing card.

Captions, paper textures and sprite animation come from make_video.py.

Usage:  python3 make_noise_quiet.py                  # renders output/noise_to_quiet.mp4
        python3 make_noise_quiet.py --preview 2 9 20 # stills at the given seconds -> output/preview/
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw

import make_video as mv
from make_video import (ART, OUT, W, H, INK, PAPER_WHITE, CHARTREUSE, SAGE, Sprite,
                        add_shadow, caveat, clamp, ease_out, marker, paper_texture, text_strip)

FPS = 30
DURATION = 33.0
PAPER = (240, 234, 222)
TEAL = (24, 62, 76)
FLOWER_CENTRE = (0.42, 0.41)


def ease_in_out(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def lerp(a, b, u):
    return a + (b - a) * u


# --------------------------------------------------------------------------- camera

def shake(frame, amp, rot_amp=0.0):
    """Hand-held jitter that changes every other frame (stop-motion feel)."""
    if amp <= 0:
        return 0.0, 0.0, 0.0
    rng = np.random.default_rng(7919 + frame // 2)
    return rng.uniform(-amp, amp), rng.uniform(-amp, amp), rng.uniform(-rot_amp, rot_amp)


def view(src, cx, cy, vw, dx=0.0, dy=0.0, rot=0.0, resample=Image.BICUBIC):
    """Render a W x H window of `src` centred on normalised (cx, cy), vw = visible width fraction."""
    sw, sh = src.size
    w = vw * sw
    h = w * H / W
    x0 = min(max(cx * sw - w / 2, 0), max(sw - w, 0))
    y0 = min(max(cy * sh - h / 2, 0), max(sh - h, 0))
    s = w / W
    ccx, ccy = x0 + w / 2, y0 + h / 2
    a = math.radians(rot)
    ca, sa = math.cos(a) * s, math.sin(a) * s
    # output (u, v) -> source: centre + R * S * ((u, v) - output centre - shake)
    ou, ov = W / 2 + dx, H / 2 + dy
    coeffs = (ca, -sa, ccx - ca * ou + sa * ov,
              sa, ca, ccy - sa * ou - ca * ov)
    return src.transform((W, H), Image.AFFINE, coeffs, resample)


# --------------------------------------------------------------------------- shots

class Shot:
    def __init__(self, t0, t1, render, fade=0.0):
        self.t0, self.t1, self.render, self.fade = t0, t1, render, fade


SHOTS = []
SPRITES = []
SRC = {}


def fish_cut(t0, t1, cx, cy, vw, punch=0.1, amp=14, rot_amp=1.2):
    def render(t, frame):
        u = clamp((t - t0) / (t1 - t0))
        dx, dy, r = shake(frame, amp, rot_amp)
        return view(SRC["fish"], cx, cy, vw * (1 - punch * ease_out(u)), dx, dy, r)
    SHOTS.append(Shot(t0, t1, render))


def flower_shot(t0, t1, path, fade=0.5):
    """path(u) -> (cx, cy, vw) for u in 0..1 across the shot."""
    def render(t, frame):
        cx, cy, vw = path(ease_in_out((t - t0) / (t1 - t0)))
        return view(SRC["flower"], cx, cy, vw)
    SHOTS.append(Shot(t0, t1, render, fade))


def paper_shot(t0, t1, fade):
    SHOTS.append(Shot(t0, t1, lambda t, frame: SRC["paper"], fade))


def background(t, frame):
    active = [s for s in SHOTS if s.t0 <= t < s.t1]
    img = active[0].render(t, frame)
    for s in active[1:]:
        k = clamp((t - s.t0) / s.fade) if s.fade else 1.0
        top = s.render(t, frame)
        img = top if k >= 1 else Image.blend(img, top, k)
    return img


# --------------------------------------------------------------------------- flower reveal

def reveal_field(src):
    """Distance from the flower centre (0..255) with a wobbly, hand-drawn edge."""
    w, h = 600, int(600 * src.height / src.width)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx, ny = xx / w - FLOWER_CENTRE[0], (yy / h - FLOWER_CENTRE[1]) * h / w
    d = np.hypot(nx, ny)
    ang = np.arctan2(ny, nx)
    wobble = 0.025 * np.sin(ang * 5 + 1.3) + 0.015 * np.sin(ang * 11 + 0.4)
    rng = np.random.default_rng(3)
    grain = np.array(Image.fromarray(rng.random((h // 12, w // 12)).astype(np.float32)).resize((w, h), Image.BICUBIC))
    d = d + wobble + grain * 0.03
    d = d / d.max()
    field = Image.fromarray((d * 255).astype(np.uint8), "L")
    return field.resize(src.size, Image.BILINEAR)


def reveal_shot(t0, t1, r0, r1, path):
    def render(t, frame):
        u = ease_in_out((t - t0) / (t1 - t0))
        cx, cy, vw = path(u)
        flower = view(SRC["flower"], cx, cy, vw)
        field = np.asarray(view(SRC["field"], cx, cy, vw, resample=Image.BILINEAR)).astype(np.float32) / 255
        radius = lerp(r0, r1, u)
        m = np.clip((radius - field) / 0.035, 0, 1)
        mask = Image.fromarray((m * 255).astype(np.uint8), "L")
        out = SRC["paper"].copy()
        out.paste(flower, (0, 0), mask)
        return out
    SHOTS.append(Shot(t0, t1, render))


# --------------------------------------------------------------------------- spread + end card

def spread_card():
    im = SRC["spread"]
    cw = 1000
    art = im.resize((cw, int(cw * im.height / im.width)), Image.LANCZOS)
    b = 18
    card = Image.new("RGBA", (art.width + 2 * b, art.height + 2 * b), PAPER_WHITE + (255,))
    card.paste(art, (b, b))
    return add_shadow(card.rotate(-2.0, Image.BICUBIC, expand=True), 8, 14, 12, 0.4)


def spread_shot(t0, t1, fade):
    card = spread_card()

    def render(t, frame):
        u = ease_in_out((t - t0) / (t1 - t0))
        out = SRC["paper"].convert("RGBA")
        s = 1.0 + 0.06 * u
        c = card.resize((int(card.width * s), int(card.height * s)), Image.BICUBIC)
        out.alpha_composite(c, (W // 2 - c.width // 2, int(910 - c.height / 2)))
        return out.convert("RGB")
    SHOTS.append(Shot(t0, t1, render, fade))


def leaf_sprig(seed=5):
    """Little hand-drawn sprig standing in for the 🌿 in the caption."""
    w, h = 420, 300
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)
    stem = [(40 + 330 * i / 12, 270 - 220 * (i / 12) ** 1.3 + rng.uniform(-1.5, 1.5)) for i in range(13)]
    col = tuple(int(c * 0.85) for c in SAGE)

    def leaf(base, ang, length):
        # Pointed leaf: two arcs meeting at the tip, rotated to `ang` degrees.
        pts = []
        for k in range(21):
            f = k / 20
            pts.append((f * length, 0.28 * length * math.sin(math.pi * f)))
        pts += [(x, -y) for x, y in reversed(pts)]
        a = math.radians(ang)
        poly = [(base[0] + x * math.cos(a) - y * math.sin(a), base[1] + x * math.sin(a) + y * math.cos(a))
                for x, y in pts]
        d.polygon(poly, fill=col + (255,), outline=TEAL + (255,), width=4)
        tip = (base[0] + length * 0.85 * math.cos(a), base[1] + length * 0.85 * math.sin(a))
        d.line([base, tip], fill=TEAL + (200,), width=3)

    for i, side in ((3, 1), (4, -1), (6, 1), (7, -1), (9, 1), (10, -1)):
        x0, y0 = stem[i]
        x1, y1 = stem[i + 1]
        heading = math.degrees(math.atan2(y1 - y0, x1 - x0))
        leaf((x0, y0), heading + side * 55, 95 - i * 4)
    d.line(stem, fill=TEAL + (255,), width=7, joint="curve")
    leaf(stem[-1], math.degrees(math.atan2(stem[-1][1] - stem[-2][1], stem[-1][0] - stem[-2][0])), 60)
    return im


# --------------------------------------------------------------------------- captions

def cap(text, t0, t1, y, x=W / 2, size=88, paper=PAPER_WHITE, ink=INK, font=None, seed=0,
        write=0.6, z=0, max_w=880, rot=None):
    img = text_strip(text, font or caveat(size), paper=paper, ink=ink, seed=seed, max_w=max_w)
    r = rot if rot is not None else np.random.default_rng(seed).uniform(-2.0, 2.0)
    s = Sprite(img, t0, (x, y), rot=r, z=z, enter="fade", enter_dur=0.2, t1=t1, leave="fade",
               leave_dur=0.35, boil=0.7, reveal=(t0, write))
    SPRITES.append(s)
    return s


def build():
    fish = Image.open(os.path.join(ART, "noise_fish.jpg")).convert("RGB")
    flower = Image.open(os.path.join(ART, "quiet_flower.jpg")).convert("RGB")
    SRC["fish"] = fish
    SRC["flower"] = flower
    SRC["field"] = reveal_field(flower)
    SRC["spread"] = Image.open(os.path.join(ART, "noise_quiet_spread.jpg")).convert("RGB")
    SRC["paper"] = Image.fromarray(paper_texture(W, H, PAPER, 11, 5))

    # 1. The noise: racing punch-in cuts around the fish page.
    cuts = [(0.00, 0.50, 0.45, 0.62), (0.55, 0.33, 0.17, 0.30), (1.05, 0.55, 0.62, 0.36),
            (1.45, 0.73, 0.36, 0.26), (1.80, 0.14, 0.34, 0.34), (2.10, 0.78, 0.61, 0.24),
            (2.35, 0.33, 0.17, 0.22), (2.58, 0.52, 0.16, 0.30), (2.80, 0.73, 0.36, 0.20),
            (3.00, 0.50, 0.70, 0.40)]
    ends = [c[0] for c in cuts[1:]] + [3.25]
    for (t0, cx, cy, vw), t1 in zip(cuts, ends):
        fish_cut(t0, t1, cx, cy, vw, punch=0.12)

    # The shaking eases off on a wide shot as the mind starts to slow down.
    def settling(t, frame):
        u = clamp((t - 3.25) / 3.6)
        amp = 16 * (1 - ease_out(u))
        dx, dy, r = shake(frame, amp, 1.3 * (1 - ease_out(u)))
        return view(fish, 0.5, 0.47, lerp(0.62, 0.66, u), dx, dy, r)
    SHOTS.append(Shot(3.25, 7.6, settling))

    # 2. Blank paper, then the flower page drawn on from its centre outwards.
    paper_shot(6.7, 8.5, fade=0.8)
    reveal_shot(8.5, 13.6, 0.0, 1.05,
                lambda u: (lerp(0.42, 0.47, u), lerp(0.42, 0.48, u), lerp(0.50, 0.57, u)))

    # 3. Slow close-ups: loops, dashes, circles, then pull back out.
    flower_shot(13.4, 16.1, lambda u: (0.83, lerp(0.28, 0.52, u), 0.34), fade=0.6)
    flower_shot(15.8, 18.1, lambda u: (lerp(0.38, 0.42, u), 0.29, lerp(0.32, 0.28, u)), fade=0.6)
    flower_shot(17.8, 20.0, lambda u: (lerp(0.62, 0.72, u), 0.74, 0.34), fade=0.6)
    flower_shot(19.7, 22.4, lambda u: (lerp(0.42, 0.47, u), lerp(0.41, 0.5, u), lerp(0.24, 0.57, u)), fade=0.6)

    # 4. The open spread, and the closing card.
    spread_shot(22.0, 27.9, fade=0.8)
    paper_shot(27.4, DURATION + 1, fade=0.7)

    neon = tuple(int(c * 0.9 + 25) for c in CHARTREUSE)
    cap("My mind was racing.", 0.25, 3.3, 300, font=marker(78), paper=neon, seed=1, write=0.45)
    cap("Left page: the noise.", 3.5, 6.7, 1600, font=marker(74), paper=neon, seed=2, write=0.5)
    cap("So I stopped trying to think.", 7.3, 9.9, H / 2 - 40, ink=TEAL, seed=3, write=0.9)
    cap("…and just let my hand\nrepeat shapes.", 9.9, 13.4, 1580, ink=TEAL, seed=4, write=1.0)
    cap("Loops,", 13.8, 19.6, 1560, x=270, size=96, ink=TEAL, seed=5, write=0.4)
    cap("dashes,", 16.1, 19.6, 1640, x=540, size=96, ink=TEAL, seed=6, write=0.45)
    cap("circles.", 18.1, 19.6, 1560, x=810, size=96, ink=TEAL, seed=7, write=0.45)
    cap("Over and over.", 20.0, 22.2, 1600, size=96, ink=TEAL, seed=8, write=0.6)
    cap("Left page: the noise.", 22.8, 27.6, 500, x=360, size=80, seed=9, write=0.6)
    cap("Right page: what it quietened into.", 24.2, 27.6, 1330, x=600, size=80, ink=TEAL, seed=10,
        write=1.0, max_w=760)
    cap("You don't need to draw\nanything “real.”", 28.1, DURATION + 1, 780, size=96, seed=11, write=1.0)
    cap("Patterns are enough.", 30.0, DURATION + 1, 1060, size=104, ink=TEAL, seed=12, write=0.8)
    SPRITES.append(Sprite(leaf_sprig(), 31.0, (W / 2, 1340), rot=-4, enter="fade", enter_dur=0.2,
                          boil=0.6, reveal=(31.0, 0.7)))
    SPRITES.sort(key=lambda s: s.z)


VIG = None
GRAIN = None


def setup():
    global VIG, GRAIN
    build()
    yy, xx = np.mgrid[0:H, 0:W]
    VIG = (1 - 0.16 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2).astype(np.float32)
    rng = np.random.default_rng(99)
    GRAIN = [rng.normal(0, 2.5, (H, W)).astype(np.float32) for _ in range(3)]


def render_frame(frame):
    t = frame / FPS
    canvas = background(t, frame).convert("RGBA")
    for s in SPRITES:
        if s.active(t):
            s.draw(canvas, t, frame)
    arr = np.asarray(canvas.convert("RGB")).astype(np.float32)
    arr = arr * VIG[..., None] + GRAIN[(frame // 2) % 3][..., None]
    return np.clip(arr, 0, 255).astype(np.uint8).tobytes()


def main():
    os.makedirs(OUT, exist_ok=True)
    setup()
    if "--preview" in sys.argv:
        pdir = os.path.join(OUT, "preview")
        os.makedirs(pdir, exist_ok=True)
        times = [float(a) for a in sys.argv[sys.argv.index("--preview") + 1:]] or \
            [1.2, 4.5, 8.0, 10.5, 12.5, 14.8, 17.0, 19.0, 21.0, 25.5, 32.0]
        for ts in times:
            Image.frombytes("RGB", (W, H), render_frame(int(ts * FPS))).save(
                os.path.join(pdir, f"nq_t{ts:05.1f}.jpg"), quality=88)
        return
    n = int(DURATION * FPS)
    out = os.path.join(OUT, "noise_to_quiet.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for i, buf in enumerate(pool.imap(render_frame, range(n), chunksize=4)):
            proc.stdin.write(buf)
            if i % 90 == 0:
                print(f"frame {i}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()
    Image.frombytes("RGB", (W, H), render_frame(int(25.5 * FPS))).save(
        os.path.join(OUT, "noise_to_quiet_cover.jpg"), quality=92)
    print("wrote", out)


if __name__ == "__main__":
    main()
