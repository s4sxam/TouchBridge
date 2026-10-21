"""TouchBridge Android Device Manager.

Detects ADB devices, queries authorization state, extracts device specs
(Xiaomi/Redmi brand, screen resolution, Android version), and sets up port forwarding.
"""

from __future__ import annotations
import logging
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("touchbridge.device_manager")


@dataclass
class AndroidDevice:
    """Represents a connected physical or virtual Android device."""
    serial: str
    state: str  # "device" (authorized), "unauthorized", "offline"
    model: str = "Unknown Device"
    manufacturer: str = "Unknown"
    android_version: str = "Unknown"
    screen_width: int = 2400
    screen_height: int = 1080
    density_dpi: int = 440
    is_xiaomi_redmi: bool = False
    requires_xiaomi_security_setup: bool = False

    @property
    def is_authorized(self) -> bool:
        return self.state == "device"


class DeviceManager:
    """Detects, inspects, and manages ADB connections to Android devices."""

    def __init__(self, custom_adb_path: Optional[str] = None):
        self.adb_path = custom_adb_path or self._find_adb()
        self.selected_device: Optional[AndroidDevice] = None

    def _find_adb(self) -> str:
        """Find ADB executable on system PATH or default Windows directories."""
        # 1. System PATH
        which_adb = shutil.which("adb")
        if which_adb:
            return which_adb

        # 2. Common Windows paths
        common_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"),
            r"C:\scrcpy\adb.exe",
            r"C:\platform-tools\adb.exe",
            os.path.expandvars(r"%USERPROFILE%\scrcpy\adb.exe"),
        ]
        for p in common_paths:
            if os.path.exists(p):
                return p

        return "adb"

    def is_adb_installed(self) -> bool:
        """Check if ADB can be executed."""
        try:
            res = subprocess.run(
                [self.adb_path, "version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3,
            )
            return res.returncode == 0
        except Exception:
            return False

    def get_adb_version(self) -> str:
        """Query ADB version string."""
        try:
            res = subprocess.run(
                [self.adb_path, "version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3,
            )
            if res.returncode == 0:
                first_line = res.stdout.strip().split("\n")[0]
                return first_line
        except Exception:
            pass
        return "ADB Not Detected"

    def list_devices(self) -> List[AndroidDevice]:
        """Query `adb devices -l` and parse all connected devices."""
        devices: List[AndroidDevice] = []
        try:
            res = subprocess.run(
                [self.adb_path, "devices", "-l"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )
            if res.returncode != 0:
                return []

            lines = res.stdout.strip().split("\n")[1:]  # skip header
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                dev = self._parse_device_line(line)
                if dev:
                    # If device is authorized, query extended properties
                    if dev.is_authorized:
                        self._populate_device_details(dev)
                    devices.append(dev)
        except Exception as e:
            logger.error("Error executing adb devices: %s", e)

        # Maintain selected device
        if devices:
            if not self.selected_device or self.selected_device.serial not in [d.serial for d in devices]:
                self.selected_device = devices[0]
        else:
            self.selected_device = None

        return devices

    def _parse_device_line(self, line: str) -> Optional[AndroidDevice]:
        """Parse single output line from `adb devices -l`."""
        parts = line.split()
        if len(parts) < 2:
            return None

        serial = parts[0]
        state = parts[1]

        model = "Android Device"
        for part in parts[2:]:
            if part.startswith("model:"):
                model = part.split("model:")[1].replace("_", " ")

        return AndroidDevice(serial=serial, state=state, model=model)

    def _populate_device_details(self, dev: AndroidDevice) -> None:
        """Query detailed device parameters via ADB shell."""
        try:
            # Query manufacturer & Android version
            props = self._run_adb_cmd(["-s", dev.serial, "shell", "getprop"])
            if props:
                for line in props.split("\n"):
                    if "ro.product.manufacturer" in line:
                        m = re.search(r":\s*\[(.*?)\]", line)
                        if m:
                            dev.manufacturer = m.group(1).capitalize()
                    elif "ro.build.version.release" in line:
                        m = re.search(r":\s*\[(.*?)\]", line)
                        if m:
                            dev.android_version = m.group(1)

            # Check Xiaomi / Redmi specific
            mfg_lower = dev.manufacturer.lower()
            if "xiaomi" in mfg_lower or "redmi" in mfg_lower or "poco" in mfg_lower:
                dev.is_xiaomi_redmi = True
                dev.requires_xiaomi_security_setup = True

            # Query screen resolution: `wm size`
            wm_size_out = self._run_adb_cmd(["-s", dev.serial, "shell", "wm", "size"])
            if wm_size_out:
                # e.g., "Physical size: 1080x2400"
                match = re.search(r"(\d+)x(\d+)", wm_size_out)
                if match:
                    w = int(match.group(1))
                    h = int(match.group(2))
                    # Usually games run in landscape: ensure width >= height
                    dev.screen_width = max(w, h)
                    dev.screen_height = min(w, h)

            # Query density: `wm density`
            wm_dens_out = self._run_adb_cmd(["-s", dev.serial, "shell", "wm", "density"])
            if wm_dens_out:
                match = re.search(r"(\d+)", wm_dens_out)
                if match:
                    dev.density_dpi = int(match.group(1))

        except Exception as e:
            logger.warning("Could not query device specs for %s: %s", dev.serial, e)

    def _run_adb_cmd(self, args: List[str]) -> str:
        """Run ADB command and return stdout."""
        try:
            res = subprocess.run(
                [self.adb_path] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=4,
            )
            return res.stdout.strip()
        except Exception:
            return ""

    def setup_port_forward(self, local_port: int = 28200, remote_port: int = 28200) -> bool:
        """Execute `adb forward tcp:<local> tcp:<remote>` for companion communication."""
        if not self.selected_device or not self.selected_device.is_authorized:
            return False
        try:
            res = subprocess.run(
                [self.adb_path, "-s", self.selected_device.serial, "forward", f"tcp:{local_port}", f"tcp:{remote_port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=4,
            )
            return res.returncode == 0
        except Exception as e:
            logger.error("Failed to forward port %d: %s", local_port, e)
            return False

    def get_foreground_package(self) -> Optional[str]:
        """Detect current active running game package on the phone screen."""
        if not self.selected_device or not self.selected_device.is_authorized:
            return None
        out = self._run_adb_cmd(["-s", self.selected_device.serial, "shell", "dumpsys", "window", "displays"])
        if not out:
            out = self._run_adb_cmd(["-s", self.selected_device.serial, "shell", "dumpsys", "activity", "activities"])
        
        match = re.search(r"(?:mCurrentFocus|mFocusedApp|topResumedActivity|mResumeActivity).*?([a-zA-Z0-9._]+)/", out)
        if match:
            pkg = match.group(1)
            # Filter out home launchers
            if not any(launcher in pkg for launcher in ("launcher", "systemui", "nexuslauncher", "miui.home")):
                return pkg
    KNOWN_GAMES = {
        "com.dts.freefireth": ("Free Fire", "fps"),
        "com.dts.freefiremax": ("Free Fire MAX", "fps"),
        "com.tencent.ig": ("PUBG Mobile", "fps"),
        "com.pubg.imobile": ("BGMI", "fps"),
        "com.activision.callofduty.shooter": ("Call of Duty: Mobile", "fps"),
        "com.miHoYo.GenshinImpact": ("Genshin Impact", "fps"),
        "com.supercell.brawlstars": ("Brawl Stars", "moba"),
        "com.mobile.legends": ("Mobile Legends", "moba"),
        "com.gameloft.android.ANMP.GloftA9HM": ("Asphalt 9", "racing"),
        "com.ea.gp.apexmobile": ("Apex Legends Mobile", "fps"),
        "com.roblox.client": ("Roblox", "fps"),
        "com.mojang.minecraftpe": ("Minecraft", "fps"),
    }

    def auto_detect_game(self) -> Optional[Tuple[str, str, str]]:
        """Detect current active game on phone. Returns (game_name, package_name, genre)."""
        pkg = self.get_foreground_package()
        if not pkg:
            return None
        if pkg in self.KNOWN_GAMES:
            name, genre = self.KNOWN_GAMES[pkg]
            return (name, pkg, genre)
        clean_name = pkg.split(".")[-1].replace("_", " ").title()
        return (clean_name, pkg, "fps")

    def remove_port_forward(self, local_port: int = 28200) -> bool:
        """Remove port forwarding."""
        try:
            subprocess.run(
                [self.adb_path, "forward", "--remove", f"tcp:{local_port}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2,
            )
            return True
        except Exception:
            return False

