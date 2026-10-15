# Creator Studio: three video ads

All three are 1080×1920 (9:16) papercut reels, rendered by `make_ads.py`. Each has a silent audio track so you can add trending audio in-app.

## 1. Artists: "You paint. Claude handles the reels." (`ad_artists_you_paint.mp4`, 23 s)

| Time | Scene |
|---|---|
| 0–3 s | Paintings drop onto mustard paper. **"You paint."** |
| 3–7 s | "...then comes the reel." The chores pop up (trim 47 clips, write captions, find music, pick a cover, hashtags?!) and get crossed out in red. **"not anymore."** |
| 7–10 s | Prompt card types out: *"Turn this week's paintings into a reel. Papercut style, my handwriting vibe."* / "just drop your art in" |
| 10–15 s | A phone plays the finished reel while ticks pop in: story + captions, papercut motion, cover + hashtags, ready to post. **"in minutes, not evenings"** |
| 15–18 s | Neon cat. "you stay in the zone." / "Claude handles the reels." |
| 18–23 s | End card: You paint. / Claude handles the reels. / CREATOR STUDIO / **Start your first reel >** |

Post copy: *You make the art. Claude makes the reel: captions, motion, cover and hashtags from your paintings. More time at the easel, less time in the editor. 🎨*

## 2. UGC and content creators (`ad_ugc_creators.mp4`, 20.5 s)

| Time | Scene |
|---|---|
| 0–3 s | **"POV: you filmed 3 hours of content"**, with 12 raw clips raining down. "...for a 30-second post" |
| 3–6 s | "skip the timeline." Prompt: *"Cut this into 3 hooks for Reels, TikTok & Shorts. Captions on, keep my brand colours."* |
| 6–11.5 s | "3 hooks. one upload." Three phones play hook A/B/C with different on-screen hooks. **"test what actually lands"** |
| 11.5–15.5 s | "Claude handles the busywork:" auto captions, every aspect ratio, on-brand fonts + colours, cover + caption copy. **"you stay on camera."** |
| 16–20.5 s | End card: Film it. / Claude ships it. / **Post more. Edit less >** |

Post copy: *Film once, post everywhere. Creator Studio cuts your footage into multiple hooks with captions and your brand look, ready for Reels, TikTok and Shorts.*

## 3. Beginners (`ad_beginners.mp4`, 22.5 s)

| Time | Scene |
|---|---|
| 0–3 s | "Never edited a video?" **"Good."** "you don't need to." |
| 3–6.5 s | Step 1: **add your photos** (cut-outs drop into a tray). "phone pics are fine" |
| 6.5–10 s | Step 2: **describe the vibe**. Prompt: *"Something cozy and slow, with a bit of handwriting. 20 seconds."* "in your own words. / no jargon, no timeline" |
| 10–14 s | Step 3: **post it**. The finished reel plays on a phone. |
| 14–17.5 s | ~~an evening of tutorials~~ → **a few minutes with Claude**. "and it looks like a pro made it." |
| 18–22.5 s | End card: Pro-looking reels. / Zero editing skills. / **Make your first reel >** |

Post copy: *No editing experience needed. Add your photos, tell Claude the vibe, and post a reel that looks pro.*

## Before you run them

- "in minutes", "a few minutes" and "every aspect ratio" are product claims. Check they match what Creator Studio actually does before buying media.
- The ads use the sketchbook paintings in `artworks/` as the demo content. To show other work, change the artwork names in the `build_*()` functions.
- Copy, colours and timings for each ad are in `build_artists()`, `build_creators()` and `build_beginners()`. Re-render one ad with `python3 make_ads.py creators`, or write stills with `python3 make_ads.py creators --preview 2 9`.
