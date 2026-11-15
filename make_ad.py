#!/usr/bin/env python3
"""A 30-second peppy ad reel: "One artist. Zero boxes."

Cut from the loudest stretch of "I Am an Ocean" (the choruses, 53.4 s -> 84.1 s of the
track, exactly 56 beats). Everything snaps to the beat: flat colour blocks that wipe in on
every cut, a spinning sunburst, sticker-style artwork with hard shadows, slammed
Permanent Marker headlines, confetti bursts, and the lyrics in a caption pill.

Story (in beats):
   0-3   hook: ONE ARTIST. / ZERO BOXES.
   4-23  roll call, 2 beats each: INK, LINEWORK, CHARCOAL, PENCIL, MOSAIC, ...
  24-31  one beat each: BOLD, COZY, WARM, FUN, ...
  32-39  half-beat stutter through everything, WILD & FREE on the lyric
  40-47  all 16 pieces pop into a grid: ALL ONE ARTIST.
  48-55  call to action (edit CTA_* below)

Usage:  python3 make_ad.py                 # renders output/ad_one_artist.mp4
        python3 make_ad.py --preview 1 5 20 # stills at those seconds -> output/preview/
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import make_ocean as mo
from make_ocean import (W, H, FONTS, OUT, SONG, art_image, transform, paste_center, clamp,
                        ease_out, ease_out_back, ease_in_out, lerp, caveat)

FPS = 30
BEAT = mo.BEAT
SONG_START = mo.beat(97)            # 53.366 s: right on "Different depths"
N_BEATS = 56
DURATION = N_BEATS * BEAT           # 30.77 s

# ---- edit the call to action here --------------------------------------------------
CTA_BIG = ["FOLLOW", "FOR MORE"]
CTA_SMALL = "DM for commissions"
# -----------------------------------------------------------------------------------

INK = (24, 20, 30)
CREAM = (255, 249, 236)
PINK = (255, 84, 140)
YELLOW = (255, 210, 26)
BLUE = (48, 92, 255)
MINT = (52, 214, 168)
ORANGE = (255, 122, 44)
PURPLE = (146, 86, 255)
RED = (240, 60, 60)

CARD_CY = 900
HEAD_CY = 300
LYRIC_CY = 1440

# (beat, beats long, art, label, background)
ROLL = [
    (4, 2, "inkflower", "INK", YELLOW),
    (6, 2, "dragonflies", "LINEWORK", PINK),
    (8, 2, "moka", "CHARCOAL", MINT),
    (10, 2, "man", "PENCIL", ORANGE),
    (12, 2, "woman", "MOSAIC", BLUE),
    (14, 2, "self", "PORTRAITS", YELLOW),
    (16, 2, "garlic", "MADHUBANI", BLUE),
    (18, 2, "diya", "FOLK ART", ORANGE),
    (20, 2, "blueflowers", "TEXTURE", PINK),
    (22, 2, "architecture", "CITYSCAPES", MINT),
    (24, 1, "fish", "BOLD", RED),
    (25, 1, "winter", "COZY", PURPLE),
    (26, 1, "fireplace", "WARM", BLUE),
    (27, 1, "scooter", "FUN", YELLOW),
    (28, 1, "nook", "CALM", PINK),
    (29, 1, "birds", "GRAPHIC", YELLOW),
    (30, 1, "blueflowers", "BRIGHT", ORANGE),
    (31, 1, "diya", "GLOWING", PURPLE),
]
STUTTER = ["self", "fish", "garlic", "dragonflies", "woman", "scooter", "moka", "fireplace",
           "inkflower", "winter", "diya", "man", "nook", "blueflowers", "architecture", "birds"]
STUTTER_BG = [PINK, YELLOW, BLUE, MINT, ORANGE, PURPLE, YELLOW, PINK]
GRID_ORDER = mo.GRID_ORDER
GRID_POP = mo.GRID_POP

# headline words: (beat it slams in, beat it leaves, text, fill colour)
HEADLINES = [
    (0, 2, "ONE ARTIST.", CREAM),
    (2, 4, "ZERO BOXES.", YELLOW),
    (32, 33.5, "NO RULES.", CREAM),
    (33.6, 35.6, "WILD", YELLOW),          # sung "wild" at 71.8 s
    (35.6, 40, "& FREE", CREAM),           # sung "free" at 72.9 s
    (40, 44, "16 PIECES.", CREAM),
    (44, 48, "ALL ONE ARTIST.", YELLOW),
]
CONFETTI_AT = [0, 2, 4, 14, 24, 33.6, 40, 44, 48]


def tb(b):
    return b * BEAT


def bg_for(beat_f):
    if beat_f < 4:
        return PINK if beat_f < 2 else BLUE
    for b, n, _, _, col in ROLL:
        if b <= beat_f < b + n:
            return col
    if 32 <= beat_f < 40:
        return STUTTER_BG[int((beat_f - 32) * 2) % len(STUTTER_BG)]
    if 40 <= beat_f < 48:
        return MINT if beat_f < 44 else PURPLE
    return YELLOW


def cut_times():
    cuts = [0, 2, 4] + [b for b, *_ in ROLL] + [32 + k / 2 for k in range(16)] + [40, 44, 48]
    return sorted(set(cuts))


CUTS = cut_times()

# --------------------------------------------------------------------------- background

_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_ANG = np.arctan2(_yy - CARD_CY, _xx - 540)
_RAD = np.hypot(_yy - CARD_CY, _xx - 540)
_DIAG = (_xx + 0.55 * _yy) / (W + 0.55 * H)        # 0..1 for the wipe
_DOTS = (((_xx % 36) - 18) ** 2 + ((_yy % 36) - 18) ** 2) < 25


def background(t):
    bf = t / BEAT
    col = np.array(bg_for(bf), np.float32)
    prev_cut = max([c for c in CUTS if c <= bf] or [0])
    prev_col = np.array(bg_for(prev_cut - 0.01), np.float32) if prev_cut > 0 else col
    img = np.empty((H, W, 3), np.float32)
    img[:] = col
    # diagonal wipe from the previous colour over the first 0.13 s of a cut
    u = (t - tb(prev_cut)) / 0.13
    if 0 <= u < 1 and prev_cut > 0:
        old = _DIAG > ease_out(u) * 1.15
        img[old] = prev_col
    # spinning sunburst
    rot = t * 0.35
    rays = ((_ANG + rot) % (2 * math.pi / 20)) < (math.pi / 20)
    img[rays] = img[rays] * 0.9 + 255 * 0.1
    # halftone dots that fade towards the centre
    dots = _DOTS & (_RAD > 640)
    img[dots] = img[dots] * 0.82
    return np.clip(img, 0, 255).astype(np.uint8)


# --------------------------------------------------------------------------- sprites

_cache = {}


def sticker(name, max_w=800, max_h=820):
    key = ("st", name, max_w, max_h)
    if key in _cache:
        return _cache[key]
    im = art_image(name)
    b, o, sh = 16, 6, 18
    s = min((max_w - 2 * (b + o)) / im.width, (max_h - 2 * (b + o)) / im.height)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    cw, ch = im.width + 2 * (b + o), im.height + 2 * (b + o)
    spr = Image.new("RGBA", (cw + sh + 4, ch + sh + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(spr)
    d.rounded_rectangle([sh, sh, sh + cw - 1, sh + ch - 1], 18, fill=INK + (255,))
    d.rounded_rectangle([0, 0, cw - 1, ch - 1], 18, fill=INK + (255,))
    d.rounded_rectangle([o, o, cw - 1 - o, ch - 1 - o], 13, fill=CREAM + (255,))
    spr.paste(im, (b + o, b + o))
    _cache[key] = spr
    return spr


def small_tile(name, size=226):
    key = ("tile", name)
    if key in _cache:
        return _cache[key]
    im = art_image(name)
    inner = size - 20
    s = inner / min(im.width, im.height)
    im = im.resize((max(inner, round(im.width * s)), max(inner, round(im.height * s))), Image.LANCZOS)
    l, t = (im.width - inner) // 2, (im.height - inner) // 2
    im = im.crop((l, t, l + inner, t + inner))
    spr = Image.new("RGBA", (size + 12, size + 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(spr)
    d.rounded_rectangle([10, 10, size + 9, size + 9], 12, fill=INK + (255,))
    d.rounded_rectangle([0, 0, size - 1, size - 1], 12, fill=INK + (255,))
    d.rounded_rectangle([4, 4, size - 5, size - 5], 9, fill=CREAM + (255,))
    spr.paste(im, (10, 10))
    _cache[key] = spr
    return spr


def marker(size):
    return ImageFont.truetype(os.path.join(FONTS, "PermanentMarker-Regular.ttf"), size)


def headline(text, fill, size=None):
    """Sticker lettering: coloured fill, thick ink outline, hard offset shadow."""
    if size is None:
        size = 150 if len(text) <= 8 else 118 if len(text) <= 11 else 96
    key = ("hl", text, fill, size)
    if key in _cache:
        return _cache[key]
    f = marker(size)
    l, t, r, b = f.getbbox(text, stroke_width=10)
    pad = 30
    im = Image.new("RGBA", (r - l + 2 * pad + 14, b - t + 2 * pad + 14), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((pad - l + 12, pad - t + 14), text, font=f, fill=INK, stroke_width=10, stroke_fill=INK)
    d.text((pad - l, pad - t), text, font=f, fill=fill, stroke_width=10, stroke_fill=INK)
    _cache[key] = im
    return im


def label_pill(text, bg):
    key = ("pill", text, bg)
    if key in _cache:
        return _cache[key]
    f = marker(92)
    l, t, r, b = f.getbbox(text)
    w, h = r - l + 90, b - t + 56
    im = Image.new("RGBA", (w + 14, h + 14), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([14, 14, w + 13, h + 13], h // 2, fill=INK + (255,))
    d.rounded_rectangle([0, 0, w - 1, h - 1], h // 2, fill=INK + (255,))
    d.rounded_rectangle([6, 6, w - 7, h - 7], h // 2 - 6, fill=CREAM + (255,))
    d.text((w / 2, h / 2 + 2), text, font=f, fill=bg if bg not in (YELLOW, MINT) else INK, anchor="mm")
    _cache[key] = im
    return im


def star(draw, cx, cy, r, fill, rot=0.0):
    pts = []
    for k in range(10):
        rr = r if k % 2 == 0 else r * 0.42
        a = rot + k * math.pi / 5 - math.pi / 2
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    draw.polygon(pts, fill=fill, outline=INK, width=4)


# --------------------------------------------------------------------------- confetti

_rng = np.random.default_rng(3)
CONF = []
for cb in CONFETTI_AT:
    n = 34
    CONF.append((cb, _rng.uniform(0, 2 * math.pi, n), _rng.uniform(900, 2000, n),
                 _rng.integers(0, 6, n), _rng.uniform(-8, 8, n), _rng.uniform(10, 22, n)))
CONF_COLS = [PINK, YELLOW, BLUE, MINT, ORANGE, CREAM]


def draw_confetti(draw, t):
    for cb, ang, spd, ci, spin, sz in CONF:
        u = t - tb(cb)
        if not 0 <= u < 1.3:
            continue
        for k in range(len(ang)):
            x = 540 + math.cos(ang[k]) * spd[k] * u * (1 - 0.35 * u)
            y = CARD_CY + math.sin(ang[k]) * spd[k] * u * (1 - 0.35 * u) + 900 * u * u
            r, a = sz[k], spin[k] * u
            pts = [(x + r * math.cos(a + q), y + r * 0.55 * math.sin(a + q)) for q in (0, 1.9, math.pi, 5.0)]
            draw.polygon(pts, fill=CONF_COLS[ci[k]] + (255,), outline=INK + (255,))


# --------------------------------------------------------------------------- lyrics pill

LYR = [(end - SONG_START, [(w, s - SONG_START) for w, s in words])
       for end, words in mo.LYRICS if end > SONG_START + 0.1 and words[0][1] < SONG_START + DURATION]


def draw_lyrics(frame, t, font):
    for n, (end, words) in enumerate(LYR):
        start = words[0][1]
        nxt = LYR[n + 1][1][0][1] if n + 1 < len(LYR) else DURATION + 1
        a = clamp((t - start + 0.12) / 0.1) * clamp((min(end + 0.4, nxt - 0.12) - t) / 0.1)
        if a <= 0:
            continue
        space = font.getlength(" ")
        widths = [font.getlength(w) for w, _ in words]
        total = sum(widths) + space * (len(words) - 1)
        h = 92
        pill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(pill)
        x0, x1 = 540 - total / 2 - 38, 540 + total / 2 + 38
        d.rounded_rectangle([x0, LYRIC_CY - h / 2, x1, LYRIC_CY + h / 2], h // 2, fill=INK + (int(225 * a),))
        x = 540 - total / 2
        for i, (w, ws) in enumerate(words):
            we = words[i + 1][1] if i + 1 < len(words) else end
            col = YELLOW if ws <= t < we + 0.05 else CREAM
            al = a * (0.45 + 0.55 * clamp((t - ws) / 0.1))
            bounce = -8 * math.exp(-(t - ws) / 0.12) if t >= ws else 0
            d.text((x, LYRIC_CY + bounce), w, font=font, fill=col + (int(255 * al),), anchor="lm")
            x += widths[i] + space
        frame.alpha_composite(pill)


# --------------------------------------------------------------------------- frame

def punch(t):
    k = math.floor(t / BEAT)
    return 1 + 0.045 * math.exp(-(t - tb(k)) / 0.11)


def slam(frame, im, t0, t, cx, cy, rot0=-4.0):
    u = t - t0
    s = lerp(1.7, 1.0, ease_out_back(u / 0.22, 2.2)) if u < 0.22 else 1.0
    rot = rot0 + 2.0 * math.sin(t * 5)
    paste_center(frame, transform(im, s * (1 + 0.5 * (punch(t) - 1)), rot, clamp(u / 0.06)), cx, cy)


def draw_card(frame, t, name, b0, idx, max_w=800, max_h=820):
    u = t - tb(b0)
    side = -1 if idx % 2 else 1
    e = ease_out_back(u / 0.25, 1.4)
    cx = 540 + side * 700 * (1 - e)
    rot = side * (5 - 9 * e) + 2.5 * math.sin(t * 3 + idx)
    paste_center(frame, transform(sticker(name, max_w, max_h), punch(t), rot), cx, CARD_CY)


_fonts = {}


def render(t):
    if not _fonts:
        _fonts["lyric"] = caveat(66)
        _fonts["small"] = marker(58)
    bf = t / BEAT
    frame = Image.fromarray(background(t)).convert("RGBA")

    # ----- artwork
    if bf < 4:
        draw_card(frame, t, "self", 0, 0, 700, 760)
        if bf >= 2:   # a dashed box that bursts on ZERO BOXES
            u = clamp((t - tb(2)) / 0.35)
            d = ImageDraw.Draw(frame)
            r = 470 + 500 * ease_out(u)
            for k in range(4):
                for j in range(14):
                    a0, a1 = j / 14, (j + 0.55) / 14
                    p = [(-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)]
                    (ax, ay), (bx, by) = p[k], p[k + 1]
                    d.line([540 + r * lerp(ax, bx, a0), CARD_CY + r * lerp(ay, by, a0),
                            540 + r * lerp(ax, bx, a1), CARD_CY + r * lerp(ay, by, a1)],
                           fill=INK + (int(255 * (1 - u)),), width=10)
    elif bf < 32:
        for i, (b, n, name, label, col) in enumerate(ROLL):
            if b <= bf < b + n:
                draw_card(frame, t, name, b, i)
                pill = label_pill(label, col)
                slam(frame, pill, tb(b), t, 540, HEAD_CY, rot0=-3 if i % 2 else 3)
    elif bf < 40:
        k = int((bf - 32) * 2)
        name = STUTTER[k % len(STUTTER)]
        u = t - tb(32 + k / 2)
        s = lerp(1.12, 1.0, ease_out(u / 0.12)) * punch(t)
        paste_center(frame, transform(sticker(name), s, (-4 if k % 2 else 4)), 540, CARD_CY)
    elif bf < 48:
        for i, name in enumerate(GRID_ORDER):
            appear = tb(40) + GRID_POP.index(i) * BEAT / 4
            u = t - appear
            if u < 0:
                continue
            col, row = i % 4, i // 4
            x = 540 + (col - 1.5) * 238
            y = CARD_CY + (row - 1.5) * 238
            s = ease_out_back(u / 0.25, 2.0) * punch(t)
            paste_center(frame, transform(small_tile(name), s, ((i * 37) % 7 - 3) * 1.2), x, y)
    else:
        # CTA: self-portrait sticker bobbing, big call to action, stars
        u = t - tb(48)
        e = ease_out_back(u / 0.35, 1.6)
        paste_center(frame, transform(sticker("self", 560, 600), e * punch(t) * 0.98, -6 + 3 * math.sin(t * 2.5)),
                     540, 980 + 20 * math.sin(t * 3))
        d = ImageDraw.Draw(frame)
        for k, (sx, sy, r) in enumerate([(150, 640, 46), (930, 700, 38), (180, 1300, 34), (900, 1290, 50)]):
            if u > 0.15 * k:
                star(d, sx, sy + 10 * math.sin(t * 4 + k), r * punch(t), CREAM if k % 2 else PINK, t * (1 if k % 2 else -1))
        slam(frame, headline(CTA_BIG[0], CREAM, 150), tb(48), t, 540, 250, -3)
        if bf >= 49:
            slam(frame, headline(CTA_BIG[1], PINK, 130), tb(49), t, 560, 420, 2)
        if bf >= 51:
            v = t - tb(51)
            pill = label_pill(CTA_SMALL, PINK)
            paste_center(frame, transform(pill, ease_out_back(v / 0.3) * 0.8 * punch(t), -2),
                         540, 1560)

    # ----- headlines
    for b0, b1, text, fill in HEADLINES:
        if b0 <= bf < b1:
            cy = HEAD_CY if bf >= 4 else 330
            slam(frame, headline(text, fill), tb(b0), t, 540, cy)

    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_confetti(ImageDraw.Draw(over), t)
    frame.alpha_composite(over)

    if bf < 48:
        draw_lyrics(frame, t, _fonts["lyric"])

    # flash on each section change
    for b in (4, 24, 32, 40, 48):
        fl = math.exp(-(t - tb(b)) / 0.07) if t >= tb(b) else 0
        if fl > 0.02:
            frame.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(170 * fl))))
    # fade out the last half second
    fo = clamp((t - (DURATION - 0.45)) / 0.45)
    if fo > 0:
        frame.alpha_composite(Image.new("RGBA", (W, H), INK + (int(255 * fo),)))
    return frame.convert("RGB")


def render_bytes(i):
    return render(i / FPS).tobytes()


def main():
    os.makedirs(OUT, exist_ok=True)
    if "--preview" in sys.argv:
        pdir = os.path.join(OUT, "preview")
        os.makedirs(pdir, exist_ok=True)
        times = [float(x) for x in sys.argv[sys.argv.index("--preview") + 1:]] or [0.5, 1.5, 3, 7, 14, 18.4, 20, 25.5, 29]
        for t in times:
            render(t).save(os.path.join(pdir, f"ad_{t:05.2f}.jpg"), quality=88)
        return
    n = int(round(DURATION * FPS))
    out = os.path.join(OUT, "ad_one_artist.mp4")
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-ss", f"{SONG_START:.3f}", "-t", f"{DURATION:.3f}", "-i", SONG,
           "-filter_complex", f"[1:a]afade=t=in:d=0.03,afade=t=out:st={DURATION - 1.3:.3f}:d=1.3[a]",
           "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count() or 1) as pool:
        for i, buf in enumerate(pool.imap(render_bytes, range(n), chunksize=8)):
            proc.stdin.write(buf)
    proc.stdin.close()
    proc.wait()
    render(tb(2) + 0.4).save(os.path.join(OUT, "ad_cover.jpg"), quality=92)
    print("wrote", out)


if __name__ == "__main__":
    main()
