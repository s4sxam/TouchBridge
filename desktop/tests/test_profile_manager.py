import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from touchbridge.core.models import Binding, ControlType, Profile, ScreenOrientation
from touchbridge.core.profile_manager import ProfileManager


class TestProfileManager(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.manager = ProfileManager(profiles_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_default_profiles_created(self):
        """Verify default profiles are created on empty directory."""
        self.assertGreaterEqual(len(self.manager.profiles), 4)
        active = self.manager.get_active_profile()
        self.assertIsNotNone(active)
        self.assertTrue(any("FPS" in p.name for p in self.manager.profiles.values()))

    def test_coordinate_clamping(self):
        """Verify out-of-bounds coordinates are clamped to [0.0, 1.0]."""
        b = Binding(name="Test", norm_x=1.5, norm_y=-0.2, radius=0.9)
        b.clamp_coordinates()
        self.assertEqual(b.norm_x, 1.0)
        self.assertEqual(b.norm_y, 0.0)
        self.assertEqual(b.radius, 0.5)

    def test_duplicate_profile(self):
        """Verify duplicate profile creates distinct ID."""
        active = self.manager.get_active_profile()
        dup = self.manager.duplicate_profile(active.id, "My Custom Clone")
        self.assertIsNotNone(dup)
        self.assertNotEqual(dup.id, active.id)
        self.assertEqual(dup.name, "My Custom Clone")
        self.assertIn(dup.id, self.manager.profiles)

    def test_export_and_import(self):
        """Verify JSON round-trip export and import with security checks."""
        active = self.manager.get_active_profile()
        json_data = self.manager.export_profile_json(active.id)

        imported = self.manager.import_profile_json(json_data)
        self.assertIsNotNone(imported)
        self.assertEqual(imported.name, active.name)
        self.assertNotEqual(imported.id, active.id)

    def test_reject_injected_shell_characters(self):
        """Verify profile with dangerous shell injection strings is rejected."""
        prof = Profile(name="Exploit")
        b = Binding(name="BadBinding; rm -rf /", norm_x=0.5, norm_y=0.5)
        prof.bindings.append(b)

        with self.assertRaises(ValueError):
            self.manager.save_profile(prof)


if __name__ == "__main__":
    unittest.main()
