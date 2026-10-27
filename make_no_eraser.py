#!/usr/bin/env python3
""""Why I draw without an eraser": a 1080x1920 reel built from the dragonfly ink page.

Black ink background (no paper/beige), white hand-lettered captions that "write"
themselves in, red accents for the key words. The artwork photos are shown in
neutral greyscale so the warm paper tone never reads as beige.

The voice-over (audio/no_eraser_voice_raw.mp3) is cut down to the spoken phrases
listed in PHRASES: dead air, the off-script aside and long pauses are dropped,
pauses are re-spaced, then the voice is denoised, compressed and loudness-normalised.
Each phrase is also the caption shown while it is spoken.

Usage:  python3 make_no_eraser.py               # renders output/no_eraser.mp4
        python3 make_no_eraser.py --preview 3 9 # stills at the given seconds -> output/preview/
        python3 make_no_eraser.py --wide        # 1920x1080 landscape cut -> output/no_eraser_wide.mp4
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

from make_video import caveat, marker

ROOT = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(ROOT, "artworks")
OUT = os.path.join(ROOT, "output")

WIDE = "--wide" in sys.argv          # 16:9 landscape cut: art on the left, captions on the right
W, H = (1920, 1080) if WIDE else (1080, 1920)
FPS = 30
DURATION = 50.0       # set by build() from the edited voice length
VOICE_RAW = os.path.join(ROOT, "audio", "no_eraser_voice_raw.mp3")
VOICE_OUT = os.path.join(OUT, "no_eraser_voice.wav")
SR = 48000
VOICE_START = 3.4     # the hook plays before the voice comes in
OUTRO = 6.0

INK_BLACK = (14, 14, 16)
CHALK = (246, 246, 244)
RED = (232, 62, 48)
GREY = (150, 150, 155)
ERASER_PINK = (236, 128, 150)
ERASER_BLUE = (70, 110, 200)

if WIDE:
    TEXT_W = 820      # caption column to the right of the art
    TEXT_X = 1400     # centre of the caption column
    TEXT_Y = 560      # caption blocks are centred on this line
    ART_C = (530, 540)
    CARD = (780, 860)
    BADGE_C = (TEXT_X, 250)
else:
    TEXT_W = 920      # max caption width
    TEXT_X = W // 2
    TEXT_Y = 1170     # top of the caption zone (below the art card, above the IG UI)
    ART_C = (W // 2, 140 + 900 // 2)          # card zone y 140..1040
    CARD = (840, 900)
    BADGE_C = (150, 1080)


# --------------------------------------------------------------------------- easing

def clamp(x):
    return max(0.0, min(1.0, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def ease_out_back(x, s=1.7):
    x = clamp(x) - 1
    return 1 + x * x * ((s + 1) * x + s)


# --------------------------------------------------------------------------- images

def neutral(im, cutoff=1.5):
    """Greyscale + levels so paper reads as clean white/grey, never beige."""
    g = ImageOps.autocontrast(im.convert("L"), cutoff=cutoff)
    return g.convert("RGB")


def load_sources():
    scan = Image.open(os.path.join(ART, "dragonflies_scan.jpg"))
    scan = neutral(scan.crop((265, 265, 2225, 3120)))
    hand = Image.open(os.path.join(ART, "dragonflies_in_hand.jpg"))
    hand = neutral(hand.crop((520, 180, 2620, 2820)), cutoff=1.0)
    selfie = ImageOps.exif_transpose(Image.open(os.path.join(ART, "dragonflies_selfie.jpg"))).convert("RGB")
    return scan, hand, selfie


class Card:
    """An image panel with a slow Ken Burns move between two normalised crop boxes."""

    def __init__(self, src, size, center, t0, t1, box0, box1, enter=0.6, leave=0.5, rot=0.0):
        self.src, self.size, self.center = src, size, center
        self.t0, self.t1, self.box0, self.box1 = t0, t1, box0, box1
        self.enter, self.leave, self.rot = enter, leave, rot

    def active(self, t):
        return self.t0 <= t < self.t1

    def frame(self, t):
        k = ease_in_out((t - self.t0) / (self.t1 - self.t0))
        b = [clamp(a + (c - a) * k) for a, c in zip(self.box0, self.box1)]
        sw, sh = self.src.size
        box = (b[0] * sw, b[1] * sh, b[2] * sw, b[3] * sh)
        return self.src.resize(self.size, Image.BILINEAR, box=box)

    def draw(self, canvas, t, img=None):
        img = img or self.frame(t)
        e = ease_out((t - self.t0) / self.enter)
        l = ease_in_out((t - (self.t1 - self.leave)) / self.leave)
        alpha = e * (1 - l)
        dy = (1 - e) * 140 - l * 120
        rot = self.rot * (0.4 + 0.6 * e)
        tile = img.convert("RGBA")
        if rot:
            tile = tile.rotate(rot, Image.BICUBIC, expand=True)
        if alpha < 1:
            tile.putalpha(tile.getchannel("A").point(lambda v: int(v * alpha)))
        x = int(self.center[0] - tile.width / 2)
        y = int(self.center[1] - tile.height / 2 + dy)
        canvas.alpha_composite(tile, (x, y))


class InkReveal(Card):
    """The page's lines draw themselves in white on black, then the real page fades up."""

    def __init__(self, *a, draw_end=3.0, page_end=4.0, **kw):
        super().__init__(*a, **kw)
        self.draw_end, self.page_end = draw_end, page_end
        page = self.src.resize(self.size, Image.LANCZOS)
        self.page = page
        lum = np.asarray(page.convert("L")).astype(np.float32) / 255.0
        self.lines = np.clip((0.62 - lum) * 4.0, 0, 1)        # ink strength
        rng = np.random.default_rng(7)
        h, w = lum.shape
        noise = rng.random((h // 40 + 2, w // 40 + 2)).astype(np.float32)
        noise = np.asarray(Image.fromarray(noise).resize((w, h), Image.BICUBIC))
        yy, xx = np.mgrid[0:h, 0:w]
        # sweep from the head of the top dragonfly downward, broken up by noise
        self.order = np.clip(0.72 * (yy / h) + 0.12 * np.abs(xx / w - 0.5) + 0.22 * noise, 0, 1)
        self.page_np = np.asarray(page).astype(np.float32)

    def frame(self, t):
        p = (t - self.t0) / self.draw_end
        a = np.clip((p * 1.15 - self.order) * 9.0, 0, 1)
        white = (self.lines * a)[..., None] * np.array(CHALK, np.float32)
        base = white + (1 - (self.lines * a)[..., None]) * np.array(INK_BLACK, np.float32)
        f = ease_in_out((t - self.t0 - self.draw_end) / (self.page_end - self.draw_end))
        out = base * (1 - f) + self.page_np * f
        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


# --------------------------------------------------------------------------- captions

def parse(text):
    """'plain *red words* plain' -> [(word, is_red), ...]"""
    words, red = [], False
    for tok in text.split(" "):
        start = tok.startswith("*")
        if start:
            red = True
            tok = tok[1:]
        end = tok.endswith("*") or tok.rstrip(".,?!:").endswith("*")
        this_red = red
        if end:
            tok = tok.replace("*", "")
            red = False
        words.append((tok, this_red))
    return words


def render_lines(text, font, max_w=TEXT_W, color=CHALK):
    """Returns a list of (RGBA line image, red_spans) for a caption."""
    words = parse(text)
    space = font.getlength(" ")
    lines, cur, cur_w = [], [], 0.0
    for w, r in words:
        wl = font.getlength(w)
        if cur and cur_w + space + wl > max_w:
            lines.append(cur)
            cur, cur_w = [], 0.0
        cur.append((w, r))
        cur_w += (space if len(cur) > 1 else 0) + wl
    if cur:
        lines.append(cur)
    asc, desc = font.getmetrics()
    out = []
    for ln in lines:
        lw = int(sum(font.getlength(w) for w, _ in ln) + space * (len(ln) - 1)) + 20
        im = Image.new("RGBA", (lw, asc + desc + 24), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        x, spans = 10, []
        for w, r in ln:
            d.text((x, 8), w, font=font, fill=(RED if r else color) + (255,))
            wl = font.getlength(w)
            if r:
                spans.append((x, x + wl))
            x += wl + space
        out.append((im, spans))
    return out


def scribble_underline(width, seed, color=RED, thick=9):
    """A quick hand-drawn double underline."""
    rng = np.random.default_rng(seed)
    h = 46
    im = Image.new("RGBA", (int(width) + 30, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for k, y0 in enumerate((14, 30)):
        n = 14
        pts = [(15 + width * i / n + rng.uniform(-3, 3), y0 + rng.uniform(-3, 3) + (i / n) * (4 if k else -3))
               for i in range(n + 1)]
        if k:
            pts = pts[:int(n * 0.85)]
        d.line(pts, fill=color + (255,), width=thick if not k else thick - 3, joint="curve")
    return im


def strike_line(width, seed, color=RED, thick=11):
    rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (int(width) + 30, 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = [(10 + width * i / 10, 34 - i * 1.2 + rng.uniform(-2, 2)) for i in range(11)]
    d.line(pts, fill=color + (255,), width=thick, joint="curve")
    return im


class Caption:
    """A block of lines that 'write' in left-to-right, then fade out."""

    def __init__(self, text, t0, t1, y, size=82, font=None, align="center", mark=None,
                 cps=34.0, color=CHALK, line_gap=1.08, write_in=None, cx=None, center_y=False,
                 max_w=None):
        self.font = font or caveat(size)
        self.lines = render_lines(text, self.font, max_w=max_w or TEXT_W, color=color)
        self.t0, self.t1, self.align, self.mark = t0, t1, align, mark
        self.cx = W // 2 if cx is None else cx
        self.cps, self.line_gap = cps, line_gap
        self.lh = int(sum(self.font.getmetrics()) * line_gap)
        self.y = y - self.height // 2 if center_y else y
        # writing schedule per line
        self.sched, t = [], t0
        for im, _ in self.lines:
            dur = max(0.35, im.width / (self.cps * self.font.size * 0.45))
            self.sched.append((t, dur))
            t += dur + 0.06
        if write_in and t - t0 > write_in:          # squeeze writing to finish within the spoken phrase
            k = write_in / (t - t0)
            self.sched = [(t0 + (ts - t0) * k, d * k) for ts, d in self.sched]
            t = t0 + write_in
        self.written = t
        self.marks = []
        if mark:
            for li, (im, spans) in enumerate(self.lines):
                for si, (a, b) in enumerate(spans):
                    fn = scribble_underline if mark == "underline" else strike_line
                    self.marks.append((li, a, fn(b - a, seed=li * 7 + si)))

    @property
    def height(self):
        return self.lh * len(self.lines)

    def active(self, t):
        return self.t0 <= t < self.t1

    def draw(self, canvas, t):
        fade = 1 - ease_in_out((t - (self.t1 - 0.35)) / 0.35)
        lift = (1 - fade) * -30
        for li, ((im, _), (ts, dur)) in enumerate(zip(self.lines, self.sched)):
            p = (t - ts) / dur
            if p <= 0:
                continue
            x = self.cx - im.width // 2 if self.align == "center" else 80
            y = int(self.y + li * self.lh + lift)
            reveal = int(im.width * ease_out(p)) if p < 1 else im.width
            if reveal <= 0:
                continue
            piece = im.crop((0, 0, reveal, im.height))
            if fade < 1:
                piece.putalpha(piece.getchannel("A").point(lambda v: int(v * fade)))
            canvas.alpha_composite(piece, (x, y))
            for mli, a, mk in self.marks:
                if mli != li:
                    continue
                mp = ease_out((t - self.written - 0.1) / 0.45)
                if mp <= 0:
                    continue
                piece = mk.crop((0, 0, max(1, int(mk.width * mp)), mk.height))
                if fade < 1:
                    piece.putalpha(piece.getchannel("A").point(lambda v: int(v * fade)))
                asc = self.font.getmetrics()[0]
                oy = asc - 4 if self.mark == "underline" else 8 + asc * 0.82 - 34
                canvas.alpha_composite(piece, (int(x + a - 15), int(y + oy)))


class Badge:
    """Big red reason number that pops in, with a thin white rule."""

    def __init__(self, label, t0, t1, center):
        f = marker(150)
        bb = f.getbbox(label)
        self.im = Image.new("RGBA", (bb[2] + 40, bb[3] + 40), (0, 0, 0, 0))
        ImageDraw.Draw(self.im).text((20, 10), label, font=f, fill=RED + (255,))
        self.t0, self.t1, self.center = t0, t1, center

    def active(self, t):
        return self.t0 <= t < self.t1

    def draw(self, canvas, t):
        s = ease_out_back((t - self.t0) / 0.45)
        fade = 1 - ease_in_out((t - (self.t1 - 0.35)) / 0.35)
        if s <= 0.02 or fade <= 0:
            return
        im = self.im.resize((max(1, int(self.im.width * s)), max(1, int(self.im.height * s))), Image.BICUBIC)
        im = im.rotate(-6, Image.BICUBIC, expand=True)
        if fade < 1:
            im.putalpha(im.getchannel("A").point(lambda v: int(v * fade)))
        canvas.alpha_composite(im, (int(self.center[0] - im.width / 2), int(self.center[1] - im.height / 2)))


class Eraser:
    """Drawn eraser that drops in and gets crossed out in red."""

    def __init__(self, t0, t1, center, strike_at):
        w, h = 460, 200
        im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((20, 20, 20 + w, 20 + h), 36, fill=ERASER_PINK + (255,), outline=CHALK + (255,), width=6)
        d.rectangle((20 + int(w * 0.58), 23, 20 + int(w * 0.8), 17 + h), fill=ERASER_BLUE + (255,))
        d.rounded_rectangle((20, 20, 20 + w, 20 + h), 36, outline=CHALK + (255,), width=6)
        self.im = im.rotate(12, Image.BICUBIC, expand=True)
        self.t0, self.t1, self.center, self.strike_at = t0, t1, center, strike_at
        rng = np.random.default_rng(3)
        self.x1 = [(-300 + 600 * i / 12, -150 + 300 * i / 12 + rng.uniform(-6, 6)) for i in range(13)]
        self.x2 = [(300 - 600 * i / 12, -150 + 300 * i / 12 + rng.uniform(-6, 6)) for i in range(13)]

    def active(self, t):
        return self.t0 <= t < self.t1

    def draw(self, canvas, t):
        fade = 1 - ease_in_out((t - (self.t1 - 0.35)) / 0.35)
        drop = ease_out_back((t - self.t0) / 0.55, 1.3)
        cx, cy = self.center
        im = self.im
        if fade < 1:
            im = im.copy()
            im.putalpha(im.getchannel("A").point(lambda v: int(v * fade)))
        canvas.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2 - (1 - drop) * 500)))
        d = ImageDraw.Draw(canvas)
        col = RED + (int(255 * fade),)
        for k, pts in enumerate((self.x1, self.x2)):
            p = ease_out((t - self.strike_at - k * 0.28) / 0.3)
            if p <= 0:
                continue
            n = max(2, int(len(pts) * p))
            d.line([(cx + x, cy + y) for x, y in pts[:n]], fill=col, width=20, joint="curve")



# --------------------------------------------------------------------------- voice

# (start, end) in the raw recording, caption text, caption mark, pause after (s).
# Timings come from a silence/transcript pass over the raw take. Everything not
# listed is cut: 13 s of lead-in noise, the aside at 26.9-28.5 s and the tail.
PHRASES = [
    [(12.98, 14.67), "Most beginners don't start", None, 0.22],
    [(15.11, 18.51), "because they fear what they will make won't be good.", None, 0.40],
    [(19.50, 22.04), "Leaving the eraser means, from the very beginning,", None, 0.22],
    [(22.46, 25.97), "it's an assurance that this page is *meant to be imperfect.*", "underline", 0.85],
    [(29.11, 32.31), "For anxious people, an eraser creates *more anxiety.*", None, 0.40],
    [(32.88, 36.88), "When you have the option to erase, you will choose to perfect.", None, 0.34],
    [(37.46, 41.12), "Hence your hand reaches out to the eraser quite often.", None, 0.40],
    [(41.69, 45.70), "Eliminating it means now you have to face the mess", None, 0.18],
    [(46.15, 47.78), "without even trying to correct it.", None, 0.36],
    [(48.39, 50.58), "And eventually, it makes us *calmer.*", "underline", 0.85],
    [(51.60, 54.86), "Life gives us the option to improvise, or to redo,", None, 0.22],
    [(55.26, 56.61), "but never to *undo.*", "strike", 0.40],
    [(57.15, 59.27), "You never stop living because of that.", None, 0.34],
    [(59.77, 61.96), "Why should art be any *different?*", "underline", 0.0],
]
PAD_IN, PAD_OUT = 0.07, 0.12          # keep soft consonants / breath tails around each phrase


def build_voice():
    """Cut, re-space and polish the voice. Returns [(new_start, new_end), ...] per phrase."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", VOICE_RAW, "-ac", "1", "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32)
    tone = a[int(3.6 * SR):int(6.3 * SR)]              # room tone from the quiet lead-in
    fade = int(0.012 * SR)
    ramp = np.linspace(0, 1, fade, dtype=np.float32)
    parts, spans, t = [], [], 0.0

    def room(sec):
        n = int(sec * SR)
        return np.resize(tone, n) * 0.6

    for (s, e), _, _, gap in PHRASES:
        seg = a[int((s - PAD_IN) * SR):int((e + PAD_OUT) * SR)].copy()
        seg[:fade] *= ramp
        seg[-fade:] *= ramp[::-1]
        parts.append(seg)
        spans.append((t + PAD_IN, t + PAD_IN + (e - s)))
        t += len(seg) / SR
        if gap:
            parts.append(room(gap))
            t += gap
    edit = np.concatenate([room(0.15)] + parts + [room(0.6)])
    spans = [(x + 0.15, y + 0.15) for x, y in spans]
    os.makedirs(OUT, exist_ok=True)
    chain = ("highpass=f=85,afftdn=nr=14:nf=-42:tn=1,"
             "equalizer=f=250:t=q:w=1.2:g=-2,equalizer=f=3500:t=q:w=1.0:g=2.5,"
             "deesser=i=0.4,acompressor=threshold=-22dB:ratio=3:attack=8:release=120:makeup=2,"
             "loudnorm=I=-15:TP=-1.5:LRA=7")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-af", chain, "-ar", str(SR), "-ac", "2", VOICE_OUT], input=edit.tobytes(), check=True)
    return spans, len(edit) / SR

# --------------------------------------------------------------------------- story

ITEMS = []


def build():
    global DURATION
    scan, hand, selfie = load_sources()
    spans, voice_len = build_voice()
    spans = [(VOICE_START + x, VOICE_START + y) for x, y in spans]
    DURATION = round(VOICE_START + voice_len + OUTRO, 2)
    cw, ch = CARD

    def captions(first, last, end):
        for i in range(first, last + 1):
            (s0, s1), text = spans[i], PHRASES[i][1]
            nxt = spans[i + 1][0] - 0.05 if i < last else end
            big = PHRASES[i][2] == "strike"
            y = TEXT_Y + (0 if WIDE else 30 if big else 0)
            ITEMS.append(Caption(text, s0 - 0.08, nxt, y, size=116 if big else 82, cx=TEXT_X, center_y=WIDE,
                                 mark=PHRASES[i][2], write_in=max(0.5, (s1 - s0) * 0.85)))

    # 0. Hook (before the voice) ---------------------------------------------
    ITEMS.append(Eraser(0.0, VOICE_START, (W // 2, 380 if WIDE else 700), strike_at=1.1))
    ITEMS.append(Caption("I stopped using an *eraser.*", 0.25, VOICE_START, 640 if WIDE else 1000, size=104,
                         write_in=1.0, max_w=1400))
    ITEMS.append(Caption("Here's why", 1.9, VOICE_START, 800 if WIDE else 1260, size=70, color=GREY))

    # 1. Reason 01: the page draws itself while she speaks ---------------------
    t0, t1 = VOICE_START - 0.2, spans[4][0] - 0.25
    rev_h = ch
    rev_w = int(rev_h * scan.width / scan.height)
    ITEMS.append(InkReveal(scan, (rev_w, rev_h), ART_C, t0, t1,
                           (0, 0, 1, 1), (0, 0, 1, 1), enter=0.3, leave=0.5, draw_end=4.0, page_end=5.2))
    ITEMS.append(Badge("01", t0 + 0.3, t1, BADGE_C))
    captions(0, 3, t1)

    # 2. Reason 02 ------------------------------------------------------------
    t0, t1 = t1, spans[10][0] - 0.25
    if WIDE:                                       # crop that keeps the card's aspect, ending at the page foot
        k = (ch / cw) * scan.width / scan.height
        boxes = (0.0, 1 - k, 1.0, 1.0), (0.05, 1 - 0.6 * k, 0.65, 1.0)
    else:
        boxes = (0.0, 0.45, 1.0, 1.0), (0.05, 0.56, 0.62, 0.9)
    ITEMS.append(Card(scan, (cw, ch), ART_C, t0, t1, *boxes))
    ITEMS.append(Badge("02", t0 + 0.4, t1, BADGE_C))
    captions(4, 9, t1)

    # 3. Reason 03 ------------------------------------------------------------
    t0, t1 = t1, spans[13][1] + 0.9
    k = (ch / cw) * hand.width / hand.height
    ITEMS.append(Card(hand, (cw, ch), ART_C, t0, t1,
                      (0.0, 0.0, 1.0, k), (0.1, 0.18, 0.9, 0.18 + 0.8 * k)))
    ITEMS.append(Badge("03", t0 + 0.4, t1, BADGE_C))
    captions(10, 13, t1)

    # 4. Outro ----------------------------------------------------------------
    t0, t1 = t1, DURATION + 1
    sw = 640 if WIDE else 760
    sh = int(sw * 1.18)
    ratio = (sh / sw) * selfie.width / selfie.height
    center = ART_C if WIDE else (W // 2, 140 + sh // 2)
    ITEMS.append(Card(selfie, (sw, sh), center, t0, t1,
                      (0.0, 0.0, 1.0, ratio), (0.04, 0.02, 0.96, 0.02 + 0.92 * ratio), rot=3, leave=0.01))
    ys = (400, 510, 690) if WIDE else (1160, 1270, 1440)
    ITEMS.append(Caption("Put the eraser down.", t0 + 0.6, t1, ys[0], size=96, cx=TEXT_X))
    ITEMS.append(Caption("Pick up the *pen.*", t0 + 1.7, t1, ys[1], size=96, mark="underline", cx=TEXT_X))
    ITEMS.append(Caption("Save this for your next blank page", t0 + 3.2, t1, ys[2], size=64, color=GREY, cx=TEXT_X))


def setup():
    global GRAIN
    build()
    rng = np.random.default_rng(11)
    yy, xx = np.mgrid[0:H, 0:W]
    vig = (1 - 0.28 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2).astype(np.float32)
    GRAIN = [(vig, rng.normal(0, 3.0, (H, W)).astype(np.float32)) for _ in range(3)]


def render_frame(frame):
    t = frame / FPS
    canvas = Image.new("RGBA", (W, H), INK_BLACK + (255,))
    for it in ITEMS:
        if it.active(t):
            it.draw(canvas, t)
    arr = np.asarray(canvas.convert("RGB")).astype(np.float32)
    vig, g = GRAIN[(frame // 2) % 3]
    arr = arr * vig[..., None] + g[..., None]
    return np.clip(arr, 0, 255).astype(np.uint8).tobytes()


def main():
    os.makedirs(OUT, exist_ok=True)
    setup()
    if "--preview" in sys.argv:
        pdir = os.path.join(OUT, "preview")
        os.makedirs(pdir, exist_ok=True)
        times = [float(a) for a in sys.argv[sys.argv.index("--preview") + 1:]] or \
            [2.5, 6.5, 9.8, 14, 19, 24, 31, 36, 39, 43, 49]
        for ts in times:
            Image.frombytes("RGB", (W, H), render_frame(int(ts * FPS))).save(
                os.path.join(pdir, f"ne{'_wide' if WIDE else ''}_t{ts:05.1f}.jpg"), quality=85)
        return
    n = int(DURATION * FPS)
    name = "no_eraser_wide" if WIDE else "no_eraser"
    out = os.path.join(OUT, name + ".mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", VOICE_OUT, "-af", f"adelay={int(VOICE_START * 1000)}:all=1,apad",
           "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for i, buf in enumerate(pool.imap(render_frame, range(n), chunksize=4)):
            proc.stdin.write(buf)
            if i % 150 == 0:
                print(f"frame {i}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()
    Image.frombytes("RGB", (W, H), render_frame(int((VOICE_START + 6.0) * FPS))).save(
        os.path.join(OUT, name + "_cover.jpg"), quality=92)
    print("wrote", out)


if __name__ == "__main__":
    main()
