# Insta-unrushed: weekly sketchbook tour

## Pencil portrait progress reel

`make_pencil_reel.py` → `output/pencil_portrait_reel.mp4` (1080×1920, 21.5 s, 30 fps, silent audio track). The 11 work-in-progress photos (`artworks/pencil_portrait/step_*.jpg`) dissolve into each other like a time-lapse with a step counter, then the finished drawing (`final.jpg`) is shown. Cover: `output/pencil_cover.jpg`; caption: `output/pencil_instagram_caption.txt`. Re-render with `python3 make_pencil_reel.py`, or `--preview 1 9` for stills.

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
