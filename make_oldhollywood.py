#!/usr/bin/env python3
"""Old Hollywood ad film: turns a road clip into a 1950s-style colour commercial.

Stabilized footage in the 1.37:1 Academy frame, a three-strip-colour grade,
art deco title and end cards, superimposed taglines, iris transitions, and
film wear (grain, flicker, dust, scratches, halation). No gate weave, so the
picture stays steady.

--art makes an art-house cut instead: black and white through a red filter
(dark skies, bright clouds), slowed to two-thirds speed, plain black
intertitles with short poetic lines and slow fades to black.

Usage:  python3 make_oldhollywood.py [--art] input.mp4 [output.mp4]
"""
import os
import random
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(ROOT, "fonts")
OUT = os.path.join(ROOT, "output")

W, H = 1480, 1080        # Academy 1.37:1 picture, pillarboxed into 1920x1080
FPS = 24
TITLE_LEN = 4.5
END_LEN = 5.0
XF_IN = 1.0              # dissolve from title card into the footage
XF_OUT = 1.2             # iris close into the end card

GOLD = (214, 178, 96)
CREAM = (246, 234, 208)
MAROON = (92, 20, 28)
MAROON_DARK = (30, 6, 9)

# (start, end) in seconds of footage, text
SUPERS = [
    (5.0, 10.5, "Smooth as silk."),
    (16.0, 21.5, "Built for the open road."),
    (27.0, 32.5, "Where every mile is a picture."),
]

ART_SLOW = 1.5           # art cut plays at 1/1.5 speed
ART_SUPERS = [
    (7.0, 14.0, "Somewhere between leaving and arriving."),
    (24.0, 31.0, "The road remembers nothing."),
    (41.0, 48.0, "And still, we go on."),
    (62.0, 69.0, "Every horizon, a beginning."),
]

# Three-strip colour for the ad, red-filtered monochrome for the art cut
AD_GRADE = (
    "colorchannelmixer=rr=1.18:rg=-0.09:rb=-0.09:gr=-0.08:gg=1.16:gb=-0.08:br=-0.07:bg=-0.07:bb=1.14,"
    "curves=r='0/0.05 0.5/0.56 1/0.98':g='0/0.04 0.5/0.51 1/0.94':b='0/0.05 0.5/0.45 1/0.84',"
    "eq=saturation=1.12:contrast=1.08,gblur=sigma=0.7"
)
ART_GRADE = (
    "colorchannelmixer=rr=0.75:rg=0.35:rb=-0.10:gr=0.75:gg=0.35:gb=-0.10:br=0.75:bg=0.35:bb=-0.10,"
    "curves=all='0/0 0.12/0.04 0.5/0.50 0.88/0.95 1/1',"
    "colorchannelmixer=rr=1.0:gg=0.98:bb=0.94,gblur=sigma=0.5,"
    f"setpts={ART_SLOW}*PTS,framerate=fps={FPS}:interp_start=0:interp_end=255"
)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def centered(draw, y, text, fnt, fill, spacing=0):
    if spacing:
        widths = [draw.textlength(c, font=fnt) for c in text]
        x = (W - sum(widths) - spacing * (len(text) - 1)) / 2
        for c, w in zip(text, widths):
            draw.text((x, y), c, font=fnt, fill=fill, anchor="ls")
            x += w + spacing
    else:
        draw.text((W / 2, y), text, font=fnt, fill=fill, anchor="ms")


