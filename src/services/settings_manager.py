"""Settings manager using QSettings for persistence."""

from pathlib import Path
from typing import Optional
from PySide6.QtCore import QSettings, QByteArray

from ..models import GridSettings


class SettingsManager:
    """Manages persistent application settings."""

    def __init__(self):
        self._settings = QSettings("TileSplitter", "TileSplitter")

    # Output folder
    def get_output_folder(self) -> Optional[Path]:
        """Get the persistent output parent folder."""
        value = self._settings.value("output_folder")
        if value:
            return Path(value)
        return None

    def set_output_folder(self, path: Path) -> None:
        """Set the output parent folder."""
        self._settings.setValue("output_folder", str(path))

    # Window geometry
    def get_window_geometry(self) -> Optional[QByteArray]:
        """Get saved window geometry."""
        return self._settings.value("window_geometry")

    def set_window_geometry(self, geometry: QByteArray) -> None:
        """Save window geometry."""
        self._settings.setValue("window_geometry", geometry)

    def get_window_state(self) -> Optional[QByteArray]:
        """Get saved window state."""
        return self._settings.value("window_state")

    def set_window_state(self, state: QByteArray) -> None:
        """Save window state."""
        self._settings.setValue("window_state", state)

    # Grid settings
    def get_grid_settings(self) -> GridSettings:
        """Get last used grid settings."""
        return GridSettings(
            tile_width=int(self._settings.value("grid/tile_width", 32)),
            tile_height=int(self._settings.value("grid/tile_height", 32)),
            separator_x=int(self._settings.value("grid/separator_x", 0)),
            separator_y=int(self._settings.value("grid/separator_y", 0)),
            offset_x=int(self._settings.value("grid/offset_x", 0)),
            offset_y=int(self._settings.value("grid/offset_y", 0)),
        )

    def set_grid_settings(self, settings: GridSettings) -> None:
        """Save grid settings."""
        self._settings.setValue("grid/tile_width", settings.tile_width)
        self._settings.setValue("grid/tile_height", settings.tile_height)
        self._settings.setValue("grid/separator_x", settings.separator_x)
        self._settings.setValue("grid/separator_y", settings.separator_y)
        self._settings.setValue("grid/offset_x", settings.offset_x)
        self._settings.setValue("grid/offset_y", settings.offset_y)

    # Recent files
    def get_recent_files(self) -> list[str]:
        """Get list of recently opened files."""
        files = self._settings.value("recent_files", [])
        if files is None:
            return []
        if isinstance(files, str):
            return [files] if files else []
        return list(files)

    def add_recent_file(self, path: Path) -> None:
        """Add a file to the recent files list."""
        files = self.get_recent_files()
        path_str = str(path)

        # Remove if already in list
        if path_str in files:
            files.remove(path_str)

        # Add to front
        files.insert(0, path_str)

        # Keep only last 10
        files = files[:10]

        self._settings.setValue("recent_files", files)

    def clear_recent_files(self) -> None:
        """Clear the recent files list."""
        self._settings.setValue("recent_files", [])

    # Export format
    def get_last_export_format(self) -> str:
        """Get the last used export format."""
        return self._settings.value("last_export_format", "")

    def set_last_export_format(self, format_ext: str) -> None:
        """Set the last used export format."""
        self._settings.setValue("last_export_format", format_ext)

    # Show grid
    def get_show_grid(self) -> bool:
        """Get whether grid overlay should be shown."""
        value = self._settings.value("show_grid", True)
        if isinstance(value, str):
            return value.lower() == "true"
        return bool(value)

    def set_show_grid(self, show: bool) -> None:
        """Set whether grid overlay should be shown."""
        self._settings.setValue("show_grid", show)

    def sync(self) -> None:
        """Force settings to be written to storage."""
        self._settings.sync()
