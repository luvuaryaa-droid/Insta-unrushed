---
name: ig
description: Instagram content engine for planning and writing (no posting). Creates Reels scripts, hooks, captions, Stories, Carousels, editorial calendars, strategy, competitor research, affiliate posts and repurposing, scored on a 100-point system for the 2026 algorithm. Use when the user mentions Instagram, IG, Reel, hook, caption, Story, Carousel, content plan or content calendar.
license: MIT (adapted from NicoJunk/claude-ig)
---

> **Safety rule (always applies):** This skill only plans and drafts. Never post,
> publish, reply, like, delete or DM on any Instagram account, never ask for
> Instagram logins or tokens, and never scrape accounts. The user posts everything
> herself.

# IG: Instagram Content Engine

Full-lifecycle Instagram management: hooks, Reels, Stories, Carousels, captions,
affiliate content, performance analysis, competitor research, editorial planning,
and content repurposing. Optimized for the 2026 Instagram algorithm with
watch time, DM-sends, and saves as primary distribution signals.

Works for any Instagram account and niche. Learns account context from what the user shares
and adapts content strategy, hook patterns, and scoring calibration accordingly.

## Quick Reference

| Command | What it does |
|---------|-------------|
| `/ig reel <topic>` | Write a complete Reel (hook, script, caption, thumbnail) |
| `/ig hook <topic>` | Generate and score hooks for any format |
| `/ig caption <topic>` | Write an optimized caption (500+ chars, save CTA) |
| `/ig story <topic>` | Plan a Story sequence (slides, stickers, polls) |
| `/ig carousel <topic>` | Plan a Carousel (cover hook, slides, CTA) |
| `/ig competitor <accounts>` | Research competitor content |
| `/ig calendar [weekly\|monthly]` | Generate an editorial content calendar |
| `/ig strategy` | Content strategy and positioning analysis |
| `/ig affiliate <partner>` | Create compliant affiliate content |
| `/ig repurpose <post>` | Repurpose IG content for other platforms |

## Orchestration Logic

### Command Routing

1. Parse the user's command to determine the sub-skill
2. If no sub-command given, ask which action they need
3. Route to the appropriate sub-skill:
   - `reel` / `skript` / `video` -> read `references/commands/ig-reel` (full Reel production)
   - `hook` / `opening` -> read `references/commands/ig-hook` (hook generation and scoring)
   - `caption` / `beschreibung` / `text` -> read `references/commands/ig-caption` (caption writing)
   - `story` / `stories` -> read `references/commands/ig-story` (Story sequence planning)
   - `carousel` / `karussell` / `slides` -> read `references/commands/ig-carousel` (Carousel planning)
   - `competitor` / `konkurrenz` / `research` / `spy` -> read `references/commands/ig-competitor` (competitor research)
   - `calendar` / `plan` / `kalender` / `schedule` -> read `references/commands/ig-calendar` (editorial calendar)
   - `strategy` / `strategie` / `positioning` -> read `references/commands/ig-strategy` (positioning and content mix)
   - `affiliate` / `werbung` / `kooperation` / `sponsored` -> read `references/commands/ig-affiliate` (compliant partner content)
   - `repurpose` / `redistribute` / `cross-post` -> read `references/commands/ig-repurpose` (cross-platform repurposing)

### Niche Detection

Detect account niche from bio, content patterns, and hashtag analysis:

| Signal | Niche | Adaptation |
|--------|-------|-----------|
| Workout demos, exercise names, body part focus | Fitness | Correction hooks, body-part targeting, safe exercise form |
| Recipe posts, nutrition tips, meal prep | Food / Nutrition | Recipe format templates, ingredient lists, macro data |
| Product reviews, tutorials, before/after | Beauty / Skincare | Transformation hooks, product comparison carousels |
| Tips, frameworks, income proof | Business / Coaching | Authority hooks, case study carousels, lead magnet CTAs |
| Lessons, how-to, step-by-step | Education | Curiosity gap hooks, carousel-heavy strategy |
| Day-in-life, travel, personal stories | Lifestyle | Identity trigger hooks, story-heavy strategy |
| Mixed / unclear | Creator | Analyze top 10 posts to determine primary content type |

