---
name: 3d-flipbook-reel
description: Make a vertical video of an open sketchbook in 3D that flips through pages made from your images, with big white hand-lettered captions. It floats in a snowy night scene, or over any background clip with --bg. Use when someone wants a sketchbook flip-through, a book or portfolio page-turn video, or 3D page flips over their own footage.
---

# 3D flip-book reel

Renderer: `make_flipbook.py` at the repo root. Output: `output/sketchbook_flipbook.mp4` (1080x1920, 30 fps) plus `output/flipbook_cover.jpg`.

```
python3 make_flipbook.py                    # drawn snowy night scene
python3 make_flipbook.py --bg my_clip.mp4   # book over your own footage (looped, scaled, cropped to 9:16)
python3 make_flipbook.py --preview 3 20     # stills -> output/preview/
```

## What to edit

- **Pages:** `build_pages()` returns spreads as `(left, right)` pairs. A full-width spread can be split in half with two crops. `None` on the left means the animated neon cat gif. `text_page([(text, size), ...], seed)` makes a handwritten page.
- **Page turns:** `FLIPS` is a list of `(leaf, start_seconds, direction, duration)`. Leaf `j` turns spread `j` into spread `j+1`; `direction=-1` turns it back. Fast riffles use durations around 0.6 s, readable turns about 0.95 s.
- **Captions:** `CAPTIONS` is a list of `(start, end, "TEXT\nON LINES")`. Text auto-shrinks to fit 900 px. Line them up with the flips so each caption describes the page that's showing.
- **Camera:** `camera_at(t)` sets yaw, pitch, roll, scale and position. It already does an intro swing and a slow drift; add time windows for extra moves (the 23.4 to 27.2 s swing is an example).
- **Ending:** `FADE_START`, `FADE_DUR` dim the scene; the last caption moves to the centre.
- `DURATION` sets the total length; `N_LEAVES` must equal the number of spreads minus one.

## Tips

- Images are cropped to the page shape (760x790) by `cover_crop`; pass `inset=0.0` for images with no photo border.
- The book layer is rendered at 2x and scaled down (`SS = 2`) for clean edges. Lower to 1 for quick tests.
- For `--bg` clips, pick footage with a calm centre; the book covers y = 330 to 1730.
