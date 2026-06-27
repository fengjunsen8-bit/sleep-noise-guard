from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class NoiseEvent:
    timestamp: float
    db: float


class NoisePolicy:
    def __init__(
        self,
        threshold_db: float,
        min_duration_seconds: Optional[float],
        cooldown_seconds: float,
        min_noise_events: Optional[int] = None,
    ):
        self.threshold_db = threshold_db
        self.min_duration_seconds = min_duration_seconds or 0.0
        self.cooldown_seconds = cooldown_seconds
        self.min_noise_events = max(1, min_noise_events or 1)
        self._above_since: Optional[float] = None
        self._last_triggered_at: Optional[float] = None
        self._noise_events = 0

    def observe(self, event: NoiseEvent) -> bool:
        if event.db < self.threshold_db:
            self._above_since = None
            self._noise_events = 0
            return False

        if self._above_since is None:
            self._above_since = event.timestamp
            self._noise_events = 0
        self._noise_events += 1

        if event.timestamp - self._above_since < self.min_duration_seconds:
            return False

        if self._noise_events < self.min_noise_events:
            return False

        if self._last_triggered_at is not None:
            if event.timestamp - self._last_triggered_at < self.cooldown_seconds:
                return False

        self._last_triggered_at = event.timestamp
        return True