def deco_background():
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
    t = np.clip(r, 0, 1)[..., None]
    img = np.array(MAROON) * (1 - t) + np.array(MAROON_DARK) * t
    im = Image.fromarray(img.astype(np.uint8), "RGB")
    d = ImageDraw.Draw(im)
    # double frame with stepped art deco corners
    for inset, width in ((56, 4), (74, 2)):
        d.rectangle([inset, inset, W - inset, H - inset], outline=GOLD, width=width)
    for cx, cy, sx, sy in ((90, 90, 1, 1), (W - 90, 90, -1, 1), (90, H - 90, 1, -1), (W - 90, H - 90, -1, -1)):
        for i, n in enumerate((70, 50, 30)):
            o = i * 12
            d.line([(cx + sx * o, cy + sy * o), (cx + sx * (o + n), cy + sy * o)], fill=GOLD, width=2)
            d.line([(cx + sx * o, cy + sy * o), (cx + sx * o, cy + sy * (o + n))], fill=GOLD, width=2)
    # sunburst rays behind the centre
    rays = Image.new("L", (W, H), 0)
    rd = ImageDraw.Draw(rays)
    for k in range(36):
        a0, a1 = k * 10, k * 10 + 4
        rd.pieslice([W / 2 - 900, H / 2 - 900, W / 2 + 900, H / 2 + 900], a0, a1, fill=18)
    mask = Image.fromarray((np.clip(1.15 - r, 0, 1) * 255).astype(np.uint8))
    rays = Image.fromarray((np.array(rays) * (np.array(mask) / 255)).astype(np.uint8))
    im = Image.composite(Image.new("RGB", (W, H), GOLD), im, rays)
    return im, ImageDraw.Draw(im)


def ornament(d, y, half=260):
    d.line([(W / 2 - half, y), (W / 2 - 22, y)], fill=GOLD, width=2)
    d.line([(W / 2 + 22, y), (W / 2 + half, y)], fill=GOLD, width=2)
    d.polygon([(W / 2, y - 12), (W / 2 + 12, y), (W / 2, y + 12), (W / 2 - 12, y)], fill=GOLD)


def title_card(path):
    im, d = deco_background()
    centered(d, 330, "PRESENTED IN GLORIOUS COLOUR", font("PlayfairDisplaySC-Italic.ttf", 40), CREAM, spacing=4)
    ornament(d, 380)
    centered(d, 590, "The Open Road", font("Limelight-Regular.ttf", 156), GOLD)
    ornament(d, 680)
    centered(d, 770, "A MOTORING PICTURE", font("PlayfairDisplaySC-Italic.ttf", 46), CREAM, spacing=6)
    im.save(path)


def end_card(path):
    im, d = deco_background()
    centered(d, 470, "THE OPEN ROAD", font("Limelight-Regular.ttf", 120), GOLD, spacing=6)
    ornament(d, 540, half=320)
    centered(d, 640, "Go further — in style.", font("PlayfairDisplaySC-Italic.ttf", 64), CREAM)
    centered(d, 880, "THE END", font("PlayfairDisplaySC-Italic.ttf", 38), GOLD, spacing=10)
    im.save(path)


def art_title_card(path):
    im = Image.new("RGB", (W, H), (8, 8, 8))
    d = ImageDraw.Draw(im)
    centered(d, 560, "THE ROAD", font("PlayfairDisplaySC-Italic.ttf", 96), CREAM, spacing=24)
    centered(d, 650, "a film in black and white", font("PlayfairDisplaySC-Italic.ttf", 34), (170, 165, 155))
    im.save(path)


def art_end_card(path):
    im = Image.new("RGB", (W, H), (8, 8, 8))
    d = ImageDraw.Draw(im)
    centered(d, 580, "Fin.", font("PlayfairDisplaySC-Italic.ttf", 110), CREAM)
    im.save(path)


def art_super_card(path, text):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fnt = font("PlayfairDisplaySC-Italic.ttf", 50)
    tw = d.textlength(text, font=fnt)
    d.rectangle([W / 2 - tw / 2 - 40, H - 200, W / 2 + tw / 2 + 40, H - 110], fill=(0, 0, 0, 150))
    d.text((W / 2, H - 140), text, font=fnt, fill=CREAM + (255,), anchor="ms")
    im.save(path)


def super_card(path, text):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fnt = font("PlayfairDisplaySC-Italic.ttf", 72)
    y = H - 170
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    tw = sd.textlength(text, font=fnt)
    sd.rectangle([W / 2 - tw / 2 - 60, y - 80, W / 2 + tw / 2 + 60, y + 50], fill=(10, 4, 4, 150))
    sd.text((W / 2 + 3, y + 4), text, font=fnt, fill=(0, 0, 0, 230), anchor="ms")
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    im.alpha_composite(shadow)
    d = ImageDraw.Draw(im)
    d.text((W / 2, y), text, font=fnt, fill=CREAM + (255,), anchor="ms")
    tw = d.textlength(text, font=fnt)
    d.line([(W / 2 - tw / 2, y + 26), (W / 2 + tw / 2, y + 26)], fill=GOLD + (230,), width=2)
    im.save(path)


