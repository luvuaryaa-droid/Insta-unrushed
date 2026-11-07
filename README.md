# Insta-unrushed: weekly sketchbook tour

## Painting process reel (Vox-style collage)

`make_vox_process.py` → `output/painting_process_vox.mp4` (1080×1920, 52 s, 12 fps stop-motion shown at 24 fps, silent audio track so you can add music in Instagram). One snake-plant painting goes from pencil to paint in 12 stages, styled like a collage explainer: newsprint grid paper, a halftone title card, torn colour blocks, bold header strips, red marker circles and arrows that draw themselves on, magnifier call-outs, paint swatches, rubber stamps, a progress filmstrip, a 2-second replay and a final grid of all 12 stages.

- `output/painting_process_vox_cover.jpg`: cover frame. `output/painting_process_caption.txt`: post caption.
- `artworks/process/stage_01.jpg` … `stage_12.jpg`: the progress photos, straightened and aligned so the painting sits in the same place in every stage. `prep_process.py` made them (it needs `opencv-python-headless`; the renderer doesn't).
- Stage titles, captions, annotations and timings are in `build()` in `make_vox_process.py`. `python3 make_vox_process.py --preview 5 20 40` writes stills to `output/preview/`.

## Weekly sketchbook tour

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

Fonts: Caveat, Special Elite and Inter (SIL OFL), and Permanent Marker (Apache 2.0), all from Google Fonts.
