"""
FastAPI Server & Web Dashboard Backend
Real-Time Video Analytics & Antivirus-Safe Telemetry Sync
"""
import os
import time
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from edgevision.config import Config
from edgevision.vision.pipeline import VisionPipeline
from edgevision.vision.recorder import EvidenceRecorder
from edgevision.telemetry.alerts import AlertManager

class SourceUpdate(BaseModel):
    source: str
    device_index: int = 0

class TelegramUpdate(BaseModel):
    enabled: bool
    bot_token: str
    chat_id: str

config = Config.load()
evidence_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "evidence")
os.makedirs(evidence_dir, exist_ok=True)
recorder = EvidenceRecorder(save_dir=evidence_dir, enabled=config.get("evidence.enabled", True))
alert_mgr = AlertManager(config_alerts=config.get("alerts", {}), save_dir=evidence_dir)
vision = VisionPipeline(config.get("vision"), recorder=recorder, alert_mgr=alert_mgr)

def create_app(config_path: str = None) -> FastAPI:
    return app

app = FastAPI(
    title="VisionSentinel: Real-Time Edge AI Security System",
    description="Edge Computer Vision, Real Intrusion Analytics & Evidence Recording",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    vision.start()

@app.on_event("shutdown")
def shutdown():
    vision.stop()

@app.get("/api/health")
def health(response: Response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return {"status": "online", "mode": "real_camera", "timestamp": time.time()}

# Main telemetry route with clean standard name
@app.get("/api/telemetry_state")
def get_telemetry_state(response: Response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return vision.get_metrics()

# Alias for backwards compatibility
@app.get("/api/metrics")
def get_metrics(response: Response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return vision.get_metrics()

# Embedded delivery: alerts endpoint ALSO carries the latest stats!
@app.get("/api/alerts")
def get_alerts(response: Response, limit: int = 20):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return {
        "alerts": alert_mgr.get_history(limit),
        "telemetry": vision.get_metrics()
    }

@app.get("/api/evidence")
def get_evidence(response: Response, limit: int = 30):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return {"evidence": recorder.list_evidence(limit)}

@app.get("/api/evidence/{filename}")
def get_evidence_file(filename: str):
    filepath = os.path.join(evidence_dir, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Evidence file not found")

@app.post("/api/trigger_snapshot")
def trigger_snapshot():
    name = vision.trigger_manual_snapshot()
    return {"status": "captured", "filename": name}

@app.post("/api/config/arm")
def set_arm(armed: bool = True):
    vision.security_armed = armed
    return {"status": "updated", "security_armed": armed}

@app.post("/api/config/source")
def update_source(data: SourceUpdate):
    vision.set_source(data.source, data.device_index)
    return {"status": "updated", "source": data.source, "device_index": data.device_index}

@app.post("/api/config/enhancer")
def update_enhancer(enabled: bool = True, method: str = "clahe", gamma: float = 1.2):
    vision.enable_enhancement = enabled
    vision.enhancer.method = method
    vision.enhancer.set_gamma(gamma)
    return {"status": "updated", "enhancement": enabled, "method": method}

@app.post("/api/config/telegram")
def update_telegram(data: TelegramUpdate):
    alert_mgr.telegram_cfg["enabled"] = data.enabled
    alert_mgr.telegram_cfg["bot_token"] = data.bot_token
    alert_mgr.telegram_cfg["chat_id"] = data.chat_id
    return {"status": "updated", "telegram": alert_mgr.telegram_cfg}

def frame_generator():
    while True:
        frame_bytes = vision.get_latest_frame_jpeg()
        if frame_bytes is not None:
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
        time.sleep(0.033)

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def index(response: Response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h2>VisionSentinel Live Backend Running</h2>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
