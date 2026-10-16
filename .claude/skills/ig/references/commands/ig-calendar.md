---
name: ig-calendar
description: >
  Generate editorial content calendars for Instagram. Validates content mix
  against targets, spaces affiliate content correctly, and outputs weekly
  or monthly plans with format, topic, hook category, and posting schedule.
allowed-tools:
  - Read
  - Write
  - Grep
  - Glob
---

# IG Calendar -- Editorial content calendar generation

**Key references:**
- `references/account-baseline.md` -- current content mix, posting frequency, audience activity times
- `references/content-rules.md` -- content pillars, banned topics, voice guidelines
- `references/affiliate-compliance.md` -- affiliate spacing rules, partner rotation, disclosure requirements

---

## Phase 1: Baseline Review

1. Load `references/account-baseline.md` to understand the current state:
   - Current posting frequency (posts per week)
   - Content type distribution (reels vs carousels vs single images)
   - Content pillar distribution (educational, personal, promotional, entertaining)
   - Best-performing days and times
   - Recent topics covered (to avoid repetition)

2. Load `references/content-rules.md` for:
   - Allowed content pillars and their target percentages
   - Banned topics and claims
   - Voice and tone guidelines

3. Load `references/affiliate-compliance.md` for:
   - Active affiliate partners
   - Spacing rules (max frequency, consecutive day restrictions)
   - Disclosure requirements

4. Ask the user for calendar scope:
   - Weekly (7 days) or monthly (28-31 days)?
   - Any specific campaigns, launches, or events to include?
   - Any topics to prioritize or avoid this period?

## Phase 2: Mix Validation

Before generating the calendar, validate the target content mix:

### Content Type Targets
| Format | Target % | Min/Week (5 posts) | Min/Week (7 posts) |
|--------|----------|--------------------|--------------------|
| Reels | 50-60% | 3 | 4 |
| Carousels | 25-35% | 1-2 | 2 |
| Single Image | 10-15% | 0-1 | 1 |
| Stories | Daily | 1-3 sequences | 1-3 sequences |

### Content Pillar Targets
| Pillar | Target % | Description |
|--------|----------|-------------|
| Educational | 40% | Tips, how-tos, myth-busting, science |
| Personal / Behind-the-Scenes | 25% | Day-in-the-life, struggles, wins |
| Community / Engagement | 20% | Polls, Q&A, user stories, challenges |
| Promotional | 15% | Products, programs, affiliate, launches |

If the user's requirements would violate these targets, flag it and suggest adjustments.

## Phase 3: Calendar Generation

Build the calendar with these fields per post:

| Field | Description |
|-------|-------------|
| Date | Posting date (day of week + date) |
| Time | Optimal posting time (from baseline data) |
| Format | Reel, Carousel, Single Image, or Story |
| Pillar | Educational, Personal, Community, Promotional |
| Topic | Specific topic description |
| Hook Category | From hook-library.md (contrarian, numbered list, question, etc.) |
| CTA Type | Save, Share, Comment, DM, Follow, or Link |
| Notes | Production notes, asset needs, or campaign tie-in |

### Calendar Rules
- No two posts of the same format on consecutive days
- Alternate between content pillars (never 3 educational posts in a row)
- Vary hook categories across the week
- Place highest-effort content (reels) on best-performing days
- Include at least one community/engagement post per week
- Stories should complement but not duplicate feed posts

### Topic Selection
Draw topics from content pillars. Ensure:
- No topic is repeated within the same week
- Seasonal or timely topics are placed on appropriate dates
- Educational topics build on each other when possible (series potential)

## Phase 4: Affiliate Spacing Check

If the calendar includes affiliate or sponsored content:

1. **Max 2 affiliate posts per week.** If exceeded, remove or reschedule.
2. **Never on consecutive days.** Minimum 2 non-affiliate posts between affiliate posts.
3. **Partner rotation.** Do not feature the same partner more than once per week.
4. **Disclosure placement.** Every affiliate post must have "Werbung" or "Anzeige" noted in the plan.

Run through the calendar and flag any violations. Fix before delivery.

## Phase 5: Quality Check

Validate the completed calendar:

- [ ] Content type distribution matches targets (within 10% tolerance)
- [ ] Content pillar distribution matches targets (within 10% tolerance)
- [ ] No consecutive same-format posts
- [ ] No consecutive same-pillar posts (max 2)
- [ ] Affiliate spacing rules are met
- [ ] Every post has a defined hook category
- [ ] Every post has a defined CTA type
- [ ] Best-performing days have the strongest content
- [ ] No banned topics or claims in any post plan
- [ ] Total post count matches target frequency

## Phase 6: Delivery

Output as a structured Markdown calendar:

```
## Content Calendar: [Week/Month of DATE]

**Posts planned:** [count]
**Content mix:** [X reels, Y carousels, Z images]
**Pillar mix:** [X% edu, Y% personal, Z% community, W% promo]

### Week [N]

| Day | Date | Time | Format | Pillar | Topic | Hook | CTA |
|-----|------|------|--------|--------|-------|------|-----|
| Mo | DD.MM | HH:MM | Reel | Educational | [topic] | Contrarian | Save |
| Di | DD.MM | HH:MM | Carousel | Personal | [topic] | Story | Share |
| Mi | DD.MM | HH:MM | Story | Community | [topic] | Question | DM |
| Do | DD.MM | HH:MM | Reel | Educational | [topic] | Numbered | Save |
| Fr | DD.MM | HH:MM | Single | Promotional | [topic] | Bold Claim | Link |
| Sa | DD.MM | -- | -- | -- | Rest day | -- | -- |
| So | DD.MM | HH:MM | Reel | Personal | [topic] | Behind-Scenes | Comment |

### Story Plan
| Day | Topic | Type | Interactive Element |
|-----|-------|------|-------------------|

### Notes
- [campaign tie-ins, asset preparation deadlines, etc.]
```

If the user requests a monthly calendar, repeat the weekly structure for each week and add a monthly summary at the top.
