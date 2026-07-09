# Measured Results (Definition of Done §8/§10)

Reproduce with: `python data/eval/run_eval.py`. Numbers below are **real measurements** from
this repo, not claims. Machine: Windows 11, Python 3.11, in-process FastAPI TestClient.

## OCR nutrition-field extraction accuracy — **1.000** (target ≥ 0.80) ✅

| Sample | Fields recovered |
|---|---|
| clean_biscuit | 6/6 |
| ocr_misspelled | 5/5 |
| comma_decimal | 4/4 |
| salt_to_sodium | 3/3 |
| kj_energy | 3/3 |
| hindi_label | 4/4 |
| high_fibre_cereal | 7/7 |
| soft_drink | 4/4 |
| noisy_spacing | 6/6 |
| oats | 6/6 |
| milk | 5/5 |
| devanagari_numerals | 2/2 |
| **Overall** | **55/55 = 1.000** |

> **Honest scope:** this measures the deterministic **parser** (`parse_nutrition`) over a
> labeled set of realistic label *texts* — including OCR-style misspellings, comma decimals,
> kJ→kcal, salt→sodium, noisy spacing, and Hindi/Devanagari (incl. Devanagari numerals). It is
> **not** end-to-end image→text accuracy, which depends on the OCR engine (PaddleOCR/EasyOCR)
> and requires real product photos. That path is wired; the eval set for it goes in
> `data/eval/images/` + `labels.csv`. The 1.000 here says the parsing/normalization layer is
> solid; the image-OCR layer still needs its own measurement with the vision stack installed.

## Server round-trip latency — p95 **≤ 6 ms** (budget < 2000 ms) ✅

| Endpoint | p50 | p95 |
|---|---|---|
| POST /analyze | 2.6 ms | 4.4 ms |
| GET /products | 4.0 ms | 6.0 ms |
| POST /value | 2.6 ms | 3.6 ms |
| POST /recommend | 3.0 ms | 4.1 ms |
| POST /diet/plan | 2.8 ms | 3.8 ms |

> **Honest scope:** these are the **deterministic/fallback** endpoints (no heavy models), so
> they show the framework + business-logic overhead is negligible (single-digit ms). The
> <2s budget in §8 is for the **detection + OCR** round trip; with the real vision stack
> (`requirements-vision.txt`) that path is dominated by YOLO + PaddleOCR inference and must be
> measured on the target hardware — the harness structure is ready for it.

## Detection mAP@0.5 — N/A (target ≥ 0.60)

Not measured: stock YOLO doesn't know the 12 grocery classes, and no labeled product-image
eval set has been added. The harness path is wired; populate `data/eval/images/` + `labels.csv`
and install `requirements-vision.txt` to produce a number. A grocery fine-tune (Phase 1
follow-up) is the expected path to hit the target — documented, not faked.
