# WC26 Web Information Architecture and Visual Direction

## Status

- **Phase:** 5A.3
- **Decision:** Accepted
- **Scope:** Information architecture, navigation, page hierarchy, visual direction, responsive behavior and shared component language
- **Related documents:**
  - `docs/WEB_PRODUCT.md`
  - `docs/WEB_TECHNOLOGY.md`

## 1. Purpose

Phase 5A.3 defines how users will see, understand and navigate the WC26 Transfer Intelligence web product.

Phase 5A.1 defines what the product must do.

Phase 5A.2 defines which technologies and repository structure will be used.

Phase 5A.3 defines:

- the product identity;
- the visual direction;
- the site map;
- the page hierarchy;
- the navigation model;
- the information priority on each page;
- the shared component language;
- loading, empty and error presentation;
- responsive behavior;
- accessibility expectations.

The objective is to create a professional football scouting and transfer intelligence product rather than a generic technical dashboard.

## 2. Product Identity

### Product name

```text
WC26 Transfer Intelligence
```

### Product description

```text
Football scouting and player replacement analysis
powered by World Cup 2026 data.
```

### Product positioning

The product should feel like:

```text
Professional scouting platform
+
Modern sports analytics product
+
Clear and understandable decision-support interface
```

The product should not look like:

- a betting website;
- a football management game;
- a generic corporate admin dashboard;
- a raw data exploration notebook;
- a direct copy of an existing UI template.

The interface should communicate analytical depth without overwhelming non-technical users.

## 3. Visual Direction

The selected visual direction is:

> A light, professional and data-focused interface with deep green, navy and restrained lime accents.

A fully dark dashboard is not the default direction for the Phase 5 MVP.

The light interface is preferred because it:

- improves readability for long analytical results;
- gives player and recommendation cards more visual separation;
- makes screenshots clearer for portfolio presentation;
- supports a wider user audience;
- allows football-pitch colors to be used as controlled accents;
- prevents the product from looking like a betting interface.

## 4. Color System

The initial color direction is:

| Token | Value | Purpose |
|---|---|---|
| Page background | `#F4F7F5` | Main application background |
| Main surface | `#FFFFFF` | Cards, forms and primary panels |
| Secondary surface | `#EAF0ED` | Secondary sections and subtle containers |
| Primary text | `#10211B` | Headings and important content |
| Secondary text | `#66736D` | Supporting text and metadata |
| Primary green | `#0B6B4B` | Main actions and football identity |
| Dark green | `#074735` | Strong headers and dark accents |
| Deep navy | `#163B65` | Analytical and comparison emphasis |
| Light lime accent | `#C8F560` | Controlled selection and score highlights |
| Success | `#16835B` | Successful states |
| Warning | `#C27A19` | Warning and partial availability states |
| Error | `#C44747` | Error states |
| Border | `#D8E1DC` | Dividers, card borders and inputs |

The lime accent must be used sparingly.

Suitable uses include:

- selected filters;
- active recommendation modes;
- key score highlights;
- small CTA details;
- selected comparison elements;
- analytical chart highlights.

It must not dominate page backgrounds or large surfaces.

## 5. Typography

### Primary font

```text
Geist Sans
```

Used for:

- player names;
- headings;
- navigation;
- paragraphs;
- labels;
- buttons;
- recommendation explanations.

### Numerical and technical font

```text
Geist Mono
```

Used selectively for:

- market values;
- similarity scores;
- recommendation scores;
- request IDs;
- deployment identifiers;
- dataset bundle hashes;
- technical status details.

Tabular numerals should be preferred where supported so that metrics align consistently across cards.

## 6. Navigation

The Phase 5 MVP navigation remains intentionally simple.

### Desktop navigation

```text
WC26 Intelligence

Home
Players
Methodology
API Status

Search Players
```

Conceptual layout:

```text
┌────────────────────────────────────────────────────────────┐
│ WC26 Intelligence   Home  Players  Methodology  API Status │
│                                      [ Search Players ]     │
└────────────────────────────────────────────────────────────┘
```

