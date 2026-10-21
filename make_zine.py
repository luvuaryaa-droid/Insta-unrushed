#!/usr/bin/env python3
"""Art for Anxious Days, Vol. 1: a printable/digital art zine plus its bonus print pack.

Builds everything that gets sold or posted:
  product/art_for_anxious_days_vol1.pdf       the zine (A5, 16 pages, 300 dpi)      -> Rs 299 tier
  product/print_pack/prints_A4.pdf            11 frameable A4 prints                 -> Rs 499 tier adds these
  product/print_pack/wallpapers/*.jpg         11 phone wallpapers (1080x1920)        -> Rs 499 tier adds these
  product/promo/slide_*.jpg                   4-slide Instagram launch carousel (1080x1350)

Usage:  python3 make_zine.py              # build everything
        python3 make_zine.py --pages      # also write each zine page as a JPEG to product/pages/ for checking
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

from make_video import (CHARCOAL, COBALT, CREAM, DUSTY_BLUE, INK, MUSTARD, PAPER_WHITE, PINK, RED_INK, SAGE,
                        TERRACOTTA, add_shadow, caveat, cutout, fit, load_art, marker, paper_circle,
                        paper_texture, star, tape_strip, text_strip, torn_sheet, typewriter, wrap)

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "product")

TITLE = "Art for Anxious Days"
VOL = "Vol. 1"
PW, PH = 1748, 2480  # A5 at 300 dpi
DPI = 300

# Light page tints, so the drawings stay the loudest thing on the page
TINTS = [(236, 226, 205), (228, 232, 220), (240, 224, 218), (222, 230, 236), (244, 232, 200)]
INK_SOFT = (70, 64, 60)

# (file, title, note, try this)
PIECES = [
    ("blue_flowers.jpg", "Dot, dot, dot",
     "This one is thousands of tiny marks. I didn't plan it. I just kept going, one dot after another, "
     "until my head went quiet.",
     "Breathe in for four dots, out for six. Do it three times."),
    ("cat_neon.gif", "Sit like a cat",
     "Cats don't explain themselves. They find a warm spot, sit very still and watch the world without "
     "needing to fix any of it.",
     "Drop your shoulders. Unclench your jaw. Stay like that for ten slow breaths."),
    ("clock_collage.jpg", "The clock can wait",
     "Some days every minute feels like it's chasing me. It isn't, really. It's just ticking, the way it "
     "always has.",
     "Set a timer for five minutes and do nothing at all until it rings."),
    ("toast_collage.jpg", "Did you eat?",
     "On heavy days the bravest thing can be a slice of toast and a glass of water. That counts. That "
     "really counts.",
     "Eat something warm, slowly, with your phone in another room."),
    ("camera_polaroid.png", "Keep one small moment",
     "An old camera taught me that you don't have to hold the whole day. Just one frame of it.",
     "Name five things you can see, four you can hear, three you can touch."),
    ("car_awning.jpg", "Parked, not stuck",
     "Resting is not the same as falling behind. Even the loveliest car spends most of its life parked.",
     "Write down one thing you're allowed to not do today."),
    ("car_front.jpg", "The slow lane is still a lane",
     "You're still going somewhere, even when everyone else seems to be overtaking you.",
     "Walk somewhere at half your usual speed. Notice what you normally miss."),
    ("flowers_mosaic.jpg", "Bloom in pieces",
     "These flowers are built from little broken tiles. Feeling scattered doesn't mean you aren't whole.",
     "List three small things that went okay this week."),
    ("flowers_vase.jpg", "Water the small things",
     "Not everything needs fixing today. Some things just need a little water and some light.",
     "Do one kind thing for your space: open a window, water a plant, make your bed."),
    ("portrait_bob.jpg", "Look away for a bit",
     "You're allowed to look away: from the news, from the group chat, from the never-ending list.",
     "Put your phone down for twenty minutes. The world will keep."),
    ("portraits_stripes.jpg", "Both of you are welcome",
     "There's the face you show people and the face that's tired. Neither one is the wrong one.",
     "Say one honest sentence about how you feel, even if it's only to yourself."),
]


# --------------------------------------------------------------------------- helpers

_art_cache = {}


def art(name):
    if name not in _art_cache:
        im = load_art(name)
        if max(im.size) > 2400:
            im = fit(im, 2400, 2400)
        _art_cache[name] = im
    return _art_cache[name]


def page(color, seed, size=(PW, PH)):
    return Image.fromarray(paper_texture(size[0], size[1], color, seed, grain=5)).convert("RGBA")


def place(canvas, img, cx, cy, rot=0.0):
    if rot:
        img = img.rotate(rot, Image.BICUBIC, expand=True)
    canvas.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))
    return img


def text_block(canvas, text, font, cx, y, max_w, fill=INK, spacing=1.3, align="center", left=None):
    """Draws wrapped text; returns the y just below it."""
    d = ImageDraw.Draw(canvas)
    asc, desc = font.getmetrics()
    lh = int((asc + desc) * spacing)
    for line in wrap(text, font, max_w):
        lw = font.getlength(line)
        x = left if align == "left" else cx - lw / 2
        d.text((x, y), line, font=font, fill=fill)
        y += lh
    return y


def text_height(text, font, max_w, spacing=1.3):
    asc, desc = font.getmetrics()
    return int((asc + desc) * spacing) * len(wrap(text, font, max_w))


def big_cutout(im, max_w, max_h, seed, tape="top", tape_color=None):
    """cutout() is tuned for a 1080 px reel; scale it up for 300 dpi pages."""
    c = cutout(im, max_w // 2, max_h // 2, seed, border=14, tape=tape, tape_color=tape_color)
    s = min(max_w / c.width, max_h / c.height)
    return c.resize((int(c.width * s), int(c.height * s)), Image.LANCZOS)


def folio(canvas, n):
    f = typewriter(30)
    label = f"{TITLE.lower()}  ·  {VOL.lower()}  ·  {n:02d}"
    ImageDraw.Draw(canvas).text((PW / 2 - f.getlength(label) / 2, PH - 120), label, font=f, fill=INK_SOFT)


# --------------------------------------------------------------------------- zine pages

def cover():
    c = page(DUSTY_BLUE, 101)
    # collage
    place(c, big_cutout(art("blue_flowers.jpg"), 1240, 1240, 3, tape="corners", tape_color=(235, 214, 150)),
          PW / 2 + 40, 1500, -4)
    place(c, big_cutout(art("cat_neon.gif"), 560, 560, 7, tape="top", tape_color=PINK), 1330, 2040, 7)
    place(c, big_cutout(art("toast_collage.jpg"), 520, 520, 9, tape="top", tape_color=(196, 216, 52)),
          380, 2080, -8)
    # title sheet
    sheet = torn_sheet(1500, 700, CREAM, 11, amp=22, grain=4)
    d = ImageDraw.Draw(sheet)
    f1, f2 = caveat(170), marker(178)
    d.text((750 - f1.getlength("Art for") / 2, 40), "Art for", font=f1, fill=INK)
    d.text((750 - f2.getlength("Anxious Days") / 2, 250), "Anxious Days", font=f2, fill=COBALT)
    f3 = typewriter(38)
    sub = "11 drawings & small kindnesses for heavy-headed days"
    d.text((750 - f3.getlength(sub) / 2, 575), sub, font=f3, fill=INK_SOFT)
    place(c, add_shadow(sheet, 8, 12, 12, 0.35), PW / 2, 520, 1.5)
    # volume stamp
    stamp = paper_circle(300, RED_INK, 13)
    sd = ImageDraw.Draw(stamp)
    f4 = marker(96)
    sd.text((stamp.width / 2 - f4.getlength(VOL) / 2, stamp.height / 2 - 66), VOL, font=f4, fill=PAPER_WHITE)
    place(c, add_shadow(stamp, 6, 9, 8, 0.35), 1530, 280, -12)
    return c


def letter():
    c = page(TINTS[0], 102)
    sheet = torn_sheet(1420, 1960, PAPER_WHITE, 21, amp=18, grain=3)
    d = ImageDraw.Draw(sheet)
    d.text((110, 110), "Hi, you.", font=caveat(150), fill=INK)
    body = ("This little book is made of pages from my sketchbook, most of them drawn on days when my head "
            "felt too loud.\n\n"
            "Drawing is the thing that slows me down. Once I'm in the zone, the noise gets quieter. I wanted to "
            "pass a bit of that quiet on to you.\n\n"
            "How to use it: open any page. You don't have to read it in order, and you don't have to finish "
            "it. Every drawing comes with one tiny thing to try. Do it, or don't. Both are fine.\n\n"
            "Take what helps and leave the rest.")
    y = text_block(sheet, body, typewriter(52), 0, 340, 1200, fill=INK, spacing=1.45, align="left", left=110)
    d.text((110, y + 50), "with love, from my sketchbook to yours", font=caveat(76), fill=COBALT)
    place(c, add_shadow(sheet, 8, 12, 12, 0.3), PW / 2, PH / 2 - 40, -1)
    place(c, tape_strip(380, 90, (235, 214, 150), 22).rotate(-4, Image.BICUBIC, expand=True), PW / 2, 330)
    place(c, star(170, MUSTARD, 23), 1480, 2170, 12)
    folio(c, 2)
    return c


def art_page(i, n):
    name, title, note, try_this = PIECES[i]
    c = page(TINTS[i % len(TINTS)], 200 + i)
    margin = 170
    ft, fn, fy = caveat(150), typewriter(42), caveat(66)
    note_h = text_height(note, fn, PW - 2 * margin, 1.4)
    strip = text_strip("try this: " + try_this, fy, paper=PAPER_WHITE, seed=300 + i, max_w=1180, pad=(60, 34))
    text_h = 190 + note_h + 70 + strip.height
    top, bottom = 160, PH - 190 - text_h
    tapes = [(235, 214, 150), PINK, (196, 216, 52), (190, 210, 222)]
    card = big_cutout(art(name), PW - 2 * margin + 60, bottom - top - 40, 400 + i, tape="top",
                      tape_color=tapes[i % len(tapes)])
    place(c, card, PW / 2, (top + bottom) / 2, [-2.5, 2, -1.5, 3][i % 4])
    y = bottom + 10
    ImageDraw.Draw(c).text((PW / 2 - ft.getlength(title) / 2, y), title, font=ft, fill=INK)
    y = text_block(c, note, fn, PW / 2, y + 215, PW - 2 * margin, fill=INK_SOFT, spacing=1.4)
    place(c, strip, PW / 2, y + 50 + strip.height / 2, [1, -1][i % 2])
    folio(c, n)
    return c


def breathe(n):
    c = page((226, 233, 240), 501)
    place(c, big_cutout(art("blue_flowers_spread.jpg"), PW - 200, 900, 502, tape="corners"), PW / 2, 600, -1.5)
    d = ImageDraw.Draw(c)
    f = caveat(190)
    d.text((PW / 2 - f.getlength("Breathe with the flowers") / 2, 1150), "Breathe with the flowers", font=f,
           fill=COBALT)
    fs, fl = marker(90), typewriter(40)
    steps = [("in", "4", "smell the flower"), ("hold", "4", "keep it close"), ("out", "6", "blow out a candle")]
    for k, (word, count, hint) in enumerate(steps):
        cx = 330 + k * 545
        circ = paper_circle(330, [MUSTARD, PINK, SAGE][k], 510 + k)
        cd = ImageDraw.Draw(circ)
        cd.text((circ.width / 2 - fs.getlength(word) / 2, 70), word, font=fs, fill=INK)
        fc = caveat(120)
        cd.text((circ.width / 2 - fc.getlength(count) / 2, 165), count, font=fc, fill=INK)
        place(c, add_shadow(circ, 5, 8, 8, 0.3), cx, 1640, [-4, 3, -2][k])
        d.text((cx - fl.getlength(hint) / 2, 1860), hint, font=fl, fill=INK_SOFT)
    text_block(c, "Count slowly. Repeat four times. Your out-breath is longer than your in-breath on purpose: "
                  "that's the part that tells your body it's safe.", typewriter(42), PW / 2, 2010, PW - 340,
               fill=INK, spacing=1.4)
    folio(c, n)
    return c


def journal(n):
    c = page(TINTS[4], 601)
    sheet = torn_sheet(1480, 2040, PAPER_WHITE, 602, amp=16, grain=3)
    d = ImageDraw.Draw(sheet)
    d.text((100, 80), "Your page", font=caveat(160), fill=INK)
    fl = typewriter(44)
    y = 330
    for prompt in ["Today I'm feeling", "One small thing that helped", "Something I'm looking forward to"]:
        d.text((100, y), prompt + ":", font=fl, fill=INK_SOFT)
        for k in range(2):
            ly = y + 120 + k * 95
            d.line([(100, ly), (1380, ly)], fill=(180, 172, 160), width=3)
        y += 360
    d.text((100, y), "Draw it, doodle it, dot it:", font=fl, fill=INK_SOFT)
    box_top = y + 80
    for x in range(100, 1380, 34):
        d.line([(x, box_top), (x + 16, box_top)], fill=(170, 160, 150), width=4)
        d.line([(x, 1940), (x + 16, 1940)], fill=(170, 160, 150), width=4)
    for yy in range(box_top, 1940, 34):
        d.line([(100, yy), (100, yy + 16)], fill=(170, 160, 150), width=4)
        d.line([(1380, yy), (1380, yy + 16)], fill=(170, 160, 150), width=4)
    place(c, add_shadow(sheet, 8, 12, 12, 0.3), PW / 2, PH / 2 - 50, 0.8)
    place(c, tape_strip(300, 80, PINK, 603).rotate(35, Image.BICUBIC, expand=True), 210, 290)
    place(c, tape_strip(300, 80, PINK, 604).rotate(-35, Image.BICUBIC, expand=True), PW - 210, 290)
    folio(c, n)
    return c


def back(n):
    c = page(DUSTY_BLUE, 701)
    sheet = torn_sheet(1380, 1150, CREAM, 702, amp=18, grain=4)
    d = ImageDraw.Draw(sheet)
    f = caveat(170)
    d.text((690 - f.getlength("Thank you") / 2, 70), "Thank you", font=f, fill=INK)
    text_block(sheet, "for buying this zine and for keeping my sketchbook going. Every copy means I get to "
                      "spend more time drawing.", typewriter(44), 690, 330, 1160, fill=INK_SOFT, spacing=1.4)
    f2 = marker(80)
    d.text((690 - f2.getlength("Vol. 2 is on its way") / 2, 700), "Vol. 2 is on its way", font=f2, fill=COBALT)
    text_block(sheet, "Keep your receipt: everyone who bought Vol. 1 gets first look at Vol. 2 and a "
                      "returning-reader price.", typewriter(40), 690, 860, 1160, fill=INK_SOFT, spacing=1.4)
    place(c, add_shadow(sheet, 8, 12, 12, 0.35), PW / 2, 700, -1)
    place(c, big_cutout(art("flowers_vase.jpg"), 720, 720, 703, tape="top", tape_color=PINK), PW / 2, 1620, 3)
    care = torn_sheet(1380, 330, PAPER_WHITE, 704, amp=12, grain=3)
    text_block(care, "This zine is a comfort, not a cure. If things feel too heavy, please talk to someone. "
                     "In India you can call Tele-MANAS on 14416, free and any time of day.", typewriter(34),
               690, 50, 1220, fill=INK, spacing=1.4)
    place(c, add_shadow(care, 5, 8, 8, 0.3), PW / 2, 2140, 0.5)
    folio(c, n)
    return c


def zine_pages():
    pages = [cover(), letter()]
    pages += [art_page(i, i + 3) for i in range(len(PIECES))]
    n = len(pages) + 1
    pages += [breathe(n), journal(n + 1), back(n + 2)]
    return [p.convert("RGB") for p in pages]


# --------------------------------------------------------------------------- print pack

def a4_print(i):
    name, title, _, _ = PIECES[i]
    w, h = 2480, 3508
    c = page(PAPER_WHITE, 800 + i, (w, h))
    im = fit(load_art(name), w - 2 * 300, h - 2 * 300 - 260)
    x, y = (w - im.width) // 2, (h - 260 - im.height) // 2
    c.paste(im, (x, y))
    d = ImageDraw.Draw(c)
    f, fs = caveat(110), typewriter(40)
    d.text((w / 2 - f.getlength(title) / 2, y + im.height + 70), title, font=f, fill=INK)
    tag = f"{TITLE}  ·  {VOL}"
    d.text((w / 2 - fs.getlength(tag) / 2, y + im.height + 220), tag, font=fs, fill=INK_SOFT)
    return c.convert("RGB")


def wallpaper(i):
    name, title, _, _ = PIECES[i]
    w, h = 1080, 1920
    c = page(TINTS[i % len(TINTS)], 900 + i, (w, h))
    card = cutout(art(name), 900, 1000, 950 + i, border=12, tape="top", tape_color=PINK)
    # keep the art clear of the lock-screen clock (top) and the home bar (bottom)
    place(c, card, w / 2, 1020, [-2, 2][i % 2])
    f = caveat(82)
    ImageDraw.Draw(c).text((w / 2 - f.getlength(title) / 2, 1620), title, font=f, fill=INK)
    return c.convert("RGB")


# --------------------------------------------------------------------------- promo carousel

def promo(pages):
    w, h = 1080, 1350
    slides = []

    def thumb(p, width, seed):
        t = p.resize((width, int(width * PH / PW)), Image.LANCZOS).convert("RGBA")
        return add_shadow(t, 10, 16, 16, 0.4)

    def heading(c, text, y, font, color=INK):
        ImageDraw.Draw(c).text((w / 2 - font.getlength(text) / 2, y), text, font=font, fill=color)

    # 1: the cover
    c = page(MUSTARD, 1001, (w, h))
    heading(c, "new in the shop", 50, typewriter(46), INK)
    place(c, thumb(pages[0], 700, 1), w / 2, 660, -3)
    heading(c, "16 pages  ·  from ₹299", 1220, caveat(76))
    slides.append(c)

    # 2: what's inside
    c = page(TINTS[1], 1002, (w, h))
    heading(c, "What's inside", 50, caveat(120))
    for k, (pi, cx, rot) in enumerate([(5, 290, -5), (6, 790, 4)]):
        place(c, thumb(pages[pi], 470, k), cx, 640, rot)
    text_block(c, "11 drawings from my sketchbook, each with one tiny thing to try on a heavy day. Plus a "
                  "breathing page and a page that's just for you.", typewriter(36), w / 2, 1050, 900,
               fill=INK, spacing=1.4)
    slides.append(c)

    # 3: two ways to get it
    c = page(TINTS[2], 1003, (w, h))
    heading(c, "Two ways to get it", 50, caveat(120))
    tiers = [("₹299", "The zine", "16-page PDF to read on your phone or print at home"),
             ("₹499", "Zine + print pack", "the zine, 11 frameable A4 prints and 11 phone wallpapers")]
    for k, (price, name, desc) in enumerate(tiers):
        card = torn_sheet(860, 440, [CREAM, PAPER_WHITE][k], 1010 + k, amp=14, grain=4)
        d = ImageDraw.Draw(card)
        d.text((60, 30), price, font=caveat(150), fill=[TERRACOTTA, COBALT][k])
        d.text((380, 80), name, font=marker(56), fill=INK)
        text_block(card, desc, typewriter(34), 0, 250, 740, fill=INK_SOFT, spacing=1.35, align="left", left=60)
        place(c, add_shadow(card, 6, 10, 10, 0.3), w / 2, 450 + k * 520, [-1.5, 1.5][k])
    slides.append(c)

    # 4: call to action
    c = page(DUSTY_BLUE, 1004, (w, h))
    place(c, cutout(art("cat_neon.gif"), 560, 560, 1020, border=12, tape="top", tape_color=PINK), w / 2, 470, -4)
    sheet = torn_sheet(900, 420, CREAM, 1021, amp=16, grain=4)
    d = ImageDraw.Draw(sheet)
    f = marker(92)
    d.text((450 - f.getlength("link in bio") / 2, 50), "link in bio", font=f, fill=COBALT)
    text_block(sheet, "Instant download. Vol. 1 buyers get first look at Vol. 2.", typewriter(36), 450, 220,
               760, fill=INK_SOFT, spacing=1.4)
    place(c, add_shadow(sheet, 6, 10, 10, 0.3), w / 2, 1060, 1)
    slides.append(c)
    return [s.convert("RGB") for s in slides]


# --------------------------------------------------------------------------- main

def main():
    os.makedirs(os.path.join(OUT, "print_pack", "wallpapers"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "promo"), exist_ok=True)

    pages = zine_pages()
    zine = os.path.join(OUT, "art_for_anxious_days_vol1.pdf")
    pages[0].save(zine, save_all=True, append_images=pages[1:], resolution=DPI, quality=86,
                  title=f"{TITLE}, {VOL}")
    print("wrote", zine, f"({len(pages)} pages)")
    pages[0].resize((PW // 2, PH // 2), Image.LANCZOS).save(os.path.join(OUT, "cover.jpg"), quality=90)
    if "--pages" in sys.argv:
        pdir = os.path.join(OUT, "pages")
        os.makedirs(pdir, exist_ok=True)
        for k, p in enumerate(pages, 1):
            p.resize((PW // 2, PH // 2), Image.LANCZOS).save(os.path.join(pdir, f"page_{k:02d}.jpg"), quality=85)

    prints = [a4_print(i) for i in range(len(PIECES))]
    pp = os.path.join(OUT, "print_pack", "prints_A4.pdf")
    prints[0].save(pp, save_all=True, append_images=prints[1:], resolution=DPI, quality=88,
                   title=f"{TITLE}, {VOL}: prints")
    print("wrote", pp)
    for i in range(len(PIECES)):
        slug = os.path.splitext(PIECES[i][0])[0]
        wallpaper(i).save(os.path.join(OUT, "print_pack", "wallpapers", f"{i + 1:02d}_{slug}.jpg"), quality=90)
    print("wrote", len(PIECES), "wallpapers")

    for k, s in enumerate(promo(pages), 1):
        s.save(os.path.join(OUT, "promo", f"slide_{k}.jpg"), quality=92)
    print("wrote promo carousel")


if __name__ == "__main__":
    main()
