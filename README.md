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

## Creator Studio ads

`make_ads.py` renders three 9:16 ads for Creator Studio into `output/ads/`: one for artists, one for UGC and content creators, and one for beginners. Each one walks through the full feature set, and the phones in the ads play footage from the sketchbook reels above. Scripts, a feature checklist and post copy are in `output/ads/ADS.md`.

```
python3 make_ads.py                        # all three
python3 make_ads.py beginners --preview 5  # stills -> output/ads/preview/
python3 make_voiceover.py                  # voice-over versions (needs kokoro-onnx + models/, see ADS.md)
python3 make_carousels.py                  # carousels + single-image ads
```

## Creator Studio guides

`make_guides.py` writes four PDF guides to `output/guides/`: animation styles, caption styles, effects and filters. Each guide separates what the renderers here already do (with sample frames from the reels) from what could be added on request.

```
python3 make_guides.py   # needs reportlab and ffmpeg
```

## Filters

`filters.py` adds nine colour filters (bw, sepia, warm, cool, contrast, matte, duotone, vhs, riso) and support for your own `.cube` colour grades (LUTs) to every renderer. Add `--filter NAME[:STRENGTH]` and/or `--lut FILE.cube` to any of them; the filtered file is saved next to the original with the filter in its name.

```
python3 make_ads.py artists --filter warm          # -> output/ads/ad_artists_you_paint_warm.mp4
python3 make_voiceover.py artists --filter warm    # voice-over on the warm version
python3 make_video.py --filter vhs:0.6
python3 make_flipbook.py --filter cool
python3 make_carousels.py creators --filter duotone
python3 filters.py IN.mp4 OUT.mp4 --filter sepia:0.8 --lut grade.cube   # any finished video/image/folder, audio kept
python3 filters.py --list
python3 filters.py --showreel output/sketchbook_tour.mp4 output/filters/filters_showreel.mp4
```

`output/guides/4_filters.pdf` shows every filter.
