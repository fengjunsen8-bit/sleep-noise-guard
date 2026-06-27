import unittest

from sleep_noise_guard.audio import dbfs_to_estimated_spl, rms_to_dbfs


class AudioTest(unittest.TestCase):
    def test_converts_rms_to_dbfs(self):
        self.assertEqual(rms_to_dbfs(1.0), 0.0)
        self.assertAlmostEqual(rms_to_dbfs(0.5), -6.0206, places=3)

    def test_uses_floor_for_silence(self):
        self.assertEqual(rms_to_dbfs(0.0), -90.0)

    def test_applies_calibration_offset_to_estimate_spl(self):
        self.assertEqual(dbfs_to_estimated_spl(-50.0, 94.0), 44.0)


if __name__ == "__main__":
    unittest.main()
