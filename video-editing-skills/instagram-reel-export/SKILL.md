---
name: instagram-reel-export
description: Finish and export a video as an Instagram Reel (also fine for TikTok and YouTube Shorts) with the right size, codec, frame rate, audio track, cover image, safe zones and post caption. Use when a video is ready to post, or when someone asks how to export, encode or check a reel.
---

# Instagram Reel export

## Target spec

- 1080x1920 (9:16), H.264 High profile, `yuv420p`, CRF 20 to 21, `-preset slow`.
- 24 or 30 fps, constant.
- Always include an audio track. If there's no music, add a silent one so Instagram lets you add music in the app.
- `-movflags +faststart` so it starts playing before it has fully downloaded.
- 15 to 90 seconds.

Pipe raw frames from Python (what both renderers here do):

```
ffmpeg -y -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 24 -i - \
  -f lavfi -i anullsrc=r=44100:cl=stereo \
  -c:v libx264 -preset slow -crf 21 -pix_fmt yuv420p -profile:v high \
  -c:a aac -b:a 128k -shortest -movflags +faststart out.mp4
```

Re-encode an existing file to spec:

```
ffmpeg -i in.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" \
  -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -profile:v high \
  -c:a aac -b:a 128k -ar 44100 -movflags +faststart reel.mp4
```

## Safe zones

Keep text and faces between y = 250 and y = 1650, and away from the right 120 px (like, comment and share buttons). The grid crop on the profile shows the centre 1080x1350 (4:5), so the cover's main subject goes there.

## Deliverables

1. `output/<name>.mp4`: the reel.
2. `output/cover.jpg`: a frame with the title showing, saved at quality about 92.
3. `output/instagram_caption.txt`: a hook line, 2 to 4 short lines in the creator's own voice, then 10 to 15 relevant hashtags.

## Check before handing over

```
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,pix_fmt -show_entries format=duration -of compact out.mp4
```

Expect `h264`, `1080x1920`, `yuv420p`, an `aac` stream, and the duration you planned. Extract a few frames (`ffmpeg -ss 10 -i out.mp4 -frames:v 1 check.jpg`) and look at them before saying the video is done.
