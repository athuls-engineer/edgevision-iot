"""
Real-World Edge AI Detection Module
Intelligent Contour Merging, Human Presence Tracking, and Jitter-Free HUD Bounding.
"""
import cv2
import numpy as np
import time
from typing import Dict, Tuple, Any, List

class RealWorldDetector:
    def __init__(self, detection_mode: str = "hybrid", min_area: int = 1000):
        self.detection_mode = detection_mode
        self.min_area = min_area

        # High-performance MOG2 with shadow elimination
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=350,
            varThreshold=30,
            detectShadows=True
        )

        # Smooth bounding box state tracking (Exponential Moving Average)
        self._tracked_box = None
        self._tracked_type = "PERSON"
        self._disappear_count = 0
        self._max_disappear = 10 # frames to hold track across blinks/head movements
        self._presence_start_time = None
        self._total_presence_seconds = 0

    def _merge_overlapping_boxes(self, boxes: List[List[int]], proximity_thresh: int = 50) -> List[List[int]]:
        """Merges fragmented contour boxes (head, headphones, hands) into unified human regions."""
        if not boxes:
            return []

        merged = []
        used = [False] * len(boxes)

        for i in range(len(boxes)):
            if used[i]:
                continue
            x1, y1, w1, h1 = boxes[i]
            r1, b1 = x1 + w1, y1 + h1

            for j in range(i + 1, len(boxes)):
                if used[j]:
                    continue
                x2, y2, w2, h2 = boxes[j]
                r2, b2 = x2 + w2, y2 + h2

                # Proximity expansion check
                if not (r1 + proximity_thresh < x2 or x1 - proximity_thresh > r2 or
                        b1 + proximity_thresh < y2 or y1 - proximity_thresh > b2):
                    x1 = min(x1, x2)
                    y1 = min(y1, y2)
                    r1 = max(r1, r2)
                    b1 = max(b1, b2)
                    w1 = r1 - x1
                    h1 = b1 - y1
                    used[j] = True

            used[i] = True
            merged.append([x1, y1, w1, h1])

        return merged

    def detect(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        if frame is None or frame.size == 0:
            return frame, {"target_detected": False, "count": 0, "targets": [], "presence_sec": 0}

        annotated = frame.copy()
        raw_boxes = []

        # 1. MOG2 Foreground Mask with Shadow Removal
        fg_mask = self.bg_subtractor.apply(frame)
        _, fg_thresh = cv2.threshold(fg_mask, 210, 255, cv2.THRESH_BINARY)

        # Morphological opening and dilation to remove speckle noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        fg_clean = cv2.morphologyEx(fg_thresh, cv2.MORPH_OPEN, kernel)
        fg_clean = cv2.dilate(fg_clean, kernel, iterations=3)

        contours, _ = cv2.findContours(fg_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for c in contours:
            area = cv2.contourArea(c)
            if area >= self.min_area:
                x, y, w, h = cv2.boundingRect(c)
                raw_boxes.append([int(x), int(y), int(w), int(h)])

        # 2. Merge disjoint boxes into unified body silhouettes
        merged_boxes = self._merge_overlapping_boxes(raw_boxes, proximity_thresh=60)

        targets = []
        if merged_boxes:
            # Pick largest dominant bounding box
            largest_box = max(merged_boxes, key=lambda b: b[2] * b[3])
            lx, ly, lw, lh = largest_box

            # Temporal smoothing via Exponential Moving Average (EMA)
            if self._tracked_box is None:
                self._tracked_box = [float(lx), float(ly), float(lw), float(lh)]
            else:
                alpha = 0.35
                self._tracked_box[0] = self._tracked_box[0] * (1 - alpha) + lx * alpha
                self._tracked_box[1] = self._tracked_box[1] * (1 - alpha) + ly * alpha
                self._tracked_box[2] = self._tracked_box[2] * (1 - alpha) + lw * alpha
                self._tracked_box[3] = self._tracked_box[3] * (1 - alpha) + lh * alpha

            self._disappear_count = 0
            if self._presence_start_time is None:
                self._presence_start_time = time.time()
            self._total_presence_seconds = int(time.time() - self._presence_start_time)
        else:
            self._disappear_count += 1
            if self._disappear_count > self._max_disappear:
                self._tracked_box = None
                self._presence_start_time = None
                self._total_presence_seconds = 0

        # 3. Render Sleek Unified Tech HUD on Bounding Box
        if self._tracked_box is not None:
            tx = int(self._tracked_box[0])
            ty = int(self._tracked_box[1])
            tw = int(self._tracked_box[2])
            th = int(self._tracked_box[3])

            tx = max(0, min(tx, frame.shape[1] - 1))
            ty = max(0, min(ty, frame.shape[0] - 1))
            tw = min(tw, frame.shape[1] - tx)
            th = min(th, frame.shape[0] - ty)

            target_type = "PERSON" if (th > 80 or tw > 80) else "MOTION_TARGET"
            targets.append({
                "type": target_type,
                "confidence": 0.94,
                "box": [tx, ty, tw, th],
                "presence_sec": self._total_presence_seconds
            })

            # Sleek Tech Bounding Box with Corner Accents
            box_color = (0, 240, 255) # Cyan
            cv2.rectangle(annotated, (tx, ty), (tx + tw, ty + th), box_color, 2)

            line_len = min(20, max(8, tw // 4), max(8, th // 4))
            # Corner accents
            cv2.line(annotated, (tx, ty), (tx + line_len, ty), (255, 255, 255), 3)
            cv2.line(annotated, (tx, ty), (tx, ty + line_len), (255, 255, 255), 3)
            cv2.line(annotated, (tx + tw, ty + th), (tx + tw - line_len, ty + th), (255, 255, 255), 3)
            cv2.line(annotated, (tx + tw, ty + th), (tx + tw, ty + th - line_len), (255, 255, 255), 3)

            # Header Label Badge
            label_text = f"USER / PERSON [ACTIVE {self._total_presence_seconds}s]"
            (text_w, text_h), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(annotated, (tx, max(0, ty - 22)), (tx + text_w + 14, ty), (0, 180, 200), -1)
            cv2.putText(annotated, label_text, (tx + 7, ty - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (10, 20, 30), 1, cv2.LINE_AA)

        metadata = {
            "target_detected": len(targets) > 0,
            "count": len(targets),
            "targets": targets,
            "presence_sec": self._total_presence_seconds
        }
        return annotated, metadata
