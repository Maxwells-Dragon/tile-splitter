"""Image loading service with metadata extraction."""

import re
from pathlib import Path
from typing import Optional

from PIL import Image
from PIL.ExifTags import TAGS
from PySide6.QtGui import QImage

from ..models import LicenseInfo, LicenseWarning
from ..utils import SUPPORTED_FORMATS


class ImageLoader:
    """Service for loading images and extracting metadata."""

    def load_image(self, path: Path) -> Optional[QImage]:
        """Load an image file and return as QImage.

        Args:
            path: Path to the image file.

        Returns:
            QImage if successful, None otherwise.
        """
        if not path.exists():
            return None

        suffix = path.suffix.lower().lstrip(".")
        if suffix not in SUPPORTED_FORMATS:
            return None

        image = QImage(str(path))
        if image.isNull():
            return None

        return image

    def get_format(self, path: Path) -> str:
        """Get the image format from file extension."""
        return path.suffix.lower().lstrip(".")

    def extract_license_info(self, path: Path) -> LicenseInfo:
        """Extract license information from image metadata.

        Attempts to read:
        - PNG text chunks (Copyright, License, Author, etc.)
        - EXIF data (Copyright, Artist, etc.)
        - XMP data (various license fields)

        Args:
            path: Path to the image file.

        Returns:
            LicenseInfo with extracted data, or empty with MISSING warning.
        """
        try:
            with Image.open(path) as img:
                info = LicenseInfo()

                # Try PNG text chunks first
                if hasattr(img, "text") and img.text:
                    info = self._extract_from_png_text(img.text)
                    if not info.is_empty():
                        return info

                # Try EXIF data
                exif_info = self._extract_from_exif(img)
                if not exif_info.is_empty():
                    return exif_info

                # Try XMP data
                xmp_info = self._extract_from_xmp(img)
                if not xmp_info.is_empty():
                    return xmp_info

                # No license found
                info.warnings = [LicenseWarning.MISSING]
                return info

        except Exception:
            # Error reading file, return missing
            return LicenseInfo(warnings=[LicenseWarning.MISSING])

    def _extract_from_png_text(self, text_chunks: dict) -> LicenseInfo:
        """Extract license info from PNG text chunks."""
        license_text = ""
        author = ""
        source_url = ""
        license_url = ""

        # Common PNG text chunk keys
        for key, value in text_chunks.items():
            key_lower = key.lower()

            if "license" in key_lower:
                if "url" in key_lower:
                    license_url = value
                else:
                    license_text = value
            elif key_lower in ("copyright", "rights"):
                if not license_text:
                    license_text = value
            elif key_lower in ("author", "artist", "creator"):
                author = value
            elif key_lower in ("source", "url", "source url"):
                source_url = value

        return LicenseInfo(
            license_text=license_text,
            license_url=license_url,
            author=author,
            source_url=source_url,
        )

    def _extract_from_exif(self, img: Image.Image) -> LicenseInfo:
        """Extract license info from EXIF data."""
        try:
            exif_data = img._getexif()
            if not exif_data:
                return LicenseInfo()

            license_text = ""
            author = ""

            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)

                if tag == "Copyright":
                    license_text = str(value)
                elif tag == "Artist":
                    author = str(value)

            return LicenseInfo(
                license_text=license_text,
                author=author,
            )

        except (AttributeError, TypeError):
            return LicenseInfo()

    def _extract_from_xmp(self, img: Image.Image) -> LicenseInfo:
        """Extract license info from XMP metadata."""
        try:
            xmp_data = img.info.get("xmp", b"")
            if not xmp_data:
                return LicenseInfo()

            # XMP is XML, do basic string parsing for common fields
            if isinstance(xmp_data, bytes):
                xmp_str = xmp_data.decode("utf-8", errors="ignore")
            else:
                xmp_str = str(xmp_data)

            license_text = ""
            license_url = ""
            author = ""

            # Look for Creative Commons URL
            cc_match = re.search(
                r'https?://creativecommons\.org/licenses/[^"<>\s]+',
                xmp_str
            )
            if cc_match:
                license_url = cc_match.group(0)
                # Derive license name from URL
                license_text = self._license_name_from_url(license_url)

            # Look for dc:creator
            creator_match = re.search(
                r"<dc:creator[^>]*>.*?<rdf:li[^>]*>([^<]+)</rdf:li>",
                xmp_str,
                re.DOTALL
            )
            if creator_match:
                author = creator_match.group(1)

            # Look for dc:rights
            rights_match = re.search(
                r"<dc:rights[^>]*>.*?<rdf:li[^>]*>([^<]+)</rdf:li>",
                xmp_str,
                re.DOTALL
            )
            if rights_match and not license_text:
                license_text = rights_match.group(1)

            return LicenseInfo(
                license_text=license_text,
                license_url=license_url,
                author=author,
            )

        except Exception:
            return LicenseInfo()

    def _license_name_from_url(self, url: str) -> str:
        """Convert a Creative Commons URL to a readable name."""
        url_lower = url.lower()

        if "cc0" in url_lower or "zero" in url_lower:
            return "CC0 (Public Domain)"

        parts = []
        if "/by" in url_lower:
            parts.append("CC BY")
        if "-nc" in url_lower:
            parts.append("NC")
        if "-nd" in url_lower:
            parts.append("ND")
        if "-sa" in url_lower:
            parts.append("SA")

        # Try to get version
        version_match = re.search(r"/(\d\.\d)/", url)
        if version_match:
            parts.append(version_match.group(1))

        if parts:
            return "-".join(parts) if len(parts) > 1 else parts[0]

        return ""
