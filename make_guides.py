#!/usr/bin/env python3
"""Four PDF reference guides for Creator Studio: animation styles, caption styles, effects and filters.

Each guide separates what the renderers in this repo already do ("Built in") from what could be
added on request ("Not built yet"). Every built-in sample is a frame from a finished reel or a tile
drawn with the same code the reels use. The filter previews under "Not built yet" are made here
with a few lines of Pillow, to show what each would look like.

Usage:  python3 make_guides.py        # writes output/guides/*.pdf (needs reportlab, ffmpeg)
"""
import os
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageFilter
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image as RLImage, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

import filters
import make_ads as ma
import make_carousels as mc
from make_video import (COBALT, CREAM, DUSTY_BLUE, FONTS, INK, MUSTARD, OUT, PAPER_WHITE,
                        PINK, SAGE, TERRACOTTA, add_shadow, caveat, cutout, load_art, marker, paper_circle,
                        star, strike, text_strip, torn_sheet, typewriter)

GUIDES = os.path.join(OUT, "guides")
TMP = tempfile.mkdtemp(prefix="guides_")

pdfmetrics.registerFont(TTFont("Marker", os.path.join(FONTS, "PermanentMarker-Regular.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))

INK_C = colors.Color(*(c / 255 for c in INK))
MUTED = colors.Color(0.38, 0.37, 0.35)
LINE = colors.Color(0.86, 0.83, 0.78)
S_BODY = ParagraphStyle("body", fontName="DejaVu", fontSize=9.2, leading=13, textColor=INK_C)
S_NAME = ParagraphStyle("name", fontName="DejaVu-Bold", fontSize=11.5, leading=15, textColor=INK_C,
                        spaceAfter=3)
S_META = ParagraphStyle("meta", parent=S_BODY, fontSize=8.4, leading=11.5, textColor=MUTED)
S_H2 = ParagraphStyle("h2", fontName="Marker", fontSize=17, leading=22, textColor=INK_C, spaceBefore=10,
                      spaceAfter=4, keepWithNext=1)
S_INTRO = ParagraphStyle("intro", parent=S_BODY, fontSize=9.8, leading=14, spaceAfter=6)
S_CELL = ParagraphStyle("cell", parent=S_BODY, fontSize=8.6, leading=11.5, alignment=TA_LEFT)
S_CELLB = ParagraphStyle("cellb", parent=S_CELL, fontName="DejaVu-Bold")


# --------------------------------------------------------------------------- sample images

def save(img, name, max_w=620):
    """Write a sample as a JPEG in the temp folder and return its path."""
    img = img.convert("RGB")
    if img.width > max_w:
        img = img.resize((max_w, int(img.height * max_w / img.width)), Image.LANCZOS)
    path = os.path.join(TMP, name + ".jpg")
    img.save(path, quality=86)
    return path


def frame(video, t, crop=None):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", os.path.join(OUT, video), "-frames:v",
                          "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    im = Image.frombytes("RGB", (1080, 1920), raw[:1080 * 1920 * 3])
    return im.crop(crop) if crop else im


def tile(draw, bg=CREAM, w=900, h=440, seed=1):
    """A paper tile with something drawn on it by draw(slide)."""
    s = mc.Slide(bg, seed, w, h)
    draw(s)
    return s.finish()


def art(name):
    return load_art(name + ".jpg")


# --------------------------------------------------------------------------- PDF scaffolding

def header_footer(title, colour, sub="what it supports today, and what can be added"):
    def draw(c, doc):
        w, h = A4
        c.saveState()
        c.setFillColor(colors.Color(*(v / 255 for v in colour)))
        c.rect(0, h - 3.1 * cm, w, 3.1 * cm, stroke=0, fill=1)
        c.setFillColor(INK_C)
        c.setFont("Marker", 26)
        c.drawString(1.6 * cm, h - 1.95 * cm, title)
        c.setFont("DejaVu", 9.5)
        c.drawString(1.6 * cm, h - 2.6 * cm, "Creator Studio · " + sub)
        c.setFont("DejaVu", 8)
        c.setFillColor(MUTED)
        c.drawString(1.6 * cm, 1.0 * cm, "Creator Studio · made with Claude · ₹699 lifetime access · "
                                         "Install once. Create forever.")
        c.drawRightString(w - 1.6 * cm, 1.0 * cm, f"page {doc.page}")
        c.restoreState()
    return draw


def item(name, desc, used=None, ask=None, img=None, img_w=5.4 * cm):
    text = [Paragraph(name, S_NAME), Paragraph(desc, S_BODY)]
    if used:
        text.append(Spacer(1, 3))
        text.append(Paragraph("<b>Where it's used:</b> " + used, S_META))
    if ask:
        text.append(Paragraph("<b>Ask for it:</b> <i>“" + ask + "”</i>", S_META))
    if img:
        im = Image.open(img)
        if im.height > im.width * 1.2:   # tall 9:16 frames: keep the card compact
            img_w = 3.3 * cm
        pic = RLImage(img, width=img_w, height=img_w * im.height / im.width)
        t = Table([[pic, text]], colWidths=[img_w + 0.4 * cm, None])
    else:
        t = Table([[text]], colWidths=[None])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 9),
                           ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE)]))
    return KeepTogether(t)