### Mobile navigation

```text
┌────────────────────────────────┐
│ WC26 Intelligence          ☰   │
└────────────────────────────────┘
```

Navigation principles:

1. The user must always have a clear route back to player search.
2. The main navigation must not include authentication controls during Phase 5.
3. Technical project documentation must not dominate the product navigation.
4. The primary action should remain visible on desktop.
5. The mobile menu must remain keyboard accessible.

## 7. Final Site Map

The Phase 5 MVP route structure is:

```text
/
├── /players
│   └── /players/[playerId]
│
├── /analysis/[playerId]
│   └── /analysis/[playerId]/results
│
├── /compare/[targetId]/[candidateId]
│
├── /methodology
│
└── /status
```

### Route responsibilities

| Route | Responsibility |
|---|---|
| `/` | Introduce the product and direct users to player search |
| `/players` | Search players and display ranked results |
| `/players/[playerId]` | Display a player's analytical profile |
| `/analysis/[playerId]` | Collect transfer-analysis criteria |
| `/analysis/[playerId]/results` | Display grouped transfer recommendations |
| `/compare/[targetId]/[candidateId]` | Compare the target player with a candidate |
| `/methodology` | Explain the analytical approach in user-friendly language |
| `/status` | Display backend availability and readiness |

Deployment details from the backend `/deployment` endpoint will not receive a separate main navigation page.

They may appear within a technical details section on `/status`.

## 8. Core User Journey

The primary journey remains:

```text
Landing page
    ↓
Player search
    ↓
Player profile
    ↓
Transfer analysis form
    ↓
Recommendation results
    ↓
Player comparison
```

This journey must remain understandable without technical knowledge or authentication.

The user should always know:

- where they are;
- which player is currently selected;
- what the next action is;
- how to return to player search;
- whether the backend is loading, unavailable or ready.

## 9. Landing Page Architecture

The landing page must explain the value of the product quickly.

It must not behave like full technical documentation.

### Section order

```text
Header
    ↓
Hero
    ↓
Player search
    ↓
How it works
    ↓
Core intelligence layers
    ↓
Example transfer recommendation
    ↓
Product credibility
    ↓
Final call to action
    ↓
Footer
```

### Hero content direction

Primary headline:

```text
Find the right replacement.
Not just the most similar player.
```

Supporting copy:

```text
Search World Cup 2026 players, explore their analytical
profiles and identify transfer alternatives through
statistical, tactical, spatial and market-based intelligence.
```

Primary action:

```text
Search Players
```

Secondary action:

```text
Explore Methodology
```

### Hero visual

The hero should show a product-oriented analytical example rather than a random football photograph.

Conceptual example:

```text
Target: Michael Olise

Best Value
Hakan Çalhanoğlu

Role Compatibility    89%
Statistical Fit       82%
Market Advantage      €72M
```

The final fields and values must be aligned with the real backend response contract.

### How it works

The process should be summarized in four steps:

```text
1. Search
2. Understand
3. Analyze
4. Compare
```

### Intelligence layers

The landing page may introduce these analytical layers:

- performance;
- similarity;
- archetype;
- role;
- spatial profile;
- heatmap;
- market context.

The landing page should explain these layers briefly rather than exposing implementation details.

## 10. Player Search Page

### Purpose

The page should focus exclusively on finding a player.

### Information order

```text
Breadcrumb
Page title
Short explanation
Search input
Search state
Results
```

Conceptual layout:

```text
Players

Search the World Cup 2026 player database.

┌─────────────────────────────────────────────┐
│ Search by player name...                    │
└─────────────────────────────────────────────┘

6 players found

┌─────────────────────────────────────────────┐
│ Michael Olise                              │
│ France · Midfielder                        │
│ Rating 7.57 · Market value €144M           │
└─────────────────────────────────────────────┘
```

