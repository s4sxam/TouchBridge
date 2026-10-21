"""TouchBridge Dashboard View.

Displays ADB status, Scrcpy status, connected device info, and quick actions.
"""

from __future__ import annotations
import logging
from typing import Optional

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QGroupBox, QGridLayout, QFrame, QMessageBox
    )
    HAS_QT = True
except ImportError:
    HAS_QT = False
    QWidget = object  # type: ignore

logger = logging.getLogger("touchbridge.gui.dashboard")


class DashboardView(QWidget if HAS_QT else object):
    """Primary overview dashboard."""

    def __init__(self, device_manager, scrcpy_manager, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        self.device_manager = device_manager
        self.scrcpy_manager = scrcpy_manager
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title Banner
        header = QLabel("TouchBridge Universal Dashboard")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #4F46E5;")
        subtitle = QLabel("Universal Android Keyboard & Mouse Gaming Bridge for Windows")
        subtitle.setStyleSheet("font-size: 13px; color: #6B7280;")
        layout.addWidget(header)
        layout.addWidget(subtitle)

        # Status Cards Grid
        grid = QGridLayout()
        grid.setSpacing(12)

        # 1. ADB Status Card
        self.adb_card = self._create_status_card("ADB Status", "Checking...", "#3B82F6")
        grid.addWidget(self.adb_card, 0, 0)

        # 2. Scrcpy Status Card
        self.scrcpy_card = self._create_status_card("scrcpy Streamer", "Checking...", "#10B981")
        grid.addWidget(self.scrcpy_card, 0, 1)

        # 3. Connected Device Card
        self.device_card = self._create_status_card("Device Connected", "None", "#8B5CF6")
        grid.addWidget(self.device_card, 1, 0)

        # 4. Display & Resolution Card
        self.display_card = self._create_status_card("Screen Calibration", "Not Connected", "#F59E0B")
        grid.addWidget(self.display_card, 1, 1)

        layout.addLayout(grid)

        # Quick Actions
        actions_box = QGroupBox("Quick Actions")
        actions_layout = QHBoxLayout(actions_box)

        self.btn_refresh = QPushButton("Refresh Status")
        self.btn_refresh.clicked.connect(self.refresh_status)
        actions_layout.addWidget(self.btn_refresh)

        self.btn_launch_scrcpy = QPushButton("Launch Game Stream (scrcpy)")
        self.btn_launch_scrcpy.setStyleSheet("background-color: #4F46E5; color: white; font-weight: bold; padding: 8px;")
        self.btn_launch_scrcpy.clicked.connect(self._launch_scrcpy)
        actions_layout.addWidget(self.btn_launch_scrcpy)

        layout.addWidget(actions_box)

        # Xiaomi / MIUI Warning Banner
        self.xiaomi_banner = QFrame()
        self.xiaomi_banner.setStyleSheet(
            "background-color: #FEF3C7; border: 1px solid #F59E0B; border-radius: 8px; padding: 12px;"
        )
        banner_layout = QVBoxLayout(self.xiaomi_banner)
        banner_title = QLabel("⚠️ Xiaomi / Redmi / POCO Security Alert")
        banner_title.setStyleSheet("font-weight: bold; color: #92400E; font-size: 14px;")
        banner_desc = QLabel(
            "MIUI/HyperOS requires 'USB debugging (Security settings)' to be turned ON to accept touch inputs.\n"
            "Go to Settings > Additional Settings > Developer Options > Enable 'USB debugging (Security settings)'."
        )
        banner_desc.setStyleSheet("color: #78350F; font-size: 12px;")
        banner_layout.addWidget(banner_title)
        banner_layout.addWidget(banner_desc)
        self.xiaomi_banner.setVisible(False)
        layout.addWidget(self.xiaomi_banner)

        layout.addStretch()
        self.refresh_status()

    def _create_status_card(self, title: str, initial_val: str, accent_color: str) -> QGroupBox:
        box = QGroupBox(title)
        box.setStyleSheet(f"QGroupBox {{ font-weight: bold; border: 1px solid #E5E7EB; border-radius: 6px; margin-top: 6px; padding-top: 10px; }} QGroupBox::title {{ subcontrol-origin: margin; left: 10px; color: {accent_color}; }}")
        box_layout = QVBoxLayout(box)
        val_label = QLabel(initial_val)
        val_label.setObjectName("value_label")
        val_label.setStyleSheet("font-size: 14px; font-weight: 500; color: #1F2937;")
        box_layout.addWidget(val_label)
        return box

    def refresh_status(self) -> None:
        """Poll ADB and scrcpy state."""
        if not HAS_QT:
            return

        # 1. Check ADB
        adb_installed = self.device_manager.is_adb_installed()
        adb_lbl = self.adb_card.findChild(QLabel, "value_label")
        if adb_installed:
            adb_lbl.setText(f"Active ({self.device_manager.get_adb_version()[:30]})")
            adb_lbl.setStyleSheet("color: #059669; font-weight: bold;")
        else:
            adb_lbl.setText("Not Installed / Not in PATH")
            adb_lbl.setStyleSheet("color: #DC2626; font-weight: bold;")

        # 2. Check Scrcpy
        scrcpy_installed = self.scrcpy_manager.is_installed()
        scrcpy_lbl = self.scrcpy_card.findChild(QLabel, "value_label")
        if self.scrcpy_manager.is_running():
            scrcpy_lbl.setText("Running (Active Mirroring)")
            scrcpy_lbl.setStyleSheet("color: #059669; font-weight: bold;")
        elif scrcpy_installed:
            scrcpy_lbl.setText("Ready to Launch")
            scrcpy_lbl.setStyleSheet("color: #2563EB;")
        else:
            scrcpy_lbl.setText("Not Found")
            scrcpy_lbl.setStyleSheet("color: #DC2626;")

        # 3. Check Devices
        devices = self.device_manager.list_devices()
        dev_lbl = self.device_card.findChild(QLabel, "value_label")
        disp_lbl = self.display_card.findChild(QLabel, "value_label")

        if devices:
            dev = devices[0]
            status_text = f"{dev.model} ({dev.manufacturer})\nSerial: {dev.serial} [{dev.state}]"
            dev_lbl.setText(status_text)
            disp_lbl.setText(f"{dev.screen_width} x {dev.screen_height} px ({dev.density_dpi} dpi)")

            if dev.requires_xiaomi_security_setup:
                self.xiaomi_banner.setVisible(True)
            else:
                self.xiaomi_banner.setVisible(False)
        else:
            dev_lbl.setText("No Android Devices Found\nConnect phone via USB with USB Debugging enabled")
            disp_lbl.setText("Reference: 2400 x 1080 px")
            self.xiaomi_banner.setVisible(False)

    def _launch_scrcpy(self) -> None:
        if not self.device_manager.selected_device:
            QMessageBox.warning(self, "No Device", "Please connect and authorize an Android phone first.")
            return

        serial = self.device_manager.selected_device.serial
        success = self.scrcpy_manager.launch(serial=serial, max_fps=120, bit_rate_mb=16)
        if success:
            QMessageBox.information(self, "scrcpy Started", "scrcpy game stream window launched successfully!")
        else:
            QMessageBox.critical(self, "Error", "Failed to launch scrcpy. Verify scrcpy installation.")
        self.refresh_status()
