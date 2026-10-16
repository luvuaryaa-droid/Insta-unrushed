---
name: ig-caption
description: >
  Write optimized Instagram captions. Generates save-optimized captions with hook
  variation openers, value body (300-400 chars), save/DM CTAs, niche hashtags,
  and 500+ character minimum. Scores each caption against the Caption & CTA
  sub-criteria (20pts max). Output is ready to paste into Instagram.
  Use when user says "caption", "Beschreibung", "Caption schreiben",
  "Bildunterschrift", "IG Text", "Reel Caption", "Post Text".
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - WebSearch
---

# IG Caption: Optimized Instagram Captions

Writes complete, paste-ready Instagram captions. Every caption follows a proven
structure optimized for saves and DM-sends (the two highest-value algorithm
signals in 2026). Captions sound like the creator wrote them. Never robotic,
never filler.

Load account context (niche, audience, voice, language) from `references/account-baseline.md`.
If not configured, ask the user about their niche, audience, and voice.

**Key references:**
- `references/content-rules.md` — Caption structure, CTA hierarchy, hashtag strategy
- `references/scoring-system.md` — Caption & CTA sub-criteria (20pts max)
- `references/account-baseline.md` — Proven caption patterns from top-performing posts

## Workflow

### Phase 1: Context

Gather the inputs needed to write a targeted caption.

1. **Identify post type** — Reel, Carousel, Feed image, or Story highlight
2. **Identify topic** — The specific content theme (e.g., "16:8 Fehler", "Proteinmythen", "Krafttraining ab 40")
3. **Identify visual hook** — The text overlay or visual hook used on the post itself (needed to create a thematically linked but different caption opener)
4. **If any of these are missing**, ask the user once. Do not proceed without all three.

### Phase 2: Caption Structure

Load `references/content-rules.md` and apply the proven caption structure.

1. **Read content-rules.md** for current caption structure rules, CTA hierarchy, and hashtag strategy
2. **Read account-baseline.md** to identify which caption patterns performed best on recent top posts
3. **Map the structure** for this specific post:
   - Hook variation opener (thematically linked to visual hook, never identical)
   - Value body (problem statement, insight, or actionable tip)
   - Line break separator
   - CTA (selected from hierarchy based on post type and goal)
   - Hashtag set (3-5 niche-specific)

### Phase 3: Writing

Write the complete caption in German following these rules.

#### 3a. Hook Variation Opener

The first line is the most important. It determines whether the user taps "more."

- MUST be thematically linked to the visual hook on the post
- MUST NOT repeat the visual hook text verbatim
- Opens a curiosity gap, challenges a belief, or makes a bold claim
- Keep it to 1-2 sentences max
- No filler openings ("Hey ihr Lieben" is for Stories, not Reel/Feed captions)

#### 3b. Value Body (300-400 characters)

The core of the caption. Choose ONE of these structures based on the topic:

| Structure | When to use |
|-----------|------------|
| Problem-Solution | Topic addresses a common mistake or frustration |
| Myth-Truth | Topic debunks a widespread belief |
| Insight-Action | Topic shares a lesser-known fact with a practical takeaway |
| Story-Lesson | Topic benefits from a personal anecdote or client story |

Rules:
- 300-400 characters of substance (not padding)
- Short sentences. Vary length (8-word punchy, 20-word explanatory)
- Write in the creator's voice (per account-baseline.md). No lecture tone.
- Use "du" (never "Sie", never "ihr" in captions)
- GROSSBUCHSTABEN for emphasis on single words (NICHT, OHNE, JETZT), not full sentences
- No em dashes. Use comma, period, colon, or sentence restructuring instead.

#### 3c. Line Break

Insert a clear visual break (empty line) between the value body and the CTA section.

#### 3d. CTA (Call to Action)

Select the CTA based on this hierarchy. Optimize for the highest-priority action that fits the post:

