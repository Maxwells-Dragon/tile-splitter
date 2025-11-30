"""Utility modules for Tile Splitter."""

from .image_formats import (
    SUPPORTED_FORMATS,
    get_format_filter,
    get_export_format_filter,
    can_embed_metadata,
)
from .name_collision import (
    resolve_collision,
    find_next_set_index,
    generate_default_set_name,
    is_valid_filename,
    sanitize_filename,
)

__all__ = [
    "SUPPORTED_FORMATS",
    "get_format_filter",
    "get_export_format_filter",
    "can_embed_metadata",
    "resolve_collision",
    "find_next_set_index",
    "generate_default_set_name",
    "is_valid_filename",
    "sanitize_filename",
]
