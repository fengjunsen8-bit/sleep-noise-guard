import csv
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from sleep_noise_guard.noise_log import NoiseLogger


class NoiseLoggerTest(unittest.TestCase):
    def test_records_noise_events_to_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "noise.csv"
            logger = NoiseLogger(path=path)
            occurred_at = datetime(2026, 6, 27, 23, 5, 7)

            logger.record(
                occurred_at=occurred_at,
                db=52.4,
                triggered=True,
                trigger_count=1,
                feedback_repeats=2,
                sounds=["cough.wav", "walk.wav"],
            )

            with path.open(encoding="utf-8") as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["timestamp"], "2026-06-27T23:05:07")
            self.assertEqual(rows[0]["hour"], "2026-06-27 23:00")
            self.assertEqual(rows[0]["date"], "2026-06-27")
            self.assertEqual(rows[0]["db"], "52.4")
            self.assertEqual(rows[0]["triggered"], "1")
            self.assertEqual(rows[0]["trigger_count"], "1")
            self.assertEqual(rows[0]["feedback_repeats"], "2")
            self.assertEqual(rows[0]["sounds"], "cough.wav|walk.wav")

    def test_summarizes_hourly_and_daily_noise(self):
        with tempfile.TemporaryDirectory() as directory:
            logger = NoiseLogger(path=Path(directory) / "noise.csv")
            logger.record(datetime(2026, 6, 27, 22, 0, 0), 50.0, False, 0, 0, [])
            logger.record(datetime(2026, 6, 27, 22, 5, 0), 60.0, True, 1, 1, ["cough.wav"])
            logger.record(datetime(2026, 6, 27, 23, 0, 0), 45.0, False, 1, 0, [])

            stats = logger.stats()

            self.assertEqual(stats.hourly["2026-06-27 22:00"].noise_count, 2)
            self.assertEqual(stats.hourly["2026-06-27 22:00"].trigger_count, 1)
            self.assertEqual(stats.hourly["2026-06-27 22:00"].max_db, 60.0)
            self.assertEqual(stats.daily["2026-06-27"].noise_count, 3)
            self.assertEqual(stats.daily["2026-06-27"].trigger_count, 1)
            self.assertEqual(stats.daily["2026-06-27"].max_db, 60.0)


if __name__ == "__main__":
    unittest.main()
