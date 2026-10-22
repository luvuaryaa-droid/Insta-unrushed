# Insta-unrushed: weekly sketchbook tour

## "The noise / what it quietened into" (two-page reel)

`make_noise_quiet.py` → `output/noise_to_quiet.mp4` (1080×1920, 33 s, 30 fps, silent audio track for adding music in Instagram).

- 0–7 s: the neon fish page as racing, shaky punch-in cuts that slowly settle ("My mind was racing." / "Left page: the noise.").
- 7–13 s: a blank sheet, then the ink flower page drawn on from its centre outwards.
- 13–22 s: slow close-ups on the loops, dashes and circles ("Over and over.").
- 22–33 s: the photo of the open spread with both page labels, then the closing card ("Patterns are enough." with a little sprig).

Also: `output/noise_to_quiet_cover.jpg` (cover frame) and `output/noise_to_quiet_caption.txt`. Source pages are `artworks/noise_fish.jpg`, `artworks/quiet_flower.jpg` and `artworks/noise_quiet_spread.jpg`. Previews: `python3 make_noise_quiet.py --preview 2 9 20`.

## Earlier reels

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