DUST_FRAMES = 48


def dust_frames(folder, n=DUST_FRAMES, seed=7):
    """Transparent overlays with specks, hairs and the odd vertical scratch."""
    rnd = random.Random(seed)
    scratch_x = rnd.uniform(0.2, 0.8) * W
    for i in range(n):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for _ in range(rnd.choice((0, 1, 2, 3, 5))):
            x, y, s = rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(1.5, 5)
            c = (20, 14, 10, rnd.randint(140, 230)) if rnd.random() < 0.7 else (255, 248, 230, rnd.randint(110, 190))
            d.ellipse([x - s, y - s * rnd.uniform(0.6, 1.4), x + s, y + s], fill=c)
        if rnd.random() < 0.12:   # a hair
            x, y = rnd.uniform(0, W), rnd.uniform(0, H)
            pts = [(x, y)]
            for _ in range(6):
                x += rnd.uniform(-14, 14)
                y += rnd.uniform(4, 16)
                pts.append((x, y))
            d.line(pts, fill=(15, 10, 8, 170), width=2)
        if rnd.random() < 0.35:   # a scratch that drifts slowly across frames
            scratch_x = min(max(scratch_x + rnd.uniform(-30, 30), 40), W - 40)
            d.line([(scratch_x, 0), (scratch_x + rnd.uniform(-6, 6), H)], fill=(255, 250, 235, rnd.randint(60, 120)), width=1)
        im = im.filter(ImageFilter.GaussianBlur(0.6))
        im.save(os.path.join(folder, f"dust_{i:03d}.png"))


def run(cmd):
    print("+", " ".join(cmd[:6]), "...", flush=True)
    subprocess.run(cmd, check=True)


def duration(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path])
    return float(out)


