"""Grid settings widget for configuring tile grid overlay."""

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QSpinBox, QGroupBox, QCheckBox, QPushButton, QLabel,
)

from ..models import GridSettings


class GridSettingsWidget(QWidget):
    """Widget for configuring tile grid settings."""

    # Signals
    settings_changed = Signal()  # Emitted when any setting changes
    grid_visibility_changed = Signal(bool)  # Emitted when show grid toggles
    hide_labeled_changed = Signal(bool)  # Emitted when hide labeled toggles

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._settings = GridSettings()
        self._block_signals = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Grid settings group
        group = QGroupBox("Grid Settings")
        form_layout = QFormLayout(group)

        # Tile size
        size_layout = QHBoxLayout()
        self._tile_width = QSpinBox()
        self._tile_width.setRange(1, 1024)
        self._tile_width.setValue(32)
        self._tile_width.setSuffix(" px")
        self._tile_width.valueChanged.connect(self._on_setting_changed)

        self._tile_height = QSpinBox()
        self._tile_height.setRange(1, 1024)
        self._tile_height.setValue(32)
        self._tile_height.setSuffix(" px")
        self._tile_height.valueChanged.connect(self._on_setting_changed)

        size_layout.addWidget(self._tile_width)
        size_layout.addWidget(QLabel("x"))
        size_layout.addWidget(self._tile_height)
        form_layout.addRow("Tile Size:", size_layout)

        # Separator
        sep_layout = QHBoxLayout()
        self._sep_x = QSpinBox()
        self._sep_x.setRange(0, 100)
        self._sep_x.setValue(0)
        self._sep_x.setSuffix(" px")
        self._sep_x.valueChanged.connect(self._on_setting_changed)

        self._sep_y = QSpinBox()
        self._sep_y.setRange(0, 100)
        self._sep_y.setValue(0)
        self._sep_y.setSuffix(" px")
        self._sep_y.valueChanged.connect(self._on_setting_changed)

        sep_layout.addWidget(self._sep_x)
        sep_layout.addWidget(QLabel("x"))
        sep_layout.addWidget(self._sep_y)
        form_layout.addRow("Separator:", sep_layout)

        # Offset
        offset_layout = QHBoxLayout()
        self._offset_x = QSpinBox()
        self._offset_x.setRange(0, 1000)
        self._offset_x.setValue(0)
        self._offset_x.setSuffix(" px")
        self._offset_x.valueChanged.connect(self._on_setting_changed)

        self._offset_y = QSpinBox()
        self._offset_y.setRange(0, 1000)
        self._offset_y.setValue(0)
        self._offset_y.setSuffix(" px")
        self._offset_y.valueChanged.connect(self._on_setting_changed)

        offset_layout.addWidget(self._offset_x)
        offset_layout.addWidget(QLabel("x"))
        offset_layout.addWidget(self._offset_y)
        form_layout.addRow("Offset:", offset_layout)

        # Show grid checkbox
        self._show_grid = QCheckBox("Show Grid Overlay")
        self._show_grid.setChecked(True)
        self._show_grid.toggled.connect(self._on_grid_visibility_changed)
        form_layout.addRow(self._show_grid)

        # Hide labeled checkbox
        self._hide_labeled = QCheckBox("Dim Labeled Tiles")
        self._hide_labeled.setChecked(False)
        self._hide_labeled.setToolTip("Grey out tiles that already have names to see what's left")
        self._hide_labeled.toggled.connect(self._on_hide_labeled_changed)
        form_layout.addRow(self._hide_labeled)

        layout.addWidget(group)

        # Common presets
        presets_layout = QHBoxLayout()
        presets_layout.addWidget(QLabel("Presets:"))

        btn_8 = QPushButton("8x8")
        btn_8.clicked.connect(lambda: self.set_tile_size(8, 8))
        presets_layout.addWidget(btn_8)

        btn_16 = QPushButton("16x16")
        btn_16.clicked.connect(lambda: self.set_tile_size(16, 16))
        presets_layout.addWidget(btn_16)

        btn_32 = QPushButton("32x32")
        btn_32.clicked.connect(lambda: self.set_tile_size(32, 32))
        presets_layout.addWidget(btn_32)

        btn_64 = QPushButton("64x64")
        btn_64.clicked.connect(lambda: self.set_tile_size(64, 64))
        presets_layout.addWidget(btn_64)

        presets_layout.addStretch()
        layout.addLayout(presets_layout)

    @property
    def settings(self) -> GridSettings:
        """Get current grid settings."""
        return GridSettings(
            tile_width=self._tile_width.value(),
            tile_height=self._tile_height.value(),
            separator_x=self._sep_x.value(),
            separator_y=self._sep_y.value(),
            offset_x=self._offset_x.value(),
            offset_y=self._offset_y.value(),
        )

    @settings.setter
    def settings(self, value: GridSettings) -> None:
        """Set grid settings."""
        self._block_signals = True

        self._tile_width.setValue(value.tile_width)
        self._tile_height.setValue(value.tile_height)
        self._sep_x.setValue(value.separator_x)
        self._sep_y.setValue(value.separator_y)
        self._offset_x.setValue(value.offset_x)
        self._offset_y.setValue(value.offset_y)

        self._block_signals = False

    @property
    def show_grid(self) -> bool:
        """Get whether grid should be shown."""
        return self._show_grid.isChecked()

    @show_grid.setter
    def show_grid(self, value: bool) -> None:
        """Set grid visibility."""
        self._show_grid.setChecked(value)

    @property
    def hide_labeled(self) -> bool:
        """Get whether labeled tiles should be dimmed."""
        return self._hide_labeled.isChecked()

    @hide_labeled.setter
    def hide_labeled(self, value: bool) -> None:
        """Set whether to dim labeled tiles."""
        self._hide_labeled.setChecked(value)

    def set_tile_size(self, width: int, height: int) -> None:
        """Set tile size (convenience method for presets)."""
        self._tile_width.setValue(width)
        self._tile_height.setValue(height)
        # The valueChanged signals will handle the update

    def _on_setting_changed(self) -> None:
        """Handle any setting change."""
        if not self._block_signals:
            self.settings_changed.emit()

    def _on_grid_visibility_changed(self, visible: bool) -> None:
        """Handle grid visibility toggle."""
        self.grid_visibility_changed.emit(visible)

    def _on_hide_labeled_changed(self, hide: bool) -> None:
        """Handle hide labeled toggle."""
        self.hide_labeled_changed.emit(hide)
