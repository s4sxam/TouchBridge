"""ADB Shell Input Transport (Fallback).

Uses a persistent background adb shell process for devices where neither scrcpy
nor the companion server is available.
"""

from __future__ import annotations
import logging
import subprocess
from typing import Optional, Set

from .base import InputTransport

logger = logging.getLogger("touchbridge.transport.adb_shell")


class AdbShellTransport(InputTransport):
    """Fallback transport utilizing a persistent ADB shell pipe."""

    def __init__(
        self,
        adb_path: str = "adb",
        device_serial: Optional[str] = None,
        screen_width: int = 2400,
        screen_height: int = 1080,
    ):
        super().__init__(screen_width, screen_height)
        self.adb_path = adb_path
        self.device_serial = device_serial
        self.proc: subprocess.Popen | None = None

    def connect(self) -> bool:
        """Spawn persistent adb shell process."""
        cmd = [self.adb_path]
        if self.device_serial:
            cmd.extend(["-s", self.device_serial])
        cmd.extend(["shell"])

        try:
            self.proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
            )
            logger.info("Spawned persistent adb shell transport")
            return True
        except Exception as e:
            logger.error("Failed to start persistent adb shell: %s", e)
            self.proc = None
            return False

    def disconnect(self) -> None:
        """Terminate persistent adb shell."""
        self.release_all()
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=1.0)
            except Exception:
                pass
            self.proc = None

    def is_connected(self) -> bool:
        """Check if shell process is running."""
        return self.proc is not None and self.proc.poll() is None

    def _write_command(self, cmd_line: str) -> bool:
        """Write command to shell stdin."""
        if not self.is_connected() or not self.proc or not self.proc.stdin:
            return False
        try:
            self.proc.stdin.write(cmd_line + "\n")
            self.proc.stdin.flush()
            return True
        except Exception as e:
            logger.error("Error writing to adb shell stdin: %s", e)
            self.disconnect()
            return False

    def touch_down(self, pointer_id: int, x: int, y: int, pressure: float = 1.0) -> bool:
        """Fallback tap/touch."""
        self.active_pointers.add(pointer_id)
        # Persistent input tap
        return self._write_command(f"input tap {int(x)} {int(y)}")

    def touch_move(self, pointer_id: int, x: int, y: int, pressure: float = 1.0) -> bool:
        """Move event in shell (limited)."""
        self.active_pointers.add(pointer_id)
        return True

    def touch_up(self, pointer_id: int, x: int, y: int) -> bool:
        """Touch up."""
        self.active_pointers.discard(pointer_id)
        return True

    def release_all(self) -> None:
        """Clear active contacts."""
        self.active_pointers.clear()

    def get_latency_ms(self) -> float:
        """Shell pipe latency is typically 20-40ms."""
        return 28.0
