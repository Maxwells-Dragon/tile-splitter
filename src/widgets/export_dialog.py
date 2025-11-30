"""Export dialog for previewing and approving tile export."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialogButtonBox, QGroupBox, QFileDialog,
    QMessageBox, QAbstractItemView, QWidget,
)

from ..models import Tileset
from ..services import TileExporter
from ..utils import (
    get_export_format_filter, generate_default_set_name,
    is_valid_filename, sanitize_filename,
)


class ExportDialog(QDialog):
    """Dialog for previewing and confirming tile export."""

    def __init__(
        self,
        tileset: Tileset,
        output_folder: Path,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)

        self._tileset = tileset
        self._output_folder = output_folder
        self._exporter = TileExporter()
        self._export_format: Optional[str] = None

        self._setup_ui()
        self._populate()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        self.setWindowTitle("Export Tiles")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)

        # Output settings
        settings_group = QGroupBox("Export Settings")
        settings_layout = QFormLayout(settings_group)

        # Output folder
        folder_layout = QHBoxLayout()
        self._folder_edit = QLineEdit()
        self._folder_edit.setReadOnly(True)
        self._folder_edit.setText(str(self._output_folder))
        folder_layout.addWidget(self._folder_edit)

        self._folder_btn = QPushButton("Browse...")
        self._folder_btn.clicked.connect(self._browse_folder)
        folder_layout.addWidget(self._folder_btn)

        settings_layout.addRow("Output Folder:", folder_layout)

        # Set name
        self._set_name_edit = QLineEdit()
        self._set_name_edit.textChanged.connect(self._update_preview)
        settings_layout.addRow("Set Name:", self._set_name_edit)

        # Format
        self._format_combo = QComboBox()
        self._format_combo.addItem("Same as source", None)
        self._format_combo.addItem("PNG", "png")
        self._format_combo.addItem("JPEG", "jpg")
        self._format_combo.addItem("WebP", "webp")
        self._format_combo.addItem("GIF", "gif")
        self._format_combo.addItem("BMP", "bmp")
        self._format_combo.currentIndexChanged.connect(self._update_preview)
        settings_layout.addRow("Format:", self._format_combo)

        layout.addWidget(settings_group)

        # Preview table
        preview_group = QGroupBox("Files to Export")
        preview_layout = QVBoxLayout(preview_group)

        self._preview_table = QTableWidget()
        self._preview_table.setColumnCount(3)
        self._preview_table.setHorizontalHeaderLabels(["Tile", "Filename", "Full Path"])
        self._preview_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self._preview_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self._preview_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self._preview_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._preview_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        preview_layout.addWidget(self._preview_table)

        # Summary
        self._summary_label = QLabel()
        preview_layout.addWidget(self._summary_label)

        layout.addWidget(preview_group)

        # License info
        license_group = QGroupBox("License")
        license_layout = QHBoxLayout(license_group)

        self._license_label = QLabel()
        self._license_label.setWordWrap(True)
        license_layout.addWidget(self._license_label)

        layout.addWidget(license_group)

        # Buttons
        self._button_box = QDialogButtonBox()
        self._export_btn = self._button_box.addButton(
            "Export", QDialogButtonBox.ButtonRole.AcceptRole
        )
        self._cancel_btn = self._button_box.addButton(
            QDialogButtonBox.StandardButton.Cancel
        )
        self._button_box.accepted.connect(self._do_export)
        self._button_box.rejected.connect(self.reject)

        layout.addWidget(self._button_box)

    def _populate(self) -> None:
        """Populate initial values."""
        # Set name
        if self._tileset.set_name:
            self._set_name_edit.setText(self._tileset.set_name)
        else:
            default_name = generate_default_set_name(self._output_folder)
            self._set_name_edit.setText(default_name)

        # License
        license_info = self._tileset.license_info
        if license_info.is_empty():
            self._license_label.setText(
                "No license information. Consider adding license info before exporting."
            )
            self._license_label.setStyleSheet("color: #ff9900;")
        else:
            text = f"License: {license_info.display_name}"
            if license_info.author:
                text += f"\nAuthor: {license_info.author}"
            self._license_label.setText(text)

            if license_info.has_blocking_warnings:
                self._license_label.setStyleSheet("color: #ff6666;")
            elif license_info.has_warnings:
                self._license_label.setStyleSheet("color: #ffcc00;")
            else:
                self._license_label.setStyleSheet("color: #88ff88;")

        self._update_preview()

    def _browse_folder(self) -> None:
        """Browse for output folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            str(self._output_folder),
        )
        if folder:
            self._output_folder = Path(folder)
            self._folder_edit.setText(folder)
            self._update_preview()

    def _get_export_format(self) -> Optional[str]:
        """Get the selected export format."""
        return self._format_combo.currentData()

    def _update_preview(self) -> None:
        """Update the preview table."""
        set_name = self._set_name_edit.text().strip()

        # Validate set name
        if not set_name:
            self._export_btn.setEnabled(False)
            self._summary_label.setText("Please enter a set name.")
            return

        if not is_valid_filename(set_name):
            self._export_btn.setEnabled(False)
            self._summary_label.setText("Invalid set name. Please remove special characters.")
            return

        # Update tileset set_name temporarily for preview
        self._tileset.set_name = set_name

        # Get preview
        preview = self._exporter.preview_export(
            self._tileset,
            self._output_folder,
            self._get_export_format(),
        )

        # Update table
        self._preview_table.setRowCount(len(preview))

        for i, item in enumerate(preview):
            # Tile position
            tile = item["tile"]
            pos_item = QTableWidgetItem(f"({tile.grid_x}, {tile.grid_y})")
            self._preview_table.setItem(i, 0, pos_item)

            # Filename
            filename_item = QTableWidgetItem(item["filename"])
            self._preview_table.setItem(i, 1, filename_item)

            # Full path
            path_item = QTableWidgetItem(item["path"])
            self._preview_table.setItem(i, 2, path_item)

        # Update summary
        self._summary_label.setText(
            f"{len(preview)} tiles will be exported to: {self._output_folder / set_name}"
        )
        self._export_btn.setEnabled(len(preview) > 0)

    def _do_export(self) -> None:
        """Perform the export."""
        set_name = self._set_name_edit.text().strip()
        self._tileset.set_name = set_name

        success, message = self._exporter.export_tileset(
            self._tileset,
            self._output_folder,
            self._get_export_format(),
        )

        if success:
            QMessageBox.information(self, "Export Complete", message)
            self.accept()
        else:
            QMessageBox.warning(self, "Export Failed", message)

    def get_output_folder(self) -> Path:
        """Get the selected output folder."""
        return self._output_folder

    def get_set_name(self) -> str:
        """Get the set name."""
        return self._set_name_edit.text().strip()
