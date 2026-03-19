FILE: docs/design/design-system-anchor.md

DESIGN SYSTEM ANCHOR — HRMS UI
VERSION: V1 (FINAL)
STATUS: LOCKED FOR POLISH PASSES

PURPOSE
This file is the single source of truth for all HRMS UI refinement and page polish.
All page updates, redesigns, cleanup passes, and visual fixes must anchor to this file.
If a prompt conflicts with this file, this file wins.

This system defines:
- visual consistency
- layout structure
- hierarchy rules
- page behavior (archetypes)

==================================================
1. DESIGN PRINCIPLES
==================================================

1. The UI must feel enterprise, calm, precise, and structured.
2. The UI must avoid visual chaos, over-carded layouts, and equal-weight sections.
3. The UI must prioritize hierarchy, clarity, alignment, and scanning speed.
4. The UI must feel modern and premium without looking flashy or decorative.
5. The UI must support heavy business workflows without looking dense or exhausting.
6. Every page must feel part of the same product.
7. Polish must come from spacing, alignment, hierarchy, and restraint — not visual noise.

==================================================
2. GLOBAL VISUAL RULES
==================================================

MANDATORY RULES

- Use a 12-column layout system for page-level structure.
- Keep section spacing consistent.
- Use only approved spacing values.
- Reuse existing visual patterns.
- Do not invent page-specific component styles.
- Do not create random card variants.
- Do not use floating layouts that break alignment.
- Do not give equal visual weight to all sections.
- Do not create heavy table feel unless explicitly required.
- Do not use decorative gradients, loud colors, or over-styled containers.
- No dark theme.
- No visual clutter.
- No uneven card padding.
- No inconsistent badge styles.
- No inconsistent button treatment.
- No random border radius values.
- No random shadow values.

==================================================
3. COLOR SYSTEM
==================================================

Use the existing project tokens only.
Do not change tokens.
Apply them consistently.

INTENT RULES

- Primary blue = key action, active state, important emphasis
- Neutral surfaces = default cards, panels, containers
- Light blue tint = soft analytical emphasis
- Green = positive / complete / success
- Amber = pending / warning / attention
- Red = urgent / risk / negative
- Gray text = secondary / supporting information

RULES

- Use color sparingly.
- Use neutral first, accent second.
- Never let color dominate structure.
- Status color belongs in badges and small signals, not large containers.
- Background color should stay calm and low-noise.

==================================================
4. TYPOGRAPHY SYSTEM
==================================================

TYPOGRAPHIC HIERARCHY

Page title
- large
- bold
- highest emphasis

Section title
- medium
- semibold
- clear but secondary to page title

Card title / block title
- small-medium
- semibold

Body text
- regular
- highly readable
- compact but not cramped

Meta text / labels
- smaller
- uppercase only where used consistently
- muted tone

NUMERIC METRICS
- prominent
- bold
- visually stronger than body text
- not oversized unless explicitly required

RULES

- Do not mix too many font sizes.
- Do not make labels louder than values.
- Do not let supporting copy compete with primary information.
- Uppercase labels should be subtle and consistent.
- Text must be scannable.

==================================================
5. SPACING SYSTEM
==================================================

APPROVED SPACING SCALE ONLY

- 4
- 8
- 12
- 16
- 20
- 24
- 32

RULES

- Prefer 24 between major sections.
- Prefer 16 inside containers.
- Prefer 12 for grouped items.
- Prefer 8 for label/value spacing.
- Do not use arbitrary spacing.
- Do not compress UI too tightly.
- Do not leave excessive dead space.

==================================================
6. BORDER RADIUS + SURFACES
==================================================

- Use one consistent radius system across all elements.
- No mixing sharp and overly rounded styles.
- Surfaces must feel soft and premium, not inflated.

RULES

- No exaggerated radius differences.
- No mismatched shapes.
- No random inset styles.

==================================================
7. SHADOW + BORDER SYSTEM
==================================================

- Shadows must be subtle.
- Prefer borders for structure.
- Hover may slightly increase emphasis.

RULES

- No heavy shadows.
- No inconsistent depth.
- Do not elevate everything.
- Data rows must not feel like cards.

==================================================
8. GRID + LAYOUT SYSTEM
==================================================

PAGE FRAME

1. Page header
2. Summary / controls
3. Primary workspace
4. Secondary sections
5. Supporting sections

RULES

- Use 12-column grid.
- Left = primary workflow
- Right = supporting context
- Avoid chaotic layouts
- Widths must feel intentional

==================================================
9. COMPONENT RULES
==================================================

CARDS
- consistent padding, radius, surface
- one family only

BUTTONS
- one primary action per area
- consistent sizing
- no competing emphasis

INPUTS
- one style
- consistent height and structure

BADGES
- one system only
- neutral / info / success / warning / danger

METRICS
- equal height in same row
- aligned numbers and labels

PANELS
- lighter than primary workspace
- consistent spacing

==================================================
10. DATA DISPLAY RULES
==================================================

- Prefer structured lists over heavy tables
- Use tables only when needed
- Mix metrics + lists + panels on analytical pages

DO NOT

- turn everything into tables
- turn everything into cards
- fragment rows visually

==================================================
11. ROW STRUCTURE RULE
==================================================

- consistent column structure
- aligned rows
- no floating elements
- equal row rhythm

==================================================
12. HIERARCHY RULES
==================================================

L1 → identity + primary action  
L2 → main workflow  
L3 → supporting context  

RULES

- L1 must dominate
- L2 must carry operations
- L3 must not compete
- never flatten hierarchy

==================================================
13. PAGE POLISH RULES
==================================================

1. Fix alignment first
2. Fix spacing second
3. Fix hierarchy third
4. Remove clutter
5. Prefer subtraction over addition

==================================================
14. RESPONSIVENESS RULES
==================================================

- Desktop first
- Preserve hierarchy on stacking
- No chaotic collapse

==================================================
15. PAGE CONSISTENCY RULE
==================================================

All pages must share:

- header logic
- spacing rhythm
- component system
- hierarchy logic

Reject new patterns unless system-wide.

==================================================
16. CODEX EXECUTION RULES
==================================================

- Always anchor to this file
- Reuse components
- Do not invent styles
- Do not break alignment
- Fix structure before visuals

==================================================
17. QC CHECKLIST
==================================================

- hierarchy clear
- spacing consistent
- alignment correct
- no clutter
- consistent components
- calm, enterprise feel

==================================================
18. FINAL LOCK
==================================================

This system is locked.
Do not drift from it.

==================================================
19. PAGE ARCHETYPE RULES (CRITICAL)
==================================================

Each page must follow ONE archetype.

COMMAND CENTER (Dashboard)
- hero required (L1)
- KPI strip required
- split layout (primary + priorities)
- action-driven

DATA DIRECTORY (Employees)
- search dominant (L1)
- filters horizontal
- table/list primary
- minimal cards
- high density

ANALYTICS / EVALUATION (Performance)
- metrics header required
- split layout (analysis + insights)
- mix list + panels
- comparison-focused

PIPELINE (Hiring)
- stage/group layout
- progression visibility
- status-driven

FORM / CONFIG (Settings)
- vertical layout
- grouped sections
- low density
- clarity-first

RULES

- each page must declare archetype
- layout must follow archetype
- do not mix archetypes
- archetype controls structure, not styling
