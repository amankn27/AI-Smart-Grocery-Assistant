# Deployment Guide

Target footprint: one small instance (Render/Railway hobby, or a single EC2 box) — brief §2.

## Local (Docker, one command)
```bash
cp .env.example .env        # optionally add GEMINI_API_KEY
docker compose up --build
# frontend  → http://localhost:8080
# backend   → http://localhost:8000  (/docs for Swagger)
```
> Compose ships with `DETECTOR_PROVIDER=stub` and no vision deps for a small, fast image.
> For real detection/OCR, build with `INSTALL_VISION=true` (much larger image) and set
> `DETECTOR_PROVIDER=yolo`.

## Local (no Docker)
```bash
# backend
cd backend
python -m venv .venv && . .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# frontend (separate terminal)
cd frontend && npm install && npm run dev
```

## Render (one-click Blueprint)

The repo ships a `render.yaml` Blueprint that provisions **backend (Docker) + Postgres +
frontend (static)** on the free tier.

1. Push this repo to GitHub (see below).
2. Render dashboard → **New → Blueprint** → select the repo. Render reads `render.yaml`.
3. It creates `grocery-db`, `grocery-backend`, `grocery-frontend` and asks for the secrets
   marked `sync: false`. Set them in two passes (because each service needs the other's URL):
   - First deploy → note the backend URL (e.g. `https://grocery-backend.onrender.com`).
   - Set the frontend's **`VITE_API_BASE`** to that backend URL and redeploy the frontend.
   - Set the backend's **`CORS_ORIGINS`** to the frontend URL (e.g.
     `https://grocery-frontend.onrender.com`) and redeploy the backend.
   - Optionally set **`GEMINI_API_KEY`** on the backend (without it, chat uses the offline echo).
4. Open the frontend URL — the full app is live.

> This is the **one step I can't do for you**: it needs your Render account. Everything the
> Blueprint needs is in the repo. Railway is equivalent (Docker service + Postgres plugin +
> static site; set the same three env vars).

- **Real detection/OCR in prod**: build the backend with `INSTALL_VISION=true` and set
  `DETECTOR_PROVIDER=yolo` / `OCR_PROVIDER=chained` (larger image, slower cold start).
- **DB migrations**: `init_db` create_all runs on startup; Alembic (`backend/alembic/`) is
  available for real migrations (`alembic upgrade head`).

## Measure (Definition of Done §8)
```bash
python data/eval/run_eval.py      # OCR-parser accuracy + endpoint latency, real numbers
```
See [RESULTS.md](RESULTS.md) for the latest measured figures.

## Health & smoke check
```bash
curl -s localhost:8000/health
curl -s -X POST localhost:8000/analyze -H 'content-type: application/json' \
  -d '{"sugar_g":45,"sodium_mg":800}'
```
