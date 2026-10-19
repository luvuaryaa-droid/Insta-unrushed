#!/usr/bin/env python3
"""Cinematic nature reel from footage/VID_20261014_232420.mp4.

    python3 make_reel.py                         # 4:5 feed -> output/final.mp4
    python3 make_reel.py --aspect 9:16           # Reels    -> output/final_9x16.mp4
    python3 make_reel.py --aspect 5:4            # 1280x1024 -> output/final_5x4.mp4
    python3 make_reel.py --lut my.cube --title "slow days" --handle @me --logo logo.png

Pipeline:
  1. every shot is cut at source resolution, conformed to 30 fps (slow-motion
     shots are motion-interpolated to 60 fps then played at half speed),
     graded (optional user LUT first, then the teal-orange LUT from grade.py),
  2. the flash-cut burst is built from 0.15 s slices of one shot,
  3. the timeline is centre-cropped to the target aspect, upscaled, sharpened,
     and wrapped in a 2 s black title card, a 1.5 s fade to
     black and a 2 s end card.

Needs ffmpeg, Pillow and numpy.
"""

import argparse
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import grade

ROOT = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(ROOT, "fonts")
SRC = os.path.join(ROOT, "footage", "VID_20261014_232420.mp4")
SRC_FPS = 24
FPS = 30

# (name, first frame, end frame) at 24 fps, from scene detection on the source
SHOTS = [
    ("swan", 0, 336),
    ("duck", 336, 732),
    ("pond", 732, 902),
    ("white_flowers", 902, 1069),
    ("purple_flower_1", 1069, 1204),
    ("purple_flower_2", 1204, 1338),
    ("orange_flower", 1338, 1487),
    ("tree_tunnel", 1487, 1658),
    ("feet", 1658, 1779),
    ("clouds", 1779, 1910),
    ("railing", 1910, 2067),
    ("street", 2067, 2230),
]

SIZES = {"4:5": (1080, 1350), "5:4": (1280, 1024), "9:16": (1080, 1920)}

TITLE_DUR = 2.0
FADE_DUR = 1.5
END_DUR = 2.0


def run(cmd):
    subprocess.run(cmd, check=True)


def ffmpeg(*args):
    run(["ffmpeg", "-v", "error", "-y", *args])


# --------------------------------------------------------------------------- cards

