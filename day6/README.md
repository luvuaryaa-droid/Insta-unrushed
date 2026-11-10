# Day 6: scooter painting

A process reel of the scooter painting, from pencil sketch to finished border. 1080×1920, 27 s, 30 fps, with a silent audio track so you can add music in Instagram.

- `output/day6_scooter.mp4`: the reel
- `output/day6_cover.jpg`: cover frame
- `output/instagram_caption.txt`: caption and hashtags
- `photos/`: the 19 progress photos, in order

## How it's made

```
python3 align.py       # finds the sheet in each photo and flattens it  -> aligned/
python3 refine.py      # matches each photo to its neighbour so nothing jumps -> refined/
python3 make_day6.py   # renders the reel (needs ffmpeg, Pillow, numpy)
python3 make_day6.py --preview 1 10 22   # stills -> output/preview/
```

`align.py` and `refine.py` need `opencv-python-headless`. Captions, timings and close-up spots are at the top of `make_day6.py`.
