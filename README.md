# Insta-unrushed: weekly sketchbook tour

## New: "I Am an Ocean" lyric reel

`make_ocean.py` → `output/i_am_an_ocean.mp4` (1080×1920, 30 fps, 90 s, with the song). Sixteen paintings from `artworks/ocean/` dive from a grey surface into a deep sea, cut to the beat of `music/I_Am_an_Ocean.mp3`, with word-by-word karaoke lyrics. Cover: `output/ocean_cover.jpg`. Caption: `output/ocean_caption.txt`.

```
python3 make_ocean.py                   # full render (~5 min on 4 cores)
python3 make_ocean.py --preview 17 66   # stills -> output/preview/
```

The lyric timings, the scene order and the artwork crops are at the top of `make_ocean.py`.

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
