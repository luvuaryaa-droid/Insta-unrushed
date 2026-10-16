#!/usr/bin/env python3
"""Artist Date cinematic treatment: stabilize, 16:9 full frame, signature grade.

Usage:
    python3 make_cinematic.py INPUT.mp4 [OUTPUT.mp4] [--mode auto|tripod|smooth] [--smoothing 90] [--no-grain]

Steps:
    1. Detect shot cuts so each shot is stabilized on its own.
    2. Two-pass vidstab per shot. Auto mode tries a full tripod lock and strong
       smoothing, measures what shake is left, and keeps the steadier result.
    3. Fill a 1920x1080 frame (no letterbox bars), cropping centre if the
       source is not 16:9.
    4. Signature grade: softened highlights, lifted shadows, warm highlights,
       cool shadows, slightly reduced saturation, light vignette and grain.
    5. Rejoin the shots and keep the original audio.

Needs ffmpeg built with libvidstab.
"""

import argparse
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile

WIDTH, HEIGHT = 1920, 1080
SCENE_THRESHOLD = 0.3

GRADE = (
    "eq=contrast=1.03:saturation=0.84,"
    "curves=all='0/0.06 0.25/0.27 0.6/0.61 0.85/0.81 1/0.93',"
    "colorbalance=rs=-0.03:bs=0.04:rm=0.03:bm=-0.02:rh=0.06:gh=0.02:bh=-0.05,"
    "vignette=PI/7"
)
FILL_16x9 = (
    f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase:flags=lanczos,"
    f"crop={WIDTH}:{HEIGHT}"
)


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        check=True, capture_output=True, text=True,
    ).stdout
    return float(out.strip())


def has_audio(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
         "stream=index", "-of", "csv=p=0", path],
        capture_output=True, text=True,
    ).stdout
    return bool(out.strip())


def detect_cuts(path):
    proc = subprocess.run(
        ["ffmpeg", "-i", path, "-vf", f"select='gt(scene,{SCENE_THRESHOLD})',showinfo",
         "-an", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    cuts = []
    for line in proc.stderr.splitlines():
        if "showinfo" in line and "pts_time:" in line:
            cuts.append(float(line.split("pts_time:")[1].split()[0]))
    return cuts


def stabilize(src, dst, trf, mode, smoothing):
    """Two-pass vidstab. tripod locks to the first frame; smooth follows gentle moves."""
    detect = ":tripod=1" if mode == "tripod" else ""
    run(["ffmpeg", "-y", "-i", src, "-vf",
         f"vidstabdetect=shakiness=8:accuracy=15{detect}:result={trf}", "-f", "null", "-"])
    motion = "tripod=1:relative=0" if mode == "tripod" else f"smoothing={smoothing}"
    run(["ffmpeg", "-y", "-i", src, "-vf",
         f"vidstabtransform=input={trf}:{motion}:optzoom=1:interpol=bicubic",
         "-c:v", "ffv1", dst])


def residual_shake(path, trf):
    """Average frame-to-frame camera movement (px) left in a clip, edges of the shot ignored."""
    run(["ffmpeg", "-y", "-i", path, "-vf",
         f"vidstabdetect=shakiness=6:accuracy=15:result={trf}", "-f", "null", "-"])
    moves = []
    with open(trf) as f:
        for line in f:
            if not line.startswith("Frame"):
                continue
            vectors = re.findall(r"LM (-?\d+) (-?\d+) ", line)
            if vectors:
                moves.append(abs(statistics.median(int(x) for x, _ in vectors))
                             + abs(statistics.median(int(y) for _, y in vectors)))
    core = moves[3:-3] or moves
    return statistics.mean(core) if core else 0.0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("output", nargs="?")
    ap.add_argument("--smoothing", type=int, default=90,
                    help="frames of camera smoothing (higher = steadier, more crop on shaky clips)")
    ap.add_argument("--mode", choices=["auto", "tripod", "smooth"], default="auto",
                    help="tripod locks each shot to its first frame (static shots only); smooth "
                         "keeps gentle camera moves; auto tries both per shot and keeps the steadier")
    ap.add_argument("--no-grain", action="store_true")
    args = ap.parse_args()

    src = os.path.abspath(args.input)
    out = os.path.abspath(args.output or os.path.join(
        "output", os.path.splitext(os.path.basename(src))[0] + "_cinematic.mp4"))
    os.makedirs(os.path.dirname(out), exist_ok=True)

    duration = probe_duration(src)
    bounds = [0.0] + [c for c in detect_cuts(src) if 0.2 < c < duration - 0.2] + [duration]
    print(f"{len(bounds) - 1} shot(s): " + ", ".join(f"{a:.2f}-{b:.2f}s" for a, b in zip(bounds, bounds[1:])))

    grain = "" if args.no_grain else ",noise=alls=5:allf=t"
    work = tempfile.mkdtemp(prefix="cinematic_")
    try:
        parts = []
        for i, (start, end) in enumerate(zip(bounds, bounds[1:])):
            raw = os.path.join(work, f"s{i}.mkv")
            done = os.path.join(work, f"s{i}_done.mkv")
            run(["ffmpeg", "-y", "-ss", f"{start:.4f}", "-i", src, "-t", f"{end - start:.4f}",
                 "-an", "-c:v", "ffv1", raw])
            results = []
            for mode in (["tripod", "smooth"] if args.mode == "auto" else [args.mode]):
                stab = os.path.join(work, f"s{i}_{mode}.mkv")
                stabilize(raw, stab, os.path.join(work, f"s{i}_{mode}.trf"), mode, args.smoothing)
                results.append((residual_shake(stab, os.path.join(work, f"s{i}_{mode}_check.trf")), mode, stab))
            shake, mode, stab = min(results)
            vf = f"unsharp=5:5:0.6:3:3:0.3,{FILL_16x9},{GRADE}{grain},format=yuv420p"
            run(["ffmpeg", "-y", "-i", stab, "-vf", vf, "-c:v", "ffv1", done])
            parts.append(done)
            print(f"  shot {i + 1}: {mode} stabilization, residual shake {shake:.2f} px/frame")

        listfile = os.path.join(work, "list.txt")
        with open(listfile, "w") as f:
            f.writelines(f"file '{p}'\n" for p in parts)
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile]
        if has_audio(src):
            cmd += ["-i", src, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "160k", "-shortest"]
        cmd += ["-c:v", "libx264", "-crf", "21", "-preset", "slow", "-movflags", "+faststart", out]
        run(cmd)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    print(f"Saved {out}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        sys.exit(f"ffmpeg failed: {' '.join(e.cmd[:6])} ...")
