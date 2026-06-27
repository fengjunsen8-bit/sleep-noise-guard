from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class AppConfig:
    sounds_dir: Path = Path("sounds")
    threshold_db: float = 45.0
    min_duration_seconds: Optional[float] = None
    min_noise_events: Optional[int] = None
    feedback_repeats: Optional[int] = None
    cooldown_seconds: float = 60.0
    sample_rate: int = 16000
    block_seconds: float = 0.5
    calibration_offset_db: float = 94.0
    input_device: Optional[str] = None
    output_device: Optional[str] = None
    log_path: Path = Path("logs/noise_events.csv")
