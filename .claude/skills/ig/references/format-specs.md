# Instagram Format Specs

Technical requirements, safe zones, editing patterns, algorithm behavior, and forbidden errors
for every Instagram format. Applies to all niches and account sizes.

Last updated: 2026-03-08. Source: Meta official specs + community-validated performance data.

---

## Table of Contents

1. [Reels](#reels)
2. [Stories](#stories)
3. [Carousels](#carousels)
4. [Feed Posts (Single Image)](#feed-posts-single-image)
5. [Instagram Live](#instagram-live)
6. [Reels Remix](#reels-remix)
7. [Collab Posts](#collab-posts)
8. [Audio Strategy](#audio-strategy)
9. [Caption Display Rules](#caption-display-rules)
10. [Instagram SEO](#instagram-seo)
11. [Grid Aesthetic and Profile Strategy](#grid-aesthetic-and-profile-strategy)
12. [Pinned Posts Strategy](#pinned-posts-strategy)
13. [Story Highlights](#story-highlights)
14. [Format Selection Decision Tree](#format-selection-decision-tree)
15. [Performance Signals: Quick Reference](#performance-signals-quick-reference)
16. [Universal Forbidden Errors](#universal-forbidden-errors)

---

## Reels

### Technical Specs

| Property | Value |
|----------|-------|
| Aspect ratio | 9:16 vertical |
| Resolution | 1080 x 1920 px |
| Duration | 7-90 seconds |
| Duration sweet spot (new audiences) | 15-30 seconds |
| Duration sweet spot (existing followers) | 30-60 seconds |
| File format | MP4 or MOV |
| Codec | H.264 |
| Max file size | 4 GB |
| Frame rate | 23-60 fps (30 fps recommended) |
| Audio | Stereo, 44.1 kHz |
| Bitrate (recommended) | 3500 kbps video, 128 kbps audio |

### Safe Zone Map

Reels safe zone is critical because Instagram overlays UI elements on top of the content.
Any text, logo, or important visual placed outside the safe zone gets covered.

| Zone | Pixel Range | What Covers It |
|------|-------------|----------------|
| Top unsafe | Y: 0-150px | Status bar, account name, follow button |
| Bottom unsafe | Y: 1570-1920px (350px) | Caption text, CTA button, music ticker, nav bar |
| Left unsafe | X: 0-70px | Like/comment/share icons overlap on some devices |
| Right unsafe | X: 1010-1080px | Like/comment/share/save icon column |
| **Safe area** | **X: 70-1010px, Y: 150-1570px** | **870 x 1420 px usable space** |

```
Reel Frame (1080 x 1920)
+----------------------------------+
|  UNSAFE: status bar (150px)      |  <- Y: 0-150
|+--------------------------------+|
||                                ||
||    SAFE CONTENT AREA           ||
||    870 x 1420 px               ||
||                                ||
||    X: 70-1010                  ||
||    Y: 150-1570                 ||
||                                ||
|+--------------------------------+|
|  UNSAFE: caption/nav (350px)     |  <- Y: 1570-1920
+----------------------------------+
  ^                              ^
  Left 70px unsafe     Right 70px unsafe
```

### Performance Thresholds (benchmark data, calibrate with your account-baseline.md)

| Metric | Below This = Problem | Average | Strong | Viral |
|--------|---------------------|---------|--------|-------|
| Avg watch time | < 10s (algorithm stops distributing) | 10-16s | 17-22s | > 25s |
| Completion rate | < 40% | 40-59% | 60-70% | > 75% |
| Save rate | < 1% (no distribution) | 1-3% | 3-5% | > 5% |
| Shares/reach | < 1% | 1-2% | 2-3% | > 5% |
| DM sends/reach | < 0.2% | 0.2-0.5% | 0.5-1% | > 1.5% |

Watch time target: 17-22 seconds average. Below 10 seconds means the algorithm stops
distributing the Reel entirely.

### Thumbnail

| Rule | Detail |
|------|--------|
| Default | First frame of video (if no custom thumbnail set) |
| Custom thumbnail | Strongly recommended. Upload via Reel editor. |
| Grid crop | Instagram crops 9:16 to 1:1 center-crop for profile grid. Keep key visuals centered. |
| Face-forward | Thumbnails showing a face consistently outperform abstract/text-only thumbnails |
| Text on thumbnail | Max 5-7 words, large font, high contrast, within center 600x600px area |
| Resolution | Same as Reel: 1080x1920, but design for 1080x1080 center visibility |

### Hook Structure (First 7 Seconds)

| Timeframe | Purpose | Technique |
|-----------|---------|-----------|
| 0-1s | Pattern interrupt | Show the result, not the setup. Movement, zoom, unexpected visual. |
| 1-3s | Audio hook | Deliver the spoken or text hook. Silence here = -40% completion rate. |
| 3-7s | Promise / retention gate | Tell the viewer what they will learn or gain by watching. |

The first 3 seconds determine whether the viewer stays. The 3-7s window determines whether
they watch to the end.

### Reel Editing Best Practices

#### Cut Rhythm

| Duration Range | Recommended Cut Frequency | Notes |
|---------------|--------------------------|-------|
| 7-15s | Every 2-3s | Fast pace, single idea, no dead air |
| 15-30s | Every 3-5s | Medium pace, 2-3 ideas max |
| 30-60s | Every 4-7s | Slower pace OK if face-to-camera; faster for B-roll |
| 60-90s | Every 5-8s | Must sustain with story arc or strong personality |

General rule: if nothing visually changes for more than 5 seconds, expect a drop-off.
Face-to-camera talking head can hold longer (7-8s) if the speaker is expressive.

#### Text Animation Timing

| Element | Duration On Screen | Entry Animation |
|---------|-------------------|-----------------|
| Hook text (0-3s) | 2-3 seconds | Pop-in or fade, timed to audio |
| Subtitle/caption text | Match spoken word duration + 0.5s buffer | Bottom-up or cut-in |
| Key stat or number | 2-3 seconds | Scale-up or highlight |
| CTA text (final) | Hold for remaining duration | Fade-in, then static |

Text must appear AFTER the spoken word starts (not before). Delay of 0.1-0.3s feels natural.
Text appearing before audio feels robotic.

#### Transition Types (ranked by general performance data)

| Transition | When to Use | Watch Time Impact |
|------------|-------------|-------------------|
| Jump cut (same angle) | Talking head, removing pauses | Neutral (expected) |
| Zoom punch-in | Emphasis on a point | +5-10% retention at that moment |
| Whip pan | Scene change, before/after | +10-15% if well-timed |
| Match cut (hand/object) | Transformation content | High virality signal |
| Cross-dissolve | Avoid. Reads as "slideshow" | Negative |
| Fade to black | Avoid for Reels. Only for cinematic long-form. | Negative |

### Forbidden Errors (tank reach immediately)

- Text or logo in unsafe zones (top 150px, bottom 350px, sides 70px)
- Watermarks from TikTok, CapCut, or other platforms (Instagram actively suppresses)
- Black bars / letterboxing: fill the full 9:16 frame, no exceptions
- Copyrighted music without licensing: use Meta Sound Collection or original audio
- Aspect ratio other than 9:16 for Reels placement
- Static image with music overlay (not a "Reel", gets suppressed)
- Recycled/re-uploaded content without meaningful changes

---

## Stories

### Technical Specs

| Property | Value |
|----------|-------|
| Aspect ratio | 9:16 vertical |
| Resolution | 1080 x 1920 px |
| Video duration | Up to 60 seconds per story slide |
| Image auto-advance | 7 seconds |
| Optimal slide count per session | 3-7 slides |
| File format | MP4, MOV (video), JPG, PNG (image) |
| Max file size | 4 GB (video), 8 MB (image) |

### Safe Zone Map

| Zone | Pixel Range | What Covers It |
|------|-------------|----------------|
| Top unsafe | Y: 0-250px | Profile picture, username, timestamp, mute button |
| Bottom unsafe | Y: 1620-1920px (300px) | Reply bar, "Send message" field, CTA button |
| Left unsafe | X: 0-70px | Edge tap zone (previous story) |
| Right unsafe | X: 1010-1080px | Edge tap zone (next story) |
| **Safe text area** | **X: 70-1010px, Y: 250-1620px** | **940 x 1370 px usable** |

```
Story Frame (1080 x 1920)
+----------------------------------+
|  UNSAFE: profile/time (250px)    |  <- Y: 0-250
|+--------------------------------+|
||                                ||
||    SAFE CONTENT AREA           ||
||    940 x 1370 px               ||
||                                ||
||    Y: 250-1620                 ||
||                                ||
|+--------------------------------+|
|  UNSAFE: reply bar (300px)       |  <- Y: 1620-1920
+----------------------------------+
```

### Interactive Elements

| Sticker Type | Engagement Effect | Best Use Case |
|-------------|-------------------|---------------|
| Poll | +23% retention vs non-interactive stories | Binary opinion ("Ja oder Nein?"), preference checks |
| Question | Replies count as DMs (algorithm boost) | Open-ended prompts, AMA, topic requests |
| Quiz | Educational fit, gamification | Teaching IF facts, myth-busting |
| Countdown | Creates anticipation, reminds users | Program launches, events, limited offers |
| Slider (emoji) | Low-friction engagement | Mood checks, intensity ratings |
| Link | Direct traffic (no swipe-up needed) | Blog posts, product pages, sign-ups |
| Add Yours | Chain engagement, community building | Challenges, meal pics, transformation shares |

### Content Mix for Stories

| Content Type | Percentage | Examples |
|-------------|-----------|----------|
| Educational / value | 70% | Quick IF tips, myth-busting, mini-tutorials |
| Behind-the-scenes / personal | 20% | Day-in-the-life, meal prep, personal moments |
| Product / promotional | 10% | Program launches, testimonials, offers |

Hard rule: max 1 story per day with direct product push. Promotional stories without
preceding value stories get skipped.

### Story Retention Rules

| Rule | Detail |
|------|--------|
| Slide 1 | Always the hook. Why should they keep watching? |
| Max words per slide | 15 words. More than that = tap-forward. |
| Text style | Large text, high contrast. White on dark background or colored text box. |
| Interactive cadence | Every 3rd slide: add a poll, quiz, question, or slider. |
| Last slide | Clear CTA: reply, tap link, DM keyword, or "save this". |
| Font size minimum | 24pt equivalent. If they cannot read it while walking, it is too small. |

---

## Carousels

### Technical Specs

| Property | Value |
|----------|-------|
| Slide count | 2-10 slides (10 is max) |
| Recommended aspect ratio | 4:5 (1080 x 1350 px) for maximum feed real estate |
| Alternative aspect ratio | 1:1 (1080 x 1080 px) |
| File format per slide | JPG or PNG |
| Max file size per slide | 8 MB |
| Video slides | Allowed (MP4/MOV, up to 60s per slide, mixed with images) |
| All slides same ratio | Yes, first slide sets the ratio for all subsequent slides |

### Carousel Algorithm Behavior

Carousels get shown TWICE by the Instagram algorithm:

1. First impression: shown normally starting on slide 1.
2. If user does not engage, shown again later starting on slide 2.

This effectively doubles the distribution opportunity. Because of this, slide 2 should
also work as a hook (not just slide 1).

Saves on carousels are weighted especially high. Instagram interprets saves as
"content worth returning to," which is the strongest positive signal for carousels.

### Cover Slide (Slide 1)

| Rule | Detail |
|------|--------|
| Hook style | Same rules as Reel hook: curiosity gap, pattern interrupt, identity trigger |
| Standalone | Must work as a standalone image even if user never swipes |
| Text | Large readable text, max 7-10 words, brand-consistent font and colors |
| Visual | Face or transformation visual outperforms abstract graphics |
| Grid appearance | Appears in profile grid. Design for both feed scroll and grid browse. |

### Slide 2 (Second Hook)

Because the algorithm re-shows carousels starting at slide 2, this slide must also
function as an entry point. Include a mini-hook or a bold statement that makes sense
without seeing slide 1.

### Slide Structure (proven pattern)

| Slide | Content |
|-------|---------|
| 1 | Hook: problem statement, bold claim, or curiosity trigger |
| 2-8 | Content: one idea per slide, delivering value |
| 9 | Reveal/transformation: the payoff, the result, the "aha" |
| 10 | CTA: "Speicher dir das", "Schick das jemanden der...", "Link in Bio" |

### Per-Slide Rules

| Rule | Detail |
|------|--------|
| One idea per slide | Never two concepts on one slide |
| Max words on slide | 15 words (details go in the caption) |
| Visual consistency | Same font, same color palette, same layout grid across all slides |
| Slide numbers | Optional but help retention ("3/10" tells users how much is left) |
| Progress indicator | Dots at bottom are automatic. Do not add fake dot indicators. |
| Readability | Sans-serif font, minimum 36pt equivalent, high contrast on background |

### Forbidden Errors (Carousels)

- Cover slide with no hook (looks like a random photo, gets scrolled past)
- Too much text per slide (more text = fewer swipes = lower distribution)
- Inconsistent visual style across slides (looks unprofessional, breaks trust)
- No CTA on the last slide (wasted opportunity on highest-intent viewers)
- Using 1:1 when 4:5 is available (loses 25% of feed real estate)

---

## Feed Posts (Single Image)

### Technical Specs

| Aspect Ratio | Resolution | Feed Real Estate | Recommendation |
|-------------|-----------|-----------------|----------------|
| 4:5 portrait | 1080 x 1350 px | Maximum | Recommended for most posts |
| 1:1 square | 1080 x 1080 px | Medium | OK for quotes, graphics |
| 1.91:1 landscape | 1080 x 566 px | Minimum | Avoid. Less scroll-stopping power. |

Format: JPG or PNG. Max file size: 8 MB.

### When to Use Single Feed Post

| Situation | Format |
|-----------|--------|
| One strong visual, quote, or transformation photo | Feed post |
| Educational multi-step content | Carousel instead |
| Behind-the-scenes single moment | Feed post |
| Before/after comparison | Carousel instead |
| Announcement or milestone | Feed post |
| Tutorial or how-to | Carousel or Reel instead |

### Feed Post Visual Rules

| Rule | Detail |
|------|--------|
| The image IS the hook | Must stop the scroll before the caption is even read |
| Face-forward + emotion | Outperforms product-only images by 30-50% on engagement |
| Text overlay on image | Max 1 line, large font, high contrast |
| Negative space | Leave breathing room. Cluttered images get scrolled past. |
| Brand consistency | Colors, fonts, and style should be recognizable as the account's brand |

### Caption as Content Vehicle

For feed posts, the caption carries the full content weight (unlike Reels where audio
carries content). Minimum 500+ characters.

Caption structure: Hook line > Body (value) > Line break > CTA.

See [Caption Display Rules](#caption-display-rules) for character truncation details.

---

## Instagram Live

### Technical Specs

| Property | Value |
|----------|-------|
| Aspect ratio | 9:16 vertical |
| Resolution | Up to 1080 x 1920 (depends on device/connection) |
| Duration | Up to 4 hours |
| Participants | Up to 4 (via Live Rooms) |
| Save to profile | Optional, saves as IGTV/Reel after ending |
| Scheduling | Can be scheduled up to 90 days in advance |

### When to Use Live

| Use Case | Why It Works |
|----------|-------------|
| Q&A sessions | Real-time interaction, builds community trust |
| Program launches | Creates urgency, allows live objection handling |
| Expert interviews | Collab exposure, adds authority |
| Behind-the-scenes | Authenticity, unpolished content performs well |
| Community events | Weekly check-ins, accountability sessions |

### Live Best Practices

| Rule | Detail |
|------|--------|
| Announce 24h ahead | Use countdown sticker in Stories to build audience |
| First 5 minutes | Wait for audience to join. Use casual intro, greet by name. |
| Pin a comment | Pin the topic/question at the top so late joiners understand context |
| CTA during live | Verbal + pinned comment. Repeat CTA every 10-15 minutes. |
| Save after | Save as Reel or long-form video. Live replay gets additional views. |
| Minimum duration | 15-20 minutes. Shorter lives do not build enough live audience. |

### Live Safe Zone

Same as Reels safe zone but with additional live-specific overlays:

| Element | Position |
|---------|----------|
| Viewer count + live badge | Top-left (Y: 0-100px) |
| Comment stream | Bottom 40% of screen (Y: 1150-1920px) |
| Share/request buttons | Bottom-right |
| **Safe for graphics/text** | **Center area: X: 100-980px, Y: 100-1100px** |

---

## Reels Remix

### How It Works

Remix places the original Reel alongside the new content, either side-by-side (split screen)
or as a picture-in-picture overlay. The remixer creates new content that reacts to, adds to,
or comments on the original.

### Technical Specs

| Property | Value |
|----------|-------|
| Aspect ratio (output) | 9:16 (same as standard Reel) |
| Layout options | Side-by-side (50/50 split), Green screen (original as background), Picture-in-picture |
| Duration | Matches original Reel duration or can be set shorter |
| Audio | Can use original audio, add new audio, or mix both |

### When to Use Remix

| Scenario | Example |
|----------|---------|
| React to trending content | Adding the creator's expert take on a viral claim |
| Duet with a client | Client shows transformation, the creator adds commentary |
| Debunk misinformation | Side-by-side with myth on left, facts on right |
| Before/after | Original shows "before," remix shows "after" |

### Remix Rules

- Only Remix content where the original creator has enabled Remixing.
- Always add meaningful value. Pure reaction without commentary is low-quality.
- Original audio plays on the left channel. Add new audio on the right or as voiceover.
- Credit the original creator in caption (tagging + verbal mention).

---

## Collab Posts

### How They Work

A Collab post appears on BOTH creators' profiles and shares engagement (likes, comments,
saves, shares) across both accounts. It is a single post with two authors.

### When to Use Collab Posts

| Scenario | Benefit |
|----------|---------|
| Expert interview clips | Tap into partner's audience |
| Joint programs or events | Shared promotion, shared credibility |
| Client transformations | Client gets visibility, the creator gets social proof |
| Cross-niche partnerships | Reach adjacent audiences (nutrition, mindset, women's health) |

### Collab Post Rules

| Rule | Detail |
|------|--------|
| Initiation | One creator publishes, invites the other as collaborator |
| Approval | Collaborator must accept before it appears on their profile |
| Engagement | All engagement is shared. Both profiles benefit equally. |
| Removal | Either creator can remove themselves from the collab at any time |
| Format | Works with Feed posts, Carousels, and Reels |
| Grid | Appears in both creators' grids |
| Limit | Max 1 collaborator per post (total 2 authors) |

### Partner Selection Criteria

- Similar or adjacent niche (overlapping audience interests)
- Audience overlap: shared region, demographics, or interest graph
- Minimum 10K followers (for meaningful reach exchange)
- Content quality and values alignment
- No direct product competitors

---

## Audio Strategy

### When to Use Each Audio Type

| Audio Type | When to Use | Performance Impact |
|-----------|-------------|-------------------|
| Trending sound | Hook-style Reels, trend participation, discovery plays | +30-60% reach via Explore/Reels tab |
| Original voiceover | Educational content, personal stories, expertise positioning | +20% completion rate (unique content) |
| Original sound (ambient) | BTS, day-in-the-life, authentic moments | Neutral reach, high authenticity signal |
| Music only (no voice) | Text-overlay Reels, transformation montages | Lower completion if no voice; use trending music |
| Meta Sound Collection | When trending sounds do not fit; safe copyright option | Neutral, no discovery boost |

### Trending Sound Rules

| Rule | Detail |
|------|--------|
| Timing | Use within first 3-7 days of trend emergence. After 14 days, it is stale. |
| Adaptation | Always adapt to niche. Never force a trend that does not fit IF/fitness. |
| Volume | Trending sound can be at 20-30% volume with voiceover at 100%. |
| Discovery | Browse Reels tab, check audio page for "trending" arrow icon. |
| Save for later | Tap the audio name on any Reel, then "Save Audio" for later use. |

### Original Voiceover Best Practices

| Rule | Detail |
|------|--------|
| First word at 0.5s | Do not start with silence. The hook begins immediately. |
| Speaking pace | 140-160 words per minute (conversational, not rushed) |
| Background music | At 15-25% volume under voiceover. Never competing. |
| Mic quality | External mic or quiet room. Background noise kills retention. |
| Language | German for DACH audience. English only if topic is globally relevant. |

---

## Caption Display Rules

Instagram truncates captions in the feed. The number of characters visible before the
"more" button depends on the format and context.

### Characters Visible Before Truncation

| Context | Characters Shown | Lines Shown |
|---------|-----------------|-------------|
| Feed (home) post caption | ~125 characters | ~2 lines |
| Feed Reel caption | ~90 characters | ~1-2 lines |
| Carousel caption | ~125 characters | ~2 lines |
| Reel in Reels tab | ~55 characters | ~1 line |
| Profile grid (tapped) | Full caption visible | All |
| Explore page | ~80 characters | ~1 line |

### Caption Strategy by Format

| Format | Caption Role | Recommended Length |
|--------|-------------|-------------------|
| Reel | Supporting (audio carries content) | 150-500 characters |
| Carousel | Complementary (slides carry main content) | 300-800 characters |
| Feed post | Primary (caption IS the content) | 500-2200 characters |
| Story | Not applicable (no persistent caption) | N/A |

### Hook Line Rules

Because only 90-125 characters show before truncation, the first line must be
a standalone hook that compels the tap on "more."

Effective patterns:
- Question: "Machst du diesen IF-Fehler auch?" (39 chars)
- Bold claim: "16:8 ist nicht der beste IF-Rhythmus." (38 chars)
- Number + promise: "3 Dinge die ich mit 45 anders mache." (37 chars)
- Identity trigger: "Frauen ab 40: Das solltet ihr wissen." (38 chars)

---

## Instagram SEO

Instagram is increasingly functioning as a search engine. Optimizing for search
means content appears in Explore, Search results, and suggested content.

### Keyword Placement Priority

| Location | SEO Weight | Example |
|----------|-----------|---------|
| Username | Highest | @[your-handle] (name recognition) |
| Display name | Very high | "[Creator Name - Niche Keyword]" |
| Caption (first 2 lines) | High | Include primary keyword naturally |
| Caption body | Medium | Use related keywords and synonyms |
| Hashtags (in caption) | Medium | 3-5 targeted hashtags, not 30 generic ones |
| Alt text | Medium-high | Describe the image content with keywords |
| Reel on-screen text | Medium | Instagram OCRs text overlays |
| Audio transcript | Low-medium | Instagram transcribes spoken words |

### Alt Text Best Practices

| Rule | Detail |
|------|--------|
| Always write custom alt text | Do not rely on auto-generated alt text |
| Describe the image content | "Frau beim Intervallfasten Meal Prep mit Gemuse und Reis" |
| Include keywords naturally | Do not keyword-stuff. Describe what is actually shown. |
| Max length | ~100 characters for best indexing |
| Access | Edit post > Advanced settings > Write alt text |

### Hashtag Strategy (2026)

| Count | Type | Examples |
|-------|------|----------|
| 1-2 | Niche-specific, high intent | #intervallfasten #intermittentfasting |
| 1-2 | Audience-specific | #frauenab40 #wechseljahre |
| 1 | Brand | #yourbrand or #yourhandle |
| Total | 3-5 hashtags | More than 5 adds no value and can look spammy |

Place hashtags at the end of the caption or in the first comment. Both work equally
for discoverability as of 2026.

---

## Grid Aesthetic and Profile Strategy

### How Formats Appear in the Profile Grid

| Format | Grid Thumbnail | Crop Behavior |
|--------|---------------|---------------|
| Reel (9:16) | Center-cropped to 1:1 square | Middle 1080x1080 of 1080x1920 frame. Top 420px and bottom 420px are cut. |
| Carousel (4:5) | First slide, center-cropped to 1:1 | Top 135px and bottom 135px are cut from 1080x1350. |
| Carousel (1:1) | First slide, shown as-is | No crop. |
| Feed post (4:5) | Center-cropped to 1:1 | Same as carousel 4:5. |
| Feed post (1:1) | Shown as-is | No crop. |
| IGTV / Live replay | Center-cropped to 1:1 | Same as Reel behavior. |

### Grid Design Implications

For Reels: the profile grid only shows the CENTER 1080x1080 pixels of the 9:16 frame.
This means the top 420px and bottom 420px are invisible in the grid. Design custom
thumbnails with the key visual (face, text) in the center square.

For 4:5 content: the top and bottom 135px each are cropped. Keep essential text and
visuals within the center 1080x1080 area.

### Grid Aesthetic Rules

| Rule | Detail |
|------|--------|
| Visual consistency | Consistent color palette, similar editing style, recognizable brand |
| Row planning | Optional: plan posts in rows of 3 for visual patterns |
| Alternation | Mix content types (Reel, Carousel, Photo) for visual variety |
| No all-text grid | Text-heavy graphics every post makes the grid look like a blog, not a person |
| Face frequency | At least 1 in 3 grid thumbnails should show the creator's face |

---

## Pinned Posts Strategy

Instagram allows pinning up to 3 posts at the top of the profile grid. These are the
first posts a profile visitor sees.

### Optimal Pinned Post Configuration

| Position | Content Type | Purpose |
|----------|-------------|---------|
| Pin 1 (leftmost) | Best-performing Reel or Carousel | Social proof: shows what content looks like at its best |
| Pin 2 (center) | Intro/origin story or value Reel | Who is the creator? Why follow? First-visitor conversion. |
| Pin 3 (rightmost) | Current program or offer Carousel | Funnel entry: what can followers buy or join? |

### Pinned Post Rules

| Rule | Detail |
|------|--------|
| Update frequency | Review monthly. Replace underperformers. |
| Performance threshold | Only pin posts with above-average save rate or engagement |
| Current offer | Always keep one pinned post for the current program/offer |
| Evergreen | At least one pinned post should be evergreen (not time-bound) |
| CTA | Every pinned post must have a clear CTA in the caption |

---

## Story Highlights

### Organization Strategy

| Highlight | Content | Cover Color/Style |
|-----------|---------|-------------------|
| Start hier | Who is the creator, what is the brand, how to follow along | Brand primary color |
| IF Basics | Foundational intermittent fasting knowledge | Educational icon |
| Rezepte | Recipe stories, meal prep ideas | Food-related icon |
| Erfahrungen | Client testimonials, transformations | Social proof icon |
| Programm | Current program info, pricing, sign-up links | CTA-colored cover |
| Q&A | Saved question sticker responses | Question mark icon |

### Highlight Cover Design Rules

| Rule | Detail |
|------|--------|
| Consistent style | All covers use same design template (icon on solid background) |
| Brand colors | Use account brand palette for cover backgrounds |
| Icon style | Simple, recognizable icons. Not photos. |
| Resolution | 1080 x 1920 (Instagram crops to circle from center) |
| Center the icon | The visible circle is approximately center 640x640 of the 1080x1920 frame |
| Max highlights shown | 5-7 visible without scrolling on most devices. Prioritize accordingly. |

### Highlight Maintenance

- Remove stories older than 6 months unless evergreen.
- Move outdated promotional stories to Archive.
- Keep "Start hier" and "IF Basics" permanently updated.
- After each program launch: update "Programm" highlight.

---

## Format Selection Decision Tree

Use this decision tree to determine which format to use for a given content idea.

### Step 1: What is the content goal?

| Goal | Recommended Format |
|------|-------------------|
| Reach new audience (discovery) | Reel |
| Educate existing followers (depth) | Carousel |
| Drive immediate action (urgency) | Story |
| Build trust (personal connection) | Reel (face-to-camera) or Live |
| Sell a product or program | Story (with link) + Carousel (for proof) |
| Social proof (transformation) | Carousel or Collab Reel |

### Step 2: What is the content type?

| Content Type | Best Format | Second Choice |
|-------------|-------------|---------------|
| Quick tip (under 30s to explain) | Reel | Story |
| Detailed tutorial (3+ steps) | Carousel | Reel (30-60s) |
| Personal story or opinion | Reel (face-to-camera) | Feed post |
| Client transformation | Carousel (before/after) | Collab Reel |
| Myth debunking | Reel | Carousel |
| Meal / recipe | Reel (process video) | Carousel (step photos) |
| Announcement | Story + Feed post | Story + Reel |
| Q&A | Story (question sticker) | Live |
| Behind the scenes | Story | Reel |
| Trending audio/topic | Reel | N/A |
| Evergreen reference content | Carousel | Feed post |
| Time-sensitive offer | Story | Feed post |
| Community engagement | Story (poll/quiz) | Live |

### Step 3: Posting Frequency by Format

| Format | Recommended Frequency |
|--------|----------------------|
| Reels | 3-5 per week |
| Carousels | 1-3 per week |
| Stories | Daily (3-7 slides per session) |
| Feed posts | 0-2 per week |
| Lives | 1-2 per month |
| Collab posts | 1-2 per month |

---

## Performance Signals: Quick Reference

| Signal | Below This = Problem | Average | Good | Excellent |
|--------|---------------------|---------|------|-----------|
| Save rate | < 1% | 1-3% | 3-5% | > 5% |
| Reel avg watch time | < 10s | 10-16s | 17-22s | > 25s |
| Completion rate | < 40% | 40-59% | 60-70% | > 75% |
| Share/reach ratio | < 1% | 1-2% | 2-3% | > 5% |
| DM sends/reach | < 0.2% | 0.2-0.5% | 0.5-1% | > 1.5% |
| Comments/reach | < 0.1% | 0.1-0.3% | 0.3-0.5% | > 1% |
| Profile visits/reach | < 0.5% | 0.5-1% | 1-2% | > 3% |
| Follows/reach | < 0.1% | 0.1-0.3% | 0.3-0.5% | > 1% |

These are baseline targets. Calibrate against account-baseline.md after each
API data pull. Thresholds shift with audience size and content type.

### Signal Priority by Format

| Format | Primary Signal | Secondary Signal | Tertiary Signal |
|--------|---------------|-----------------|-----------------|
| Reel | Watch time + completion | Saves | Shares |
| Carousel | Saves | Swipe-through rate | Comments |
| Feed post | Comments | Saves | Profile visits |
| Story | Reply rate + sticker taps | Completion (no skip) | Link taps |
| Live | Peak concurrent viewers | Comments during live | Replay views |

---

## Universal Forbidden Errors

These errors apply across ALL formats and will tank reach or violate platform rules.

| Error | Impact | Applies To |
|-------|--------|-----------|
| TikTok / CapCut watermark | Instagram suppresses distribution | Reels |
| Black bars / letterboxing | Signals repurposed or lazy content | Reels, Stories |
| Copyrighted music | Muted audio or content removal | Reels, Stories |
| Text in unsafe zones | Content unreadable, unprofessional | All video/image formats |
| Wrong aspect ratio | Cropping, black bars, lost real estate | All formats |
| Static image uploaded as Reel | Gets classified as low-effort | Reels |
| Engagement bait ("Like if you agree") | Reduced distribution per Meta policy | All formats |
| Pods or engagement groups | Account-level penalty if detected | All formats |
| Excessive hashtags (30) | Spam signal since 2024 algorithm update | Feed, Carousel |
| Broken link in bio during Story CTA | Wasted traffic, poor user experience | Stories |
| Re-uploading same content | Duplicate content suppression | All formats |
| Posting and deleting repeatedly | Signals to algorithm that content is low quality | All formats |
