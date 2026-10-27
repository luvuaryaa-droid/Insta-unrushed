#!/usr/bin/env python3
"""Call-to-action end card for the no-eraser reel, in the same black/white/red style.

Writes output/no_eraser_cta_story.jpg (1080x1920, reel end card / story),
output/no_eraser_cta_feed.jpg (1080x1350, feed post / carousel slide) and
output/no_eraser_cta_wide.jpg (1920x1080, 16:9 for YouTube / landscape video).
"""
import os

import numpy as np
from PIL import Image, ImageDraw

from make_no_eraser import (CHALK, ERASER_BLUE, ERASER_PINK, GREY, INK_BLACK, OUT, RED, load_sources,
                            render_lines, scribble_underline, strike_line)
from make_video import caveat, marker


def eraser_icon(scale=1.0):
    w, h = int(300 * scale), int(130 * scale)
    pad = int(40 * scale)
    im = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    box = (pad, pad, pad + w, pad + h)
    d.rounded_rectangle(box, int(26 * scale), fill=ERASER_PINK + (255,))
    d.rectangle((pad + int(w * 0.58), pad + 3, pad + int(w * 0.8), pad + h - 3), fill=ERASER_BLUE + (255,))
    d.rounded_rectangle(box, int(26 * scale), outline=CHALK + (255,), width=max(3, int(5 * scale)))
    im = im.rotate(12, Image.BICUBIC, expand=True)
    d = ImageDraw.Draw(im)
    cx, cy, r = im.width / 2, im.height / 2, 190 * scale
    rng = np.random.default_rng(5)
    for sx in (1, -1):
        pts = [(cx - sx * r + sx * 2 * r * i / 10, cy - r * 0.5 + r * i / 10 + rng.uniform(-4, 4)) for i in range(11)]
        d.line(pts, fill=RED + (255,), width=int(15 * scale), joint="curve")
    return im


def text_block(canvas, text, y, size, mark=None, color=CHALK, font=None, gap=1.05, left=None, max_w=None):
    font = font or caveat(size)
    lh = int(sum(font.getmetrics()) * gap)
    lines = render_lines(text, font, color=color, **({"max_w": max_w} if max_w else {}))
    for i, (im, spans) in enumerate(lines):
        x = (canvas.width - im.width) // 2 if left is None else left - 10
        canvas.alpha_composite(im, (x, y + i * lh))
        merged = []
        for a, b in spans:                       # one continuous mark across adjacent red words
            if merged and a - merged[-1][1] < font.size * 0.5:
                merged[-1] = (merged[-1][0], b)
            else:
                merged.append((a, b))
        for j, (a, b) in enumerate(merged if mark else []):
            mk = (scribble_underline if mark == "underline" else strike_line)(b - a, seed=i * 5 + j)
            asc = font.getmetrics()[0]
            oy = asc - 4 if mark == "underline" else 8 + asc * 0.82 - 34
            canvas.alpha_composite(mk, (int(x + a - 15), int(y + i * lh + oy)))
        last = i
    return y + (last + 1) * lh


def action_row(canvas, y, items, size=64, x0=150):
    """Numbered actions, each with a red marker number and a white hand-lettered label."""
    num_f, lab_f = marker(size + 6), caveat(size)
    for k, label in enumerate(items):
        yy = y + k * int(size * 1.55)
        d = ImageDraw.Draw(canvas)
        d.text((x0, yy - 6), f"{k + 1}", font=num_f, fill=RED + (255,))
        d.text((x0 + 90, yy), label, font=lab_f, fill=CHALK + (255,))
    return y + len(items) * int(size * 1.55)


def dragonfly_card(scan, w, h, box=(0.04, 0.02, 0.96, 0.50)):
    sw, sh = scan.size
    crop = scan.resize((w, h), Image.LANCZOS, box=(box[0] * sw, box[1] * sh, box[2] * sw, box[3] * sh))
    return crop.convert("RGBA")


def finish(canvas):
    w, h = canvas.size
    rng = np.random.default_rng(3)
    yy, xx = np.mgrid[0:h, 0:w]
    vig = 1 - 0.28 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / 2
    arr = np.asarray(canvas.convert("RGB")).astype(np.float32) * vig[..., None] + rng.normal(0, 3, (h, w, 1))
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def story(scan):
    W, H = 1080, 1920
    c = Image.new("RGBA", (W, H), INK_BLACK + (255,))
    card = dragonfly_card(scan, 840, 640)
    top = 260
    c.alpha_composite(card, ((W - card.width) // 2, top))
    er = eraser_icon(0.75)
    c.alpha_composite(er, (W - er.width - 40, top + 640 - er.height // 2 - 20))
    y = text_block(c, "Your turn.", top + 740, 150, font=marker(130))
    y = text_block(c, "One page. In pen. *No eraser.*", y + 10, 92, mark="underline")
    y = action_row(c, y + 70, ["Save this for your next blank page",
                               "Share it with a friend who erases a lot",
                               "Comment PEN when you've tried it"], size=60, x0=110)
    text_block(c, "Imperfect pages welcome here", y + 40, 58, color=GREY)
    return finish(c)


def feed(scan):
    W, H = 1080, 1350
    c = Image.new("RGBA", (W, H), INK_BLACK + (255,))
    card = dragonfly_card(scan, 760, 440, box=(0.04, 0.06, 0.96, 0.41))
    c.alpha_composite(card, ((W - card.width) // 2, 90))
    er = eraser_icon(0.6)
    c.alpha_composite(er, (W - er.width - 50, 90 + 440 - er.height // 2 - 10))
    y = text_block(c, "Your turn.", 580, 130, font=marker(112))
    y = text_block(c, "One page. In pen. *No eraser.*", y + 4, 82, mark="underline")
    action_row(c, y + 50, ["Save this for your next blank page",
                           "Share it with a friend who erases a lot",
                           "Comment PEN when you've tried it"], size=56)
    return finish(c)


def wide(scan):
    W, H = 1920, 1080
    c = Image.new("RGBA", (W, H), INK_BLACK + (255,))
    card = dragonfly_card(scan, 820, 640, box=(0.02, 0.02, 0.98, 0.52))
    top = (H - card.height) // 2
    c.alpha_composite(card, (110, top))
    er = eraser_icon(0.7)
    c.alpha_composite(er, (60, top + card.height - er.height // 2 - 30))
    x = 1040
    y = text_block(c, "Your turn.", 190, 150, font=marker(124), left=x)
    y = text_block(c, "One page. In pen. *No eraser.*", y + 10, 76, mark="underline", left=x, max_w=840)
    y = action_row(c, y + 60, ["Save this for your next blank page",
                               "Share it with a friend who erases a lot",
                               "Comment PEN when you've tried it"], size=52, x0=x)
    text_block(c, "Imperfect pages welcome here", y + 30, 50, color=GREY, left=x)
    return finish(c)


def main():
    scan, _, _ = load_sources()
    os.makedirs(OUT, exist_ok=True)
    story(scan).save(os.path.join(OUT, "no_eraser_cta_story.jpg"), quality=93)
    feed(scan).save(os.path.join(OUT, "no_eraser_cta_feed.jpg"), quality=93)
    wide(scan).save(os.path.join(OUT, "no_eraser_cta_wide.jpg"), quality=93)
    print("wrote output/no_eraser_cta_story.jpg, output/no_eraser_cta_feed.jpg, output/no_eraser_cta_wide.jpg")


if __name__ == "__main__":
    main()
