# Conversion Pipeline: ManyChat, UTM, DM Automation

End-to-end conversion architecture from Instagram content to product purchase.

## Funnel Overview

```
Instagram Content (Reel/Story/Carousel)
    |
    v
Comment Keyword Trigger (e.g., "GUIDE")
    |
    v
ManyChat Auto-DM (delivers link + value)
    |
    v
Landing Page (with UTM tracking)
    |
    v
Email Capture / Direct Purchase
    |
    v
Email Nurture Sequence (optional)
    |
    v
Product Purchase / Coaching Signup
```

## ManyChat Integration

### How It Works

1. User comments a keyword on a post (e.g., "GUIDE")
2. ManyChat detects the keyword and sends an automated DM
3. DM contains a personalized message + trackable link
4. User clicks link, lands on page with UTM parameters
5. Conversion tracked via UTM in analytics

### Keyword Trigger Rules

| Rule | Details |
|------|---------|
| Format | ALL CAPS, single word, easy to spell |
| Uniqueness | One keyword per active campaign. Never reuse across concurrent campaigns. |
| Simplicity | Max 8 characters. Avoid special characters or umlauts. |
| Mention frequency | Say keyword in video + write in caption + pin in comments |
| Response time | ManyChat should respond within 60 seconds |

### Keyword Examples by Campaign Type

| Campaign | Keyword | What Gets Delivered |
|----------|---------|-------------------|
| Free BodyGuide sample | GUIDE | PDF preview + signup link |
| Waitlist for new program | START | Waitlist form link |
| Free recipe collection | REZEPT | Recipe PDF download |
| Challenge signup | CHALLENGE | Challenge info + registration |
| Consultation booking | TERMIN | Booking calendar link |
| Generic lead magnet | GRATIS | Current lead magnet |

### ManyChat DM Templates

#### Freebie Delivery Flow
```
Message 1 (immediate):
"Hey [Name]! 💪 Mega, dass du dabei sein willst.

Hier ist dein [Freebie-Name]: [LINK]

Kurze Frage: Was ist gerade dein groesstes Ziel beim Training?"

Message 2 (24h later, if no click):
"Ich wollte sichergehen, dass du deinen [Freebie-Name] bekommen hast.
Falls du Fragen hast, schreib mir einfach hier. 🤍"
```

#### Waitlist Signup Flow
```
Message 1 (immediate):
"Hey [Name]! Schoen, dass du Interesse hast. 🤍

[Programmname] startet am [Datum].

Trag dich hier auf die Warteliste ein und sichere dir [Vorteil]: [LINK]"

Message 2 (48h before launch):
"[Name], morgen geht's los! Hast du dich schon eingetragen?
Die Plaetze sind begrenzt: [LINK]"
```

#### Product Launch Flow
```
Message 1 (immediate):
"Hey [Name]! Danke fuer dein Interesse an [Produkt]. 🔥

Hier findest du alle Infos: [LINK]

Falls du Fragen hast, schreib mir einfach."

Message 2 (if clicked but not purchased, 48h):
"Hey [Name], ich hab gesehen, dass du dir [Produkt] angeschaut hast.
Gibt's noch offene Fragen? Ich helfe gerne. 🤍"
```

### ManyChat Best Practices

| Practice | Why |
|----------|-----|
| Always include the person's name | Feels personal, not automated |
| Keep first message under 500 characters | Long DMs feel spammy |
| Include only ONE link per message | Multiple links = decision paralysis |
| Add a question at the end | Turns automation into conversation |
| Set up "no keyword match" fallback | Catches typos and general inquiries |
| Exclude existing customers from campaigns | Prevents annoying loyal followers |

## UTM Structure

### Standard UTM Parameters

All links from Instagram must include UTM parameters for tracking:

```
https://[yourdomain.com]/[page]?utm_source=instagram&utm_medium=[medium]&utm_campaign=[campaign]&utm_content=[content]
```

| Parameter | Value | Example |
|-----------|-------|---------|
| `utm_source` | Always `instagram` | `utm_source=instagram` |
| `utm_medium` | Content type | `organic`, `story`, `dm`, `bio` |
| `utm_campaign` | Campaign name | `bodyguide-launch-2026`, `freebie-trainingsplan` |
| `utm_content` | Specific post/variant | `reel-krafttraining-fehler`, `story-poll-ernaehrung` |

### UTM by Channel

