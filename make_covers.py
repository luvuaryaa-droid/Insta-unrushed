#!/usr/bin/env python3
"""Designed cover images for the no-eraser reel, in the reel's black/white/red style.

Writes output/no_eraser_reel_cover.jpg (1080x1920; title and art kept inside the
centre 1080x1350 so the 4:5 profile-grid crop still reads) and
output/no_eraser_thumbnail.jpg (1280x720 YouTube thumbnail for the 16:9 cut).
"""
import os

from PIL import Image

from make_cta import dragonfly_card, eraser_icon, finish, text_block
from make_no_eraser import GREY, INK_BLACK, OUT, RED, load_sources
from make_video import caveat, marker


def reel_cover(scan):
    W, H = 1080, 1920
    c = Image.new("RGBA", (W, H), INK_BLACK + (255,))
    y = text_block(c, "I stopped using", 310, 110, font=marker(104))
    y = text_block(c, "an eraser.", y - 10, 150, font=marker(150), color=RED)
    card = dragonfly_card(scan, 860, 640, box=(0.02, 0.03, 0.98, 0.54))
    top = y + 30
    c.alpha_composite(card, ((W - card.width) // 2, top))
    er = eraser_icon(0.8)
    c.alpha_composite(er, (W - er.width - 20, top - er.height // 2 + 10))
    y = text_block(c, "Here's *why*", top + card.height + 20, 96, mark="underline", font=caveat(96))
    text_block(c, "3 reasons from a pen-only sketchbook", y - 6, 54, color=GREY)
    return finish(c)


def thumbnail(scan):
    W, H = 1280, 720
    c = Image.new("RGBA", (W, H), INK_BLACK + (255,))
    card = dragonfly_card(scan, 560, 620, box=(0.02, 0.02, 0.98, 0.56))
    c.alpha_composite(card, (50, (H - card.height) // 2))
    er = eraser_icon(0.62)
    c.alpha_composite(er, (50 + card.width - er.width // 2 - 10, (H - card.height) // 2 - 50))
    x = 700
    y = text_block(c, "I stopped", 70, 120, font=marker(112), left=x)
    y = text_block(c, "using an", y - 14, 120, font=marker(112), left=x)
    y = text_block(c, "eraser.", y - 14, 130, font=marker(132), color=RED, left=x)
    text_block(c, "Here's *why*", y + 4, 80, mark="underline", left=x)
    return finish(c)


def main():
    scan, _, _ = load_sources()
    os.makedirs(OUT, exist_ok=True)
    reel_cover(scan).save(os.path.join(OUT, "no_eraser_reel_cover.jpg"), quality=93)
    thumbnail(scan).save(os.path.join(OUT, "no_eraser_thumbnail.jpg"), quality=93)
    print("wrote output/no_eraser_reel_cover.jpg, output/no_eraser_thumbnail.jpg")


if __name__ == "__main__":
    main()
