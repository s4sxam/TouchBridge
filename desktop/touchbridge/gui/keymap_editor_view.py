"""TouchBridge Live Keymap Editor View.

Provides an interactive visual canvas allowing users to drag and place virtual controls,
bind keyboard keys and mouse buttons, and tune sensitivity/radius parameters.
"""

from __future__ import annotations
import logging
from typing import Optional

try:
    from PySide6.QtCore import Qt, QRectF, QPointF
    from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QKeyEvent
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QGroupBox, QComboBox, QSlider, QLineEdit, QCheckBox, QMessageBox, QSplitter
    )
    HAS_QT = True
except ImportError:
    HAS_QT = False
    QWidget = object  # type: ignore

from ..core.models import Binding, ControlType, Profile

logger = logging.getLogger("touchbridge.gui.keymap_editor")


class KeymapCanvas(QWidget if HAS_QT else object):
    """Interactive screen viewport canvas where virtual controls are rendered and dragged."""

    def __init__(self, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        self.profile: Optional[Profile] = None
        self.selected_binding: Optional[Binding] = None
        self.dragging_binding: Optional[Binding] = None
        self.drag_offset: QPointF = QPointF(0, 0)
        self.on_binding_selected = None
        self.setMouseTracking(True)
        self.setMinimumSize(640, 360)

    def set_profile(self, profile: Profile) -> None:
        self.profile = profile
        self.selected_binding = None
        self.update()

    def paintEvent(self, event) -> None:
        if not HAS_QT or not self.profile:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Draw phone screen background (dark gaming display)
        painter.fillRect(0, 0, w, h, QColor(24, 24, 37))

        # Draw grid
        painter.setPen(QPen(QColor(40, 40, 60), 1, Qt.PenStyle.DashLine))
        for x in range(0, w, 50):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, 50):
            painter.drawLine(0, y, w, y)

        # Center line
        painter.setPen(QPen(QColor(60, 60, 90), 1))
        painter.drawLine(w // 2, 0, w // 2, h)

        # Draw bindings
        for b in self.profile.bindings:
            self._draw_binding(painter, b, w, h)

        # Selection indicator text
        painter.setPen(QColor(160, 160, 180))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(10, 20, f"Profile: {self.profile.name} ({self.profile.orientation.value.upper()}) | Drag to reposition")

    def _draw_binding(self, painter: QPainter, b: Binding, w: int, h: int) -> None:
        cx = b.norm_x * w
        cy = b.norm_y * h
        is_sel = (b == self.selected_binding)

        if b.control_type == ControlType.JOYSTICK:
            # Draw Joystick Outer Circle & WASD cross
            radius = b.radius * h
            painter.setBrush(QBrush(QColor(59, 130, 246, 40 if not is_sel else 80)))
            painter.setPen(QPen(QColor(59, 130, 246, 220), 2 if not is_sel else 3))
            painter.drawEllipse(QPointF(cx, cy), radius, radius)

            # Center knob
            painter.setBrush(QBrush(QColor(59, 130, 246, 200)))
            painter.drawEllipse(QPointF(cx, cy), 16, 16)

            # WASD Labels
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.drawText(QRectF(cx - 15, cy - radius - 20, 30, 20), Qt.AlignmentFlag.AlignCenter, b.up_key.upper())
            painter.drawText(QRectF(cx - 15, cy + radius, 30, 20), Qt.AlignmentFlag.AlignCenter, b.down_key.upper())
            painter.drawText(QRectF(cx - radius - 25, cy - 10, 20, 20), Qt.AlignmentFlag.AlignCenter, b.left_key.upper())
            painter.drawText(QRectF(cx + radius + 5, cy - 10, 20, 20), Qt.AlignmentFlag.AlignCenter, b.right_key.upper())

        elif b.control_type == ControlType.MOUSE_LOOK:
            # Draw Aim Zone Bounding Box
            zw = b.zone_width * w
            zh = b.zone_height * h
            rect = QRectF(cx - zw / 2, cy - zh / 2, zw, zh)

            painter.setBrush(QBrush(QColor(16, 185, 129, 30 if not is_sel else 70)))
            painter.setPen(QPen(QColor(16, 185, 129, 200), 2 if not is_sel else 3, Qt.PenStyle.DashLine))
            painter.drawRect(rect)

            painter.setPen(QColor(16, 185, 129))
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"🖱️ {b.name}\n(Sens: {b.sensitivity_x:.1f})")

        else:
            # Standard Tap / Hold / Toggle Button
            radius = max(18.0, b.radius * h)
            fill_color = QColor(239, 68, 68, 120 if not is_sel else 200) if b.mouse_button else QColor(99, 102, 241, 120 if not is_sel else 200)
            border_color = QColor(255, 255, 255, 240) if is_sel else QColor(255, 255, 255, 140)

            painter.setBrush(QBrush(fill_color))
            painter.setPen(QPen(border_color, 2 if not is_sel else 3))
            painter.drawEllipse(QPointF(cx, cy), radius, radius)

            # Key label
            key_label = (b.mouse_button or b.key or "?").upper()
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            painter.drawText(QRectF(cx - radius, cy - radius, radius * 2, radius * 2), Qt.AlignmentFlag.AlignCenter, key_label)

    def mousePressEvent(self, event) -> None:
        if not HAS_QT or not self.profile:
            return
        w = self.width()
        h = self.height()
        pos = event.position()

        # Find clicked binding (reverse order for top z-index)
        clicked = None
        for b in reversed(self.profile.bindings):
            cx = b.norm_x * w
            cy = b.norm_y * h
            r = max(24.0, b.radius * h)
            dist_sq = (pos.x() - cx) ** 2 + (pos.y() - cy) ** 2
            if dist_sq <= r ** 2:
                clicked = b
                break
            elif b.control_type == ControlType.MOUSE_LOOK:
                zw = b.zone_width * w
                zh = b.zone_height * h
                if (cx - zw / 2 <= pos.x() <= cx + zw / 2) and (cy - zh / 2 <= pos.y() <= cy + zh / 2):
                    clicked = b
                    break

        self.selected_binding = clicked
        self.dragging_binding = clicked
        if clicked:
            self.drag_offset = QPointF(pos.x() - clicked.norm_x * w, pos.y() - clicked.norm_y * h)
            if self.on_binding_selected:
                self.on_binding_selected(clicked)

        self.update()

    def mouseMoveEvent(self, event) -> None:
        if not HAS_QT or not self.dragging_binding:
            return
        w = self.width()
        h = self.height()
        pos = event.position()

        new_x = (pos.x() - self.drag_offset.x()) / w
        new_y = (pos.y() - self.drag_offset.y()) / h

        self.dragging_binding.norm_x = max(0.02, min(0.98, new_x))
        self.dragging_binding.norm_y = max(0.02, min(0.98, new_y))
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        self.dragging_binding = None