def main():
    args = sys.argv[1:]
    art = "--art" in args
    args = [a for a in args if a != "--art"]
    src = args[0]
    default = "road_artfilm.mp4" if art else "road_oldhollywood.mp4"
    dst = args[1] if len(args) > 1 else os.path.join(OUT, default)
    tmp = tempfile.mkdtemp(prefix="oldhw_")
    trf = os.path.join(tmp, "tf.trf")
    supers = ART_SUPERS if art else SUPERS

    (art_title_card if art else title_card)(os.path.join(tmp, "title.png"))
    (art_end_card if art else end_card)(os.path.join(tmp, "end.png"))
    for i, (_, _, text) in enumerate(supers):
        (art_super_card if art else super_card)(os.path.join(tmp, f"super{i}.png"), text)
    dust_frames(tmp)

    # 1. Stabilize, crop to Academy ratio and grade
    grade = (
        f"vidstabtransform=input={trf}:smoothing=30:optalgo=gauss:optzoom=1:zoom=2:maxangle=0.05:interpol=bicubic,"
        f"crop=ih*{W}/{H}:ih,scale={W}:{H}:flags=lanczos,"
        f"{ART_GRADE if art else AD_GRADE},format=yuv420p"
    )
    foot = os.environ.get("OLDHW_FOOT")      # reuse already-graded footage when re-cutting
    if not foot:
        foot = os.path.join(tmp, "foot.mp4")
        run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", f"vidstabdetect=shakiness=8:accuracy=15:stepsize=6:result={trf}",
             "-f", "null", "-"])
        run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", grade, "-r", str(FPS), "-an",
             "-c:v", "libx264", "-preset", "fast", "-crf", "12", foot])

    # Phone clips can carry broken AAC packets; decode once to clean PCM
    wav = os.path.join(tmp, "audio.wav")
    run(["ffmpeg", "-v", "error", "-y", "-err_detect", "ignore_err", "-i", src, "-vn",
         "-af", "aresample=async=1:first_pts=0", "-ar", "48000", "-c:a", "pcm_s16le", wav])

    # 2. Cut together with cards, supers and transitions, then add the film wear
    flen = duration(foot)
    supers = [sp for sp in supers if sp[1] < flen - 3]   # drop lines past the end of a short clip
    start = TITLE_LEN - XF_IN                 # footage begins here in the timeline
    total = start + flen - XF_OUT + END_LEN
    inputs = ["-loop", "1", "-framerate", str(FPS), "-t", str(TITLE_LEN), "-i", os.path.join(tmp, "title.png"),
              "-i", foot,
              "-loop", "1", "-framerate", str(FPS), "-t", str(END_LEN), "-i", os.path.join(tmp, "end.png")]
    for i in range(len(supers)):
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{total:.3f}", "-i", os.path.join(tmp, f"super{i}.png")]
    loops = int(total * FPS / DUST_FRAMES) + 1
    inputs += ["-stream_loop", str(loops), "-framerate", str(FPS), "-i", os.path.join(tmp, "dust_%03d.png")]
    dust_in = 3 + len(supers)

    fc = [
        "[0:v]fps=24,settb=1/24,format=yuv420p,setsar=1[t]",
        "[1:v]fps=24,settb=1/24,format=yuv420p,setsar=1[f]",
        "[2:v]fps=24,settb=1/24,format=yuv420p,setsar=1[e]",
        f"[t][f]xfade=transition=fade:duration={XF_IN}:offset={start:.3f}[tf]",
        f"[tf][e]xfade=transition={'fadeblack' if art else 'circleclose'}:duration={XF_OUT}:offset={start + flen - XF_OUT:.3f}[v0]",
    ]
    last = "v0"
    for i, (a, b, _) in enumerate(supers):
        a, b = start + a, start + b
        fc.append(f"[{3 + i}:v]format=rgba,fade=t=in:st={a}:d=0.8:alpha=1,fade=t=out:st={b - 0.8}:d=0.8:alpha=1[s{i}]")
        fc.append(f"[{last}][s{i}]overlay=enable='between(t,{a},{b})'[v{i + 1}]")
        last = f"v{i + 1}"
    fc += [
        f"[{dust_in}:v]format=rgba[dust]",
        f"[{last}][dust]overlay=shortest=0[vd]",
        # halation: a warm glow bleeding around the highlights
        "[vd]format=gbrp,split[a][b]",
        "[b]gblur=sigma=14" + ("" if art else ",colorchannelmixer=rr=1.0:gg=0.55:bb=0.35") + "[glow]",
        f"[a][glow]blend=all_mode=screen:all_opacity={0.15 if art else 0.22},"
        f"noise=alls={10 if art else 14}:allf=t+u,"
        "eq=brightness='0.018*sin(t*41)+0.012*sin(t*97+1.3)':eval=frame,"
        f"vignette=angle=PI/4,fade=t=in:st=0:d=0.8,fade=t=out:st={total - 1.2:.3f}:d=1.2,"
        "pad=1920:1080:(ow-iw)/2:0:black,format=yuv420p[vout]",
    ]
    picture = os.path.join(tmp, "picture.mp4")
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[vout]",
         "-r", str(FPS), "-frames:v", str(int(round(total * FPS))),
         "-c:v", "libx264", "-preset", "medium", "-crf", "24", picture])

    # sound: the road ambience thinned out like an optical track, plus a little crackle
    afc = [
        # the delay goes before atempo: atempo followed by adelay breaks the timestamps
        f"[0:a]adelay={int(start * 1000 / (ART_SLOW if art else 1))}:all=1,"
        f"{f'atempo={1 / ART_SLOW:.4f},lowpass=f=1800,volume=0.9' if art else 'highpass=f=280,lowpass=f=3800,volume=0.7'},apad[road]",
        f"anoisesrc=color=pink:amplitude=0.02:sample_rate=48000:duration={total + 1:.3f},highpass=f=900,lowpass=f=6000[crackle]",
        f"[road][crackle]amix=inputs=2:normalize=0:duration=shortest,afade=t=in:d=0.8,afade=t=out:st={total - 1.5:.3f}:d=1.5,"
        f"atrim=duration={total:.3f},pan=mono|c0=c0[aout]",
    ]
    sound = os.path.join(tmp, "sound.m4a")
    run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-filter_complex", ";".join(afc), "-map", "[aout]",
         "-c:a", "aac", "-b:a", "128k", sound])

    run(["ffmpeg", "-v", "error", "-y", "-i", picture, "-i", sound, "-map", "0:v", "-map", "1:a",
         "-c", "copy", "-shortest", "-movflags", "+faststart", dst])
    print("wrote", dst)


if __name__ == "__main__":
    main()
