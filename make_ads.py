#!/usr/bin/env python3
"""Three 9:16 video ads for Creator Studio, in the same papercut style as the sketchbook reel.

  1. artists     "You paint. Claude handles the reels."
  2. creators    UGC and content creators: film it, Claude ships it
  3. beginners   professional-looking reels without editing experience

Every ad covers the full feature set (see USPS below); the order and wording are tuned per audience.
The phones play real footage from the sketchbook reels in output/. The paper sprites, easing and
grain all come from make_video.py.

Usage:  python3 make_ads.py                       # renders all three to output/ads/
        python3 make_ads.py artists               # renders one ad
        python3 make_ads.py artists --preview 2 9 # writes stills to output/ads/preview/
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageSequence

import make_video as mv
from make_video import (ART, CHARCOAL, CHARTREUSE, COBALT, CREAM, DUSTY_BLUE, FPS, H, INK, MUSTARD,
                        OUT, OUT_FPS, PAPER_WHITE, PINK, SAGE, TERRACOTTA, W, Sprite, add, add_shadow,
                        background, caption, caveat, cutout, load_art, marker, paper_circle, square_thumb,
                        star, strike, text_strip, torn_sheet, typewriter)

ADS_OUT = os.path.join(OUT, "ads")
BRAND = "CREATOR STUDIO"

# What every ad has to get across. Each one is backed by something this repo already does.
USPS = [
    "your art, photos or footage in, a finished reel out: story and pacing written for you",
    "hand-lettered captions burned in",
    "two looks: papercut stop-motion or a 3D flip-book, which can float over your own footage",
    "colours pulled from your own work",
    "natural voice-over that reads the captions, with a choice of voices",
    "the whole post kit: cover frame, caption and hashtags, music-ready track",
    "change anything by asking, with preview stills before the final render",
    "full HD 9:16, ready for Reels, TikTok and Shorts",
    "several versions from one upload",
]


# --------------------------------------------------------------------------- props

def cover_crop(im, w, h):
    s = max(w / im.width, h / im.height)
    im = im.resize((max(w, int(im.width * s + 0.5)), max(h, int(im.height * s + 0.5))), Image.LANCZOS)
    l, t = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((l, t, l + w, t + h))


_FOOTAGE = {}


def footage(name, start, dur, fps=8):
    """Frames from one of the finished reels in output/, as 540x960 images."""
    key = (name, start, dur, fps)
    if key not in _FOOTAGE:
        cmd = ["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(dur), "-i", os.path.join(OUT, name),
               "-vf", f"fps={fps},scale=540:960", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        raw = subprocess.run(cmd, capture_output=True, check=True).stdout
        size = 540 * 960 * 3
        _FOOTAGE[key] = [Image.frombytes("RGB", (540, 960), raw[i:i + size])
                         for i in range(0, len(raw) - size + 1, size)]
    return _FOOTAGE[key]


def phone(screens, captions=None, w=500, label=None):
    """A phone playing a reel: one frame per screen. With captions, each screen is a slide with
    progress segments and a burned-in caption; without, the screens are video frames."""
    bez, rad = 16, 62
    sw = w - 2 * bez
    sh = int(sw * 16 / 9)
    h = sh + 2 * bez
    smask = Image.new("L", (sw, sh), 0)
    ImageDraw.Draw(smask).rounded_rectangle((0, 0, sw - 1, sh - 1), rad - bez, fill=255)
    f_cap = caveat(max(34, w // 11))
    f_lab = marker(max(26, w // 16))
    frames = []
    n = len(screens)
    for i, im in enumerate(screens):
        cap = captions[i] if captions else None
        body = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(body).rounded_rectangle((0, 0, w - 1, h - 1), rad, fill=(24, 24, 26, 255))
        scr = cover_crop(im, sw, sh).convert("RGBA")
        d = ImageDraw.Draw(scr, "RGBA")
        if captions:
            seg = (sw - 40 - (n - 1) * 6) / n
            for k in range(n):
                x0 = 20 + k * (seg + 6)
                d.rounded_rectangle((x0, 34, x0 + seg, 40), 3, fill=(255, 255, 255, 235 if k <= i else 90))
        else:
            d.rounded_rectangle((20, sh - 22, sw - 20, sh - 16), 3, fill=(255, 255, 255, 90))
            d.rounded_rectangle((20, sh - 22, 20 + (sw - 40) * (i + 1) / n, sh - 16), 3,
                                fill=(255, 255, 255, 235))
        for k in range(3):
            cy = sh - 300 + k * 74
            d.ellipse((sw - 58, cy, sw - 20, cy + 38), fill=(255, 255, 255, 200))
        if cap:
            lines = mv.wrap(cap, f_cap, sw - 120)
            asc, desc = f_cap.getmetrics()
            lh = int((asc + desc) * 0.95)
            by = sh - 70 - lh * len(lines)
            tw = max(f_cap.getlength(l) for l in lines)
            d.rounded_rectangle(((sw - tw) / 2 - 22, by - 14, (sw + tw) / 2 + 22, by + lh * len(lines) + 10),
                                18, fill=(255, 255, 255, 230))
            for j, l in enumerate(lines):
                d.text(((sw - f_cap.getlength(l)) / 2, by + j * lh - desc * 0.2), l, font=f_cap, fill=INK)
        body.paste(scr, (bez, bez), smask)
        if label:
            ImageDraw.Draw(body).text((bez + 26, bez + 56), label, font=f_lab, fill=PAPER_WHITE)
        frames.append(add_shadow(body, 10, 16, 14, 0.42))
    return frames


def play(frames, t, pos, z, rot=0.0, fps=8, enter="slide_up"):
    add(Sprite(frames[0], t, pos, rot=rot, z=z, enter=enter, enter_dur=0.5, frames=frames,
               frame_dur=1 / fps))


def card(text, seed, w=900, header="ask Claude", size=52, head_col=TERRACOTTA):
    """A chat-style card; returns (card, text layer) so the text can be 'typed' with a reveal.
    Hashtags are inked in cobalt."""
    f = typewriter(size)
    lines = mv.wrap(text, f, w - 112)
    asc, desc = f.getmetrics()
    lh = int((asc + desc) * 1.05)
    top = 140 if header else 50
    h = top + lh * len(lines) + 40
    sheet = torn_sheet(w, h, PAPER_WHITE, seed, sides="", amp=0, grain=3)
    if header:
        d = ImageDraw.Draw(sheet)
        d.text((56, 30), header, font=caveat(58), fill=head_col)
        d.line((56, 112, w - 56, 112), fill=(210, 200, 185), width=3)
    txt = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
    td = ImageDraw.Draw(txt)
    space = f.getlength(" ")
    for i, l in enumerate(lines):
        x = 56
        for word in l.split(" "):
            td.text((x, top + i * lh), word, font=f, fill=COBALT if word.startswith("#") else INK)
            x += f.getlength(word) + space
    pad = 9 * 3 + 16   # add_shadow's padding for these settings
    big = add_shadow(sheet, 8, 12, 9, 0.35)
    tl = Image.new("RGBA", big.size, (0, 0, 0, 0))
    tl.alpha_composite(txt, (pad, pad))
    return big, tl


def type_in(card_and_text, t, pos, z, rot=0.0, dur=1.6):
    sheet, txt = card_and_text
    add(Sprite(sheet, t, pos, rot=rot, z=z, enter="pop", enter_dur=0.35, boil=0.4))
    add(Sprite(txt, t + 0.35, pos, rot=rot, z=z + 1, enter="none", enter_dur=0,
               reveal=(t + 0.35, dur), boil=0.4))


def tick(text, seed, paper=PAPER_WHITE, dot=CHARTREUSE, size=66):
    """A paper check-mark circle followed by a caption strip."""
    c = paper_circle(96, dot, seed)
    ImageDraw.Draw(c).line([(26, 50), (42, 66), (72, 32)], fill=INK, width=11, joint="curve")
    s = text_strip(text, caveat(size), paper=paper, seed=seed + 1, sides="lr", shadow=False, max_w=760)
    out = Image.new("RGBA", (c.width + 14 + s.width, max(c.height, s.height)), (0, 0, 0, 0))
    out.alpha_composite(c, (0, (out.height - c.height) // 2))
    out.alpha_composite(s, (c.width + 14, (out.height - s.height) // 2))
    return add_shadow(out, 5, 8, 7, 0.3)


def fit_x(img, x, margin=8):
    """Nudge a centre x so the sprite stays on screen."""
    half = img.width / 2
    return min(max(x, half + margin), W - half - margin)


def ticks(items, t, x, y0, z, seed, gap=150, step=0.4, size=60, paper=PAPER_WHITE,
          dots=(CHARTREUSE, MUSTARD, PINK, SAGE, DUSTY_BLUE)):
    rng = np.random.default_rng(seed)
    for i, txt in enumerate(items):
        im = tick(txt, seed + 3 * i, paper=paper, dot=dots[i % len(dots)], size=size)
        xx = x if isinstance(x, (int, float)) else x[i]
        add(Sprite(im, t + i * step, (fit_x(im, xx), y0 + i * gap), rot=rng.uniform(-2.5, 2.5), z=z + i,
                   enter="slide_" + ("left", "right")[i % 2], enter_dur=0.35))


def clip_card(im, size, label, seed):
    """A raw-footage thumbnail: square frame with a black border and a duration tag."""
    th = square_thumb(im, size).convert("RGBA")
    c = Image.new("RGBA", (size + 20, size + 20), (24, 24, 26, 255))
    c.alpha_composite(th, (10, 10))
    d = ImageDraw.Draw(c, "RGBA")
    f = typewriter(30)
    tw = f.getlength(label)
    d.rounded_rectangle((size - tw - 14, size - 36, size + 6, size + 2), 6, fill=(0, 0, 0, 170))
    d.text((size - tw - 4, size - 34), label, font=f, fill=PAPER_WHITE)
    d.polygon([(26, 26), (26, 62), (56, 44)], fill=(255, 255, 255, 220))
    return add_shadow(c, 5, 8, 7, 0.32)


def palette_of(im, n=5):
    """The n main accent colours of an image: quantize only its saturated pixels, sort by hue."""
    import colorsys
    px = np.asarray(im.convert("RGB").resize((240, 240))).reshape(-1, 3).astype(np.float32) / 255
    mx, mn = px.max(1), px.min(1)
    sat = (mx - mn) / np.maximum(mx, 1e-6)
    vivid = px[(sat > 0.35) & (mx > 0.3)]
    if len(vivid) < n * 50:
        vivid = px
    strip = Image.fromarray((vivid[None] * 255).astype(np.uint8))
    q = strip.quantize(colors=n, method=Image.Quantize.MAXCOVERAGE)
    pal = q.getpalette()[:3 * n]
    cols = [tuple(pal[k:k + 3]) for k in range(0, 3 * n, 3)]
    return sorted(cols, key=lambda c: colorsys.rgb_to_hsv(*(x / 255 for x in c))[0])


def waveform(w, h, seed, n=8):
    """An animated voice waveform card (n looping frames)."""
    rng = np.random.default_rng(seed)
    base = rng.uniform(0.35, 1.0, 40)
    sheet = torn_sheet(w, h, PAPER_WHITE, seed, sides="", amp=0, grain=3)
    frames = []
    for f in range(n):
        im = sheet.copy()
        d = ImageDraw.Draw(im)
        d.ellipse((40, h / 2 - 50, 140, h / 2 + 50), fill=TERRACOTTA)
        d.polygon([(76, h / 2 - 26), (76, h / 2 + 26), (116, h / 2)], fill=PAPER_WHITE)
        bars, x0 = len(base), 180
        bw = (w - x0 - 40) / bars
        for i in range(bars):
            a = base[i] * (0.35 + 0.65 * abs(math.sin(i * 0.5 + f * 2 * math.pi / n)))
            bh = max(10, a * (h - 70))
            x = x0 + i * bw
            d.rounded_rectangle((x + 3, h / 2 - bh / 2, x + bw - 3, h / 2 + bh / 2), 5, fill=INK)
        frames.append(add_shadow(im, 8, 12, 9, 0.35))
    return frames


def arts():
    a = {n.split(".")[0]: load_art(n) for n in sorted(os.listdir(ART))}
    cat = Image.open(os.path.join(ART, "cat_neon.gif"))
    a["cat_frames"] = [f.convert("RGB") for f in ImageSequence.Iterator(cat)]
    return a


def papercut_clip():
    return footage("sketchbook_tour.mp4", 0.2, 3.4)


def flipbook_clip():
    return footage("sketchbook_flipbook.mp4", 4.5, 3.4)


# --------------------------------------------------------------------------- feature scenes
# Each takes about 3.5 s; t is when its background sheet has finished wiping in.

def scene_styles(t, z, seed, bg, wipe, title, note):
    background(t - 0.5, bg, seed, wipe, z)
    caption(title, t + 0.05, 230, z + 10, size=92, seed=seed + 1)
    play(phone(papercut_clip(), w=420), t + 0.3, (285, 900), z + 2, rot=-3)
    play(phone(flipbook_clip(), w=420), t + 0.6, (795, 900), z + 3, rot=3)
    add(Sprite(text_strip("papercut", marker(60), paper=MUSTARD, seed=seed + 2), t + 1.0, (285, 1390), rot=-3,
               z=z + 11, enter="pop", enter_dur=0.35))
    add(Sprite(text_strip("3D flip-book", marker(60), paper=COBALT, ink=PAPER_WHITE, seed=seed + 3), t + 1.25,
               (795, 1390), rot=2, z=z + 12, enter="pop", enter_dur=0.35))
    caption(note, t + 1.7, 1610, z + 13, size=68, seed=seed + 4, paper=CREAM, max_w=900)


def scene_palette(t, z, seed, bg, wipe, art, title, note):
    background(t - 0.5, bg, seed, wipe, z)
    caption(title, t + 0.05, 230, z + 10, size=88, seed=seed + 1)
    add(Sprite(cutout(art, 560, 560, seed + 2, tape="top"), t + 0.2, (540, 730), rot=-3, z=z + 2,
               enter="drop"))
    rng = np.random.default_rng(seed)
    for i, col in enumerate(palette_of(art)):
        dot = add_shadow(paper_circle(150, col, seed + 10 + i), 4, 7, 6, 0.3)
        add(Sprite(dot, t + 0.9 + i * 0.15, (140 + i * 200, 1180), rot=rng.uniform(-10, 10), z=z + 3 + i,
                   enter="pop", enter_dur=0.3))
    add(Sprite(text_strip("your palette, on every frame", marker(62), paper=PAPER_WHITE, seed=seed + 3),
               t + 1.8, (540, 1420), rot=-1.5, z=z + 11, enter="slide_up", enter_dur=0.35))
    caption(note, t + 2.2, 1600, z + 12, size=66, seed=seed + 4, paper=CREAM)


def scene_voice(t, z, seed, bg, wipe, title, note, pick=0):
    background(t - 0.5, bg, seed, wipe, z)
    caption(title, t + 0.05, 260, z + 10, size=92, seed=seed + 1)
    wf = waveform(920, 300, seed + 2)
    add(Sprite(wf[0], t + 0.3, (540, 690), rot=-1.5, z=z + 2, enter="pop", enter_dur=0.4, frames=wf,
               frame_dur=0.09))
    voices = ["warm", "deep", "bright"]
    for i, v in enumerate(voices):
        if i == pick:
            im = tick(v, seed + 5, dot=CHARTREUSE, size=64)
        else:
            im = text_strip(v, caveat(64), paper=CREAM, seed=seed + 6 + i)
        add(Sprite(im, t + 0.9 + i * 0.2, (200 + i * 340, 1020), rot=(-3, 2, -2)[i], z=z + 3 + i,
                   enter="pop", enter_dur=0.3))
    caption("pick a voice", t + 1.6, 1180, z + 11, size=60, seed=seed + 9, paper=PAPER_WHITE)
    add(Sprite(text_strip(note, marker(60), paper=MUSTARD, seed=seed + 10, max_w=900), t + 2.0, (540, 1500),
               rot=1.5, z=z + 12, enter="slide_up", enter_dur=0.35))


def scene_kit(t, z, seed, bg, wipe, title):
    background(t - 0.5, bg, seed, wipe, z)
    caption(title, t + 0.05, 230, z + 10, size=88, seed=seed + 1)
    cover = Image.open(os.path.join(OUT, "cover.jpg")).convert("RGB")
    add(Sprite(cutout(cover, 380, 680, seed + 2, tape="top"), t + 0.2, (255, 790), rot=-4, z=z + 2,
               enter="drop"))
    add(Sprite(text_strip("cover", marker(52), paper=MUSTARD, seed=seed + 3), t + 0.6, (255, 1170), rot=3,
               z=z + 9, enter="pop", enter_dur=0.3))
    type_in(card("Weekly sketchbook tour. Creating makes me happier... #sketchbooktour #inkdrawing "
                 "#collageart #artistsoninstagram", seed + 4, w=560, header="caption", size=38),
            t + 0.5, (760, 790), z + 3, rot=2, dur=1.3)
    ticks(["cover frame", "caption + hashtags", "music-ready: add trending audio in-app"], t + 1.6, 540, 1360,
          z + 12, seed + 10, gap=135, step=0.3, size=54)


def scene_edit(t, z, seed, bg, wipe, request, title="change anything. just ask."):
    background(t - 0.5, bg, seed, wipe, z)
    caption(title, t + 0.05, 230, z + 10, size=86, seed=seed + 1)
    type_in(card(request, seed + 2), t + 0.3, (540, 560), z + 2, rot=-1.5, dur=1.0)
    type_in(card("Done. Preview stills before the final render:", seed + 3, header="Claude", head_col=COBALT),
            t + 1.4, (540, 920), z + 4, rot=1.5, dur=0.6)
    rng = np.random.default_rng(seed)
    for i, at in enumerate((5.5, 22.5, 41.0)):
        th = cutout(footage("sketchbook_tour.mp4", at, 0.25)[0], 250, 440, seed + 10 + i, border=10)
        add(Sprite(th, t + 2.1 + i * 0.2, (230 + i * 310, 1430), rot=rng.uniform(-6, 6), z=z + 6 + i,
                   enter="drop", enter_dur=0.3))


def end_card(t, z, bg, line1, line2, cta, seed, from_dir="down", accent=COBALT):
    background(t - 0.5, bg, seed, from_dir, z)
    rng = np.random.default_rng(seed)
    add(Sprite(text_strip(line1, marker(84), paper=PAPER_WHITE, seed=seed + 1, max_w=940), t + 0.05,
               (540, 380), rot=-2, z=z + 2, enter="slide_left", enter_dur=0.4))
    add(Sprite(text_strip(line2, marker(72), paper=accent, ink=PAPER_WHITE, seed=seed + 2, max_w=940),
               t + 0.45, (540, 580), rot=1.5, z=z + 3, enter="slide_right", enter_dur=0.4))
    logo = paper_circle(330, CREAM, seed + 3)
    d = ImageDraw.Draw(logo)
    d.ellipse((115, 85, 215, 185), fill=TERRACOTTA)
    d.polygon([(150, 112), (150, 158), (192, 135)], fill=PAPER_WHITE)
    d.text((165 - caveat(54).getlength("studio") / 2, 196), "studio", font=caveat(54), fill=INK)
    add(Sprite(add_shadow(logo), t + 1.0, (540, 980), rot=-4, z=z + 4, enter="pop", enter_dur=0.45))
    add(Sprite(text_strip(BRAND, marker(96), paper=PAPER_WHITE if bg == CHARCOAL else INK,
                          ink=INK if bg == CHARCOAL else PAPER_WHITE, seed=seed + 4, max_w=1000), t + 1.3,
               (540, 1250), rot=-1.5, z=z + 5, enter="pop", enter_dur=0.45))
    add(Sprite(text_strip("made with Claude", caveat(66), paper=CREAM, seed=seed + 5), t + 1.6,
               (540, 1410), rot=1.5, z=z + 6, enter="pop", enter_dur=0.4))
    add(Sprite(text_strip(cta, marker(72), paper=CHARTREUSE, seed=seed + 6), t + 2.1, (540, 1610), rot=-2,
               z=z + 7, enter="slide_up", enter_dur=0.45))
    for i, (sx, sy, sc, col) in enumerate(((150, 1000, 110, PAPER_WHITE), (930, 900, 90, TERRACOTTA),
                                           (920, 1130, 70, accent), (160, 1720, 80, PAPER_WHITE))):
        add(Sprite(star(sc, col, seed + 10 + i), t + 2.4 + i * 0.12, (sx, sy), rot=rng.uniform(-20, 20),
                   z=z + 8, enter="pop", enter_dur=0.3))
    return t + 4.5


# --------------------------------------------------------------------------- ad 1: artists

def build_artists():
    A = arts()
    rng = np.random.default_rng(1)

    # 0: hook - "You paint." (0 - 3)
    z = 0
    background(0, MUSTARD, 1001, None, z)
    for i, (name, pos, r) in enumerate((("flowers_vase", (300, 560), -8), ("portrait_bob", (790, 620), 6),
                                        ("car_front", (330, 1330), 5), ("blue_flowers", (790, 1330), -6))):
        add(Sprite(cutout(A[name], 430, 430, 1010 + i, tape="top"), 0.1 + i * 0.2, pos, rot=r, z=z + 2 + i,
                   enter="drop", enter_dur=0.35))
    add(Sprite(text_strip("You paint.", marker(140), seed=1020), 0.9, (540, 960), rot=-3, z=z + 10,
               enter="pop", enter_dur=0.45))

    # 1: the chores (3 - 6.5)
    t, z = 3.0, 100
    background(t - 0.5, PINK, 1101, "right", z)
    caption("...then comes the reel.", t + 0.05, 300, z + 10, size=96, seed=1110)
    chores = [("trim 47 clips", 330, 640, -6), ("write captions", 760, 760, 5), ("find music", 320, 940, 4),
              ("pick a cover", 750, 1100, -4), ("hashtags?!", 380, 1260, -3)]
    for i, (txt, x, y, r) in enumerate(chores):
        im = text_strip(txt, typewriter(56), paper=PAPER_WHITE if i % 2 else CREAM, seed=1120 + i,
                        sides="tblr", max_w=600)
        add(Sprite(im, t + 0.5 + i * 0.22, (x, y), rot=r, z=z + 2 + i, enter="pop", enter_dur=0.3))
        ts = t + 1.9 + i * 0.13
        add(Sprite(strike(int(im.width * 0.85), 1130 + i), ts, (x, y), rot=r + rng.uniform(-4, 4), z=z + 8,
                   enter="none", enter_dur=0, reveal=(ts, 0.2), boil=0.5))
    add(Sprite(text_strip("not anymore.", marker(96), paper=COBALT, ink=PAPER_WHITE, seed=1140), t + 2.6,
               (540, 1560), rot=2, z=z + 12, enter="slide_up", enter_dur=0.4))

    # 2: ask Claude (6.5 - 9.5)
    t, z = 6.5, 200
    background(t - 0.5, SAGE, 1201, "left", z)
    for i, (name, pos, r) in enumerate((("toast_collage", (250, 380), -7), ("clock_collage", (540, 330), 3),
                                        ("flowers_mosaic", (830, 390), 8))):
        add(Sprite(cutout(A[name], 300, 300, 1210 + i, border=10), t + 0.05 + i * 0.12, pos, rot=r,
                   z=z + 2 + i, enter="drop", enter_dur=0.3))
    type_in(card("Turn this week's paintings into a reel. Papercut style, my handwriting vibe.", 1220),
            t + 0.5, (540, 980), z + 10, rot=-1.5, dur=1.4)
    caption("just drop your art in", t + 1.2, 1540, z + 12, size=80, seed=1230, paper=CREAM)

    # 3: the reel builds itself (9.5 - 14)
    t, z = 9.5, 300
    background(t - 0.5, CREAM, 1301, "up", z)
    play(phone(papercut_clip(), w=480), t + 0.05, (290, 860), z + 2, rot=-4)
    ticks(["story written", "hand-lettered text", "papercut motion", "full HD 9:16"], t + 0.8, 790, 520,
          z + 5, 1310, gap=210, step=0.45, size=56)
    add(Sprite(text_strip("in minutes, not evenings", marker(74), paper=MUSTARD, seed=1330), t + 2.9,
               (540, 1680), rot=-2, z=z + 12, enter="pop", enter_dur=0.45))

    # 4 - 8: the feature tour (14 - 31.5)
    scene_styles(14.0, 400, 1401, COBALT, "right", "pick your look.",
                 "or float the flip-book over your own studio footage")
    scene_palette(17.5, 500, 1501, PINK, "left", A["clock_collage"], "it paints with your colours.",
                  "pulled straight from your art")
    scene_voice(21.0, 600, 1601, SAGE, "up", "want a voice-over?", "reads your captions, timed to every cut")
    scene_kit(24.5, 700, 1701, DUSTY_BLUE, "right", "the whole post, done.")
    scene_edit(28.0, 800, 1801, CREAM, "left", "Make the captions bigger and slow down the ending.")

    return end_card(32.0, 900, MUSTARD, "You paint.", "Claude handles the reels.", "Start your first reel >",
                    1901)


# --------------------------------------------------------------------------- ad 2: UGC / content creators

def build_creators():
    A = arts()
    rng = np.random.default_rng(2)

    # 0: hook - raw footage pile (0 - 3)
    z = 0
    background(0, CHARCOAL, 2001, None, z)
    names = ["portrait_bob", "car_front", "flowers_vase", "toast_collage", "camera_polaroid", "blue_flowers",
             "car_awning", "clock_collage", "flowers_mosaic", "portraits_stripes", "spread_cars",
             "cat_neon"]
    for i, name in enumerate(names):
        x, y = 160 + (i % 4) * 253 + rng.uniform(-30, 30), 760 + (i // 4) * 300 + rng.uniform(-30, 30)
        lbl = f"{rng.integers(0, 4)}:{rng.integers(10, 59):02d}"
        add(Sprite(clip_card(A[name], 220, lbl, 2010 + i), 0.15 + i * 0.09, (x, y), rot=rng.uniform(-10, 10),
                   z=z + 2 + i, enter="drop", enter_dur=0.25))
    add(Sprite(text_strip("POV: you filmed", marker(92), paper=PAPER_WHITE, seed=2030), 0.05, (540, 300),
               rot=-2, z=z + 20, enter="slide_left", enter_dur=0.35))
    add(Sprite(text_strip("3 hours of content", marker(92), paper=CHARTREUSE, seed=2031), 0.4, (540, 450),
               rot=1.5, z=z + 21, enter="slide_right", enter_dur=0.35))
    add(Sprite(text_strip("...for a 30-second post", caveat(80), paper=CREAM, seed=2032), 1.6, (540, 1700),
               rot=-1, z=z + 22, enter="pop", enter_dur=0.35))

    # 1: Claude prompt (3 - 6)
    t, z = 3.0, 100
    background(t - 0.5, CHARTREUSE, 2101, "down", z)
    caption("skip the timeline.", t + 0.05, 330, z + 10, size=100, seed=2110)
    type_in(card("Cut this into 3 versions with different hooks. Captions on, 9:16 for Reels, TikTok "
                 "& Shorts.", 2120), t + 0.4, (540, 930), z + 4, rot=1.5, dur=1.5)
    add(Sprite(star(120, COBALT, 2130), t + 2.0, (900, 1400), rot=12, z=z + 12, enter="pop"))

    # 2: three hooks (6 - 10.5)
    t, z = 6.0, 200
    background(t - 0.5, COBALT, 2201, "left", z)
    caption("3 hooks. one upload.", t + 0.05, 260, z + 10, size=96, seed=2210)
    sets = [([A["portrait_bob"], A["portraits_stripes"], A["camera_polaroid"]],
             ["wait for the last one", "3 tools I use daily", "save this"], "A"),
            ([A["car_front"], A["car_awning"], A["spread_cars"]],
             ["nobody talks about this", "here's the trick", "follow for part 2"], "B"),
            ([A["flowers_vase"], A["blue_flowers"], A["flowers_mosaic"]],
             ["I tried it for 7 days", "day 1 vs day 7", "worth it?"], "C")]
    for i, (scr, caps, lab) in enumerate(sets):
        ph = phone(scr, caps, w=320, label=f"hook {lab}")
        add(Sprite(ph[0], t + 0.4 + i * 0.3, (195 + i * 345, 960), rot=(-5, 0, 5)[i], z=z + 2 + i,
                   enter="slide_up", enter_dur=0.45, frames=ph, frame_dur=0.6 + 0.07 * i))
    add(Sprite(text_strip("test what actually lands", marker(70), paper=CHARTREUSE, seed=2220), t + 2.4,
               (540, 1650), rot=-2, z=z + 12, enter="pop", enter_dur=0.4))

    # 3 - 7: the feature tour (10.5 - 28)
    scene_styles(10.5, 300, 2301, PINK, "right", "two looks. zero editing.",
                 "the flip-book floats over your own clips")
    scene_voice(14.0, 400, 2401, MUSTARD, "up", "no mic? no retakes.", "voice-over in seconds", pick=1)

    t, z = 17.5, 500
    background(t - 0.5, PAPER_WHITE, 2501, "right", z)
    caption("Claude handles the busywork:", t + 0.05, 260, z + 10, size=84, seed=2510, paper=CREAM)
    ticks(["story + pacing written for you", "hand-lettered captions", "colours pulled from your footage",
           "full HD 9:16 for every platform"], t + 0.4, (500, 580, 500, 580), 560, z + 2, 2520, gap=200,
          step=0.4, size=58, paper=CREAM)
    add(Sprite(text_strip("you stay on camera.", marker(84), paper=INK, ink=PAPER_WHITE, seed=2540),
               t + 2.2, (540, 1560), rot=2, z=z + 12, enter="pop", enter_dur=0.4))

    scene_kit(21.0, 600, 2601, SAGE, "left", "post-ready, every time.")
    scene_edit(24.5, 700, 2701, CREAM, "down", "Hook B, but make the first line punchier.",
               title="notes? just type them.")

    return end_card(28.5, 800, CHARCOAL, "Film it.", "Claude ships it.", "Post more. Edit less >", 2801,
                    accent=TERRACOTTA)


# --------------------------------------------------------------------------- ad 3: beginners

def build_beginners():
    A = arts()

    # 0: hook (0 - 3)
    z = 0
    background(0, DUSTY_BLUE, 3001, None, z)
    add(Sprite(text_strip("Never edited a video?", marker(84), seed=3010), 0.1, (540, 820), rot=-2, z=z + 2,
               enter="pop", enter_dur=0.45))
    add(Sprite(text_strip("Good.", marker(150), paper=MUSTARD, seed=3011), 1.2, (540, 1060), rot=3,
               z=z + 3, enter="pop", enter_dur=0.45))
    add(Sprite(text_strip("you don't need to.", caveat(80), paper=CREAM, seed=3012), 1.9, (560, 1250),
               rot=-1, z=z + 4, enter="pop", enter_dur=0.4))

    def step(n, title, t, z, bg, seed, wipe):
        background(t - 0.5, bg, seed, wipe, z)
        num = marker(110)
        circ = paper_circle(170, INK, seed + 1)
        ImageDraw.Draw(circ).text((85 - num.getlength(str(n)) / 2, 8), str(n), font=num, fill=PAPER_WHITE)
        add(Sprite(add_shadow(circ), t + 0.05, (170, 250), rot=-6, z=z + 20, enter="pop", enter_dur=0.35))
        add(Sprite(text_strip(title, marker(76), seed=seed + 2, max_w=700), t + 0.25, (610, 260), rot=-2,
                   z=z + 21, enter="slide_right", enter_dur=0.35))

    # 1: step 1 - add your photos (3 - 6.5)
    t, z = 3.0, 100
    step(1, "add your photos", t, z, CREAM, 3101, "right")
    tray = torn_sheet(860, 640, SAGE, 3110, sides="t", amp=18, grain=5)
    add(Sprite(add_shadow(tray), t + 0.2, (540, 1250), z=z + 1, enter="slide_up", enter_dur=0.4))
    for i, (name, pos, r) in enumerate((("flowers_vase", (320, 1040), -9), ("portrait_bob", (560, 980), 4),
                                        ("toast_collage", (790, 1060), 9), ("blue_flowers", (420, 1320), 6),
                                        ("car_awning", (700, 1330), -5))):
        add(Sprite(cutout(A[name], 300, 300, 3120 + i, border=10), t + 0.6 + i * 0.22, pos, rot=r,
                   z=z + 2 + i, enter="drop", enter_dur=0.3))
    caption("phone pics or clips are fine", t + 1.9, 1720, z + 12, size=76, seed=3130, paper=PAPER_WHITE)

    # 2: step 2 - describe the vibe (6.5 - 10)
    t, z = 6.5, 200
    step(2, "describe the vibe", t, z, PINK, 3201, "left")
    type_in(card("Something cozy and slow, with a bit of handwriting. 20 seconds.", 3210),
            t + 0.4, (540, 900), z + 4, rot=-1, dur=1.3)
    caption("in your own words.", t + 1.9, 1420, z + 10, size=84, seed=3220)
    caption("no jargon, no timeline", t + 2.3, 1580, z + 11, size=70, seed=3221, paper=CREAM)

    # 3: step 3 - post (10 - 14), with the pro work Claude did
    t, z = 10.0, 300
    step(3, "post it", t, z, SAGE, 3301, "up")
    play(phone(papercut_clip(), w=440), t + 0.3, (265, 1020), z + 2, rot=-3)
    ticks(["story + pacing", "hand-lettered text", "colours matched", "full HD 9:16"], t + 1.0, 775, 640,
          z + 5, 3310, gap=200, step=0.4, size=54,
          dots=(CHARTREUSE, MUSTARD, PINK, PAPER_WHITE))

    # 4 - 7: the feature tour (14 - 28)
    scene_styles(14.0, 400, 3401, MUSTARD, "right", "pick a look.", "both made for you. no skills needed")
    scene_voice(17.5, 500, 3501, DUSTY_BLUE, "left", "want a voice? pick one.",
                "it reads your captions for you", pick=2)
    scene_kit(21.0, 600, 3601, PINK, "up", "and the bits you'd forget:")
    scene_edit(24.5, 700, 3701, CREAM, "right", "Can you make the text bigger?",
               title="not quite right? just say so.")

    # 8: before / after (28 - 31.5)
    t, z = 28.0, 800
    background(t - 0.5, PAPER_WHITE, 3801, "down", z)
    add(Sprite(cutout(A["clock_collage"], 400, 400, 3810, tape="top"), t + 0.05, (540, 560), rot=-4,
               z=z + 2, enter="drop"))
    old = text_strip("an evening of tutorials", typewriter(58), paper=CREAM, seed=3820, sides="tblr")
    add(Sprite(old, t + 0.4, (540, 1000), rot=-2, z=z + 3, enter="pop", enter_dur=0.35))
    add(Sprite(strike(int(old.width * 0.9), 3821), t + 1.0, (540, 1000), rot=-4, z=z + 4, enter="none",
               enter_dur=0, reveal=(t + 1.0, 0.25), boil=0.5))
    add(Sprite(text_strip("a few minutes with Claude", marker(76), paper=MUSTARD, seed=3830), t + 1.4,
               (540, 1180), rot=1.5, z=z + 5, enter="pop", enter_dur=0.4))
    caption("and it looks like a pro made it.", t + 2.0, 1480, z + 6, size=80, seed=3840, paper=CREAM)

    return end_card(32.0, 900, DUSTY_BLUE, "Pro-looking reels.", "Zero editing skills.",
                    "Make your first reel >", 3901, accent=TERRACOTTA)


ADS = {
    "artists": (build_artists, "ad_artists_you_paint.mp4", 11.5),
    "creators": (build_creators, "ad_ugc_creators.mp4", 7.5),
    "beginners": (build_beginners, "ad_beginners.mp4", 12.0),
}


# --------------------------------------------------------------------------- render

def setup(build):
    mv.SPRITES.clear()
    mv.DURATION = build()
    mv.SPRITES.sort(key=lambda s: s.z)
    sheets = [s for s in mv.SPRITES if s.img.size[0] >= W and s.img.size[1] >= H]
    for s in mv.SPRITES:
        later = [b.t0 + b.enter_dur for b in sheets if b.z > s.z]
        if later:
            end = min(later)
            s.t1 = end if s.t1 is None else min(s.t1, end)
    if mv.GRAIN is None:
        rng = np.random.default_rng(99)
        yy, xx = np.mgrid[0:H, 0:W]
        vig = 1 - 0.18 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2
        mv.GRAIN = [(vig.astype(np.float32), rng.normal(0, 2.5, (H, W)).astype(np.float32)) for _ in range(3)]


def still(t):
    return Image.frombytes("RGB", (W, H), mv.render_frame(int(t * FPS)))


def render(name):
    build, fname, cover_t = ADS[name]
    setup(build)
    if "--preview" in sys.argv:
        pdir = os.path.join(ADS_OUT, "preview")
        os.makedirs(pdir, exist_ok=True)
        times = [float(a) for a in sys.argv[sys.argv.index("--preview") + 1:]]
        for ts in times or [x + 0.5 for x in range(0, int(mv.DURATION), 2)]:
            still(ts).save(os.path.join(pdir, f"{name}_t{ts:05.1f}.jpg"), quality=85)
        return
    n = int(mv.DURATION * FPS)
    out = os.path.join(ADS_OUT, fname)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-r", str(OUT_FPS), "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for buf in pool.imap(mv.render_frame, range(n), chunksize=4):
            proc.stdin.write(buf)
    proc.stdin.close()
    proc.wait()
    still(cover_t).save(os.path.join(ADS_OUT, fname.replace(".mp4", "_cover.jpg")), quality=90)
    print(f"wrote {out} ({mv.DURATION:.1f}s)")


def main():
    os.makedirs(ADS_OUT, exist_ok=True)
    names = [a for a in sys.argv[1:] if a in ADS] or list(ADS)
    for name in names:
        render(name)


if __name__ == "__main__":
    main()