def grid(rows, widths, head=True):
    data = [[Paragraph(c, S_CELLB if (head and r == 0) else S_CELL) for c in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if head else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.5, LINE),
             ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]
    if head:
        style.append(("BACKGROUND", (0, 0), (-1, 0), colors.Color(*(v / 255 for v in CREAM))))
    t.setStyle(TableStyle(style))
    return t


def gallery(cells, cols=5, w=3.15 * cm):
    """Image grid with a caption under each picture."""
    rows, row = [], []
    for path, cap in cells:
        im = Image.open(path)
        row.append([RLImage(path, width=w, height=w * im.height / im.width), Paragraph(cap, S_CELL)])
        if len(row) == cols:
            rows.append(row)
            row = []
    if row:
        rows.append(row + [""] * (cols - len(row)))
    t = Table(rows, colWidths=[w + 0.35 * cm] * cols)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return t


def build(path, title, colour, story, sub=None):
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=1.6 * cm, rightMargin=1.6 * cm, topMargin=3.7 * cm,
                            bottomMargin=1.8 * cm, title=f"Creator Studio · {title}", author="Creator Studio")
    glued = []   # never leave a section heading stranded at the bottom of a page
    for f in story:
        if glued and isinstance(glued[-1], Paragraph) and glued[-1].style is S_H2:
            glued[-1] = KeepTogether([glued[-1]] + (f._content if isinstance(f, KeepTogether) else [f]))
        else:
            glued.append(f)
    hf = header_footer(title, colour, sub) if sub else header_footer(title, colour)
    doc.build(glued, onFirstPage=hf, onLaterPages=hf)
    print("wrote", path)


# --------------------------------------------------------------------------- 1. animation styles

