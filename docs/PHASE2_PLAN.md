
# Phase 2 — Implementation Plan (Interaction)

Builds on Phase 0+1. Same principles: **deterministic core, probabilistic edges; every model
behind an interface; graceful degradation; boots with zero deps.**

## Slices (shipped in order, each tested before the next)

### 1. Pantry / inventory + expiry tracking + reminders
- `services/pantry.py` — **pure, tested** expiry logic: `days_left`, `expiry_status`
  (`expired` / `expiring_soon` / `fresh` / `no_date`), and `reminders()` filtering + sorting.
  `today` is injectable so tests are deterministic.
- DB: `pantry_items` (user, product, qty, added_at, expiry_date, opened).
- `POST /pantry`, `GET /pantry` (with computed status), `DELETE /pantry/{id}`,
  `GET /pantry/reminders?within_days=3`. Auth required.
- Reminders are pull-based (endpoint); scheduled push/cron is a documented follow-up.

### 2. Recipe generator from cart contents (`/recipe`)
- `services/recipe.py` — **deterministic** ingredient assembly from cart (+ optional pantry /
  extra items) and prompt building; tested. The LLM turns ingredients + constraints
  (veg/non-veg, cuisine, servings) into a recipe; **echo fallback** yields a deterministic
  suggestion so it never dead-ends.
- `POST /recipe` (session cart or explicit ingredients) → { ingredients, recipe_text, provider }.

### 3. Voice assistant (`/voice`)
- STT behind an interface: **Whisper** (faster-whisper, lazy) → **null** (client sends text).
- TTS behind an interface: **browser** default (server returns text, client speaks via Web
  Speech API — no heavy dep) → optional **gTTS** server-side audio. XTTS stays deferred.
- `POST /voice` (audio) → { transcript, answer, audio? } — reuses the Phase 0 `/chat` LLM so
  voice is just STT + chat + TTS wired together.

## Interface additions (config-selectable)
| Kind | Default | Fallback | Env |
|---|---|---|---|
| STT | whisper | null (text input) | `STT_PROVIDER` |
| TTS | browser | (gtts optional) | `TTS_PROVIDER` |

## Testing gates (added this phase)
`test_pantry.py` (deterministic expiry/reminders), `test_recipe.py` (deterministic ingredient
assembly + prompt), pantry API tests (auth), `/voice` + `/recipe` API tests (importorskip /
null-provider paths).

## Status — all slices complete (56 backend tests passing)
- [x] Slice 1 — pantry + expiry + reminders  (`/pantry*`, `services/pantry.py`, `PantryItem`)
- [x] Slice 2 — recipe generator  (`/recipe`, `services/recipe.py`)
- [x] Slice 3 — voice assistant  (`/voice`, STT+TTS interfaces, reuses `/chat` LLM)

### Notes / honest status
- STT/TTS heavy deps live in `requirements-ml.txt` (faster-whisper, gTTS). Defaults degrade to
  client text input + browser Web Speech API, so `/voice` works with zero server deps.
- Reminders are pull-based (`/pantry/reminders`); scheduled push/cron notifications are a
  documented follow-up (would need Celery/APScheduler + a channel).
- Frontend: voice assistant + recipe-from-cart wired, and the **pantry UI** (add/list/delete
  with color-coded expiry status + reminder banner) is complete behind the auth flow.
