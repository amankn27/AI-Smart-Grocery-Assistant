# Architecture (Phase 0)

```
                         ┌──────────────────────────────────────────┐
   Browser (React/TS)    │  FastAPI backend                         │
  ┌───────────────────┐  │                                          │
  │ CameraCapture     │  │  routers/                                │
  │ NutritionPanel    │──┼─▶ vision  (/detect, /ocr)                │
  │ Cart              │  │   analyze (/analyze)                     │
  │ ChatBox           │  │   cart    (/cart/*)                      │
  └───────────────────┘  │   chat    (/chat)                        │
        │  /api proxy     │   products(/products)                   │
        ▼                 │                                          │
                          │  services/ (DETERMINISTIC, tested)       │
                          │   billing · nutrition · health_scoring · │
                          │   catalog · cart                         │
                          │                                          │
                          │  providers/ (PROBABILISTIC, swappable)   │
                          │   llm ──▶ Gemini | Echo(offline)         │
                          │   ocr ──▶ Paddle → EasyOCR → Null        │
                          │   detector ──▶ YOLO | Stub               │
                          │      ▲ selected by config/providers.py   │
                          └──────┼───────────────────────────────────┘
                                 │
                     config/settings.py  (.env)
                                 │
                  Postgres (catalog/history*)   Redis (cache*)
                                        (* wired; used more in Phase 1)
```

## The two halves (brief §3, "deterministic core, probabilistic edges")

- **Deterministic core** — `app/services/*`: pure functions, no I/O, fully unit-tested.
  GST/MRP math, nutrition-text parsing, and health scoring live here so results are
  explainable and repeatable. The LLM never computes a number that ends up on the bill.
- **Probabilistic edges** — `app/providers/*`: every model (LLM, OCR, detector) sits behind
  an ABC in `providers/base.py`. `config/providers.py` is the *only* place that maps config
  to a concrete implementation, and every factory degrades to a safe fallback.

## Request flow: "scan a product"

1. UI captures a frame → `POST /detect` and `POST /ocr` (parallel).
2. `/detect` runs the detector; low-confidence boxes come back `needs_confirmation=true`.
3. `/ocr` runs the OCR chain, then hands the raw text to `parse_nutrition` → structured
   fields + per-field confidence.
4. UI sends the confident fields to `POST /analyze` → deterministic score + warnings.
5. User adds the item → `POST /cart/add`; totals recomputed by the billing core.
6. `POST /chat` answers questions, grounded with the nutrition context.

## Graceful degradation ladder

| Edge | Primary | Fallback 1 | Fallback 2 |
|---|---|---|---|
| Product ID | YOLO detection | Stub box → user confirms | Manual entry / catalog search |
| Nutrition | OCR (Paddle) | OCR (EasyOCR) | Barcode → catalog → manual |
| Q&A | Gemini | (retry) | Offline echo provider |

Nothing in the happy path can return an unhandled 500: missing key/dep/weights all resolve
to a working fallback at factory time.