class KeymapEditorView(QWidget if HAS_QT else object):
    """Full Keymap Editor view with canvas and properties drawer."""

    def __init__(self, profile_manager, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.current_binding: Optional[Binding] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Interactive Canvas
        self.canvas = KeymapCanvas()
        self.canvas.on_binding_selected = self._on_binding_selected
        splitter.addWidget(self.canvas)

        # Right: Property Inspector
        prop_box = QGroupBox("Control Properties")
        prop_layout = QVBoxLayout(prop_box)
        prop_layout.setSpacing(10)

        # Add Controls Toolbar
        add_box = QGroupBox("Add Virtual Control")
        add_layout = QHBoxLayout(add_box)
        self.btn_add_btn = QPushButton("+ Button")
        self.btn_add_btn.clicked.connect(self._add_button)
        add_layout.addWidget(self.btn_add_btn)

        self.btn_add_joy = QPushButton("+ Joystick")
        self.btn_add_joy.clicked.connect(self._add_joystick)
        add_layout.addWidget(self.btn_add_joy)

        self.btn_add_look = QPushButton("+ Mouse Look")
        self.btn_add_look.clicked.connect(self._add_mouse_look)
        add_layout.addWidget(self.btn_add_look)
        prop_layout.addWidget(add_box)

        # Selected Control Form
        self.lbl_selected = QLabel("Select a control on canvas to edit")
        self.lbl_selected.setStyleSheet("font-weight: bold; color: #4F46E5;")
        prop_layout.addWidget(self.lbl_selected)

        prop_layout.addWidget(QLabel("Label / Name:"))
        self.txt_bname = QLineEdit()
        self.txt_bname.textChanged.connect(self._update_binding_name)
        prop_layout.addWidget(self.txt_bname)

        prop_layout.addWidget(QLabel("Physical Key Binding:"))
        self.txt_key = QLineEdit()
        self.txt_key.setPlaceholderText("Press physical key (e.g. space, r, f)")
        self.txt_key.textChanged.connect(self._update_binding_key)
        prop_layout.addWidget(self.txt_key)

        prop_layout.addWidget(QLabel("Mouse Button Binding:"))
        self.cmb_mouse = QComboBox()
        self.cmb_mouse.addItems(["None", "left", "right", "middle"])
        self.cmb_mouse.currentTextChanged.connect(self._update_binding_mouse)
        prop_layout.addWidget(self.cmb_mouse)

        prop_layout.addWidget(QLabel("Size / Radius:"))
        self.slider_radius = QSlider(Qt.Orientation.Horizontal)
        self.slider_radius.setRange(20, 200)
        self.slider_radius.valueChanged.connect(self._update_binding_radius)
        prop_layout.addWidget(self.slider_radius)

        self.chk_toggle = QCheckBox("Toggle Mode (Tap to toggle state)")
        self.chk_toggle.toggled.connect(self._update_binding_toggle)
        prop_layout.addWidget(self.chk_toggle)

        self.btn_delete = QPushButton("Remove Selected Control")
        self.btn_delete.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold;")
        self.btn_delete.clicked.connect(self._delete_selected_binding)
        prop_layout.addWidget(self.btn_delete)

        prop_layout.addStretch()
        splitter.addWidget(prop_box)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)
        self.reload_profile()

    def reload_profile(self) -> None:
        prof = self.profile_manager.get_active_profile()
        if prof:
            self.canvas.set_profile(prof)

    def _on_binding_selected(self, b: Binding) -> None:
        self.current_binding = b
        self.lbl_selected.setText(f"Editing: {b.name} ({b.control_type.value.upper()})")
        self.txt_bname.setText(b.name)
        self.txt_key.setText(b.key or "")
        self.cmb_mouse.setCurrentText(b.mouse_button or "None")
        self.slider_radius.setValue(int(b.radius * 1000))
        self.chk_toggle.setChecked(b.toggle)

    def _update_binding_name(self, text: str) -> None:
        if self.current_binding:
            self.current_binding.name = text
            self.canvas.update()

    def _update_binding_key(self, text: str) -> None:
        if self.current_binding:
            self.current_binding.key = text.lower().strip() or None
            self.canvas.update()

    def _update_binding_mouse(self, text: str) -> None:
        if self.current_binding:
            self.current_binding.mouse_button = None if text == "None" else text.lower()
            self.canvas.update()

    def _update_binding_radius(self, val: int) -> None:
        if self.current_binding:
            self.current_binding.radius = val / 1000.0
            self.canvas.update()

    def _update_binding_toggle(self, checked: bool) -> None:
        if self.current_binding:
            self.current_binding.toggle = checked

    def _add_button(self) -> None:
        prof = self.profile_manager.get_active_profile()
        if not prof:
            return
        b = Binding(name="New Action", control_type=ControlType.TAP, norm_x=0.5, norm_y=0.5, radius=0.05, key="e")
        prof.bindings.append(b)
        self.profile_manager.save_profile(prof)
        self.canvas.set_profile(prof)

    def _add_joystick(self) -> None:
        prof = self.profile_manager.get_active_profile()
        if not prof:
            return
        b = Binding(name="Movement", control_type=ControlType.JOYSTICK, norm_x=0.2, norm_y=0.7, radius=0.12)
        prof.bindings.append(b)
        self.profile_manager.save_profile(prof)
        self.canvas.set_profile(prof)

    def _add_mouse_look(self) -> None:
        prof = self.profile_manager.get_active_profile()
        if not prof:
            return
        b = Binding(name="Mouse Aim", control_type=ControlType.MOUSE_LOOK, norm_x=0.75, norm_y=0.5, zone_width=0.4, zone_height=0.6)
        prof.bindings.append(b)
        self.profile_manager.save_profile(prof)
        self.canvas.set_profile(prof)

    def _delete_selected_binding(self) -> None:
        prof = self.profile_manager.get_active_profile()
        if not prof or not self.current_binding:
            return
        prof.bindings = [b for b in prof.bindings if b.id != self.current_binding.id]
        self.current_binding = None
        self.profile_manager.save_profile(prof)
        self.canvas.set_profile(prof)
