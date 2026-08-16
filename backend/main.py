from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import cv2
import asyncio
import shutil
from pathlib import Path
import sys
import time
import base64
from alerts import send_sms_alert, send_email_alert
sys.path.append(str(Path(__file__).resolve().parent.parent / "ai_pipeline"))
from pipeline import StampedePipeline
from config import settings
from pydantic import BaseModel
from alert_config import alert_settings
import json
from fastapi.responses import Response
from report_pdf import generate_report_pdf

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

REPORTS_FILE = Path(__file__).resolve().parent / "reports.json"

def load_reports():
    if REPORTS_FILE.exists():
        with open(REPORTS_FILE, "r") as f:
            return json.load(f)
    return []

def save_report(report):
    reports = load_reports()
    reports.append(report)
    with open(REPORTS_FILE, "w") as f:
        json.dump(reports, f, indent=2)


@app.websocket("/ws/stream")
async def stream(websocket: WebSocket):
    await websocket.accept()
    config_msg = await websocket.receive_json()
    source_type = config_msg.get("source_type", "file")
    source = 0 if source_type == "webcam" else str(UPLOAD_DIR / config_msg["filename"])

    pipeline = StampedePipeline()
    cap = cv2.VideoCapture(source)
    was_imminent = False
    last_alert_time = 0
    alert_count = 0
    MAX_ALERTS_PER_SESSION = 3
    session_start = time.time()

    session_stats = {
        "source": config_msg.get("filename", "webcam"),
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "max_people": 0,
        "max_risk_score": 0,
        "phase_durations": {"NORMAL": 0, "RISING": 0, "IMMINENT": 0},
        "alert_events": [],
        "frame_count": 0,
    }
    last_frame_time = time.time()

    def make_log(event_type, message):
        return {"type": "log", "event": event_type, "message": message, "timestamp": time.strftime("%X")}

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                await websocket.send_json(make_log("info", "Stream ended (video finished)"))
                break
            output = pipeline.process_frame(frame)

            now = time.time()
            dt = now - last_frame_time
            last_frame_time = now
            session_stats["frame_count"] += 1
            session_stats["max_people"] = max(session_stats["max_people"], len(output["tracks"]))

            if output["risk"]:
                phase = output["risk"]["phase"]
                session_stats["phase_durations"][phase] = session_stats["phase_durations"].get(phase, 0) + dt
                session_stats["max_risk_score"] = max(session_stats["max_risk_score"], output["risk"]["score"])

                is_imminent = phase == "IMMINENT"
                if phase != getattr(stream, "_last_phase", None):
                    await websocket.send_json(make_log("phase_change", f'Risk phase: {phase} (score {output["risk"]["score"]})'))
                    stream._last_phase = phase

                if is_imminent and not was_imminent and (now - last_alert_time) > settings.alert_cooldown_seconds:
                    if alert_count < MAX_ALERTS_PER_SESSION:
                        alert_msg = f"StampedeShield ALERT: IMMINENT risk detected at {time.strftime('%X')} — {len(output['tracks'])} people in frame."
                        await websocket.send_json(make_log("alert", alert_msg))
                        session_stats["alert_events"].append({"time": time.strftime("%X"), "message": alert_msg})
                        try:
                            send_sms_alert(alert_msg)
                            send_email_alert("StampedeShield Alert", alert_msg)
                        except Exception as e:
                            await websocket.send_json(make_log("error", f"Alert send failed: {e}"))
                        alert_count += 1
                        last_alert_time = now
                    else:
                        await websocket.send_json(make_log("info", "Max alerts reached for this session"))
                was_imminent = is_imminent

            _, buffer = cv2.imencode(".jpg", output["frame"], [cv2.IMWRITE_JPEG_QUALITY, 60])
            frame_b64 = base64.b64encode(buffer).decode("utf-8")

            payload = {
                "type": "frame",
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
        session_stats["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        session_stats["duration_seconds"] = round(time.time() - session_start, 1)
        save_report(session_stats)



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

class AlertToggle(BaseModel):
    email_enabled: bool = None
    sms_enabled: bool = None

@app.post("/settings/alerts")
def update_alert_settings(toggle: AlertToggle):
    if toggle.email_enabled is not None:
        alert_settings.email_enabled = toggle.email_enabled
    if toggle.sms_enabled is not None:
        alert_settings.sms_enabled = toggle.sms_enabled
    return {"email_enabled": alert_settings.email_enabled, "sms_enabled": alert_settings.sms_enabled}

@app.get("/settings/alerts")
def get_alert_settings():
    return {"email_enabled": alert_settings.email_enabled, "sms_enabled": alert_settings.sms_enabled}

@app.get("/reports")
def get_reports():
    return {"reports": load_reports()[-10:]}

@app.get("/reports/{index}/pdf")
def download_report_pdf(index: int):
    reports = load_reports()
    if index < 0 or index >= len(reports):
        return Response(content="Report not found", status_code=404)
    pdf_bytes = generate_report_pdf(reports[index])
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=stampedeshield_report_{index}.pdf"}
    )