import math
import random
import wave
from pathlib import Path


SAMPLE_RATE = 22050
OUTPUT_DIR = Path("sounds")


def write_wav(path: Path, samples):
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for sample in samples:
            clamped = max(-1.0, min(1.0, sample))
            frames.extend(int(clamped * 32767).to_bytes(2, "little", signed=True))
        wav.writeframes(bytes(frames))


def silence(seconds: float):
    return [0.0] * int(SAMPLE_RATE * seconds)


def burst(seconds: float, amplitude: float, lowpass: int = 12):
    value = 0.0
    samples = []
    count = int(SAMPLE_RATE * seconds)
    for index in range(count):
        envelope = 1.0 - index / max(1, count)
        value = (value * (lowpass - 1) + random.uniform(-1.0, 1.0)) / lowpass
        samples.append(value * amplitude * envelope)
    return samples


def tone(seconds: float, frequency: float, amplitude: float):
    count = int(SAMPLE_RATE * seconds)
    return [
        math.sin(2.0 * math.pi * frequency * index / SAMPLE_RATE) * amplitude
        for index in range(count)
    ]


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    cough = burst(0.22, 0.9, lowpass=8) + silence(0.08) + burst(0.18, 0.65, lowpass=7)
    steps = []
    for _ in range(5):
        steps += burst(0.07, 0.65, lowpass=10) + silence(0.28)
    moving = burst(0.7, 0.4, lowpass=24) + tone(0.25, 80, 0.2) + burst(0.35, 0.45, lowpass=20)
    dropped = silence(0.05) + burst(0.08, 1.0, lowpass=4) + tone(0.22, 160, 0.25)

    write_wav(OUTPUT_DIR / "cough_placeholder.wav", cough)
    write_wav(OUTPUT_DIR / "walking_placeholder.wav", steps)
    write_wav(OUTPUT_DIR / "moving_placeholder.wav", moving)
    write_wav(OUTPUT_DIR / "dropped_placeholder.wav", dropped)

    print(f"Wrote placeholder sounds to {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
