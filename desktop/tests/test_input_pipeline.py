"""Unit tests for InputPipeline, simultaneous multi-touch, and joystick math."""

import unittest

from touchbridge.core.models import Binding, ControlType, Profile
from touchbridge.core.input_pipeline import (
    InputPipeline,
    JOYSTICK_POINTER_ID,
    MOUSE_LOOK_POINTER_ID,
    MIN_DYNAMIC_POINTER_ID,
)
from touchbridge.transport.mock_transport import MockTransport


class TestInputPipeline(unittest.TestCase):

    def setUp(self):
        self.profile = Profile(
            name="Test FPS",
            ref_width=2000,
            ref_height=1000,
            bindings=[
                Binding(
                    id="wasd_joy",
                    name="Movement",
                    control_type=ControlType.JOYSTICK,
                    norm_x=0.2,
                    norm_y=0.7,
                    radius=0.1,
                    up_key="w",
                    down_key="s",
                    left_key="a",
                    right_key="d",
                ),
                Binding(
                    id="mouse_aim",
                    name="Mouse Aim",
                    control_type=ControlType.MOUSE_LOOK,
                    norm_x=0.7,
                    norm_y=0.5,
                    zone_width=0.4,
                    zone_height=0.6,
                ),
                Binding(
                    id="jump_btn",
                    name="Jump",
                    control_type=ControlType.TAP,
                    norm_x=0.9,
                    norm_y=0.8,
                    key="space",
                ),
                Binding(
                    id="fire_btn",
                    name="Fire",
                    control_type=ControlType.TAP,
                    norm_x=0.85,
                    norm_y=0.65,
                    mouse_button="left",
                ),
            ],
        )
        self.transport = MockTransport(2000, 1000)
        self.transport.connect()
        self.pipeline = InputPipeline(self.transport, self.profile)
        self.pipeline.start()

    def tearDown(self):
        self.pipeline.stop()

    def test_wasd_joystick_movement_and_diagonal(self):
        """Test pressing W moves up, pressing D moves diagonal without releasing touch."""
        # 1. Press W -> DOWN at (400, 700 - 100) = (400, 600)
        self.pipeline.on_key_down("w")
        self.assertTrue(self.pipeline.joystick_active)
        self.assertIn(JOYSTICK_POINTER_ID, self.transport.active_pointers)
        self.assertEqual(self.transport.events[-1].action, "DOWN")
        self.assertEqual(self.transport.events[-1].pointer_id, JOYSTICK_POINTER_ID)
        self.assertEqual(self.transport.events[-1].x, 400)
        self.assertEqual(self.transport.events[-1].y, 600)

        # 2. While holding W, press D -> MOVE event (diagonal ~45 degrees)
        self.pipeline.on_key_down("d")
        self.assertTrue(self.pipeline.joystick_active)
        # Crucial check: still exactly ONE DOWN event on ID 0, no extra DOWN
        self.assertEqual(self.transport.down_counts[JOYSTICK_POINTER_ID], 1)
        self.assertEqual(self.transport.events[-1].action, "MOVE")
        self.assertEqual(self.transport.events[-1].pointer_id, JOYSTICK_POINTER_ID)
        # Vector should be (400 + 70, 700 - 70) = (470, 630)
        self.assertGreater(self.transport.events[-1].x, 400)
        self.assertLess(self.transport.events[-1].y, 700)

        # 3. Release W -> still moving right (D only)
        self.pipeline.on_key_up("w")
        self.assertTrue(self.pipeline.joystick_active)
        self.assertEqual(self.transport.events[-1].action, "MOVE")
        self.assertEqual(self.transport.events[-1].x, 500)  # 400 + 100

        # 4. Release D -> UP event
        self.pipeline.on_key_up("d")
        self.assertFalse(self.pipeline.joystick_active)
        self.assertNotIn(JOYSTICK_POINTER_ID, self.transport.active_pointers)
        self.assertEqual(self.transport.events[-1].action, "UP")

    def test_key_repeat_deduplication(self):
        """Verify repeated OS key-down events for held keys are ignored."""
        self.pipeline.on_key_down("space")
        initial_events_count = len(self.transport.events)
        # Simulate OS auto-repeat while key is held
        self.pipeline.on_key_down("space")
        self.pipeline.on_key_down("space")
        self.assertEqual(len(self.transport.events), initial_events_count)

        self.pipeline.on_key_up("space")
        self.assertEqual(len(self.transport.events), initial_events_count + 1)
        self.assertEqual(self.transport.events[-1].action, "UP")

    def test_simultaneous_multi_touch(self):
        """Verify holding WASD (ID 0) + Space (ID 2) + Left Click (ID 3) produces 3 active contacts."""
        self.pipeline.on_key_down("w")
        self.pipeline.on_key_down("space")
        self.pipeline.on_mouse_down("left")

        # 3 simultaneous pointers active
        self.assertEqual(len(self.transport.active_pointers), 3)
        self.assertIn(JOYSTICK_POINTER_ID, self.transport.active_pointers)
        self.assertIn(MIN_DYNAMIC_POINTER_ID, self.transport.active_pointers)
        self.assertIn(MIN_DYNAMIC_POINTER_ID + 1, self.transport.active_pointers)

        # Release Jump (space) -> only ID 2 is released; Joystick and Fire remain active
        self.pipeline.on_key_up("space")
        self.assertEqual(len(self.transport.active_pointers), 2)
        self.assertIn(JOYSTICK_POINTER_ID, self.transport.active_pointers)
        self.assertNotIn(MIN_DYNAMIC_POINTER_ID, self.transport.active_pointers)

        # Release Fire (mouse) -> only ID 0 remains active
        self.pipeline.on_mouse_up("left")
        self.assertEqual(len(self.transport.active_pointers), 1)
        self.assertIn(JOYSTICK_POINTER_ID, self.transport.active_pointers)

        # Release W -> 0 active pointers
        self.pipeline.on_key_up("w")
        self.assertEqual(len(self.transport.active_pointers), 0)

    def test_mouse_look_and_boundary_reset(self):
        """Test mouse look movement and micro-flick reset at zone boundary."""
        # Relative mouse movement
        self.pipeline.on_mouse_move(10.0, 5.0)
        self.assertIn(MOUSE_LOOK_POINTER_ID, self.transport.active_pointers)
        self.assertEqual(self.transport.events[-1].pointer_id, MOUSE_LOOK_POINTER_ID)

        # Giant swipe triggering boundary reset
        self.pipeline.on_mouse_move(2000.0, 0.0)
        # Should have executed UP and immediate DOWN reset at center
        self.assertIn(MOUSE_LOOK_POINTER_ID, self.transport.active_pointers)
        self.assertEqual(self.transport.events[-1].action, "DOWN")


if __name__ == "__main__":
    unittest.main()
