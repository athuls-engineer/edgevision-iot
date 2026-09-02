# 🛡️ VisionSentinel: Edge AI Smart Surveillance & Intrusion Detection System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com)
[![OpenCV](https://img.shields.io/badge/OpenCV-5.0%2B-5C3EE8.svg)](https://opencv.org/)
[![Telegram](https://img.shields.io/badge/Alerts-Telegram%20Bot%20API-blue.svg)](https://core.telegram.org/bots)

An open-source, production-ready **Edge AI Surveillance & Home Security System** that transforms any physical webcam, IP camera, or ESP32-CAM into an intelligent security monitor. 

Runs real-time **Person Detection (HOG + Linear SVM)**, **Face Verification (Haar Cascades)**, and **Adaptive Background Subtraction (MOG2 with Shadow Removal)** with automatic timestamped evidence snapshot saving and instant **Telegram alert dispatching**.

---

## 🌟 Real-World Practical Features

- **Live Physical Camera Ingestion**: Plug-and-play with your laptop webcam, external USB camera, or any phone camera streaming via IP Webcam / RTSP.
- **True Edge AI Person & Face Detection**: Uses OpenCV's pre-trained HOG pedestrian SVM and Haar Cascade models to accurately identify humans and faces rather than simple pixel noise.
- **Automatic Evidence Recording**: Instantly saves high-resolution, watermarked `.jpg` snapshots and event logs into a secure local `evidence/` directory whenever a person is detected.
- **Instant Telegram Phone Alerts**: Dispatches intruder photos straight to your Telegram account within 500ms using the Telegram Bot API.
- **Low-Light CLAHE Enhancement**: Enhances visibility in dark rooms dynamically using Contrast Limited Adaptive Histogram Equalization.
- **Cyber-Security Web Portal**: Live MJPEG video stream with detection overlays, Armed/Disarmed alarm switch, real-time FPS/Lux HUD, and a built-in **Evidence Gallery** to browse and download captured snapshots.

---

## 📐 System Architecture

```
[ Physical Webcam / IP Camera / ESP32-CAM ]
                     │
                     ▼
       [ OpenCV Video Ingestion Loop ]
                     │
                     ▼
  [ Low-Light CLAHE Histogram Equalization ]
                     │
                     ▼
  [ Real AI Detector (HOG Person + Haar Face + MOG2) ]
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
[ MJPEG Live Stream ]    [ Security Trigger Engine ]
(Web UI /video_feed)              │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
             [ Save Evidence ] [ Audible ] [ Telegram Bot ]
             (evidence/*.jpg)  (Siren/Beep) (Photo Alert)
```

---

## 📖 Documentation

For an in-depth setup, hardware requirements, REST API reference, and Docker deployment guide, see **[SETUP.md](SETUP.md)**.

---

## 🚀 Quickstart Guide

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/athuls-engineer/edgevision-iot.git
cd edgevision-iot

# Activate your virtual environment
venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Run with Your Physical Webcam

```bash
python -m edgevision.server.app
```

Open **`http://localhost:8000`** in your browser.

1. **Step in front of your webcam**: The system will identify you as a `Person` or `Face Verified`.
2. **Watch the Evidence Gallery**: Scroll down to see high-res timestamped evidence snapshots automatically captured and saved in the `evidence/` folder.
3. **Test CLAHE**: Dim your room lights and toggle the *CLAHE Low-Light Enhancement* switch to see real-time contrast correction.
4. **Connect your Phone as a Camera (Optional)**: Install "IP Webcam" on Android/iOS, click *Camera Source* on the dashboard, and paste the URL (e.g. `http://192.168.1.50:8080/video`).

---

## 📱 Setting Up Free Telegram Phone Alerts (1 Minute Setup)

1. Open Telegram and message **`@BotFather`** -> send `/newbot` and copy your **HTTP API Token**.
2. Message **`@userinfobot`** on Telegram to get your numeric **Chat ID**.
3. In the VisionSentinel web dashboard, click **Configure Telegram Bot**, paste your Token & Chat ID, and click Save.
4. Step in front of the camera — you will receive an instant photo alert on your phone!

---

## 📁 Repository Structure

```
edgevision-iot/
├── edgevision/
│   ├── config.py              # System configuration & threshold defaults
│   ├── vision/
│   │   ├── detector.py        # Real HOG Person & Haar Face detector
│   │   ├── enhancer.py        # CLAHE & Gamma contrast enhancement
│   │   ├── recorder.py        # Automatic evidence snapshot manager
│   │   └── pipeline.py        # Real camera loop & telemetry HUD
│   ├── telemetry/
│   │   └── alerts.py          # Telegram dispatcher & audio alarm
│   └── server/
│       └── app.py             # FastAPI server, MJPEG stream & Evidence API
├── static/
│   ├── index.html             # Security dashboard & Evidence Gallery UI
│   ├── style.css              # Cyber-security dark theme
│   └── app.js                 # WebSocket client & modal controllers
├── evidence/                  # Auto-generated intrusion snapshots directory
├── requirements.txt
└── README.md
```

---

## 👨‍💻 Author

**Athul S**  
* Electronics and Communication Engineering Undergraduate  
* GitHub: [@athuls-engineer](https://github.com/athuls-engineer)  
* LinkedIn: [linkedin.com/in/athul-s-engineer](https://www.linkedin.com/in/athul-s-engineer)
