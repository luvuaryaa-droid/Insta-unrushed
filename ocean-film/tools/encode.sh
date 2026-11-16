#!/usr/bin/env bash
# Final encode: ProRes master from Remotion -> H.264 1080p24, original MP3 audio stream copied bit-for-bit.
set -euo pipefail
cd "$(dirname "$0")/.."
ffmpeg -y -i out/master_raw.mov -i public/ocean.mp3 -map 0:v:0 -map 1:a:0 \
  -c:v libx264 -preset slow -crf "${CRF:-19}" -maxrate 24M -bufsize 48M -tune grain -profile:v high -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a copy -movflags +faststart out/I_Am_an_Ocean_1080p.mp4
