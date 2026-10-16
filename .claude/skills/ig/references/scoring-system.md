# Instagram Content Quality Scoring System

Deterministic scoring rubric for all Instagram content.
Applied by the orchestrator, sub-skills, and the ig-content audit agent.

## Scoring Architecture

### 5-Category Weighted Model (100 points)

| Category | Weight | Points | Measures |
|----------|--------|--------|----------|
| Hook Strength | 25% | 0-25 | First 3 seconds, curiosity mechanics, retention trigger |
| Content Quality | 25% | 0-25 | Value density, structure, voice authenticity, information gain |
| Caption & CTA | 20% | 0-20 | Length, CTA type, opener quality, hashtag strategy |
| Format Compliance | 15% | 0-15 | Technical specs, safe zones, thumbnail, duration |
| Algorithm Signals | 15% | 0-15 | Save/DM optimization, originality, watch time design |

### Category Breakdown

#### Hook Strength (25 points)

| Sub-Criterion | Points | How to Score |
|--------------|--------|-------------|
| Hook type identified | 5 | Uses a documented hook category (Correction, Identity Trigger, Bold Claim, Curiosity Gap, Relatable Pain) |
| Curiosity gap present | 5 | Creates information asymmetry in first 3 seconds |
| Pattern interrupt | 5 | Breaks scrolling behavior (visual, verbal, or structural) |
| First 3 seconds explicit | 5 | Exact opening text/action described in writing |
| Compound hook used | 5 | Combines 2+ hook mechanics (e.g., Correction + Identity Trigger) |

**Scoring guide:**
- 0-5: No clear hook, generic opening
- 6-10: Basic hook present but weak execution
- 11-15: Single strong hook mechanic
- 16-20: Strong hook with clear category identification
- 21-25: Compound hook with multiple mechanics, proven formula adapted

#### Content Quality (25 points)

| Sub-Criterion | Points | How to Score |
|--------------|--------|-------------|
| Value density | 5 | Every second/slide delivers actionable information |
| Problem-solution structure | 5 | Clear problem statement followed by concrete solution |
| Creator voice authenticity | 5 | Matches the creator's established tone and language patterns from account-baseline.md |
| Information gain | 5 | Viewer learns something they did not know before watching |
| Watch time design | 5 | Content structured to maximize completion (payoff at end, curiosity loops) |

**Scoring guide:**
- 0-5: Generic fitness content, no unique angle
- 6-10: Some value but could be from any creator
- 11-15: Clear value with recognizable perspective
- 16-20: Strong value density with the creator's authentic voice
- 21-25: Exceptional value density, unique insight, perfect voice match

**Creator voice markers (check against account-baseline.md):**
- Tone consistency: matches the documented tone (e.g., warm/direct, playful/edgy, authoritative/casual)
- Personal experience integrated: uses first-person anecdotes that fit the creator's background
- Language patterns: uses vocabulary, sentence rhythms, and phrases typical for this creator
- Audience alignment: speaks to the target audience in a way that feels native, not generic
- No hedging or filler unless it is part of the creator's documented style

#### Caption & CTA (20 points)

