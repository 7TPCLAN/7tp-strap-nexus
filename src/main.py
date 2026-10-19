import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import psutil
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QMainWindow, QMessageBox, QPlainTextEdit,
    QProgressBar, QPushButton, QStackedWidget, QVBoxLayout, QWidget
)

import nexus_services as services

APP_NAME = "7TP Nexus Strap"


def button(text, callback, primary=False):
    item = QPushButton(text)
    item.setObjectName("primaryButton" if primary else "actionButton")
    item.setCursor(Qt.CursorShape.PointingHandCursor)
    item.clicked.connect(callback)
    return item


def panel():
    item = QFrame()
    item.setObjectName("card")
    return item


class NexusWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        services.ensure_dirs()
        self.capture_process = None
        self.capture_log = None
        self.nav_buttons = []
        self.setWindowTitle(APP_NAME)
        self.resize(1160, 760)
        self.setMinimumSize(900, 620)

        root = QWidget()
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(238)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 24, 18, 18)
        side.setSpacing(8)
        logo = QLabel("7TP")
        logo.setObjectName("logo")
        brand = QLabel("NEXUS STRAP")
        brand.setObjectName("brand")
        tagline = QLabel("PLAY. CREATE. OPTIMIZE.")
        tagline.setObjectName("tagline")
        side.addWidget(logo)
        side.addWidget(brand)
        side.addWidget(tagline)
        side.addSpacing(22)

        self.pages = QStackedWidget()
        self.page_specs = [
            ("Dashboard", "Your gaming toolkit, in one place."),
            ("Nexus Boost", "Read-only system monitoring."),
            ("Nexus Capture", "Record your Windows desktop with FFmpeg."),
            ("Nexus Packs", "Import and organize local texture assets."),
            ("Nexus Skies", "Create local sky presets from images."),
            ("FastFlag Studio", "Edit and export a JSON settings file."),
            ("Nexus Profiles", "Save and reload your Nexus configuration."),
        ]
        for index, (name, _) in enumerate(self.page_specs):
            nav = QPushButton(("⌂   " if index == 0 else "✦   ") + name)
            nav.setObjectName("navButton")
            nav.setCheckable(True)
            nav.setCursor(Qt.CursorShape.PointingHandCursor)
            nav.clicked.connect(lambda checked=False, i=index: self.open_page(i))
            side.addWidget(nav)
            self.nav_buttons.append(nav)
        side.addStretch()
        footer = QLabel("BY 7TPCLAN\nDeveloper: ThunderPainYT")
        footer.setObjectName("footer")
        side.addWidget(footer)
        outer.addWidget(sidebar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 26, 30, 26)
        content_layout.setSpacing(18)
        header = QHBoxLayout()
        heading_stack = QVBoxLayout()
        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("pageTitle")
        self.page_subtitle = QLabel(self.page_specs[0][1])
        self.page_subtitle.setObjectName("muted")
        heading_stack.addWidget(self.page_title)
        heading_stack.addWidget(self.page_subtitle)
        header.addLayout(heading_stack)
        header.addStretch()
        status = QLabel("WINDOWS • FOUNDATION")
        status.setObjectName("status")
        header.addWidget(status, alignment=Qt.AlignmentFlag.AlignVCenter)
        content_layout.addLayout(header)

        self.pages.addWidget(self.build_dashboard())
        self.pages.addWidget(self.build_boost())
        self.pages.addWidget(self.build_capture())
        self.pages.addWidget(self.build_packs())
        self.pages.addWidget(self.build_skies())
        self.pages.addWidget(self.build_flags())
        self.pages.addWidget(self.build_profiles())
        content_layout.addWidget(self.pages, 1)
        outer.addWidget(content, 1)
        self.setCentralWidget(root)
        self.setStyleSheet(self.stylesheet())
        self.open_page(0)

        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.refresh_stats)
        self.stats_timer.start(2000)
        self.refresh_stats()
        self.refresh_packs()
        self.refresh_skies()
        self.refresh_profiles()

        self.capture_timer = QTimer(self)
        self.capture_timer.timeout.connect(self.check_capture)
        self.capture_timer.start(1000)

    def build_dashboard(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        hero = panel()
        hero.setObjectName("hero")
        hl = QVBoxLayout(hero)
        hl.setContentsMargins(24, 22, 24, 22)
        eyebrow = QLabel("WELCOME TO YOUR NEXUS")
        eyebrow.setObjectName("eyebrow")
        title = QLabel("One toolkit. Your setup.")
        title.setObjectName("heroTitle")
        title.setWordWrap(True)
        copy = QLabel("A Windows-first desktop companion for system monitoring, recording, texture assets, sky presets and settings profiles.")
        copy.setObjectName("heroCopy")
        copy.setWordWrap(True)
        hl.addWidget(eyebrow)
        hl.addWidget(title)
        hl.addWidget(copy)
        layout.addWidget(hero)

        section = QLabel("QUICK ACCESS")
        section.setObjectName("section")
        layout.addWidget(section)
        row = QHBoxLayout()
        for name, description, index in [
            ("Nexus Boost", "CPU and memory", 1),
            ("Nexus Capture", "Desktop recording", 2),
            ("Nexus Packs", "Import texture assets", 3),
        ]:
            card = panel()
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 16, 16, 16)
            name_label = QLabel(name)
            name_label.setObjectName("cardTitle")
            desc = QLabel(description)
            desc.setObjectName("muted")
            desc.setWordWrap(True)
            go = button("Open module  →", lambda checked=False, i=index: self.open_page(i))
            cl.addWidget(name_label)
            cl.addWidget(desc)
            cl.addStretch()
            cl.addWidget(go)
            row.addWidget(card, 1)
        layout.addLayout(row)

        self.dashboard_status = QLabel("Loading local system status…")
        self.dashboard_status.setObjectName("muted")
        status_card = panel()
        sl = QVBoxLayout(status_card)
        sl.setContentsMargins(18, 16, 18, 16)
        sl.addWidget(self.dashboard_status)
        layout.addWidget(status_card)
        layout.addStretch()
        return page

    def build_boost(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        intro = QLabel("Live read-only statistics. Nexus Boost does not alter Windows settings in this build.")
        intro.setObjectName("heroCopy")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        self.cpu_value = QLabel("CPU: —")
        self.ram_value = QLabel("Memory: —")
        self.ram_detail = QLabel("")
        self.ram_detail.setObjectName("muted")
        self.cpu_bar = QProgressBar()
        self.ram_bar = QProgressBar()
        for bar in (self.cpu_bar, self.ram_bar):
            bar.setRange(0, 100)
            bar.setTextVisible(True)
        for title, value, bar in [
            ("PROCESSOR", self.cpu_value, self.cpu_bar),
            ("SYSTEM MEMORY", self.ram_value, self.ram_bar),
        ]:
            card = panel()
            cl = QVBoxLayout(card)
            cl.setContentsMargins(20, 18, 20, 18)
            label = QLabel(title)
            label.setObjectName("eyebrow")
            cl.addWidget(label)
            cl.addWidget(value)
            cl.addWidget(bar)
            if title == "SYSTEM MEMORY":
                cl.addWidget(self.ram_detail)
            layout.addWidget(card)
        layout.addWidget(button("Refresh now", self.refresh_stats, True))
        layout.addStretch()
        return page

    def build_capture(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        card = panel()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(22, 22, 22, 22)
        title = QLabel("Desktop recording")
        title.setObjectName("heroTitle")
        info = QLabel("Uses FFmpeg's Windows desktop-capture input. This initial recorder captures video only; system/game audio is not recorded.")
        info.setObjectName("heroCopy")
        info.setWordWrap(True)
        cl.addWidget(title)
        cl.addWidget(info)
        cl.addWidget(QLabel("Frame rate"))
        self.capture_fps = QComboBox()
        self.capture_fps.addItems(["30 FPS", "60 FPS"])
        cl.addWidget(self.capture_fps)
        cl.addWidget(QLabel("Quality (lower number = higher quality and larger files)"))
        self.capture_quality = QComboBox()
        self.capture_quality.addItems(["18 - High", "23 - Balanced", "28 - Smaller file"])
        self.capture_quality.setCurrentIndex(1)
        cl.addWidget(self.capture_quality)
        cl.addWidget(QLabel("Output folder"))
        outrow = QHBoxLayout()
        self.capture_folder = QLineEdit(str(Path.home() / "Videos" / "NexusStrap"))
        outrow.addWidget(self.capture_folder, 1)
        outrow.addWidget(button("Browse…", self.choose_capture_folder))
        cl.addLayout(outrow)
        controls = QHBoxLayout()
        self.record_button = button("●  Start recording", self.start_capture, True)
        self.stop_button = button("■  Stop recording", self.stop_capture)
        self.stop_button.setEnabled(False)
        controls.addWidget(self.record_button)
        controls.addWidget(self.stop_button)
        cl.addLayout(controls)
        self.capture_status = QLabel("Ready. FFmpeg must be installed and available on PATH.")
        self.capture_status.setObjectName("muted")
        self.capture_status.setWordWrap(True)
        cl.addWidget(self.capture_status)
        layout.addWidget(card)
        layout.addStretch()
        return page

    def build_packs(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        card = panel()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 20, 20, 20)
        heading = QLabel("Import a texture pack")
        heading.setObjectName("heroTitle")
        help_text = QLabel("Import a ZIP or a folder containing supported image/texture files. Nexus stores them in its own data folder and does not automatically patch Roblox.")
        help_text.setObjectName("heroCopy")
        help_text.setWordWrap(True)
        cl.addWidget(heading)
        cl.addWidget(help_text)
        cl.addWidget(QLabel("Pack name"))
        self.pack_name = QLineEdit()
        self.pack_name.setPlaceholderText("e.g. Purple Rivals Pack")
        cl.addWidget(self.pack_name)
        actions = QHBoxLayout()
        actions.addWidget(button("Import ZIP…", self.import_pack_zip, True))
        actions.addWidget(button("Import folder…", self.import_pack_folder))
        cl.addLayout(actions)
        cl.addWidget(QLabel("Imported packs"))
        self.pack_list = QListWidget()
        cl.addWidget(self.pack_list, 1)
        actions2 = QHBoxLayout()
        actions2.addWidget(button("Open packs folder", self.open_packs_folder))
        actions2.addWidget(button("Delete selected", self.delete_selected_pack))
        cl.addLayout(actions2)
        layout.addWidget(card, 1)
        return page

    def build_skies(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        card = panel()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 20, 20, 20)
        heading = QLabel("Local sky presets")
        heading.setObjectName("heroTitle")
        info = QLabel("Choose one image to use on all six faces, or select six images in this order: back, down, front, left, right, up. Images are converted to 512×512 PNGs and saved locally. Applying them to a Roblox client is not included.")
        info.setObjectName("heroCopy")
        info.setWordWrap(True)
        cl.addWidget(heading)
        cl.addWidget(info)
        cl.addWidget(QLabel("Preset name"))
        self.sky_name = QLineEdit()
        self.sky_name.setPlaceholderText("e.g. Violet Galaxy")
        cl.addWidget(self.sky_name)
        cl.addWidget(button("Choose image(s) and import…", self.import_sky_images, True))
        cl.addWidget(QLabel("Saved presets"))
        self.sky_list = QListWidget()
        cl.addWidget(self.sky_list, 1)
        actions = QHBoxLayout()
        actions.addWidget(button("Open skies folder", self.open_skies_folder))
        actions.addWidget(button("Delete selected", self.delete_selected_sky))
        cl.addLayout(actions)
        layout.addWidget(card, 1)
        return page

    def build_flags(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        card = panel()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(18, 18, 18, 18)
        heading = QLabel("Client settings JSON")
        heading.setObjectName("heroTitle")
        info = QLabel("Edit a JSON object and save it as a Nexus profile setting, or export it as ClientAppSettings.json yourself. Nexus does not silently modify Roblox files.")
        info.setObjectName("heroCopy")
        info.setWordWrap(True)
        cl.addWidget(heading)
        cl.addWidget(info)
        self.flags_editor = QPlainTextEdit()
        self.flags_editor.setPlaceholderText('{\n  "ExampleFlag": true\n}')
        self.flags_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        cl.addWidget(self.flags_editor, 1)
        try:
            self.flags_editor.setPlainText(json.dumps(services.load_flags(), indent=2))
        except ValueError as exc:
            self.flags_editor.setPlainText("{}")
            self.show_error(str(exc))
        actions = QHBoxLayout()
        actions.addWidget(button("Load saved JSON", self.load_flags_editor))
        actions.addWidget(button("Save in Nexus", self.save_flags_editor, True))
        actions.addWidget(button("Export JSON…", self.export_flags))
        cl.addLayout(actions)
        layout.addWidget(card, 1)
        return page

    def build_profiles(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        card = panel()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 20, 20, 20)
        heading = QLabel("Configuration profiles")
        heading.setObjectName("heroTitle")
        info = QLabel("Profiles store your Nexus settings JSON so you can switch between named configurations.")
        info.setObjectName("heroCopy")
        info.setWordWrap(True)
        cl.addWidget(heading)
        cl.addWidget(info)
        cl.addWidget(QLabel("New profile name"))
        self.profile_name = QLineEdit()
        self.profile_name.setPlaceholderText("e.g. Rivals Low Graphics")
        cl.addWidget(self.profile_name)
        cl.addWidget(button("Save current settings as profile", self.save_profile, True))
        cl.addWidget(QLabel("Saved profiles"))
        self.profile_list = QListWidget()
        cl.addWidget(self.profile_list, 1)
        actions = QHBoxLayout()
        actions.addWidget(button("Load selected profile", self.load_profile))
        actions.addWidget(button("Open profiles folder", self.open_profiles_folder))
        cl.addLayout(actions)
        layout.addWidget(card, 1)
        return page

    def open_page(self, index):
        self.pages.setCurrentIndex(index)
        for i, nav in enumerate(self.nav_buttons):
            nav.setChecked(i == index)
        self.page_title.setText(self.page_specs[index][0])
        self.page_subtitle.setText(self.page_specs[index][1])
        if index == 5:
            self.load_flags_editor()
        if index == 6:
            self.refresh_profiles()

    def refresh_stats(self):
        try:
            cpu = max(0, min(100, int(psutil.cpu_percent(interval=None))))
            memory = psutil.virtual_memory()
            used = memory.percent
            self.cpu_value.setText(f"{cpu}% in use")
            self.cpu_bar.setValue(cpu)
            self.ram_value.setText(f"{used}% in use")
            self.ram_bar.setValue(int(used))
            self.ram_detail.setText(f"{memory.used / (1024 ** 3):.1f} GB used of {memory.total / (1024 ** 3):.1f} GB")
            self.dashboard_status.setText(
                f"CPU {cpu}%  •  Memory {used}%  •  {len(services.list_packs())} imported pack(s)  •  {len(services.list_skies())} sky preset(s)"
            )
        except Exception as exc:
            self.dashboard_status.setText(f"System statistics unavailable: {exc}")

    def _pack_source(self, source):
        name = self.pack_name.text().strip()
        if not name:
            name = Path(source).stem if Path(source).is_file() else Path(source).name
        try:
            result = services.import_pack(source, name)
            self.pack_name.clear()
            self.refresh_packs()
            QMessageBox.information(self, "Pack imported", f"{result['name']} imported with {result['assets']} supported file(s).\n\nStored at:\n{result['path']}")
            self.refresh_stats()
        except Exception as exc:
            self.show_error(str(exc))

    def import_pack_zip(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose texture pack ZIP", str(Path.home()), "ZIP archives (*.zip)")
        if path:
            self._pack_source(path)

    def import_pack_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Choose a texture pack folder", str(Path.home()))
        if path:
            self._pack_source(path)

    def refresh_packs(self):
        if not hasattr(self, "pack_list"):
            return
        self.pack_list.clear()
        for pack in services.list_packs():
            from PySide6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(f"{pack['name']}  •  {pack['assets']} files")
            item.setData(Qt.ItemDataRole.UserRole, pack["path"])
            self.pack_list.addItem(item)

    def delete_selected_pack(self):
        item = self.pack_list.currentItem()
        if not item:
            return
        if QMessageBox.question(self, "Delete pack", f"Delete '{item.text()}' from Nexus storage?") != QMessageBox.StandardButton.Yes:
            return
        try:
            services.delete_pack(item.data(Qt.ItemDataRole.UserRole))
            self.refresh_packs()
            self.refresh_stats()
        except Exception as exc:
            self.show_error(str(exc))

    def import_sky_images(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Choose one image or six sky-face images", str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff)"
        )
        if not paths:
            return
        if len(paths) not in (1, 6):
            self.show_error("Choose either one image or exactly six images.")
            return
        name = self.sky_name.text().strip() or Path(paths[0]).stem
        try:
            result = services.import_sky(paths, name)
            self.sky_name.clear()
            self.refresh_skies()
            QMessageBox.information(self, "Sky preset saved", f"{result['name']} saved locally.\n\nNo Roblox files were changed.")
            self.refresh_stats()
        except Exception as exc:
            self.show_error(str(exc))

    def refresh_skies(self):
        if not hasattr(self, "sky_list"):
            return
        self.sky_list.clear()
        for sky in services.list_skies():
            from PySide6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(sky["name"])
            item.setData(Qt.ItemDataRole.UserRole, sky["path"])
            self.sky_list.addItem(item)

    def delete_selected_sky(self):
        item = self.sky_list.currentItem()
        if not item:
            return
        if QMessageBox.question(self, "Delete sky preset", f"Delete '{item.text()}' from Nexus storage?") != QMessageBox.StandardButton.Yes:
            return
        try:
            services.delete_sky(item.data(Qt.ItemDataRole.UserRole))
            self.refresh_skies()
            self.refresh_stats()
        except Exception as exc:
            self.show_error(str(exc))

    def load_flags_editor(self):
        try:
            self.flags_editor.setPlainText(json.dumps(services.load_flags(), indent=2, ensure_ascii=False))
        except Exception as exc:
            self.show_error(str(exc))

    def _validated_flags(self):
        try:
            data = json.loads(self.flags_editor.toPlainText() or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
        if not isinstance(data, dict):
            raise ValueError("The top level of the JSON must be an object.")
        return data

    def save_flags_editor(self):
        try:
            services.save_flags(self._validated_flags())
            QMessageBox.information(self, "Settings saved", "Your JSON settings were saved inside Nexus Strap.")
        except Exception as exc:
            self.show_error(str(exc))

    def export_flags(self):
        try:
            data = self._validated_flags()
            path, _ = QFileDialog.getSaveFileName(self, "Export settings JSON", "ClientAppSettings.json", "JSON files (*.json)")
            if not path:
                return
            Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            QMessageBox.information(self, "Export complete", f"Exported JSON to:\n{path}\n\nThis did not automatically change Roblox settings.")
        except Exception as exc:
            self.show_error(str(exc))

    def refresh_profiles(self):
        if not hasattr(self, "profile_list"):
            return
        self.profile_list.clear()
        from PySide6.QtWidgets import QListWidgetItem
        for profile in services.list_profiles():
            item = QListWidgetItem(profile)
            item.setData(Qt.ItemDataRole.UserRole, profile)
            self.profile_list.addItem(item)

    def save_profile(self):
        try:
            name = self.profile_name.text().strip()
            if not name:
                raise ValueError("Enter a profile name first.")
            flags = self._validated_flags()
            profile_id = services.save_profile(name, flags)
            services.save_flags(flags)
            self.profile_name.clear()
            self.refresh_profiles()
            QMessageBox.information(self, "Profile saved", f"Saved '{name}'.")
        except Exception as exc:
            self.show_error(str(exc))

    def load_profile(self):
        item = self.profile_list.currentItem()
        if not item:
            self.show_error("Choose a profile first.")
            return
        try:
            profile = services.load_profile(item.data(Qt.ItemDataRole.UserRole))
            services.save_flags(profile["client_flags"])
            self.flags_editor.setPlainText(json.dumps(profile["client_flags"], indent=2, ensure_ascii=False))
            QMessageBox.information(self, "Profile loaded", f"Loaded '{profile['name']}' into Nexus settings. Export separately if you want a JSON file.")
            self.open_page(5)
        except Exception as exc:
            self.show_error(str(exc))

    def choose_capture_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Choose recording output folder", self.capture_folder.text())
        if path:
            self.capture_folder.setText(path)

    def start_capture(self):
        if self.capture_process and self.capture_process.poll() is None:
            return
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            self.show_error("FFmpeg was not found. Install FFmpeg and make sure ffmpeg.exe is available on PATH, then restart Nexus Strap.")
            return
        folder = Path(self.capture_folder.text()).expanduser()
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self.show_error(f"Cannot create output folder: {exc}")
            return
        fps = "60" if self.capture_fps.currentIndex() == 1 else "30"
        crf = ["18", "23", "28"][self.capture_quality.currentIndex()]
        output = folder / f"NexusCapture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        command = [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "gdigrab", "-framerate", fps, "-i", "desktop",
            "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", crf,
            str(output),
        ]
        try:
            self.capture_log = (folder / "nexus-capture.log").open("a", encoding="utf-8")
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
            self.capture_process = subprocess.Popen(
                command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                stderr=self.capture_log, creationflags=creationflags,
            )
            self.record_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.capture_status.setText(f"Recording video only to: {output}")
        except Exception as exc:
            if self.capture_log:
                self.capture_log.close()
                self.capture_log = None
            self.show_error(f"Could not start FFmpeg: {exc}")

    def stop_capture(self):
        process = self.capture_process
        if not process or process.poll() is not None:
            self.finish_capture()
            return
        try:
            if process.stdin:
                process.stdin.write(b"q\n")
                process.stdin.flush()
            process.wait(timeout=8)
        except Exception:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
        self.finish_capture()

    def check_capture(self):
        if self.capture_process and self.capture_process.poll() is not None:
            code = self.capture_process.returncode
            self.finish_capture()
            if code not in (0, None):
                self.capture_status.setText(f"FFmpeg stopped with exit code {code}. Check nexus-capture.log in the output folder.")

    def finish_capture(self):
        self.capture_process = None
        self.record_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        if self.capture_log:
            self.capture_log.close()
            self.capture_log = None
        if hasattr(self, "capture_status") and "Recording video only" in self.capture_status.text():
            self.capture_status.setText("Recording stopped. Check the output folder for the MP4 file.")

    def open_data_folder(self, path):
        try:
            path.mkdir(parents=True, exist_ok=True)
            if sys.platform == "win32":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            self.show_error(str(exc))

    def open_packs_folder(self):
        self.open_data_folder(services.PACKS_DIR)

    def open_skies_folder(self):
        self.open_data_folder(services.SKIES_DIR)

    def open_profiles_folder(self):
        self.open_data_folder(services.PROFILES_DIR)

    def show_error(self, message):
        QMessageBox.warning(self, "7TP Nexus Strap", message)

    def closeEvent(self, event):
        if self.capture_process and self.capture_process.poll() is None:
            self.stop_capture()
        event.accept()

    @staticmethod
    def stylesheet():
        return """
        QWidget { background: #0B0B14; color: #F2F0FF; font-family: "Segoe UI", Arial; font-size: 13px; }
        QFrame#sidebar { background: #10101D; border-right: 1px solid #29243D; }
        QLabel#logo { color: #A78BFA; font-size: 38px; font-weight: 900; letter-spacing: 2px; }
        QLabel#brand { color: #FFFFFF; font-size: 15px; font-weight: 800; letter-spacing: 1px; }
        QLabel#tagline { color: #9B91B8; font-size: 9px; font-weight: 800; letter-spacing: 1px; }
        QLabel#footer { color: #77718E; font-size: 11px; padding-top: 12px; border-top: 1px solid #29243D; }
        QPushButton#navButton { text-align: left; color: #A7A1BC; background: transparent; border: 1px solid transparent; border-radius: 9px; padding: 11px 9px; font-weight: 600; }
        QPushButton#navButton:hover { background: #1B1830; color: white; }
        QPushButton#navButton:checked { background: #241B3F; color: #C4B5FD; border: 1px solid #4C347A; }
        QLabel#pageTitle { color: white; font-size: 25px; font-weight: 800; }
        QLabel#muted { color: #9892AC; font-size: 12px; }
        QLabel#status { color: #C4B5FD; background: #201936; border: 1px solid #48346B; border-radius: 10px; padding: 8px 10px; font-size: 10px; font-weight: 800; }
        QFrame#hero { background: #1A1530; border: 1px solid #40305F; border-radius: 15px; }
        QFrame#card { background: #12121F; border: 1px solid #29263D; border-radius: 13px; }
        QLabel#eyebrow { color: #A78BFA; font-size: 10px; font-weight: 800; letter-spacing: 1px; }
        QLabel#heroTitle { color: white; font-size: 24px; font-weight: 800; }
        QLabel#heroCopy { color: #B7B0CC; font-size: 13px; }
        QLabel#section { color: #A8A1BA; font-size: 10px; font-weight: 800; letter-spacing: 1.2px; }
        QLabel#cardTitle { color: #F7F5FF; font-size: 15px; font-weight: 750; }
        QLineEdit, QComboBox, QPlainTextEdit, QListWidget { background: #0E0D18; border: 1px solid #302A45; border-radius: 7px; padding: 8px; selection-background-color: #493276; }
        QPlainTextEdit { font-family: Consolas, monospace; }
        QPushButton#actionButton { color: #C4B5FD; background: #211936; border: 1px solid #40305F; border-radius: 7px; padding: 9px 11px; font-weight: 700; }
        QPushButton#actionButton:hover { background: #30234D; }
        QPushButton#primaryButton { color: #FFFFFF; background: #6D45C7; border: 1px solid #8B5CF6; border-radius: 7px; padding: 9px 11px; font-weight: 800; }
        QPushButton#primaryButton:hover { background: #8057DE; }
        QPushButton:disabled { color: #77718E; background: #181622; border-color: #29243D; }
        QProgressBar { background: #0E0D18; color: #F2F0FF; border: 1px solid #302A45; border-radius: 6px; text-align: center; min-height: 18px; }
        QProgressBar::chunk { background: #7C4DFF; border-radius: 5px; }
        """

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("7TPCLAN")
    app.setFont(QFont("Segoe UI", 10))
    window = NexusWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
