#!/usr/bin/env bash
# Nostalgic / diffused / cinematic grade with stabilisation.
#
# Usage: ./grade_clip.sh [options] input.mp4 output.mp4
#   --warm          stronger warm (golden) colour temperature
#   --vintage       vintage warm: amber cast, faded blacks, muted colour, more grain
#   --clean         grain-free soft film: denoised, peach highlights, teal-ish
#                   shadows, stronger glow (overrides --warm / --vintage)
#   --hollywood     grain-free blockbuster teal & orange: deeper contrast, teal
#                   shadows, orange highlights, soft glow (overrides the above)
#   --width W       scale output to W pixels wide (e.g. 1080)
#   --no-bars       skip the 2.39:1 letterbox bars
#   --views "T..."  keep only --len seconds starting at each time T (one per
#                   view/shot); T:L keeps L seconds for that view instead. Each
#                   piece is stabilised on its own, then joined
#   --len N         seconds kept per view (default 4)
set -euo pipefail

WARM=0; VINTAGE=0; CLEAN=0; HOLLY=0; WIDTH=""; BARS=1; VIEWS=""; LEN=4
while [[ $# -gt 2 ]]; do
  case "$1" in
    --warm) WARM=1; shift ;;
    --vintage) VINTAGE=1; shift ;;
    --clean) CLEAN=1; shift ;;
    --hollywood) HOLLY=1; shift ;;
    --width) WIDTH="$2"; shift 2 ;;
    --no-bars) BARS=0; shift ;;
    --views) VIEWS="$2"; shift 2 ;;
    --len) LEN="$2"; shift 2 ;;
    *) echo "unknown option $1" >&2; exit 1 ;;
  esac
done
IN="$1"; OUT="$2"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

SAT=0.88; GRAIN=8; GLOW=0.30; PRE=""; CONTRAST=1.06; SEL=""
if [[ $HOLLY == 1 ]]; then
  CURVES="r='0/0.02 0.25/0.21 0.5/0.52 0.75/0.81 1/1':g='0/0.04 0.25/0.24 0.5/0.50 0.75/0.77 1/0.97':b='0/0.12 0.25/0.31 0.5/0.50 0.75/0.74 1/0.94'"
  BALANCE="rs=-0.11:gs=0.01:bs=0.10:rm=-0.02:bm=0.02:rh=0.07:gh=0.01:bh=-0.05"
  SAT=1.0; GLOW=0.30; PRE="hqdn3d=3:2:4:3,"; GRAIN=0; CONTRAST=1.10
  # Greens and shadows lean teal, yellows lean orange.
  SEL="selectivecolor=greens='0.30 0 -0.25 0':yellows='-0.10 0.12 0 0':blacks='0.12 0 -0.08 0',"
elif [[ $CLEAN == 1 ]]; then
  CURVES="r='0/0.05 0.25/0.26 0.5/0.53 0.8/0.84 1/0.98':g='0/0.06 0.5/0.51 1/0.95':b='0/0.10 0.25/0.27 0.5/0.48 1/0.88'"
  BALANCE="rs=-0.02:gs=0.01:bs=0.04:rh=0.06:gh=0.02:bh=-0.04"
  SAT=0.90; GLOW=0.38; PRE="hqdn3d=3:2:4:3,"; GRAIN=0
elif [[ $VINTAGE == 1 ]]; then
  CURVES="r='0/0.10 0.5/0.57 1/0.97':g='0/0.08 0.5/0.52 1/0.93':b='0/0.07 0.5/0.42 1/0.78'"
  BALANCE="rs=0.05:gs=0.02:bs=-0.04:rm=0.05:gm=0.01:bm=-0.06:rh=0.06:gh=0.03:bh=-0.08"
  SAT=0.78; GRAIN=11
elif [[ $WARM == 1 ]]; then
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
  local fc="[0:v]vidstabtransform=input=$trf:smoothing=45:optzoom=1:zoomspeed=0.2:interpol=bicubic,${PRE}unsharp=5:5:0.3,
format=gbrp,split[a][b];
[b]gblur=sigma=20,curves=all='0/0 0.55/0.7 1/1'[glow];
[a][glow]blend=all_mode=screen:all_opacity=$GLOW,
curves=$CURVES,
eq=saturation=$SAT:contrast=$CONTRAST:gamma=1.04,
colorbalance=$BALANCE,
$SEL
vignette=angle=PI/5:mode=forward,
$( ((GRAIN)) && echo "noise=alls=$GRAIN:allf=t," )
$BOXES
${WIDTH:+scale=$WIDTH:-2:flags=lanczos,}format=yuv420p[v]"
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
for v in $VIEWS; do
  t="${v%%:*}"; len="$LEN"
  [[ $v == *:* ]] && len="${v#*:}"
  piece="$TMP/view$i.mp4"
  ffmpeg -v error -y -ss "$t" -t "$len" -i "$IN" \
    -af "afade=t=in:d=0.08,afade=t=out:st=$(echo "$len - 0.08" | bc):d=0.08" \
    -c:v libx264 -crf 12 -preset fast -c:a pcm_s16le "$TMP/cut$i.mkv"
  grade "$TMP/cut$i.mkv" "$piece"
  echo "file '$piece'" >> "$TMP/list.txt"
  i=$((i + 1))
done
# Re-encode the join with a bitrate cap: film grain otherwise bloats the file.
ffmpeg -v error -y -f concat -safe 0 -i "$TMP/list.txt" \
  -c:v libx264 -crf 20 -maxrate 12M -bufsize 24M -preset slow -c:a copy -movflags +faststart "$OUT"
