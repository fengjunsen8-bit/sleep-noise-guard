import unittest

from sleep_noise_guard.policy import NoiseEvent, NoisePolicy


class NoisePolicyTest(unittest.TestCase):
    def test_triggers_after_noise_stays_above_threshold_for_required_duration(self):
        policy = NoisePolicy(threshold_db=45.0, min_duration_seconds=3.0, cooldown_seconds=10.0)

        self.assertFalse(policy.observe(NoiseEvent(timestamp=0.0, db=46.0)))
        self.assertFalse(policy.observe(NoiseEvent(timestamp=2.9, db=47.0)))
        self.assertTrue(policy.observe(NoiseEvent(timestamp=3.0, db=48.0)))

    def test_resets_when_noise_drops_below_threshold(self):
        policy = NoisePolicy(threshold_db=45.0, min_duration_seconds=3.0, cooldown_seconds=10.0)

        self.assertFalse(policy.observe(NoiseEvent(timestamp=0.0, db=46.0)))
        self.assertFalse(policy.observe(NoiseEvent(timestamp=1.0, db=40.0)))
        self.assertFalse(policy.observe(NoiseEvent(timestamp=3.0, db=48.0)))

    def test_respects_cooldown_after_triggering(self):
        policy = NoisePolicy(threshold_db=45.0, min_duration_seconds=1.0, cooldown_seconds=10.0)

        self.assertFalse(policy.observe(NoiseEvent(timestamp=0.0, db=46.0)))
        self.assertTrue(policy.observe(NoiseEvent(timestamp=1.0, db=47.0)))
        self.assertFalse(policy.observe(NoiseEvent(timestamp=2.0, db=48.0)))
        self.assertTrue(policy.observe(NoiseEvent(timestamp=11.0, db=48.0)))

    def test_can_wait_for_multiple_noise_events_before_triggering(self):
        policy = NoisePolicy(
            threshold_db=45.0,
            min_duration_seconds=0.0,
            cooldown_seconds=10.0,
            min_noise_events=3,
        )

        self.assertFalse(policy.observe(NoiseEvent(timestamp=0.0, db=46.0)))
        self.assertFalse(policy.observe(NoiseEvent(timestamp=0.5, db=47.0)))
        self.assertTrue(policy.observe(NoiseEvent(timestamp=1.0, db=48.0)))

    def test_default_policy_triggers_on_first_noise_event(self):
        policy = NoisePolicy(threshold_db=45.0, min_duration_seconds=None, cooldown_seconds=10.0)

        self.assertTrue(policy.observe(NoiseEvent(timestamp=0.0, db=46.0)))


if __name__ == "__main__":
    unittest.main()
