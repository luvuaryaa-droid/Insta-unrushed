# I Am an Ocean: an experimental mixed-media art film

An 88-second, 16:9 art film (1920×1080, 24 fps) cut to the track *I Am an Ocean*, built from the original paintings, their framed mockups and the ink sketches in `../artworks/`. Credit: **@the_Unrushed.whispers**.

The paintings are never redrawn or generated. Every piece is shown with its own pixels. The "animation" is camera moves, paper and light layered over the work, and glows or tiny rotations of regions cut from the same image (lantern, moon, diya flame, fire, latte foam). The black cat is the artist's own animated GIF.

## Structure (times measured from the track: 107.7 BPM, drums enter at 17.8 s)

| Time | Music | Picture |
|---|---|---|
| 0–17.8 | Intro: the critic's voice | **The Box.** Monochrome. Moka-pot mockup, *"you change too much"* crossed out, a tidy gallery wall of ink sketches, a push through the mat into the ink architecture, then a drop of ink in the silence |
| 17.8–35.6 | Verse 1 | Colour bursts out of the ink: lantern girl (*"I paint, but my niche is me."*), torn-paper portraits, seasons landing on a pile, the walking woman and her moon |
| 35.6–49.0 | Chorus | Torn strips collide, mosaic sapling (*"I was never meant to stay the same."*), latte cup, then the gallery frames break apart: *"I won't be boxed up"* |
| 49.0–53.4 | Breakdown | The diya in stillness, then the screen floods with its blue |
| 53.4–79.8 | Outro | A dive: cat, blue flowers, a portrait panorama (*"I am an ocean"*), pieces rising past at different depths, then every work as mosaic tiles |
| 79.8–87.6 | Tail | Pull back from the reading nook into its framed mockup: *"at every depth, a different me."* Title card |

## Files

- `src/scenes.tsx`: every scene. Times are absolute seconds in the song.
- `src/Film.tsx`: master timeline, colour grade, gate weave, grain, dust, light leaks.
- `src/parts.tsx`: sheets, camera, handwriting, ink/torn-paper/ripple transitions.
- `tools/crop.py`: cuts each painting out of its mockup (`tools/crops.json` has the boxes).
- `tools/textures.py`: procedural paper, 16mm grain, leaf-shadow gobo and caustics.

## Rendering

```
npm install
npm run studio                      # interactive preview
npx remotion render src/index.ts Ocean out/master_raw.mov --codec=prores --prores-profile=hq
tools/encode.sh                     # -> out/I_Am_an_Ocean_1080p.mp4 (H.264, original MP3 audio copied)
node tools/stills.mjs <dir> 0.5 18.3 60.5   # stills at given seconds
```

In the cloud container, add `--browser-executable=/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell`.
