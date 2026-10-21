"""TouchBridge Scrcpy Integration Manager.

Detects, configures, and launches scrcpy with optimal gaming parameters.
"""

from __future__ import annotations
import logging
import os
import shutil
import subprocess
from typing import List, Optional

logger = logging.getLogger("touchbridge.scrcpy_manager")


class ScrcpyManager:
    """Manages discovery and lifecycle of scrcpy processes."""

    def __init__(self, custom_scrcpy_path: Optional[str] = None):
        self.scrcpy_path = custom_scrcpy_path or self._find_scrcpy()
        self.proc: subprocess.Popen | None = None

    def _find_scrcpy(self) -> str:
        """Locate scrcpy executable."""
        which_scrcpy = shutil.which("scrcpy")
        if which_scrcpy:
            return which_scrcpy

        common_paths = [
            r"C:\scrcpy\scrcpy.exe",
            os.path.expandvars(r"%USERPROFILE%\scrcpy\scrcpy.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\scrcpy\scrcpy.exe"),
            r"C:\Program Files\scrcpy\scrcpy.exe",
        ]
        for p in common_paths:
            if os.path.exists(p):
                return p

        return "scrcpy"

    def is_installed(self) -> bool:
        """Check if scrcpy executable exists and runs."""
        try:
            res = subprocess.run(
                [self.scrcpy_path, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3,
            )
            return res.returncode == 0
        except Exception:
            return False

    def get_version(self) -> str:
        """Query scrcpy version."""
        try:
            res = subprocess.run(
                [self.scrcpy_path, "--version"],
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
        return "scrcpy Not Detected"

    def is_running(self) -> bool:
        """Check if scrcpy process is actively running."""
        return self.proc is not None and self.proc.poll() is None

    def launch(
        self,
        serial: Optional[str] = None,
        max_fps: int = 120,
        bit_rate_mb: int = 16,
        stay_awake: bool = True,
        turn_screen_off: bool = False,
        control: bool = True,
        port_range: str = "27183:27184",
    ) -> bool:
        """Launch scrcpy with gaming performance parameters."""
        if self.is_running():
            logger.info("Scrcpy is already running")
            return True

        args: List[str] = [self.scrcpy_path]
        if serial:
            args.extend(["-s", serial])

        args.extend([
            "--max-fps", str(max_fps),
            "--video-bit-rate", f"{bit_rate_mb}M",
            "--port", port_range,
            "--window-title", "TouchBridge Stream",
        ])

        if stay_awake:
            args.append("--stay-awake")
        if turn_screen_off:
            args.append("--turn-screen-off")
        if not control:
            args.append("--no-control")

        try:
            logger.info("Launching scrcpy: %s", " ".join(args))
            self.proc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return True
        except Exception as e:
            logger.error("Failed to launch scrcpy: %s", e)
            self.proc = None
            return False

    def stop(self) -> None:
        """Stop running scrcpy process."""
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=2.0)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
            self.proc = None
            logger.info("Scrcpy stopped")
