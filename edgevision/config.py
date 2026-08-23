import os
import yaml
from typing import Dict, Any

DEFAULT_CONFIG = {
    "vision": {
        "source": "webcam",  # 'webcam', 'synthetic', or rtsp/http stream url
        "device_index": 0,
        "frame_width": 640,
        "frame_height": 480,
        "target_fps": 30,
        "enable_enhancement": True,
        "enhancement_method": "clahe", # 'clahe', 'global_he', 'gamma'
        "clahe_clip_limit": 2.5,
        "clahe_grid_size": [8, 8],
        "gamma_value": 1.2,
        "detection_mode": "hybrid", # 'person', 'face', 'motion', or 'hybrid'
        "min_contour_area": 800,
        "security_armed": True,
        "cooldown_seconds": 5
    },
    "evidence": {
        "enabled": True,
        "save_dir": "evidence",
        "record_clips": True,
        "clip_duration_sec": 5
    },
    "alerts": {
        "audio_alarm": True,
        "telegram": {
            "enabled": False,
            "bot_token": "",
            "chat_id": ""
        }
    },
    "server": {
        "host": "0.0.0.0",
        "port": 8000,
        "cors_origins": ["*"]
    }
}

class Config:
    def __init__(self, config_dict: Dict[str, Any] = None):
        self._config = config_dict or DEFAULT_CONFIG

    @classmethod
    def load(cls, config_path: str = None) -> "Config":
        if config_path and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                merged = cls._deep_merge(DEFAULT_CONFIG, loaded or {})
                return cls(merged)
        return cls(DEFAULT_CONFIG)

    @staticmethod
    def _deep_merge(default: dict, override: dict) -> dict:
        result = default.copy()
        for k, v in override.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = Config._deep_merge(result[k], v)
            else:
                result[k] = v
        return result

    def get(self, key_path: str, default=None):
        parts = key_path.split(".")
        val = self._config
        for p in parts:
            if isinstance(val, dict) and p in val:
                val = val[p]
            else:
                return default
        return val

    def set(self, key_path: str, value):
        parts = key_path.split(".")
        val = self._config
        for p in parts[:-1]:
            if p not in val or not isinstance(val[p], dict):
                val[p] = {}
            val = val[p]
        val[parts[-1]] = value

    @property
    def raw(self) -> Dict[str, Any]:
        return self._config
