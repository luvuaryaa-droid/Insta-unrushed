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

## Diwali diya card: pencil-to-painting transition

`output/diya_transition.mp4` (1080×1920, 33 s, 30 fps). The 14 progress photos are aligned on top of each other, so the card stays still and appears to paint itself, from the pencil sketch to the finished border. Each new layer spreads across the card like wet paint. The reel ends with a before/after slider and "Happy Diwali". Cover: `output/diya_transition_cover.jpg`.

- `make_transition.py`: the renderer.
- `artworks/diya_aligned/`: the aligned, colour-matched frames. These are already committed, so re-rendering doesn't need OpenCV.
- `python3 make_transition.py --align`: re-runs the alignment (needs `pip install opencv-python-headless`). It uses SIFT matches between neighbouring steps, chained onto step 13.

## Shubh Deepawali / Happy Deepavali: collage animation

`output/shubh_deepawali_collage.mp4` and `output/happy_deepavali_collage.mp4` (1080×1920, 12 s, stop-motion at 12 fps). The two videos are the same animation with a different greeting. This is an explainer-style paper collage. The diya, fish, lotuses and flower vines are cut out of the finished painting and layered over torn indigo paper, a halftone sunburst and newsprint scraps. The diya slams in as black-and-white newsprint and pops into colour, the fish swim in, and the flame flickers. The only text is the greeting, made from ransom-note letters. Covers: `output/shubh_deepawali_cover.jpg` and `output/happy_deepavali_cover.jpg`.

- `make_vox_collage.py`: the renderer. By default it renders "Shubh Deepawali". For another greeting, use `--greeting Happy Deepavali`. `--preview 1 3 6` writes stills.
- `artworks/diya_cutouts/`: the cut-out elements as transparent PNGs. These are already committed. `python3 make_vox_collage.py --cut` recreates them (needs OpenCV).
