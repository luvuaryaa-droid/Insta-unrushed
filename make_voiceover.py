#!/usr/bin/env python3
"""Voice-over versions of the three Creator Studio ads.

Each line is spoken when its scene starts. Lines come from Kokoro (local neural TTS), are
time-stretched (pitch kept) if they would run into the next scene, and are muxed with the
untouched video stream from output/ads/.

    pip install kokoro-onnx soundfile
    # put kokoro-v1.0.onnx and voices-v1.0.bin (kokoro-onnx GitHub release model-files-v1.0) in models/
    python3 make_voiceover.py              # all three -> output/ads/*_voiceover.mp4
    python3 make_voiceover.py creators     # one ad
"""
import os
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = os.path.dirname(os.path.abspath(__file__))
ADS = os.path.join(ROOT, "output", "ads")
MODELS = os.path.join(ROOT, "models")
SR = 24000
LEAD = 0.15   # start each line just after its scene lands
GAP = 0.12    # silence kept before the next line

# ad: (video, voice, [(start s, line, speed)]). Starts match the scene times in make_ads.py.
SCRIPTS = {
    "artists": ("ad_artists_you_paint.mp4", "af_heart", [
        (0.2, "You paint.", 0.9),
        (3.0, "Then comes the reel. Clips, captions, hashtags... not anymore.", 1.1),
        (6.5, "Just drop your art in, and tell Claude what you want.", 1.0),
        (9.5, "Claude writes the story, letters the captions, and animates every page.", 1.05),
        (14.0, "Pick papercut stop-motion, or a three-D flip-book.", 1.0),
        (17.5, "It even paints with colours pulled from your art.", 1.0),
        (21.0, "Want a voice-over? Pick a voice, and it reads your captions.", 1.05),
        (24.5, "You get the cover, the caption, and the hashtags too.", 1.0),
        (28.0, "Want changes? Just ask, and preview before the final render.", 1.05),
        (32.2, "You paint. Claude handles the reels. Creator Studio.", 1.0),
        (34.7, "Lifetime access, just six ninety-nine rupees.", 1.0),
        (37.4, "Install once. Create forever.", 0.95),
    ]),
    "creators": ("ad_ugc_creators.mp4", "am_michael", [
        (0.1, "Three hours of footage... for thirty seconds?", 1.1),
        (3.0, "Skip the timeline. Just tell Claude what you need.", 1.1),
        (6.0, "Three versions. Three hooks. One upload. Test what actually lands.", 1.1),
        (10.5, "Papercut, or flip-book, even over your own clips.", 1.1),
        (14.0, "No mic? No retakes. Pick a voice. Done.", 1.05),
        (17.5, "Story, captions, colours: done. You stay on camera.", 1.15),
        (21.0, "Cover, caption, and hashtags. Ready to post.", 1.05),
        (24.5, "Notes? Just type them. Preview, then render.", 1.05),
        (28.7, "Film it. Claude ships it. Creator Studio.", 1.0),
        (31.2, "Lifetime access, just six ninety-nine rupees.", 1.0),
        (33.9, "Install once. Create forever.", 0.95),
    ]),
    "beginners": ("ad_beginners.mp4", "af_bella", [
        (0.1, "Never edited a video? Good. You don't need to.", 1.05),
        (3.0, "Step one: add your photos. Phone pics are fine.", 1.0),
        (6.5, "Step two: describe the vibe, in your own words.", 1.0),
        (10.0, "Step three: post it. Claude does all the pro stuff.", 1.0),
        (14.0, "Pick a look. Papercut, or three-D flip-book.", 1.0),
        (17.5, "Want a voice? Pick one, and it reads your captions.", 1.0),
        (21.0, "Plus the bits you'd forget: cover, caption, hashtags.", 1.0),
        (24.5, "Not quite right? Just say so.", 0.95),
        (28.0, "Skip the evening of tutorials. It takes a few minutes.", 1.0),
        (32.2, "Pro-looking reels. Zero editing skills.", 1.0),
        (34.7, "Lifetime access, just six ninety-nine rupees.", 1.0),
        (37.4, "Install once. Create forever.", 0.95),
    ]),
}


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
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a, "-af", f"atempo={dur / max_len:.4f}", b],
                   check=True)
    return sf.read(b, dtype="float32")[0]


def voice_over(tts, name):
    video, voice, script = SCRIPTS[name]
    src = os.path.join(ADS, video)
    out = src.replace(".mp4", "_voiceover.mp4")
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", src]))
    track = np.zeros(int(total * SR) + SR, dtype=np.float32)
    with tempfile.TemporaryDirectory() as tmp:
        for i, (start, text, speed) in enumerate(script):
            end = script[i + 1][0] if i + 1 < len(script) else total
            x, _ = tts.create(text, voice=voice, speed=speed, lang="en-us")
            x = fit(trim(x), end - start - LEAD - GAP, tmp)
            fade = int(0.01 * SR)
            x[-fade:] *= np.linspace(1, 0, fade)
            s = int((start + LEAD) * SR)
            track[s:s + len(x)] += x
            print(f"  {start:5.2f}s  {len(x) / SR:.2f}s of {end - start:.2f}s  {text}")
        track = track[:int(total * SR)]
        track *= 0.89 / max(1e-6, np.abs(track).max())
        wav = os.path.join(tmp, "vo.wav")
        sf.write(wav, track, SR)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-i", wav, "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest",
                        "-movflags", "+faststart", out], check=True)
    print("wrote", out)


def main():
    tts = Kokoro(os.path.join(MODELS, "kokoro-v1.0.onnx"), os.path.join(MODELS, "voices-v1.0.bin"))
    for name in [a for a in sys.argv[1:] if a in SCRIPTS] or list(SCRIPTS):
        print(name)
        voice_over(tts, name)


if __name__ == "__main__":
    main()
