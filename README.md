# Insta-unrushed

## Art for Anxious Days, Vol. 1 (shop product)

A digital art zine made from the sketchbook pages, sold in two tiers. Everything is in `product/`:

| File | What it is | Tier |
|---|---|---|
| `art_for_anxious_days_vol1.pdf` | The zine: 16 A5 pages (cover, letter, 11 drawings with a note and a "try this" prompt, breathing page, journal page, thank-you/Vol. 2 page) | ₹299 |
| `print_pack/prints_A4.pdf` | 11 frameable A4 prints, 300 dpi | ₹499 adds |
| `print_pack/wallpapers/` | 11 phone wallpapers, 1080×1920 | ₹499 adds |
| `promo/slide_1..4.jpg` + `promo/launch_caption.txt` | Instagram launch carousel (1080×1350) and caption | – |
| `listing.md` | Copy to paste into the shop page (title, description, FAQ, which files to upload) | – |
| `cover.jpg` | Product thumbnail | – |

Rebuild with `python3 make_zine.py` (add `--pages` to also dump page JPEGs to `product/pages/`). All the text (titles, notes, prompts) is in `PIECES` and the page functions at the top of `make_zine.py`.

# Weekly sketchbook tour reel

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
