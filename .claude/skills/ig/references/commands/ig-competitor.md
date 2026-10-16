---
name: ig-competitor
description: >
  Competitor research and analysis via delegation to the ig-research skill.
  Identifies target accounts, delegates data collection, synthesizes findings
  into actionable hooks, formats, and content gaps.
allowed-tools:
  - Read
  - Write
  - Grep
  - Glob
  - Bash
---

# IG Competitor -- Competitor research via delegation

**Key references:**
- `references/competitor-framework.md` -- competitor selection criteria, analysis dimensions, comparison matrix
- `references/account-baseline.md` -- own account metrics for gap analysis

**NOTE:** This is a DELEGATION skill. The primary data collection happens via the `ig-research` skill. This skill orchestrates the research, reads results, and synthesizes recommendations.

---

## Phase 1: Target Selection

Identify which competitor accounts to research:

1. Ask the user for specific accounts, or suggest based on these criteria:
   - Same niche (fitness, nutrition, health for German-speaking audience)
   - Similar follower count range (0.5x to 5x of own account)
   - Active posting (at least 3 posts/week)
   - High engagement relative to follower count
2. Select 3-5 target accounts. More than 5 dilutes the analysis.
3. Load `references/competitor-framework.md` for the analysis dimensions to apply.
4. Load `references/account-baseline.md` for own account metrics (needed for gap analysis).

Document the selected accounts with handles and reasoning for selection.

## Phase 2: Delegation

For each target account, invoke the `ig-research` skill:

1. Pass the account handle and the analysis dimensions from competitor-framework.md.
2. The ig-research skill will:
   - Collect public data (post frequency, content types, engagement patterns)
   - Analyze content pillars and topic distribution
   - Document hook patterns and CTA strategies
   - Note visual style and branding approach
3. Each research run produces a report file. Note the output paths.

If ig-research is unavailable, fall back to manual data collection using available API tools or web research tools.

## Phase 3: Report Reading

Read all generated research reports:

1. Load each competitor report file.
2. Extract key data points per competitor:
   - Posting frequency and consistency
   - Top-performing content (by visible engagement: likes, comments)
   - Content pillar distribution
   - Hook patterns used (categorize into hook-library.md categories)
   - CTA strategies
   - Audience interaction style (comment responses, story engagement)
   - Affiliate/partnership approach

Compile into a comparison matrix.

## Phase 4: Synthesis

Analyze the collected data for actionable insights:

### Hook Adaptation
- Which hook patterns are competitors using successfully that we are NOT using?
- List 3-5 hooks to adapt (not copy) with German examples:
  - Original: "[competitor hook]"
  - Adapted: "[our version in German]"
  - Why it works: [psychological trigger]

### Format Testing
- Which formats are competitors using that we are underrepresenting?
- Prioritize by: (a) competitor success with the format, (b) our audience alignment
- Recommend 2-3 format experiments with specific topic suggestions

### Content Pillar Insights
- What topics do competitors cover that we do not?
- What topics do WE cover that competitors do not (our differentiation)?
- Where is there topic saturation across all competitors (avoid or differentiate)?

### Engagement Tactics
- How do competitors drive saves, shares, and DMs?
- Which CTA patterns are most effective?
- Comment response strategies worth adopting

## Phase 5: Gap Analysis

Cross-reference competitor findings with own account baseline:

| Dimension | Our Account | Competitor Avg | Gap | Priority |
|-----------|------------|----------------|-----|----------|
| Posting Frequency | X/week | Y/week | +/-Z | High/Med/Low |
| Reel Ratio | X% | Y% | +/-Z% | High/Med/Low |
| Carousel Ratio | X% | Y% | +/-Z% | High/Med/Low |
| Avg Engagement Rate | X% | Y% | +/-Z% | High/Med/Low |
| Hook Diversity | X categories | Y categories | +/-Z | High/Med/Low |
| CTA Variety | X types | Y types | +/-Z | High/Med/Low |

Flag any gap where competitor average exceeds our metric by more than 30% as high priority.

### Differentiation Check
Equally important: identify what we do BETTER than competitors. These are strengths to double down on, not change.

## Phase 6: Quality Check

Before delivering the report, verify:

- [ ] At least 3 competitor accounts analyzed
- [ ] Comparison matrix includes all key dimensions
- [ ] Hook adaptations are original (adapted, not copied verbatim)
- [ ] Gap analysis references actual baseline data
- [ ] Recommendations are specific and actionable
- [ ] Differentiation strengths are identified (not just gaps)

## Phase 7: Delivery

Output as a structured Markdown report:

```
## Competitor Analysis Report

**Accounts Analyzed:** [list of handles]
**Own Account Baseline:** [key metrics summary]
**Date:** [date]

### Competitor Comparison Matrix
| Metric | Our Account | [Comp 1] | [Comp 2] | [Comp 3] |
|--------|------------|----------|----------|----------|

### Hooks to Adapt
1. **[Pattern Name]:** "[adapted hook in German]" -- Source: [competitor]
2. ...

### Formats to Test
1. [format] -- [why, based on competitor data]
2. ...

### Content Gaps (We Should Add)
- [topic/format gap]

### Our Strengths (Double Down)
- [differentiator]

### Gap Analysis Summary
| Dimension | Gap | Priority | Recommended Action |
|-----------|-----|----------|-------------------|

### 30-Day Action Plan
1. [specific action from synthesis]
2. [specific action from synthesis]
3. [specific action from synthesis]
```
