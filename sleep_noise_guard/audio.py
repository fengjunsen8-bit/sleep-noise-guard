import math
from dataclasses import dataclass
from typing import Iterator, Optional


@dataclass(frozen=True)
class AudioLevel:
    timestamp: float
    dbfs: float
    estimated_db: float


def rms_to_dbfs(rms: float, floor_dbfs: float = -90.0) -> float:
    if rms <= 0:
        return floor_dbfs
    return max(20.0 * math.log10(rms), floor_dbfs)


def dbfs_to_estimated_spl(dbfs: float, calibration_offset_db: float) -> float:
    return dbfs + calibration_offset_db


class MicrophoneLevelStream:
    def __init__(
        self,
        sample_rate: int = 16000,
        block_seconds: float = 0.5,
        input_device: Optional[str] = None,
        calibration_offset_db: float = 94.0,
    ):
        self.sample_rate = sample_rate
        self.block_seconds = block_seconds
        self.input_device = input_device
        self.calibration_offset_db = calibration_offset_db

    def levels(self) -> Iterator[AudioLevel]:
        try:
            import numpy as np
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError(
                "Microphone capture needs the optional packages: sounddevice numpy"
            ) from exc

        block_size = max(1, int(self.sample_rate * self.block_seconds))

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=block_size,
            device=self.input_device,
        ) as stream:
            while True:
                samples, _overflowed = stream.read(block_size)
                rms = float(np.sqrt(np.mean(np.square(samples))))
                dbfs = rms_to_dbfs(rms)
                timestamp = sd.get_stream_time()
                yield AudioLevel(
                    timestamp=timestamp,
                    dbfs=dbfs,
                    estimated_db=dbfs_to_estimated_spl(dbfs, self.calibration_offset_db),
                )
