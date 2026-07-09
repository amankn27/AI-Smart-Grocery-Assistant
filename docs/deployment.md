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

## Render / Railway
- **Backend**: deploy `docker/Dockerfile.backend`. Set `DATABASE_URL` (managed Postgres),
  `GEMINI_API_KEY`, `DETECTOR_PROVIDER=stub` (or `yolo` with `INSTALL_VISION=true`).
- **Frontend**: static site from `frontend` (`npm run build`, publish `dist/`), or the nginx
  image in `docker/Dockerfile.frontend`. Point `/api` at the backend URL.
- **DB migrations**: Phase 0 uses `create_all` on startup; Alembic is introduced in Phase 1.

## Health & smoke check
```bash
curl -s localhost:8000/health
curl -s -X POST localhost:8000/analyze -H 'content-type: application/json' \
  -d '{"sugar_g":45,"sodium_mg":800}'
```