def animation_guide():
    S = []
    S.append(Paragraph(
        "Every reel is rendered as full HD 9:16 video (1080 × 1920) ready for Reels, TikTok and Shorts. "
        "Papercut pieces animate at 12 fps (each frame held twice, for a hand-moved stop-motion feel); the "
        "3D flip-book runs at a smooth 30 fps. The same paper kit also makes still carousels and images.",
        S_INTRO))
    S.append(Paragraph("Built in", S_H2))
    S.append(item("Papercut stop-motion",
                  "Every element is a paper cut-out (torn sheets, taped art prints, caption strips, stars) "
                  "that slides, drops or pops into place, with a slight per-frame “boil” so it looks moved by "
                  "hand.", "the weekly sketchbook tour reel and all three Creator Studio ads",
                  "Make it a papercut stop-motion reel.",
                  save(frame("sketchbook_tour.mp4", 3.2), "a_papercut")))
    S.append(item("3D flip-book",
                  "An open sketchbook floats in a snowy night street and turns its pages in 3D. Each turning "
                  "page curves and catches the light, and the camera drifts gently.",
                  "the sketchbook flip-book reel", "Do it as a 3D flip-book.",
                  save(frame("sketchbook_flipbook.mp4", 8.6), "a_flipbook")))
    S.append(item("Flip-book over your own footage",
                  "The same turning book with a transparent background, laid over a video clip you supply "
                  "(your studio, your desk, a walk outside). No sample in this guide: it needs your clip.",
                  "available as an option of the flip-book renderer",
                  "Float the flip-book over this clip of my studio."))
    S.append(item("Torn-paper scene wipes",
                  "Each new scene arrives as a full-screen sheet of paper sliding in from the left, right, top "
                  "or bottom, with a torn leading edge and a soft shadow.",
                  "every scene change in the papercut reel and the ads", "Use paper wipes between scenes.",
                  save(frame("ads/ad_artists_you_paint.mp4", 2.62), "a_wipe")))
    S.append(item("Collage build-up",
                  "Pieces drop in one after another to fill a grid or a loose pile, e.g. a 10-day tracker "
                  "filling up, or every painting of the week landing in a heap.",
                  "the “day 1 … day 10” tracker and the outro pile",
                  "Show my week filling up day by day.",
                  save(frame("sketchbook_tour.mp4", 18.5), "a_collage")))
    S.append(item("Orbit / motion paths",
                  "Any piece can follow a path. In the sketchbook reel the paintings orbit a centre piece "
                  "(“you make your whole life revolve around it”).",
                  "the “revolve around it” scene", "Have my paintings orbit the centre one.",
                  save(frame("sketchbook_tour.mp4", 23.5), "a_orbit")))
    S.append(item("Animated GIFs inside a scene",
                  "A looping GIF plays inside a taped paper print, so animated art moves while everything "
                  "else stays papercut.", "the neon cat in the sketchbook reel",
                  "Use my animated GIF as one of the prints.",
                  save(frame("sketchbook_tour.mp4", 38), "a_gif")))
    S.append(item("Phone mock-up playback",
                  "A reel plays inside a phone, with Reels-style progress bars, side icons and a caption "
                  "bubble. Several phones can play side by side (e.g. hook A / B / C).",
                  "all three ads", "Show three versions playing on phones.",
                  save(frame("ads/ad_ugc_creators.mp4", 8.5), "a_phones")))
    S.append(item("Typed text reveal",
                  "Text types itself across a card, left to right, like a chat message being written.",
                  "the “ask Claude” prompt cards in the ads", "Type the prompt out on screen.",
                  save(frame("ads/ad_artists_you_paint.mp4", 7.9), "a_typed")))
    S.append(item("Animated voice waveform",
                  "A looping waveform card with a play button, used to show a voice-over.",
                  "the voice-over scenes in the ads", "Show a voice waveform while it talks.",
                  save(frame("ads/ad_artists_you_paint.mp4", 22.5), "a_wave")))
    S.append(item("Still collages (carousels and images)",
                  "The same paper kit laid out as still images: 4:5 carousel slides, 1:1 feed posts and "
                  "9:16 story images.", "the Creator Studio carousels and single-image ads",
                  "Turn this into a 6-slide carousel.",
                  save(Image.open(os.path.join(OUT, "ads", "carousel_artists", "slide_4.jpg")), "a_still")))

    S.append(Paragraph("Motion moves you can mix", S_H2))
    S.append(grid([
        ["Move", "What it does", "Works with"],
        ["Drop", "Falls in from slightly above, shrinking and straightening as it lands.", "any piece"],
        ["Pop", "Springs up from nothing with a small overshoot.", "any piece, captions, stickers"],
        ["Slide in", "Enters from the left, right, top or bottom with a slight tilt.", "any piece, full scenes"],
        ["Fade in / out", "Fades opacity in or out.", "any piece"],
        ["Shrink out", "Shrinks to nothing on exit.", "any piece"],
        ["Slide out", "Leaves the frame in any direction.", "any piece"],
        ["Boil", "Tiny per-frame jitter in position and rotation: the stop-motion look.", "papercut pieces"],
        ["Path", "Follows any route (orbit, arc, zig-zag) with its own rotation and scale.", "any piece"],
        ["Frame loop", "Plays a sequence of frames (GIF, video, waveform) in place.", "prints, phones, cards"],
        ["Wipe reveal", "Reveals left to right (typing, ink strike-throughs).", "text, strike-throughs"],
        ["Page turn", "3D page flip with curl and lighting.", "flip-book"],
        ["Camera drift", "Slow, gentle camera sway around the scene.", "flip-book"],
        ["Caption pop", "Caption scales up with a spring and fades out at the end.", "flip-book captions"],
        ["Fade to dark", "Scene dims at the end.", "flip-book ending"],
    ], [3.2 * cm, 9.6 * cm, 5.0 * cm]))

    S.append(Paragraph("Not built yet (can be added on request)", S_H2))
    S.append(Paragraph("These would need new code. None of them is in the renderers today.", S_INTRO))
    S.append(grid([
        ["Style", "What it would be"],
        ["Ken Burns pan and zoom", "Slow zoom and pan across a still photo or painting."],
        ["2.5D parallax", "Foreground and background layers moving at different speeds for depth."],
        ["Split screen / before-after", "Two clips side by side, or a slider wiping from sketch to finished art."],
        ["Hand-drawn line reveal", "Ink lines drawing themselves on, like a time-lapse sketch."],
        ["Zoom and whip transitions", "Fast punch-in or blurred whip pans between scenes."],
        ["Beat-synced cuts", "Scene changes timed to the beats of a music track."],
        ["Other video shapes", "1:1 and 4:5 video renders (stills already come in 1:1, 4:5 and 9:16)."],
    ], [5.2 * cm, 12.6 * cm]))
    build(os.path.join(GUIDES, "1_animation_styles.pdf"), "ANIMATION STYLES", MUSTARD, S)


