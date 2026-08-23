import unittest
from edgevision.telemetry.alerts import AlertManager

class TestAlertManager(unittest.TestCase):
    def test_alert_manager_intrusion(self):
        mgr = AlertManager({"audio_alarm": False})
        meta = {
            "target_detected": True,
            "targets": [{"type": "PERSON", "confidence": 0.92, "box": [10, 10, 50, 100]}],
            "count": 1
        }
        alert = mgr.trigger_intrusion(meta, "snapshot_test.jpg")
        self.assertEqual(alert["type"], "INTRUSION_DETECTED")
        self.assertEqual(alert["severity"], "CRITICAL")
        self.assertEqual(len(mgr.get_history()), 1)

if __name__ == '__main__':
    unittest.main()
