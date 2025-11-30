"""Image format utilities."""

# Supported image formats for pixel art
SUPPORTED_FORMATS = {
    "png": "PNG Image",
    "jpg": "JPEG Image",
    "jpeg": "JPEG Image",
    "gif": "GIF Image",
    "bmp": "BMP Image",
    "webp": "WebP Image",
}

# Formats that support metadata embedding
METADATA_FORMATS = {"png", "webp"}

# Format groups for file dialogs
FORMAT_GROUPS = {
    "all": ("All Supported Images", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
    "png": ("PNG Images", "*.png"),
    "jpg": ("JPEG Images", "*.jpg *.jpeg"),
    "gif": ("GIF Images", "*.gif"),
    "bmp": ("BMP Images", "*.bmp"),
    "webp": ("WebP Images", "*.webp"),
}


def get_format_filter(include_all: bool = True) -> str:
    """Get a filter string for file dialogs.

    Args:
        include_all: Whether to include an "All Images" option.

    Returns:
        Filter string for QFileDialog.
    """
    filters = []

    if include_all:
        filters.append(f"{FORMAT_GROUPS['all'][0]} ({FORMAT_GROUPS['all'][1]})")

    for key in ["png", "jpg", "gif", "bmp", "webp"]:
        name, pattern = FORMAT_GROUPS[key]
        filters.append(f"{name} ({pattern})")

    return ";;".join(filters)


def get_export_format_filter() -> str:
    """Get a filter string for export dialogs."""
    filters = []
    for key in ["png", "jpg", "gif", "bmp", "webp"]:
        name, pattern = FORMAT_GROUPS[key]
        filters.append(f"{name} ({pattern})")
    return ";;".join(filters)


def can_embed_metadata(format_ext: str) -> bool:
    """Check if a format supports metadata embedding.

    Args:
        format_ext: File extension (with or without dot).

    Returns:
        True if format supports embedded metadata.
    """
    ext = format_ext.lower().lstrip(".")
    return ext in METADATA_FORMATS


def normalize_format(format_ext: str) -> str:
    """Normalize a format extension.

    Args:
        format_ext: File extension (with or without dot).

    Returns:
        Normalized extension without dot.
    """
    ext = format_ext.lower().lstrip(".")
    if ext == "jpeg":
        return "jpg"
    return ext


def get_format_description(format_ext: str) -> str:
    """Get a human-readable description for a format.

    Args:
        format_ext: File extension (with or without dot).

    Returns:
        Human-readable format name.
    """
    ext = normalize_format(format_ext)
    return SUPPORTED_FORMATS.get(ext, "Unknown Format")
