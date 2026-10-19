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

## Cinematic nature reel

`make_reel.py` → `output/final.mp4` (1080×1350 4:5, 30 fps, H.264, 1:58) is made from `footage/VID_20261014_232420.mp4`.

- **Grade:** a teal-orange matte film look. Skies and shadows go teal, skin and warm colours stay orange, greens shift toward olive, overall saturation is 15 % lower, blacks are lifted and contrast is soft. The grade is generated as a 3D LUT by `grade.py`. A `--lut file.cube` is applied before it.
- **Effects:** a 2 s black title card, 50 % slow-motion (motion-interpolated) on the swan and orange-flower shots, a 5-piece flash-cut burst (~0.15 s slices) from the feet shot, a 1.5 s fade to black and a 2 s end card.

```
python3 make_reel.py                                  # 4:5 -> output/final.mp4
python3 make_reel.py --aspect 9:16                    # Reels 1080x1920
python3 make_reel.py --aspect 5:4                     # 1280x1024
python3 make_reel.py --title "slow days" --handle @me --logo logo.png \
                     --slow swan clouds --burst railing --lut film.cube
```

Shot names for `--slow` / `--burst`: swan, duck, pond, white_flowers, purple_flower_1, purple_flower_2, orange_flower, tree_tunnel, feet, clouds, railing, street.
