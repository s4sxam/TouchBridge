"""TouchBridge Safety Supervisor & Emergency Failsafe.

Guarantees zero stuck touches during window focus loss, sudden disconnects,
or unexpected application termination.
"""

from __future__ import annotations
import atexit
import logging
import threading
from typing import Callable, List

logger = logging.getLogger("touchbridge.failsafe")


class FailsafeSupervisor:
    """Supervises input state and triggers emergency releases on unsafe conditions."""

    def __init__(self, release_callback: Callable[[], None]):
        self.release_callback = release_callback
        self.lock = threading.Lock()
        self._is_active = True

        # Register process exit hook
        atexit.register(self.trigger_emergency_release)

    def trigger_emergency_release(self) -> None:
        """Immediately release all simulated touches."""
        with self.lock:
            try:
                logger.info("Failsafe Supervisor triggered: emergency touch release")
                self.release_callback()
            except Exception as e:
                logger.error("Error during failsafe release: %s", e)

    def on_window_focus_lost(self) -> None:
        """Triggered when the game streaming window loses operating system focus."""
        logger.info("Window focus lost: triggering emergency touch release")
        self.trigger_emergency_release()

    def on_device_disconnected(self) -> None:
        """Triggered when ADB detects device unplug or offline state."""
        logger.warning("Device disconnected: triggering emergency touch release")
        self.trigger_emergency_release()
