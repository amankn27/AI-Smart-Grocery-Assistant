# Phase 3 — Implementation Plan (selected backlog items)

Phase 3 is a **backlog, not a commitment** (brief §4). Building the feasible, high-value items
that fit the architecture; native mobile, wearable/fridge, and offline PWA are **out of scope**
for this codebase. Same principles: deterministic core (tested), model edges behind interfaces.

Selected this round: **price comparison & value**, **diet/meal planner**, **multi-language OCR**.

## Slices (shipped in order, each tested before the next)

### 1. Price comparison & value analysis
- `services/value.py` — **pure, tested**: per-product `health_per_rupee`, price percentile
  within category, cheapest option, and the best-value pick among same-category alternatives.
- `POST /value` — product → value analysis (uses the catalog + deterministic health scoring).

### 2. Diet / meal planner
- `services/diet.py` — **pure, tested** greedy basket builder: pick highest-health catalog
  items toward a calorie target without exceeding it, report total kcal/protein and the gap.
- `POST /diet/plan` — { target_kcal, min_protein_g, diet, cuisine } → deterministic basket +
  LLM narrative on how to use it (echo fallback keeps it working with no key).

### 3. Multi-language OCR
- Config-driven OCR language (`OCR_LANG`) passed to Paddle/EasyOCR (provider passthrough).
- **Tested deterministic parts**: Hindi (Devanagari) nutrition-label synonyms added to the
  parser (ऊर्जा/प्रोटीन/वसा/…), and a `detect_script()` language hint returned by `/ocr`.

## Interface additions
| Kind | Setting | Default | Notes |
|---|---|---|---|
| OCR language | `OCR_LANG` | `en` | `en` \| `hi` \| … (Paddle/EasyOCR lang codes) |

## Testing gates (added this phase)
`test_value.py`, `test_diet.py`, and multi-language cases added to `test_nutrition.py`.

## Explicitly out of scope (stay in backlog)
Offline PWA/service worker, coupon detection, family shared lists (picked out this round),
native mobile app, wearable/fridge integrations.

## Status — selected slices complete (68 backend tests passing)
- [x] Slice 1 — price comparison & value  (`/value`, `services/value.py`)
- [x] Slice 2 — diet / meal planner  (`/diet/plan`, `services/diet.py`)
- [x] Slice 3 — multi-language OCR  (`OCR_LANG`, Devanagari label + numeral parsing, `/ocr` language hint)

### Not built (remain in backlog by choice)
Family shared lists, offline PWA, coupon detection, native mobile, wearable/fridge.
