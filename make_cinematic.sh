#!/usr/bin/env bash
# Hollywood-style cinematic edit of a short clip.
#   ./make_cinematic.sh input.mp4 [output.mp4]
# Optional fixes for handheld footage (environment variables):
#   STABILIZE=1   lock the shot off like a tripod (stabilize.py, needs OpenCV)
#   ROTATE=-5.2   (with STABILIZE) straighten by this many degrees (negative = anticlockwise)
#   KEYSTONE=23   (with STABILIZE) pull the top corners in by this many pixels so verticals
#                 that lean apart towards the top become parallel
#   ZOOM=1.08     starting zoom for the push-in (crops away stabilizer edges)
# Look: 1.6x optical-flow slow motion, slow push-in, golden teal/orange grade,
# vignette, film grain, 2.39:1 letterbox, fade from/to black.
# Sound: sub boom on the open, low drone + swell, the clip's own room tone
# slowed down and washed in reverb underneath.
set -euo pipefail

IN="${1:?usage: $0 input.mp4 [output.mp4]}"
OUT="${2:-output/cinematic.mp4}"
SLOW=1.6                       # slow-motion factor
SRC_DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
DUR=$(awk "BEGIN{printf \"%.3f\", $SRC_DUR*$SLOW}")
FADE_OUT=$(awk "BEGIN{printf \"%.3f\", $DUR-1.2}")
FRAMES=$(awk "BEGIN{printf \"%d\", $DUR*24}")
BAR=138                        # 1080 - 1920/2.39, halved
STABILIZE="${STABILIZE:-0}"
ROTATE="${ROTATE:-0}"
KEYSTONE="${KEYSTONE:-0}"
ZOOM="${ZOOM:-1}"

IN_V="$IN"
# Default: slow push-in done by zoompan at 4K so it doesn't step.
GEOM="scale=3840:2160:flags=bicubic,\
zoompan=z='${ZOOM}+0.10*on/${FRAMES}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=24,"
if [ "$STABILIZE" = 1 ]; then
  # stabilize.py locks the shot, straightens it and does the push-in in a
  # single sub-pixel warp per frame.
  IN_V=$(mktemp --suffix=.mkv)
  trap 'rm -f "$IN_V"' EXIT
  python3 "$(dirname "$0")/stabilize.py" "$IN" "$IN_V" --rotate "$ROTATE" \
    --keystone "$KEYSTONE" --zoom "$ZOOM" "$(awk "BEGIN{print $ZOOM+0.10}")" --size 1920x1080
  GEOM=""
elif [ "$ROTATE" != 0 ] || [ "$KEYSTONE" != 0 ]; then
  echo "ROTATE and KEYSTONE need STABILIZE=1" >&2; exit 1
fi

GRADE="eq=gamma=0.82:contrast=1.18:saturation=1.15:brightness=-0.04,\
curves=r='0/0 0.25/0.20 0.75/0.82 1/1':g='0/0.02 0.5/0.48 1/0.97':b='0/0.08 0.25/0.26 0.75/0.66 1/0.88',\
colorbalance=rs=-0.08:bs=0.10:rh=0.08:bh=-0.10"

VIDEO="[1:v]scale=1920:1080:flags=lanczos,setpts=${SLOW}*PTS,\
minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,\
${GEOM}${GRADE},vignette=angle=PI/4.5,noise=alls=7:allf=t,\
drawbox=y=0:w=iw:h=${BAR}:color=black:t=fill,drawbox=y=ih-${BAR}:w=iw:h=${BAR}:color=black:t=fill,\
fade=t=in:st=0:d=1.0,fade=t=out:st=${FADE_OUT}:d=1.2,format=yuv420p[v]"

# Sub boom: pitch-dropping sine with exponential decay, hit at 0.25 s.
BOOM="aevalsrc='if(gt(t,0.25),0.9*sin(2*PI*(38+40*exp(-(t-0.25)*6))*(t-0.25))*exp(-(t-0.25)*1.6),0)':s=48000:d=${DUR}"
# Drone: detuned low fifths that swell towards the end.
DRONE="aevalsrc='0.22*(sin(2*PI*55*t)+0.7*sin(2*PI*82.6*t)+0.5*sin(2*PI*110.4*t))*(0.35+0.65*t/${DUR})*(1+0.15*sin(2*PI*0.25*t))':s=48000:d=${DUR}"

AUDIO="${BOOM},pan=stereo|c0=c0|c1=c0[boom];\
${DRONE},lowpass=f=400,pan=stereo|c0=c0|c1=c0,aecho=0.8:0.7:60|120:0.3|0.2[drone];\
[0:a]atempo=0.8,atempo=0.8,asetrate=48000*0.8,aresample=48000,volume=8dB,aecho=0.8:0.85:400|800:0.4|0.25[room];\
[boom][drone][room]amix=inputs=3:normalize=0,atrim=0:${DUR},\
afade=t=in:st=0:d=0.2,afade=t=out:st=${FADE_OUT}:d=1.2,alimiter=limit=0.89,loudnorm=I=-16:TP=-1.5[a]"

mkdir -p "$(dirname "$OUT")"
ffmpeg -hide_banner -loglevel error -stats -y -i "$IN" -i "$IN_V" \
  -filter_complex "${VIDEO};${AUDIO}" -map "[v]" -map "[a]" \
  -c:v libx264 -preset slow -crf 18 -profile:v high -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart -t "$DUR" "$OUT"
echo "wrote $OUT (${DUR}s)"
