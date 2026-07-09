"""Evaluation harness — produces REAL measured numbers against the brief's §8 targets.

Two measurements that don't need model weights (so they run in CI / any machine):

1. **OCR nutrition-field extraction accuracy** — runs the deterministic ``parse_nutrition``
   over a labeled set of real-world label texts (``nutrition_labels.jsonl``: clean, misspelled,
   comma-decimals, kJ, salt→sodium, Hindi/Devanagari) and reports the fraction of ground-truth
   fields recovered within tolerance. Target: >= 0.80.
2. **Server round-trip latency** — micro-benchmarks the deterministic endpoints via the
   in-process TestClient and reports p50/p95. Budget: < 2000 ms/request.

Detection mAP needs labeled product images + YOLO weights; that path is wired but reported as
N/A here (documented, not faked). Run:  ``python data/eval/run_eval.py``
"""

from __future__ import annotations

import json
import logging
import statistics
import sys
import time
from pathlib import Path

# Keep the benchmark output readable — silence per-request INFO logs.
logging.disable(logging.INFO)

# Make the backend importable whether run from repo root or elsewhere.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.nutrition import parse_nutrition  # noqa: E402

FIELD_TOL = {  # absolute tolerance per field for "correct"
    "energy_kcal": 2.0, "protein_g": 0.2, "fat_g": 0.2, "saturated_fat_g": 0.2,
    "carbohydrate_g": 0.2, "sugar_g": 0.2, "fiber_g": 0.2, "sodium_mg": 5.0,
}


def eval_ocr_accuracy() -> dict:
    path = Path(__file__).parent / "nutrition_labels.jsonl"
    samples = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    total_fields = 0
    correct = 0
    per_sample = []
    for s in samples:
        facts = parse_nutrition(s["text"])
        truth = s["truth"]
        hits = 0
        for field, expected in truth.items():
            total_fields += 1
            got = facts.get(field)
            if got is not None and abs(got - expected) <= FIELD_TOL.get(field, 0.5):
                hits += 1
                correct += 1
        per_sample.append((s["id"], hits, len(truth)))

    accuracy = correct / total_fields if total_fields else 0.0
    return {"accuracy": accuracy, "correct": correct, "total": total_fields, "per_sample": per_sample}


def eval_latency(iterations: int = 50) -> list[dict]:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)

    # (label, callable). Only deterministic / fallback paths — no heavy models required.
    cases = [
        ("POST /analyze", lambda: client.post("/analyze", json={"sugar_g": 45, "sodium_mg": 800})),
        ("GET  /products", lambda: client.get("/products", params={"q": "biscuit"})),
        ("POST /value", lambda: client.post("/value", json={"product_id": _a_product_id(client)})),
        ("POST /recommend", lambda: client.post("/recommend", json={"product_id": _a_product_id(client)})),
        ("POST /diet/plan", lambda: client.post("/diet/plan", json={"target_kcal": 1200, "min_protein_g": 40})),
    ]
    results = []
    for label, call in cases:
        timings = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            call()
            timings.append((time.perf_counter() - t0) * 1000.0)
        timings.sort()
        results.append({
            "endpoint": label,
            "p50_ms": round(statistics.median(timings), 1),
            "p95_ms": round(timings[int(len(timings) * 0.95) - 1], 1),
            "max_ms": round(max(timings), 1),
        })
    return results


_cached_pid = None


def _a_product_id(client) -> str:
    global _cached_pid
    if _cached_pid is None:
        _cached_pid = client.get("/products", params={"limit": 1}).json()["results"][0]["product_id"]
    return _cached_pid


def main() -> int:
    print("=" * 64)
    print("OCR nutrition-field extraction accuracy (target >= 0.80)")
    print("=" * 64)
    ocr = eval_ocr_accuracy()
    for sid, hits, total in ocr["per_sample"]:
        print(f"  {sid:22s} {hits}/{total}")
    print(f"\n  OVERALL: {ocr['correct']}/{ocr['total']} = {ocr['accuracy']:.3f} "
          f"{'PASS' if ocr['accuracy'] >= 0.80 else 'FAIL'}")

    print("\n" + "=" * 64)
    print("Server latency (budget < 2000 ms/request)")
    print("=" * 64)
    lat = eval_latency()
    for r in lat:
        ok = "PASS" if r["p95_ms"] < 2000 else "FAIL"
        print(f"  {r['endpoint']:18s} p50={r['p50_ms']:7.1f}ms  p95={r['p95_ms']:7.1f}ms  {ok}")

    print("\n" + "=" * 64)
    print("Detection mAP@0.5 (target >= 0.60): N/A — needs labeled product images + YOLO")
    print("weights. Harness path is wired; add data/eval/images/ + labels to populate.")
    print("=" * 64)

    return 0 if ocr["accuracy"] >= 0.80 else 1


if __name__ == "__main__":
    raise SystemExit(main())
