#!/usr/bin/env python3
"""Three alternative looks for the moka pot process reel, as ~10 s samples to choose from.

  cinematic : slow smooth push-ins, dip-to-black dissolves, small white serif captions
  kinetic   : huge bold words slam in one at a time, cut against fast photo punch-ins
  film      : a 35mm film strip scrolls frame to frame, warm grade, typewriter captions

Usage:  python3 make_style_samples.py [cinematic|kinetic|film ...]   -> output/samples/<style>.mp4
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
PHOTOS = os.path.join(ROOT, "photos", "moka_pot")
FONTS = os.path.join(ROOT, "fonts")
OUT = os.path.join(ROOT, "output", "samples")
W, H, FPS = 1080, 1920, 30

SERIF_IT = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
INTER_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
INTER_MED = "/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf"
TYPEWRITER = os.path.join(FONTS, "SpecialElite-Regular.ttf")

PHOTO_FILES = ["1_sketch.jpg", "2_clipboard.jpg", "3_filled.jpg", "4_final_scan.jpg", "5_holding.jpg"]


def font(path, size):
    return ImageFont.truetype(path, size)


def clamp(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    return 1 - (1 - clamp(x)) ** 3


def ease_out_back(x, s=2.2):
    x = clamp(x) - 1
    return x * x * ((s + 1) * x + s) + 1


_cache = {}


def photo(i):
    if i not in _cache:
        _cache[i] = Image.open(os.path.join(PHOTOS, PHOTO_FILES[i])).convert("RGB")
    return _cache[i]


def cover(im, w, h, zoom=1.0, focus=(0.5, 0.5)):
    """Cover-crop `im` to w x h at `zoom`, sub-pixel smooth (no stepping on slow pushes)."""
    s = max(w / im.width, h / im.height) * zoom
    cw, ch = w / s, h / s
    cx = min(max(focus[0] * im.width, cw / 2), im.width - cw / 2)
    cy = min(max(focus[1] * im.height, ch / 2), im.height - ch / 2)
    box = (max(0.0, cx - cw / 2), max(0.0, cy - ch / 2), min(im.width, cx + cw / 2), min(im.height, cy + ch / 2))
    return im.resize((w, h), Image.BICUBIC, box=box, reducing_gap=2.0)


def contain(im, w, h):
    s = min(w / im.width, h / im.height)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)


def text_size(d, txt, f):
    l, t, r, b = d.textbbox((0, 0), txt, font=f)
    return r - l, b - t, l, t


def vignette(strength):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2
    return (1 - strength * np.clip(r - 0.25, 0, None)).astype(np.float32)


# =========================================================================== cinematic

VIG = None
SHADE = None


def cinematic(t):
    """0-3.6 sketch, 3.6-6.8 filled in, 6.8-10 final scan on black."""
    shots = [  # (start, end, photo, zoom from, zoom to, focus)
        (0.0, 3.9, 0, 1.0, 1.10, (0.5, 0.45)),
        (3.3, 7.1, 2, 1.12, 1.02, (0.5, 0.45)),
        (6.5, 10.0, 3, None, None, None),
    ]
    canvas = np.zeros((H, W, 3), np.float32)
    for s0, s1, idx, z0, z1, focus in shots:
        if not (s0 <= t < s1):
            continue
        a = smooth((t - s0) / 0.6) * (1 - smooth((t - (s1 - 0.6)) / 0.6)) if s1 < 10 else smooth((t - s0) / 0.6)
        k = (t - s0) / (s1 - s0)
        if z0 is None:
            # final scan floats on black, gently growing
            art = photo(idx)
            sc = 0.80 + 0.05 * smooth(k)
            im = contain(art, int(W * sc), int(H * 0.72 * sc / 0.8))
            frame = Image.new("RGB", (W, H), (10, 10, 10))
            frame.paste(im, ((W - im.width) // 2, int(H * 0.47 - im.height / 2)))
        else:
            frame = cover(photo(idx), W, H, z0 + (z1 - z0) * smooth(k), focus)
        canvas += np.asarray(frame, np.float32) * a
    # warm, slightly lifted blacks
    canvas = canvas * np.array([1.03, 1.0, 0.94], np.float32) * VIG[..., None] * SHADE[..., None]
    img = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8))

    lines = [  # (start, end, text, y, size)
        (0.5, 3.6, "You don't need to be good", 1480, 92),
        (1.3, 3.6, "to show your art.", 1590, 92),
        (4.0, 6.8, "I almost didn't share", 1500, 92),
        (4.7, 6.8, "any of this.", 1610, 92),
        (7.3, 10.5, "Then it became this.", 1640, 96),
    ]
    draw_lines(img, t, lines)
    return img


def draw_lines(img, t, lines):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d, ds = ImageDraw.Draw(layer), ImageDraw.Draw(shadow)
    for l0, l1, txt, y, size in lines:
        if not (l0 <= t < l1):
            continue
        a = smooth((t - l0) / 0.7) * (1 - smooth((t - (l1 - 0.4)) / 0.4))
        f = font(SERIF_IT, size)
        tw, th, ox, oy = text_size(d, txt, f)
        dy = 14 * (1 - ease_out((t - l0) / 0.9))
        pos = ((W - tw) / 2 - ox, y + dy - oy)
        ds.text(pos, txt, font=f, fill=(0, 0, 0, int(200 * a)))
        d.text(pos, txt, font=f, fill=(250, 246, 238, int(255 * a)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    img.paste(shadow, (0, 0), shadow)
    img.paste(layer, (0, 0), layer)


# =========================================================================== kinetic

PAPER = (244, 240, 232)
INK = (18, 18, 18)
HILITE = (255, 214, 0)


def kinetic(t):
    """Words slam in on a paper background; hard cuts to photo punch-ins between phrases."""
    beats = 0.42
    # timeline of (start, kind, payload)
    seq = [
        (0.00, "words", ["YOU", "DON'T", "NEED", "TO BE", "GOOD"], {"GOOD"}),
        (2.30, "photo", 0),
        (3.10, "words", ["TO", "SHOW", "YOUR", "ART."], {"ART."}),
        (4.90, "photo", 1),
        (5.50, "photo", 2),
        (6.10, "photo", 3),
        (6.90, "photo", 4),
        (7.60, "words", ["SHOW", "UP", "ANYWAY."], {"ANYWAY."}),
        (10.0, "end", None),
    ]
    cur = max(i for i, s in enumerate(seq) if s[0] <= t)
    s0, kind, payload = seq[cur][0], seq[cur][1], seq[cur][2]
    lt = t - s0
    if kind == "photo":
        z = 1.18 - 0.16 * ease_out(lt / 0.35)
        img = cover(photo(payload), W, H, z, (0.55 if payload == 4 else 0.5, 0.45))
        if lt < 0.05:   # one bright flash frame on the cut
            img = Image.blend(img, Image.new("RGB", (W, H), (255, 255, 255)), 0.6)
        return img
    words, hot = payload, seq[cur][3]
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    shown = min(len(words), int(lt / beats) + 1)
    f = font(INTER_BLACK, 200)
    lh = 210
    top = H / 2 - lh * len(words) / 2
    for i in range(shown):
        w = words[i]
        p = (lt - i * beats) / 0.16
        sc = 1 + 0.35 * (1 - ease_out_back(p, 1.2)) if p < 1 else 1.0
        fs = font(INTER_BLACK, max(10, int(200 * min(sc, 1.6))))
        tw, th, ox, oy = text_size(d, w, fs)
        x, y = (W - tw) / 2 - ox, top + i * lh + (lh - th) / 2 - oy
        if w in hot:
            hw, hh, _, _ = text_size(d, w, f)
            grow = ease_out((lt - i * beats) / 0.25)
            d.rectangle(((W - hw) / 2 - 24, top + i * lh + 12, (W - hw) / 2 - 24 + (hw + 48) * grow,
                         top + (i + 1) * lh - 4), fill=HILITE)
        d.text((x, y), w, font=fs, fill=INK)
    # small kicker under the stack
    small = font(INTER_MED, 58)
    tag = "the moka pot, start to finish" if cur == 0 else "that's the whole skill." if cur == 7 else ""
    if tag and lt > beats * len(words):
        tw, th, ox, oy = text_size(d, tag, small)
        d.text(((W - tw) / 2 - ox, top + lh * len(words) + 50), tag, font=small, fill=(90, 90, 90))
    return img


# =========================================================================== film

def film_strip_frame(idx, fw, fh):
    im = cover(photo(idx), fw, fh, 1.0, (0.55 if idx == 4 else 0.5, 0.45))
    arr = np.asarray(im, np.float32)
    # faded warm film: lifted blacks, warm mids, softer contrast
    arr = 18 + arr * 0.9
    arr *= np.array([1.06, 1.0, 0.86], np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


FILM = None


def film(t):
    """The strip scrolls up and settles on each frame; caption types out underneath."""
    fw, fh, gap = 820, 1093, 70
    pitch = fh + gap
    stops = [(0.0, 0), (3.2, 1), (6.4, 2)]   # (time it starts moving to frame n, n)
    pos = 0.0
    for st, n in stops:
        if t >= st:
            pos = (n - 1) + smooth((t - st) / 0.9) if n > 0 else 0.0
    img = Image.new("RGB", (W, H), (14, 12, 11))
    d = ImageDraw.Draw(img)
    strip_w = fw + 2 * 110
    sx = (W - strip_w) // 2
    cy = 700
    d.rectangle((sx, 0, sx + strip_w, H), fill=(32, 24, 18))
    off = -pos * pitch
    # sprocket holes scroll with the film
    hole_pitch = pitch / 8
    first = -((off % hole_pitch) + hole_pitch)
    y = first
    while y < H + hole_pitch:
        for hx in (sx + 34, sx + strip_w - 34 - 46):
            d.rounded_rectangle((hx, y, hx + 46, y + 64), 9, fill=(14, 12, 11))
        y += hole_pitch
    lab = font(INTER_MED, 30)
    for n in range(-1, 5):
        fy = cy - fh / 2 + n * pitch + off
        if fy > H or fy + fh < 0 or n < 0 or n > 4:
            continue
        img.paste(FILM[n], (sx + 110, int(fy)))
        d.text((sx + 112, fy + fh + 14), f"{n + 1}A        400", font=lab, fill=(232, 140, 50))
    # light leak drifting in from the right edge
    arr = np.asarray(img, np.float32)
    leak = 0.5 + 0.5 * math.sin(t * 1.3)
    arr += LEAK * leak
    # grain
    rng = np.random.default_rng(int(t * FPS))
    arr += rng.normal(0, 7, (H // 2, W // 2)).repeat(2, 0).repeat(2, 1)[..., None]
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    # typewriter caption in a dark band under the strip
    band = Image.new("L", (W, H), 0)
    ImageDraw.Draw(band).rectangle((0, 1400, W, H), fill=255)
    band = band.filter(ImageFilter.GaussianBlur(30))
    img.paste((14, 12, 11), (0, 0), band)
    caps = [(0.6, 3.2, "You don't need to be good\nto show your art."),
            (3.9, 6.4, "Half the page was\nstill just lines."),
            (7.1, 10.0, "I almost didn't share\nany of this.")]
    d = ImageDraw.Draw(img)
    f = font(TYPEWRITER, 66)
    for c0, c1, txt in caps:
        if c0 <= t < c1:
            n = int((t - c0) * 22)
            shown = txt[:n]
            cursor = "_" if int(t * 3) % 2 == 0 or n < len(txt) else ""
            ylines = shown.split("\n")
            for i, line in enumerate(txt.split("\n")):
                tw, th, ox, oy = text_size(d, line, f)
                part = ylines[i] if i < len(ylines) else ""
                cur = cursor if i == len(ylines) - 1 else ""
                d.text(((W - tw) / 2 - ox, 1530 + i * 92 - oy), part + cur, font=f, fill=(240, 230, 210))
    return img


LEAK = None


# =========================================================================== render

STYLES = {"cinematic": cinematic, "kinetic": kinetic, "film": film}
STYLE = None


def init(style):
    global STYLE, VIG, SHADE, FILM, LEAK
    STYLE = style
    VIG = vignette(0.35)
    ys = np.linspace(0, 1, H, dtype=np.float32)[:, None].repeat(W, 1)
    SHADE = 1 - 0.62 * np.clip((ys - 0.62) / 0.3, 0, 1) ** 1.2
    FILM = [film_strip_frame(i, 820, 1093) for i in range(5)]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    LEAK = (np.exp(-(((xx - W * 1.05) / 380) ** 2 + ((yy - H * 0.3) / 700) ** 2))[..., None]
            * np.array([90, 40, 0], np.float32))


def render(i):
    return np.asarray(STYLES[STYLE](i / FPS).convert("RGB")).tobytes()


def main():
    os.makedirs(OUT, exist_ok=True)
    for style in sys.argv[1:] or list(STYLES):
        out = os.path.join(OUT, style + ".mp4")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        with Pool(os.cpu_count(), initializer=init, initargs=(style,)) as pool:
            for buf in pool.imap(render, range(int(10 * FPS)), chunksize=4):
                proc.stdin.write(buf)
        proc.stdin.close()
        proc.wait()
        print("wrote", out, flush=True)


if __name__ == "__main__":
    main()
