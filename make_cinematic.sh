#!/bin/sh
# Hollywood-style grade + stabilization for a handheld clip.
# Usage: ./make_cinematic.sh input.mp4 [output.mp4]
set -e
IN="$1"; OUT="${2:-output/road_cinematic.mp4}"
TRF=$(mktemp --suffix=.trf)
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
FO=$(echo "$DUR - 1.5" | bc)

# Pass 1: motion analysis
ffmpeg -y -i "$IN" -vf "vidstabdetect=shakiness=8:accuracy=15:stepsize=6:result=$TRF" -f null -

# Pass 2: stabilize (auto-zoom hides borders), 2.39:1 letterbox, teal/orange grade, vignette, grain
ffmpeg -y -i "$IN" -vf "vidstabtransform=input=$TRF:smoothing=30:optalgo=gauss:optzoom=1:zoom=2:maxangle=0.05:interpol=bicubic,\
crop=iw:iw/2.39,scale=1920:804:flags=lanczos,unsharp=5:5:0.5:5:5:0,\
curves=all='0/0.02 0.25/0.22 0.5/0.52 0.8/0.84 1/0.97',\
colorbalance=rs=-0.08:bs=0.10:rm=0.03:bm=-0.03:rh=0.08:gh=0.02:bh=-0.08,\
eq=saturation=0.92:contrast=1.05:brightness=0.02,\
vignette=angle=PI/5,noise=alls=4:allf=t,\
pad=1920:1080:0:138:black,fade=t=in:st=0:d=1.2,fade=t=out:st=$FO:d=1.5,format=yuv420p" \
  -af "afade=t=in:d=1.2,afade=t=out:st=$FO:d=1.5" \
  -c:v libx264 -preset medium -crf 20 -tune film -c:a aac -b:a 192k -movflags +faststart "$OUT"
rm -f "$TRF"
