"""TouchBridge Universal — Entry Point.

Universal Android Keyboard & Mouse Mapping for Windows.
"""

from __future__ import annotations
import argparse
import logging
import sys
from typing import Optional

from .core.models import Profile
from .core.profile_manager import ProfileManager
from .core.input_pipeline import InputPipeline
from .core.failsafe import FailsafeSupervisor
from .adb.device_manager import DeviceManager
from .adb.scrcpy_manager import ScrcpyManager
from .transport.scrcpy_transport import ScrcpyTransport
from .transport.companion_transport import CompanionTransport
from .transport.mock_transport import MockTransport
from .transport.base import InputTransport

# Optional PySide6 import
try:
    from PySide6.QtWidgets import QApplication
    from .gui.app_window import MainWindow
    HAS_GUI = True
except ImportError:
    HAS_GUI = False

# Optional pynput hook for global physical input capture
try:
    from pynput import keyboard, mouse
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("touchbridge")


class TouchBridgeApp:
    """TouchBridge Desktop Application orchestrator."""

    def __init__(self, use_mock: bool = False, headless: bool = False):
        self.use_mock = use_mock
        self.headless = headless

        logger.info("Initializing TouchBridge Universal...")
        self.device_manager = DeviceManager()
        self.scrcpy_manager = ScrcpyManager()
        self.profile_manager = ProfileManager()

        active_prof = self.profile_manager.get_active_profile() or Profile(name="Fallback")

        # Select transport
        if self.use_mock:
            self.transport: InputTransport = MockTransport(active_prof.ref_width, active_prof.ref_height)
        else:
            # Primary: scrcpy control transport
            self.transport = ScrcpyTransport(screen_width=active_prof.ref_width, screen_height=active_prof.ref_height)

        self.pipeline = InputPipeline(self.transport, active_prof)
        self.failsafe = FailsafeSupervisor(self.pipeline.emergency_release)

        self.kb_listener: Optional[object] = None
        self.mouse_listener: Optional[object] = None

    def start_global_listeners(self) -> None:
        """Start global physical keyboard and mouse listener hooks via pynput."""
        if not HAS_PYNPUT:
            logger.warning("pynput not installed; global hardware input listening disabled.")
            return

        def _on_press(key):
            try:
                k_name = key.char if hasattr(key, "char") and key.char else key.name
                self.pipeline.on_key_down(k_name)
            except Exception:
                pass

        def _on_release(key):
            try:
                k_name = key.char if hasattr(key, "char") and key.char else key.name
                self.pipeline.on_key_up(k_name)
            except Exception:
                pass

        def _on_click(x, y, button, pressed):
            btn_name = button.name if hasattr(button, "name") else str(button)
            if pressed:
                self.pipeline.on_mouse_down(btn_name)
            else:
                self.pipeline.on_mouse_up(btn_name)

        def _on_move(x, y):
            # Track relative delta
            if not hasattr(self, "_last_mouse_coord"):
                self._last_mouse_coord = (x, y)
                return
            dx = x - self._last_mouse_coord[0]
            dy = y - self._last_mouse_coord[1]
            self._last_mouse_coord = (x, y)
            self.pipeline.on_mouse_move(dx, dy)

        self.kb_listener = keyboard.Listener(on_press=_on_press, on_release=_on_release)
        self.kb_listener.daemon = True
        self.kb_listener.start()

        self.mouse_listener = mouse.Listener(on_move=_on_move, on_click=_on_click)
        self.mouse_listener.daemon = True
        self.mouse_listener.start()

        logger.info("Global input capture hooks active")

    def run(self) -> int:
        """Run application."""
        self.start_global_listeners()

        if HAS_GUI and not self.headless:
            app = QApplication(sys.argv)
            window = MainWindow(
                self.device_manager,
                self.scrcpy_manager,
                self.profile_manager,
                self.pipeline,
                self.failsafe,
            )
            window.show()
            return app.exec()
        else:
            logger.info("Running in headless / CLI mode.")
            logger.info("Active Profile: %s", self.profile_manager.get_active_profile().name)
            logger.info("Devices connected: %d", len(self.device_manager.list_devices()))
            logger.info("TouchBridge Universal core ready.")
            return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="TouchBridge Universal — Android Keyboard & Mouse Gaming Bridge")
    parser.add_argument("--mock", action="store_true", help="Run with in-memory mock transport for testing")
    parser.add_argument("--headless", action="store_true", help="Run in headless CLI mode without Qt GUI")
    args = parser.parse_args()

    app = TouchBridgeApp(use_mock=args.mock, headless=args.headless)
    sys.exit(app.run())


if __name__ == "__main__":
    main()
