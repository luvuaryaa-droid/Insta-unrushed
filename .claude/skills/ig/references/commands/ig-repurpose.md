---
name: ig-repurpose
description: >
  Cross-platform content repurposing from Instagram to TikTok, YouTube Shorts,
  LinkedIn, Email Newsletter, and Blog. Adapts format, aspect ratio, duration,
  tone, and CTA per platform while preserving core message.
allowed-tools:
  - Read
  - Write
  - Grep
  - Glob
---

# IG Repurpose -- Cross-platform content repurposing

**Key references:**
- `references/repurpose-playbook.md` -- platform-specific rules, adaptation patterns, timing offsets
- `references/format-specs.md` -- Instagram format specs (source format reference)
- `references/content-rules.md` -- brand voice baseline for adaptation

---

## Phase 1: Source Analysis

Identify and analyze the Instagram post to repurpose:

1. **Post identification:** Get the post URL, ID, or description from the user.
2. **Content extraction:** Document the following from the source post:
   - Format (Reel, Carousel, Single Image, Story)
   - Duration (if video)
   - Caption (full text)
   - Hook (first 3 seconds or cover slide)
   - Core message (one sentence summary)
   - CTA (what action was requested)
   - Performance data (if available: engagement rate, saves, shares)
   - Visual assets list (clips, images, graphics)

3. **Repurpose potential assessment:**
   - Is the content evergreen or time-sensitive?
   - Is it platform-specific (e.g., uses IG-only features like polls)?
   - Does it contain affiliate content (disclosure rules change per platform)?
   - How well did it perform on Instagram? (high performers repurpose best)

4. Ask the user which target platforms to repurpose for, or suggest based on content type.

## Phase 2: Platform Adaptation

Apply platform-specific rules for each target:

### TikTok
| Dimension | Rule |
|-----------|------|
| Aspect Ratio | 9:16 (same as Reels) |
| Duration | 15-60s optimal (shorter than IG Reels) |
| Hook | Must be faster. First 1 second, not 3. |
| Text Overlays | Larger, more frequent. TikTok audience skims faster. |
| Audio | Replace IG audio with trending TikTok sound if possible |
| Caption | Shorter (max 150 chars for visibility). Hashtags: 3-5 niche. |
| CTA | "Folgen fuer mehr" or "Teil 2?" (TikTok rewards follow CTAs) |
| Posting Delay | Post 24-48 hours AFTER Instagram (IG gets priority) |
| Watermark | REMOVE any Instagram watermark before posting to TikTok |

### YouTube Shorts
| Dimension | Rule |
|-----------|------|
| Aspect Ratio | 9:16 |
| Duration | 30-60s optimal (YouTube rewards slightly longer Shorts) |
| Hook | Same as IG, but add a title card in first frame |
| Text Overlays | Standard size, YouTube compresses less than TikTok |
| Audio | Original audio preferred (YouTube values original content) |
| Caption | Title: max 100 chars with keyword. Description: full IG caption adapted. |
| CTA | "Abonnieren" or comment prompt (YouTube values watch time + comments) |
| Posting Delay | Post 48-72 hours after Instagram |
| SEO | Add 3-5 relevant keywords in title and description |

