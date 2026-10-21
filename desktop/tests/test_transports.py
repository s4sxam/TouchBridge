import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from touchbridge.transport.scrcpy_transport import (
    ScrcpyTransport,
    CONTROL_MSG_TYPE_INJECT_TOUCH_EVENT,
    ACTION_DOWN,
    ACTION_MOVE,
    ACTION_UP,
)


class TestTransports(unittest.TestCase):

    def setUp(self):
        self.transport = ScrcpyTransport(screen_width=2400, screen_height=1080)

    def test_scrcpy_binary_packet_structure(self):
        """Verify binary packet exactly matches scrcpy C protocol 32-byte layout."""
        raw_pkt = self.transport._pack_touch_event(
            action=ACTION_DOWN,
            pointer_id=3,
            x=1200,
            y=540,
            pressure=1.0,
        )

        self.assertEqual(len(raw_pkt), 32)

        # Unpack big-endian struct
        msg_type, action, pointer_id, x, y, width, height, pressure_u16, btn, buttons = struct.unpack(
            ">BBQiiHHHII", raw_pkt
        )

        self.assertEqual(msg_type, CONTROL_MSG_TYPE_INJECT_TOUCH_EVENT)
        self.assertEqual(action, ACTION_DOWN)
        self.assertEqual(pointer_id, 3)
        self.assertEqual(x, 1200)
        self.assertEqual(y, 540)
        self.assertEqual(width, 2400)
        self.assertEqual(height, 1080)
        self.assertEqual(pressure_u16, 0xFFFF)
        self.assertEqual(btn, 1)

    def test_coordinate_clamping_in_packet(self):
        """Verify negative coordinates and oversize coordinates are clamped."""
        raw_pkt = self.transport._pack_touch_event(
            action=ACTION_MOVE,
            pointer_id=0,
            x=-50,
            y=3000,
            pressure=0.5,
        )

        _, _, _, x, y, width, height, _, _, _ = struct.unpack(">BBQiiHHHII", raw_pkt)
        self.assertEqual(x, 0)
        self.assertEqual(y, 1080)


if __name__ == "__main__":
    unittest.main()
