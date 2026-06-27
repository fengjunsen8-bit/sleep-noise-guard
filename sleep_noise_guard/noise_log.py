import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List


FIELDNAMES = [
    "timestamp",
    "hour",
    "date",
    "db",
    "triggered",
    "trigger_count",
    "feedback_repeats",
    "sounds",
]


@dataclass
class StatBucket:
    noise_count: int = 0
    trigger_count: int = 0
    max_db: float = 0.0
    total_db: float = 0.0

    @property
    def avg_db(self) -> float:
        if self.noise_count == 0:
            return 0.0
        return self.total_db / self.noise_count

    def add(self, db: float, triggered: bool) -> None:
        self.noise_count += 1
        if triggered:
            self.trigger_count += 1
        self.max_db = max(self.max_db, db)
        self.total_db += db


@dataclass
class NoiseStats:
    hourly: Dict[str, StatBucket] = field(default_factory=dict)
    daily: Dict[str, StatBucket] = field(default_factory=dict)


class NoiseLogger:
    def __init__(self, path: Path = Path("logs/noise_events.csv")):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            with self.path.open("w", newline="", encoding="utf-8") as file:
                csv.DictWriter(file, fieldnames=FIELDNAMES).writeheader()

    def record(
        self,
        occurred_at: datetime,
        db: float,
        triggered: bool,
        trigger_count: int,
        feedback_repeats: int,
        sounds: Iterable[str],
    ) -> None:
        row = {
            "timestamp": occurred_at.isoformat(timespec="seconds"),
            "hour": occurred_at.strftime("%Y-%m-%d %H:00"),
            "date": occurred_at.strftime("%Y-%m-%d"),
            "db": f"{db:.1f}",
            "triggered": "1" if triggered else "0",
            "trigger_count": str(trigger_count),
            "feedback_repeats": str(feedback_repeats),
            "sounds": "|".join(sounds),
        }
        with self.path.open("a", newline="", encoding="utf-8") as file:
            csv.DictWriter(file, fieldnames=FIELDNAMES).writerow(row)

    def stats(self) -> NoiseStats:
        stats = NoiseStats()
        if not self.path.exists():
            return stats

        with self.path.open(encoding="utf-8") as file:
            for row in csv.DictReader(file):
                db = float(row["db"])
                triggered = row["triggered"] == "1"
                hour = row["hour"]
                day = row["date"]
                stats.hourly.setdefault(hour, StatBucket()).add(db, triggered)
                stats.daily.setdefault(day, StatBucket()).add(db, triggered)
        return stats