| Priority | CTA Type | Template | When to use |
|----------|----------|----------|-------------|
| 1 | Save | "Speicher dir das fur spater" | Default for educational/tip content |
| 2 | DM-Send | "Schick das einer Freundin, die das braucht" | Relatable/emotional content |
| 3 | Comment | "Schreib mir [keyword] in die Kommentare" | Interactive/opinion content |
| 4 | Follow | "Folg mir fur mehr [topic]" | Only when demonstrating ongoing value |

Rules:
- Primary CTA first (save or DM-send for most posts)
- Secondary CTA optional (combine save + DM-send if both fit naturally)
- Never stack more than 2 CTAs
- CTA must feel like a natural closing, not a demand

#### 3e. Hashtags (3-5 niche-specific)

- Place after the CTA with one empty line above
- 3-5 hashtags maximum
- NEVER use generic hashtags: #fitness, #motivation, #workout, #healthy, #fitnessmotivation, #healthylifestyle
- Use niche-specific hashtags relevant to the DACH fitness/IF audience

Good examples: #intervallfasten168 #krafttrainingfrauen #abnehmenab40 #proteinrezepte #wechseljahrefitness
Bad examples: #fitness #motivation #gym #healthyfood #fitfam

#### 3f. Length Check

- Total caption: 500+ characters minimum (including hashtags)
- If under 500 characters, expand the value body with additional detail or a second insight. Never pad with filler.

### Phase 4: Scoring

Score the caption against the Caption & CTA sub-criteria from `references/scoring-system.md`.

1. **Load scoring-system.md** and extract the Caption & CTA category (20pts max)
2. **Score each sub-criterion** individually
3. **Calculate the total** out of 20 points
4. **If score < 16/20**, revise the weakest sub-criterion before delivery
5. **Present the score breakdown** with the caption

Score presentation format:

```
Caption Score: [X]/20

- [Sub-criterion 1]: [X]/[max] — [1-line justification]
- [Sub-criterion 2]: [X]/[max] — [1-line justification]
- [Sub-criterion 3]: [X]/[max] — [1-line justification]
- [Sub-criterion 4]: [X]/[max] — [1-line justification]
```

### Phase 5: Delivery

Deliver the complete caption ready to paste into Instagram.

#### Quality Gate Checklist (verify before delivery)

| # | Check | Pass? |
|---|-------|-------|
| 1 | Hook variation opener differs from visual hook | |
| 2 | Value body is 300-400 characters | |
| 3 | Total caption is 500+ characters | |
| 4 | CTA follows the priority hierarchy | |
| 5 | 3-5 niche hashtags (no generic ones) | |
| 6 | No em dashes anywhere in the caption | |
| 7 | Correct language, address form, and creator voice (per account-baseline.md) | |
| 8 | Score is 16+/20 | |

#### Delivery Format

```
## Caption fur: [Post Topic]

### Post Type: [Reel / Carousel / Feed / Story Highlight]
### Visual Hook: "[hook text from the post]"

---

[Complete caption — ready to paste]

---

### Score: [X]/20
[Score breakdown per sub-criterion]

### Hashtags included: [N]
### Character count: [N]
```

## Anti-Patterns (Never Do These)

| Anti-Pattern | Why |
|-------------|-----|
| Copy visual hook as caption opener | Redundancy kills engagement; algorithm sees duplicate text |
| Generic hashtags (#fitness, #motivation) | Zero discovery value, signals low-effort content |
| Em dashes in caption | Quality Gate G2 violation; #1 signal of AI-generated text |
| "Hey ihr Lieben" as Reel/Feed opener | Stories-only greeting; captions need hooks, not greetings |
| Stacking 3+ CTAs | Overwhelms the reader; max 2 (primary + secondary) |
| Caption under 500 characters | Underperforms on saves; Instagram rewards substantive captions |
| Using "Sie" or overly formal tone | Audience is community-driven; "du" is mandatory |
| Delivering without score | Quality Gate G1 violation; score is mandatory for every deliverable |
