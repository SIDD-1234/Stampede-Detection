# Week 2 — Backend & Real-Time Streaming

## Overview

FastAPI backend wrapping the AI pipeline, streaming live tracking + risk data (and video frames) to the frontend over WebSocket, plus alerting on high-risk events.

## Modules built

- `backend/main.py` — FastAPI app: CORS, health check, video upload/listing, and the core `/ws/stream` WebSocket endpoint
- `backend/alerts.py` — Twilio SMS + Gmail email alert senders, with `.env`-based on/off toggles
- `backend/uploads/` — stored uploaded videos (gitignored)
- `backend/.env` — secrets (Twilio SID/token/numbers, Gmail address/app password, alert toggles) — gitignored

## Day-by-day

### Day 1 — FastAPI skeleton + WebSocket streaming

- `/health` GET endpoint
- Imported `StampedePipeline` from `ai_pipeline/` via a `sys.path` hook
- `/ws/stream` WebSocket endpoint: reads frames from a hardcoded video, runs them through the pipeline, sends per-frame JSON (`num_people`, `tracks`, `risk`) at ~15 FPS
- Confirmed working via a Python `websocket-client` test script

### Day 2 — Configurable video source

- `/upload` POST endpoint — saves uploaded video files to `backend/uploads/`
- `/ws/stream` now expects a handshake JSON from the client (`{"source_type": "webcam"|"file", "filename": ...}`) instead of a hardcoded path
- Each WebSocket connection creates its own `StampedePipeline` + `cv2.VideoCapture` instance — no shared state across concurrent clients

### Day 3 — Video listing + alert logging

- `/videos` GET endpoint — lists uploaded video files for the frontend to select from
- Added IMMINENT-transition detection in `/ws/stream` — logs a timestamped alert only when risk phase transitions into IMMINENT (not every frame it stays high)

### Day 4 (carried into Week 3 chronologically, but backend-side) — Alerts

- `alerts.py`: `send_sms_alert()` (Twilio) and `send_email_alert()` (Gmail via `smtplib` + app password)
- Wired into the IMMINENT-transition point in `/ws/stream`, wrapped in try/except so a failed send doesn't crash the stream
- Cooldown logic using `settings.alert_cooldown_seconds` to avoid alert spam if risk flickers near the threshold
- `.env` toggles (`ALERTS_ENABLED`, `SMS_ENABLED`, `EMAIL_ENABLED`) to disable alerts entirely or per-channel, saving Twilio/Gmail usage during development
- Also added JPEG-encoding of the processed frame to base64, sent alongside track/risk data, so the frontend can render the actual video (not just an overlay)

## Known limitations / notes

- Twilio trial account balance depletion caused suspension once before — resolved by creating a fresh trial account or topping up funds; credentials are fully `.env`-driven so switching accounts needs no code changes
- Alert cooldown and phase thresholds are first-pass values, not rigorously tuned
- No authentication/authorization on backend endpoints themselves yet (auth is frontend-gated via Firebase) — fine for local dev, would need hardening for real deployment

## Status

✅ Week 2 (Backend + Real-Time Streaming) complete
