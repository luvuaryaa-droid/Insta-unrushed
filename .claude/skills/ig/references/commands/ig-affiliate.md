---
name: ig-affiliate
description: >
  Create compliant affiliate content for Instagram. Loads partner playbooks,
  selects proven content patterns, writes scripts and captions with mandatory
  German advertising disclosure, and validates against legal and scheduling rules.
allowed-tools:
  - Read
  - Write
  - Grep
  - Glob
---

# IG Affiliate -- Compliant affiliate content creation

**Key references:**
- `references/affiliate-compliance.md` -- partner playbooks, disclosure rules, spacing constraints
- `references/format-specs.md` -- format dimensions, duration limits, text sizing
- `references/hook-library.md` -- proven hook patterns with performance data
- `references/scoring-system.md` -- engagement scoring criteria and thresholds

**Active Partners:** Harvest Republic, Les Mills, InnoNature, Sunday Natural

---

## Phase 1: Partner Selection

1. Load `references/affiliate-compliance.md` for partner playbooks.
2. Confirm which partner the content is for. If not specified, ask the user.
3. Load the partner-specific playbook section which includes:
   - Product/service to promote
   - Key selling points and approved claims
   - Affiliate link or discount code
   - Commission structure (for internal reference only, never share publicly)
   - Content restrictions (what NOT to say)
   - Past performance data (if available)

4. Verify the partner is on the active partners list. If not, flag to the user.

## Phase 2: Content Type Selection

Select from 5 proven affiliate content patterns:

| Pattern | Format | Best For | Save Potential |
|---------|--------|----------|----------------|
| **Honest Review** | Reel (60-90s) | Trust building, high conversion | Medium |
| **Day-in-the-Life Integration** | Reel (30-60s) | Natural placement, low resistance | Low |
| **Problem-Solution** | Carousel (7-10 slides) | Educational angle, high save rate | High |
| **Before/After or Comparison** | Carousel (5-7 slides) | Visual proof, social proof | Medium |
| **Quick Tip with Product** | Reel (15-30s) | Easy production, high reach | Low |

Selection criteria:
- Match the pattern to the product type
- Consider recent content mix (avoid 2 reviews in a row)
- Prioritize patterns with higher save potential for long-term value
- Consider the user's production capacity

Document the selected pattern and reasoning.

## Phase 3: Script / Caption Writing

### Reel Script (if reel format selected)

Structure:
```
HOOK (0-3s): [attention-grabbing opener, NOT about the product]
PROBLEM (3-10s): [relatable pain point]
BRIDGE (10-15s): [transition to solution]
PRODUCT (15-40s): [natural integration, personal experience]
PROOF (40-50s): [results, feelings, specific details]
CTA (50-60s): [specific call to action with code/link reference]
```

Rules:
- Hook must NOT mention the product or brand (pattern interrupt first)
- Product mention comes after value delivery
- Use personal experience language ("Ich nutze...", "Bei mir hat...")
- Never use superlatives that sound like ad copy ("das BESTE Produkt ever")
- Include the discount code verbally AND on screen

### Caption

Structure:
```
Werbung | Anzeige

[Hook line -- same rules as non-affiliate content]

[Personal story or context -- why this product matters to you]

[Product details -- specific, honest, personal]

[Code/link reference]

[CTA -- save for later, share with someone who needs this]

[3-5 niche hashtags]
```

**MANDATORY:** "Werbung" or "Anzeige" MUST be the FIRST word in the caption. Not buried. Not at the end. FIRST.

### Caption Rules
- Max 300 words
- Personal voice throughout (not brand-speak)
- At least one honest limitation or "not for everyone" qualifier
- Specific results or experiences (not vague "it changed my life")

## Phase 4: Legal Compliance Check

German Kennzeichnungspflicht (advertising disclosure) requirements:

### Mandatory Elements
- [ ] "Werbung" or "Anzeige" at the TOP of the caption (first word)
- [ ] If Reel: "Werbung" visible as text overlay in the first 3 seconds
- [ ] If Story: "Werbung" or "Anzeige" visible on EVERY slide that shows the product
- [ ] If Carousel: "Werbung" on the cover slide AND in the caption

### Prohibited
- [ ] No health claims that are not scientifically proven
- [ ] No before/after images with misleading timeframes
- [ ] No claims about curing, treating, or preventing disease
- [ ] No "guaranteed results" language
- [ ] No fake urgency ("nur noch heute!" unless actually true)

### Partner-Specific
- [ ] Content matches partner-approved claims only
- [ ] Discount code is current and valid
- [ ] No competitor mention in the same post

If ANY compliance check fails, revise the content before proceeding.

## Phase 5: Scheduling Check

Validate against calendar rules:

1. **Max 2 affiliate posts per week.** Check the current week's calendar.
2. **No consecutive affiliate days.** At least 2 non-affiliate posts between affiliate posts.
3. **Partner rotation.** Same partner max once per week.
4. **Cluster avoidance.** No more than 4 affiliate posts in any 14-day window.

If a violation is detected, suggest alternative posting dates.

## Phase 6: Scoring

Score the affiliate content using scoring-system.md criteria with affiliate-specific adjustments:

| Criterion | Weight | Score (1-10) |
|-----------|--------|--------------|
| Hook strength (non-salesy) | 20% | |
| Natural product integration | 25% | |
| Value for non-buyers | 15% | |
| Legal compliance | 20% | |
| CTA effectiveness | 10% | |
| Authenticity | 10% | |

**Minimum passing score: 7.5** (higher threshold than non-affiliate content because bad affiliate content damages trust disproportionately).

If below 7.5, revise the weakest criteria before delivery.

## Phase 7: Delivery

Output format:

```
## Affiliate Content Brief

**Partner:** [partner name]
**Product:** [product/service]
**Format:** [Reel/Carousel/Story]
**Content Pattern:** [selected pattern]
**Score:** [X.X / 10]
**Discount Code:** [code]

### Compliance Status
- Caption disclosure: OK
- Visual disclosure: OK
- Health claims: OK
- Scheduling: OK -- Suggested date: [date]

### Script / Slide Breakdown
[Full script or slide-by-slide breakdown]

### Caption
[Full caption with Werbung/Anzeige at top]

### Production Notes
- [filming tips, product placement notes]
- [text overlay reminders for "Werbung"]
- [B-roll suggestions]
```