Search results should use cards or list rows rather than wide desktop-only tables.

### Required states

```text
Initial
Query too short
Searching
Results found
No results
Network failure
API unavailable
```

Search should start only when the backend-defined minimum query length is reached.

The interface must not hard-code behavior that contradicts the backend contract.

## 11. Player Profile Page

The profile page should use three information levels.

### Level 1 — Player identity

Example:

```text
Michael Olise
France · Midfielder
```

Primary metrics:

- age;
- tournament minutes;
- tournament rating;
- market value;
- position;
- national team.

Primary action:

```text
Find Transfer Alternatives
```

### Level 2 — Player intelligence

Primary analytical fields:

```text
Archetype
Role
Spatial profile
Role confidence
```

Conceptual example:

```text
Archetype
Wide Creator

Discovered Role
Advanced Central Playmaker

Spatial Profile
Advanced Central Zone

Role Confidence
87.2%
```

### Level 3 — Analytical overview

The first profile version may include:

- key strengths;
- role description;
- profile reliability;
- tournament context;
- optional data availability notices.

Radar charts and heatmaps are deferred until Phase 5E.2.

The profile page must remain useful before advanced visualizations are available.

## 12. Transfer Analysis Form

The selected player must remain visible while configuring filters.

### Target summary

```text
Analyzing replacement options for

Michael Olise
France · Midfielder
```

### Initial filters

```text
Minimum tournament minutes
Minimum role confidence
Maximum market value
Recommendations per mode
```

Each filter should include a short explanation.

Example:

```text
Minimum tournament minutes

Removes candidates with limited tournament samples.
```

Primary action:

```text
Run Transfer Analysis
```

Secondary action:

```text
Reset Filters
```

### Layout

The form should start as a simple single-column layout.

A controlled two-column layout may be used on wider screens where labels and descriptions remain readable.

The form must include:

- visible labels;
- validation messages;
- disabled submission while pending;
- preservation of the selected player;
- understandable backend error feedback.

## 13. Recommendation Results Page

This is the most important product page in Phase 5.

### Page header

```text
Transfer Alternatives for Michael Olise
```

Optional summary fields may include:

```text
42 candidates evaluated
16 candidates qualified
4 recommendation groups
```

These values must only be shown when supported by the real API response.

### Recommendation grouping

The final mode names must follow the production API contract.

The interface should provide:

```text
Recommendation tabs or segmented navigation
    ↓
Selected mode explanation
    ↓
Ranked candidate cards
```

Each mode should include a user-friendly description.

Conceptual example:

```text
Best Value

Strong analytical fit with a more accessible market profile.
```

### Recommendation card

Conceptual structure:

```text
┌────────────────────────────────────────────────┐
│ 01  Candidate Name                             │
│     National Team · Position                   │
│                                                │
│ Suitability       86%                          │
│ Market Value      €42M                         │
│ Role Match        Strong                       │
│                                                │
│ Why this player?                               │
│ Similar creative output with a lower market    │
│ value and a compatible tactical role.          │
│                                                │
│ [ View Profile ]       [ Compare Players ]     │
└────────────────────────────────────────────────┘
```

The first card view should prioritize no more than four or five key fields.

Detailed analytical fields may be revealed through expandable sections or secondary views.

The frontend must not calculate rankings or rewrite recommendation explanations.

## 14. Player Comparison Page

The comparison page must interpret the comparison rather than placing two raw JSON responses side by side.

### Header

```text
Michael Olise
      VS
Candidate Player
```

### Comparison sections

```text
Identity
Market profile
Tournament performance
Role and archetype
Spatial compatibility
Similarity
Recommendation reasoning
```

### Desktop layout

```text
┌────────────────┬──────────────────┬────────────────┐
│ Michael Olise  │ Metric           │ Candidate      │
├────────────────┼──────────────────┼────────────────┤
│ 24.6           │ Age              │ 22.1           │
│ €144M          │ Market value     │ €31M           │
│ 7.57           │ Rating           │ 7.37           │
│ Wide Creator   │ Archetype        │ Wide Creator   │
└────────────────┴──────────────────┴────────────────┘
```

