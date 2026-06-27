from pathlib import Path
from typing import Iterable, List


SUPPORTED_EXTENSIONS = {".aiff", ".aif", ".flac", ".m4a", ".mp3", ".ogg", ".wav"}


class SoundLibrary:
    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self._index = 0

    def files(self) -> List[Path]:
        if not self.directory.exists():
            return []

        return sorted(
            path
            for path in self.directory.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        )

    def next_sound(self) -> Path:
        files = self.files()
        if not files:
            raise FileNotFoundError(f"No supported audio files found in {self.directory}")

        selected = files[self._index % len(files)]
        self._index += 1
        return selected
