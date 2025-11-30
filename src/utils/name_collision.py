"""Name collision resolution utilities."""

import re
from pathlib import Path
from typing import Set


def resolve_collision(
    base_name: str,
    used_names: Set[str],
    extension: str,
) -> str:
    """Resolve a name collision by appending a numeric suffix.

    Args:
        base_name: The desired name (without extension).
        used_names: Set of already used filenames (with extension).
        extension: File extension (without dot).

    Returns:
        A unique filename (with extension).
    """
    filename = f"{base_name}.{extension}"

    if filename not in used_names:
        return filename

    # Try appending _1, _2, etc.
    counter = 1
    while True:
        new_filename = f"{base_name}_{counter}.{extension}"
        if new_filename not in used_names:
            return new_filename
        counter += 1

        # Safety limit
        if counter > 10000:
            raise ValueError(f"Could not resolve collision for {base_name}")


def find_next_set_index(output_folder: Path, prefix: str = "tileset") -> int:
    """Find the next available index for tileset folders.

    Looks for existing folders matching the pattern {prefix}_{i} and
    returns the next available index.

    Args:
        output_folder: The parent output folder.
        prefix: Folder name prefix (default: "tileset").

    Returns:
        Next available zero-based index.
    """
    if not output_folder.exists():
        return 0

    # Pattern to match tileset_0, tileset_1, etc.
    pattern = re.compile(rf"^{re.escape(prefix)}_(\d+)$")

    max_index = -1

    try:
        for item in output_folder.iterdir():
            if item.is_dir():
                match = pattern.match(item.name)
                if match:
                    index = int(match.group(1))
                    max_index = max(max_index, index)
    except OSError:
        pass

    return max_index + 1


def generate_default_set_name(output_folder: Path, prefix: str = "tileset") -> str:
    """Generate a default tileset folder name.

    Args:
        output_folder: The parent output folder.
        prefix: Folder name prefix (default: "tileset").

    Returns:
        Default folder name like "tileset_0".
    """
    index = find_next_set_index(output_folder, prefix)
    return f"{prefix}_{index}"


def is_valid_filename(name: str) -> bool:
    """Check if a string is a valid filename.

    Args:
        name: The proposed filename (without extension).

    Returns:
        True if valid.
    """
    if not name:
        return False

    # Check for invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        if char in name:
            return False

    # Check for reserved names on Windows
    reserved = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
    }
    if name.upper() in reserved:
        return False

    # Check for names ending in space or period
    if name.endswith(" ") or name.endswith("."):
        return False

    return True


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be a valid filename.

    Args:
        name: The proposed filename.

    Returns:
        Sanitized filename.
    """
    # Replace invalid characters with underscore
    invalid_chars = '<>:"/\\|?*'
    result = name
    for char in invalid_chars:
        result = result.replace(char, "_")

    # Remove trailing spaces and periods
    result = result.rstrip(" .")

    # Handle empty result
    if not result:
        result = "unnamed"

    return result