### Mobile layout

Wide comparison tables must not be used.

Preferred stacked structure:

```text
Age
Michael Olise       24.6
Candidate           22.1

Market Value
Michael Olise       €144M
Candidate           €31M
```

The comparison should help users understand:

- where the candidate is stronger;
- where the target remains stronger;
- whether the price difference is meaningful;
- whether the role is compatible;
- whether the recommendation contains important trade-offs.

## 15. Methodology Page

The methodology page must explain the system in product language rather than copying GitHub documentation.

It should answer:

```text
What does the engine analyze?
What does similarity mean?
What is an archetype?
What is a discovered role?
How are spatial and heatmap profiles used?
Why is the cheapest player not always the best replacement?
What are the limitations?
```

A visible limitation statement should be included:

> Tournament-based analysis reflects performance within the available World Cup 2026 dataset and should support, not replace, professional scouting judgment.

The methodology page should improve trust without overwhelming users with implementation details.

## 16. API Status Page

The status page should remain small and readable.

### Primary information

```text
API availability
Analytics catalog readiness
Environment
Service version
Last checked time
```

### Optional technical details

```text
Commit SHA
Dataset bundle SHA
Deployment ID
Request ID
```

Technical identifiers should appear in an expandable section or secondary panel.

Raw JSON should not be the default presentation.

The status page must clearly distinguish:

```text
Process available
Analytics catalog ready
Service unavailable
Temporary network failure
```

## 17. Shared Component Language

### Layout components

```text
SiteHeader
MobileNavigation
PageContainer
PageHeader
Breadcrumbs
SiteFooter
```

### Product domain components

```text
PlayerSearchInput
PlayerSearchResult
PlayerIdentityCard
PlayerMetricGrid
RoleProfileCard
AnalysisFilterForm
RecommendationModeTabs
RecommendationCard
ComparisonMetric
ApiStatusPanel
```

### State components

```text
LoadingSkeleton
EmptyState
ErrorState
InlineNotice
UnavailableValue
```

### Component organization principle

Every component should belong clearly to one of these groups:

```text
Generic UI
Product domain
Page composition
```

Components should not be stored in one unstructured directory.

## 18. Information Density

The product contains detailed scouting data, but all data should not be shown at the same visual level.

The selected approach is:

```text
Summary first
    ↓
Important metrics
    ↓
Recommendation explanation
    ↓
Optional analytical detail
```

This progressive disclosure strategy should be used across:

- player profiles;
- recommendation cards;
- comparison pages;
- methodology explanations;
- technical status information.

Example recommendation-card priority:

```text
Player
Score
Market value
Role match
Reason
```

Detailed similarity breakdowns should appear only when users request more information.

## 19. Player Imagery

The MVP will not depend on football player photographs.

Reasons include:

- licensing uncertainty;
- inconsistent image availability;
- broken image risk;
- difficulty maintaining visual consistency;
- risk of the interface appearing image-focused rather than analysis-focused.

Initial player identity may use:

```text
Initials
National team
Position badge
Subtle pitch pattern
```

Conceptual example:

```text
┌─────────┐
│   MO    │
└─────────┘
Michael Olise
France · M
```

Player photographs may be reconsidered later only when a reliable and legally appropriate source exists.

## 20. Responsive Strategy

Responsive behavior must be designed from the beginning.

### Desktop

```text
Maximum content width: approximately 1280px
Multi-column player profile layouts
Side-by-side comparison
Sticky analysis summary where useful
```

### Tablet

```text
Two-column metric grids
Single-column recommendation list
Reduced navigation density
```

### Mobile

```text
Single-column layout
Full-width primary buttons
No overflowing tables
Stacked comparison metrics
Touch-friendly controls
Collapsible navigation
```

