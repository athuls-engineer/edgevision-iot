import unittest
import numpy as np
from edgevision.vision.enhancer import ImageEnhancer
from edgevision.vision.detector import RealWorldDetector

class TestVisionModules(unittest.TestCase):
    def test_enhancer_initialization(self):
        enhancer = ImageEnhancer(method="clahe", clip_limit=2.5)
        self.assertEqual(enhancer.method, "clahe")
        self.assertEqual(enhancer.clip_limit, 2.5)

    def test_enhancer_processing_preserves_shape(self):
        enhancer = ImageEnhancer(method="clahe")
        dummy_frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        enhanced = enhancer.enhance(dummy_frame)
        self.assertEqual(enhanced.shape, dummy_frame.shape)
        self.assertEqual(enhanced.dtype, np.uint8)

    def test_real_world_detector_initialization(self):
        detector = RealWorldDetector(detection_mode="hybrid", min_area=500)
        self.assertEqual(detector.detection_mode, "hybrid")
        self.assertEqual(detector.min_area, 500)

    def test_detector_execution(self):
        detector = RealWorldDetector(detection_mode="motion", min_area=200)
        dummy_frame = np.zeros((300, 300, 3), dtype=np.uint8)
        annotated, meta = detector.detect(dummy_frame)
        self.assertIn("target_detected", meta)
        self.assertEqual(annotated.shape, dummy_frame.shape)

if __name__ == '__main__':
    unittest.main()
