"""
Alert Management & Real Notification Dispatcher
Triggers audible beeps and sends real photos to Telegram channels.
"""
import os
import time
import logging
import threading
import urllib.request
from typing import Dict, Any, List, Optional

logger = logging.getLogger("edgevision.alerts")

class AlertManager:
    def __init__(self, config_alerts: dict = None, save_dir: str = "evidence"):
        self.config = config_alerts or {}
        self.save_dir = save_dir
        self.audio_alarm = self.config.get("audio_alarm", True)
        self.telegram_cfg = self.config.get("telegram", {})
        self.alert_history: List[Dict[str, Any]] = []
        self._last_alert_time = 0
        self._cooldown = 4 # seconds

    def trigger_intrusion(self, metadata: Dict[str, Any], snapshot_file: Optional[str] = None) -> Dict[str, Any]:
        """Dispatches real alert notifications when an intrusion/target is detected."""
        now = time.time()
        targets = metadata.get("targets", [])
        types = [t.get("type", "TARGET") for t in targets]
        summary = ", ".join(set(types)) or "MOTION"

        alert_item = {
            "id": f"ALT-{int(now * 1000) % 100000}",
            "type": "INTRUSION_DETECTED",
            "severity": "CRITICAL" if ("PERSON" in types or "FACE" in types) else "WARNING",
            "message": f"Security Alert: {summary} detected ({len(targets)} target(s)).",
            "timestamp": now,
            "snapshot": snapshot_file
        }

        self.alert_history.insert(0, alert_item)
        if len(self.alert_history) > 100:
            self.alert_history.pop()

        if now - self._last_alert_time >= self._cooldown:
            self._last_alert_time = now
            # 1. Play local audible warning on Windows
            if self.audio_alarm:
                threading.Thread(target=self._play_beep, daemon=True).start()

            # 2. Send Telegram photo alert if configured
            if self.telegram_cfg.get("enabled", False) and snapshot_file:
                threading.Thread(target=self._send_telegram, args=(alert_item, snapshot_file), daemon=True).start()

        return alert_item

    def _play_beep(self):
        try:
            import winsound
            winsound.Beep(1200, 250)
        except Exception:
            pass

    def _send_telegram(self, alert: dict, snapshot_file: str):
        bot_token = self.telegram_cfg.get("bot_token")
        chat_id = self.telegram_cfg.get("chat_id")
        if not bot_token or not chat_id:
            return

        filepath = os.path.join(self.save_dir, snapshot_file)
        if not os.path.exists(filepath):
            return

        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
            body = []

            body.extend([
                f"--{boundary}".encode(),
                f'Content-Disposition: form-data; name="chat_id"'.encode(),
                b'',
                str(chat_id).encode()
            ])

            caption = "Alert: " + alert['message'] + " at " + time.strftime('%Y-%m-%d %H:%M:%S')
            body.extend([
                f"--{boundary}".encode(),
                f'Content-Disposition: form-data; name="caption"'.encode(),
                b'',
                caption.encode()
            ])

            with open(filepath, "rb") as f:
                photo_bytes = f.read()

            body.extend([
                f"--{boundary}".encode(),
                f'Content-Disposition: form-data; name="photo"; filename="{snapshot_file}"'.encode(),
                b'Content-Type: image/jpeg',
                b'',
                photo_bytes
            ])
            body.extend([f"--{boundary}--".encode(), b''])

            req = urllib.request.Request(url, data=b'\r\n'.join(body))
            req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
            with urllib.request.urlopen(req, timeout=10) as resp:
                logger.info(f"Telegram alert photo dispatched successfully: {resp.status}")
        except Exception as e:
            logger.warning(f"Failed to send Telegram alert: {e}")

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self.alert_history[:limit]
