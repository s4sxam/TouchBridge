"""Unit tests for FailsafeSupervisor and Emergency Release."""

import unittest
from touchbridge.core.models import Binding, ControlType, Profile
from touchbridge.core.input_pipeline import InputPipeline
from touchbridge.core.failsafe import FailsafeSupervisor
from touchbridge.transport.mock_transport import MockTransport


class TestFailsafe(unittest.TestCase):

    def setUp(self):
        self.profile = Profile(
            name="Failsafe Test",
            emergency_stop_key="f12",
            bindings=[
                Binding(id="b1", name="Action 1", control_type=ControlType.TAP, key="q"),
                Binding(id="b2", name="Action 2", control_type=ControlType.TAP, key="e"),
            ],
        )
        self.transport = MockTransport(2400, 1080)
        self.transport.connect()
        self.pipeline = InputPipeline(self.transport, self.profile)
        self.pipeline.start()
        self.failsafe = FailsafeSupervisor(self.pipeline.emergency_release)

    def tearDown(self):
        self.pipeline.stop()

    def test_emergency_key_releases_all(self):
        """Verify pressing F12 emergency stop hotkey instantly releases all contacts."""
        self.pipeline.on_key_down("q")
        self.pipeline.on_key_down("e")
        self.assertEqual(len(self.transport.active_pointers), 2)

        # Trigger emergency hotkey
        self.pipeline.on_key_down("f12")
        self.assertEqual(len(self.transport.active_pointers), 0)
        self.assertEqual(len(self.pipeline.held_keys), 0)

    def test_window_focus_lost_triggers_release(self):
        """Verify losing window focus clears all active touch pointers."""
        self.pipeline.on_key_down("q")
        self.assertEqual(len(self.transport.active_pointers), 1)

        self.failsafe.on_window_focus_lost()
        self.assertEqual(len(self.transport.active_pointers), 0)


if __name__ == "__main__":
    unittest.main()
