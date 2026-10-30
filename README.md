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

## Day 1: "Painting my way back to Myself"

`make_day1.py` → `output/day1_progress.mp4` (1080×1920, 20 s, 30 fps, silent audio track) and `output/day1_cover.jpg`.
The seven progress photos in `artworks/day1/` cross-fade from the first pair of socks to the finished page, under the title "Painting my way back to Myself" and a "Day 1" badge.
The six earlier photos get the same colour look as the edited final picture (`stage7.jpg`): warm whites, deeper darks, richer colour and a deeper violet background.
The look is tuned in `grade()`.

### Brush-reveal version

`make_day1_brush.py` → `output/day1_brush.mp4` (21 s) and `output/day1_brush_cover.jpg`.
This version uses the same graded photos, shown full width. Each stage is painted on over the last one with brush strokes, the title writes itself out by hand, and "Day 1" sits on a yellow brush swash.
