"""
Evidence Capture & Video Clip Recorder
Saves timestamped high-resolution intrusion snapshots and video recordings.
"""
import os
import cv2
import time
import glob
from typing import List, Dict, Any, Optional

class EvidenceRecorder:
    def __init__(self, save_dir: str = "evidence", enabled: bool = True):
        self.save_dir = save_dir
        self.enabled = enabled
        self.last_capture_time = 0
        self.min_cooldown = 4 # seconds between captures
        os.makedirs(self.save_dir, exist_ok=True)

    def capture_evidence(self, frame: Any, metadata: Dict[str, Any]) -> Optional[str]:
        """Saves a timestamped JPEG evidence snapshot."""
        if not self.enabled or frame is None:
            return None

        now = time.time()
        if now - self.last_capture_time < self.min_cooldown:
            return None

        self.last_capture_time = now
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        target_type = metadata.get("targets", [{}])[0].get("type", "EVENT") if metadata.get("targets") else "EVENT"
        filename = f"snapshot_{target_type}_{timestamp_str}.jpg"
        filepath = os.path.join(self.save_dir, filename)

        # Add watermark on snapshot
        watermarked = frame.copy()
        date_text = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(watermarked, f"[EVIDENCE] {date_text}", (15, watermarked.shape[0] - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)

        cv2.imwrite(filepath, watermarked, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        return filename

    def list_evidence(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Returns sorted list of captured evidence files."""
        pattern = os.path.join(self.save_dir, "snapshot_*.jpg")
        files = glob.glob(pattern)
        files.sort(key=os.path.getmtime, reverse=True)

        results = []
        for f in files[:limit]:
            fname = os.path.basename(f)
            mtime = os.path.getmtime(f)
            size_kb = round(os.path.getsize(f) / 1024, 1)
            results.append({
                "filename": fname,
                "url": f"/api/evidence/{fname}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime)),
                "size_kb": size_kb
            })
        return results
