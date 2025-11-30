"""Main application window."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence, QUndoStack, QCloseEvent, QShortcut
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QStatusBar, QLabel,
    QLineEdit, QPushButton, QFileDialog, QMessageBox,
    QGroupBox,
)

from .models import Tileset, GridSettings
from .services import ImageLoader, SettingsManager
from .widgets import (
    TilesetView, TileEditor, GridSettingsWidget,
    LicenseDisplayWidget, ExportDialog,
)
from .commands import RenameDuplicatesCommand, RenameSetCommand
from .utils import get_format_filter, generate_default_set_name


class MainWindow(QMainWindow):
    """Main application window for Tile Splitter."""

    def __init__(self):
        super().__init__()

        # Services
        self._settings = SettingsManager()
        self._image_loader = ImageLoader()

        # State
        self._tileset: Optional[Tileset] = None
        self._undo_stack = QUndoStack(self)

        # Rename timer for debouncing
        self._rename_timer = QTimer()
        self._rename_timer.setSingleShot(True)
        self._rename_timer.setInterval(500)  # 500ms debounce
        self._rename_timer.timeout.connect(self._commit_tile_rename)
        self._pending_tile_name: Optional[str] = None

        self._setup_ui()
        self._setup_actions()
        self._setup_shortcuts()
        self._restore_state()

    def _setup_ui(self) -> None:
        """Setup the main window UI."""
        self.setWindowTitle("Tile Splitter")
        self.setMinimumSize(1000, 700)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Top toolbar area
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(5, 5, 5, 5)

        # Output folder
        folder_group = QGroupBox("Output")
        folder_layout = QHBoxLayout(folder_group)

        self._output_folder_edit = QLineEdit()
        self._output_folder_edit.setReadOnly(True)
        self._output_folder_edit.setPlaceholderText("Select output folder...")
        folder_layout.addWidget(self._output_folder_edit)

        self._browse_btn = QPushButton("Browse...")
        self._browse_btn.clicked.connect(self._browse_output_folder)
        folder_layout.addWidget(self._browse_btn)

        top_layout.addWidget(folder_group)

        # Set name
        set_group = QGroupBox("Set Name")
        set_layout = QHBoxLayout(set_group)

        self._set_name_edit = QLineEdit()
        self._set_name_edit.setPlaceholderText("tileset_0")
        self._set_name_edit.textChanged.connect(self._on_set_name_changed)
        set_layout.addWidget(self._set_name_edit)

        top_layout.addWidget(set_group)

        # Export button
        self._export_btn = QPushButton("Export...")
        self._export_btn.setEnabled(False)
        self._export_btn.clicked.connect(self._show_export_dialog)
        top_layout.addWidget(self._export_btn)

        main_layout.addWidget(top_bar)

        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side - tileset view and grid settings
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Grid settings
        self._grid_settings = GridSettingsWidget()
        self._grid_settings.settings_changed.connect(self._on_grid_settings_changed)
        self._grid_settings.grid_visibility_changed.connect(self._on_grid_visibility_changed)
        self._grid_settings.hide_labeled_changed.connect(self._on_hide_labeled_changed)
        left_layout.addWidget(self._grid_settings)

        # Tileset view
        self._tileset_view = TilesetView()
        self._tileset_view.tile_selected.connect(self._on_tile_selected)
        self._tileset_view.file_dropped.connect(self._load_file)
        left_layout.addWidget(self._tileset_view, stretch=1)

        splitter.addWidget(left_widget)

        # Right side - tile editor
        self._tile_editor = TileEditor()
        self._tile_editor.name_changed.connect(self._on_tile_name_changed)
        splitter.addWidget(self._tile_editor)

        # Set splitter sizes (70/30 split)
        splitter.setSizes([700, 300])

        main_layout.addWidget(splitter, stretch=1)

        # Status bar with license display
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        self._license_display = LicenseDisplayWidget()
        self._license_display.license_updated.connect(self._on_license_updated)
        status_bar.addPermanentWidget(self._license_display, stretch=1)

        # Tile count label
        self._tile_count_label = QLabel("No tiles")
        status_bar.addWidget(self._tile_count_label)

    def _setup_actions(self) -> None:
        """Setup menu actions."""
        # File menu
        file_menu = self.menuBar().addMenu("&File")

        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        export_action = QAction("&Export...", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self._show_export_dialog)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = self.menuBar().addMenu("&Edit")

        self._undo_action = self._undo_stack.createUndoAction(self, "&Undo")
        self._undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        edit_menu.addAction(self._undo_action)

        self._redo_action = self._undo_stack.createRedoAction(self, "&Redo")
        self._redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        edit_menu.addAction(self._redo_action)

        # View menu
        view_menu = self.menuBar().addMenu("&View")

        reset_zoom_action = QAction("&Fit to Window", self)
        reset_zoom_action.setShortcut(QKeySequence("Ctrl+0"))
        reset_zoom_action.triggered.connect(self._tileset_view.reset_zoom)
        view_menu.addAction(reset_zoom_action)

        actual_size_action = QAction("&Actual Size (100%)", self)
        actual_size_action.setShortcut(QKeySequence("Ctrl+1"))
        actual_size_action.triggered.connect(self._tileset_view.zoom_to_actual)
        view_menu.addAction(actual_size_action)

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        # Undo/Redo are handled by actions

        # Tab to next tile in unique set
        next_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Tab), self)
        next_shortcut.activated.connect(self._select_next_unique_tile)

        # Shift+Tab to previous tile in unique set
        prev_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Tab | Qt.KeyboardModifier.ShiftModifier), self)
        prev_shortcut.activated.connect(self._select_prev_unique_tile)

    def _restore_state(self) -> None:
        """Restore window state from settings."""
        # Window geometry
        geometry = self._settings.get_window_geometry()
        if geometry:
            self.restoreGeometry(geometry)

        state = self._settings.get_window_state()
        if state:
            self.restoreState(state)

        # Output folder
        output_folder = self._settings.get_output_folder()
        if output_folder and output_folder.exists():
            self._output_folder_edit.setText(str(output_folder))

        # Grid settings
        grid_settings = self._settings.get_grid_settings()
        self._grid_settings.settings = grid_settings
        self._grid_settings.show_grid = self._settings.get_show_grid()

    def _save_state(self) -> None:
        """Save window state to settings."""
        self._settings.set_window_geometry(self.saveGeometry())
        self._settings.set_window_state(self.saveState())
        self._settings.set_grid_settings(self._grid_settings.settings)
        self._settings.set_show_grid(self._grid_settings.show_grid)
        self._settings.sync()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close."""
        self._save_state()
        super().closeEvent(event)

    # File operations

    def _open_file(self) -> None:
        """Open a file dialog to load a tileset."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Tileset",
            "",
            get_format_filter(),
        )
        if path:
            self._load_file(path)

    def _load_file(self, path: str) -> None:
        """Load a tileset file."""
        file_path = Path(path)

        # Load image
        image = self._image_loader.load_image(file_path)
        if image is None:
            QMessageBox.warning(
                self,
                "Load Failed",
                f"Could not load image: {file_path.name}"
            )
            return

        # Extract license info
        license_info = self._image_loader.extract_license_info(file_path)

        # Create tileset
        self._tileset = Tileset(
            source_path=file_path,
            source_format=self._image_loader.get_format(file_path),
            grid_settings=self._grid_settings.settings,
            license_info=license_info,
        )
        self._tileset.image = image

        # Generate default set name
        output_folder = self._get_output_folder()
        if output_folder:
            default_name = generate_default_set_name(output_folder)
            self._set_name_edit.setText(default_name)
            self._tileset.set_name = default_name

        # Update UI
        self._tileset_view.tileset = self._tileset
        self._tileset_view.show_grid = self._grid_settings.show_grid
        self._tileset_view.hide_labeled = self._grid_settings.hide_labeled
        self._license_display.license_info = license_info
        self._tile_editor.clear()

        # Update tile count
        self._update_tile_count()

        # Enable export
        self._export_btn.setEnabled(True)

        # Add to recent files
        self._settings.add_recent_file(file_path)

        # Clear undo stack
        self._undo_stack.clear()

        self.setWindowTitle(f"Tile Splitter - {file_path.name}")

    def _get_output_folder(self) -> Optional[Path]:
        """Get the current output folder."""
        text = self._output_folder_edit.text()
        if text:
            path = Path(text)
            if path.exists():
                return path
        return self._settings.get_output_folder()

    def _browse_output_folder(self) -> None:
        """Browse for output folder."""
        current = self._get_output_folder()
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            str(current) if current else "",
        )
        if folder:
            self._output_folder_edit.setText(folder)
            self._settings.set_output_folder(Path(folder))

    # Grid settings handlers

    def _on_grid_settings_changed(self) -> None:
        """Handle grid settings change."""
        if self._tileset:
            self._tileset.grid_settings = self._grid_settings.settings
            self._tileset_view.update_grid()
            self._update_tile_count()

            # Clear selection if tile no longer exists
            if self._tileset.selected_tile is None:
                self._tile_editor.clear()

    def _on_grid_visibility_changed(self, visible: bool) -> None:
        """Handle grid visibility toggle."""
        self._tileset_view.show_grid = visible

    def _on_hide_labeled_changed(self, hide: bool) -> None:
        """Handle hide labeled toggle."""
        self._tileset_view.hide_labeled = hide

    # Tile selection and naming

    def _select_next_unique_tile(self) -> None:
        """Select the next unique tile (skip duplicates)."""
        if self._tileset is None or not self._tileset.tiles:
            return

        # Get list of unique tile indices (first tile of each duplicate group)
        unique_indices = self._get_unique_tile_indices()
        if not unique_indices:
            return

        current = self._tileset.selected_tile_index
        if current is None:
            # No selection, select first unique tile
            next_idx = unique_indices[0]
        else:
            # Find current position in unique list and go to next
            # First, find which unique group we're in
            current_tile = self._tileset.tiles[current]
            current_group = current_tile.duplicate_group_id
            if current_group is None:
                current_group = current

            # Find this group in unique_indices and go to next
            try:
                pos = unique_indices.index(current_group)
                next_pos = (pos + 1) % len(unique_indices)
                next_idx = unique_indices[next_pos]
            except ValueError:
                next_idx = unique_indices[0]

        self._select_tile_by_index(next_idx)

    def _select_prev_unique_tile(self) -> None:
        """Select the previous unique tile (skip duplicates)."""
        if self._tileset is None or not self._tileset.tiles:
            return

        unique_indices = self._get_unique_tile_indices()
        if not unique_indices:
            return

        current = self._tileset.selected_tile_index
        if current is None:
            # No selection, select last unique tile
            next_idx = unique_indices[-1]
        else:
            # Find current position in unique list and go to previous
            current_tile = self._tileset.tiles[current]
            current_group = current_tile.duplicate_group_id
            if current_group is None:
                current_group = current

            try:
                pos = unique_indices.index(current_group)
                prev_pos = (pos - 1) % len(unique_indices)
                next_idx = unique_indices[prev_pos]
            except ValueError:
                next_idx = unique_indices[-1]

        self._select_tile_by_index(next_idx)

    def _get_unique_tile_indices(self) -> list[int]:
        """Get indices of first tile in each duplicate group."""
        if self._tileset is None:
            return []

        seen_groups: set[int] = set()
        unique_indices: list[int] = []

        for i, tile in enumerate(self._tileset.tiles):
            group_id = tile.duplicate_group_id if tile.duplicate_group_id is not None else i
            if group_id not in seen_groups:
                seen_groups.add(group_id)
                unique_indices.append(i)

        return unique_indices

    def _select_tile_by_index(self, index: int) -> None:
        """Select a tile by index and update UI."""
        if self._tileset is None:
            return

        self._tileset.selected_tile_index = index
        self._tileset_view.select_tile(index)
        self._on_tile_selected(index)

    def _on_tile_selected(self, index: int) -> None:
        """Handle tile selection."""
        if self._tileset and 0 <= index < len(self._tileset.tiles):
            tile = self._tileset.tiles[index]
            duplicate_count = self._tileset.get_duplicate_count(tile)
            self._tile_editor.set_tile_with_duplicates(tile, duplicate_count)

    def _on_tile_name_changed(self, new_name: str) -> None:
        """Handle tile name change (debounced)."""
        self._pending_tile_name = new_name
        self._rename_timer.start()

    def _commit_tile_rename(self) -> None:
        """Commit the pending tile rename."""
        if self._tileset is None or self._pending_tile_name is None:
            return

        tile = self._tileset.selected_tile
        if tile is None:
            return

        # Don't create command if name hasn't changed
        current_name = tile.name
        new_name = self._pending_tile_name

        if new_name == current_name:
            return

        # Create and push command (handles duplicates)
        command = RenameDuplicatesCommand(self._tileset, tile, new_name)
        self._undo_stack.push(command)

        self._pending_tile_name = None

        # Refresh the labeled overlays
        self._tileset_view.refresh_overlays()
        self._update_tile_count()

    def _on_set_name_changed(self, new_name: str) -> None:
        """Handle set name change."""
        if self._tileset is None:
            return

        # Create command for undo
        if new_name != self._tileset.set_name:
            command = RenameSetCommand(self._tileset, new_name)
            self._undo_stack.push(command)

    # License

    def _on_license_updated(self) -> None:
        """Handle license info update."""
        if self._tileset:
            self._tileset.license_info = self._license_display.license_info

    # Export

    def _show_export_dialog(self) -> None:
        """Show the export dialog."""
        if self._tileset is None:
            return

        output_folder = self._get_output_folder()
        if output_folder is None:
            QMessageBox.warning(
                self,
                "No Output Folder",
                "Please select an output folder first."
            )
            self._browse_output_folder()
            output_folder = self._get_output_folder()
            if output_folder is None:
                return

        # Check if any tiles are labeled
        exportable = self._tileset.get_exportable_tiles()
        if not exportable:
            QMessageBox.warning(
                self,
                "No Labeled Tiles",
                "No tiles have been labeled. Please name at least one tile before exporting."
            )
            return

        # Update tileset set name from edit
        self._tileset.set_name = self._set_name_edit.text().strip()

        dialog = ExportDialog(self._tileset, output_folder, self)
        if dialog.exec():
            # Update output folder if changed
            new_folder = dialog.get_output_folder()
            if new_folder != output_folder:
                self._output_folder_edit.setText(str(new_folder))
                self._settings.set_output_folder(new_folder)

            # Update set name
            self._set_name_edit.setText(dialog.get_set_name())

    # Helpers

    def _update_tile_count(self) -> None:
        """Update the tile count label."""
        if self._tileset:
            total = len(self._tileset.tiles)
            unique = self._tileset.unique_tile_count
            labeled = self._tileset.labeled_count
            cols = self._tileset.grid_columns
            rows = self._tileset.grid_rows

            # Show: "X labeled / Y unique / Z total (CxR)"
            self._tile_count_label.setText(
                f"{labeled} labeled / {unique} unique / {total} total ({cols}x{rows})"
            )
        else:
            self._tile_count_label.setText("No tiles")
