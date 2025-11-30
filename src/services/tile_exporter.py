"""Tile export service with metadata embedding."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from PIL import Image
from PIL.PngImagePlugin import PngInfo
from PySide6.QtGui import QImage

from ..models import Tileset, Tile, LicenseInfo
from ..utils import resolve_collision, can_embed_metadata

# Software identifier for metadata
SOFTWARE_NAME = "Tile Splitter"


class TileExporter:
    """Service for exporting tiles with embedded metadata."""

    def export_tileset(
        self,
        tileset: Tileset,
        output_folder: Path,
        export_format: Optional[str] = None,
    ) -> tuple[bool, str]:
        """Export all tiles from a tileset.

        Args:
            tileset: The tileset to export.
            output_folder: Parent folder for output.
            export_format: Format to export (None = same as source).

        Returns:
            Tuple of (success, message).
        """
        # Determine output format
        if export_format:
            fmt = export_format.lower().lstrip(".")
        else:
            fmt = tileset.source_format

        # Create set folder
        set_folder = output_folder / tileset.set_name
        try:
            set_folder.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return False, f"Failed to create output folder: {e}"

        # Get only exportable tiles (labeled and deduplicated)
        exportable_tiles = tileset.get_exportable_tiles()

        if not exportable_tiles:
            return False, "No labeled tiles to export."

        # Track exported files for LICENSE.json
        exported_files: list[str] = []
        errors: list[str] = []

        # Resolve any name collisions
        used_names: set[str] = set()

        for tile in exportable_tiles:
            # Get filename with collision resolution
            base_name = tile.name
            filename = f"{base_name}.{fmt}"

            if filename in used_names:
                resolved_name = resolve_collision(base_name, used_names, fmt)
                filename = resolved_name
            used_names.add(filename)

            # Export the tile
            output_path = set_folder / filename
            success = self._export_tile(
                tile, output_path, fmt, tileset.license_info
            )

            if success:
                exported_files.append(filename)
            else:
                errors.append(f"Failed to export {filename}")

        # Write LICENSE.json
        self._write_license_json(
            set_folder,
            tileset.source_path,
            tileset.license_info,
            exported_files,
        )

        if errors:
            return False, f"Exported {len(exported_files)} tiles with {len(errors)} errors:\n" + "\n".join(errors)

        return True, f"Successfully exported {len(exported_files)} tiles to {set_folder}"

    def _export_tile(
        self,
        tile: Tile,
        output_path: Path,
        fmt: str,
        license_info: LicenseInfo,
    ) -> bool:
        """Export a single tile with embedded metadata.

        Args:
            tile: The tile to export.
            output_path: Path to write the file.
            fmt: Image format.
            license_info: License info to embed.

        Returns:
            True if successful.
        """
        if tile.image is None:
            return False

        try:
            # Convert QImage to PIL Image
            pil_image = self._qimage_to_pil(tile.image)
            if pil_image is None:
                return False

            # Build save kwargs with format-specific options
            save_kwargs = self._get_save_kwargs(fmt, pil_image, license_info)

            pil_image.save(output_path, **save_kwargs)

            return True

        except Exception:
            return False

    def _qimage_to_pil(self, qimage: QImage) -> Optional[Image.Image]:
        """Convert a QImage to a PIL Image."""
        try:
            # Convert to a format PIL can read
            qimage = qimage.convertToFormat(QImage.Format.Format_RGBA8888)

            width = qimage.width()
            height = qimage.height()

            # Get the raw data
            ptr = qimage.bits()
            if ptr is None:
                return None

            # Create PIL image from bytes
            arr = bytes(ptr)
            pil_image = Image.frombytes("RGBA", (width, height), arr)

            return pil_image

        except Exception:
            return None

    def _build_png_metadata(self, license_info: LicenseInfo) -> PngInfo:
        """Build PNG text chunks with license and software metadata."""
        pnginfo = PngInfo()

        # Software and creation info
        pnginfo.add_text("Software", SOFTWARE_NAME)
        pnginfo.add_text(
            "Creation Time",
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        # License/copyright info - preserve original attribution
        if license_info.license_text:
            pnginfo.add_text("License", license_info.license_text)
        if license_info.license_url:
            pnginfo.add_text("License URL", license_info.license_url)
        if license_info.author:
            # Use "Original Author" to distinguish from claiming authorship
            pnginfo.add_text("Original Author", license_info.author)
        if license_info.source_url:
            pnginfo.add_text("Source", license_info.source_url)
        if license_info.normalized_name:
            pnginfo.add_text("Copyright", license_info.normalized_name)

        return pnginfo

    def _get_save_kwargs(
        self,
        fmt: str,
        image: Image.Image,
        license_info: LicenseInfo,
    ) -> dict:
        """Get format-specific save options including metadata."""
        kwargs: dict = {}

        if fmt == "png":
            kwargs["pnginfo"] = self._build_png_metadata(license_info)
            kwargs["compress_level"] = 9

            # Preserve ICC profile if present
            if "icc_profile" in image.info:
                kwargs["icc_profile"] = image.info["icc_profile"]

        elif fmt in ("jpg", "jpeg"):
            kwargs["quality"] = 95
            kwargs["optimize"] = True

            # Preserve ICC profile if present
            if "icc_profile" in image.info:
                kwargs["icc_profile"] = image.info["icc_profile"]

        elif fmt == "webp":
            kwargs["quality"] = 95
            kwargs["lossless"] = True  # Good for pixel art

            # Preserve ICC profile if present
            if "icc_profile" in image.info:
                kwargs["icc_profile"] = image.info["icc_profile"]

        elif fmt == "gif":
            kwargs["optimize"] = True

        return kwargs

    def _write_license_json(
        self,
        set_folder: Path,
        source_path: Optional[Path],
        license_info: LicenseInfo,
        exported_files: list[str],
    ) -> None:
        """Write LICENSE.json to the set folder."""
        license_data = {
            "sources": [
                {
                    "source_file": source_path.name if source_path else "unknown",
                    "license": license_info.license_text,
                    "license_url": license_info.license_url,
                    "author": license_info.author,
                    "source_url": license_info.source_url,
                    "tiles": exported_files,
                }
            ]
        }

        license_path = set_folder / "LICENSE.json"

        # If LICENSE.json already exists, merge with it
        if license_path.exists():
            try:
                with open(license_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                if "sources" in existing:
                    existing["sources"].append(license_data["sources"][0])
                    license_data = existing
            except (json.JSONDecodeError, OSError):
                pass  # Overwrite if can't read

        with open(license_path, "w", encoding="utf-8") as f:
            json.dump(license_data, f, indent=2)

    def preview_export(
        self,
        tileset: Tileset,
        output_folder: Path,
        export_format: Optional[str] = None,
    ) -> list[dict]:
        """Generate a preview of what would be exported.

        Args:
            tileset: The tileset to preview.
            output_folder: Parent folder for output.
            export_format: Format to export (None = same as source).

        Returns:
            List of dicts with 'filename' and 'path' keys.
        """
        if export_format:
            fmt = export_format.lower().lstrip(".")
        else:
            fmt = tileset.source_format

        set_folder = output_folder / tileset.set_name
        used_names: set[str] = set()
        preview: list[dict] = []

        # Only preview exportable tiles (labeled and deduplicated)
        for tile in tileset.get_exportable_tiles():
            base_name = tile.name
            filename = f"{base_name}.{fmt}"

            if filename in used_names:
                filename = resolve_collision(base_name, used_names, fmt)
            used_names.add(filename)

            preview.append({
                "tile": tile,
                "filename": filename,
                "path": str(set_folder / filename),
            })

        return preview