Adapt hook library selection, caption voice, CTA strategy, and content mix
recommendations based on detected niche. If the user has configured
`references/account-baseline.md`, use that data instead of detecting.

### Algorithm Priority (2026)

Every piece of content is optimized in this priority order:

| Priority | Signal | Weight | Why |
|----------|--------|--------|-----|
| 1 | Watch Time | Highest | First 3 seconds determine distribution. Completion rate is king. |
| 2 | DM-Sends per Reach | 3-5x likes | Primary signal for reaching new audiences via Explore |
| 3 | Saves | ~3x likes | Signal for lasting value, drives Explore and Suggested placement |
| 4 | Likes/Comments | Lowest | Weakest signals; comments without saves = algorithm ignores |
| 5 | Originality Score | Gate | Recycled formats tank reach; always adapt through creator's unique lens |

## Quality Gates

Hard rules. Content that violates any gate is blocked from delivery:

| # | Gate | Threshold |
|---|------|-----------|
| G1 | Score before delivery | NEVER deliver content without a Content Quality Score |
| G2 | Em dashes | NEVER use em dashes (U+2014) in any output |
| G3 | Affiliate disclosure | NEVER create affiliate content without proper disclosure at caption TOP |
| G4 | Controversial opinions | NEVER recommend controversial opinion posts (high comments, zero saves) |
| G5 | Affiliate spacing | NEVER place 2 affiliate posts on consecutive days |
| G6 | Metrics guessing | NEVER guess account metrics; use numbers the user gives, or state data is unavailable |
| G7 | Safe zones | NEVER place text in format-specific unsafe zones (check format-specs.md) |

## Scoring Methodology

### Content Quality Score (0-100)

5-category weighted scoring from `references/scoring-system.md`:

| Category | Weight | What it measures |
|----------|--------|-----------------|
| Hook Strength | 25 pts | Curiosity gap, pattern interrupt, identity trigger, first 3s clarity |
| Content Quality | 25 pts | Value density, structure, problem-solution flow, voice authenticity |
| Caption & CTA | 20 pts | Length (500+ chars), save/DM CTA, hook variation opener, hashtag quality |
| Format Compliance | 15 pts | Correct specs, safe zones, thumbnail, duration targets |
| Algorithm Signals | 15 pts | Save/DM optimization, originality, non-controversial, watch time design |

### Scoring Bands

| Score | Grade | Rating | Action |
|-------|-------|--------|--------|
| 90-100 | A | Publish | Ready to post, flagship content |
| 80-89 | B | Strong | Minor polish, ready for publication |
| 60-79 | C | OK | Targeted improvements needed (must include fix instructions) |
| 40-59 | D | Below Standard | Significant rework required |
| < 40 | F | Reject | Fundamental issues, start over |

Content scoring below 80 MUST include specific revision instructions per
deficient category. Do not just deliver the score.

### Priority Levels (for audit findings)

- **Critical**: Content violates a Quality Gate (fix immediately)
- **High**: Score < 60, significant performance drag (fix before posting)
- **Medium**: Score 60-79, optimization opportunity (improve within week)
- **Low**: Minor polish, best practice (backlog)

## Reference Files

Load on-demand as needed. NEVER load all references at startup.

**Path resolution:** All references live in this skill's `references/` folder (`.claude/skills/ig/references/` in this repo, or `~/.claude/skills/ig/references/` if installed user-level).
Sub-skills referencing `references/*.md` resolve to this path.

