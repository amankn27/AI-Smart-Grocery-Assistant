# Models directory

Weights are **git-ignored** (see `.gitignore`) — do not commit large binaries. This file
documents what goes here and how to get it.

| File | Source | Notes |
|---|---|---|
| `yolov8n.pt` | Ultralytics (auto-downloads on first `YOLO("yolov8n.pt")`) | Pretrained COCO checkpoint used by the Phase 0 detector |
| `grocery_yolo.pt` | *(Phase 1)* fine-tuned on labeled grocery images | Only when eval shows stock weights are inadequate (brief §4 model note) |

Deferred by default (introduce only on a measured need): SAM2, CLIP, XTTS.