### LinkedIn
| Dimension | Rule |
|-----------|------|
| Format | Convert to text post with image, or native video (1:1 or 16:9) |
| Tone | Professional but personal. Remove casual slang, keep vulnerability. |
| Hook | LinkedIn hook = first 2 lines before "...mehr anzeigen". Must earn the click. |
| Length | 800-1500 characters for text posts |
| Structure | Short paragraphs (1-2 sentences each), line breaks between. |
| CTA | "Was ist eure Erfahrung?" or thought-provoking question |
| Hashtags | 3-5 professional hashtags (#Fitness, #Ernaehrung, #Gesundheit) |
| Language | Can be German or English depending on audience. Ask user. |
| Posting Delay | Post 3-7 days after Instagram (different audience cycle) |

### Email Newsletter
| Dimension | Rule |
|-----------|------|
| Format | Text-based with 1-2 images maximum |
| Tone | More intimate than social media. Direct "du" address. |
| Hook | Subject line = adapted IG hook (curiosity gap or benefit) |
| Length | 300-500 words |
| Structure | Hook > Story/Context > Key Insight > CTA |
| CTA | Link to product, reply prompt, or forward prompt |
| Personalization | Reference subscriber relationship ("Als Teil der Community...") |
| Images | Use 1 key image from the IG post, not the full carousel |
| Timing | Send within 7 days of IG post while topic is fresh |

### Blog Post
| Dimension | Rule |
|-----------|------|
| Format | Long-form article (800-1500 words) |
| Tone | Educational, authoritative, still personal |
| Structure | H2 sections expanding on each carousel slide or reel segment |
| SEO | Target 1 primary keyword, 3-5 secondary keywords |
| Hook | Blog title = SEO-optimized version of IG hook |
| CTA | Internal links to related content, email signup, or product |
| Images | Repurpose IG visuals with alt text for SEO |
| Timing | Publish within 14 days of IG post |

## Phase 3: Format Conversion

For each target platform, specify technical conversion needs:

### Video Conversions
- Source aspect ratio > target aspect ratio (crop/reframe if needed)
- Duration adjustments (trim, cut, or extend)
- Audio replacement or retention
- Watermark removal
- Text overlay repositioning (safe zones differ per platform)
- Export settings (resolution, bitrate, format)

### Image Conversions
- Resize for platform optimal dimensions
- Text overlay adjustments for readability at platform-native size
- Color profile check (sRGB for web)

### Text Conversions
- Caption adaptation (length, tone, structure)
- Hashtag strategy per platform
- CTA adaptation
- SEO optimization (for blog and YouTube)

## Phase 4: Voice Adaptation

Adjust the brand voice for each platform while keeping core identity:

| Platform | Voice Adjustment |
|----------|-----------------|
| TikTok | More casual, faster paced, trend-aware. "Alter, DAS musst du wissen" |
| YouTube Shorts | Slightly more informative, keyword-conscious. "In 60 Sekunden erklaert" |
| LinkedIn | Professional-personal hybrid. Drop fitness slang, keep personal stories. |
| Newsletter | Most intimate. Like writing to a friend. "Hey, ich wollte dir was erzaehlen" |
| Blog | Most authoritative. Backed by sources, structured, SEO-friendly. |

### Voice Rules Per Platform
- NEVER copy-paste the IG caption to another platform unchanged
- Each platform version must feel native to that platform
- Core message stays the same, delivery changes
- Humor and casual tone scale: TikTok > IG > Newsletter > YouTube > LinkedIn > Blog

## Phase 5: Quality Check

For each platform adaptation, verify:

- [ ] Format matches platform specifications (aspect ratio, duration, dimensions)
- [ ] Hook is adapted for platform-specific consumption patterns
- [ ] Tone matches platform expectations (not too casual for LinkedIn, not too formal for TikTok)
- [ ] CTA is platform-appropriate
- [ ] No Instagram-specific references left ("Link in Bio" on LinkedIn, etc.)
- [ ] Affiliate disclosures adapted for platform-specific requirements (if applicable)
- [ ] Posting delay schedule is set (IG gets priority)
- [ ] No watermarks from source platform

## Phase 6: Delivery

Output per-platform briefs:

```
## Repurpose Brief

**Source Post:** [IG post reference]
**Source Format:** [Reel/Carousel/Image]
**Source Performance:** [engagement rate, saves, shares]
**Target Platforms:** [list]

---

### TikTok Version
**Format:** [video specs]
**Duration:** [adjusted duration]
**Hook:** "[adapted hook]"
**Caption:** "[full adapted caption]"
**Audio:** [original / trending sound suggestion]
**CTA:** "[platform CTA]"
**Post Date:** [date, 24-48h after IG]
**Technical Notes:** [crop, trim, watermark removal]

---

### LinkedIn Version
**Format:** [text + image / video]
**Hook (first 2 lines):** "[adapted hook]"
**Body:** "[full adapted text]"
**CTA:** "[platform CTA]"
**Hashtags:** [list]
**Post Date:** [date, 3-7 days after IG]

---

[Repeat for each target platform]

### Production Checklist
- [ ] Video re-exported at correct specs per platform
- [ ] Watermarks removed
- [ ] Text overlays repositioned for safe zones
- [ ] Captions written and reviewed per platform
- [ ] Posting schedule set with correct delays
```
