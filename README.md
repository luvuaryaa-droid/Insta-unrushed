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

## "Do it anyway" reel with voice-over

`output/do_it_anyway_voiceover.mp4` (female voice `af_heart`) and the male-voice versions `output/do_it_anyway_voiceover_am_michael.mp4` (warm) and `output/do_it_anyway_voiceover_am_onyx.mp4` (deeper) are the 11 s "Do it sad / angry / ... / anyway" sketchbook clip with a spoken voice-over reading each caption as it appears. The original video stream is copied unchanged. The voice is Kokoro neural TTS (pick one with `--voice`), and every line ends before the next cut.

```
pip install kokoro-onnx soundfile
# put kokoro-v1.0.onnx and voices-v1.0.bin (from the kokoro-onnx GitHub release model-files-v1.0) in models/
python3 add_voiceover.py my_clip.mp4 output/do_it_anyway_voiceover.mp4 --models models
```

The lines, shot timings and speaking speeds are in `SCRIPT` at the top of `add_voiceover.py`.
