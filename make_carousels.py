#!/usr/bin/env python3
"""Carousel and single-image ads for Creator Studio, matching the three video ads.

  output/ads/carousel_<ad>/slide_1.jpg ...   1080x1350 (4:5) carousel slides
  output/ads/image_<ad>_square.jpg           1080x1080 single-image feed ad
  output/ads/image_<ad>_story.jpg            1080x1920 single-image story ad

Same papercut kit as make_ads.py, laid out as still collages.

Usage:  python3 make_carousels.py            # everything
        python3 make_carousels.py artists    # one ad
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

import filters
import make_ads as ma
from make_video import (CHARCOAL, CHARTREUSE, COBALT, CREAM, DUSTY_BLUE, INK, MUSTARD, OUT, PAPER_WHITE,
                        PINK, SAGE, TERRACOTTA, add_shadow, caveat, cutout, marker, paper_circle,
                        paper_texture, star, strike, text_strip, torn_sheet, typewriter)

ADS_OUT = os.path.join(OUT, "ads")
LOOK = None   # filters.Look from --filter / --lut


class Slide:
    def __init__(self, bg, seed, w=1080, h=1350):
        self.w, self.h = w, h
        self.dark = sum(bg) < 300
        self.im = Image.fromarray(paper_texture(w, h, bg, seed, 6)).convert("RGBA")
        self.rng = np.random.default_rng(seed)

    def put(self, img, x, y, rot=0.0, fit=True):
        if abs(rot) > 0.05:
            img = img.rotate(rot, Image.BICUBIC, expand=True)
        if fit:
            x = min(max(x, img.width / 2), self.w - img.width / 2)
        self.im.alpha_composite(img, (int(x - img.width / 2), int(y - img.height / 2)))
        return img

    def strip(self, text, y, font, paper=PAPER_WHITE, ink=INK, rot=None, x=None, max_w=900, seed=0):
        r = self.rng.uniform(-2.5, 2.5) if rot is None else rot
        return self.put(text_strip(text, font, paper=paper, ink=ink, seed=seed, max_w=max_w),
                        self.w / 2 if x is None else x, y, r)

    def ticks(self, items, x, y0, gap, size=56, paper=PAPER_WHITE, dots=(CHARTREUSE, MUSTARD, PINK, SAGE),
              seed=0):
        for i, txt in enumerate(items):
            self.put(ma.tick(txt, seed + 3 * i, paper=paper, dot=dots[i % len(dots)], size=size),
                     x, y0 + i * gap, self.rng.uniform(-2, 2))

    def stars(self, spots, seed):
        for i, (x, y, s, c) in enumerate(spots):
            self.put(star(s, c, seed + i), x, y, self.rng.uniform(-20, 20), fit=False)

    def counter(self, i, n, swipe=True):
        d = ImageDraw.Draw(self.im)
        f = caveat(44)
        lab = f"{i}/{n}" + ("   swipe >" if swipe else "")
        d.text((self.w - 40 - f.getlength(lab), self.h - 78), lab, font=f, fill=PAPER_WHITE if self.dark else INK)

    def finish(self):
        arr = np.asarray(self.im.convert("RGB")).astype(np.float32)
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        vig = 1 - 0.16 * (((xx - self.w / 2) / (self.w / 2)) ** 2 + ((yy - self.h / 2) / (self.h / 2)) ** 2) / 2
        arr = arr * vig[..., None] + np.random.default_rng(5).normal(0, 2.5, (self.h, self.w))[..., None]
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        return Image.fromarray(LOOK.apply(arr) if LOOK else arr)


def brand_block(s, y, bg_dark=False):
    logo = paper_circle(220, CREAM, 77)
    d = ImageDraw.Draw(logo)
    d.ellipse((76, 50, 144, 118), fill=TERRACOTTA)
    d.polygon([(100, 68), (100, 100), (128, 84)], fill=PAPER_WHITE)
    d.text((110 - caveat(38).getlength("studio") / 2, 128), "studio", font=caveat(38), fill=INK)
    s.put(add_shadow(logo), s.w / 2, y, -4)
    s.strip(ma.BRAND, y + 200, marker(84), paper=PAPER_WHITE if bg_dark else INK,
            ink=INK if bg_dark else PAPER_WHITE, rot=-1.5, max_w=1000, seed=78)
    s.strip("made with Claude", y + 320, caveat(58), paper=CREAM, rot=1.5, seed=79)


def price_slide(bg, seed, k, n, cta, accent=COBALT):
    """Closing slide: lifetime access at the price, the tagline and the CTA."""
    s = Slide(bg, seed)
    dark = sum(bg) < 300
    s.strip("Lifetime access.", 150, marker(92), rot=-2, seed=seed + 1)
    s.put(ma.price_badge(520, seed + 2, color=CHARTREUSE if accent == TERRACOTTA else TERRACOTTA,
                         ink=INK if accent == TERRACOTTA else PAPER_WHITE), 540, 530, 6)
    s.strip(ma.TAGLINE, 870, marker(68), paper=accent, ink=PAPER_WHITE, rot=1.5, seed=seed + 3, max_w=1000)
    s.strip(ma.BRAND + " · made with Claude", 1010, caveat(56), paper=PAPER_WHITE if dark else CREAM,
            rot=-1, seed=seed + 4)
    s.strip(cta, 1170, marker(68), paper=CHARTREUSE, rot=-2, seed=seed + 5)
    s.stars(((150, 380, 100, PAPER_WHITE), (930, 330, 80, accent), (940, 720, 90, PAPER_WHITE)), seed + 6)
    s.counter(k, n, swipe=False)
    return s


def phone_still(clip_name, at, w):
    return ma.phone([ma.footage(clip_name, at, 0.25)[0]], w=w)[0]


def two_looks(s, y, w=380):
    s.put(phone_still("sketchbook_tour.mp4", 1.5, w), 290, y, -3)
    s.put(phone_still("sketchbook_flipbook.mp4", 6.0, w), 790, y, 3)
    s.strip("papercut", y + 370, marker(54), paper=MUSTARD, rot=-3, x=290, seed=81)
    s.strip("3D flip-book", y + 370, marker(54), paper=COBALT, ink=PAPER_WHITE, rot=2, x=790, seed=82)


def voice_block(s, y, pick, seed):
    s.put(ma.waveform(900, 260, seed)[3], s.w / 2, y, -1.5)
    for i, v in enumerate(("warm", "deep", "bright")):
        im = ma.tick(v, seed + 5, size=60) if i == pick else text_strip(v, caveat(60), paper=CREAM, seed=seed + i)
        s.put(im, 200 + i * 340, y + 260, (-3, 2, -2)[i])


def chat(s, text, y, seed, header="ask Claude", w=900, size=48, rot=-1.5, x=None, head_col=TERRACOTTA):
    big, txt = ma.card(text, seed, w=w, header=header, size=size, head_col=head_col)
    big = big.copy()
    big.alpha_composite(txt)
    s.put(big, s.w / 2 if x is None else x, y, rot)


def kit_block(s, y, seed):
    cover = Image.open(os.path.join(OUT, "cover.jpg")).convert("RGB")
    s.put(cutout(cover, 330, 590, seed, tape="top"), 245, y, -4)
    chat(s, "Weekly sketchbook tour. Creating makes me happier... #sketchbooktour #inkdrawing "
            "#collageart #artistsoninstagram", y - 40, seed + 1, header="caption", w=560, size=36, rot=2, x=740)


def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, quality=92)


# --------------------------------------------------------------------------- artists

def artists(A):
    n, slides = 8, []

    s = Slide(MUSTARD, 1)
    for i, (name, x, y, r) in enumerate((("flowers_vase", 260, 300, -8), ("portrait_bob", 820, 330, 6),
                                         ("car_front", 270, 1010, 5), ("blue_flowers", 820, 1010, -6))):
        s.put(cutout(A[name], 400, 400, 10 + i, tape="top"), x, y, r)
    s.strip("You paint.", 600, marker(130), rot=-3, seed=20)
    s.strip("Claude handles the reels.", 770, marker(66), paper=COBALT, ink=PAPER_WHITE, rot=2, seed=21)
    s.counter(1, n)
    slides.append(s)

    s = Slide(PINK, 2)
    s.strip("the painting is the fun part.", 150, caveat(84), seed=30)
    s.strip("then comes the reel:", 290, caveat(84), paper=CREAM, seed=31)
    for i, (txt, x, y, r) in enumerate((("trim 47 clips", 330, 500, -6), ("write captions", 760, 610, 5),
                                        ("find music", 320, 760, 4), ("pick a cover", 750, 880, -4),
                                        ("hashtags?!", 380, 1010, -3))):
        im = s.put(text_strip(txt, typewriter(54), paper=PAPER_WHITE if i % 2 else CREAM, seed=32 + i,
                              sides="tblr"), x, y, r)
        s.put(strike(int(im.width * 0.85), 40 + i), x, y, r + 2)
    s.strip("not anymore.", 1180, marker(92), paper=COBALT, ink=PAPER_WHITE, rot=2, seed=45)
    s.counter(2, n)
    slides.append(s)

    s = Slide(SAGE, 3)
    s.strip("1. drop your art in", 150, marker(78), seed=50)
    for i, (name, x, r) in enumerate((("toast_collage", 250, -7), ("clock_collage", 540, 3),
                                      ("flowers_mosaic", 830, 8))):
        s.put(cutout(A[name], 290, 290, 51 + i, border=10), x, 400, r)
    chat(s, "Turn this week's paintings into a reel. Papercut style, my handwriting vibe.", 780, 55)
    s.ticks(["story written for you", "hand-lettered captions"], 540, 1080, 125, size=54, seed=56)
    s.counter(3, n)
    slides.append(s)

    s = Slide(COBALT, 4)
    s.strip("2. pick your look", 140, marker(78), seed=60)
    two_looks(s, 620)
    s.strip("or float the flip-book over your own studio footage", 1210, caveat(56), paper=CREAM, seed=61,
            max_w=980)
    s.counter(4, n)
    slides.append(s)

    s = Slide(CREAM, 5)
    s.strip("3. your colours. your voice.", 140, marker(70), seed=70)
    s.put(cutout(A["clock_collage"], 380, 380, 71, tape="top"), 300, 450, -4)
    for i, col in enumerate(ma.palette_of(A["clock_collage"])):
        s.put(add_shadow(paper_circle(110, col, 72 + i), 3, 5, 5, 0.3), 620 + (i % 3) * 140,
              370 + (i // 3) * 150, s.rng.uniform(-8, 8))
    s.strip("palette pulled from your art", 690, caveat(56), paper=PAPER_WHITE, x=760, seed=78, max_w=520)
    voice_block(s, 920, 0, 80)
    s.counter(5, n)
    slides.append(s)

    s = Slide(DUSTY_BLUE, 6)
    s.strip("the whole post, done.", 140, marker(78), seed=90)
    kit_block(s, 560, 91)
    s.ticks(["cover frame", "caption + hashtags", "music-ready, full HD 9:16"], 540, 990, 120, size=52, seed=93)
    s.counter(6, n)
    slides.append(s)

    s = Slide(MUSTARD, 7)
    chat(s, "Make the captions bigger and slow down the ending.", 200, 100, rot=-1)
    s.strip("change anything. just ask.", 420, marker(64), paper=PAPER_WHITE, rot=1.5, seed=101)
    brand_block(s, 680)
    s.strip("Start your first reel >", 1230, marker(66), paper=CHARTREUSE, rot=-2, seed=102)
    s.counter(7, n)
    slides.append(s)
    slides.append(price_slide(MUSTARD, 105, 8, n, "Start your first reel >"))
    return slides


# --------------------------------------------------------------------------- UGC creators

def creators(A):
    n, slides = 7, []
    rng = np.random.default_rng(9)

    s = Slide(CHARCOAL, 11)
    s.strip("POV: you filmed", 150, marker(88), rot=-2, seed=110)
    s.strip("3 hours of content", 290, marker(88), paper=CHARTREUSE, rot=1.5, seed=111)
    names = ["portrait_bob", "car_front", "flowers_vase", "toast_collage", "camera_polaroid", "blue_flowers",
             "car_awning", "clock_collage"]
    for i, name in enumerate(names):
        s.put(ma.clip_card(A[name], 220, f"{rng.integers(0, 4)}:{rng.integers(10, 59):02d}", 112 + i),
              160 + (i % 4) * 253 + rng.uniform(-20, 20), 560 + (i // 4) * 290, rng.uniform(-9, 9))
    s.strip("...for a 30-second post?", 1150, caveat(80), paper=CREAM, seed=120)
    s.counter(1, n)
    slides.append(s)

    s = Slide(COBALT, 12)
    s.strip("one upload. 3 hooks.", 140, marker(80), seed=130)
    sets = [(A["portrait_bob"], "wait for the last one", "A"), (A["car_front"], "nobody talks about this", "B"),
            (A["flowers_vase"], "I tried it for 7 days", "C")]
    for i, (im, cap, lab) in enumerate(sets):
        s.put(ma.phone([im], [cap], w=320, label=f"hook {lab}")[0], 195 + i * 345, 640, (-5, 0, 5)[i])
    s.strip("test what actually lands", 1170, marker(66), paper=CHARTREUSE, rot=-2, seed=131)
    s.counter(2, n)
    slides.append(s)

    s = Slide(PINK, 13)
    s.strip("two looks. zero editing.", 140, marker(76), seed=140)
    two_looks(s, 620)
    s.strip("the flip-book floats over your own clips", 1210, caveat(58), paper=CREAM, seed=141, max_w=980)
    s.counter(3, n)
    slides.append(s)

    s = Slide(MUSTARD, 14)
    s.strip("no mic? no retakes.", 150, marker(84), seed=150)
    voice_block(s, 480, 1, 151)
    s.strip("pick a voice. it reads your captions.", 960, caveat(64), paper=PAPER_WHITE, seed=152)
    s.strip("voice-over in seconds", 1120, marker(70), paper=INK, ink=PAPER_WHITE, rot=1.5, seed=153)
    s.counter(4, n)
    slides.append(s)

    s = Slide(PAPER_WHITE, 15)
    s.strip("Claude handles the busywork:", 130, caveat(80), paper=CREAM, seed=160)
    s.ticks(["story + pacing written for you", "hand-lettered captions", "colours pulled from your footage",
             "cover, caption + hashtags", "full HD 9:16, music-ready"], 540, 330, 150, size=56, paper=CREAM,
            seed=161)
    chat(s, "Hook B, but make the first line punchier.", 1130, 170, w=860, size=44, rot=1)
    s.counter(5, n)
    slides.append(s)

    s = Slide(CHARCOAL, 16)
    s.strip("Film it.", 150, marker(96), rot=-2, seed=180)
    s.strip("Claude ships it.", 300, marker(84), paper=TERRACOTTA, ink=PAPER_WHITE, rot=1.5, seed=181)
    brand_block(s, 560, bg_dark=True)
    s.strip("Post more. Edit less >", 1130, marker(68), paper=CHARTREUSE, rot=-2, seed=182)
    s.stars(((140, 600, 100, PAPER_WHITE), (940, 520, 80, TERRACOTTA), (930, 760, 70, CHARTREUSE)), 183)
    s.counter(6, n)
    slides.append(s)
    slides.append(price_slide(CHARCOAL, 185, 7, n, "Post more. Edit less >", accent=TERRACOTTA))
    return slides


# --------------------------------------------------------------------------- beginners

def step_head(s, k, title, seed):
    num = marker(100)
    c = paper_circle(150, INK, seed)
    ImageDraw.Draw(c).text((75 - num.getlength(str(k)) / 2, 6), str(k), font=num, fill=PAPER_WHITE)
    s.put(add_shadow(c), 150, 150, -6)
    s.strip(title, 160, marker(72), rot=-2, x=620, seed=seed + 1, max_w=700)


def beginners(A):
    n, slides = 7, []

    s = Slide(DUSTY_BLUE, 21)
    s.strip("Never edited a video?", 430, marker(84), rot=-2, seed=210)
    s.strip("Good.", 640, marker(150), paper=MUSTARD, rot=3, seed=211)
    s.strip("you don't need to.", 840, caveat(84), paper=CREAM, rot=-1, seed=212)
    s.stars(((170, 230, 110, PAPER_WHITE), (920, 260, 90, TERRACOTTA), (900, 1080, 100, MUSTARD)), 213)
    s.counter(1, n)
    slides.append(s)

    s = Slide(CREAM, 22)
    step_head(s, 1, "add your photos", 220)
    s.put(add_shadow(torn_sheet(860, 640, SAGE, 223, sides="t", amp=18, grain=5)), 540, 800)
    for i, (name, x, y, r) in enumerate((("flowers_vase", 320, 600, -9), ("portrait_bob", 560, 540, 4),
                                         ("toast_collage", 790, 620, 9), ("blue_flowers", 420, 880, 6),
                                         ("car_awning", 700, 890, -5))):
        s.put(cutout(A[name], 290, 290, 224 + i, border=10), x, y, r)
    s.strip("phone pics or clips are fine", 1200, caveat(70), seed=230)
    s.counter(2, n)
    slides.append(s)

    s = Slide(PINK, 23)
    step_head(s, 2, "describe the vibe", 240)
    chat(s, "Something cozy and slow, with a bit of handwriting. 20 seconds.", 560, 243)
    s.strip("in your own words.", 880, caveat(84), seed=244)
    s.strip("no jargon, no timeline", 1030, caveat(70), paper=CREAM, seed=245)
    s.counter(3, n)
    slides.append(s)

    s = Slide(SAGE, 24)
    step_head(s, 3, "post it", 250)
    s.put(phone_still("sketchbook_tour.mp4", 1.5, 420), 270, 760, -3)
    s.ticks(["story + pacing", "hand-lettered text", "colours matched", "papercut or flip-book",
             "full HD 9:16"], 790, 430, 150, size=50, dots=(CHARTREUSE, MUSTARD, PINK, PAPER_WHITE), seed=253)
    s.counter(4, n)
    slides.append(s)

    s = Slide(MUSTARD, 25)
    s.strip("and the bits you'd forget:", 130, caveat(80), seed=260)
    voice_block(s, 380, 2, 261)
    s.strip("a voice that reads your captions", 790, caveat(58), paper=CREAM, seed=262)
    s.ticks(["cover frame", "caption + hashtags", "music-ready track"], 540, 950, 120, size=52, seed=263)
    s.counter(5, n)
    slides.append(s)

    s = Slide(DUSTY_BLUE, 26)
    chat(s, "Can you make the text bigger?", 170, 270, rot=-1)
    s.strip("not quite right? just say so.", 370, marker(58), paper=PAPER_WHITE, rot=1.5, seed=271)
    brand_block(s, 640)
    s.strip("Make your first reel >", 1210, marker(66), paper=CHARTREUSE, rot=-2, seed=272)
    s.counter(6, n)
    slides.append(s)
    slides.append(price_slide(PINK, 275, 7, n, "Make your first reel >", accent=TERRACOTTA))
    return slides


# --------------------------------------------------------------------------- single images

def single(A, ad, w, h):
    s = Slide({"artists": MUSTARD, "creators": CHARCOAL, "beginners": DUSTY_BLUE}[ad], 300 + h, w, h)
    tall = h > 1500
    cy = h / 2
    if ad == "artists":
        art = [("flowers_vase", 0.24, 0.17, -8), ("portrait_bob", 0.76, 0.18, 6), ("car_front", 0.24, 0.80, 5),
               ("blue_flowers", 0.76, 0.80, -6)]
        for i, (name, fx, fy, r) in enumerate(art if tall else art[:1]):
            s.put(cutout(A[name], 330 if not tall else 420, 330 if not tall else 420, 310 + i, tape="top"),
                  fx * w, fy * h, r)
        cy += 0 if tall else 60
        s.strip("You paint.", cy - 90, marker(120), rot=-3, seed=320)
        s.strip("Claude handles the reels.", cy + 60, marker(62), paper=COBALT, ink=PAPER_WHITE, rot=2, seed=321)
        s.strip("story · captions · motion · voice-over · hashtags", cy + 175, caveat(46), paper=CREAM,
                seed=322, max_w=w - 100)
        badge = (0.5 * w, 640, 290, 4) if tall else (0.75 * w, 0.18 * h, 300, 8)
        cta = "Start your first reel >"
    elif ad == "creators":
        s.strip("Film it.", h * 0.12, marker(100), rot=-2, seed=330)
        s.strip("Claude ships it.", h * 0.12 + 145, marker(80), paper=TERRACOTTA, ink=PAPER_WHITE, rot=1.5,
                seed=331)
        pw = 240 if not tall else 320
        sets = [(A["portrait_bob"], "wait for the last one", "A"), (A["car_front"], "nobody talks about this", "B"),
                (A["flowers_vase"], "I tried it for 7 days", "C")]
        for i, (im, cap, lab) in enumerate(sets):
            s.put(ma.phone([im], [cap], w=pw, label=f"hook {lab}")[0], w / 2 + (i - 1) * (pw + 30),
                  cy + (10 if not tall else 0), (-5, 0, 5)[i])
        s.strip("3 hooks · captions · voice-over · one upload", h * (0.765 if tall else 0.745), caveat(48), paper=CREAM, seed=332,
                max_w=w - 100)
        badge = (0.82 * w, 545, 290, 8) if tall else (0.87 * w, 0.13 * h, 250, 8)
        cta = "Post more. Edit less >"
    else:
        s.strip("Never edited a video?", h * 0.14, marker(76), rot=-2, seed=340)
        s.strip("Good.", h * 0.14 + 150, marker(120), paper=MUSTARD, rot=3, seed=341)
        s.put(phone_still("sketchbook_tour.mp4", 1.5, 250 if not tall else 460), w * 0.30,
              cy + (100 if not tall else 120), -3)
        s.ticks(["add photos", "describe the vibe", "post it"], w * 0.68, cy + (0 if not tall else 20),
                120 if not tall else 150, size=54,
                dots=(CHARTREUSE, PAPER_WHITE, PINK), seed=342)
        badge = (0.80 * w, 0.30 * h, 300, 8) if tall else (0.15 * w, 0.31 * h, 250, -6)
        cta = "Make your first reel >"
    bx, by, bs, br = badge
    accent = TERRACOTTA if ad != "creators" else CHARTREUSE
    s.put(ma.price_badge(bs, 360, color=accent, ink=PAPER_WHITE if ad != "creators" else INK), bx, by, br)
    y = h - (175 if not tall else 300)
    s.strip(cta, y, marker(60), paper=CHARTREUSE, rot=-2, seed=350)
    s.strip("Creator Studio · " + ma.TAGLINE, y + (95 if not tall else 120), caveat(44),
            paper=PAPER_WHITE if ad == "creators" else CREAM, rot=1, seed=351)
    return s.finish()


BUILDERS = {"artists": artists, "creators": creators, "beginners": beginners}


def main():
    global LOOK
    LOOK = filters.from_argv()
    sfx = LOOK.suffix() if LOOK else ""
    A = ma.arts()
    for ad in [a for a in sys.argv[1:] if a in BUILDERS] or list(BUILDERS):
        for i, s in enumerate(BUILDERS[ad](A), 1):
            save(s.finish(), os.path.join(ADS_OUT, f"carousel_{ad}{sfx}", f"slide_{i}.jpg"))
        save(single(A, ad, 1080, 1080), os.path.join(ADS_OUT, f"image_{ad}_square{sfx}.jpg"))
        save(single(A, ad, 1080, 1920), os.path.join(ADS_OUT, f"image_{ad}_story{sfx}.jpg"))
        print("wrote", ad)


if __name__ == "__main__":
    main()
