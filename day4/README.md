# Painting my way back to myself: Day 4

A 36 s process reel (1080×1920, 30 fps) of the snake-plant folk painting. The ten progress photos are lined up so the board stays still, then each stage is brushed in over the last with a painterly stroke wipe and a short caption.

- `output/day4_painting_3x4.mp4`: minimal 3:4 (1080×1440) version: the painting building up, with only the "painting my way back to myself / DAY 4" title above it (`python3 make_day4_clean.py`).
- `output/day4_process.mp4`: the finished reel. Its audio track is silent, so you can add music in Instagram.
- `output/cover.jpg`: cover frame.
- `output/instagram_caption.txt`: post caption with hashtags.
- `stages/`: the original progress photos, upright and resized.
- `aligned/`: the same photos warped onto one shared square canvas (written by `align.py`).

## Re-rendering

```
pip install opencv-python-headless   # only needed for align.py
python3 align.py                     # stages/ -> aligned/
python3 make_day4.py                 # aligned/ -> output/day4_process.mp4
python3 make_day4.py --preview 3 16 30   # stills -> output/preview/
```

Step captions are in `STEPS` and timings in the `T_*` constants at the top of `make_day4.py`.
