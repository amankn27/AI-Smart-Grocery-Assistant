# 🛒 Smart Grocery Assistant

Point a camera at a grocery product → identify it, read the nutrition label, score its
health, and build a running INR bill with GST. A modular, containerized web app built as a
**vertical slice** (camera → detection → OCR → nutrition → cart → chat), not a demo throwaway.

> **Status: Phases 0–2 complete — 56 tests passing.** The deterministic core (billing,
> nutrition parsing, health scoring, catalog, gap-fill merge, alternative ranking, analytics,
> pantry/expiry, recipe assembly) is implemented and unit-tested. Model edges (YOLO,
> PaddleOCR, Gemini, barcode, embeddings, vector store, Whisper STT, TTS) are wired behind
> swappable interfaces and degrade gracefully when heavy deps or API keys are absent, so the
> app boots with zero configuration. Phase 1 adds barcode scanning, RAG healthier-alternatives,
> JWT auth + history, dashboards and PDF invoices; Phase 2 adds a voice assistant, a recipe
> generator, and pantry/expiry tracking with reminders.

## Why it's built this way (design principles)

- **Deterministic core, probabilistic edges** — GST/MRP math, nutrition parsing, and health
  scoring are pure, unit-tested functions. Models never compute a number on the bill.
- **Every model behind an interface** — LLM / OCR / detector are ABCs selected by
  `config/providers.py` from `.env`. No provider is hard-coded into business logic.
- **Graceful degradation** — OCR → barcode/catalog → manual entry; low-confidence detection
  → user confirm; no Gemini key → offline echo answers. Nothing dead-ends.

## Quick start

### Run everything (Docker)
```bash
cp .env.example .env      # optional: add GEMINI_API_KEY for real chat answers
docker compose up --build
# frontend → http://localhost:8080   backend → http://localhost:8000/docs
```
> Compose defaults to the light image (stub detector, no heavy vision deps). See
> [docs/deployment.md](docs/deployment.md) to enable real YOLO/PaddleOCR.

### Backend only (no Docker)
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate      # PowerShell
pip install -r requirements.txt
uvicorn app.main:app --reload                        # http://localhost:8000/docs
pytest                                               # 23 tests
```

### Frontend dev
```bash
cd frontend && npm install && npm run dev            # http://localhost:5173
```

## Layout
```
backend/    FastAPI app — routers, deterministic services, provider interfaces, db
frontend/   React + TS + Tailwind — tabs: Scan (camera/nutrition/cart/chat/voice/recipe),
            Pantry (expiry tracking), Dashboard (analytics); JWT auth bar
data/seed/  Open Food Facts (India) subset + reproducible build_seed.py  (53 products)
data/eval/  accuracy/latency harness + targets
docker/     Dockerfiles + nginx config
docs/       PHASE0_PLAN, architecture, api, env-vars, deployment
models/     weights (git-ignored, documented)
```

## Documentation
- **[Phase 0 plan & decisions](docs/PHASE0_PLAN.md)** — scope, locked choices, what's real vs stubbed
- **[Architecture](docs/architecture.md)** — the two halves + request flow + degradation ladder
- **[API reference](docs/api.md)** · **[Env vars](docs/env-vars.md)** · **[Deployment](docs/deployment.md)**

## Configuration highlights
| | Default | |
|---|---|---|
| LLM | Gemini (`GEMINI_API_KEY`), else offline echo | swap via `LLM_PROVIDER` |
| OCR | Paddle → EasyOCR → manual | `OCR_PROVIDER` |
| Detector | YOLOv8 (or stub) | `DETECTOR_PROVIDER` |
| Locale | India · INR · GST · MRP | `CURRENCY` / `LOCALE` |

See [`.env.example`](.env.example) for the full list.

## Known limitations / honest status
- **Seed data** is a real Open Food Facts India subset — it carries OFF's noise; the builder
  clamps implausible values, and OFF has **no reliable MRP**, so prices are nominal seed values.
- **Detection**: Phase 0 uses stock pretrained YOLO, which doesn't know the 12 grocery
  categories — mAP against them will be low until a Phase 1 fine-tune. Documented, not hidden.
- **Docker compose** is written but **not verified** in the authoring environment (no Docker
  on PATH there).
- Auth, RAG recommendations, barcode camera scanning, dashboards, PDF invoice → **Phase 1**.
  Voice, recipes, pantry → **Phase 2**. (See [docs/PHASE0_PLAN.md](docs/PHASE0_PLAN.md).)

## Roadmap
- **Phase 0:** detection · OCR · nutrition parse · cart/GST · chat · minimal UI ✅
- **Phase 1:** barcode scan · RAG alternatives · JWT auth + history · dashboard · PDF invoice ✅
- **Phase 2:** voice (Whisper→LLM→TTS) · recipes from cart · pantry/expiry + reminders ✅
- **Phase 3 (backlog):** multi-language OCR · offline mode · price comparison · diet planner · shared lists

Plans: [Phase 0](docs/PHASE0_PLAN.md) · [Phase 1](docs/PHASE1_PLAN.md) · [Phase 2](docs/PHASE2_PLAN.md).
