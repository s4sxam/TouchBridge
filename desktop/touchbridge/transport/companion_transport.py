"""TouchBridge Android Companion App Transport.

Communicates over ADB port-forwarding (tcp:28200) to the TouchBridge Companion
App running on the Android device for live diagnostics, overlay calibration,
and testing.
"""

from __future__ import annotations
import json
import logging
import socket
import time
from typing import Dict, Tuple

from .base import InputTransport

logger = logging.getLogger("touchbridge.transport.companion")


class CompanionTransport(InputTransport):
    """TCP transport connecting to on-device TouchBridge Companion Server."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 28200,
        screen_width: int = 2400,
        screen_height: int = 1080,
    ):
        super().__init__(screen_width, screen_height)
        self.host = host
        self.port = port
        self.sock: socket.socket | None = None
        self._last_known_positions: Dict[int, Tuple[int, int]] = {}
        self._latencies: list[float] = []

    def connect(self) -> bool:
        """Connect to Android Companion TCP socket."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.sock.settimeout(2.0)
            self.sock.connect((self.host, self.port))
            self.sock.setblocking(False)
            logger.info("Connected to Companion Server at %s:%d", self.host, self.port)
            return True
        except Exception as e:
            logger.debug("Could not connect to Companion Server (%s:%d): %s", self.host, self.port, e)
            self.sock = None
            return False

    def disconnect(self) -> None:
        """Close companion socket."""
        self.release_all()
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def is_connected(self) -> bool:
        """Check connection state."""
        return self.sock is not None

    def _send_cmd(self, action: str, pointer_id: int, x: int, y: int, pressure: float = 1.0) -> bool:
        """Send a newline-delimited JSON command."""
        if not self.sock:
            return False
        payload = {
            "action": action,
            "id": int(pointer_id),
            "x": int(x),
            "y": int(y),
            "norm_x": round(x / max(1, self.screen_width), 4),
            "norm_y": round(y / max(1, self.screen_height), 4),
            "pressure": round(pressure, 2),
            "timestamp": time.time_ns() // 1_000_000,
        }
        data = (json.dumps(payload) + "\n").encode("utf-8")
        try:
            t0 = time.perf_counter()
            self.sock.sendall(data)
            dt = (time.perf_counter() - t0) * 1000.0
            self._latencies.append(dt)
            if len(self._latencies) > 50:
                self._latencies.pop(0)
            return True
        except Exception as e:
            logger.warning("Error sending to companion app: %s", e)
            self.disconnect()
            return False

    def touch_down(self, pointer_id: int, x: int, y: int, pressure: float = 1.0) -> bool:
        """Emit DOWN."""
        self.active_pointers.add(pointer_id)
        self._last_known_positions[pointer_id] = (x, y)
        return self._send_cmd("DOWN", pointer_id, x, y, pressure)

    def touch_move(self, pointer_id: int, x: int, y: int, pressure: float = 1.0) -> bool:
        """Emit MOVE."""
        self.active_pointers.add(pointer_id)
        self._last_known_positions[pointer_id] = (x, y)
        return self._send_cmd("MOVE", pointer_id, x, y, pressure)

    def touch_up(self, pointer_id: int, x: int, y: int) -> bool:
        """Emit UP."""
        self.active_pointers.discard(pointer_id)
        self._last_known_positions.pop(pointer_id, None)
        return self._send_cmd("UP", pointer_id, x, y, 0.0)

    def release_all(self) -> None:
        """Emergency release."""
        if not self.sock:
            return
        try:
            cmd = json.dumps({"action": "RELEASE_ALL", "timestamp": time.time_ns() // 1_000_000}) + "\n"
            self.sock.sendall(cmd.encode("utf-8"))
        except Exception:
            pass
        self.active_pointers.clear()
        self._last_known_positions.clear()

    def get_latency_ms(self) -> float:
        """Return average injection latency."""
        if not self._latencies:
            return 2.5
        return sum(self._latencies) / len(self._latencies)
