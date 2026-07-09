# Evaluation set (accuracy/latency gates — brief §8, §10)

This folder holds the held-out set used to measure the vision edges against explicit targets.
Phase 0 ships the harness + targets; populate `images/` and `labels.csv` with real product
photos (include **rotated** and **low-light** shots) to produce real numbers.

## Targets (gates, not aspirations)

| Metric | Target | Measured |
|---|---|---|
| Detection mAP@0.5 (12 classes) | ≥ 0.60 | _TBD — needs labeled images_ |
| OCR nutrition-field accuracy | ≥ 0.80 of fields correct | _TBD_ |
| Server round trip (detect+ocr) | < 2.0 s / frame | _TBD_ |

## Layout
```
data/eval/
  images/        # *.jpg product photos
  labels.csv     # image, true_category, true_energy_kcal, true_protein_g, ...
  run_eval.py    # (Phase 1) loads images, calls providers, prints the table above
```

## Note on Phase 0 detection
Stock YOLO weights don't know the 12 grocery categories, so detection mAP against those
labels will be low until a fine-tune (Phase 1). This is expected and documented rather than
hidden — the eval harness exists so that decision is data-driven.