| Sub-Criterion | Points | How to Score |
|--------------|--------|-------------|
| Length (500+ characters) | 4 | Minimum 500 characters for algorithm boost |
| Save-focused CTA | 4 | Primary CTA drives saves ("Speicher dir das") or DM-sends |
| Hook variation opener | 4 | Caption opens with a variation of the visual hook, not filler |
| Hashtag quality | 4 | 3-5 niche hashtags, NEVER generic (#fitness, #motivation) |
| No em dashes | 4 | Zero em dash characters in entire caption |

**Scoring guide:**
- 0-4: Short caption, like-focused CTA, generic hashtags
- 5-8: Adequate length, basic CTA, some niche hashtags
- 9-12: Good length, save CTA present, mostly niche hashtags
- 13-16: Strong caption with hook opener and save/DM CTA
- 17-20: Perfect caption: 500+ chars, compound CTA (save+DM), hook opener, all niche hashtags

**CTA hierarchy (optimize in this order):**
1. Save CTA: "Speicher dir das fur spater"
2. DM-Send CTA: "Schick das einer Freundin, die das braucht"
3. Comment CTA: "Schreib mir [keyword] in die Kommentare"
4. Follow CTA: Only if content explicitly demonstrates ongoing value

#### Format Compliance (15 points)

| Sub-Criterion | Points | How to Score |
|--------------|--------|-------------|
| Correct aspect ratio | 3 | Matches format requirements (9:16 Reel, 4:5 Carousel, etc.) |
| Safe zone compliance | 3 | No text/critical elements in UI overlay zones |
| Duration target met | 3 | Within optimal range for content type (see format-specs.md) |
| Thumbnail described | 3 | Clear thumbnail concept provided (for Reels) |
| Technical specs correct | 3 | Resolution, file format, size limits met |

**Scoring guide:**
- 0-3: Wrong format or major spec violations
- 4-6: Correct format but missing safe zone awareness
- 7-9: Format correct, safe zones respected
- 10-12: All specs met, thumbnail concept included
- 13-15: Perfect compliance, optimized for each format's sweet spot

#### Algorithm Signals (15 points)

| Sub-Criterion | Points | How to Score |
|--------------|--------|-------------|
| Save/DM optimized | 3 | Content structure drives saves and DM-sends, not just likes |
| Not controversial | 3 | Topic does NOT invite polarizing debate (high comments, zero saves) |
| Originality | 3 | Unique angle through the creator's unique perspective, not recycled format |
| Watch time architecture | 3 | Open loop, payoff placement, or curiosity sustain designed |
| Completion rate design | 3 | Content structured for high % completion (no early drop-off triggers) |

**Scoring guide:**
- 0-3: Optimizes for likes/comments, generic angle
- 4-6: Some save optimization, but predictable format
- 7-9: Clear save/DM optimization, original angle
- 10-12: Strong algorithmic awareness, unique perspective
- 13-15: Perfect algorithm alignment, maximum signal density

## Quality Gates (Zero Tolerance)

These are binary checks. Any violation blocks content delivery, regardless of score.

| ID | Gate | Check | Action on Violation |
|----|------|-------|-------------------|
| G1 | Score present | Content has a completed Content Quality Score | Block delivery until scored |
| G2 | No em dashes | Zero em dash characters (U+2014) in all text | Auto-replace or rewrite |
| G3 | Affiliate disclosure | "Werbung" or "Anzeige" at TOP of caption for partner content | Block delivery |
| G4 | No controversial opinions | Content does not invite polarizing debate | Reject topic, suggest alternative |
| G5 | Affiliate spacing | No 2 affiliate posts on consecutive days | Reschedule |
| G6 | No metric guessing | All metrics come from Instagram API, never estimated | Require API call |
| G7 | Safe zone compliance | No text in format-specific unsafe zones | Flag for repositioning |

## Scoring Bands and Actions

| Score | Band | Label | Required Action |
|-------|------|-------|----------------|
| 90-100 | A | Publish | Ready to post. Flagship content. |
| 80-89 | B | Strong | Minor polish. Specific improvement noted. Ready for publication. |
| 60-79 | C | OK | Targeted improvements needed. MUST include specific revision instructions per deficient category. |
| 40-59 | D | Below Standard | Significant rework. Auto-revision triggered. Specific rewrite instructions per category. |
| < 40 | F | Reject | Fundamental issues. Start over from hook selection. |

## Severity Multipliers

When multiple issues compound, apply severity multipliers:

| Condition | Multiplier | Effect |
|-----------|-----------|--------|
| Quality Gate violation | 0x | Score is irrelevant; content blocked |
| 2+ categories below 50% of max | 0.85x | Compound weakness penalty |
| Hook Strength < 10 | 0.9x | Weak hook drags everything down |
| Caption < 300 chars | 0.9x | Under-length penalty |

## Output Format

Always display the score in this format:

```
Content Quality Score (0-100)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Hook Strength        (25%): __/25
  [ ] Hook category identified
  [ ] Curiosity gap present
  [ ] Pattern interrupt
  [ ] First 3s explicit
  [ ] Compound hook

Content Quality      (25%): __/25
  [ ] Value density
  [ ] Problem-solution structure
  [ ] Creator voice authenticity
  [ ] Information gain
  [ ] Watch time design

Caption & CTA        (20%): __/20
  [ ] 500+ characters
  [ ] Save-focused CTA
  [ ] Hook variation opener
  [ ] Niche hashtags (3-5)
  [ ] No em dashes

Format Compliance    (15%): __/15
  [ ] Correct aspect ratio
  [ ] Safe zone compliance
  [ ] Duration target met
  [ ] Thumbnail described
  [ ] Technical specs correct

Algorithm Signals    (15%): __/15
  [ ] Save/DM optimized
  [ ] Not controversial
  [ ] Originality
  [ ] Watch time architecture
  [ ] Completion rate design

QUALITY GATES:
  [ ] G1: Score present
  [ ] G2: No em dashes
  [ ] G3: Affiliate disclosure (if applicable)
  [ ] G4: No controversial opinions
  [ ] G5: Affiliate spacing (if applicable)
  [ ] G6: No metric guessing
  [ ] G7: Safe zone compliance

TOTAL: __/100  [Band: _ | Action: ________]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Revision Instructions

When score < 80, include specific revision instructions per deficient category:

```
REVISION NEEDED:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Category: [name] (scored __/__)
Issue: [specific problem]
Fix: [exact action to take]
Example: [concrete example of the fix]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Calibration Notes

These benchmarks are derived from the account's top-performing content (configure in account-baseline.md):

| Metric | Top 10% Posts | Average Posts | Bottom 10% Posts |
|--------|--------------|---------------|-----------------|
| Save Rate | > 5% | 2-4% | < 1% |
| DM-Send Rate | > 2% | 0.5-1.5% | < 0.3% |
| Avg Watch Time | > 15s | 8-12s | < 5s |
| Completion Rate | > 60% | 35-50% | < 20% |
| Content Score | 85+ | 65-80 | < 55 |

Use these to calibrate scoring: a post scoring 90+ should exhibit metrics
comparable to the top 10% when published.
