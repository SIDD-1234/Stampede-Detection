from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import cv2
import asyncio
import shutil
from pathlib import Path
import time
import base64

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
    config_msg = await websocket.receive_json()
    source_type = config_msg.get("source_type", "file")
    source = 0 if source_type == "webcam" else str(UPLOAD_DIR / config_msg["filename"])

    pipeline = StampedePipeline()
    cap = cv2.VideoCapture(source)
    was_imminent = False

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            output = pipeline.process_frame(frame)

            if output["risk"]:
                is_imminent = output["risk"]["phase"] == "IMMINENT"
                if is_imminent and not was_imminent:
                    print(f"[ALERT] IMMINENT risk detected at {time.strftime('%X')}")
                was_imminent = is_imminent

            # encode the (already resized) frame as JPEG -> base64
            _, buffer = cv2.imencode(".jpg", output["frame"], [cv2.IMWRITE_JPEG_QUALITY, 60])
            frame_b64 = base64.b64encode(buffer).decode("utf-8")

            payload = {
                "frame": frame_b64,
                "num_people": len(output["tracks"]),
                "tracks": [{"id": t["track_id"], "bbox": t["bbox"]} for t in output["tracks"]],
                "risk": output["risk"],
            }
            await websocket.send_json(payload)
            await asyncio.sleep(1 / 15)
    except WebSocketDisconnect:
        pass
    finally:
        cap.release()



UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    dest = UPLOAD_DIR / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"filename": file.filename, "path": str(dest)}


@app.get("/videos")
def list_videos():
    files = [f.name for f in UPLOAD_DIR.iterdir() if f.suffix.lower() in (".mp4", ".mov", ".avi")]
    return {"videos": files}