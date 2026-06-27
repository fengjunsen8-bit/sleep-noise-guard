import argparse
import time

from .audio import MicrophoneLevelStream
from .config import AppConfig
from .monitor import MonitorService
from .noise_log import NoiseLogger
from .player import SoundPlayer
from .policy import NoisePolicy
from .sound_library import SoundLibrary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Listen for sustained sleep-disturbing noise and play a feedback sound."
    )
    parser.add_argument("--sounds-dir", default="sounds", help="Directory containing feedback sounds")
    parser.add_argument("--threshold-db", type=float, default=45.0, help="Estimated dB threshold")
    parser.add_argument("--min-duration", type=float, default=None, help="Seconds above threshold before triggering")
    parser.add_argument("--noise-events", type=int, default=None, help="Number of noisy samples before triggering")
    parser.add_argument("--feedback-repeats", type=int, default=None, help="How many times to play feedback per trigger")
    parser.add_argument("--cooldown", type=float, default=60.0, help="Seconds to wait between triggers")
    parser.add_argument("--log-path", default="logs/noise_events.csv", help="CSV log path")
    parser.add_argument("--sample-rate", type=int, default=16000)
    parser.add_argument("--block-seconds", type=float, default=0.5)
    parser.add_argument(
        "--calibration-offset-db",
        type=float,
        default=94.0,
        help="Offset added to dBFS to estimate SPL; calibrate for your microphone.",
    )
    parser.add_argument("--input-device", default=None, help="sounddevice input device name or id")
    parser.add_argument("--output-device", default=None, help="sounddevice output device name or id")
    parser.add_argument("--list-devices", action="store_true", help="List audio devices and exit")
    return parser


def list_devices() -> None:
    try:
        import sounddevice as sd
    except ImportError as exc:
        raise RuntimeError("Device listing needs the optional package: sounddevice") from exc

    print(sd.query_devices())


def config_from_args(args: argparse.Namespace) -> AppConfig:
    return AppConfig(
        sounds_dir=args.sounds_dir,
        threshold_db=args.threshold_db,
        min_duration_seconds=args.min_duration,
        min_noise_events=args.noise_events,
        feedback_repeats=args.feedback_repeats,
        cooldown_seconds=args.cooldown,
        sample_rate=args.sample_rate,
        block_seconds=args.block_seconds,
        calibration_offset_db=args.calibration_offset_db,
        input_device=args.input_device,
        output_device=args.output_device,
        log_path=args.log_path,
    )


def run(config: AppConfig) -> None:
    library = SoundLibrary(config.sounds_dir)
    policy = NoisePolicy(
        threshold_db=config.threshold_db,
        min_duration_seconds=config.min_duration_seconds,
        cooldown_seconds=config.cooldown_seconds,
        min_noise_events=config.min_noise_events,
    )
    player = SoundPlayer(output_device=config.output_device)
    logger = NoiseLogger(path=config.log_path)
    service = MonitorService(
        policy=policy,
        library=library,
        player=player,
        logger=logger,
        feedback_repeats=config.feedback_repeats,
    )
    stream = MicrophoneLevelStream(
        sample_rate=config.sample_rate,
        block_seconds=config.block_seconds,
        input_device=config.input_device,
        calibration_offset_db=config.calibration_offset_db,
    )

    print("Listening. Press Ctrl+C to stop.")
    print(f"Log path: {logger.path}")
    last_printed_trigger_count = -1

    def print_update(state):
        nonlocal last_printed_trigger_count
        if state.current_db is None:
            return
        print(f"{time.strftime('%H:%M:%S')} estimated={state.current_db:.1f} dB dbfs={state.current_dbfs:.1f}")
        if state.last_sound is not None and state.trigger_count != last_printed_trigger_count:
            last_printed_trigger_count = state.trigger_count
            print(f"Last feedback sound: {state.last_sound}")
        print(
            "Stats: "
            f"hour_noise={state.hourly_noise_count} "
            f"hour_triggers={state.hourly_trigger_count} "
            f"day_noise={state.daily_noise_count} "
            f"day_triggers={state.daily_trigger_count}"
        )

    service.run(stream, on_update=print_update)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.list_devices:
        list_devices()
        return
    run(config_from_args(args))


if __name__ == "__main__":
    main()