# --------------------------------------------------------------------------- 2. caption styles

def caption_guide():
    S = []
    S.append(Paragraph(
        "Captions are burned into the video, so they show the same everywhere. Every caption below can use "
        "any paper and ink colour, wraps to fit, can tilt slightly, and comes in with any of the motion "
        "moves (drop, pop, slide, fade, typing).", S_INTRO))
    S.append(Paragraph("Built in", S_H2))

    def strip_tile(text, font, paper=PAPER_WHITE, ink=INK, bg=CREAM, seed=1):
        return tile(lambda s: s.strip(text, 220, font, paper=paper, ink=ink, rot=-2, seed=seed), bg=bg, seed=seed)

    S.append(item("Handwritten paper strip",
                  "A torn strip of paper with a handwritten caption (Caveat). The everyday caption style: "
                  "friendly and personal.", "most captions in the papercut reel and ads",
                  "Handwritten captions on torn paper.",
                  save(strip_tile("creating makes me happier.", caveat(84)), "c_hand")))
    S.append(item("Bold marker headline",
                  "Thick hand-lettered marker (Permanent Marker) on a paper strip, for hooks, titles and "
                  "punchlines. Any paper colour.", "titles, hooks, end cards",
                  "Make the hook a bold marker headline.",
                  save(tile(lambda s: (s.strip("YOU PAINT.", 160, marker(100), rot=-3, seed=3),
                                       s.strip("Claude handles the reels.", 310, marker(58), paper=COBALT,
                                               ink=PAPER_WHITE, rot=2, seed=4)), bg=MUSTARD, seed=2),
                       "c_marker")))
    S.append(item("Typewriter labels",
                  "Small typewritten slips (Special Elite) torn on every side, for lists, labels and asides.",
                  "the crossed-out chores and excuses",
                  "Put the list on typewriter labels.",
                  save(tile(lambda s: [s.put(text_strip(t, typewriter(54), paper=PAPER_WHITE if i % 2 else CREAM,
                                                        seed=10 + i, sides="tblr"), x, y, r)
                                       for i, (t, x, y, r) in enumerate((("too tired", 250, 130, -6),
                                                                         ("no time", 650, 160, 5),
                                                                         ("tomorrow!", 420, 320, 3)))],
                            bg=PINK, seed=5), "c_type")))
    S.append(item("Flip-book lettering",
                  "Big white hand-lettered captions with a soft shadow, floating over the scene. They pop in "
                  "with a spring, fade out, and shrink to fit long lines.", "the 3D flip-book reel",
                  "Big white hand-lettered captions over the scene.",
                  save(frame("sketchbook_flipbook.mp4", 6.0, (0, 120, 1080, 760)), "c_flip")))
    S.append(item("Reel caption bubble",
                  "A white rounded bubble with a handwritten caption, placed like an on-screen Reels caption, "
                  "plus optional labels such as “hook A”.", "the phone mock-ups in the ads",
                  "Add Reels-style caption bubbles.",
                  save(ma.phone([art("flowers_vase")], ["I tried it for 7 days"], w=420, label="hook C")[0]
                       .crop((0, 380, 470, 870)), "c_bubble")))
    S.append(item("Typed chat card",
                  "A card with a small header that types its message out, typewriter style. Hashtags are "
                  "automatically inked in blue.", "the “ask Claude” prompts and the caption card",
                  "Show the caption and hashtags typing out.",
                  save(tile(lambda s: mc.chat(s, "Weekly sketchbook tour. #sketchbooktour #inkdrawing "
                                                 "#collageart", 220, 7, header="caption", w=760, size=44),
                            bg=DUSTY_BLUE, seed=6), "c_chat")))
    S.append(item("Red-ink strike-through",
                  "A hand-drawn red line that draws itself across a caption, for “not anymore” moments.",
                  "the crossed-out chores and “an evening of tutorials”",
                  "Cross out the old way in red.",
                  save(tile(lambda s: (lambda im: s.put(strike(int(im.width * 0.9), 9), 450, 220, -3))(
                      s.put(text_strip("an evening of tutorials", typewriter(58), paper=CREAM, seed=8,
                                       sides="tblr"), 450, 220, -2)), seed=8), "c_strike")))
    S.append(item("Checklist ticks",
                  "A paper check-mark dot beside a handwritten strip. Great for feature lists and steps.",
                  "the “what you get” lists in the ads and carousels",
                  "List the features as ticks.",
                  save(tile(lambda s: s.ticks(["hand-lettered captions", "cover + hashtags"], 450, 140, 150,
                                              seed=12), bg=SAGE, seed=11), "c_ticks")))
    S.append(item("Price sticker",
                  "A scalloped sale sticker with the price in handwriting. The ₹ sign is supported (it is "
                  "set in Caveat, which has the glyph).", "the ₹699 lifetime-access end cards",
                  "Add a ₹699 sticker.",
                  save(tile(lambda s: s.put(ma.price_badge(380, 13), 450, 220, 8), bg=MUSTARD, seed=13),
                       "c_price")))
    S.append(item("Step numbers",
                  "A big numbered paper dot next to a marker title, for step-by-step reels.",
                  "the 1-2-3 steps in the beginners ad and carousel", "Number the steps.",
                  save(tile(lambda s: mc.step_head(s, 2, "describe the vibe", 14), bg=PINK, h=320, seed=14),
                       "c_step")))
    S.append(item("Post caption and hashtags",
                  "The text that goes under the post: a written caption plus a set of relevant hashtags, "
                  "saved as a text file next to the video.", "instagram_caption.txt for the sketchbook reel",
                  "Write the post caption and hashtags."))

    S.append(Paragraph("Fonts and colours", S_H2))
    S.append(grid([
        ["Font", "Look", "Notes"],
        ["Caveat", "Handwriting, regular to bold", "Has the ₹ sign. Used for prices."],
        ["Permanent Marker", "Thick hand-lettered marker", "No ₹ sign: write “Rs. 699” in marker text."],
        ["Special Elite", "Old typewriter", "Labels, prompts, chat cards."],
        ["Your own font", "Any .ttf you supply", "Drop it in the fonts folder and ask for it."],
    ], [3.6 * cm, 5.4 * cm, 8.8 * cm]))
    S.append(Spacer(1, 6))
    S.append(Paragraph(
        "Paper and ink colours: mustard, sage, terracotta, dusty blue, cream, pink, cobalt, charcoal, chartreuse, "
        "paper white, ink black and red ink, or colours pulled straight from your artwork.", S_BODY))
    S.append(Paragraph("Not built yet (can be added on request)", S_H2))
    S.append(grid([
        ["Caption style", "What it would be"],
        ["Word-by-word highlight", "Karaoke-style captions where each word lights up as it is spoken."],
        ["Auto subtitles from speech", "Captions transcribed from your own voice or footage audio. There is no "
                                       "speech-to-text step yet; captions are written from your brief."],
        ["Hindi and other scripts", "The current fonts are Latin-only. Devanagari etc. needs an added font "
                                    "(e.g. Noto Sans Devanagari)."],
        ["Emoji in captions", "The bundled fonts have no emoji glyphs; needs a colour emoji font."],
        ["Outlined / stroked text", "White text with a dark outline, the classic TikTok look."],
    ], [5.2 * cm, 12.6 * cm]))
    build(os.path.join(GUIDES, "2_caption_styles.pdf"), "CAPTION STYLES", PINK, S)


