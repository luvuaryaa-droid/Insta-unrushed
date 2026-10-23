#!/usr/bin/env python3
"""Books that inspired me: a papercut stop-motion reel, one scene per author.

Reuses the paper sprites and renderer from make_video.py. Each author's book covers
(photos from covers/, cut out with a paper border and tape) drop onto a torn sheet with
a one-line note about what they gave me. Books without a photo get a paper stand-in
cover. The reel ends on a stack of spines, one per author.

Usage:  python3 make_books.py              # renders output/books_reel.mp4
        python3 make_books.py --preview    # writes still frames to output/preview/
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw

import make_video as mv
from make_video import (CHARCOAL, COBALT, CREAM, DUSTY_BLUE, INK, MUSTARD, PAPER_WHITE, PINK, SAGE,
                        TERRACOTTA, W, H, FPS, OUT_FPS, Sprite, add, add_shadow, background, caption,
                        caveat, marker, star, text_strip, torn_sheet, typewriter, wrap, cutout)

PLUM = (112, 68, 98)
FOREST = (58, 92, 74)
COVERS = os.path.join(mv.ROOT, "covers")

# One scene per author: (author, scene background, wipe direction, note, books). A book is either
# a photo in covers/ or, when I don't have a photo, a paper stand-in: (title, cover colour, ink).
AUTHORS = [
    ("Julia Cameron", CREAM, "right", "morning pages + artist dates",
     ["cameron_walking_in_this_world.jpg", "cameron_finding_water.jpg", "cameron_sound_of_paper.jpg",
      "cameron_vein_of_gold.jpg", "cameron_artists_way.jpg"]),
    ("Rick Rubin", SAGE, "down", "creativity is a way of being",
     ["rubin_creative_act.jpg"]),
    ("Austin Kleon", PINK, "left", "steal. show your work.\nkeep going.",
     ["kleon_steal_like_an_artist.jpg", "kleon_show_your_work.jpg", "kleon_keep_going.jpg"]),
    ("Danny Gregory", DUSTY_BLUE, "up", "permission to just draw",
     ["gregory_creative_license.jpg", "gregory_art_before_breakfast.jpg",
      "gregory_shut_your_monkey.jpg", "gregory_how_to_draw_without_talent.jpg"]),
    ("Jessica Swift", MUSTARD, "right", "listen to your inner voice",
     ["swift_art_for_self_care.jpg"]),
    ("Natalie Goldberg", TERRACOTTA, "down", "keep your hand moving",
     ["goldberg_writing_down_the_bones.jpg"]),
    ("Clarissa Pinkola Estés", CREAM, "left", "trust your wild, intuitive self",
     ["estes_women_who_run_with_the_wolves.jpg"]),
    ("James McCrae", SAGE, "up", "reclaim your creativity",
     ["mccrae_art_of_you.jpg"]),
]

# Cover centres and max sizes per number of books; the middle one of five is the hero.
LAYOUTS = {
    1: [((540, 880), 640, 860)],
    3: [((290, 720), 470, 500), ((790, 760), 470, 500), ((540, 1200), 470, 500)],
    4: [((290, 690), 460, 500), ((790, 720), 460, 500), ((300, 1190), 460, 500), ((780, 1210), 460, 500)],
    5: [((270, 640), 400, 440), ((810, 660), 400, 440), ((280, 1230), 400, 440), ((800, 1250), 400, 440),
        ((540, 940), 520, 600)],
}


def book_cover(title, author, color, ink, seed, w=560, h=780):
    """A hardback cover: darker spine band, hand-lettered title, author at the foot."""
    cover = torn_sheet(w, h, color, seed, sides="", amp=0, grain=5)
    d = ImageDraw.Draw(cover)
    spine = tuple(int(c * 0.72) for c in color)
    d.rectangle((0, 0, 44, h), fill=spine + (255,))
    d.line((46, 0, 46, h), fill=tuple(int(c * 0.55) for c in color) + (255,), width=3)
    fa = caveat(62)
    authors = wrap(author, fa, w - 120)
    room = h - 120 - (len(authors) - 1) * 64 - 90 - 150   # space between the top margin and the author
    size = 92
    while True:
        f = marker(size)
        lines = wrap(title, f, w - 130)
        asc, desc = f.getmetrics()
        lh = int((asc + desc) * 0.95)
        if lh * len(lines) <= room or size <= 50:
            break
        size -= 4
    y = 150
    for l in lines:
        d.text((44 + (w - 44 - f.getlength(l)) / 2, y), l, font=f, fill=ink)
        y += lh
    rng = np.random.default_rng(seed)
    pts = [(110 + (w - 200) * i / 8, y + 30 + rng.uniform(-5, 5)) for i in range(9)]
    d.line(pts, fill=ink, width=5, joint="curve")
    for i, l in enumerate(authors[::-1]):
        d.text((44 + (w - 44 - fa.getlength(l)) / 2, h - 120 - i * 64), l, font=fa, fill=ink)
    return add_shadow(cover, 10, 14, 12, 0.42)


def book_spine(author, count, color, ink, seed, w=820, h=104):
    sp = torn_sheet(w, h, color, seed, sides="", amp=0, grain=5)
    d = ImageDraw.Draw(sp)
    band = tuple(int(c * 0.75) for c in color)
    d.rectangle((0, 0, w, 12), fill=band + (255,))
    d.rectangle((0, h - 12, w, h), fill=band + (255,))
    ft, fa = typewriter(40), caveat(42)
    d.text((28, h / 2 - 24), author, font=ft, fill=ink)
    label = f"{count} books" if count > 1 else "1 book"
    d.text((w - 28 - fa.getlength(label), h / 2 - 28), label, font=fa, fill=ink)
    return add_shadow(sp, 4, 7, 6, 0.35)


SPINE_COLOURS = [(TERRACOTTA, PAPER_WHITE), (CHARCOAL, PAPER_WHITE), (PAPER_WHITE, INK), (COBALT, PAPER_WHITE),
                 (PINK, INK), (MUSTARD, INK), (FOREST, PAPER_WHITE), (DUSTY_BLUE, INK)]


def scene_duration(n):
    return 4.5 + 0.4 * n


def build():
    rng = np.random.default_rng(17)

    # ---------------- title (0 - 4.5)
    z = 0
    background(0, PLUM, 11, None, z)
    for i, (author, _bg, _w, _n, books) in enumerate(AUTHORS[:4]):
        col, ink = SPINE_COLOURS[i]
        add(Sprite(book_spine(author, len(books), col, ink, 30 + i, w=700), 0.1 + i * 0.18,
                   (540 + rng.uniform(-40, 40), 1640 - i * 100), rot=rng.uniform(-3, 3), z=z + 1 + i,
                   enter="slide_" + ("left" if i % 2 else "right"), enter_dur=0.4, boil=0.4))
    add(Sprite(text_strip("BOOKS", marker(150), seed=41), 0.9, (540, 560), rot=-3, z=z + 10,
               enter="slide_left", enter_dur=0.45))
    add(Sprite(text_strip("that inspired me", caveat(104), paper=MUSTARD, seed=42), 1.3, (560, 760),
               rot=2.5, z=z + 11, enter="slide_right", enter_dur=0.45))
    add(Sprite(text_strip("(and still do)", caveat(70), paper=CREAM, seed=43), 1.9, (520, 910),
               rot=-1.5, z=z + 12, enter="pop", enter_dur=0.4))
    for i, (sx, sy, sc, col) in enumerate(((170, 330, 110, PAPER_WHITE), (920, 380, 90, MUSTARD),
                                           (910, 1050, 80, PINK))):
        add(Sprite(star(sc, col, 50 + i), 2.2 + i * 0.15, (sx, sy), rot=rng.uniform(-20, 20), z=z + 13,
                   enter="pop", enter_dur=0.35))

    # ---------------- one scene per author
    t = 4.5
    for ai, (author, bg, wipe, note, books) in enumerate(AUTHORS):
        z = 100 + ai * 100
        background(t - 0.5, bg, 100 + ai, wipe, z)
        tag_paper = PAPER_WHITE if bg != PAPER_WHITE else CREAM
        add(Sprite(text_strip(author, marker(80), paper=tag_paper, seed=110 + ai, max_w=900), t + 0.05,
                   (540, 250), rot=rng.uniform(-3, 3), z=z + 20, enter="slide_up", enter_dur=0.4))
        for bi, (book, (pos, mw, mh)) in enumerate(zip(books, LAYOUTS[len(books)])):
            if isinstance(book, str):
                img = cutout(Image.open(os.path.join(COVERS, book)).convert("RGB"), mw, mh, 120 + ai * 10 + bi,
                             border=12, tape="top" if bi % 2 == 0 else "corners")
            else:
                title, col, ink = book
                img = book_cover(title, author, col, ink, 120 + ai * 10 + bi, w=int(mh * 0.72), h=mh)
            add(Sprite(img, t + 0.3 + bi * 0.3, pos, rot=rng.uniform(-6, 6), z=z + 2 + bi, enter="drop",
                       enter_dur=0.45))
        caption(note, t + 0.9 + 0.3 * len(books), 1620, z + 21, size=80, seed=140 + ai, paper=tag_paper,
                max_w=860)
        t += scene_duration(len(books))

    # ---------------- outro: the stack
    z = 1000
    background(t - 0.5, PLUM, 1001, "down", z)
    for i, (author, _bg, _w, _n, books) in enumerate(AUTHORS):
        col, ink = SPINE_COLOURS[i]
        add(Sprite(book_spine(author, len(books), col, ink, 1010 + i), t + 0.1 + i * 0.2,
                   (540 + rng.uniform(-50, 50), 1660 - i * 104), rot=rng.uniform(-3, 3), z=z + 2 + i,
                   enter="slide_down" if i == 0 else "drop", enter_dur=0.35, boil=0.4))
    caption("my creative bookshelf.", t + 1.9, 300, z + 20, size=96, seed=1021)
    add(Sprite(text_strip("what should I read next?", marker(70), paper=MUSTARD, seed=1022, max_w=820),
               t + 2.8, (540, 500), rot=-2, z=z + 21, enter="slide_up", enter_dur=0.45))
    return t + 6.0


def scene_times():
    """A moment near the end of each author scene, once everything has landed."""
    t, out = 4.5, []
    for a in AUTHORS:
        d = scene_duration(len(a[4]))
        out.append(round(t + d - 0.8, 1))
        t += d
    return out


def main():
    mv.build = build
    os.makedirs(mv.OUT, exist_ok=True)
    mv.setup()
    if "--preview" in sys.argv:
        pdir = os.path.join(mv.OUT, "preview")
        os.makedirs(pdir, exist_ok=True)
        times = [float(a) for a in sys.argv[sys.argv.index("--preview") + 1:]] or \
            [3.5] + scene_times() + [mv.DURATION - 1]
        for ts in times:
            Image.frombytes("RGB", (W, H), mv.render_frame(int(ts * FPS))).save(
                os.path.join(pdir, f"books_t{ts:05.1f}.jpg"), quality=88)
        return
    n = int(mv.DURATION * FPS)
    out = os.path.join(mv.OUT, "books_reel.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-r", str(OUT_FPS), "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for i, buf in enumerate(pool.imap(mv.render_frame, range(n), chunksize=4)):
            proc.stdin.write(buf)
            if i % 60 == 0:
                print(f"frame {i}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()
    Image.frombytes("RGB", (W, H), mv.render_frame(int(3.5 * FPS))).save(
        os.path.join(mv.OUT, "books_cover.jpg"), quality=92)
    print("wrote", out)


if __name__ == "__main__":
    main()