Desktop layouts must not be created first and repaired for mobile at the end.

Every shared component should be reviewed at mobile, tablet and desktop widths.

## 21. Accessibility Direction

Important scores must not be communicated through color alone.

Incorrect:

```text
Green = good
Red = bad
```

Preferred:

```text
Strong match · 86%
Moderate match · 64%
Limited match · 38%
```

Baseline accessibility requirements:

- visible focus states;
- keyboard-accessible navigation;
- semantic headings;
- associated form labels;
- understandable validation errors;
- sufficient text contrast;
- descriptive button labels;
- non-color-only status communication;
- reduced-motion consideration;
- accessible loading announcements where appropriate;
- meaningful alternative text for analytical images.

Accessibility must be included in shared components rather than postponed until the end.

## 22. Loading, Empty and Error Presentation

Every API-driven page must define deliberate states.

### Loading

Preferred patterns:

- skeleton cards;
- inline progress indicators;
- disabled form controls;
- preserved page structure.

### Empty

Examples:

- no search results;
- no candidate meets the selected criteria;
- optional profile field unavailable.

An empty state should explain what happened and suggest a next action.

### Client error

Examples:

- query too short;
- invalid analysis filters;
- player not found;
- invalid route identity.

The interface should help the user correct the request.

### Service error

Examples:

- API not ready;
- dataset unavailable;
- network failure;
- unexpected backend failure.

Internal implementation details must not be exposed.

A backend request ID may be shown in a small diagnostic section when available.

## 23. Initial Design and Development Order

After Phase 5A.3, implementation should follow this sequence:

```text
1. Design tokens
2. Site layout
3. Landing page shell
4. Player search shell
5. Player profile shell
6. Analysis form shell
7. Results shell
8. Comparison shell
9. Loading and error components
10. Responsive review
```

Temporary static data may be used while page shells are being built.

Real API integration begins in later Phase 5B and Phase 5C tasks.

## 24. Visual and Product Principles

### Clarity before density

The interface should prioritize understanding over showing every available field.

### Explanation before decoration

Recommendation reasoning is more important than decorative visual effects.

### Product before documentation

The landing page and methodology page should not reproduce repository documentation.

### Data before imagery

The product should remain useful without player photographs.

### Responsive by default

All shared components should support mobile layouts from the beginning.

### Accessibility by default

Accessibility is part of component quality, not an optional final task.

### Backend as source of truth

The frontend must present backend results without recalculating analytical conclusions.

## 25. Phase 5A.3 Acceptance Criteria

- [x] Product identity defined.
- [x] Visual direction selected.
- [x] Initial color system defined.
- [x] Typography direction selected.
- [x] Main navigation defined.
- [x] Final MVP route map defined.
- [x] Landing page hierarchy defined.
- [x] Player search hierarchy defined.
- [x] Player profile hierarchy defined.
- [x] Transfer-analysis form hierarchy defined.
- [x] Recommendation result hierarchy defined.
- [x] Player comparison hierarchy defined.
- [x] Methodology page scope defined.
- [x] API status page scope defined.
- [x] Shared component language defined.
- [x] Responsive strategy defined.
- [x] Accessibility baseline defined.
- [x] Player photography excluded from the MVP.
- [x] Progressive disclosure selected for dense analytical content.

## 26. Final Decision Summary

```text
Product identity
WC26 Transfer Intelligence

Visual direction
Light, professional and analytical football product

Primary palette
Deep green, navy and restrained lime accent

Typography
Geist Sans and Geist Mono

Navigation
Home, Players, Methodology and API Status

Core journey
Search → Profile → Analyze → Results → Compare

Layout
Readable cards, responsive grids and progressive disclosure

Player imagery
Not required for the Phase 5 MVP

Design priority
Clarity before data density

Mobile strategy
Stacked content and no overflowing tables

Accessibility
Built into shared components from the beginning
```

This information architecture and visual direction are accepted as the product-design foundation for the WC26 Phase 5 web application.
