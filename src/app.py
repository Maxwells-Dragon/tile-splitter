"""Application setup and configuration."""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor


def create_application() -> QApplication:
    """Create and configure the application."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Tile Splitter")
    app.setOrganizationName("TileSplitter")
    app.setOrganizationDomain("tilesplitter.local")

    # Apply dark theme
    _apply_dark_theme(app)

    return app


def _apply_dark_theme(app: QApplication) -> None:
    """Apply a dark color palette to the application."""
    palette = QPalette()

    # Base colors
    dark = QColor(45, 45, 45)
    darker = QColor(35, 35, 35)
    darkest = QColor(25, 25, 25)
    light = QColor(200, 200, 200)
    lighter = QColor(220, 220, 220)
    highlight = QColor(70, 130, 180)
    disabled = QColor(100, 100, 100)

    # Set palette colors
    palette.setColor(QPalette.ColorRole.Window, dark)
    palette.setColor(QPalette.ColorRole.WindowText, light)
    palette.setColor(QPalette.ColorRole.Base, darker)
    palette.setColor(QPalette.ColorRole.AlternateBase, dark)
    palette.setColor(QPalette.ColorRole.ToolTipBase, darkest)
    palette.setColor(QPalette.ColorRole.ToolTipText, light)
    palette.setColor(QPalette.ColorRole.Text, light)
    palette.setColor(QPalette.ColorRole.Button, dark)
    palette.setColor(QPalette.ColorRole.ButtonText, light)
    palette.setColor(QPalette.ColorRole.BrightText, lighter)
    palette.setColor(QPalette.ColorRole.Link, highlight)
    palette.setColor(QPalette.ColorRole.Highlight, highlight)
    palette.setColor(QPalette.ColorRole.HighlightedText, lighter)
    palette.setColor(QPalette.ColorRole.PlaceholderText, disabled)

    # Disabled colors
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.WindowText,
        disabled
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Text,
        disabled
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ButtonText,
        disabled
    )

    app.setPalette(palette)

    # Additional stylesheet for fine-tuning
    app.setStyleSheet("""
        QToolTip {
            background-color: #232323;
            color: #cccccc;
            border: 1px solid #555555;
            padding: 4px;
        }

        QGroupBox {
            border: 1px solid #555555;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 8px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 8px;
            padding: 0 4px;
        }

        QLineEdit, QSpinBox, QComboBox {
            background-color: #2a2a2a;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 4px;
        }

        QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
            border-color: #4682b4;
        }

        QPushButton {
            background-color: #3a3a3a;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 6px 12px;
        }

        QPushButton:hover {
            background-color: #454545;
        }

        QPushButton:pressed {
            background-color: #353535;
        }

        QPushButton:disabled {
            background-color: #2a2a2a;
            color: #666666;
        }

        QTableWidget {
            background-color: #2a2a2a;
            gridline-color: #404040;
        }

        QTableWidget::item:selected {
            background-color: #4682b4;
        }

        QHeaderView::section {
            background-color: #353535;
            border: 1px solid #404040;
            padding: 4px;
        }

        QScrollBar:vertical {
            background-color: #2a2a2a;
            width: 12px;
        }

        QScrollBar::handle:vertical {
            background-color: #4a4a4a;
            border-radius: 4px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #5a5a5a;
        }

        QScrollBar:horizontal {
            background-color: #2a2a2a;
            height: 12px;
        }

        QScrollBar::handle:horizontal {
            background-color: #4a4a4a;
            border-radius: 4px;
            min-width: 20px;
        }

        QScrollBar::handle:horizontal:hover {
            background-color: #5a5a5a;
        }

        QMenuBar {
            background-color: #2d2d2d;
        }

        QMenuBar::item:selected {
            background-color: #4682b4;
        }

        QMenu {
            background-color: #2d2d2d;
            border: 1px solid #404040;
        }

        QMenu::item:selected {
            background-color: #4682b4;
        }

        QStatusBar {
            background-color: #252525;
        }
    """)