# --------------------------------------------------------------------------- 3. effects

def effects_guide():
    S = []
    S.append(Paragraph("Visual and audio effects the renderers use today, and ones that could be added.",
                       S_INTRO))
    S.append(Paragraph("Built in: paper and craft", S_H2))
    S.append(item("Torn paper edges",
                  "Any sheet or strip can have torn edges on any side, with a lighter fibrous rim where the "
                  "paper ripped.", "scene backgrounds, caption strips, hills",
                  "Tear the edges of the backgrounds.",
                  save(tile(lambda s: s.put(add_shadow(torn_sheet(620, 260, TERRACOTTA, 21, sides="tblr", amp=22)),
                                            450, 220, -3), bg=CREAM, seed=20), "e_torn")))
    S.append(item("Paper texture",
                  "Flat colour with blotchy fibres and fine grain, so nothing looks digital-flat.",
                  "every background and strip", None,
                  save(Image.fromarray(mc.paper_texture(900, 300, SAGE, 22, 9)), "e_paper")))
    S.append(item("Taped art prints",
                  "Your art printed with a scissor-cut white border, held by washi tape on top or at the "
                  "corners, in any tape colour.", "every painting in the papercut reels",
                  "Tape my paintings on with pink washi tape.",
                  save(tile(lambda s: (s.put(cutout(art("flowers_vase"), 300, 300, 23, tape="top"), 270, 220, -6),
                                       s.put(cutout(art("portrait_bob"), 300, 300, 24, tape="corners",
                                                    tape_color=(230, 170, 190)), 630, 220, 5)),
                            bg=MUSTARD, seed=23), "e_tape")))
    S.append(item("Soft drop shadows",
                  "Every piece casts a soft offset shadow, so the layers read as real paper on a desk.",
                  "everything in the papercut style", None))
    S.append(item("Paper stars and dots",
                  "Cut-paper stars and circles that pop in as accents.", "titles and end cards",
                  "Add some paper stars.",
                  save(tile(lambda s: [s.put(star(sz, c, 30 + i), x, 220, r, fit=False) for i, (x, sz, c, r) in
                                       enumerate(((180, 140, MUSTARD, -12), (430, 110, COBALT, 8),
                                                  (660, 160, TERRACOTTA, 15)))], bg=CREAM, seed=30), "e_stars")))
    S.append(item("Stop-motion boil",
                  "Each piece jitters by a pixel or two and a fraction of a degree every other frame, the "
                  "signature hand-animated wobble. Strength is adjustable per piece.",
                  "every papercut piece", "Give it more stop-motion wobble."))
    S.append(Paragraph("Built in: scene and light", S_H2))
    S.append(item("Snowfall with depth",
                  "Snowflakes in near and far layers: far ones fall behind the book, near ones in front, "
                  "larger and softer.", "the flip-book reel", "Make it snow.",
                  save(frame("sketchbook_flipbook.mp4", 9.5, (0, 1000, 1080, 1700)), "e_snow")))
    S.append(item("Lamp glow, light pools and haze",
                  "Warm street-lamp glows, pools of light on the snow and haze on the horizon.",
                  "the flip-book night scene", None,
                  save(frame("sketchbook_flipbook.mp4", 4.0, (0, 200, 1080, 800)), "e_glow")))
    S.append(item("Background defocus and foreground framing",
                  "The background is blurred like a shallow depth of field, with an out-of-focus tree in the "
                  "foreground framing the shot.", "the flip-book reel", None))
    S.append(item("Page-turn lighting",
                  "Turning pages darken and brighten as they curve towards and away from the light.",
                  "the flip-book reel", None,
                  save(frame("sketchbook_flipbook.mp4", 8.6, (0, 640, 1080, 1340)), "e_page")))
    S.append(item("Fade to dark",
                  "The scene dims for the ending.", "the end of the flip-book reel", "Fade out at the end."))
    S.append(item("Colours from your art",
                  "The main accent colours are pulled out of a painting and used for the swatches and paper.",
                  "the “it paints with your colours” scene",
                  "Use the colours from this painting.",
                  save(tile(lambda s: [s.put(add_shadow(paper_circle(130, c, 40 + i), 3, 5, 5, 0.3), 120 + i * 165,
                                             220, 0) for i, c in enumerate(ma.palette_of(art("clock_collage")))],
                            bg=PINK, seed=40), "e_palette")))
    S.append(Paragraph("Built in: sound", S_H2))
    S.append(grid([
        ["Effect", "What it does"],
        ["Neural voice-over", "Reads your lines aloud with a local neural voice (Kokoro). The voice model has 28 "
                              "English voices (US and UK, female and male); the ads use warm, upbeat and bright "
                              "ones."],
        ["Timed to every cut", "Each line starts as its scene lands. Lines that would overrun are sped up "
                               "slightly with the pitch kept natural."],
        ["Clean tails and levels", "Short fade at the end of each line, and the whole track is normalised."],
        ["Music-ready silent track", "Every video also comes with a silent track, so you can add trending audio "
                                     "inside Instagram, TikTok or YouTube."],
    ], [4.6 * cm, 13.2 * cm]))
    S.append(Paragraph("Not built yet (can be added on request)", S_H2))
    S.append(grid([
        ["Effect", "What it would be"],
        ["Background music bed", "A music track under the voice-over, lowered automatically while it speaks."],
        ["Sound effects", "Paper rustles, page flips, pops and whooshes on the matching moves."],
        ["Light leaks and lens flares", "Warm film-style light washes across the frame."],
        ["Confetti and sparkles", "Particle bursts on reveals and end cards."],
        ["Motion blur", "Blur on fast slides and whip moves."],
    ], [5.2 * cm, 12.6 * cm]))
    build(os.path.join(GUIDES, "3_effects.pdf"), "EFFECTS", SAGE, S)


