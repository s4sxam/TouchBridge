"""TouchBridge Profile Manager View."""

from __future__ import annotations
import logging

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QListWidget, QListWidgetItem, QGroupBox, QLineEdit, QComboBox,
        QSpinBox, QFileDialog, QMessageBox, QInputDialog, QDialog, QGridLayout
    )
    HAS_QT = True
except ImportError:
    HAS_QT = False
    QWidget = object  # type: ignore

from ..core.models import Profile, ScreenOrientation

logger = logging.getLogger("touchbridge.gui.profile_view")


class ProfileView(QWidget if HAS_QT else object):
    """View to manage, import, export, and configure profiles."""

    profile_changed = Signal(str) if HAS_QT else None

    def __init__(self, profile_manager, device_manager=None, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.device_manager = device_manager
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Left Column: Profile List
        left_box = QGroupBox("Saved Profiles")
        left_layout = QVBoxLayout(left_box)

        # 1-Click Quick Add Game Button
        self.btn_quick_add = QPushButton("⚡ 1-Click Quick Add Game")
        self.btn_quick_add.setStyleSheet(
            "background-color: #10B981; color: white; font-weight: bold; font-size: 13px; padding: 10px; border-radius: 6px;"
        )
        self.btn_quick_add.clicked.connect(self._open_quick_add_dialog)
        left_layout.addWidget(self.btn_quick_add)

        self.profile_list = QListWidget()
        self.profile_list.itemClicked.connect(self._on_profile_clicked)
        left_layout.addWidget(self.profile_list)

        btn_grid = QHBoxLayout()
        self.btn_new = QPushButton("New Profile")
        self.btn_new.clicked.connect(self._create_new_profile)
        btn_grid.addWidget(self.btn_new)

        self.btn_dup = QPushButton("Duplicate")
        self.btn_dup.clicked.connect(self._duplicate_profile)
        btn_grid.addWidget(self.btn_dup)

        self.btn_del = QPushButton("Delete")
        self.btn_del.clicked.connect(self._delete_profile)
        btn_grid.addWidget(self.btn_del)

        left_layout.addLayout(btn_grid)

        io_row = QHBoxLayout()
        self.btn_import = QPushButton("Import JSON")
        self.btn_import.clicked.connect(self._import_profile)
        io_row.addWidget(self.btn_import)

        self.btn_export = QPushButton("Export JSON")
        self.btn_export.clicked.connect(self._export_profile)
        io_row.addWidget(self.btn_export)

        left_layout.addLayout(io_row)
        layout.addWidget(left_box, stretch=1)

        # Right Column: Profile Configuration
        right_box = QGroupBox("Profile Settings")
        right_layout = QVBoxLayout(right_box)
        right_layout.setSpacing(12)

        # Name
        right_layout.addWidget(QLabel("Profile Name:"))
        self.txt_name = QLineEdit()
        right_layout.addWidget(self.txt_name)

        # Package Name
        right_layout.addWidget(QLabel("Target Package Name (Optional):"))
        pkg_row = QHBoxLayout()
        self.txt_package = QLineEdit()
        self.txt_package.setPlaceholderText("e.g. com.dts.freefireth (leave blank for generic)")
        pkg_row.addWidget(self.txt_package)

        self.btn_detect_pkg = QPushButton("🔍 Detect Game on Phone")
        self.btn_detect_pkg.setToolTip("Reads current foreground game running on phone screen")
        self.btn_detect_pkg.clicked.connect(self._detect_running_game)
        pkg_row.addWidget(self.btn_detect_pkg)
        right_layout.addLayout(pkg_row)

        # Orientation
        right_layout.addWidget(QLabel("Screen Orientation:"))
        self.cmb_orientation = QComboBox()
        self.cmb_orientation.addItems(["landscape", "portrait"])
        right_layout.addWidget(self.cmb_orientation)

        # Reference Resolution
        res_layout = QHBoxLayout()
        res_layout.addWidget(QLabel("Width:"))
        self.spin_width = QSpinBox()
        self.spin_width.setRange(480, 7680)
        self.spin_width.setValue(2400)
        res_layout.addWidget(self.spin_width)

        res_layout.addWidget(QLabel("Height:"))
        self.spin_height = QSpinBox()
        self.spin_height.setRange(320, 4320)
        self.spin_height.setValue(1080)
        res_layout.addWidget(self.spin_height)
        right_layout.addLayout(res_layout)

        # Save Button
        self.btn_save = QPushButton("Save Profile Changes")
        self.btn_save.setStyleSheet("background-color: #4F46E5; color: white; font-weight: bold; padding: 10px;")
        self.btn_save.clicked.connect(self._save_active_profile)
        right_layout.addWidget(self.btn_save)

        right_layout.addStretch()
        layout.addWidget(right_box, stretch=2)

        self.populate_profiles()

    def populate_profiles(self) -> None:
        """Populate profile list widget."""
        if not HAS_QT:
            return
        self.profile_list.clear()
        for pid, prof in self.profile_manager.profiles.items():
            active_marker = " ★ (Active)" if pid == self.profile_manager.active_profile_id else ""
            item = QListWidgetItem(f"{prof.name}{active_marker}")
            item.setData(Qt.ItemDataRole.UserRole, pid)
            self.profile_list.addItem(item)
            if pid == self.profile_manager.active_profile_id:
                self.profile_list.setCurrentItem(item)

        self._load_active_into_form()

    def _load_active_into_form(self) -> None:
        prof = self.profile_manager.get_active_profile()
        if not prof:
            return
        self.txt_name.setText(prof.name)
        self.txt_package.setText(prof.package_name or "")
        self.cmb_orientation.setCurrentText(prof.orientation.value)
        self.spin_width.setValue(prof.ref_width)
        self.spin_height.setValue(prof.ref_height)

    def _on_profile_clicked(self, item: QListWidgetItem) -> None:
        pid = item.data(Qt.ItemDataRole.UserRole)
        if pid:
            self.profile_manager.set_active_profile(pid)
            self.populate_profiles()
            if self.profile_changed:
                self.profile_changed.emit(pid)

    def _save_active_profile(self) -> None:
        prof = self.profile_manager.get_active_profile()
        if not prof:
            return
        prof.name = self.txt_name.text().strip() or "Untitled"
        prof.package_name = self.txt_package.text().strip() or None
        prof.orientation = ScreenOrientation(self.cmb_orientation.currentText())
        prof.ref_width = self.spin_width.value()
        prof.ref_height = self.spin_height.value()

        self.profile_manager.save_profile(prof)
        QMessageBox.information(self, "Profile Saved", f"Profile '{prof.name}' saved successfully!")
        self.populate_profiles()

    def _detect_running_game(self) -> None:
        """Query foreground app running on Android device."""
        if not self.device_manager:
            QMessageBox.information(self, "Device Manager", "Device manager not available.")
            return
        pkg = self.device_manager.get_foreground_package()
        if pkg:
            self.txt_package.setText(pkg)
            curr_name = self.txt_name.text().strip()
            if not curr_name or "Untitled" in curr_name or "Generic" in curr_name:
                suggested = pkg.split(".")[-1].replace("_", " ").title()
                self.txt_name.setText(suggested)
            QMessageBox.information(self, "Game Detected", f"Detected running game package:\n{pkg}")
        else:
            QMessageBox.warning(
                self, "Not Detected",
                "Could not detect running game.\nMake sure your game is open on the phone screen and USB debugging is connected."
            )

    def _create_new_profile(self) -> None:
        import uuid
        name, ok = QInputDialog.getText(self, "New Game Profile", "Enter game name (e.g. Genshin Impact, COD Mobile):")
        if not ok or not name.strip():
            return

        templates = [
            "Shooter / FPS (WASD + Mouse Aim + Fire)",
            "MOBA (WASD + Skills Q/E/R)",
            "Arcade Racing (Steer A/D + Nitro)",
            "Blank Canvas"
        ]
        template, tok = QInputDialog.getItem(
            self, "Select Control Template", "Choose starting control template for this game:",
            templates, 0, False
        )
        if not tok:
            return

        if "Shooter" in template:
            base = self.profile_manager._build_generic_fps_profile()
        elif "MOBA" in template:
            base = self.profile_manager._build_generic_moba_profile()
        elif "Racing" in template:
            base = self.profile_manager._build_racing_profile()
        else:
            base = Profile()

        base.id = str(uuid.uuid4())
        base.name = name.strip()
        self.profile_manager.save_profile(base)
        self.profile_manager.set_active_profile(base.id)
        self.populate_profiles()

    def _duplicate_profile(self) -> None:
        prof = self.profile_manager.get_active_profile()
        if not prof:
            return
        dup = self.profile_manager.duplicate_profile(prof.id)
        if dup:
            self.profile_manager.set_active_profile(dup.id)
            self.populate_profiles()

    def _delete_profile(self) -> None:
        prof = self.profile_manager.get_active_profile()
        if not prof:
            return
        if len(self.profile_manager.profiles) <= 1:
            QMessageBox.warning(self, "Cannot Delete", "You must keep at least one profile.")
            return

        confirm = QMessageBox.question(
            self, "Confirm Delete", f"Delete profile '{prof.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.profile_manager.delete_profile(prof.id)
            self.populate_profiles()

    def _export_profile(self) -> None:
        prof = self.profile_manager.get_active_profile()
        if not prof:
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Profile JSON", f"{prof.name.lower()}.json", "JSON Files (*.json)")
        if file_path:
            json_str = self.profile_manager.export_profile_json(prof.id)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(json_str)
            QMessageBox.information(self, "Exported", "Profile exported successfully!")

    def _import_profile(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Profile JSON", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                imported = self.profile_manager.import_profile_json(content)
                self.profile_manager.set_active_profile(imported.id)
                self.populate_profiles()
                QMessageBox.information(self, "Imported", f"Successfully imported '{imported.name}'!")
            except Exception as e:
    def _open_quick_add_dialog(self) -> None:
        """Open the 1-Click Simple Game Wizard."""
        if not HAS_QT:
            return
        dialog = QuickAddGameDialog(self.profile_manager, self.device_manager, self)
        if dialog.exec():
            self.populate_profiles()
            if self.profile_manager.active_profile_id and self.profile_changed:
                self.profile_changed.emit(self.profile_manager.active_profile_id)


class QuickAddGameDialog(QDialog if HAS_QT else object):
    """1-Click Simple Game Addition Dialog."""

    def __init__(self, profile_manager, device_manager=None, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.device_manager = device_manager
        self.setWindowTitle("⚡ 1-Click Add Game")
        self.setMinimumWidth(520)
        self._init_ui()

    def _init_ui(self) -> None:
        import uuid
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Add Game Keymap in 1-Click")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4F46E5;")
        subtitle = QLabel("Open the game on your phone and click Auto-Detect, or select a popular preset:")
        subtitle.setStyleSheet("font-size: 12px; color: #6B7280;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Big Auto Detect Button
        btn_auto = QPushButton("⚡ Auto-Detect Game Currently Open on Phone")
        btn_auto.setStyleSheet(
            "background-color: #059669; color: white; font-size: 14px; font-weight: bold; padding: 12px; border-radius: 8px;"
        )
        btn_auto.clicked.connect(self._auto_detect)
        layout.addWidget(btn_auto)

        # Preset Games Grid
        preset_box = QGroupBox("Popular Game Presets (Instant Setup)")
        grid = QGridLayout(preset_box)
        grid.setSpacing(8)

        games = [
            ("🎯 Free Fire / MAX", "com.dts.freefireth", "fps"),
            ("🪖 PUBG Mobile / BGMI", "com.tencent.ig", "fps"),
            ("🎖️ Call of Duty: Mobile", "com.activision.callofduty.shooter", "fps"),
            ("⚔️ Genshin Impact", "com.miHoYo.GenshinImpact", "fps"),
            ("⭐ Brawl Stars", "com.supercell.brawlstars", "moba"),
            ("🛡️ Mobile Legends", "com.mobile.legends", "moba"),
            ("🏎️ Asphalt 9 / Legends", "com.gameloft.android.ANMP.GloftA9HM", "racing"),
            ("🕹️ Roblox Mobile", "com.roblox.client", "fps"),
            ("🧱 Minecraft Bedrock", "com.mojang.minecraftpe", "fps"),
            ("🔫 Custom Shooter", None, "fps"),
            ("🧙 Custom MOBA", None, "moba"),
            ("🏎️ Custom Racing", None, "racing"),
        ]

        for i, (label, pkg, genre) in enumerate(games):
            btn = QPushButton(label)
            btn.setStyleSheet(
                "QPushButton { background-color: #F3F4F6; color: #1F2937; font-weight: bold; padding: 8px; border-radius: 6px; border: 1px solid #D1D5DB; } "
                "QPushButton:hover { background-color: #4F46E5; color: white; }"
            )
            # Closure for click
            btn.clicked.connect(lambda checked=False, l=label, p=pkg, g=genre: self._add_game_preset(l, p, g))
            grid.addWidget(btn, i // 3, i % 3)

        layout.addWidget(preset_box)

    def _auto_detect(self) -> None:
        import uuid
        if not self.device_manager:
            QMessageBox.warning(self, "Device Manager", "ADB Device manager not connected.")
            return

        game_info = self.device_manager.auto_detect_game()
        if not game_info:
            QMessageBox.warning(
                self, "No Game Running",
                "Could not detect a running game.\nMake sure your game is open on your phone screen with USB debugging enabled!"
            )
            return

        game_name, pkg, genre = game_info
        self._add_game_preset(game_name, pkg, genre)

    def _add_game_preset(self, name_clean: str, pkg: str | None, genre: str) -> None:
        import uuid
        # Strip emojis
        clean_title = "".join(c for c in name_clean if c.isalnum() or c in (" ", "-", "/", ":")).strip()
        if genre == "moba":
            prof = self.profile_manager._build_generic_moba_profile()
        elif genre == "racing":
            prof = self.profile_manager._build_racing_profile()
        else:
            prof = self.profile_manager._build_generic_fps_profile()

        prof.id = str(uuid.uuid4())
        prof.name = clean_title
        prof.package_name = pkg
        self.profile_manager.save_profile(prof)
        self.profile_manager.set_active_profile(prof.id)

        QMessageBox.information(
            self, "Game Added!",
            f"✅ '{clean_title}' keymap profile created and activated!\n\n"
            f"Controls are pre-mapped for keyboard and mouse.\n"
            f"You can fine-tune them anytime in the Keymap Editor."
        )
        self.accept()

