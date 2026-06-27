# 睡眠噪音守卫

Sleep Noise Guard listens to the local microphone, estimates noise level, and plays a feedback sound when the room stays above a sleep-disturbing threshold.

It is designed for a Bluetooth speaker and microphone through the operating system audio stack. Pair the devices first, then either use them as the default input/output devices or pass their `sounddevice` device IDs.

## What I Found on GitHub

I did not find a complete project that matches this exact workflow: sleep-focused ambient noise monitoring plus automatic playback of cough/walking/moving/dropping feedback sounds.

Closest references found:

- `ajithm3015/REAL-TIME-ACOUSTIC-NOISE-MONITORING-AND-VISUALIZATION-SYSTEM`: real-time environmental noise monitoring and dB visualization, but no sleep feedback playback workflow.
- `muehleisen/pyvslm`, `arupiot/Sound-level-meter`, and similar projects: sound level meter utilities, mostly focused on measuring/displaying SPL.
- `Kkawka0/ggwave-chat`: has a real-time microphone volume meter, but it is for sound-based chat rather than noise-triggered feedback.

So this repo implements the missing workflow locally.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

On macOS, `sounddevice` uses PortAudio. If installation or capture fails, install PortAudio first:

```bash
brew install portaudio
```

## Prepare Sounds

Put feedback audio files in `sounds/`. Supported extensions include `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`, `.aif`, and `.aiff`.

You can generate rough placeholder WAV files:

```bash
python3 scripts/generate_sample_sounds.py
```

For realistic use, replace them with short recordings such as cough, walking, moving furniture, or a dropped object.

## Run

List audio devices:

```bash
sleep-noise-guard --list-devices
```

Start with default input/output devices:

```bash
sleep-noise-guard --sounds-dir sounds --threshold-db 45 --min-duration 3 --cooldown 60
```

Use specific devices:

```bash
sleep-noise-guard --input-device 2 --output-device 5 --sounds-dir sounds
```

## Desktop UI / 桌面界面

Build the standalone macOS desktop UI:

```bash
chmod +x scripts/build_macos_app.sh
scripts/build_macos_app.sh
```

Open it:

```bash
open "outputs/睡眠噪音守卫.app"
```

Build the macOS DMG:

```bash
chmod +x scripts/build_macos_dmg.sh
scripts/build_macos_dmg.sh
```

Output:

```text
outputs/睡眠噪音守卫.dmg
```

The native UI is Chinese and uses a light desktop layout with controls for:

- Current estimated dB
- Start/stop listening
- Test feedback sound
- Threshold, sustained duration, cooldown, and calibration
- Optional trigger delay in seconds
- Optional trigger delay by noisy sample count
- Optional feedback playback repeat count
- CSV log path
- Hourly and daily noise/trigger statistics
- Input/output device ID or name
- Feedback sound directory

Leave input/output device fields blank to use the system default Bluetooth microphone and speaker.

Trigger delay fields are optional. If `出现几秒后触发`, `出现几次后触发`, and `每次反馈播放次数` are empty, the app plays one feedback sound as soon as a noise event crosses the threshold.

Noise events are recorded to CSV, defaulting to:

```bash
logs/noise_events.csv
```

Each row includes timestamp, hour bucket, date bucket, dB value, whether feedback was triggered, trigger count, feedback repeat count, and sound filenames.

## Windows EXE and Android APK

Windows and Android packages are built through GitHub Actions:

```text
.github/workflows/build-release.yml
```

Artifacts:

- `sleep-noise-guard-windows-exe`
- `sleep-noise-guard-android-apk`

Chinese documentation:

```text
docs/中文说明.md
```

## Calibration

The app measures microphone dBFS and adds `--calibration-offset-db` to estimate real-world dB. The default offset is only a practical starting point.

For better results, compare the printed reading against a phone SPL meter app or a real sound level meter, then adjust:

```bash
sleep-noise-guard --calibration-offset-db 90
```

## Defaults

- Threshold: `45 dB`
- Sustained duration before trigger: `3 seconds`
- Cooldown between triggers: `60 seconds`
- Sample rate: `16000 Hz`
- Audio block size: `0.5 seconds`

## Tests

```bash
python3 -m unittest discover -s tests
```
