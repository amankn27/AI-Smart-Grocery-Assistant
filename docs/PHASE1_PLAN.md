

# Phase 1 — Implementation Plan (Depth)

Builds on the Phase 0 vertical slice. Same principles: **deterministic core, probabilistic
edges; every model behind an interface; graceful degradation; boots with zero deps.**

## Slices (shipped in order, each tested before the next)

### 1. Barcode scanning + gap-filling lookup
- `POST /barcode` — image → decoded EAN/UPC/QR → catalog product (fills what OCR missed).
- Decoder behind an interface: **pyzbar** (optional) → **null** (manual entry) fallback.
- `services/merge.py` — deterministic merge of OCR nutrition + catalog nutrition (catalog
  fills only missing/low-confidence fields; OCR wins when confident). **Pure + tested.**

### 2. RAG healthier-alternatives (`/recommend`)
- **Deterministic** ranking (`services/recommend.py`): same-category catalog products with a
  **higher health score** than the scanned item, ranked by score delta. Tested, no model.
- **RAG-grounded explanation**: retrieve relevant nutrition-guidance snippets and let the LLM
  phrase *why* — never invents the alternatives or their numbers.
- Vector store: **Chroma** (the one store we ship — brief §6) as the optional persistent
  backend, with a pure-python cosine `InMemoryStore` fallback so it runs with zero deps.
- Embeddings behind an interface: **sentence-transformers** (optional) → deterministic
  **hashing embedder** fallback (bag-of-words → fixed-dim, L2-normalized) for zero-dep/tests.
- Seed corpus in `data/rag/` (WHO/FSSAI-style nutrition guidance snippets).

### 3. Auth + persistence + history/saved products
- SQLAlchemy models: `users`, `sessions/carts`, `saved_products`, `scans`. **Alembic** intro'd.
- JWT (access+refresh, hashed passwords via passlib/bcrypt) + one OAuth provider (Google).
- `services/*` stay pure; persistence lives in `db/repositories/`.
- `GET /history`, `POST /products/save`, `GET /products/saved`.

### 4. Dashboard analytics + PDF invoice
- `GET /dashboard` — spend, calories, category mix aggregations (deterministic, tested).
- `GET /report` — cart → PDF invoice (reportlab), GST breakup from the billing core.

## Interface additions (config-selectable)
| Kind | Default | Fallback | Env |
|---|---|---|---|
| Barcode | pyzbar | null (manual) | `BARCODE_PROVIDER` |
| Embeddings | sentence-transformers | hashing (deterministic) | `EMBEDDINGS_PROVIDER` |
| Vector store | chroma | in-memory cosine | `VECTOR_STORE` |

## Testing gates (added this phase)
`test_merge.py`, `test_recommend.py`, `test_rag.py` (hashing embedder + in-memory store are
deterministic), plus API tests for `/barcode` and `/recommend` (importorskip heavy deps).

## Status — all slices complete (43 backend tests passing)
- [x] Slice 1 — barcode + deterministic merge  (`/barcode`, `services/merge.py`)
- [x] Slice 2 — RAG recommendations  (`/recommend`, embedder + store interfaces, seed corpus)
- [x] Slice 3 — auth + persistence  (JWT access/refresh, bcrypt, users/scans/saved, Alembic)
- [x] Slice 4 — dashboard + PDF  (`/dashboard` analytics, `/report` reportlab invoice)

### Notes / honest status
- Google OAuth route is scaffolded via env (`GOOGLE_CLIENT_ID/SECRET`); the password flow is
  the tested default. Full OAuth redirect handling is a small follow-up.
- Migrations: `init_db` create_all is the dev path; Alembic is wired (`backend/alembic/`) for
  real migrations (`alembic revision --autogenerate`).
- Frontend: barcode scan + healthier-options panel wired; auth screens + dashboard charts are
  the remaining UI polish (backend fully covered).
