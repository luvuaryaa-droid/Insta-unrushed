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

## Diwali diya card: process reel

A photo-animation reel (1080×1920, 29.5 s, 30 fps) made from 14 progress photos of a gouache Diwali card. Each photo becomes a printed photo with a handwritten step label. The prints are tossed onto a pile one by one, with a shutter flash and a small camera shake as each lands. At the end the finished card lifts off the pile, the flame glows, and "Happy Diwali" appears.

- `output/diya_process.mp4`: the finished reel. It has a silent audio track, so you can add music in Instagram.
- `output/diya_cover.jpg`: cover frame.
- `output/diya_instagram_caption.txt`: post caption with hashtags.
- `artworks/diya_process/`: the 14 progress photos, cropped to the card.
- `make_diya_reel.py`: the renderer. Step labels are in `LABELS` and timings are at the top of the file.

```
python3 make_diya_reel.py                  # full render
python3 make_diya_reel.py --preview 2 9 26  # stills at the given seconds -> output/preview/
```
