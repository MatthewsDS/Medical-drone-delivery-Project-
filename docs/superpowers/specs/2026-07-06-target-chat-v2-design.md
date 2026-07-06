# Target Chat v2 — Sidebar UI + Posture Filters (Design)

**Date:** 2026-07-06 · **Owner:** Matthews · **Status:** approved (Matthews pre-authorised)
**File:** `01_learning_and_simulation/coding_and_cv/target_chat.py` (stays single-file)

## Goal
One screen: full-bleed live camera + collapsible details sidebar. The details
language gains postures — `waving` and `lying` — alongside the existing
colours/garments/objects. Partial details always work (only what you type is
checked). AI search (YOLO-World) kept as a second button. This is the
foundation UI until the AI HAT+ hardware upgrade.

## Filter language (keyword mode)
`spec = {upper[], lower[], objects[], posture[]}` — all optional, AND-ed when given.
- Colours/garments/objects: unchanged.
- `waving`/`wave` → posture "waving". `lying`/`laying` → posture "lying".

## Matching pipeline (per frame)
1. Stateless filters: colour regions (pose-keypoint located), `lying`
   (box width > 1.15 × height — ponytail: aspect heuristic, upgrade to
   keypoint-axis check if false positives bite), objects near person.
2. Largest passing person = candidate (amber box if waving still pending).
3. If `waving` required: candidate's wrists feed the existing
   `waving.WaveDetector` pair (imported, not copied); target confirmed
   (green) only while the wave test passes. Detectors reset on spec change.
   Known ceiling: detector state follows the *current* candidate; two
   similar candidates alternating can reset progress — acceptable foundation.

## UI (single served page, no frameworks)
- Camera `<img>` fills viewport (keeps the freeze-proof /frame polling).
- Left sidebar, 300 px, slides closed (CSS transform); ☰ toggle always visible.
- Sidebar: brand header → details input → [Set target] [AI search β] [Clear]
  → active-filter chips → status line → vocabulary cheat-sheet.
- Design system via ui-ux-pro-max: dark mission-control theme.

## Testing
Selfcheck additions: parse postures (incl. partial-only specs), lying aspect
function, posture veto in person matching. Existing endpoint smoke rerun.
Wave temporal logic already covered by waving.py selfcheck.
