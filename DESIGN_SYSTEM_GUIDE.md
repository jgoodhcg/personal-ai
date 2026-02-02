# Design System Prompting + Template

This document consolidates the repo guidance into one place so you can:
- Prompt a user to determine a design system.
- Capture the system in a reusable template.
- Apply consistent UI decisions across sessions.

This is aimed at interface design for dashboards, apps, tools, and admin panels.

---

## 1) Prompting a user to determine a design system

### A. Quick discovery (ask first)
Ask these short questions to establish direction before building UI:
- What type of product is this? (dashboard, admin tool, consumer app, analytics)
- Who are the primary users? (power users, casual users, internal teams)
- Should the UI feel compact and technical, or spacious and approachable?
- Any brand or mood words you want to lean into?

### B. Offer a direction (then confirm)
Use one of these directions as a starting point. Present 1-2 options and ask for confirmation.

Directions from this repo:
- Precision & Density: tight, technical, monochrome. Best for dev tools, admin dashboards.
- Warmth & Approachability: generous spacing, soft shadows. Best for collaborative or consumer apps.
- Sophistication & Trust: cool tones, layered depth. Best for finance and enterprise B2B.
- Boldness & Clarity: high contrast, dramatic space. Best for modern data-heavy dashboards.
- Utility & Function: muted, functional density. Best for GitHub-style tools.
- Data & Analysis: chart-optimized, numbers-first. Best for analytics and BI tools.

Example prompt to the user:
"This feels like a data-heavy dashboard. I suggest Precision & Density with a cool slate foundation and borders-only depth. Does that fit?"

### C. State concrete decisions before building components
Once the user agrees, state the key choices you will apply consistently:
- Personality, foundation, depth strategy
- Spacing base and scale
- Core colors and accent
- Radius and typography direction

This reduces drift across components and sessions.

### D. Save the system
When the direction is accepted, propose saving the system so it loads automatically in future sessions:
- File location: `.interface-design/system.md`
- This is the single source of truth for tokens, patterns, and decisions

---

## 2) Design system document template

Use this template as the canonical design system file. Save it to `.interface-design/system.md`.

```markdown
# Design System

## Direction

**Personality:** [Precision & Density | Warmth & Approachability | Sophistication & Trust | Boldness & Clarity | Utility & Function | Data & Analysis]

**Foundation:** [warm | cool | neutral | tinted]

**Depth:** [borders-only | subtle-shadows | layered-shadows]

## Tokens

### Spacing
Base: [4px | 8px]
Scale: [4, 8, 12, 16, 24, 32, 64]

### Colors
```
--foreground: [slate-900]
--secondary: [slate-600]
--muted: [slate-400]
--faint: [slate-200]
--accent: [blue-600]
```

### Radius
Scale: [4px, 6px, 8px] (sharp) | [8px, 12px, 16px] (soft)

### Typography
Font: [system | Inter | Geist]
Scale: 12, 13, 14 (base), 16, 18, 24, 32
Weights: 400, 500, 600

## Patterns

### Button Primary
- Height: 36px
- Padding: 12px 16px
- Radius: 6px
- Font: 14px, 500 weight
- Background: accent color
- Usage: Primary actions

### Card Default
- Border: 0.5px solid (faint)
- Padding: 16px
- Radius: 8px
- Background: white
- Usage: Content containers

## Decisions

| Decision | Rationale | Date |
|----------|-----------|------|
| Borders-only depth | Dashboard tool, users want density. Shadows add visual weight without information value. | YYYY-MM-DD |
| 4px spacing base | Tight enough for data tables, divisible by common UI sizes | YYYY-MM-DD |
```

---

## 3) Two example systems (optional reference)

Precision and density (dashboard/admin):
- Borders-only depth, compact spacing, sharp radii, system fonts

Warmth and approachability (collab/consumer):
- Subtle shadows, generous spacing, soft radii, friendly typography

Full examples live in:
- `reference/examples/system-precision.md`
- `reference/examples/system-warmth.md`

---

## 4) Extra guidance from this repo

### Philosophy to keep you consistent
- Decisions compound. A single spacing value becomes a system.
- Consistency beats perfection. Coherence outperforms scattered "correct" values.
- Memory enables iteration. Log decisions to evolve intentionally.

### Common drift to avoid
- Spacing that is not on a single base grid
- Slightly different button sizes across screens
- Random depth treatment (sometimes shadows, sometimes borders)

### Helpful commands (if using the plugin)
- `/interface-design:init` start a session with design principles
- `/interface-design:status` show current system
- `/interface-design:audit <path>` check code against the system
- `/interface-design:extract` extract patterns from existing UI

---

## 5) Suggested workflow

1. Ask the quick discovery questions.
2. Propose 1-2 directions and confirm.
3. State your decisions before building UI.
4. Build components consistently to the system.
5. Save or update `.interface-design/system.md` after changes.
