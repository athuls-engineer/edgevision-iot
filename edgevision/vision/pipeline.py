"""
VisionSentinel Camera Pipeline
High-performance camera reader with auto-reconnect, CLAHE, Human Detection & Real-Time Telemetry.
"""
import cv2
import time
import threading
import numpy as np
from typing import Optional, Dict, Any
from edgevision.vision.enhancer import ImageEnhancer
from edgevision.vision.detector import RealWorldDetector
from edgevision.vision.recorder import EvidenceRecorder
from edgevision.telemetry.alerts import AlertManager

class VisionPipeline:
    def __init__(self, config_vision: dict = None, recorder: EvidenceRecorder = None, alert_mgr: AlertManager = None):
        self.config = config_vision or {}
        self.source = self.config.get("source", "webcam")
        self.device_index = self.config.get("device_index", 0)
        self.width = self.config.get("frame_width", 640)
        self.height = self.config.get("frame_height", 480)
        self.security_armed = self.config.get("security_armed", True)

        self.enhancer = ImageEnhancer(
            method=self.config.get("enhancement_method", "clahe"),
            clip_limit=self.config.get("clahe_clip_limit", 2.5),
            grid_size=self.config.get("clahe_grid_size", (8, 8)),
            gamma=self.config.get("gamma_value", 1.2)
        )
        self.enable_enhancement = self.config.get("enable_enhancement", True)

        self.detector = RealWorldDetector(
            detection_mode=self.config.get("detection_mode", "hybrid"),
            min_area=self.config.get("min_contour_area", 1000)
        )

        self.recorder = recorder or EvidenceRecorder()
        self.alert_mgr = alert_mgr or AlertManager()

        self._cap = None
        self._is_running = False
        self._lock = threading.Lock()
        self._latest_jpeg = None
        self._total_intrusions = 0
        self._current_fps = 0.0
        self._last_frame_time = time.time()
        self._fps_history = []
        self._latest_metrics = {
            "fps": 0.0,
            "target_detected": False,
            "target_count": 0,
            "avg_luminance": 0.0,
            "source_type": self.source,
            "total_intrusions": 0,
            "armed": self.security_armed,
            "presence_sec": 0,
            "latency_ms": 15.0,
            "clahe_enabled": self.enable_enhancement,
            "timestamp": time.time()
        }

    def start(self):
        if self._is_running:
            return
        self._is_running = True
        self._open_camera()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def set_source(self, new_source: str, device_index: int = 0):
        with self._lock:
            self.source = new_source
            self.device_index = device_index
            if self._cap:
                try: self._cap.release()
                except Exception: pass
            self._open_camera()

    def _open_camera(self):
        if self.source == "webcam":
            # Standard direct capture
            self._cap = cv2.VideoCapture(self.device_index)
            if self._cap.isOpened():
                self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        elif self.source.startswith("http") or self.source.startswith("rtsp"):
            self._cap = cv2.VideoCapture(self.source)
        else:
            self._cap = None

    def stop(self):
        self._is_running = False
        if self._cap:
            try: self._cap.release()
            except Exception: pass

    def trigger_manual_snapshot(self) -> str:
        with self._lock:
            frame = self._latest_processed_frame if hasattr(self, '_latest_processed_frame') and self._latest_processed_frame is not None else self._generate_standby_frame("SNAPSHOT CAPTURED")
        snap_name = self.recorder.capture_evidence(frame, {"targets": [{"type": "MANUAL_CAPTURE"}]})
        if snap_name:
            self._total_intrusions += 1
            self.alert_mgr.trigger_intrusion({"targets": [{"type": "MANUAL_CAPTURE"}]}, snap_name)
            return snap_name
        return "snapshot_manual.jpg"

    def _generate_standby_frame(self, message: str = "INITIALIZING WEBCAM...") -> np.ndarray:
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:] = (15, 20, 32)
        cv2.putText(frame, "VisionSentinel Edge Engine", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (56, 189, 248), 2, cv2.LINE_AA)
        cv2.putText(frame, message, (20, self.height // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (148, 163, 184), 1, cv2.LINE_AA)
        return frame

    def _run_loop(self):
        while self._is_running:
            t_start = time.perf_counter()
            frame = None

            if self._cap and self._cap.isOpened():
                ret, frame = self._cap.read()
                if not ret or frame is None or np.mean(frame) < 0.01:
                    # Retry camera open if empty/black frame received
                    time.sleep(0.1)
                    if not ret:
                        self._open_camera()
                    frame = self._generate_standby_frame("RECONNECTING WEBCAM...")
            else:
                frame = self._generate_standby_frame("SEARCHING FOR WEBCAM...")
                time.sleep(0.2)
                self._open_camera()

            # Compute real luminance
            luminance = self.enhancer.compute_luminance(frame)

            # Apply Low-Light CLAHE Enhancement if enabled
            enhanced = self.enhancer.enhance(frame) if self.enable_enhancement else frame

            # Run AI Detection
            annotated, meta = self.detector.detect(enhanced)

            # Check for intrusion triggers
            if self.security_armed and meta["target_detected"]:
                self._total_intrusions += 1
                snap_name = self.recorder.capture_evidence(annotated, meta)
                if snap_name:
                    self.alert_mgr.trigger_intrusion(meta, snap_name)

            # Calculate FPS dynamically
            t_end = time.perf_counter()
            dt = max(t_end - self._last_frame_time, 0.001)
            self._last_frame_time = t_end
            inst_fps = 1.0 / dt
            self._fps_history.append(inst_fps)
            if len(self._fps_history) > 8:
                self._fps_history.pop(0)

            self._current_fps = round(sum(self._fps_history) / len(self._fps_history), 1)
            latency_ms = round((t_end - t_start) * 1000.0, 1)

            # Overlay HUD Telemetry on Frame
            cv2.putText(annotated, f"FPS: {self._current_fps}", (annotated.shape[1] - 115, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(annotated, f"Lux: {luminance:.1f}", (annotated.shape[1] - 120, 48),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)

            hud_status = "ARMED: " + ("ALERT" if meta["target_detected"] else "GUARDING") if self.security_armed else "DISARMED"
            hud_color = (0, 0, 255) if (self.security_armed and meta["target_detected"]) else ((0, 255, 128) if self.security_armed else (128, 128, 128))
            cv2.putText(annotated, hud_status, (15, annotated.shape[0] - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, hud_color, 2, cv2.LINE_AA)

            # JPEG Encode
            ret_enc, jpeg = cv2.imencode(".jpg", annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 82])

            with self._lock:
                self._latest_processed_frame = annotated
                if ret_enc:
                    self._latest_jpeg = jpeg.tobytes()
                self._latest_metrics = {
                    "fps": self._current_fps,
                    "target_detected": meta["target_detected"],
                    "target_count": meta["count"],
                    "avg_luminance": round(luminance, 1),
                    "source_type": self.source,
                    "total_intrusions": self._total_intrusions,
                    "armed": self.security_armed,
                    "presence_sec": meta.get("presence_sec", 0),
                    "latency_ms": latency_ms,
                    "clahe_enabled": self.enable_enhancement,
                    "timestamp": time.time()
                }

            # Target 30 FPS sleep limit
            proc_time = time.perf_counter() - t_start
            sleep_time = max(0.001, (1.0 / 30.0) - proc_time)
            time.sleep(sleep_time)

    def get_latest_frame_jpeg(self) -> Optional[bytes]:
        with self._lock:
            return self._latest_jpeg

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._latest_metrics)
