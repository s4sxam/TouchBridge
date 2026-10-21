"""TouchBridge Profile Manager.

Handles persistence, validation, import/export, and switching of game keymap profiles.
"""

from __future__ import annotations
import json
import logging
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from .models import Binding, ControlType, Profile, ScreenOrientation

logger = logging.getLogger("touchbridge.profile_manager")


class ProfileManager:
    """Manages collection of game profiles stored on disk."""

    def __init__(self, profiles_dir: Optional[str] = None):
        if profiles_dir:
            self.profiles_dir = Path(profiles_dir)
        else:
            # Default profiles directory in project root or appdata
            self.profiles_dir = Path(__file__).resolve().parent.parent.parent / "profiles"

        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.profiles: Dict[str, Profile] = {}
        self.active_profile_id: Optional[str] = None
        self.load_all_profiles()

        if not self.profiles:
            self.create_default_profiles()

    def load_all_profiles(self) -> None:
        """Load all valid JSON profile files from the profiles directory."""
        self.profiles.clear()
        for file_path in self.profiles_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                profile = Profile.from_dict(data)
                self.profiles[profile.id] = profile
                logger.info("Loaded profile: %s (%s)", profile.name, profile.id)
            except Exception as e:
                logger.warning("Failed to load profile from %s: %s", file_path, e)

        if self.profiles and not self.active_profile_id:
            self.active_profile_id = next(iter(self.profiles.keys()))

    def create_default_profiles(self) -> None:
        """Create reference profiles for Generic FPS, MOBA, Battle Royale, and Racing."""
        fps_profile = self._build_generic_fps_profile()
        self.save_profile(fps_profile)

        moba_profile = self._build_generic_moba_profile()
        self.save_profile(moba_profile)

        br_profile = self._build_battle_royale_profile()
        self.save_profile(br_profile)

        racing_profile = self._build_racing_profile()
        self.save_profile(racing_profile)

        self.active_profile_id = fps_profile.id

    def save_profile(self, profile: Profile) -> Path:
        """Save a profile safely to disk in JSON format."""
        # Sanitize filename
        safe_name = "".join(c for c in profile.name if c.isalnum() or c in ("-", "_")).strip()
        if not safe_name:
            safe_name = "profile"
        file_path = self.profiles_dir / f"{safe_name.lower()}_{profile.id[:6]}.json"

        # Validate before writing
        self.validate_profile(profile)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, indent=2)

        self.profiles[profile.id] = profile
        return file_path

    def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile from memory and disk."""
        if profile_id not in self.profiles:
            return False

        profile = self.profiles.pop(profile_id)
        for file_path in self.profiles_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("id") == profile_id:
                    file_path.unlink(missing_ok=True)
                    break
            except Exception:
                continue

        if self.active_profile_id == profile_id:
            self.active_profile_id = next(iter(self.profiles.keys())) if self.profiles else None

        return True

    def duplicate_profile(self, profile_id: str, new_name: Optional[str] = None) -> Optional[Profile]:
        """Duplicate an existing profile with a new ID."""
        src = self.profiles.get(profile_id)
        if not src:
            return None

        data = src.to_dict()
        data["id"] = str(uuid.uuid4())
        data["name"] = new_name or f"{src.name} (Copy)"
        dup = Profile.from_dict(data)
        self.save_profile(dup)
        return dup

    def export_profile_json(self, profile_id: str) -> str:
        """Export profile as JSON string."""
        profile = self.profiles.get(profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found")
        return json.dumps(profile.to_dict(), indent=2)

    def import_profile_json(self, json_str: str) -> Profile:
        """Import a profile from JSON string with strict validation."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON data: {e}")

        if not isinstance(data, dict):
            raise ValueError("Root profile must be a JSON object")

        # Assign new ID to avoid collisions
        data["id"] = str(uuid.uuid4())
        profile = Profile.from_dict(data)
        self.validate_profile(profile)
        self.save_profile(profile)
        return profile

    def validate_profile(self, profile: Profile) -> None:
        """Enforce boundary checks, non-empty names, and security rules."""
        if not profile.name or not profile.name.strip():
            raise ValueError("Profile name cannot be empty")

        if profile.ref_width <= 0 or profile.ref_height <= 0:
            raise ValueError("Reference resolution width and height must be positive")

        for b in profile.bindings:
            b.clamp_coordinates()
            # Ensure no command injection strings in string fields
            for str_field in (b.name, b.key or "", b.mouse_button or "", b.up_key, b.down_key, b.left_key, b.right_key):
                if any(bad in str_field for bad in (";", "&&", "||", "`", "$", "|", "\n")):
                    raise ValueError(f"Dangerous characters detected in binding: {b.name}")

    def get_active_profile(self) -> Optional[Profile]:
        """Get currently active profile."""
        if self.active_profile_id and self.active_profile_id in self.profiles:
            return self.profiles[self.active_profile_id]
        if self.profiles:
            return next(iter(self.profiles.values()))
        return None

    def set_active_profile(self, profile_id: str) -> bool:
        """Set active profile by ID."""
        if profile_id in self.profiles:
            self.active_profile_id = profile_id
            return True
        return False

    # Reference profile builders
    def _build_generic_fps_profile(self) -> Profile:
        """Generic FPS Profile (WASD movement, Mouse Look, Space jump, R reload, C crouch, Shift sprint)."""
        bindings = [
            Binding(
                id="wasd_joy",
                name="Movement Joystick",
                control_type=ControlType.JOYSTICK,
                norm_x=0.18,
                norm_y=0.72,
                radius=0.12,
                up_key="w",
                down_key="s",
                left_key="a",
                right_key="d",
            ),
            Binding(
                id="mouse_aim",
                name="Mouse Look Zone",
                control_type=ControlType.MOUSE_LOOK,
                norm_x=0.72,
                norm_y=0.48,
                sensitivity_x=1.0,
                sensitivity_y=1.0,
                zone_width=0.45,
                zone_height=0.65,
            ),
            Binding(
                id="fire_btn",
                name="Primary Fire",
                control_type=ControlType.TAP,
                norm_x=0.88,
                norm_y=0.68,
                radius=0.06,
                mouse_button="left",
            ),
            Binding(
                id="ads_aim",
                name="Aim / Scope (ADS)",
                control_type=ControlType.TAP,
                norm_x=0.84,
                norm_y=0.48,
                radius=0.05,
                mouse_button="right",
                toggle=True,
            ),
            Binding(
                id="jump_btn",
                name="Jump",
                control_type=ControlType.TAP,
                norm_x=0.92,
                norm_y=0.78,
                radius=0.05,
                key="space",
            ),
            Binding(
                id="crouch_btn",
                name="Crouch",
                control_type=ControlType.TAP,
                norm_x=0.82,
                norm_y=0.82,
                radius=0.05,
                key="c",
            ),
            Binding(
                id="reload_btn",
                name="Reload",
                control_type=ControlType.TAP,
                norm_x=0.75,
                norm_y=0.28,
                radius=0.04,
                key="r",
            ),
            Binding(
                id="sprint_btn",
                name="Sprint",
                control_type=ControlType.TAP,
                norm_x=0.22,
                norm_y=0.52,
                radius=0.04,
                key="shift",
            ),
        ]
        return Profile(
            name="Generic Mobile FPS",
            package_name=None,
            orientation=ScreenOrientation.LANDSCAPE,
            ref_width=2400,
            ref_height=1080,
            mouse_sensitivity=1.0,
            bindings=bindings,
        )

    def _build_generic_moba_profile(self) -> Profile:
        """Generic MOBA Profile (WASD movement, Q/E/R/F Skills, B Recall, Space Attack)."""
        bindings = [
            Binding(
                id="moba_joy",
                name="Hero Movement",
                control_type=ControlType.JOYSTICK,
                norm_x=0.16,
                norm_y=0.74,
                radius=0.12,
                up_key="w",
                down_key="s",
                left_key="a",
                right_key="d",
            ),
            Binding(
                id="basic_attack",
                name="Basic Attack",
                control_type=ControlType.TAP,
                norm_x=0.88,
                norm_y=0.78,
                radius=0.08,
                key="space",
                mouse_button="left",
            ),
            Binding(
                id="skill_1",
                name="Skill 1",
                control_type=ControlType.TAP,
                norm_x=0.78,
                norm_y=0.82,
                radius=0.06,
                key="q",
            ),
            Binding(
                id="skill_2",
                name="Skill 2",
                control_type=ControlType.TAP,
                norm_x=0.82,
                norm_y=0.66,
                radius=0.06,
                key="e",
            ),
            Binding(
                id="skill_ult",
                name="Ultimate Skill",
                control_type=ControlType.TAP,
                norm_x=0.88,
                norm_y=0.54,
                radius=0.06,
                key="r",
            ),
            Binding(
                id="spell_btn",
                name="Battle Spell / Flash",
                control_type=ControlType.TAP,
                norm_x=0.72,
                norm_y=0.72,
                radius=0.05,
                key="f",
            ),
            Binding(
                id="recall_btn",
                name="Recall",
                control_type=ControlType.TAP,
                norm_x=0.62,
                norm_y=0.90,
                radius=0.04,
                key="b",
            ),
        ]
        return Profile(
            name="Generic Mobile MOBA",
            package_name=None,
            orientation=ScreenOrientation.LANDSCAPE,
            ref_width=2400,
            ref_height=1080,
            bindings=bindings,
        )

    def _build_battle_royale_profile(self) -> Profile:
        """Battle Royale shooter profile (Free Fire / PUBG Mobile style)."""
        fps = self._build_generic_fps_profile()
        fps.name = "Battle Royale Shooter"
        fps.package_name = "com.dts.freefireth"
        # Additional BR bindings: Backpack (Tab), Heal (4), Grenade (G), Interact (F)
        fps.bindings.extend([
            Binding(id="interact_f", name="Pick Up / Interact", norm_x=0.68, norm_y=0.45, key="f"),
            Binding(id="backpack_tab", name="Backpack", norm_x=0.10, norm_y=0.85, key="tab"),
            Binding(id="medkit_4", name="Use Medkit", norm_x=0.12, norm_y=0.60, key="4"),
            Binding(id="grenade_g", name="Grenade", norm_x=0.74, norm_y=0.60, key="g"),
        ])
        return fps

    def _build_racing_profile(self) -> Profile:
        """Arcade Racing Profile (Left/Right Steer, Space Nitro, Shift Drift)."""
        bindings = [
            Binding(id="steer_left", name="Steer Left", norm_x=0.12, norm_y=0.70, radius=0.08, key="a"),
            Binding(id="steer_right", name="Steer Right", norm_x=0.26, norm_y=0.70, radius=0.08, key="d"),
            Binding(id="nitro_btn", name="Nitro Boost", norm_x=0.88, norm_y=0.65, radius=0.09, key="space"),
            Binding(id="drift_btn", name="Brake / Drift", norm_x=0.72, norm_y=0.75, radius=0.08, key="shift"),
        ]
        return Profile(
            name="Arcade Racing",
            package_name=None,
            orientation=ScreenOrientation.LANDSCAPE,
            ref_width=2400,
            ref_height=1080,
            bindings=bindings,
        )
