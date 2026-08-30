# WC26 Web Information Architecture

## Status

- Product version: `0.5.0`
- Phase 8 information architecture: implemented
- Design direction: light, professional and evidence-focused

This document defines navigation, page hierarchy, visual language and responsive behaviour. Product rules belong in `WEB_PRODUCT.md`; implementation decisions belong in `WEB_TECHNOLOGY.md`.

## Product Identity

```text
WC26 Transfer Intelligence
Recruitment decision support powered by World Cup 2026 data
```

The interface should feel like a modern scouting product, not a betting site, game or generic admin dashboard. Analytical depth is introduced progressively.

## Visual System

| Token | Value | Use |
|---|---|---|
| Page background | `#F4F7F5` | Application canvas |
| Surface | `#FFFFFF` | Cards and panels |
| Secondary surface | `#EAF0ED` | Subtle grouping |
| Primary text | `#10211B` | Headings and key values |
| Secondary text | `#66736D` | Supporting context |
| Brand green | `#0B6B4B` | Primary actions and selection |
| Dark green | `#074735` | High-contrast active states |
| Deep navy | `#163B65` | Comparison evidence |
| Border | `#D8E1DC` | Structure and separation |

Geist Sans is the primary typeface. Geist Mono or tabular numerals may be used selectively for technical identifiers and aligned metrics.

Selected controls must meet WCAG AA contrast in every browser engine.

## Navigation

Desktop navigation:

```text
WC26 Transfer Intelligence | Home | Players | Shortlists | Methodology | API ready
```

Mobile navigation collapses without hiding the primary routes from keyboard or screen-reader users.

Principles:

1. Player discovery is always easy to reach.
2. Shortlists are a first-class recruitment workspace.
3. Status is compact; technical identity remains on `/status`.
4. Back actions appear before primary actions and use a directional cue.

## Route Map

```text
/
├── /players
│   └── /players/[playerId]
├── /shortlists
├── /analysis/[playerId]
│   └── /analysis/[playerId]/results
├── /compare/[targetId]/[candidateId]
├── /compare/multi/[targetId]?candidates=...
├── /methodology
└── /status
```

## Page Hierarchy

### Landing

1. Product value proposition
2. Player-search entry point
3. Short explanation of discovery, analysis and comparison
4. Selected analytical capabilities
5. Methodology and status references

The landing page is product-oriented and does not duplicate repository documentation.

### Player discovery

1. Page context
2. Search input and advanced filters
3. Active-filter summary and reset controls
4. Result count and cards
5. Loading, empty or error feedback

Filters remain URL-addressable. Mobile filter controls may use a dedicated panel, while results stay readable as cards rather than a wide table.

### Player profile

1. Deterministic player image and identity
2. Country, position, final role and spatial role
3. Age, height and market value
4. Back, transfer-analysis and shortlist actions
5. Featured metrics and performance profile
6. Spatial profile, scouting insights and role evidence

The action order is `Back → Run transfer analysis → Add to shortlist`.

### Shortlists

1. Shortlist selection and management
2. Player membership and removal actions
3. Target selection
4. Up to three eligible same-position candidates
5. Canonical comparison action

The interface explains why an ineligible candidate cannot be selected.

### Recommendation results

1. Target and applied criteria
2. Recruitment-mode navigation
3. Ranked candidate cards
4. Explanation, evidence availability and reliability
5. Profile, shortlist and pair-comparison actions

### Multi-player comparison

1. Page identity and return path
2. Target-relative overview matrix
3. Target final-role metrics grouped by duty
4. Position-relative radar
5. Measured tournament heatmaps

Candidate controls live beside both radar and heatmap headers. They share one focused state, removing the need to return to a separate selector while scrolling.

Role metrics display values in canonical player order as `total (per90/90)`. Wide matrices use an internal horizontal scroll region and never widen the document.

## Shared Component Language

- Surfaces use consistent radius, border and restrained shadow.
- Green communicates product identity and active selection.
- Navy distinguishes candidate evidence from the target baseline.
- Badges provide short evidence or status context, not repeated prose.
- Skeletons preserve layout during loading.
- Empty and error states explain what happened and offer one next action.
- Missing data uses “Unavailable”, never an ambiguous blank or zero.

## Responsive Rules

- Desktop may use analytical grids and side-by-side heatmaps.
- Tablet reduces columns before reducing readability.
- Mobile uses stacked cards and contained table scrolling.
- Controls wrap without truncating their accessible names.
- Charts scale inside their cards and do not create document overflow.
- Sticky table cells are used only when paint containment remains correct on mobile WebKit.

## Accessibility

- Logical heading order and landmarks
- Semantic tables with labelled scroll regions
- Keyboard-operable buttons, tabs and disclosures
- Visible focus and `aria-pressed` for candidate selection
- WCAG AA color contrast
- Descriptive chart and player-image alternatives
- Live regions for loading and retry feedback
- No information communicated by color alone

## Final Design Principles

```text
Clarity before density
Evidence before decoration
Progressive disclosure for detail
Responsive and accessible by default
Backend data as the source of truth
```