# --------------------------------------------------------------------------- 4. filters

def grain_vignette(im, amount=1.0):
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    vig = 1 - 0.18 * amount * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / 2
    a = a * vig[..., None] + np.random.default_rng(1).normal(0, 2.5 * amount * 2, (h, w))[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def filters_guide():
    base = art("clock_collage").resize((560, 560))
    S = []
    S.append(Paragraph(
        "Nine colour filters plus your own colour grades (.cube LUT files) can go on anything Creator Studio makes: "
        "the papercut reel, the 3D flip-book, the ads, the carousels and images, or any finished video or image, "
        "with the voice-over and audio kept. Every filter has a strength from 0 to 1. Each preview below is made "
        "by the filter code itself, on the same painting, so you can compare.", S_INTRO))
    S.append(Paragraph("Colour filters", S_H2))
    arr = np.asarray(base)
    cells = [(save(base, "f_orig", 440), "<b>Original</b><br/>no filter")]
    for name in filters.FILTERS:
        title, _, rest = filters.DESCRIPTIONS[name].partition(": ")
        cells.append((save(Image.fromarray(filters.Look(name).apply(arr, frame=3)), "f_" + name, 440),
                      f"<b>{title}</b>  <font name='DejaVu' color='#7a756d'>{name}</font><br/>{rest}"))
    S.append(gallery(cells, cols=4, w=3.9 * cm))
    S.append(KeepTogether([Paragraph("Strength", S_H2), Paragraph(
        "Add <b>:0.5</b> (or any value from 0 to 1) to blend a filter in partly. Below: sepia at 25%, 50% and 100%.",
        S_BODY), Spacer(1, 4), gallery([(save(Image.fromarray(filters.Look("sepia", k).apply(arr)), f"f_s{int(k * 100)}", 440),
                       f"<b>sepia:{k:g}</b>") for k in (0.25, 0.5, 1.0)], cols=4, w=3.9 * cm)]))
    S.append(Paragraph("How to use them", S_H2))
    S.append(grid([
        ["To filter", "Ask for it / run"],
        ["An ad", "<i>“Make the artists ad warm.”</i><br/>python3 make_ads.py artists --filter warm"],
        ["An ad with its voice-over", "python3 make_ads.py artists --filter warm<br/>"
                                      "python3 make_voiceover.py artists --filter warm"],
        ["The papercut reel", "python3 make_video.py --filter vhs:0.6"],
        ["The 3D flip-book", "python3 make_flipbook.py --filter cool  (also with --bg your_clip.mp4)"],
        ["Carousels and images", "python3 make_carousels.py creators --filter duotone"],
        ["Anything already made", "python3 filters.py IN.mp4 OUT.mp4 --filter sepia:0.8<br/>"
                                  "Works on videos (audio kept), images, or a whole folder of slides."],
        ["Your own colour grade", "python3 make_ads.py beginners --lut my_grade.cube<br/>"
                                  "python3 filters.py IN.mp4 OUT.mp4 --lut my_grade.cube --filter contrast:0.4"],
        ["See them all", "python3 filters.py --list<br/>python3 filters.py --showreel IN.mp4 OUT.mp4"],
    ], [4.4 * cm, 13.4 * cm]))
    S.append(Spacer(1, 6))
    S.append(Paragraph(
        "Filtered files are saved next to the originals with the filter in the name (for example "
        "ad_artists_you_paint_warm.mp4), so nothing is overwritten. LUTs are standard 3D .cube files as exported "
        "by DaVinci Resolve, Premiere, Lightroom and most colour-grading apps; the LUT is applied first, then the "
        "filter. VHS and riso move a little from frame to frame, like real tape and print grain; the other filters "
        "are steady, so videos don't flicker.", S_BODY))
    S.append(Paragraph("Also part of the styles", S_H2))
    haze = np.asarray(base).astype(np.float32) * 0.72 + np.array([120, 128, 150]) * 0.28
    cells = [
        (save(grain_vignette(base), "f_grain", 440), "<b>Film grain + vignette</b><br/>on every papercut frame; "
                                                    "the grain changes each frame"),
        (save(base.filter(ImageFilter.GaussianBlur(9)), "f_blur", 440), "<b>Defocus blur</b><br/>flip-book "
                                                                       "backgrounds, foreground tree"),
        (save(Image.fromarray(np.clip(haze, 0, 255).astype(np.uint8)), "f_haze", 440),
         "<b>Haze</b><br/>misty horizon in the night scene"),
        (save(Image.blend(base, Image.new("RGB", base.size, (6, 7, 10)), 0.55), "f_dark", 440),
         "<b>Fade to dark</b><br/>ending dim of the flip-book"),
        (save(frame("sketchbook_flipbook.mp4", 4.0, (0, 700, 1080, 1780)), "f_night", 440),
         "<b>Night scene grade</b><br/>cool blue night with warm lamps (flip-book)"),
    ]
    S.append(gallery(cells, cols=5, w=3.05 * cm))
    build(os.path.join(GUIDES, "4_filters.pdf"), "FILTERS", DUSTY_BLUE, S,
          sub="nine colour filters and your own colour grades, on everything it makes")


def main():
    os.makedirs(GUIDES, exist_ok=True)
    animation_guide()
    caption_guide()
    effects_guide()
    filters_guide()


if __name__ == "__main__":
    main()