| Reference | Content | Used by |
|-----------|---------|---------|
| `references/algorithm-2026.md` | Algorithm signals, ranking factors, distribution mechanics | All sub-skills |
| `references/format-specs.md` | Technical specs per format (Reel, Story, Carousel, Feed) with safe zones | ig-reel, ig-story, ig-carousel |
| `references/scoring-system.md` | Full 5-category scoring rubric with sub-criteria and severity multipliers | All content sub-skills |
| `references/hook-library.md` | 50+ hook templates in 5 categories with scoring and adaptation rules | ig-hook, ig-reel, ig-carousel |
| `references/content-rules.md` | Caption structure, CTA hierarchy, hashtag strategy, voice guidelines | ig-caption, ig-reel, ig-story |
| `references/account-baseline.md` | Account metrics template and KPI tracking (fill in by hand) | ig-strategy, ig-calendar |
| `references/affiliate-compliance.md` | Disclosure requirements, partner management, scheduling rules | ig-affiliate |
| `references/conversion-pipeline.md` | DM automation, link tracking, funnel architecture | ig-caption, ig-strategy |
| `references/competitor-framework.md` | Competitor monitoring methodology, benchmarks, trend detection | ig-competitor |
| `references/story-strategy.md` | Story types, slide sequences, interactive elements, retention rules | ig-story |
| `references/repurpose-playbook.md` | Cross-platform adaptation rules per channel | ig-repurpose |

## Sub-Skills

This skill orchestrates 13 specialized sub-skills:

| # | Sub-Skill | Purpose |
|---|-----------|---------|
| 1 | `ig-reel` | Full Reel production (hook, script, caption, thumbnail) |
| 2 | `ig-hook` | Hook generation, scoring, and A/B variants |
| 3 | `ig-caption` | Caption writing with save CTA, hashtags, 500+ chars |
| 4 | `ig-story` | Story sequence planning (slides, stickers, polls) |
| 5 | `ig-carousel` | Carousel planning (cover, slides, CTA structure) |
| 8 | `ig-competitor` | Competitor research and benchmarking |
| 9 | `ig-calendar` | Editorial calendar with content mix validation |
| 10 | `ig-strategy` | Content positioning, niche analysis, growth strategy |
| 11 | `ig-affiliate` | Compliant affiliate/sponsored content |
| 13 | `ig-repurpose` | Cross-platform content repurposing |

## Execution Flow

Standard execution order for `/ig reel`:

1. **Parse**: Identify topic, detect content type and niche context
2. **Load References**: format-specs.md + hook-library.md + content-rules.md
3. **Hook**: Generate 3 hook variants from different categories, score each, select best
4. **Script**: Structure body (problem -> solution -> insight) with segment timing
5. **Caption**: Write 500+ char caption with save CTA and niche hashtags
6. **Thumbnail**: Describe thumbnail concept with text overlay
7. **Score**: Apply full 5-category Content Quality Score
8. **Deliver**: Output complete package with score and revision notes


## Setup

No setup, logins or tokens needed. Tell Claude about your page (niche, audience,
style, what has worked) or fill in `references/account-baseline.md` by hand.
For performance questions, share screenshots or numbers from Instagram Insights.

## Anti-Patterns (Never Do These)

| Anti-Pattern | Why |
|-------------|-----|
| Deliver without score | Incomplete deliverable; score is mandatory |
| Use em dashes | #1 signal of AI-generated text |
| Generic hashtags (#fitness, #motivation) | Zero distribution value, signals low effort |
| Controversial opinion posts | High comments, zero saves = algorithm ignores |
| Copy competitor hooks verbatim | Originality Score (2026) penalizes recycled formats |
| Guess metrics | Stale data leads to wrong decisions; use numbers the user gives, or state uncertainty |
| Skip format-specs.md | Wrong specs = reduced reach (safe zones, duration, ratio) |
| Affiliate without disclosure | Legal violation in most jurisdictions |
| Optimize for likes over saves | Likes are the weakest algorithm signal |
| Wall-of-text captions | Line breaks mandatory for readability and retention |
| Post at the same time every day | Algorithm rewards variation within optimal windows |
