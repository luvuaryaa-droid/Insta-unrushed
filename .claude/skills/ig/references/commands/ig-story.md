---
name: ig-story
description: >
  Plan and structure Instagram Story sequences. Selects the right story type,
  builds a slide sequence with text overlays and interactive elements, and
  delivers a ready-to-produce story brief.
allowed-tools:
  - Read
  - Write
  - Grep
  - Glob
---

# IG Story -- Plan engaging Instagram Story sequences

**Key references:**
- `references/format-specs.md` -- dimensions, duration limits, safe zones
- `references/content-rules.md` -- brand voice, banned topics, caption rules
- `references/story-strategy.md` -- story arc patterns, frequency targets, sticker usage

---

## Phase 1: Context

1. Ask the user for the story goal (one of: educate, engage, sell, entertain, build trust).
2. Confirm the topic or product to feature.
3. If a specific date or campaign is mentioned, note any calendar constraints.
4. Load all key reference files listed above before proceeding.

## Phase 2: Story Type Selection

Select **one** primary story type based on the goal:

| Goal | Story Type | Characteristics |
|------|-----------|-----------------|
| Educate | Educational | Tip sequence, "Wusstest du...?" opener, text-heavy slides |
| Engage | Poll / Quiz | Interactive stickers, opinion-based, low friction |
| Sell | Product Spotlight | Demo or testimonial, swipe-up / link sticker, clear CTA |
| Entertain | Behind-the-Scenes | Raw footage feel, casual voice, day-in-the-life |
| Build Trust | Social Proof | Screenshots, results, user messages (anonymized) |

Document the selected type and reasoning.

## Phase 3: Slide Sequence

Build the sequence with a **maximum of 5 slides**. Each slide must specify:

1. **Slide number** (1-5)
2. **Visual description** -- what the viewer sees (photo, video clip, graphic)
3. **Text overlay** -- large text, high contrast, max 2 lines per slide
4. **Duration** -- 5s for static, up to 15s for video
5. **Transition note** -- how it connects to the next slide

### Slide Sequence Rules
- Slide 1 is the hook. It must stop the tap-through. Use a bold statement or question.
- Middle slides deliver the payload (info, proof, entertainment).
- Final slide contains the CTA or interactive element.
- Text overlays: minimum 24pt equivalent, always within safe zone (see format-specs.md).
- High contrast required: white text on dark overlay, or dark text on light overlay.

### Example Hook Slides (German)
- "Das macht 90% falsch beim Abnehmen"
- "3 Fehler, die deinen Stoffwechsel zerstoeren"
- "Schau dir das an, bevor du aufgibst"

## Phase 4: Interactive Element

Every story sequence MUST include at least one interactive element. Select from:

| Element | Best For | Placement |
|---------|----------|-----------|
| Poll sticker | Quick engagement, binary opinion | Slide 2-4 |
| Question sticker | DM generation, audience research | Final slide |
| Quiz sticker | Educational content, gamification | Slide 3-4 |
| Slider sticker | Emotional reaction, rating | Any middle slide |
| Countdown sticker | Launch, event, offer deadline | Final slide |

Document:
- Which sticker type and why
- Exact text for the sticker (in German)
- Expected response pattern

## Phase 5: Quality Check

Validate the sequence against these criteria:

- [ ] Max 5 slides
- [ ] Slide 1 is a clear hook (no logo-only slides)
- [ ] Text overlays are large and high-contrast
- [ ] At least one interactive element included
- [ ] All text overlays are within safe zone dimensions
- [ ] CTA is specific and actionable (not generic "Link in Bio")
- [ ] Brand voice matches content-rules.md
- [ ] No banned topics or claims (check content-rules.md)

If any check fails, revise the affected slide before delivery.

## Phase 6: Delivery

Output format: structured brief with the following sections.

```
## Story Brief

**Type:** [story type]
**Goal:** [goal]
**Slides:** [count]
**Interactive:** [sticker type]

### Slide-by-Slide

#### Slide 1 (Hook)
- Visual: [description]
- Text Overlay: "[text]"
- Duration: [Xs]

#### Slide 2
...

### Production Notes
- [any filming tips, asset needs, or timing notes]
```

Deliver the brief as a single Markdown block. Do not create image files or design mockups.
