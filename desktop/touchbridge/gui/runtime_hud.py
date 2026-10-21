"""TouchBridge Runtime Controls & Monitoring HUD."""

from __future__ import annotations
import logging

try:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QGroupBox, QProgressBar, QFrame
    )
    HAS_QT = True
except ImportError:
    HAS_QT = False
    QWidget = object  # type: ignore

logger = logging.getLogger("touchbridge.gui.runtime_hud")


class RuntimeHudView(QWidget if HAS_QT else object):
    """Runtime control bar and input telemetry."""

    def __init__(self, pipeline, failsafe, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        self.pipeline = pipeline
        self.failsafe = failsafe
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("Runtime Mapping Controls & Live Telemetry")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F2937;")
        layout.addWidget(title)

        # Control Panel Box
        ctrl_box = QGroupBox("Mapping State")
        ctrl_layout = QHBoxLayout(ctrl_box)
        ctrl_layout.setSpacing(12)

        self.btn_toggle = QPushButton("▶ START MAPPING")
        self.btn_toggle.setStyleSheet("background-color: #10B981; color: white; font-size: 16px; font-weight: bold; padding: 14px;")
        self.btn_toggle.clicked.connect(self._toggle_mapping)
        ctrl_layout.addWidget(self.btn_toggle, stretch=2)

        self.btn_emergency = QPushButton("🛑 EMERGENCY STOP (F12)")
        self.btn_emergency.setStyleSheet("background-color: #EF4444; color: white; font-size: 14px; font-weight: bold; padding: 14px;")
        self.btn_emergency.clicked.connect(self._emergency_stop)
        ctrl_layout.addWidget(self.btn_emergency, stretch=1)

        layout.addWidget(ctrl_box)

        # Telemetry Box
        tele_box = QGroupBox("Live Input Telemetry")
        tele_layout = QVBoxLayout(tele_box)

        row1 = QHBoxLayout()
        self.lbl_status = QLabel("Status: Idle (Mapping Stopped)")
        self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #6B7280;")
        row1.addWidget(self.lbl_status)

        self.lbl_latency = QLabel("Injection Latency: 0.0 ms")
        self.lbl_latency.setStyleSheet("font-size: 14px; color: #059669; font-weight: bold;")
        row1.addWidget(self.lbl_latency)
        tele_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.lbl_active_contacts = QLabel("Active Touch Contacts: 0 / 10")
        self.lbl_active_contacts.setStyleSheet("font-size: 13px; color: #374151;")
        row2.addWidget(self.lbl_active_contacts)

        self.lbl_held_keys = QLabel("Held Keys: None")
        self.lbl_held_keys.setStyleSheet("font-size: 13px; color: #374151;")
        row2.addWidget(self.lbl_held_keys)
        tele_layout.addLayout(row2)

        layout.addWidget(tele_box)

        # Safety Guidelines
        guide_box = QGroupBox("Failsafe Protections")
        guide_layout = QVBoxLayout(guide_box)
        info = QLabel(
            "• <b>Emergency Release:</b> Press <b>F12</b> or <b>Escape</b> anytime to instantly release all active touches.<br>"
            "• <b>Focus Guard:</b> Switching away from the game window automatically releases all simulated touches.<br>"
            "• <b>Zero Trap:</b> Your mouse and keyboard are never trapped when mapping is stopped or during emergency release."
        )
        info.setStyleSheet("font-size: 13px; color: #4B5563;")
        guide_layout.addWidget(info)
        layout.addWidget(guide_box)

        layout.addStretch()

        # Polling Timer for Telemetry
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_telemetry)
        self.timer.start(100)  # 10Hz UI refresh

    def _toggle_mapping(self) -> None:
        if not self.pipeline.is_running:
            self.pipeline.start()
            self.btn_toggle.setText("⏸ STOP MAPPING")
            self.btn_toggle.setStyleSheet("background-color: #EF4444; color: white; font-size: 16px; font-weight: bold; padding: 14px;")
            self.lbl_status.setText("Status: ACTIVE (Routing Keys & Mouse to Phone)")
            self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #059669;")
        else:
            self.pipeline.stop()
            self.btn_toggle.setText("▶ START MAPPING")
            self.btn_toggle.setStyleSheet("background-color: #10B981; color: white; font-size: 16px; font-weight: bold; padding: 14px;")
            self.lbl_status.setText("Status: Idle (Mapping Stopped)")
            self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #6B7280;")

    def _emergency_stop(self) -> None:
        self.failsafe.trigger_emergency_release()
        if self.pipeline.is_running:
            self._toggle_mapping()

    def _update_telemetry(self) -> None:
        if not HAS_QT:
            return
        active_count = len(self.pipeline.transport.active_pointers)
        self.lbl_active_contacts.setText(f"Active Touch Contacts: {active_count} / 10")
        lat = self.pipeline.transport.get_latency_ms()
        self.lbl_latency.setText(f"Injection Latency: {lat:.1f} ms")

        held = list(self.pipeline.held_keys) + list(self.pipeline.held_mouse_buttons)
        if held:
            self.lbl_held_keys.setText(f"Held Keys: {', '.join(held).upper()}")
        else:
            self.lbl_held_keys.setText("Held Keys: None")
