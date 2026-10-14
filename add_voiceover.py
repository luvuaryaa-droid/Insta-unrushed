"""Add a spoken voice-over to the "Do it ..." sketchbook reel.

Each caption in the reel is read out as it appears. Lines are synthesised
with Kokoro (local neural TTS), squeezed to fit inside their shot if needed,
and laid onto a silent track that is muxed with the untouched video stream.

    python3 add_voiceover.py IN.mp4 [OUT.mp4] [--models DIR] [--voice af_heart]

DIR must contain kokoro-v1.0.onnx and voices-v1.0.bin from
https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
(pip install kokoro-onnx soundfile; needs ffmpeg).
"""
import argparse
import os
import subprocess
import tempfile

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

SR = 24000

# (shot start in seconds, spoken line, speech speed). Shot starts come from
# scene-cut detection on the source clip; each line must finish before the
# next shot. Speed rises through the "up" moods and the last line is slow.
SCRIPT = [
    (0.00, "Do it sad.", 0.95),
    (0.79, "Do it angry!", 1.15),
    (1.67, "Do it heartbroken.", 1.15),
    (2.58, "Do it miserable.", 1.1),
    (3.46, "Do it excited!", 1.2),
    (4.29, "Do it energized!", 1.2),
    (5.29, "Do it happy!", 1.25),
    (5.96, "Do it tired.", 1.0),
    (6.79, "Do it confident.", 1.15),
    (7.83, "Do it discouraged.", 1.05),
    (9.00, "Do it... anyway.", 0.85),
]
LEAD = 0.04  # start each line just after the cut
GAP = 0.03   # keep this much silence before the next cut


def trim(x, thresh=0.01):
    idx = np.where(np.abs(x) > thresh)[0]
    return x[idx[0]:idx[-1] + 1] if len(idx) else x


def fit(x, max_len, tmp):
    """Time-stretch (pitch-preserving) x down to max_len seconds if longer."""
    dur = len(x) / SR
    if dur <= max_len:
        return x
    a, b = os.path.join(tmp, "in.wav"), os.path.join(tmp, "out.wav")
    sf.write(a, x, SR)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a, "-af",
                    f"atempo={dur / max_len:.4f}", b], check=True)
    return sf.read(b, dtype="float32")[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out", nargs="?", default="output/do_it_anyway_voiceover.mp4")
    ap.add_argument("--models", default="models")
    ap.add_argument("--voice", default="af_heart")
    args = ap.parse_args()

    total = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", args.src]))
    tts = Kokoro(os.path.join(args.models, "kokoro-v1.0.onnx"),
                 os.path.join(args.models, "voices-v1.0.bin"))
    track = np.zeros(int(total * SR) + SR, dtype=np.float32)

    with tempfile.TemporaryDirectory() as tmp:
        for i, (start, text, speed) in enumerate(SCRIPT):
            end = SCRIPT[i + 1][0] if i + 1 < len(SCRIPT) else total
            x, _ = tts.create(text, voice=args.voice, speed=speed, lang="en-us")
            x = fit(trim(x), end - start - LEAD - GAP, tmp)
            fade = int(0.01 * SR)
            x[-fade:] *= np.linspace(1, 0, fade)
            s = int((start + LEAD) * SR)
            track[s:s + len(x)] += x
            print(f"{start:5.2f}s  {len(x) / SR:.2f}s / {end - start:.2f}s  {text}")

        track = track[:int(total * SR)]
        track *= 0.89 / max(1e-6, np.abs(track).max())
        wav = os.path.join(tmp, "vo.wav")
        sf.write(wav, track, SR)
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", args.src, "-i", wav,
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                        "-shortest", "-movflags", "+faststart", args.out],
                       check=True)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
