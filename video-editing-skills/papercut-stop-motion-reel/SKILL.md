---
name: papercut-stop-motion-reel
description: Make a vertical (1080x1920) papercut stop-motion video from still images such as artworks, photos or sketchbook pages. Torn paper backgrounds wipe between scenes, images become cut-outs with washi tape and shadows, and captions sit on torn paper strips. Use when someone wants a handmade, collage or stop-motion reel, TikTok or Short built from pictures.
---

# Papercut stop-motion reel

Renderer: `make_video.py` at the repo root. Output: `output/sketchbook_tour.mp4` plus `output/cover.jpg`.

## Workflow

1. Put the source images in `artworks/` (jpg, png; an animated gif plays as a looping sprite).
2. Write the story first: one short sentence per scene, 3 to 6 seconds each. Put the hook in the first 2 seconds.
3. Edit `build()` in `make_video.py`. Each scene is a block that starts at time `t` with z-base `z` (use `z = 100 * scene_number` so later scenes sit on top).
4. Check stills before a full render: `python3 make_video.py --preview 3 8 13.5`. Look at the JPGs in `output/preview/`.
5. Render: `python3 make_video.py`.

## Building blocks

| Call | What it makes |
|---|---|
| `background(t, color, seed, from_dir, z)` | Full-screen torn sheet that slides in from `left/right/up/down` and covers the previous scene. Start it 0.5 s before the scene so the wipe lands on time. |
| `cutout(img, max_w, max_h, seed, tape="top"/"corners")` | Image on a scissor-cut white border with tape and a drop shadow |
| `text_strip(text, font, paper=, ink=)` | Text on a torn paper strip |
| `caption(text, t, y, z, size=, paper=)` | Shortcut: a text strip that pops in with a slight random tilt |
| `star(size, color, seed)`, `paper_circle(...)`, `strike(w, seed)` | Decorations; `strike` with `reveal=(start, dur)` draws a red cross-out from left to right |
| `Sprite(img, t0, (x, y), rot=, z=, enter=, t1=, leave=, path=)` | Anything that moves |

Sprite options:
- `enter`: `drop` (falls in with a bounce), `pop` (scales up with overshoot), `slide_left/right/up/down`, `fade`, `none`.
- `leave` (needs `t1`): `shrink`, `slide_*`, `fade`.
- `path=f(t) -> (x, y, rot, scale)` for custom motion, for example orbits.
- `frames=[...]`, `frame_dur=` for animated sprites.
- `boil` (default 1.0): per-frame jitter that makes the paper look hand-moved. Set 0 for backgrounds.

Fonts: `caveat(size)` (handwriting), `marker(size)` (Permanent Marker, for big titles), `typewriter(size)` (Special Elite).

## Style rules

- Animate at 12 fps and output at 24 fps (each frame shows twice). That is what makes it read as stop-motion; don't raise `FPS`.
- Take the palette from the artworks (the constants at the top of the file). Alternate light and dark backgrounds between scenes.
- Keep captions inside y = 250 to 1650 so the Instagram UI doesn't cover them.
- Change `seed` values for new layouts; the same seed gives the same tear and tilt.
- Sprites covered by a later full-screen sheet are culled automatically, so long videos stay fast.
