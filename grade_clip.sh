#!/usr/bin/env bash
# Nostalgic / diffused / cinematic grade with stabilisation.
# Usage: ./grade_clip.sh input.mp4 output.mp4
set -euo pipefail
IN="$1"; OUT="$2"
TRF="$(mktemp --suffix=.trf)"
trap 'rm -f "$TRF"' EXIT

# Pass 1: measure camera shake.
ffmpeg -v error -y -i "$IN" -vf "vidstabdetect=shakiness=8:accuracy=15:result=$TRF" -f null -

# Pass 2: stabilise (heavy smoothing), soft bloom, warm faded film grade,
# vignette, grain, 2.39:1 letterbox bars.
FC="[0:v]vidstabtransform=input=$TRF:smoothing=45:optzoom=1:zoomspeed=0.2:interpol=bicubic,unsharp=5:5:0.3,
format=gbrp,split[a][b];
[b]gblur=sigma=20,curves=all='0/0 0.55/0.7 1/1'[glow];
[a][glow]blend=all_mode=screen:all_opacity=0.30,
curves=r='0/0.06 0.5/0.53 1/0.98':g='0/0.05 0.5/0.51 1/0.96':b='0/0.09 0.5/0.48 1/0.90',
eq=saturation=0.88:contrast=1.06:gamma=1.04,
colorbalance=rs=0.03:bs=0.04:rh=0.05:bh=-0.04,
vignette=angle=PI/5:mode=forward,
noise=alls=8:allf=t,
drawbox=x=0:y=0:w=iw:h=ih*0.128:color=black:t=fill,drawbox=x=0:y=ih-ih*0.128:w=iw:h=ih*0.128:color=black:t=fill,
format=yuv420p[v]"

ffmpeg -v error -y -i "$IN" -filter_complex "$FC" -map "[v]" -map 0:a? \
  -c:v libx264 -crf 19 -preset slow -c:a aac -b:a 192k -movflags +faststart "$OUT"
