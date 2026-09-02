# VisionSentinel: Setup & Developer Guide

This document provides step-by-step instructions to configure, run, test, and deploy **VisionSentinel** across local development environments, Docker containers, and edge hardware platforms (e.g., Raspberry Pi 4 / NVIDIA Jetson).

---

## 1. System Architecture Overview

VisionSentinel is a modular Edge AI computer vision and surveillance gateway designed for low-latency detection, local evidence archiving, and real-time dashboard telemetry.

```
┌─────────────────┐     ┌───────────────────────┐     ┌────────────────────────┐
│  Video Source   │ ──▶ │ ImageEnhancer (CLAHE) │ ──▶ │ RealWorldDetector      │
│ (Webcam / RTSP) │     │ Low-light adaptation  │     │ Motion/Presence filter │
└─────────────────┘     └───────────────────────┘     └────────────────────────┘
                                                                   │
                                ┌──────────────────────────────────┴──────────────────────────────────┐
                                ▼                                     ▼                               ▼
                     ┌──────────────────────┐              ┌──────────────────────┐        ┌──────────────────────┐
                     │ Stream Generator     │              │ Telemetry Dispatcher │        │ Evidence Recorder    │
                     │ MJPEG multipart/feed │              │ State polling & REST │        │ Local JPEG + Telegram│
                     └──────────────────────┘              └──────────────────────┘        └──────────────────────┘
```

### Core Components:
- **`edgevision.vision.pipeline.VisionPipeline`**: Coordinates camera ingestion thread, frame preprocessing, detection inference, moving-average FPS calculation, and thread-safe buffer sharing.
- **`edgevision.vision.enhancer.ImageEnhancer`**: Applies Contrast Limited Adaptive Histogram Equalization (CLAHE) on the Luminance channel (LAB/YUV color spaces) and gamma correction to improve visibility in dim environments without over-saturating highlights.
- **`edgevision.vision.detector.RealWorldDetector`**: Computes foreground motion masks via Background Subtraction (MOG2), contour morphological filtering, aspect ratio heuristics, and Exponential Moving Average (EMA) bounding box smoothing.
- **`edgevision.vision.recorder.EvidenceRecorder`**: Automates timestamped, watermarked JPEG snapshots into `evidence/` when persistent dwell thresholds are exceeded.
- **`edgevision.telemetry.alerts.AlertManager`**: Manages event history buffers, local audible sirens, and Telegram Bot photo push notifications.
- **`edgevision.server.app`**: FastAPI backend exposing MJPEG video streaming, REST endpoints (`/api/telemetry_state`, `/api/alerts`, `/api/evidence`), and self-contained cyber-security dashboard.

---

## 2. Prerequisites & Requirements

### Hardware:
- **Host**: Standard PC (Windows 10/11, macOS, Linux) or Edge SBC (Raspberry Pi 4B 4GB+, NVIDIA Jetson Nano / Orin).
- **Camera**: USB Webcam (UVC compliant), integrated laptop camera, or IP / RTSP camera (e.g., DroidCam, IP Webcam app).

### Software:
- **Python**: Version `3.10` or higher (`3.11`, `3.12`, `3.14` supported).
- **Git**: For version control.
- **Docker** *(Optional)*: For containerized deployment.

---

## 3. Local Installation & Setup

### Step 1: Clone the Repository
```bash
git clone https://github.com/athuls-engineer/edgevision-iot.git
cd edgevision-iot
```

### Step 2: Create a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Running the Application

### Start the Server:
```bash
python -m edgevision.server.app
```

Once running, the application initializes the video ingestion thread and starts the web server at:
- **Dashboard URL**: `http://localhost:8000`
- **Swagger API Docs**: `http://localhost:8000/docs`

### Open in Browser:
Navigate to `http://localhost:8000` in Google Chrome, Microsoft Edge, or Mozilla Firefox.

---

## 5. Configuration Guide

Default parameters are loaded from `config.example.yaml` or overridden programmatically.

