# Week 3 — Frontend

## Overview

React + Vite + Tailwind dashboard consuming the backend's `/videos`, `/upload`, and `/ws/stream`, rendering a live video feed with tracking overlays, a risk dashboard, and a Firebase Auth login gate.

## Modules built

- `frontend/src/api.js` — `listVideos()`, `uploadVideo()`, `connectStream()` helpers
- `frontend/src/App.jsx` — main dashboard: video canvas, controls, live stats, auth gating
- `frontend/src/Login.jsx` — email/password login + signup form
- `frontend/src/firebase.js` — Firebase app/auth init, config loaded from `.env` via `import.meta.env`
- `frontend/.env` — Firebase config values (gitignored)

## Day-by-day

### Day 1 — Basic data flow

- Built `api.js` and a minimal `App.jsx`: video upload input, video-select dropdown, Start button
- WebSocket connection via `connectStream()` showing live `People:` count and `Risk:` score/phase as plain text
- Confirmed full chain working: browser ← WebSocket ← FastAPI ← pipeline

### Day 2 — Canvas overlay + real video frame

- Added a `<canvas>` overlay drawing live bounding boxes and track IDs from WebSocket payload
- Color-coded risk phase badge (NORMAL green / RISING orange / IMMINENT red)
- Initially rendered boxes on a blank canvas ("radar view"); switched to drawing the actual JPEG-encoded video frame (base64, decoded via `Image` + `drawImage`) underneath the boxes once the backend started sending frames

### Day 3 — Tailwind styling pass

- Dark theme (`bg-neutral-950`) layout: video canvas on the left, sidebar on the right
- Sidebar: upload control, video-select dropdown, Start/Stop button, live stats panel (People, Density, Entropy, Stagnation)
- Pulsing red badge styling for IMMINENT phase (`animate-pulse`)

### Day 4 — Stream control polish

- Added Start/Stop button toggle (`isStreaming` state) with proper WebSocket close on Stop
- Added a "Stream ended" indicator (`isEnded` state) shown when the WebSocket closes on its own (video finishes)

### Day 5 — Firebase Auth login gate

- Installed `firebase` SDK; created Firebase project with Email/Password auth enabled (test-mode database, to be hardened before demo)
- `firebase.js` reads config from `.env` (`VITE_FIREBASE_*` vars), `.env` gitignored
- `Login.jsx` — combined login/signup form
- `App.jsx` gated behind `onAuthStateChanged`: shows blank screen while checking auth, `Login` if logged out, full dashboard (with Log out button) if logged in
- Confirmed working: signup → dashboard → refresh persists session → logout returns to login screen

### Day 6 — Alert wiring (frontend-adjacent, backend-driven)

- No frontend changes; alerts are fully backend-side (Twilio SMS + Gmail), but this closed out the last planned Week 3 feature (alerts carried over from the old build) alongside auth

## Known limitations / notes

- Firebase database currently in test mode — needs security rules tightened (e.g. `request.auth != null`) before the 30-day test-mode window expires or before the live demo
- No password reset / email verification flow — acceptable for a single-user demo login
- Canvas size is hardcoded to 640×480, matching the pipeline's `frame_resize_width` — not responsive to different video aspect ratios yet

## Status

✅ Week 3 (Frontend) complete
