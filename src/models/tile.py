"""Individual tile data model."""

import hashlib
from dataclasses import dataclass, field
from typing import Optional
from PySide6.QtGui import QImage


def compute_image_hash(image: QImage) -> str:
    """Compute a hash of the image pixel data for deduplication."""
    if image is None:
        return ""

    # Convert to consistent format
    img = image.convertToFormat(QImage.Format.Format_RGBA8888)

    # Get raw pixel data
    ptr = img.bits()
    if ptr is None:
        return ""

    data = bytes(ptr)
    return hashlib.sha256(data).hexdigest()


@dataclass
class Tile:
    """Represents an individual tile extracted from a tileset."""

    # Grid position (zero-indexed)
    grid_x: int
    grid_y: int

    # Pixel coordinates in source image
    pixel_x: int
    pixel_y: int
    width: int
    height: int

    # Naming - None means unlabeled (won't be exported)
    custom_name: Optional[str] = None

    # Deduplication - hash of pixel data
    _image_hash: str = field(default="", repr=False)

    # Group ID for duplicate tiles (all duplicates share same group_id)
    # The group_id is the index of the first tile with this hash
    duplicate_group_id: Optional[int] = None

    # Cached image data (not serialized)
    _image: Optional[QImage] = field(default=None, repr=False, compare=False)

    @property
    def name(self) -> str:
        """Get the current name (custom or empty string if unlabeled)."""
        return self.custom_name if self.custom_name else ""

    @name.setter
    def name(self, value: str) -> None:
        """Set a custom name, or clear if empty."""
        if value:
            self.custom_name = value
        else:
            self.custom_name = None

    @property
    def is_labeled(self) -> bool:
        """Check if tile has been labeled."""
        return self.custom_name is not None and self.custom_name != ""

    @property
    def has_custom_name(self) -> bool:
        """Check if tile has a custom name (alias for is_labeled)."""
        return self.is_labeled

    @property
    def image(self) -> Optional[QImage]:
        """Get the cached tile image."""
        return self._image

    @image.setter
    def image(self, value: QImage) -> None:
        """Set the cached tile image and compute hash."""
        self._image = value
        if value is not None:
            self._image_hash = compute_image_hash(value)
        else:
            self._image_hash = ""

    @property
    def image_hash(self) -> str:
        """Get the image hash for deduplication."""
        return self._image_hash

    def get_filename(self, extension: str) -> str:
        """Get the filename for export."""
        ext = extension.lstrip(".")
        return f"{self.name}.{ext}"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "grid_x": self.grid_x,
            "grid_y": self.grid_y,
            "pixel_x": self.pixel_x,
            "pixel_y": self.pixel_y,
            "width": self.width,
            "height": self.height,
            "custom_name": self.custom_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Tile":
        """Create from dictionary."""
        return cls(
            grid_x=data["grid_x"],
            grid_y=data["grid_y"],
            pixel_x=data["pixel_x"],
            pixel_y=data["pixel_y"],
            width=data["width"],
            height=data["height"],
            custom_name=data.get("custom_name"),
        )
