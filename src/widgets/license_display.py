"""License display widget with warnings."""

from typing import Optional

from PySide6.QtCore import Qt, Signal, QThread, QObject
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QGroupBox,
    QDialog, QDialogButtonBox, QFormLayout,
)

from ..models import LicenseInfo, LicenseWarning, get_license_url


class LicenseFetchWorker(QObject):
    """Worker to fetch license info in a background thread."""

    finished = Signal(object)  # Emits LicenseInfo
    error = Signal(str)  # Emits error message

    def __init__(self, url: str):
        super().__init__()
        self._url = url
        self._cancelled = False

    def cancel(self) -> None:
        """Request cancellation."""
        self._cancelled = True

    def run(self) -> None:
        """Fetch license info from URL."""
        if self._cancelled:
            return

        try:
            from ..services import LicenseExtractor

            extractor = LicenseExtractor()
            info = extractor.fetch_license_from_url(self._url)

            if not self._cancelled:
                self.finished.emit(info)

        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))


class LicenseDisplayWidget(QWidget):
    """Widget for displaying and editing license information."""

    # Signals
    license_updated = Signal()  # Emitted when license info changes
    fetch_url_requested = Signal(str)  # Emitted when user wants to fetch from URL

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._license_info = LicenseInfo()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        # Warning icon
        self._warning_icon = QLabel()
        self._warning_icon.setFixedSize(20, 20)
        layout.addWidget(self._warning_icon)

        # License text
        self._license_label = QLabel("No license")
        self._license_label.setStyleSheet("color: #888;")
        layout.addWidget(self._license_label)

        layout.addStretch()

        # Edit button
        self._edit_btn = QPushButton("Edit License")
        self._edit_btn.clicked.connect(self._show_license_dialog)
        layout.addWidget(self._edit_btn)

        self._update_display()

    @property
    def license_info(self) -> LicenseInfo:
        """Get current license info."""
        return self._license_info

    @license_info.setter
    def license_info(self, value: LicenseInfo) -> None:
        """Set license info and update display."""
        self._license_info = value
        self._update_display()

    def _update_display(self) -> None:
        """Update the display based on current license info."""
        # Update license text
        self._license_label.setText(self._license_info.display_name)

        # Update warning icon
        if LicenseWarning.NO_DERIVATIVES in self._license_info.warnings:
            self._set_warning_icon("red", "!")
            self._license_label.setStyleSheet("color: #ff6666;")
        elif LicenseWarning.NON_COMMERCIAL in self._license_info.warnings:
            self._set_warning_icon("yellow", "!")
            self._license_label.setStyleSheet("color: #ffcc00;")
        elif LicenseWarning.UNKNOWN in self._license_info.warnings:
            self._set_warning_icon("orange", "?")
            self._license_label.setStyleSheet("color: #ff9900;")
        elif LicenseWarning.MISSING in self._license_info.warnings:
            self._set_warning_icon("gray", "?")
            self._license_label.setStyleSheet("color: #888;")
        elif LicenseWarning.SHARE_ALIKE in self._license_info.warnings:
            self._set_warning_icon("blue", "i")
            self._license_label.setStyleSheet("color: #88ccff;")
        else:
            self._warning_icon.clear()
            self._license_label.setStyleSheet("color: #88ff88;")

        # Set tooltip
        if self._license_info.warning_message:
            self._warning_icon.setToolTip(self._license_info.warning_message)
            self._license_label.setToolTip(self._license_info.warning_message)
        else:
            self._warning_icon.setToolTip("")
            self._license_label.setToolTip("")

    def _set_warning_icon(self, color: str, text: str) -> None:
        """Create a simple warning icon."""
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw circle
        color_map = {
            "red": QColor(255, 80, 80),
            "yellow": QColor(255, 200, 0),
            "orange": QColor(255, 150, 0),
            "gray": QColor(128, 128, 128),
            "blue": QColor(100, 150, 255),
        }
        painter.setBrush(color_map.get(color, QColor(128, 128, 128)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 16, 16)

        # Draw text
        painter.setPen(QColor(0, 0, 0))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)

        painter.end()
        self._warning_icon.setPixmap(pixmap)

    def _show_license_dialog(self) -> None:
        """Show dialog for editing license information."""
        dialog = LicenseEditDialog(self._license_info, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._license_info = dialog.get_license_info()
            self._update_display()
            self.license_updated.emit()


class LicenseEditDialog(QDialog):
    """Dialog for editing license information."""

    def __init__(
        self,
        license_info: LicenseInfo,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)

        self._license_info = license_info
        self._fetch_thread: Optional[QThread] = None
        self._fetch_worker: Optional[LicenseFetchWorker] = None
        self._setup_ui()
        self._populate()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        self.setWindowTitle("Edit License Information")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Form
        form_group = QGroupBox("License Details")
        form_layout = QFormLayout(form_group)

        self._license_text = QLineEdit()
        self._license_text.setPlaceholderText("e.g., CC BY 4.0, MIT, Public Domain")
        form_layout.addRow("License:", self._license_text)

        self._license_url = QLineEdit()
        self._license_url.setPlaceholderText("https://creativecommons.org/licenses/by/4.0/")
        form_layout.addRow("License URL:", self._license_url)

        self._author = QLineEdit()
        self._author.setPlaceholderText("Original author/artist name")
        form_layout.addRow("Author:", self._author)

        self._source_url = QLineEdit()
        self._source_url.setPlaceholderText("https://opengameart.org/content/...")
        form_layout.addRow("Source URL:", self._source_url)

        layout.addWidget(form_group)

        # Fetch from URL section
        fetch_group = QGroupBox("Fetch from URL")
        fetch_layout = QHBoxLayout(fetch_group)

        self._fetch_url = QLineEdit()
        self._fetch_url.setPlaceholderText("Enter URL to fetch license info...")
        fetch_layout.addWidget(self._fetch_url)

        self._fetch_btn = QPushButton("Fetch")
        self._fetch_btn.clicked.connect(self._fetch_license)
        fetch_layout.addWidget(self._fetch_btn)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._cancel_fetch)
        self._cancel_btn.setVisible(False)
        fetch_layout.addWidget(self._cancel_btn)

        layout.addWidget(fetch_group)

        # Warning preview
        self._warning_preview = QLabel("")
        self._warning_preview.setWordWrap(True)
        self._warning_preview.setStyleSheet(
            "QLabel { padding: 10px; background: #333; border-radius: 5px; }"
        )
        layout.addWidget(self._warning_preview)

        # Update preview and auto-fill URL when license text changes
        self._license_text.textChanged.connect(self._update_warning_preview)
        self._license_text.textChanged.connect(self._auto_fill_license_url)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate(self) -> None:
        """Populate fields from license info."""
        self._license_text.setText(self._license_info.license_text)
        self._license_url.setText(self._license_info.license_url)
        self._author.setText(self._license_info.author)
        self._source_url.setText(self._license_info.source_url)
        self._fetch_url.setText(self._license_info.source_url)
        self._update_warning_preview()

    def _auto_fill_license_url(self) -> None:
        """Auto-fill license URL if license text matches a known license."""
        license_text = self._license_text.text().strip()
        if not license_text:
            return

        # Only auto-fill if URL is empty or was previously auto-filled
        current_url = self._license_url.text().strip()
        if current_url and not current_url.startswith("https://creativecommons.org") and not current_url.startswith("https://opensource.org"):
            # User has a custom URL, don't overwrite
            return

        url = get_license_url(license_text)
        if url:
            self._license_url.setText(url)

    def _update_warning_preview(self) -> None:
        """Update the warning preview based on current license text."""
        temp_info = LicenseInfo(
            license_text=self._license_text.text(),
            license_url=self._license_url.text(),
        )

        if temp_info.warning_message:
            self._warning_preview.setText(temp_info.warning_message)
            if LicenseWarning.NO_DERIVATIVES in temp_info.warnings:
                self._warning_preview.setStyleSheet(
                    "QLabel { padding: 10px; background: #662222; border-radius: 5px; color: #ff8888; }"
                )
            elif LicenseWarning.NON_COMMERCIAL in temp_info.warnings:
                self._warning_preview.setStyleSheet(
                    "QLabel { padding: 10px; background: #665522; border-radius: 5px; color: #ffcc00; }"
                )
            else:
                self._warning_preview.setStyleSheet(
                    "QLabel { padding: 10px; background: #333; border-radius: 5px; }"
                )
        else:
            if temp_info.license_text:
                self._warning_preview.setText("No license issues detected.")
                self._warning_preview.setStyleSheet(
                    "QLabel { padding: 10px; background: #225522; border-radius: 5px; color: #88ff88; }"
                )
            else:
                self._warning_preview.setText("Enter license information above.")
                self._warning_preview.setStyleSheet(
                    "QLabel { padding: 10px; background: #333; border-radius: 5px; color: #888; }"
                )

    def _fetch_license(self) -> None:
        """Start fetching license info from the provided URL in a background thread."""
        url = self._fetch_url.text().strip()
        if not url:
            return

        # Cancel any existing fetch
        self._cancel_fetch()

        # Update UI for fetching state
        self._fetch_btn.setEnabled(False)
        self._fetch_btn.setText("Fetching...")
        self._cancel_btn.setVisible(True)
        self._fetch_url.setEnabled(False)

        # Create worker and thread
        self._fetch_thread = QThread()
        self._fetch_worker = LicenseFetchWorker(url)
        self._fetch_worker.moveToThread(self._fetch_thread)

        # Connect signals
        self._fetch_thread.started.connect(self._fetch_worker.run)
        self._fetch_worker.finished.connect(self._on_fetch_finished)
        self._fetch_worker.error.connect(self._on_fetch_error)
        self._fetch_worker.finished.connect(self._fetch_thread.quit)
        self._fetch_worker.error.connect(self._fetch_thread.quit)
        self._fetch_thread.finished.connect(self._cleanup_fetch)

        # Start
        self._fetch_thread.start()

    def _cancel_fetch(self) -> None:
        """Cancel the current fetch operation."""
        if self._fetch_worker:
            self._fetch_worker.cancel()
        if self._fetch_thread and self._fetch_thread.isRunning():
            self._fetch_thread.quit()
            self._fetch_thread.wait(1000)  # Wait up to 1 second
        self._cleanup_fetch()

    def _on_fetch_finished(self, info: LicenseInfo) -> None:
        """Handle successful fetch."""
        if info.license_text:
            self._license_text.setText(info.license_text)
        if info.license_url:
            self._license_url.setText(info.license_url)
        if info.author:
            self._author.setText(info.author)
        if info.source_url:
            self._source_url.setText(info.source_url)

    def _on_fetch_error(self, error_msg: str) -> None:
        """Handle fetch error."""
        self._warning_preview.setText(f"Fetch failed: {error_msg}")
        self._warning_preview.setStyleSheet(
            "QLabel { padding: 10px; background: #662222; border-radius: 5px; color: #ff8888; }"
        )

    def _cleanup_fetch(self) -> None:
        """Clean up after fetch completes or is cancelled."""
        self._fetch_btn.setEnabled(True)
        self._fetch_btn.setText("Fetch")
        self._cancel_btn.setVisible(False)
        self._fetch_url.setEnabled(True)
        self._fetch_worker = None
        self._fetch_thread = None

    def reject(self) -> None:
        """Handle dialog rejection - cancel any pending fetch."""
        self._cancel_fetch()
        super().reject()

    def get_license_info(self) -> LicenseInfo:
        """Get the license info from the dialog."""
        return LicenseInfo(
            license_text=self._license_text.text().strip(),
            license_url=self._license_url.text().strip(),
            author=self._author.text().strip(),
            source_url=self._source_url.text().strip(),
        )
