import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

from .audio import AudioLevel
from .policy import NoiseEvent


@dataclass
class MonitorState:
    running: bool = False
    current_db: Optional[float] = None
    current_dbfs: Optional[float] = None
    last_sound: Optional[Path] = None
    trigger_count: int = 0
    hourly_noise_count: int = 0
    hourly_trigger_count: int = 0
    daily_noise_count: int = 0
    daily_trigger_count: int = 0
    error: Optional[str] = None


class MonitorService:
    def __init__(self, policy, library, player, logger=None, feedback_repeats: Optional[int] = None):
        self.policy = policy
        self.library = library
        self.player = player
        self.logger = logger
        self.feedback_repeats = max(1, feedback_repeats or 1)
        self.state = MonitorState()
        self._stop_requested = threading.Event()
        self._lock = threading.Lock()

    def process_level(self, level: AudioLevel) -> MonitorState:
        triggered = self.policy.observe(NoiseEvent(timestamp=level.timestamp, db=level.estimated_db))
        sound_names: List[str] = []
        with self._lock:
            self.state.current_db = level.estimated_db
            self.state.current_dbfs = level.dbfs
            self.state.error = None

        if triggered:
            sound = None
            for _ in range(self.feedback_repeats):
                sound = self.library.next_sound()
                self.player.play(sound)
                sound_names.append(sound.name)
            with self._lock:
                self.state.last_sound = sound
                self.state.trigger_count += 1

        self._record_noise_if_needed(level=level, triggered=triggered, sound_names=sound_names)
        return self.snapshot()

    def _record_noise_if_needed(self, level: AudioLevel, triggered: bool, sound_names: List[str]) -> None:
        if self.logger is None:
            return

        threshold = getattr(self.policy, "threshold_db", None)
        if threshold is not None and level.estimated_db < threshold:
            return

        self.logger.record(
            occurred_at=datetime.now(),
            db=level.estimated_db,
            triggered=triggered,
            trigger_count=self.state.trigger_count,
            feedback_repeats=self.feedback_repeats if triggered else 0,
            sounds=sound_names,
        )
        stats = self.logger.stats()
        now = datetime.now()
        hour_key = now.strftime("%Y-%m-%d %H:00")
        day_key = now.strftime("%Y-%m-%d")
        hourly = stats.hourly.get(hour_key)
        daily = stats.daily.get(day_key)
        with self._lock:
            self.state.hourly_noise_count = hourly.noise_count if hourly else 0
            self.state.hourly_trigger_count = hourly.trigger_count if hourly else 0
            self.state.daily_noise_count = daily.noise_count if daily else 0
            self.state.daily_trigger_count = daily.trigger_count if daily else 0

    def run(self, stream, on_update: Optional[Callable[[MonitorState], None]] = None) -> None:
        self._stop_requested.clear()
        with self._lock:
            self.state.running = True
            self.state.error = None

        try:
            for level in stream.levels():
                if self._stop_requested.is_set():
                    break
                state = self.process_level(level)
                if on_update is not None:
                    on_update(state)
        except Exception as exc:
            with self._lock:
                self.state.error = str(exc)
            if on_update is not None:
                on_update(self.snapshot())
        finally:
            with self._lock:
                self.state.running = False
            if on_update is not None:
                on_update(self.snapshot())

    def stop(self) -> None:
        self._stop_requested.set()

    def snapshot(self) -> MonitorState:
        with self._lock:
            return MonitorState(
                running=self.state.running,
                current_db=self.state.current_db,
                current_dbfs=self.state.current_dbfs,
                last_sound=self.state.last_sound,
                trigger_count=self.state.trigger_count,
                hourly_noise_count=self.state.hourly_noise_count,
                hourly_trigger_count=self.state.hourly_trigger_count,
                daily_noise_count=self.state.daily_noise_count,
                daily_trigger_count=self.state.daily_trigger_count,
                error=self.state.error,
            )
