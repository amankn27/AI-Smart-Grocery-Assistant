# API Reference (Phase 0 + Phase 1)

Base URL: `http://localhost:8000`. Interactive docs at `/docs` (Swagger) when running.

### Phase 0
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness + config echo |
| POST | `/detect` | Image → product boxes + confidence + `needs_confirmation` |
| POST | `/ocr` | Image → OCR text + structured nutrition (per-field confidence) |
| POST | `/analyze` | Nutrition object → health score, grade, warnings |
| POST | `/chat` | Question (+context) → grounded answer |
| GET | `/cart` | Current cart + subtotal / GST / total |
| POST | `/cart/add` | Add/increment an item |
| POST | `/cart/update` | Set quantity (0 removes) |
| POST | `/cart/remove` | Remove an item |
| GET | `/products` | Catalog lookup by `q` (fuzzy) or `barcode` |

### Phase 1
| Method | Path | Purpose | Auth |
|---|---|---|---|
| POST | `/barcode` | Image → decoded EAN/UPC/QR → catalog product | — |
| POST | `/barcode/lookup` | Manual barcode entry → product | — |
| POST | `/recommend` | Product → healthier alternatives + RAG explanation | — |
| POST | `/auth/register` | Create account → access+refresh tokens | — |
| POST | `/auth/login` | OAuth2 password login → tokens | — |
| POST | `/auth/refresh` | Refresh token → new access token | — |
| GET | `/auth/me` | Current user | Bearer |
| POST | `/history/scan` | Record a scan | Bearer |
| GET | `/history` | List past scans | Bearer |
| POST | `/products/save` | Save a product | Bearer |
| GET | `/products/saved` | List saved products | Bearer |
| GET | `/dashboard` | Spend / calories / category mix / avg health | Bearer |
| GET | `/report` | Cart → PDF invoice (GST breakup) | — |

### Phase 2
| Method | Path | Purpose | Auth |
|---|---|---|---|
| POST | `/recipe` | Cart (or explicit ingredients) → recipe | — |
| POST | `/voice` | Audio (or text) → transcript + answer (+optional audio) | — |
| POST | `/pantry` | Add pantry item | Bearer |
| GET | `/pantry` | List items with expiry status | Bearer |
| GET | `/pantry/reminders` | Items expired / expiring within N days | Bearer |
| DELETE | `/pantry/{id}` | Remove a pantry item | Bearer |

## Examples

### POST /analyze
```json
// request
{ "sugar_g": 45, "sodium_mg": 800, "saturated_fat_g": 14, "protein_g": 4, "fiber_g": 1 }
// response
{ "score": 24, "grade": "E",
  "warnings": [ {"field":"sugar_g","severity":"red","message":"High sugar g: 45 per 100g"} ],
  "positives": [] }
```

### POST /cart/add?session_id=demo
```json
// request
{ "product_id": "c1", "name": "Cola 250ml", "mrp": 40, "quantity": 1, "category": "soft_drink" }
// response (GST is back-computed from the inclusive MRP)
{ "session_id":"demo", "item_count":1, "subtotal":"40.00",
  "total_gst":"8.75", "total":"40.00", "items":[ ... ] }
```

### POST /detect  (multipart form: `image`)
```json
{ "model":"stub", "width":1280, "height":720,
  "detections":[ {"label":"unknown_product","confidence":0.0,
                  "bbox_xyxy":[256,144,1024,576],"needs_confirmation":true} ] }
```

### POST /chat
```json
// request
{ "question":"Is this healthy?", "context": { "grade":"E", "sugar_g":45 } }
// response (offline fallback when no GEMINI_API_KEY)
{ "answer":"[offline assistant] ...", "provider":"echo" }
```

### POST /ocr  (multipart form: `image`)
```json
{ "engine":"null", "text":"", "mean_confidence":0.0,
  "nutrition": { "basis":"unknown", "fields":{}, "low_confidence_fields":[] } }
```
> With the vision stack installed and a real label image, `engine` becomes `paddle`/`easyocr`
> and `nutrition.fields` is populated.

### POST /recommend
```json
// request
{ "product_id": "8901063139329", "limit": 3 }
// response — alternatives are DETERMINISTIC (same category, higher health score);
// the explanation is LLM-phrased from retrieved guidance (offline echo when no key)
{ "target": { "name": "bourbon", "category": "biscuits" },
  "alternatives": [ { "name": "Parle G biscuit", "health_score": 48, "score_delta": 22 } ],
  "explanation": "…", "explanation_provider": "echo",
  "sources": [ { "id": "who-sugar", "score": 0.41 } ] }
```

### Auth flow
```bash
curl -X POST localhost:8000/auth/register -H 'content-type: application/json' \
  -d '{"email":"a@b.com","password":"secret123"}'          # → {access_token, refresh_token}
curl localhost:8000/auth/me -H "Authorization: Bearer $ACCESS"
curl "localhost:8000/report?session_id=demo" -o invoice.pdf  # PDF invoice
```

### POST /voice  (multipart form: `audio` OR `text`)
```json
// with typed text (or when Whisper isn't installed, client sends text):
{ "transcript": "Is this healthy?", "answer": "…", "stt_engine": "client",
  "llm_provider": "echo", "tts_engine": "browser", "audio_base64": null, "audio_mime": "text/plain" }
// audio_base64 = null → client speaks the answer via the Web Speech API.
```

### POST /recipe
```json
// request (omit `ingredients` to use the current cart)
{ "ingredients": ["paneer", "peas"], "diet": "veg", "servings": 2 }
// response
{ "ingredients": ["paneer","peas"], "recipe_text": "…", "provider": "echo" }
```
