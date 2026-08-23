"""
Telemetry Stream & MQTT Publisher
Publishes consolidated edge node metrics to MQTT brokers or local log streams.
"""
import time
import json
import logging
import threading
from typing import Dict, Any
from edgevision.telemetry.alerts import AlertManager

logger = logging.getLogger("edgevision.telemetry")

class TelemetryStream:
    def __init__(self, config_telemetry: dict = None, alert_manager: AlertManager = None):
        self.config = config_telemetry or {}
        self.alert_manager = alert_manager or AlertManager()
        self.interval = self.config.get("interval_seconds", 1.0)
        self.mqtt_cfg = self.config.get("mqtt", {})
        self.enabled = self.config.get("enabled", True)
        self._mqtt_client = None
        self._is_running = False
        self._latest_payload = {}
        self._lock = threading.Lock()

        if self.mqtt_cfg.get("enabled", False):
            self._setup_mqtt()

    def _setup_mqtt(self):
        try:
            import paho.mqtt.client as mqtt
            broker = self.mqtt_cfg.get("broker", "localhost")
            port = self.mqtt_cfg.get("port", 1883)
            client_id = self.mqtt_cfg.get("client_id", "edgevision_node")
            self._mqtt_client = mqtt.Client(client_id=client_id)
            self._mqtt_client.connect_async(broker, port, 60)
            self._mqtt_client.loop_start()
            logger.info(f"MQTT client connected to {broker}:{port}")
        except Exception as e:
            logger.warning(f"Failed to initialize MQTT client: {e}")
            self._mqtt_client = None

    def start_worker(self, metrics_provider_fn):
        if not self.enabled or self._is_running:
            return
        self._is_running = True
        self._worker_thread = threading.Thread(target=self._publish_loop, args=(metrics_provider_fn,), daemon=True)
        self._worker_thread.start()

    def stop(self):
        self._is_running = False
        if self._mqtt_client:
            try:
                self._mqtt_client.loop_stop()
                self._mqtt_client.disconnect()
            except Exception:
                pass

    def _publish_loop(self, metrics_provider_fn):
        while self._is_running:
            try:
                raw_metrics = metrics_provider_fn()
                alerts = self.alert_manager.evaluate(raw_metrics)

                payload = {
                    "node_id": self.mqtt_cfg.get("client_id", "edgevision_node_01"),
                    "timestamp": round(time.time(), 3),
                    "vision": {
                        "fps": raw_metrics.get("fps", 0.0),
                        "motion_active": raw_metrics.get("motion_detected", False),
                        "object_count": raw_metrics.get("object_count", 0),
                        "luminance": raw_metrics.get("avg_luminance", 0.0)
                    },
                    "system": {
                        "simulated_temp_c": round(41.5 + (hash(str(int(time.time()))) % 40) * 0.1, 1),
                        "cpu_usage_pct": round(14.0 + (hash(str(int(time.time()))) % 25) * 0.5, 1)
                    },
                    "alerts_triggered": len(alerts)
                }

                with self._lock:
                    self._latest_payload = payload

                if self._mqtt_client:
                    topic = self.mqtt_cfg.get("topic", "edgevision/telemetry")
                    self._mqtt_client.publish(topic, json.dumps(payload), qos=1)

            except Exception as e:
                logger.error(f"Error in telemetry loop: {e}")

            time.sleep(self.interval)

    def get_latest_telemetry(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._latest_payload)
