import platform
import subprocess
from pathlib import Path
from typing import Optional


class SoundPlayer:
    def __init__(self, output_device: Optional[str] = None):
        self.output_device = output_device

    def play(self, path: Path) -> None:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(path)

        if path.suffix.lower() == ".wav":
            if self._try_sounddevice(path):
                return

        self._play_with_system_player(path)

    def _try_sounddevice(self, path: Path) -> bool:
        try:
            import sounddevice as sd
            import wave
            import numpy as np
        except ImportError:
            return False

        with wave.open(str(path), "rb") as wav:
            frames = wav.readframes(wav.getnframes())
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            sample_rate = wav.getframerate()

        if sample_width == 2:
            samples = np.frombuffer(frames, dtype=np.int16).astype("float32") / 32768.0
        elif sample_width == 1:
            samples = (np.frombuffer(frames, dtype=np.uint8).astype("float32") - 128.0) / 128.0
        else:
            return False

        if channels > 1:
            samples = samples.reshape(-1, channels)

        sd.play(samples, samplerate=sample_rate, device=self.output_device)
        sd.wait()
        return True

    def _play_with_system_player(self, path: Path) -> None:
        system = platform.system()
        if system == "Darwin":
            command = ["afplay", str(path)]
        elif system == "Linux":
            command = ["aplay", str(path)]
        elif system == "Windows":
            command = [
                "powershell",
                "-NoProfile",
                "-Command",
                f"(New-Object Media.SoundPlayer '{path}').PlaySync();",
            ]
        else:
            raise RuntimeError(f"No system audio player configured for {system}")

        subprocess.run(command, check=True)