```yaml
vision:
  source: "webcam"            # "webcam" or RTSP/HTTP URL
  device_index: 0             # Camera device index (0 = default)
  frame_width: 640
  frame_height: 480
  target_fps: 30
  enable_enhancement: true    # Enable/disable low-light CLAHE
  enhancement_method: "clahe" # "clahe" | "equalize" | "gamma"
  clahe_clip_limit: 2.5
  clahe_grid_size: [8, 8]
  gamma_value: 1.2
  min_contour_area: 1000      # Minimum area in pixels to trigger detection
  security_armed: true

alerts:
  audio_beep: false
  telegram:
    enabled: false
    bot_token: ""             # Token from @BotFather
    chat_id: ""               # Target chat ID from @userinfobot

evidence:
  enabled: true
  save_dir: "evidence"
  max_stored_snapshots: 100
```

---

## 6. Testing Camera Sources

### 1. Default Physical Webcam:
The system automatically connects to device index `0`. If you have multiple webcams:
1. Click **"📹 Camera Source"** on the dashboard top bar.
2. Enter Device Index (e.g., `0`, `1`, `2`).
3. Click **Apply & Reconnect**.

### 2. Smartphone Camera / IP Stream (RTSP / HTTP):
To use an Android or iPhone as a wireless security camera:
1. Install an IP camera app (e.g., *IP Webcam* or *DroidCam*).
2. Start the stream on your phone (e.g., `http://192.168.1.15:8080/video`).
3. In the VisionSentinel dashboard, open **"📹 Camera Source"**.
4. Select **"Phone Camera / IP RTSP URL"**, paste the URL, and click **Apply & Reconnect**.

---

## 7. Telegram Alert Setup (Optional)

To receive real-time intrusion photos directly on your mobile device:
1. Open Telegram and search for `@BotFather`.
2. Send `/newbot`, follow prompts, and copy the generated **Bot Token**.
3. Search for `@userinfobot` on Telegram to get your numeric **Chat ID**.
4. In the VisionSentinel web dashboard, click **"Configure Telegram Bot"**.
5. Paste your Bot Token, Chat ID, and click **Save Telegram Settings**.

---

## 8. Docker Deployment

### Build the Docker Image:
```bash
docker build -t vision-sentinel:latest .
```

### Run with Docker Compose:
```bash
docker-compose up -d
```

*(Note: On Linux hosts with physical USB cameras, ensure `--device=/dev/video0:/dev/video0` is mapped in `docker-compose.yml`.)*

---

## 9. API Reference Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the web surveillance dashboard |
| `GET` | `/video_feed` | Multipart MJPEG real-time video stream |
| `GET` | `/api/telemetry_state` | Returns live telemetry (FPS, Lux, Dwell Time, Targets) |
| `GET` | `/api/alerts` | Returns recent security alert logs & embedded telemetry |
| `GET` | `/api/evidence` | Lists captured timestamped forensic snapshots |
| `GET` | `/api/evidence/{filename}` | Downloads a specific snapshot JPEG |
| `POST` | `/api/trigger_snapshot` | Manually captures and archives an annotated snapshot |
| `POST` | `/api/config/arm` | Arms or disarms the intrusion security monitor |
| `POST` | `/api/config/source` | Hot-switches the video source (webcam index or IP URL) |
| `POST` | `/api/config/enhancer` | Toggles CLAHE / contrast enhancement settings |
| `POST` | `/api/config/telegram` | Configures and enables Telegram Bot API dispatch |

---

## 10. Running Automated Tests

VisionSentinel includes a full `unittest` test suite covering computer vision algorithms, low-light enhancement mathematical limits, and telemetry dispatchers.

```bash
# Run all unit tests
python -m unittest discover tests

# Run specific test modules
python -m unittest tests.test_vision
python -m unittest tests.test_telemetry
```

---

## 11. Edge Deployment Considerations

When running on resource-constrained platforms such as the **Raspberry Pi 4**:
- Keep resolution at `640x480` for consistent 30 FPS throughput.
- CLAHE execution on OpenCV CPU uses optimized SIMD instructions (NEON on ARM), averaging `< 2.5ms` per frame.
- MOG2 background subtraction runs with `history=200, varThreshold=36`, consuming `< 12%` CPU on quad-core ARM Cortex-A72.
