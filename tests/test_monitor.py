import unittest
from pathlib import Path

from sleep_noise_guard.audio import AudioLevel
from sleep_noise_guard.monitor import MonitorService


class FakePolicy:
    def __init__(self, trigger_on_call):
        self.trigger_on_call = trigger_on_call
        self.calls = 0

    def observe(self, _event):
        self.calls += 1
        return self.calls == self.trigger_on_call


class FakeLibrary:
    def __init__(self):
        self.selected = 0

    def next_sound(self):
        self.selected += 1
        return Path("sounds/cough.wav")


class FakePlayer:
    def __init__(self):
        self.played = []

    def play(self, path):
        self.played.append(path)


class FakeLogger:
    def __init__(self):
        self.records = []

    def record(self, **kwargs):
        self.records.append(kwargs)

    def stats(self):
        class Stats:
            hourly = {}
            daily = {}

        return Stats()


class MonitorServiceTest(unittest.TestCase):
    def test_updates_state_without_triggering_feedback(self):
        policy = FakePolicy(trigger_on_call=99)
        library = FakeLibrary()
        player = FakePlayer()
        service = MonitorService(policy=policy, library=library, player=player)

        service.process_level(AudioLevel(timestamp=1.0, dbfs=-50.0, estimated_db=44.0))

        self.assertEqual(service.state.current_db, 44.0)
        self.assertEqual(service.state.last_sound, None)
        self.assertEqual(player.played, [])

    def test_plays_next_sound_when_policy_triggers(self):
        policy = FakePolicy(trigger_on_call=1)
        library = FakeLibrary()
        player = FakePlayer()
        service = MonitorService(policy=policy, library=library, player=player)

        service.process_level(AudioLevel(timestamp=1.0, dbfs=-40.0, estimated_db=54.0))

        self.assertEqual(player.played, [Path("sounds/cough.wav")])
        self.assertEqual(service.state.last_sound, Path("sounds/cough.wav"))
        self.assertEqual(service.state.trigger_count, 1)

    def test_repeats_feedback_audio_when_configured(self):
        policy = FakePolicy(trigger_on_call=1)
        library = FakeLibrary()
        player = FakePlayer()
        service = MonitorService(policy=policy, library=library, player=player, feedback_repeats=3)

        service.process_level(AudioLevel(timestamp=1.0, dbfs=-40.0, estimated_db=54.0))

        self.assertEqual(player.played, [Path("sounds/cough.wav")] * 3)
        self.assertEqual(service.state.trigger_count, 1)

    def test_records_noisy_levels_to_logger(self):
        policy = FakePolicy(trigger_on_call=1)
        policy.threshold_db = 45.0
        logger = FakeLogger()
        service = MonitorService(
            policy=policy,
            library=FakeLibrary(),
            player=FakePlayer(),
            logger=logger,
            feedback_repeats=2,
        )

        service.process_level(AudioLevel(timestamp=1.0, dbfs=-40.0, estimated_db=54.0))
        service.process_level(AudioLevel(timestamp=2.0, dbfs=-70.0, estimated_db=24.0))

        self.assertEqual(len(logger.records), 1)
        self.assertEqual(logger.records[0]["db"], 54.0)
        self.assertTrue(logger.records[0]["triggered"])
        self.assertEqual(logger.records[0]["trigger_count"], 1)
        self.assertEqual(logger.records[0]["feedback_repeats"], 2)
        self.assertEqual(logger.records[0]["sounds"], ["cough.wav", "cough.wav"])


if __name__ == "__main__":
    unittest.main()
