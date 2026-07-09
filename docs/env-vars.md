# Environment Variables

All configuration is env-driven (`.env`, see `.env.example`). The app boots with none set.

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | Free-form environment label |
| `CURRENCY` | `INR` | Display currency |
| `LOCALE` | `en_IN` | Locale |
| `LLM_PROVIDER` | `gemini` | `gemini` \| `echo`. `echo` = offline deterministic fallback |
| `GEMINI_API_KEY` | *(empty)* | If unset, `/chat` uses the offline echo provider |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model id |
| `OCR_PROVIDER` | `chained` | `chained` \| `paddle` \| `easyocr` \| `null` |
| `OCR_LANG` | `en` | OCR engine language (`en` \| `hi` \| …); parser also reads Devanagari labels |
| `DETECTOR_PROVIDER` | `yolo` | `yolo` \| `stub`. Compose default is `stub` (no heavy deps) |
| `YOLO_WEIGHTS` | `yolov8n.pt` | Checkpoint path/name for Ultralytics |
| `DETECTOR_CONF_THRESHOLD` | `0.25` | Min detection confidence to report a box |
| `LOW_CONFIDENCE_THRESHOLD` | `0.40` | Below this a box is flagged `needs_confirmation` |
| `DATABASE_URL` | `sqlite:///./grocery.db` | SQLite locally; Postgres in compose |
| `REDIS_URL` | *(empty)* | Redis cache URL (Phase 1 usage) |
| `SEED_PRODUCTS_CSV` | `data/seed/products.csv` | Catalog seed path |
| `BARCODE_PROVIDER` | `pyzbar` | `pyzbar` \| `null` (manual entry) |
| `EMBEDDINGS_PROVIDER` | `hashing` | `sentence_transformers` \| `hashing` (deterministic) |
| `VECTOR_STORE` | `memory` | `chroma` \| `memory` (pure-python cosine) |
| `RAG_CORPUS_PATH` | `data/rag/corpus.jsonl` | RAG seed corpus |
| `CHROMA_PATH` | `./.chroma` | Chroma persistence dir (when `VECTOR_STORE=chroma`) |
| `JWT_SECRET` | `change-me-in-production` | HS256 signing secret — **set in prod** |
| `JWT_ACCESS_TTL_MIN` | `30` | Access token lifetime (minutes) |
| `JWT_REFRESH_TTL_DAYS` | `7` | Refresh token lifetime (days) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | *(empty)* | Optional Google OAuth |
| `STT_PROVIDER` | `whisper` | `whisper` \| `null` (client sends typed text) |
| `WHISPER_MODEL` | `base` | faster-whisper model size (`tiny`/`base`/`small`/…) |
| `TTS_PROVIDER` | `browser` | `browser` (Web Speech API) \| `gtts` (server MP3) |

Both the seed catalog and RAG corpus paths resolve from either the repo root or `backend/`
(so `uvicorn` works from either cwd).

## Provider selection matrix

| Want | Set |
|---|---|
| Zero-config offline run | nothing (echo LLM, stub detector, null OCR) |
| Real LLM answers | `GEMINI_API_KEY=...` |
| Real detection | install `requirements-vision.txt`, `DETECTOR_PROVIDER=yolo` |
| Real OCR | install `requirements-vision.txt`, `OCR_PROVIDER=chained` |
