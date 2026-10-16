# Artist Date: Hollywood Cinematic Style Guide

Your signature look for every artist date video. Same settings, same grade, same voice, every time.

## Camera settings (phone)

| Setting | Use | Why |
|---------|-----|-----|
| Resolution | 4K, horizontal | Room to reframe and crop to widescreen without losing sharpness |
| Frame rate | 24 fps | The "film" frame rate |
| Shutter | 1/50 | Natural motion blur (the 180-degree rule). Fast shutters make movement look jittery and "video-ish" |
| ND filter | Yes, in daylight | Lets you keep 1/50 on a bright day without overexposing. A clip-on variable ND for phones is cheap |
| White balance | Locked (about 5600K in daylight) | Colour won't shift mid-shot |
| Focus and exposure | Locked | No "breathing" or brightness jumps |
| Profile | Flat or log if your app offers it | More room to grade later |

## How to shoot

1. **Hold every shot 5 to 8 seconds.** Use a tripod, a wall or a railing, or brace your elbows on your body.
2. **Move slowly or not at all.** Slow push-ins and slow pans only.
3. **Frame through something.** Leaves, railings, doorways in the foreground add depth (your street clip already does this with the leaves).
4. **Put your subject on a third,** not dead centre.
5. **Get 4 kinds of shots on every date:** wide (the place), medium (a person or object), close-up (a flower, a cup), detail (your hand, your sketchbook).
6. **Put yourself in it:** from behind, your hands, your shadow, your feet on a path. No face needed.
7. **Chase soft light:** early morning or the hour before sunset. Backlight (sun behind the subject) looks most cinematic.
8. **Record 20 seconds of plain ambient sound** at each location (birds, traffic, wind) to put under your voiceover.

## Grade recipe (CapCut, VN, Lightroom or any editor)

Save this as a preset and use it on every artist date.

| Adjustment | Value |
|------------|-------|
| Contrast | +5 |
| Saturation | -15 |
| Fade / lift blacks | +5 to +10 |
| Highlights tint | slightly warm (orange) |
| Shadows tint | slightly cool (teal) |
| Vignette | light |
| Grain | 5 to 10 |

## Export (your signature)

- Horizontal 16:9, 1920x1080. **No letterbox bars**: the full frame is picture.
- The film feel comes from the grade, 24 fps, slow shots and the 1/50 shutter, not from bars.
- Subtitles in the lower third, white serif. On phones the video sits small in the middle of the screen, so size text big enough to read there.
- Cover image: make a separate vertical 9:16 cover (a still with your title) so the grid tile looks good.

## Midday sun fix

Harsh noon light (like the leaf and temple clips) blows out pale ground and makes shadows hard. In the grade, pull highlights down (-15 to -25), lift shadows a little (+10), then add the warm/cool tint. Better still, shoot before 10 am or after 4 pm.

## One-command treatment

`make_cinematic.py` in this repo applies the whole look to a raw clip:

```
python3 make_cinematic.py raw_clip.mp4 output/my_clip_cinematic.mp4
```

It finds the cuts between shots, stabilises each shot (trying a full tripod lock and smooth mode, keeping whichever is steadier), fills a 1920x1080 frame with no bars, applies the signature grade and grain, and keeps the original sound. Options: `--mode tripod|smooth`, `--smoothing 90`, `--no-grain`.
