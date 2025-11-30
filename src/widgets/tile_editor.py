"""Tile editor widget for viewing and naming selected tiles."""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QGroupBox, QSizePolicy,
)

from ..models import Tile


class TileEditor(QWidget):
    """Widget for viewing and editing a selected tile."""

    # Signals
    name_changed = Signal(str)  # Emits new name when edited

    # Display settings
    PREVIEW_SIZE = 128  # Size to display tile preview

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._tile: Optional[Tile] = None
        self._duplicate_count: int = 1
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the widget UI."""
        layout = QVBoxLayout(self)

        # Group box for the editor
        group = QGroupBox("Selected Tile")
        group_layout = QVBoxLayout(group)

        # Tile preview
        self._preview_label = QLabel()
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setMinimumSize(self.PREVIEW_SIZE, self.PREVIEW_SIZE)
        self._preview_label.setMaximumSize(256, 256)
        self._preview_label.setStyleSheet(
            "QLabel { background-color: #2a2a2a; border: 1px solid #555; }"
        )
        self._preview_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        group_layout.addWidget(self._preview_label)

        # Tile info
        self._info_label = QLabel("No tile selected")
        self._info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._info_label.setStyleSheet("color: #888;")
        group_layout.addWidget(self._info_label)

        # Duplicate info
        self._duplicate_label = QLabel("")
        self._duplicate_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._duplicate_label.setStyleSheet("color: #ffcc00;")
        self._duplicate_label.setVisible(False)
        group_layout.addWidget(self._duplicate_label)

        # Name editor
        name_layout = QHBoxLayout()
        name_label = QLabel("Name:")
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Enter tile name to export...")
        self._name_edit.textChanged.connect(self._on_name_changed)
        self._name_edit.setEnabled(False)

        name_layout.addWidget(name_label)
        name_layout.addWidget(self._name_edit)
        group_layout.addLayout(name_layout)

        # Filename preview
        self._filename_label = QLabel("")
        self._filename_label.setStyleSheet("color: #888; font-size: 10px;")
        self._filename_label.setWordWrap(True)
        group_layout.addWidget(self._filename_label)

        layout.addWidget(group)
        layout.addStretch()

    @property
    def tile(self) -> Optional[Tile]:
        """Get the current tile."""
        return self._tile

    @tile.setter
    def tile(self, value: Optional[Tile]) -> None:
        """Set the tile to edit."""
        self._tile = value
        self._update_display()

    def set_tile_with_duplicates(self, tile: Optional[Tile], duplicate_count: int = 1) -> None:
        """Set the tile with duplicate count info."""
        self._tile = tile
        self._duplicate_count = duplicate_count
        self._update_display()

    def _update_display(self) -> None:
        """Update the display for the current tile."""
        if self._tile is None:
            self._preview_label.clear()
            self._info_label.setText("No tile selected")
            self._duplicate_label.setVisible(False)
            self._name_edit.clear()
            self._name_edit.setEnabled(False)
            self._filename_label.clear()
            return

        # Update preview
        if self._tile.image:
            pixmap = QPixmap.fromImage(self._tile.image)
            # Scale up for preview, keeping pixel-perfect
            scaled = pixmap.scaled(
                self.PREVIEW_SIZE, self.PREVIEW_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation  # No smoothing for pixel art
            )
            self._preview_label.setPixmap(scaled)

        # Update info
        self._info_label.setText(
            f"Position: ({self._tile.grid_x}, {self._tile.grid_y}) | "
            f"Size: {self._tile.width}x{self._tile.height}"
        )

        # Update duplicate info
        if self._duplicate_count > 1:
            self._duplicate_label.setText(
                f"This tile appears {self._duplicate_count} times in the tileset.\n"
                "Naming will apply to all copies."
            )
            self._duplicate_label.setVisible(True)
        else:
            self._duplicate_label.setVisible(False)

        # Update name editor
        self._name_edit.setEnabled(True)
        # Block signals to avoid triggering name_changed
        self._name_edit.blockSignals(True)
        self._name_edit.setText(self._tile.name)
        self._name_edit.blockSignals(False)

        # Update filename preview
        self._update_filename_preview()

    def _update_filename_preview(self) -> None:
        """Update the filename preview label."""
        if self._tile is None:
            self._filename_label.clear()
            return

        name = self._name_edit.text().strip()

        if name:
            self._filename_label.setText(f"Will be saved as: {name}.<ext>")
            self._filename_label.setStyleSheet("color: #88ff88; font-size: 10px;")
        else:
            self._filename_label.setText("Unlabeled - will not be exported")
            self._filename_label.setStyleSheet("color: #ff8888; font-size: 10px;")

    def _on_name_changed(self, text: str) -> None:
        """Handle name text changes."""
        if self._tile is not None:
            self._update_filename_preview()
            self.name_changed.emit(text)

    def get_current_name(self) -> str:
        """Get the current name in the editor."""
        return self._name_edit.text()

    def set_name(self, name: str) -> None:
        """Set the name in the editor without emitting signal."""
        self._name_edit.blockSignals(True)
        self._name_edit.setText(name)
        self._name_edit.blockSignals(False)
        self._update_filename_preview()

    def clear(self) -> None:
        """Clear the editor."""
        self._duplicate_count = 1
        self.tile = None
