import tempfile
import unittest
from pathlib import Path

from sleep_noise_guard.sound_library import SoundLibrary


class SoundLibraryTest(unittest.TestCase):
    def test_lists_supported_audio_files_in_stable_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "walk.wav").write_bytes(b"")
            (root / "note.txt").write_text("ignored", encoding="utf-8")
            (root / "cough.mp3").write_bytes(b"")

            library = SoundLibrary(root)

            self.assertEqual([path.name for path in library.files()], ["cough.mp3", "walk.wav"])

    def test_cycles_through_sound_files_without_repeating_first_choice(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.wav").write_bytes(b"")
            (root / "b.wav").write_bytes(b"")

            library = SoundLibrary(root)

            self.assertEqual(library.next_sound().name, "a.wav")
            self.assertEqual(library.next_sound().name, "b.wav")
            self.assertEqual(library.next_sound().name, "a.wav")


if __name__ == "__main__":
    unittest.main()
