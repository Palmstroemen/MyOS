"""Layout-related mixin methods for PostFixWindow."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QWidget,
)


class WindowLayoutMixin:
    """Toolbar construction and signal wiring for PostFixWindow."""

    def _populate_note_style_combo(self, keep_data=None):
        combo = getattr(self, "note_style_combo", None)
        if combo is None:
            return
        old_data = keep_data if keep_data is not None else combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(self.tr("Stil: Auto"), "")
        combo.addItem(self.tr("Kurznotiz / Post-it"), "postit")
        combo.addItem(self.tr("Mitschrift / A4"), "sheet")
        combo.addItem(self.tr("Konzept / Heft"), "notebook")
        combo.addItem(self.tr("Gedankenskizze / Cloud"), "cloud")
        combo.addItem(self.tr("KI-Chat / Bubble"), "chat")
        combo.addItem(self.tr("Config / Einstellungen"), "config")
        idx = combo.findData(old_data if old_data is not None else "")
        if idx < 0:
            idx = combo.findData("")
        combo.setCurrentIndex(max(0, idx))
        combo.blockSignals(False)

    def create_top_toolbar(self):
        """Create the top toolbar with all controls."""
        self.top_toolbar = QWidget()
        self.top_toolbar.setMinimumHeight(40)
        self.top_toolbar.setMaximumHeight(40)
        self.top_toolbar.setStyleSheet(
            "QWidget { background-color: #ffffff; border-bottom: 1px solid transparent; }"
        )

        layout = QHBoxLayout(self.top_toolbar)
        layout.setSpacing(10)
        layout.setContentsMargins(8, 0, 2, 0)

        self.btn_menu = QPushButton("☰")
        self.btn_menu.setCursor(Qt.PointingHandCursor)

        self.btn_bg_color = QPushButton()
        self.btn_bg_color.setCursor(Qt.PointingHandCursor)

        self.btn_text_color = QPushButton("T")
        self.btn_text_color.setCursor(Qt.PointingHandCursor)

        self.btn_highlight = QPushButton()
        self.btn_highlight.setCursor(Qt.PointingHandCursor)

        self.apply_round_button_style(self.btn_menu, "#FFF740", "#d4c600")
        self.apply_round_button_style(self.btn_bg_color, "#FFF740", "#d4c600")
        self.apply_round_button_style(self.btn_text_color, "#FFF740", "#d4c600")
        self.apply_round_button_style(self.btn_highlight, "#FFF740", "#d4c600")
        self.btn_text_color.setStyleSheet(
            self.btn_text_color.styleSheet() + "QPushButton { font-weight: bold; font-size: 14px; }"
        )
        self.btn_menu.setStyleSheet(
            self.btn_menu.styleSheet() + "QPushButton { font-size: 14px; }"
        )
        icon_path = Path(__file__).with_name("icons").joinpath("highlighter.svg")
        if icon_path.exists():
            self.btn_highlight.setIcon(QIcon(str(icon_path)))
            self.btn_highlight.setIconSize(self.btn_highlight.size())

        layout.addWidget(self.btn_menu)
        layout.addWidget(self.btn_bg_color)
        layout.addWidget(self.btn_text_color)
        layout.addWidget(self.btn_highlight)

        self.note_style_combo = QComboBox()
        self.note_style_combo.setCursor(Qt.PointingHandCursor)
        self.note_style_combo.setFixedHeight(30)
        self.note_style_combo.setMinimumWidth(170)
        self._populate_note_style_combo("")
        self.note_style_combo.setStyleSheet(
            """
            QComboBox {
                background-color: #fff740;
                border: 1px solid #d4c600;
                border-radius: 15px;
                padding: 4px 10px;
                color: #333333;
                font-size: 12px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #fff9b0;
                border: 1px solid #d4c600;
                selection-background-color: #ffe76b;
                color: #222222;
            }
            """
        )
        layout.addWidget(self.note_style_combo)
        self.file_name_edit = QLineEdit()
        self.file_name_edit.setPlaceholderText(self.tr("Dateiname"))
        self.file_name_edit.setFixedHeight(30)
        self.file_name_edit.setMinimumWidth(190)
        self.file_name_edit.setStyleSheet(
            """
            QLineEdit {
                background-color: #fff9b0;
                border: 1px solid #d4c600;
                border-radius: 15px;
                padding: 4px 10px;
                color: #333333;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #c2b100;
            }
            """
        )
        layout.addWidget(self.file_name_edit)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))

        self.btn_view_mode = QPushButton(self.tr("Fokusmodus"))
        self.btn_view_mode.setCursor(Qt.PointingHandCursor)
        self.apply_oval_button_style(self.btn_view_mode, "#FFF740", "#d4c600")
        self.btn_view_mode.hide()

        self.btn_language = QPushButton("DE")
        self.btn_language.setCursor(Qt.PointingHandCursor)
        self.apply_oval_button_style(self.btn_language, "#FFF740", "#d4c600")
        self.btn_language.setFixedHeight(30)
        self.btn_language.setMinimumWidth(68)
        layout.addWidget(self.btn_language)
        layout.addStretch()

        self.btn_minimize = QPushButton("−")
        self.btn_minimize.setCursor(Qt.PointingHandCursor)
        self.apply_round_button_style(self.btn_minimize, "#FFF740", "#d4c600")
        self.btn_minimize.setStyleSheet(
            self.btn_minimize.styleSheet() + "QPushButton { font-size: 14px; }"
        )

        self.btn_maximize = QPushButton("□")
        self.btn_maximize.setCursor(Qt.PointingHandCursor)
        self.apply_round_button_style(self.btn_maximize, "#FFF740", "#d4c600")
        self.btn_maximize.setStyleSheet(
            self.btn_maximize.styleSheet() + "QPushButton { font-size: 14px; }"
        )

        self.btn_close = QPushButton("✕")
        self.btn_close.setStyleSheet(
            """
            QPushButton {
                border-radius: 15px;
                background-color: #ff5b5b;
                color: #ffffff;
                border: 1px solid #d64a4a;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e24a4a;
                border: 1px solid #c23d3d;
            }
            """
        )
        self.btn_close.setFixedSize(30, 30)
        self.btn_close.setCursor(Qt.PointingHandCursor)

        layout.addWidget(self.btn_minimize)
        layout.addWidget(self.btn_maximize)

    def connect_signals(self):
        """Connect all button signals."""
        self.btn_minimize.clicked.connect(self.showMinimized)
        self.btn_maximize.clicked.connect(self.toggle_maximize)
        self.btn_close.clicked.connect(self.close)
        self.btn_bg_color.clicked.connect(self.pick_background_color)
        self.btn_text_color.clicked.connect(self.pick_text_color)
        self.btn_highlight.clicked.connect(self.pick_highlight_color)
        self.note_style_combo.currentIndexChanged.connect(self.on_note_style_selected)
        self.file_name_edit.editingFinished.connect(self.on_filename_edit_finished)
        self.btn_view_mode.clicked.connect(self.toggle_view_mode)
        self.btn_language.clicked.connect(self.toggle_language)
        self.btn_menu.clicked.connect(self.show_menu)
