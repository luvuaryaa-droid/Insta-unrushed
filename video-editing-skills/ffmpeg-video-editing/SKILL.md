---
name: ffmpeg-video-editing
description: Everyday video edits on the command line with ffmpeg - trim, cut, join clips, crop or pad to 9:16, resize, change speed, replace or mix music, fade, burn in subtitles or text, overlay a logo or picture-in-picture, extract frames, make GIFs, and inspect files with ffprobe. Use for any edit to an existing video or audio file that doesn't need a full renderer.
---

# Video editing with ffmpeg

Always inspect first: `ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,r_frame_rate -show_entries format=duration -of compact in.mp4`

Default output flags (add to any command below that re-encodes):
`-c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart`

## Cutting and joining

| Task | Command |
|---|---|
| Trim, frame-accurate | `ffmpeg -ss 00:00:05 -to 00:00:12 -i in.mp4 <flags> out.mp4` |
| Trim, instant, no re-encode (cuts on keyframes) | `ffmpeg -ss 5 -to 12 -i in.mp4 -c copy out.mp4` |
| Join clips with identical codecs | write `file 'a.mp4'` lines to `list.txt`, then `ffmpeg -f concat -safe 0 -i list.txt -c copy out.mp4` |
| Join clips that differ | `ffmpeg -i a.mp4 -i b.mp4 -filter_complex "[0:v]scale=1080:1920,setsar=1[v0];[1:v]scale=1080:1920,setsar=1[v1];[v0][0:a][v1][1:a]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" <flags> out.mp4` |
| Crossfade two clips | `-filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=<len_a-0.5>[v];[0:a][1:a]acrossfade=d=0.5[a]"` |

## Framing

| Task | Filter (`-vf`) |
|---|---|
| Fill 9:16 by cropping | `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920` |
| Fit 9:16 with blurred background | use `-filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2"` |
| Fit with black bars | `scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2` |
| Rotate 90° clockwise | `transpose=1` |
| Slow zoom (Ken Burns) on a still | `zoompan=z='min(zoom+0.0008,1.2)':d=150:s=1080x1920:fps=30` with `-loop 1 -t 5 -i photo.jpg` |

## Time and audio

| Task | Command |
|---|---|
| 2x speed | `-filter_complex "[0:v]setpts=0.5*PTS[v];[0:a]atempo=2.0[a]" -map "[v]" -map "[a]"` |
| Half speed | `setpts=2.0*PTS` and `atempo=0.5` |
| Replace audio with music | `ffmpeg -i in.mp4 -i song.mp3 -map 0:v -map 1:a -c:v copy -c:a aac -shortest out.mp4` |
| Mix music under voice | `-filter_complex "[1:a]volume=0.25[m];[0:a][m]amix=inputs=2:duration=first[a]" -map 0:v -map "[a]"` |
| Fade in/out | `-vf "fade=t=in:d=0.5,fade=t=out:st=<len-0.5>:d=0.5" -af "afade=t=in:d=0.5,afade=t=out:st=<len-0.5>:d=0.5"` |
| Remove audio | `-an` |
| Add silent track | `-f lavfi -i anullsrc=r=44100:cl=stereo -shortest` |
| Loudness normalise | `-af loudnorm=I=-14:TP=-1.5:LRA=11` |

## Text and overlays

| Task | Command |
|---|---|
| Burn in an `.srt` | `-vf "subtitles=subs.srt:force_style='FontName=Permanent Marker,FontSize=16,Outline=2,Alignment=2,MarginV=180'"` (add `:fontsdir=fonts` for repo fonts) |
| Timed text | `-vf "drawtext=fontfile=fonts/Caveat.ttf:text='hello':fontsize=90:fontcolor=white:borderw=4:x=(w-tw)/2:y=300:enable='between(t,1,4)'"` |
| Logo in the corner | `-filter_complex "[1:v]scale=180:-1[l];[0:v][l]overlay=W-w-40:40"` |
| Picture-in-picture | `-filter_complex "[1:v]scale=360:-1[p];[0:v][p]overlay=W-w-40:H-h-260"` |
| Green screen | `-filter_complex "[1:v]chromakey=0x00FF00:0.15:0.05[k];[0:v][k]overlay"` |

## Frames and GIFs

| Task | Command |
|---|---|
| One frame | `ffmpeg -ss 3 -i in.mp4 -frames:v 1 frame.jpg` |
| Contact sheet | `ffmpeg -i in.mp4 -vf "fps=1/5,scale=270:-1,tile=4x3" -frames:v 1 sheet.jpg` |
| Images to video | `ffmpeg -framerate 12 -i img_%03d.png <flags> out.mp4` |
| Good-looking GIF | `ffmpeg -i in.mp4 -vf "fps=12,scale=540:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse" out.gif` |

## Habits

- Put `-ss` before `-i` for fast seeking.
- Use `-c copy` only when no filter is applied.
- After any edit, run ffprobe and pull a frame to check the result before reporting it as done.
