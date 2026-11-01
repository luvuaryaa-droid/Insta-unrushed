# Insta-unrushed: weekly sketchbook tour

There are two versions of this week's reel:

1. **3D flip-book** (`make_flipbook.py` → `output/sketchbook_flipbook.mp4`, 59 s, 30 fps): an open sketchbook floats in a snowy night scene and flips through the pages, with big white hand-lettered captions. To float the book over your own footage instead of the drawn scene, run `python3 make_flipbook.py --bg my_clip.mp4`.
2. **Papercut stop-motion** (`make_video.py` → `output/sketchbook_tour.mp4`), described below.

## Papercut version

A papercut stop-motion reel (1080×1920, 56 s) made from this week's sketchbook pages. It has burned-in captions and no voice-over.

- `output/sketchbook_tour.mp4`: the finished reel. It has a silent audio track, so you can add music in Instagram.
- `output/cover.jpg`: cover frame for the reel.
- `output/instagram_caption.txt`: post caption with hashtags.
- `artworks/`: the source paintings.
- `make_video.py`: the renderer.

## Re-rendering

```
python3 make_video.py                 # full render (needs ffmpeg, Pillow, numpy)
python3 make_video.py --preview 3 20  # stills at the given seconds -> output/preview/
```

The story, captions, colours and timings are all in `build()` in `make_video.py`.

Fonts: Caveat and Special Elite (SIL OFL), and Permanent Marker (Apache 2.0), all from Google Fonts.

## Painting My Way Back to Myself, Day 1 (self portrait)

`day1_self_portrait/` holds the 17 progress shots, colour-corrected so they match the final scan (`raw/17.jpg`).

- `raw/`: the original photos in order (01 is the line drawing, 17 is the finished piece).
- `corrected/`: full-resolution colour-corrected photos with the original framing.
- `instagram/`: 1080×1350 (4:5) carousel slides.
- `before_after.jpg`: contact sheet comparing each photo before and after.

`python3 color_correct.py` re-runs it. The script white-balances each photo on the paper, sets the ink black and paper white to match the final, then matches saturation hue by hue (reds to reds, greens to greens).

### Day 1 reel

`make_day1_reel.py` → `output/day1_self_portrait_reel.mp4` (1080×1920, 111 s, 30 fps). It carries your voice-over (`day1_self_portrait/voiceover.m4a`), levelled to −14 LUFS for Instagram. The reel opens on the finished piece, plays every stage from the first line to the final with hand-lettered captions and progress dots, then shows close-ups of the finished painting before the outro. Each section starts on a pause in the voice-over (about 5, 12, 34, 49 and 68 s). The cover frame is `output/day1_cover.jpg` and the post caption is `output/day1_instagram_caption.txt`. Captions, timings and per-photo crops are in `STEPS` and `CROPS` at the top of the script. If the voice-over file is missing, the reel gets a silent track instead.