| Channel | utm_medium | utm_content Pattern |
|---------|-----------|-------------------|
| Reel caption (link in bio reference) | `organic` | `reel-[topic-slug]` |
| Story link sticker | `story` | `story-[date]-[topic]` |
| ManyChat DM | `dm` | `dm-[keyword]-[date]` |
| Link in Bio (persistent) | `bio` | `bio-[page-name]` |
| Paid promotion | `paid` | `ad-[campaign-name]` |

### UTM Tracking Dashboard

Track these metrics weekly:

| Metric | Target | Source |
|--------|--------|--------|
| Click-through rate (Story link sticker) | >3% of story viewers | Instagram Insights |
| DM-to-click rate (ManyChat) | >60% of DMs sent | ManyChat analytics |
| Click-to-signup rate (Landing page) | >25% of clicks | Google Analytics / UTM |
| Signup-to-purchase rate | >5% (cold), >15% (warm) | Email/CRM |

## Link in Bio Strategy

### Recommended Setup

Use a custom landing page (not Linktree) for maximum control and tracking:

| Element | Details |
|---------|---------|
| Platform | Custom page on [yourdomain.com] (preferred) or Linktree Pro |
| Top link | Current campaign / launch (rotated frequently) |
| Persistent links | BodyGuide, Coaching, Free Resource, Podcast/Blog |
| Design | Matches account brand (match colors from brand guidelines) |
| Tracking | Every link has UTM parameters |
| Update frequency | Weekly (align with content calendar) |

### Link Hierarchy

| Position | Link Type | Why |
|----------|-----------|-----|
| 1 (top) | Current campaign / time-sensitive offer | Highest visibility, catches impulse clicks |
| 2 | Evergreen lead magnet (free resource) | Captures emails from new followers |
| 3 | Main product (BodyGuide / Coaching) | Always available for purchase-ready visitors |
| 4 | Community / Podcast / Blog | Deepens relationship for not-yet-ready leads |
| 5 (bottom) | Contact / FAQ | Catches support inquiries |

## Story Link Sticker Tracking

| Best Practice | Details |
|--------------|---------|
| Placement | Lower third of screen, above safe zone (not bottom 20%) |
| CTA text | Custom text, not default "Learn more" (e.g., "Zum Trainingsplan") |
| Frequency | Max 1 link sticker per 5 story slides (overuse = perceived as pushy) |
| UTM | Always include full UTM string |
| Tracking | Compare click rate across different CTA texts and placements |

## Product Funnel Architecture

### Cold Audience (New Followers)

```
Free Content (Reels) -> value, trust, expertise
    |
    v
Lead Magnet (ManyChat DM) -> email capture
    |
    v
Email Welcome Sequence (3-5 emails) -> education + soft pitch
    |
    v
Tripwire Offer (low-price product) -> BodyGuide or mini-course
    |
    v
Core Offer (Coaching / Program) -> full price, high commitment
```

### Warm Audience (Existing Followers)

```
Story Poll / Question -> engagement + segmentation
    |
    v
DM Conversation (manual or ManyChat) -> needs assessment
    |
    v
Direct Offer (product link) -> targeted pitch
    |
    v
Testimonial Follow-up -> social proof reinforcement
```

## Conversion Benchmarks

| Stage | Metric | Poor | Average | Good | Excellent |
|-------|--------|------|---------|------|-----------|
| Reel to Comment | Comment rate | <0.5% | 0.5-1% | 1-3% | >3% |
| Comment to DM delivery | ManyChat trigger rate | <70% | 70-85% | 85-95% | >95% |
| DM to Click | Click-through rate | <30% | 30-50% | 50-70% | >70% |
| Click to Signup | Conversion rate | <10% | 10-20% | 20-35% | >35% |
| Signup to Purchase | Sales conversion | <2% | 2-5% | 5-10% | >10% |
| End-to-end | Viewer to Customer | <0.01% | 0.01-0.05% | 0.05-0.1% | >0.1% |

## Automation Maintenance

| Task | Frequency | Details |
|------|-----------|---------|
| Check ManyChat delivery rates | Weekly | Ensure DMs are being delivered (Instagram can throttle) |
| Update keywords for new campaigns | Per campaign | Deactivate old keywords, activate new ones |
| Review UTM data in analytics | Weekly | Identify highest-converting content types |
| Test all links | Bi-weekly | Click every link in bio and ManyChat flows |
| Clean up expired campaigns | Monthly | Archive old ManyChat flows, update link in bio |
| Review DM conversation quality | Monthly | Read sample DM threads, improve templates |
