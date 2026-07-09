# Phase 0 — Implementation Plan (Smart Grocery Assistant)

> Goal: a **deployable vertical slice**: camera → detection → OCR → nutrition → cart → chat,
> with a deterministic, tested billing/nutrition core and every model call behind a swappable interface.

## Locked decisions (this session)

| Question | Decision |
|---|---|
| Locale | **India** — INR, GST, MRP (per brief §2) |
| Default LLM | **Gemini** (`google-generativeai`), key via `.env`; falls back to a zero-dep `echo` provider so the API boots with no key |
| Seed data | **Open Food Facts subset** (India), fetched by `data/seed/build_seed.py`; a small committed `products.csv` ships so the app runs offline |
| Detection classes | 12 common Indian grocery categories (see below); **pretrained YOLO**, no custom training in Phase 0 |
| Vector store | Deferred (Phase 1) |

### Starting detection class set (12)
`biscuits, chips_namkeen, chocolate, instant_noodles, soft_drink, juice, milk_dairy, bread, cereal, cooking_oil, tea_coffee, snack_bar`

> Note: stock COCO YOLO doesn't know these grocery classes. Phase 0 ships the **detector behind an interface**
> with a pretrained checkpoint that returns generic boxes + a `low_confidence` path that routes to manual/OCR
> confirmation. Fine-tuning on a labeled grocery set is a **measured** follow-up, not assumed (brief §4, §5).

## Architecture principle mapping (brief §3)

- **Deterministic core, probabilistic edges** → `services/billing.py`, `services/health_scoring.py`,
  and the parsing in `services/nutrition.py` are **pure functions with unit tests** and no model/network deps.
  Only `providers/{llm,ocr,detector}` touch models.
- **Every model call behind an interface** → `providers/base.py` defines `LLMProvider`, `OCREngine`, `Detector`
  ABCs; `config/providers.py` is the factory selecting an implementation from env.
- **Graceful degradation** → OCR → barcode/catalog lookup → manual entry; low-confidence detection → user confirm.
  LLM missing key → `echo` provider (deterministic canned answer) so no dead-ends.

## Build order (what runs, what's stubbed in Phase 0)

| Component | Phase 0 status | Notes |
|---|---|---|
| `services/billing.py` (GST/MRP/cart totals) | **Real + tested** | Pure functions, INR rounding, GST slabs |
| `services/nutrition.py` (OCR text → structured) | **Real + tested** | Regex/heuristic parser, per-field confidence |
| `services/health_scoring.py` | **Real + tested** | Deterministic score vs. Indian RDA + warnings |
| `services/catalog.py` (seed lookup + barcode) | **Real** | Loads `data/seed/products.csv` |
| `providers/llm/{gemini,echo}.py` | **Real (echo) / wired (gemini)** | Gemini used when `GEMINI_API_KEY` set |
| `providers/ocr/{paddle,easyocr}.py` | **Wired, lazy-loaded** | Heavy deps optional; interface + fallback chain real |
| `providers/detector/yolo.py` | **Wired, lazy-loaded** | Ultralytics optional; returns boxes+conf |
| `routers/{cart,analyze,chat,products}` | **Real** | Depend only on deterministic core + providers |
| `routers/{detect,ocr}` | **Real endpoints, model lazy** | Boot without ultralytics/paddle installed |
| Frontend (Vite React TS) | **Skeleton** | Camera, detection overlay, nutrition panel, cart wired to API |
| Postgres + SQLAlchemy | **Wired** | Models + session; Alembic in Phase 1; SQLite fallback for local/tests |
| Docker + compose | **Written** | backend + postgres + redis; not tested in this env (no docker) |

## API surface (Phase 0)

```
GET  /health
POST /detect        image → boxes + confidence + class
POST /ocr           crop  → structured text fields (+ per-field confidence)
POST /analyze       nutrition → health score + warnings
POST /chat          question (+context) → answer (LLM provider)
POST /cart/add      product → updated cart
POST /cart/remove   item → updated cart
POST /cart/update   item qty → updated cart
GET  /cart          cart + subtotal/GST/total
GET  /products      catalog lookup (name / barcode)
```
`/recommend`, `/report`, `/history`, auth → Phase 1. `/voice`, `/recipe` → Phase 2.

## Testing gates (brief §10)

- `pytest tests/` green: `test_billing.py`, `test_nutrition.py`, `test_health_scoring.py`, `test_api.py`.
- Deterministic-core tests run with **no model/network deps** installed.
- Accuracy/latency eval harness stub in `data/eval/` with explicit targets (brief §8): detection mAP,
  OCR field accuracy, < 2s server round trip — to be populated when weights/eval images are added.

## Explicit deferrals / flagged conflicts

- Custom YOLO training, barcode camera scanning, RAG, auth, dashboards → **Phase 1** (not built now).
- SAM2 / CLIP / XTTS → deferred by default (brief §4 model note).
- Docker compose is written but **unverified in this environment** (no Docker on PATH) — flagged in README.
