# Insta-unrushed

## Moka pot process reel

`make_process_reel.py` → `output/moka_pot_process.mp4` (1080×1920, 29 s). It turns the five moka pot process photos in `photos/moka_pot/` (sketch, clipboard, filled in, final scan, holding it) into a papercut reel with the "You don't need to be good to show your art" captions, and ends on a "Save this" card listing 5 things to post. It reuses the paper sprites and renderer from `make_video.py`. The post caption is in `output/moka_pot_process_caption.txt`, and the cover frame is `output/moka_pot_process_cover.jpg`.

```
python3 make_process_reel.py              # full render
python3 make_process_reel.py --preview 2 19.5   # stills -> output/preview/
```

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

Fonts: Caveat and Special Elite (SIL OFL), and Permanent Marker (Apache 2.0), all from Google Fonts.
