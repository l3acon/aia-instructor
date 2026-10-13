# Challenge Scoring Methodology

Points are assigned by **difficulty tier** based on what a player must do to solve the challenge. Tiers define a range — the listed value is the baseline, but challenges can be adjusted within the band when they fall between two tiers.

## Point Tiers

| Tier | Baseline | Range | Criteria |
|---|---:|---|---|
| Setup | 5 | 5 | UI clicks only, no technical skill |
| Knowledge | 10 | 8–12 | Basic web search or general awareness |
| Directed Knowledge | 15 | 13–20 | Specific domain knowledge or simple system navigation |
| Exploration | 25 | 21–35 | Log into a system and discover information |
| Execution | 50 | 40–60 | Multi-step CLI workflow |
| Orchestration | 75 | 65–85 | Configure AAP Controller (projects, templates, credentials) |
| Mastery | 100 | 90–120 | Combine multiple concepts into a working deployment |
| *(reserved)* | 150+ | 150+ | Future expert-level challenges |

**Side Quest** challenges are worth **5 pts** each. They are in-game multiple-choice questions (4 options) that can be brute-forced, so they sit at the bottom of the scale.

### When to adjust within a range

Use the baseline unless the challenge clearly skews easier or harder than its peers in the same tier. For example, a trivia question whose answer is strongly hinted in the description text itself would sit at the low end of its tier range.

## Hint Cost Tiers

Hint costs are sized relative to the Side Quest value so there is a clear hierarchy:

| Tier | Cost | What the player gets |
|---|---:|---|
| Nudge | 2 | Points in the right direction |
| Guide | 5 | Significant step-by-step guidance |
| Reveal | 10 | Nearly gives the answer |

### Design constraint

```
Nudge (2)  <  Side Quest (5)  <  Reveal (10)
```

A simple hint is always cheaper than a Side Quest point. A heavy hint that nearly hands over the answer costs more than an entire Side Quest challenge.

## Adding a New Challenge

1. Classify it into a tier from the table above based on what the player must do.
2. Set `value:` to the tier baseline, adjusting within the range if warranted.
3. Add hints (if applicable) using the Nudge / Guide / Reveal cost tiers.
4. For challenges harder than Mastery, use 150+ and add a new row to the tier table.
