import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget
)

APP_NAME = "7TP Nexus Strap"


class NexusWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1120, 720)
        self.setMinimumSize(860, 580)
        self.nav_buttons = []

        root = QWidget()
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 24, 18, 18)
        side.setSpacing(9)

        logo = QLabel("7TP")
        logo.setObjectName("logo")
        side.addWidget(logo)
        brand = QLabel("NEXUS STRAP")
        brand.setObjectName("brand")
        side.addWidget(brand)
        tagline = QLabel("PLAY. CREATE. OPTIMIZE.")
        tagline.setObjectName("tagline")
        side.addWidget(tagline)
        side.addSpacing(26)

        self.pages = QStackedWidget()
        page_names = ["Dashboard", "Nexus Boost", "Nexus Capture", "Nexus Packs", "Nexus Skies", "Nexus Profiles"]
        for index, name in enumerate(page_names):
            button = QPushButton(("⌂   " if index == 0 else "✦   ") + name)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False, i=index: self.open_page(i))
            side.addWidget(button)
            self.nav_buttons.append(button)

        side.addStretch()
        footer = QLabel("BY 7TPCLAN\nDeveloper: ThunderPainYT")
        footer.setObjectName("footer")
        side.addWidget(footer)
        outer.addWidget(sidebar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(32, 26, 32, 26)
        content_layout.setSpacing(18)

        header = QHBoxLayout()
        heading_stack = QVBoxLayout()
        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("pageTitle")
        self.page_subtitle = QLabel("Your gaming toolkit, in one place.")
        self.page_subtitle.setObjectName("muted")
        heading_stack.addWidget(self.page_title)
        heading_stack.addWidget(self.page_subtitle)
        header.addLayout(heading_stack)
        header.addStretch()
        status = QLabel("FOUNDATION BUILD")
        status.setObjectName("status")
        header.addWidget(status, alignment=Qt.AlignmentFlag.AlignVCenter)
        content_layout.addLayout(header)

        self.pages.addWidget(self.dashboard())
        module_data = [
            ("Nexus Boost", "Performance tools will be added here.", ["Read-only system monitoring", "Clearly explained, reversible settings", "No changes to Windows settings in this starter build"]),
            ("Nexus Capture", "Recording controls will be added here.", ["Recording setup and output folder", "Resolution, FPS and quality choices", "Audio options and recording status"]),
            ("Nexus Packs", "Pack management will be added here.", ["Import compatible packs", "Back up files before applying changes", "Restore originals where supported"]),
            ("Nexus Skies", "Sky presets and custom assets will be managed here.", ["Built-in presets", "Import supported custom assets", "Disable changes and restore originals"]),
            ("Nexus Profiles", "Your saved app configurations will live here.", ["Create named profiles", "Switch between saved app preferences", "Import and export profile files"]),
        ]
        for title, description, features in module_data:
            self.pages.addWidget(self.module_page(title, description, features))
        content_layout.addWidget(self.pages, 1)
        outer.addWidget(content, 1)
        self.setCentralWidget(root)
        self.setStyleSheet(self.stylesheet())
        self.open_page(0)

    def dashboard(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        hero = QFrame()
        hero.setObjectName("hero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(25, 24, 25, 24)
        eyebrow = QLabel("WELCOME TO YOUR NEXUS")
        eyebrow.setObjectName("eyebrow")
        title = QLabel("One toolkit. Your setup.")
        title.setObjectName("heroTitle")
        title.setWordWrap(True)
        copy = QLabel("A desktop companion for performance, recording, packs and profiles. This first build establishes the interface; features will be connected one at a time.")
        copy.setObjectName("heroCopy")
        copy.setWordWrap(True)
        hero_layout.addWidget(eyebrow)
        hero_layout.addWidget(title)
        hero_layout.addWidget(copy)
        layout.addWidget(hero)

        section = QLabel("YOUR MODULES")
        section.setObjectName("section")
        layout.addWidget(section)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        for index, (name, description) in enumerate([
            ("Nexus Boost", "Performance monitoring"),
            ("Nexus Capture", "Recording workflow"),
            ("Nexus Packs", "Pack management"),
        ], start=1):
            card = QFrame()
            card.setObjectName("card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(17, 17, 17, 17)
            number = QLabel(f"MODULE 0{index}")
            number.setObjectName("eyebrow")
            card_title = QLabel(name)
            card_title.setObjectName("cardTitle")
            card_copy = QLabel(description)
            card_copy.setObjectName("muted")
            card_copy.setWordWrap(True)
            button = QPushButton("Open module  →")
            button.setObjectName("actionButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False, i=index: self.open_page(i))
            card_layout.addWidget(number)
            card_layout.addWidget(card_title)
            card_layout.addWidget(card_copy)
            card_layout.addStretch()
            card_layout.addWidget(button)
            cards.addWidget(card, 1)
        layout.addLayout(cards)

        note = QFrame()
        note.setObjectName("card")
        note_layout = QVBoxLayout(note)
        note_layout.setContentsMargins(18, 16, 18, 16)
        note_title = QLabel("BUILD STATUS")
        note_title.setObjectName("eyebrow")
        note_text = QLabel("Foundation UI ready to extend. No system settings have been changed.")
        note_text.setObjectName("muted")
        note_text.setWordWrap(True)
        note_layout.addWidget(note_title)
        note_layout.addWidget(note_text)
        layout.addWidget(note)
        layout.addStretch()
        return page

    def module_page(self, title, description, features):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        panel = QFrame()
        panel.setObjectName("card")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(24, 24, 24, 24)
        panel_layout.setSpacing(13)
        eyebrow = QLabel("NEXUS MODULE")
        eyebrow.setObjectName("eyebrow")
        heading = QLabel(title)
        heading.setObjectName("heroTitle")
        summary = QLabel(description)
        summary.setObjectName("heroCopy")
        summary.setWordWrap(True)
        panel_layout.addWidget(eyebrow)
        panel_layout.addWidget(heading)
        panel_layout.addWidget(summary)
        panel_layout.addSpacing(10)
        feature_heading = QLabel("PLANNED FEATURES")
        feature_heading.setObjectName("section")
        panel_layout.addWidget(feature_heading)
        for feature in features:
            row = QHBoxLayout()
            bullet = QLabel("✦")
            bullet.setObjectName("bullet")
            text = QLabel(feature)
            text.setObjectName("feature")
            text.setWordWrap(True)
            row.addWidget(bullet, alignment=Qt.AlignmentFlag.AlignTop)
            row.addWidget(text, 1)
            panel_layout.addLayout(row)
        note = QLabel("These are planned features, not active tools yet.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        panel_layout.addSpacing(8)
        panel_layout.addWidget(note)
        layout.addWidget(panel)
        layout.addStretch()
        return page

    def open_page(self, index):
        self.pages.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)
        names = [
            ("Dashboard", "Your gaming toolkit, in one place."),
            ("Nexus Boost", "Understand your system before changing anything."),
            ("Nexus Capture", "Plan your recording workflow."),
            ("Nexus Packs", "Organize compatible packs safely."),
            ("Nexus Skies", "Manage supported sky presets and assets."),
            ("Nexus Profiles", "Keep your configurations together."),
        ]
        self.page_title.setText(names[index][0])
        self.page_subtitle.setText(names[index][1])

    @staticmethod
    def stylesheet():
        return """
        QWidget { background: #0B0B14; color: #F2F0FF; font-family: "Segoe UI", Arial; font-size: 13px; }
        QFrame#sidebar { background: #10101D; border-right: 1px solid #29243D; }
        QLabel#logo { color: #A78BFA; font-size: 38px; font-weight: 900; letter-spacing: 2px; }
        QLabel#brand { color: #FFFFFF; font-size: 15px; font-weight: 800; letter-spacing: 1px; }
        QLabel#tagline { color: #9B91B8; font-size: 9px; font-weight: 800; letter-spacing: 1px; }
        QLabel#footer { color: #77718E; font-size: 11px; padding-top: 12px; border-top: 1px solid #29243D; }
        QPushButton#navButton { text-align: left; color: #A7A1BC; background: transparent; border: 1px solid transparent; border-radius: 9px; padding: 12px 10px; font-weight: 600; }
        QPushButton#navButton:hover { background: #1B1830; color: white; }
        QPushButton#navButton:checked { background: #241B3F; color: #C4B5FD; border: 1px solid #4C347A; }
        QLabel#pageTitle { color: white; font-size: 25px; font-weight: 800; }
        QLabel#muted { color: #9892AC; font-size: 12px; }
        QLabel#status { color: #C4B5FD; background: #201936; border: 1px solid #48346B; border-radius: 10px; padding: 8px 10px; font-size: 10px; font-weight: 800; }
        QFrame#hero { background: #1A1530; border: 1px solid #40305F; border-radius: 15px; }
        QFrame#card { background: #12121F; border: 1px solid #29263D; border-radius: 13px; }
        QLabel#eyebrow { color: #A78BFA; font-size: 10px; font-weight: 800; letter-spacing: 1px; }
        QLabel#heroTitle { color: white; font-size: 25px; font-weight: 800; }
        QLabel#heroCopy { color: #B7B0CC; font-size: 13px; }
        QLabel#section { color: #A8A1BA; font-size: 10px; font-weight: 800; letter-spacing: 1.2px; }
        QLabel#cardTitle { color: #F7F5FF; font-size: 15px; font-weight: 750; }
        QLabel#feature { color: #D7D2E5; font-size: 13px; }
        QLabel#bullet { color: #A78BFA; font-size: 14px; }
        QPushButton#actionButton { color: #C4B5FD; background: #211936; border: 1px solid #40305F; border-radius: 7px; padding: 9px; text-align: left; font-weight: 700; }
        QPushButton#actionButton:hover { background: #30234D; }
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
