"""TouchBridge Device Manager View."""

from __future__ import annotations
import logging

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QListWidget, QListWidgetItem, QGroupBox, QTextEdit, QMessageBox
    )
    HAS_QT = True
except ImportError:
    HAS_QT = False
    QWidget = object  # type: ignore

logger = logging.getLogger("touchbridge.gui.device_view")


class DeviceView(QWidget if HAS_QT else object):
    """View to select connected phone, view ADB authorization, and troubleshoot connection."""

    def __init__(self, device_manager, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        self.device_manager = device_manager
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Connected Devices & USB Debugging")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F2937;")
        layout.addWidget(title)

        # Device List Box
        list_box = QGroupBox("Detected ADB Devices")
        list_layout = QVBoxLayout(list_box)

        self.device_list = QListWidget()
        self.device_list.setStyleSheet("font-size: 13px; padding: 4px;")
        self.device_list.itemClicked.connect(self._on_device_selected)
        list_layout.addWidget(self.device_list)

        btn_row = QHBoxLayout()
        self.btn_refresh = QPushButton("Scan for Devices")
        self.btn_refresh.clicked.connect(self.scan_devices)
        btn_row.addWidget(self.btn_refresh)

        self.btn_forward = QPushButton("Setup Companion Port Forward (28200)")
        self.btn_forward.clicked.connect(self._setup_forward)
        btn_row.addWidget(self.btn_forward)

        list_layout.addLayout(btn_row)
        layout.addWidget(list_box)

        # Troubleshooting / Guide Box
        guide_box = QGroupBox("USB Debugging & Device Setup Guide")
        guide_layout = QVBoxLayout(guide_box)

        guide_text = (
            "<h3>How to Connect Your Android Phone:</h3>"
            "<ol>"
            "<li><b>Enable Developer Options:</b> Open phone Settings > About Phone > Tap <i>Build Number</i> 7 times.</li>"
            "<li><b>Enable USB Debugging:</b> Settings > System / Additional Settings > Developer Options > Toggle <b>USB Debugging</b> ON.</li>"
            "<li><b>Authorize Windows PC:</b> Connect phone via USB. A prompt will appear: <i>'Allow USB debugging?'</i> Check <i>'Always allow from this computer'</i> and tap <b>Allow</b>.</li>"
            "<li><b>For Xiaomi / Redmi / POCO Phones (CRITICAL):</b><br>"
            "Xiaomi phones require enabling <b>'USB debugging (Security settings)'</b> located below normal USB debugging. "
            "This permits input simulation. You will need a SIM card and Mi Account to toggle this setting once.</li>"
            "</ol>"
        )
        self.guide_view = QTextEdit()
        self.guide_view.setReadOnly(True)
        self.guide_view.setHtml(guide_text)
        guide_layout.addWidget(self.guide_view)

        layout.addWidget(guide_box)
        self.scan_devices()

    def scan_devices(self) -> None:
        """Scan and populate list."""
        if not HAS_QT:
            return
        self.device_list.clear()
        devices = self.device_manager.list_devices()
        if not devices:
            item = QListWidgetItem("No devices found. Ensure phone is connected with USB Debugging enabled.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.device_list.addItem(item)
            return

        for dev in devices:
            auth_status = "✅ Authorized" if dev.is_authorized else f"❌ {dev.state.upper()} (Check phone screen for prompt)"
            xiaomi_warn = " [Xiaomi: Security Settings Required]" if dev.requires_xiaomi_security_setup else ""
            txt = f"{dev.model} ({dev.manufacturer}) — Serial: {dev.serial} — {auth_status}{xiaomi_warn}"
            item = QListWidgetItem(txt)
            item.setData(Qt.ItemDataRole.UserRole, dev.serial)
            self.device_list.addItem(item)

    def _on_device_selected(self, item: QListWidgetItem) -> None:
        serial = item.data(Qt.ItemDataRole.UserRole)
        if not serial:
            return
        devices = self.device_manager.list_devices()
        selected = next((d for d in devices if d.serial == serial), None)
        if selected:
            self.device_manager.selected_device = selected
            logger.info("Selected active device: %s", selected.serial)

    def _setup_forward(self) -> None:
        if not self.device_manager.selected_device:
            QMessageBox.warning(self, "No Device", "Please select an authorized Android device first.")
            return

        success = self.device_manager.setup_port_forward(28200, 28200)
        if success:
            QMessageBox.information(self, "Port Forward Active", "Port tcp:28200 forwarded successfully to phone companion app!")
        else:
            QMessageBox.critical(self, "Port Forward Error", "Failed to setup ADB port forwarding.")
