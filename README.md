# Insta-unrushed: weekly sketchbook tour

**New: "Why I draw without an eraser"** (`make_no_eraser.py` → `output/no_eraser.mp4`, 57 s, 30 fps), with the artist's own voice-over. The raw take (`audio/no_eraser_voice_raw.mp3`) is trimmed to the spoken phrases (dead air, an off-script aside and long pauses removed), denoised, EQ'd, compressed and normalised to -15 LUFS (`output/no_eraser_voice.wav`). The dragonfly ink page draws itself in white on a black background, and each spoken phrase writes itself in as a caption with red accents. The phrase cut list and captions are `PHRASES` in the script. Caption: `output/no_eraser_caption.txt`. Cover: `output/no_eraser_cover.jpg`. CTA end cards (`make_cta.py`): `output/no_eraser_cta_story.jpg` (1080×1920), `output/no_eraser_cta_feed.jpg` (1080×1350) and `output/no_eraser_cta_wide.jpg` (1920×1080, 16:9). Preview stills: `python3 make_no_eraser.py --preview 3 20`.

There are two versions of the weekly sketchbook tour reel:

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
