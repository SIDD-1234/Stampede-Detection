# Week 1 — AI Pipeline (Day 1–5)

## Overview

Core AI pipeline for StampedeShield: detection, tracking, motion estimation, and risk scoring, unified into a single reusable module.

## Modules built

- `video_source.py` — unified interface for file/webcam/stream input
- `config.py` — pydantic-settings shared config (thresholds, zone grid, FPS, weights)
- `detector.py` — YOLOv8n person-only detector
- `tracker.py` — YOLO + ByteTrack (person tracking with persistent IDs)
- `motion.py` — Farnebäck optical flow, per-person movement vectors
- `risk_scorer.py` — density / entropy / stagnation → EMA 0–100 risk score with NORMAL/RISING/IMMINENT phases
- `pipeline.py` — single entry point (`StampedePipeline`) combining all of the above; `process_frame()` returns structured data (tracks + risk) decoupled from display, ready for backend/WebSocket use in Week 2

## Day-by-day

### Day 1 — Setup

- Repo structure: `backend/`, `frontend/`, `ai_pipeline/`, `docs/`
- Python venv + deps (ultralytics, opencv-python, deep-sort-realtime → later removed, fastapi, uvicorn, websockets)
- Vite + React frontend scaffold with Tailwind v4 (`@tailwindcss/vite`, no config file needed)
- `VideoSource` class, shared `config.py`
- ESLint + Prettier (frontend), ruff (Python)
- `.gitignore` added (venv, node*modules, *.mp4, \_.pt, etc.)

### Day 2 — Detection

- YOLOv8n person-only detector + bounding box sanity check
- Synthetic/simulated crowd data (stylized avatars) failed detection — YOLO trained on real imagery
- Switched to real footage (UMN Crowd Dataset) — detection worked correctly

### Day 3 — Tracking

- Initial DeepSORT rebuild caused heavy CPU load/heating on Mac
- Root cause: `deep-sort-realtime` v1.3.2 hardcodes `torch.cuda.is_available()`, no MPS support — embedder silently ran on CPU despite `embedder_gpu=True`
- Switched to YOLO's built-in ByteTrack (motion/IOU-based, no appearance embedding) — MPS-accelerated, resolved perf/heat issue

### Day 4 — Motion & Risk Scoring

- Farnebäck optical flow for per-person movement vectors
- Risk scoring engine: density, movement entropy, stagnation ratio → weighted raw score → EMA smoothing → 0–100 score with NORMAL/RISING/IMMINENT phases
- Weights tuned from initial 40/30/30 (density/entropy/stagnation) to 50/20/30 based on sanity-check observation

### Day 5 — Pipeline Integration

- Unified all modules into `pipeline.py` (`StampedePipeline` class)
- `process_frame()` returns clean structured output (tracks, risk) — no `cv2` coupling, ready to be called per-frame from FastAPI in Week 2
- End-to-end run on full mock video across normal→panic arc

## Known limitations

- ByteTrack may reassign new IDs after heavy occlusion (no appearance re-ID)
- Risk score weights are first-pass, not rigorously tuned/validated
- Synthetic/simulated crowd data unsupported by YOLO — real footage only
- Frame resize width and density normalization (`max_cell / 10`) are placeholder values, need tuning per deployment resolution

## Status

✅ Week 1 (AI Pipeline) complete — ready for Week 2 (backend + real-time streaming)
