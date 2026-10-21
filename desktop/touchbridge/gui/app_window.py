"""TouchBridge Main Application Window."""

from __future__ import annotations
import logging

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QMainWindow, QTabWidget, QStatusBar, QMessageBox
    )
    HAS_QT = True
except ImportError:
    HAS_QT = False
    QMainWindow = object  # type: ignore

from .dashboard_view import DashboardView
from .device_view import DeviceView
from .profile_view import ProfileView
from .keymap_editor_view import KeymapEditorView
from .runtime_hud import RuntimeHudView

logger = logging.getLogger("touchbridge.gui.main_window")


class MainWindow(QMainWindow if HAS_QT else object):
    """Main TouchBridge Desktop Application Window."""

    def __init__(self, device_manager, scrcpy_manager, profile_manager, pipeline, failsafe):
        if not HAS_QT:
            return
        super().__init__()
        self.device_manager = device_manager
        self.scrcpy_manager = scrcpy_manager
        self.profile_manager = profile_manager
        self.pipeline = pipeline
        self.failsafe = failsafe

        self.setWindowTitle("TouchBridge Universal — Android Keyboard & Mouse Gaming Bridge")
        self.resize(1100, 720)
        self.setMinimumSize(880, 560)

        self._init_ui()

    def _init_ui(self) -> None:
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            "QTabBar::tab { font-size: 13px; font-weight: bold; padding: 10px 18px; }"
            "QTabBar::tab:selected { color: #4F46E5; border-bottom: 3px solid #4F46E5; }"
        )

        # 1. Dashboard
        self.dashboard_view = DashboardView(self.device_manager, self.scrcpy_manager)
        self.tabs.addTab(self.dashboard_view, "📊 Dashboard")

        # 2. Device Manager
        self.device_view = DeviceView(self.device_manager)
        self.tabs.addTab(self.device_view, "📱 Device Manager")

        # 3. Game Profile Manager
        self.profile_view = ProfileView(self.profile_manager, self.device_manager)
        if hasattr(self.profile_view, "profile_changed") and self.profile_view.profile_changed:
            self.profile_view.profile_changed.connect(self._on_profile_switched)
        self.tabs.addTab(self.profile_view, "🎮 Game Profiles")

        # 4. Live Keymap Editor
        self.editor_view = KeymapEditorView(self.profile_manager)
        self.tabs.addTab(self.editor_view, "🎯 Keymap Editor")

        # 5. Runtime Controls & HUD
        self.runtime_view = RuntimeHudView(self.pipeline, self.failsafe)
        self.tabs.addTab(self.runtime_view, "⚡ Runtime Controls")

        self.setCentralWidget(self.tabs)

        # Status Bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("TouchBridge Universal Ready | Press F12 for Emergency Stop")

    def _on_profile_switched(self, profile_id: str) -> None:
        """Propagate active profile change to editor and pipeline."""
        prof = self.profile_manager.get_active_profile()
        if prof:
            self.editor_view.reload_profile()
            self.pipeline._configure_profile(prof)
            self.statusBar.showMessage(f"Active Profile: {prof.name}")

    def closeEvent(self, event) -> None:
        """Handle application close safely."""
        logger.info("Window close event received: executing failsafe release")
        self.failsafe.trigger_emergency_release()
        self.scrcpy_manager.stop()
        event.accept()
