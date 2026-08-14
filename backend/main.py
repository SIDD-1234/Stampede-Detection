from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket, WebSocketDisconnect
import cv2
import asyncio

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent / "ai_pipeline"))

from pipeline import StampedePipeline

app = FastAPI(title="StampedeShield API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}



@app.websocket("/ws/stream")
async def stream(websocket: WebSocket):
    await websocket.accept()
    pipeline = StampedePipeline()
    source = "/Users/siddhanthmungekar/Documents/FINAL YEAR/Project/Crowd-Activity-All.mp4"  # placeholder, hardcode for now

    cap = cv2.VideoCapture(source)
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            output = pipeline.process_frame(frame)
            payload = {
                "num_people": len(output["tracks"]),
                "tracks": [{"id": t["track_id"], "bbox": t["bbox"]} for t in output["tracks"]],
                "risk": output["risk"],
            }
            await websocket.send_json(payload)
            await asyncio.sleep(1 / 15)  # ~15 FPS pacing
    except WebSocketDisconnect:
        pass
    finally:
        cap.release()