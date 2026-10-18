#!/usr/bin/env bash
# Nostalgic / diffused / cinematic grade with stabilisation.
#
# Usage: ./grade_clip.sh [options] input.mp4 output.mp4
#   --warm          stronger warm (golden) colour temperature
#   --no-bars       skip the 2.39:1 letterbox bars
#   --views "T..."  keep only --len seconds starting at each time T (one per
#                   view/shot); each piece is stabilised on its own, then joined
#   --len N         seconds kept per view (default 4)
set -euo pipefail

WARM=0; BARS=1; VIEWS=""; LEN=4
while [[ $# -gt 2 ]]; do
  case "$1" in
    --warm) WARM=1; shift ;;
    --no-bars) BARS=0; shift ;;
    --views) VIEWS="$2"; shift 2 ;;
    --len) LEN="$2"; shift 2 ;;
    *) echo "unknown option $1" >&2; exit 1 ;;
  esac
done
IN="$1"; OUT="$2"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

if [[ $WARM == 1 ]]; then
  CURVES="r='0/0.07 0.5/0.56 1/1':g='0/0.05 0.5/0.51 1/0.96':b='0/0.06 0.5/0.44 1/0.84'"
  BALANCE="rs=0.05:gs=0.01:bs=-0.02:rm=0.04:bm=-0.04:rh=0.07:gh=0.02:bh=-0.07"
else
  CURVES="r='0/0.06 0.5/0.53 1/0.98':g='0/0.05 0.5/0.51 1/0.96':b='0/0.09 0.5/0.48 1/0.90'"
  BALANCE="rs=0.03:bs=0.04:rh=0.05:bh=-0.04"
fi
BOXES=""
if [[ $BARS == 1 ]]; then
  BOXES="drawbox=x=0:y=0:w=iw:h=ih*0.128:color=black:t=fill,drawbox=x=0:y=ih-ih*0.128:w=iw:h=ih*0.128:color=black:t=fill,"
fi

# grade SRC DST [extra input args...]: stabilise and grade one piece.
grade() {
  local src="$1" dst="$2"; shift 2
  local trf="$TMP/$(basename "$dst").trf"
  # Pass 1: measure camera shake.
  ffmpeg -v error -y "$@" -i "$src" -vf "vidstabdetect=shakiness=8:accuracy=15:result=$trf" -f null -
  # Pass 2: stabilise (heavy smoothing), soft bloom, faded film grade,
  # vignette, grain, optional letterbox bars.
  local fc="[0:v]vidstabtransform=input=$trf:smoothing=45:optzoom=1:zoomspeed=0.2:interpol=bicubic,unsharp=5:5:0.3,
format=gbrp,split[a][b];
[b]gblur=sigma=20,curves=all='0/0 0.55/0.7 1/1'[glow];
[a][glow]blend=all_mode=screen:all_opacity=0.30,
curves=$CURVES,
eq=saturation=0.88:contrast=1.06:gamma=1.04,
colorbalance=$BALANCE,
vignette=angle=PI/5:mode=forward,
noise=alls=8:allf=t,
$BOXES
format=yuv420p[v]"
  ffmpeg -v error -y "$@" -i "$src" -filter_complex "$fc" -map "[v]" -map 0:a? \
    -c:v libx264 -crf 19 -preset slow -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$dst"
}

if [[ -z $VIEWS ]]; then
  grade "$IN" "$OUT"
  exit 0
fi

# One piece per view, with short audio fades so the cuts don't click.
: > "$TMP/list.txt"
i=0
for t in $VIEWS; do
  piece="$TMP/view$i.mp4"
  ffmpeg -v error -y -ss "$t" -t "$LEN" -i "$IN" \
    -af "afade=t=in:d=0.08,afade=t=out:st=$(echo "$LEN - 0.08" | bc):d=0.08" \
    -c:v libx264 -crf 12 -preset fast -c:a pcm_s16le "$TMP/cut$i.mkv"
  grade "$TMP/cut$i.mkv" "$piece"
  echo "file '$piece'" >> "$TMP/list.txt"
  i=$((i + 1))
done
# Re-encode the join with a bitrate cap: film grain otherwise bloats the file.
ffmpeg -v error -y -f concat -safe 0 -i "$TMP/list.txt" \
  -c:v libx264 -crf 20 -maxrate 12M -bufsize 24M -preset slow -c:a copy -movflags +faststart "$OUT"
