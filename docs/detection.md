# Day 2 — Detection

## Goal

Person detection using YOLOv8n, person-only class, tuned confidence threshold.

## What was built

- `ai_pipeline/detector.py` — `PersonDetector` class wrapping YOLOv8n
  - Filters to COCO class 0 (person) only
  - Confidence/IOU thresholds pulled from `config.py` (not hardcoded)
- `ai_pipeline/sanity_check.py` — draws bounding boxes + confidence on frames for visual QA

## Model

- `yolov8n.pt` (Ultralytics, nano variant) — auto-downloaded on first run (~6MB)

## Testing notes

- Initially tested on **synthetic/simulated crowd data** (stylized capsule avatars) — YOLO failed to detect them (near-zero confidence), since it's trained on real-world COCO imagery, not synthetic renders.
- Switched to **real crowd footage** — detection worked correctly, no major false positives/negatives observed in sanity check.
- Decision: use real footage (UMN Crowd Dataset recommended) for detection/tracking/risk-scoring dev going forward. Synthetic sim kept only as an optional separate test path (bypassing YOLO, feeding known ground-truth positions directly).

## Status

✅ Step 6 (detection) — done
✅ Step 7 (visual sanity check) — done
