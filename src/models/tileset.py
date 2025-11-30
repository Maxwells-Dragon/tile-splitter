"""Tileset data model."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PySide6.QtGui import QImage

from .tile import Tile
from .license_info import LicenseInfo


@dataclass
class GridSettings:
    """Settings for the tile grid overlay."""

    tile_width: int = 32
    tile_height: int = 32
    separator_x: int = 0  # Horizontal gap between tiles
    separator_y: int = 0  # Vertical gap between tiles
    offset_x: int = 0  # Starting X offset
    offset_y: int = 0  # Starting Y offset

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "tile_width": self.tile_width,
            "tile_height": self.tile_height,
            "separator_x": self.separator_x,
            "separator_y": self.separator_y,
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GridSettings":
        """Create from dictionary."""
        return cls(
            tile_width=data.get("tile_width", 32),
            tile_height=data.get("tile_height", 32),
            separator_x=data.get("separator_x", 0),
            separator_y=data.get("separator_y", 0),
            offset_x=data.get("offset_x", 0),
            offset_y=data.get("offset_y", 0),
        )


class Tileset:
    """Represents a loaded tileset with its tiles and metadata."""

    def __init__(
        self,
        source_path: Optional[Path] = None,
        source_format: str = "png",
        grid_settings: Optional[GridSettings] = None,
        license_info: Optional[LicenseInfo] = None,
    ):
        # Source file info
        self.source_path = source_path
        self.source_format = source_format

        # The full image
        self._image: Optional[QImage] = None

        # Grid configuration
        self.grid_settings = grid_settings or GridSettings()

        # Extracted tiles
        self.tiles: list[Tile] = []

        # Duplicate groups: hash -> list of tile indices
        self._duplicate_groups: dict[str, list[int]] = {}

        # Naming
        self.set_name: str = ""

        # License information
        self.license_info = license_info or LicenseInfo()

        # Currently selected tile index
        self.selected_tile_index: Optional[int] = None

    @property
    def image(self) -> Optional[QImage]:
        """Get the source image."""
        return self._image

    @image.setter
    def image(self, value: QImage) -> None:
        """Set the source image and regenerate tiles."""
        self._image = value
        if value is not None:
            self._generate_tiles()

    @property
    def selected_tile(self) -> Optional[Tile]:
        """Get the currently selected tile."""
        if self.selected_tile_index is not None and 0 <= self.selected_tile_index < len(self.tiles):
            return self.tiles[self.selected_tile_index]
        return None

    @property
    def selected_tile_indices(self) -> list[int]:
        """Get all selected tile indices (including duplicates)."""
        if self.selected_tile_index is None:
            return []

        tile = self.selected_tile
        if tile is None:
            return []

        # Get all tiles in the same duplicate group
        if tile.image_hash and tile.image_hash in self._duplicate_groups:
            return self._duplicate_groups[tile.image_hash]

        return [self.selected_tile_index]

    @property
    def grid_columns(self) -> int:
        """Calculate number of columns in the grid."""
        if self._image is None:
            return 0
        gs = self.grid_settings
        available_width = self._image.width() - gs.offset_x
        if gs.tile_width <= 0:
            return 0
        # Calculate how many tiles fit
        step = gs.tile_width + gs.separator_x
        if step <= 0:
            return 0
        return max(0, (available_width + gs.separator_x) // step)

    @property
    def grid_rows(self) -> int:
        """Calculate number of rows in the grid."""
        if self._image is None:
            return 0
        gs = self.grid_settings
        available_height = self._image.height() - gs.offset_y
        if gs.tile_height <= 0:
            return 0
        step = gs.tile_height + gs.separator_y
        if step <= 0:
            return 0
        return max(0, (available_height + gs.separator_y) // step)

    @property
    def tile_count(self) -> int:
        """Get total number of tiles."""
        return len(self.tiles)

    @property
    def labeled_count(self) -> int:
        """Get number of labeled tiles."""
        return sum(1 for t in self.tiles if t.is_labeled)

    @property
    def unique_tile_count(self) -> int:
        """Get number of unique tiles (after deduplication)."""
        return len(self._duplicate_groups)

    def _generate_tiles(self) -> None:
        """Generate tile objects based on current grid settings."""
        if self._image is None:
            self.tiles = []
            self._duplicate_groups = {}
            return

        gs = self.grid_settings
        cols = self.grid_columns
        rows = self.grid_rows

        # Preserve existing custom names where possible (by grid position)
        old_names: dict[tuple[int, int], str] = {}
        for tile in self.tiles:
            if tile.is_labeled and tile.custom_name:
                old_names[(tile.grid_x, tile.grid_y)] = tile.custom_name

        self.tiles = []
        self._duplicate_groups = {}

        for row in range(rows):
            for col in range(cols):
                pixel_x = gs.offset_x + col * (gs.tile_width + gs.separator_x)
                pixel_y = gs.offset_y + row * (gs.tile_height + gs.separator_y)

                # TODO: Handle partial tiles at edges
                # For now, skip tiles that would extend beyond image bounds
                if pixel_x + gs.tile_width > self._image.width():
                    continue
                if pixel_y + gs.tile_height > self._image.height():
                    continue

                tile = Tile(
                    grid_x=col,
                    grid_y=row,
                    pixel_x=pixel_x,
                    pixel_y=pixel_y,
                    width=gs.tile_width,
                    height=gs.tile_height,
                    custom_name=old_names.get((col, row)),
                )

                # Extract tile image (this also computes the hash)
                tile.image = self._image.copy(
                    pixel_x, pixel_y, gs.tile_width, gs.tile_height
                )

                tile_index = len(self.tiles)
                self.tiles.append(tile)

                # Track duplicate groups
                if tile.image_hash:
                    if tile.image_hash not in self._duplicate_groups:
                        self._duplicate_groups[tile.image_hash] = []
                    self._duplicate_groups[tile.image_hash].append(tile_index)

        # Assign duplicate group IDs (index of first tile with this hash)
        for hash_val, indices in self._duplicate_groups.items():
            group_id = indices[0]
            for idx in indices:
                self.tiles[idx].duplicate_group_id = group_id

        # Clear selection if it's now invalid
        if self.selected_tile_index is not None:
            if self.selected_tile_index >= len(self.tiles):
                self.selected_tile_index = None

    def regenerate_tiles(self) -> None:
        """Public method to regenerate tiles after grid settings change."""
        self._generate_tiles()

    def select_tile_at_position(self, pixel_x: int, pixel_y: int) -> Optional[int]:
        """Select a tile at the given pixel position in the image.

        Returns the tile index if found, None otherwise.
        """
        gs = self.grid_settings

        # Check if position is within the grid area
        if pixel_x < gs.offset_x or pixel_y < gs.offset_y:
            return None

        # Calculate grid position
        rel_x = pixel_x - gs.offset_x
        rel_y = pixel_y - gs.offset_y

        step_x = gs.tile_width + gs.separator_x
        step_y = gs.tile_height + gs.separator_y

        if step_x <= 0 or step_y <= 0:
            return None

        col = rel_x // step_x
        row = rel_y // step_y

        # Check if click is within a tile (not in separator)
        pos_in_cell_x = rel_x % step_x
        pos_in_cell_y = rel_y % step_y

        if pos_in_cell_x >= gs.tile_width or pos_in_cell_y >= gs.tile_height:
            # Click is in separator area
            return None

        # Find the tile at this grid position
        for i, tile in enumerate(self.tiles):
            if tile.grid_x == col and tile.grid_y == row:
                self.selected_tile_index = i
                return i

        return None

    def get_tile_by_grid_pos(self, col: int, row: int) -> Optional[Tile]:
        """Get a tile by its grid position."""
        for tile in self.tiles:
            if tile.grid_x == col and tile.grid_y == row:
                return tile
        return None

    def get_duplicate_tiles(self, tile: Tile) -> list[Tile]:
        """Get all tiles that are duplicates of the given tile."""
        if not tile.image_hash or tile.image_hash not in self._duplicate_groups:
            return [tile]

        indices = self._duplicate_groups[tile.image_hash]
        return [self.tiles[i] for i in indices]

    def get_duplicate_count(self, tile: Tile) -> int:
        """Get the number of duplicates for a tile (including itself)."""
        if not tile.image_hash or tile.image_hash not in self._duplicate_groups:
            return 1
        return len(self._duplicate_groups[tile.image_hash])

    def set_name_for_duplicates(self, tile: Tile, name: str) -> list[Tile]:
        """Set the name for a tile and all its duplicates.

        Returns list of all tiles that were modified.
        """
        duplicates = self.get_duplicate_tiles(tile)
        for dup in duplicates:
            dup.name = name
        return duplicates

    def get_exportable_tiles(self) -> list[Tile]:
        """Get tiles that are labeled and ready for export.

        Only returns one tile per duplicate group.
        """
        exported_hashes: set[str] = set()
        exportable: list[Tile] = []

        for tile in self.tiles:
            if not tile.is_labeled:
                continue

            # Skip if we've already included a tile with this hash
            if tile.image_hash and tile.image_hash in exported_hashes:
                continue

            exportable.append(tile)
            if tile.image_hash:
                exported_hashes.add(tile.image_hash)

        return exportable

    def get_all_filenames(self, extension: str) -> list[str]:
        """Get all tile filenames for export (only labeled, deduplicated)."""
        return [tile.get_filename(extension) for tile in self.get_exportable_tiles()]

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "source_path": str(self.source_path) if self.source_path else None,
            "source_format": self.source_format,
            "grid_settings": self.grid_settings.to_dict(),
            "tiles": [tile.to_dict() for tile in self.tiles],
            "set_name": self.set_name,
            "license_info": self.license_info.to_dict(),
        }
