"""
Image Processing & Low-Light Enhancement Module
Implements Adaptive Histogram Equalization (CLAHE), Global HE, and Gamma Correction.
"""
import cv2
import numpy as np
from typing import Tuple

class ImageEnhancer:
    def __init__(self, method: str = "clahe", clip_limit: float = 2.0, grid_size: Tuple[int, int] = (8, 8), gamma: float = 1.2):
        self.method = method
        self.clip_limit = clip_limit
        self.grid_size = tuple(grid_size)
        self.gamma = gamma
        self._clahe = cv2.createCLAHE(clipLimit=self.clip_limit, tileGridSize=self.grid_size)
        self._gamma_lut = self._build_gamma_lut(self.gamma)

    @staticmethod
    def _build_gamma_lut(gamma: float) -> np.ndarray:
        inv_gamma = 1.0 / max(gamma, 0.01)
        lut = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        return lut

    def set_gamma(self, gamma: float):
        self.gamma = gamma
        self._gamma_lut = self._build_gamma_lut(gamma)

    def enhance(self, frame: np.ndarray) -> np.ndarray:
        if frame is None or frame.size == 0:
            return frame

        if self.method == "clahe":
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab)
            enhanced_l = self._clahe.apply(l_channel)
            merged = cv2.merge((enhanced_l, a_channel, b_channel))
            return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

        elif self.method == "global_he":
            ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
            y, cr, cb = cv2.split(ycrcb)
            enhanced_y = cv2.equalizeHist(y)
            merged = cv2.merge((enhanced_y, cr, cb))
            return cv2.cvtColor(merged, cv2.COLOR_YCrCb2BGR)

        elif self.method == "gamma":
            return cv2.LUT(frame, self._gamma_lut)

        return frame

    @staticmethod
    def compute_luminance(frame: np.ndarray) -> float:
        if frame is None or frame.size == 0:
            return 0.0
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return float(np.mean(gray))
