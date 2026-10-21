"""Unit tests for DeviceManager ADB parsing."""

import unittest
from touchbridge.adb.device_manager import DeviceManager, AndroidDevice


class TestDeviceManager(unittest.TestCase):

    def setUp(self):
        self.mgr = DeviceManager()

    def test_parse_device_line_authorized(self):
        """Verify parsing standard authorized adb device line."""
        line = "988a1b444558504f47 device product:redmi_note12 model:Redmi_Note_12 device:sunstone transport_id:1"
        dev = self.mgr._parse_device_line(line)
        self.assertIsNotNone(dev)
        self.assertEqual(dev.serial, "988a1b444558504f47")
        self.assertEqual(dev.state, "device")
        self.assertTrue(dev.is_authorized)
        self.assertEqual(dev.model, "Redmi Note 12")

    def test_parse_device_line_unauthorized(self):
        """Verify parsing unauthorized adb device line."""
        line = "emulator-5554 unauthorized transport_id:2"
        dev = self.mgr._parse_device_line(line)
        self.assertIsNotNone(dev)
        self.assertEqual(dev.serial, "emulator-5554")
        self.assertEqual(dev.state, "unauthorized")
        self.assertFalse(dev.is_authorized)


if __name__ == "__main__":
    unittest.main()