def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def subtitle_layer(lines, size, max_w):
    """White Permanent Marker text with a soft drop shadow (the flip-book caption style)."""
    while max(font("PermanentMarker-Regular.ttf", size).getlength(l) for l in lines) > max_w:
        size -= 4
    f = font("PermanentMarker-Regular.ttf", size)
    lh = int(size * 1.08)
    tw = int(max(f.getlength(l) for l in lines)) + 80
    th = lh * len(lines) + 70
    layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i, l in enumerate(lines):
        d.text(((tw - f.getlength(l)) / 2, 30 + i * lh), l, font=f, fill=(255, 255, 255, 255))
    shadow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    shadow.putalpha(layer.getchannel("A").point(lambda v: int(v * 0.55)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    img = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    img.alpha_composite(shadow, (0, 6))
    img.alpha_composite(layer)
    return img


def title_card(path, size, text):
    w, h = size
    card = Image.new("RGBA", size, (0, 0, 0, 255))
    t = subtitle_layer(text.split("\n"), int(w * 0.085), w * 0.84)
    card.alpha_composite(t, ((w - t.width) // 2, (h - t.height) // 2))
    card.convert("RGB").save(path)


def default_logo(d):
    """A simple wordmark-style badge used when no --logo image is given."""
    img = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    dr.ellipse((4, 4, d - 4, d - 4), outline=(240, 226, 205, 255), width=max(3, d // 40))
    f = font("Caveat.ttf", int(d * 0.62))
    f.set_variation_by_name("Bold")
    l, t, r, b = dr.textbbox((0, 0), "u", font=f)
    dr.text(((d - (r - l)) / 2 - l, (d - (b - t)) / 2 - t), "u", font=f, fill=(240, 226, 205, 255))
    return img


def end_card(path, size, logo_path, handle):
    w, h = size
    card = Image.new("RGBA", size, (0, 0, 0, 255))
    d = int(min(w, h) * 0.30)
    if logo_path:
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail((d, d), Image.LANCZOS)
    else:
        logo = default_logo(d)
    parts = [logo]
    if handle:
        parts.append(subtitle_layer([handle], int(w * 0.06), w * 0.84))
    gap = int(h * 0.02)
    total = sum(p.height for p in parts) + gap * (len(parts) - 1)
    y = (h - total) // 2
    for p in parts:
        card.alpha_composite(p, ((w - p.width) // 2, y))
        y += p.height + gap
    card.convert("RGB").save(path)


# --------------------------------------------------------------------------- shots

def grade_chain(user_lut, our_lut):
    chain = [f"lut3d=file='{user_lut}'"] if user_lut else []
    return chain + [f"lut3d=file='{our_lut}'"]


def cut(out, a, b, slow, grade_filters):
    """Frames [a, b) of the source -> 30 fps graded clip with audio (lossless intermediate)."""
    v = [f"trim=start_frame={a}:end_frame={b}", "setpts=PTS-STARTPTS"]
    au = [f"atrim=start={a / SRC_FPS}:end={b / SRC_FPS}", "asetpts=PTS-STARTPTS"]
    if slow:
        v += ["minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
              "setpts=2*PTS", f"fps={FPS}"]
        au += ["atempo=0.5"]
    else:
        v += [f"fps={FPS}"]
    v += grade_filters + ["format=yuv444p"]
    dur = (b - a) / SRC_FPS * (2 if slow else 1)
    au += [f"afade=t=in:d=0.04", f"afade=t=out:st={dur - 0.04:.3f}:d=0.04"]
    ffmpeg("-i", SRC, "-filter_complex",
           f"[0:v]{','.join(v)}[v];[0:a]{','.join(au)}[a]",
           "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}",
           "-c:v", "libx264", "-qp", "0", "-preset", "ultrafast",
           "-c:a", "pcm_s16le", "-ar", "48000", out)
    return dur


def burst(out, clip, clip_dur, pieces):
    """Flash-cut burst: `pieces` slices (~0.15 s each) spread across `clip`,
    each opening on a one-frame white flash."""
    frames = [4 if i % 2 == 0 else 5 for i in range(pieces)]  # 4/5 frames at 30 fps ~ 0.15 s
    starts = [(clip_dur - 0.2) * i / (pieces - 1) for i in range(pieces)]
    starts = starts[::-1][: pieces // 2] + starts[: pieces - pieces // 2]  # jump around the clip
    vf, af, labels = [], [], ""
    for i, (s, n) in enumerate(zip(starts, frames)):
        d = n / FPS
        vf.append(f"[0:v]trim=start={s:.3f}:duration={d:.4f},setpts=PTS-STARTPTS,"
                  f"fade=t=in:st=0:d={1.5 / FPS:.4f}:color=white[v{i}]")
        af.append(f"[0:a]atrim=start={s:.3f}:duration={d:.4f},asetpts=PTS-STARTPTS,"
                  f"afade=t=in:d=0.01,afade=t=out:st={d - 0.01:.4f}:d=0.01[a{i}]")
        labels += f"[v{i}][a{i}]"
    graph = ";".join(vf + af) + f";{labels}concat=n={pieces}:v=1:a=1[v][a]"
    ffmpeg("-i", clip, "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-qp", "0", "-preset", "ultrafast",
           "-c:a", "pcm_s16le", "-ar", "48000", out)
    return sum(frames) / FPS


def build_timeline(work, args):
    lut = os.path.join(work, "teal_orange.cube")
    grade.write_cube(lut)
    gf = grade_chain(args.lut, lut)
    parts = []
    for name, a, b in SHOTS:
        clip = os.path.join(work, f"{name}.mkv")
        print(f"  {name}{' (slow-mo)' if name in args.slow else ''}")
        dur = cut(clip, a, b, name in args.slow, gf)
        if name == args.burst:
            bclip = os.path.join(work, f"{name}_burst.mkv")
            burst(bclip, clip, dur, args.burst_pieces)
            parts.append(bclip)
        parts.append(clip)
    listing = os.path.join(work, "parts.txt")
    with open(listing, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    timeline = os.path.join(work, "timeline.mkv")
    ffmpeg("-f", "concat", "-safe", "0", "-i", listing, "-c", "copy", timeline)
    return timeline


# --------------------------------------------------------------------------- final

def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(out.stdout)


def render(timeline, work, args, out):
    w, h = SIZES[args.aspect]
    title_png = os.path.join(work, f"title_{w}x{h}.png")
    end_png = os.path.join(work, f"end_{w}x{h}.png")
    title_card(title_png, (w, h), args.title)
    end_card(end_png, (w, h), args.logo, args.handle)
    tl = duration(timeline)
    fo = tl - FADE_DUR
    graph = ";".join([
        f"[0:v]loop=loop=-1:size=1:start=0,trim=duration={TITLE_DUR},fps={FPS},setpts=PTS-STARTPTS,"
        f"fade=t=in:d=0.4,fade=t=out:st={TITLE_DUR - 0.4}:d=0.4,format=yuv420p,setsar=1[t]",
        # centre crop to the target aspect at source res, then upscale
        f"[1:v]crop='min(iw,ih*{w}/{h})':'min(ih,iw*{h}/{w})',"
        f"scale={w}:{h}:flags=lanczos,unsharp=5:5:0.55,"
        f"fade=t=out:st={fo:.3f}:d={FADE_DUR},format=yuv420p,setsar=1[m]",
        f"[2:v]loop=loop=-1:size=1:start=0,trim=duration={END_DUR},fps={FPS},setpts=PTS-STARTPTS,"
        f"fade=t=in:d=0.5,format=yuv420p,setsar=1[e]",
        f"[1:a]loudnorm=I=-18:TP=-1.5:LRA=11,aresample=48000,"
        f"afade=t=out:st={fo:.3f}:d={FADE_DUR}[ma]",
        f"anullsrc=r=48000:cl=stereo,atrim=duration={TITLE_DUR}[ta]",
        f"anullsrc=r=48000:cl=stereo,atrim=duration={END_DUR}[ea]",
        "[t][ta][m][ma][e][ea]concat=n=3:v=1:a=1[v][a]",
    ])
    ffmpeg("-i", title_png, "-i", timeline, "-i", end_png, "-filter_complex", graph,
           "-map", "[v]", "-map", "[a]", "-r", str(FPS),
           "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-crf", "18",
           "-maxrate", "5M", "-bufsize", "10M",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", out)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--aspect", choices=list(SIZES), default="4:5")
    p.add_argument("--out", help="output file (default output/final.mp4 for 4:5)")
    p.add_argument("--lut", help=".cube LUT applied before the teal-orange grade")
    p.add_argument("--slow", nargs="*", default=["swan", "orange_flower"],
                   help="shots played at 50%% speed (names: %s)" % ", ".join(s[0] for s in SHOTS))
    p.add_argument("--burst", default="feet", help="shot the flash-cut burst is made from")
    p.add_argument("--burst-pieces", type=int, default=5)
    p.add_argument("--title", default="unrushed")
    p.add_argument("--handle", default="", help="e.g. @yourname (shown under the logo)")
    p.add_argument("--logo", help="logo image (PNG with transparency works best)")
    p.add_argument("--keep", help="reuse/keep intermediates in this folder")
    args = p.parse_args()

    names = {s[0] for s in SHOTS}
    for n in args.slow + [args.burst]:
        if n not in names:
            p.error(f"unknown shot {n!r}")
    default_out = "final.mp4" if args.aspect == "4:5" else f"final_{args.aspect.replace(':', 'x')}.mp4"
    out = args.out or os.path.join(ROOT, "output", default_out)

    work = args.keep or tempfile.mkdtemp(prefix="reel_")
    os.makedirs(work, exist_ok=True)
    try:
        timeline = os.path.join(work, "timeline.mkv")
        if not (args.keep and os.path.exists(timeline)):
            print("cutting + grading shots")
            timeline = build_timeline(work, args)
        print(f"rendering {args.aspect} -> {out}")
        render(timeline, work, args, out)
    finally:
        if not args.keep:
            shutil.rmtree(work, ignore_errors=True)
    print("done")


if __name__ == "__main__":
    main()
