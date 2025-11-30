"""License information data model."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class LicenseWarning(Enum):
    """Types of license warnings."""

    NONE = "none"
    NON_COMMERCIAL = "non_commercial"  # NC restriction
    NO_DERIVATIVES = "no_derivatives"  # ND restriction
    SHARE_ALIKE = "share_alike"  # SA requirement (informational)
    UNKNOWN = "unknown"  # Could not parse license
    MISSING = "missing"  # No license found


# Common license patterns and their warnings
LICENSE_PATTERNS = {
    # Public Domain / Very Permissive
    "cc0": ([], "Public Domain (CC0)"),
    "public domain": ([], "Public Domain"),
    "unlicense": ([], "Unlicense (Public Domain)"),
    # Attribution only
    "cc by 4": ([], "CC BY 4.0"),
    "cc by 3": ([], "CC BY 3.0"),
    "cc-by-4": ([], "CC BY 4.0"),
    "cc-by-3": ([], "CC BY 3.0"),
    # Share-alike (informational warning)
    "cc by-sa": ([LicenseWarning.SHARE_ALIKE], "CC BY-SA"),
    "cc-by-sa": ([LicenseWarning.SHARE_ALIKE], "CC BY-SA"),
    # Non-commercial (yellow warning)
    "cc by-nc-sa": (
        [LicenseWarning.NON_COMMERCIAL, LicenseWarning.SHARE_ALIKE],
        "CC BY-NC-SA",
    ),
    "cc by-nc-nd": (
        [LicenseWarning.NON_COMMERCIAL, LicenseWarning.NO_DERIVATIVES],
        "CC BY-NC-ND",
    ),
    "cc by-nc": ([LicenseWarning.NON_COMMERCIAL], "CC BY-NC"),
    "cc-by-nc": ([LicenseWarning.NON_COMMERCIAL], "CC BY-NC"),
    "-nc-": ([LicenseWarning.NON_COMMERCIAL], None),
    "non-commercial": ([LicenseWarning.NON_COMMERCIAL], None),
    "noncommercial": ([LicenseWarning.NON_COMMERCIAL], None),
    # No derivatives (red warning)
    "cc by-nd": ([LicenseWarning.NO_DERIVATIVES], "CC BY-ND"),
    "cc-by-nd": ([LicenseWarning.NO_DERIVATIVES], "CC BY-ND"),
    "-nd": ([LicenseWarning.NO_DERIVATIVES], None),
    "no derivatives": ([LicenseWarning.NO_DERIVATIVES], None),
    "no-derivatives": ([LicenseWarning.NO_DERIVATIVES], None),
    # Other permissive
    "mit": ([], "MIT License"),
    "apache": ([], "Apache License"),
    "bsd": ([], "BSD License"),
    "gpl": ([LicenseWarning.SHARE_ALIKE], "GPL"),
    "lgpl": ([LicenseWarning.SHARE_ALIKE], "LGPL"),
    "ofl": ([], "SIL Open Font License"),
}

# License name to canonical URL mapping
LICENSE_URLS = {
    "CC0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "Public Domain": "https://creativecommons.org/publicdomain/zero/1.0/",
    "Public Domain (CC0)": "https://creativecommons.org/publicdomain/zero/1.0/",
    "Unlicense (Public Domain)": "https://unlicense.org/",
    "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC BY 3.0": "https://creativecommons.org/licenses/by/3.0/",
    "CC BY-SA": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/",
    "CC BY-NC": "https://creativecommons.org/licenses/by-nc/4.0/",
    "CC BY-NC-SA": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
    "CC BY-NC-ND": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
    "CC BY-ND": "https://creativecommons.org/licenses/by-nd/4.0/",
    "MIT License": "https://opensource.org/licenses/MIT",
    "Apache License": "https://www.apache.org/licenses/LICENSE-2.0",
    "BSD License": "https://opensource.org/licenses/BSD-3-Clause",
    "GPL": "https://www.gnu.org/licenses/gpl-3.0.html",
    "LGPL": "https://www.gnu.org/licenses/lgpl-3.0.html",
    "SIL Open Font License": "https://scripts.sil.org/OFL",
}


def get_license_url(license_name: str) -> str:
    """Get canonical URL for a license name.

    Args:
        license_name: License name (e.g., "CC0", "CC BY 4.0")

    Returns:
        URL string, or empty string if not found
    """
    # Direct lookup
    if license_name in LICENSE_URLS:
        return LICENSE_URLS[license_name]

    # Try case-insensitive lookup
    name_lower = license_name.lower()
    for key, url in LICENSE_URLS.items():
        if key.lower() == name_lower:
            return url

    return ""


@dataclass
class LicenseInfo:
    """Represents license information for a tileset."""

    license_text: str = ""
    license_url: str = ""
    author: str = ""
    source_url: str = ""
    warnings: list[LicenseWarning] = field(default_factory=list)
    normalized_name: Optional[str] = None  # e.g., "CC BY 4.0"

    def __post_init__(self):
        """Analyze license text for warnings after initialization."""
        if self.license_text and not self.warnings:
            self._analyze_license()

    def _analyze_license(self) -> None:
        """Analyze license text to detect warnings and normalize name."""
        text_lower = self.license_text.lower()

        for pattern, (warnings, name) in LICENSE_PATTERNS.items():
            if pattern in text_lower:
                self.warnings = list(warnings)
                if name and not self.normalized_name:
                    self.normalized_name = name
                return

        # If we have text but couldn't parse it
        if self.license_text and not self.normalized_name:
            self.warnings = [LicenseWarning.UNKNOWN]

    @property
    def has_warnings(self) -> bool:
        """Check if there are any concerning warnings."""
        return any(
            w in self.warnings
            for w in [
                LicenseWarning.NON_COMMERCIAL,
                LicenseWarning.NO_DERIVATIVES,
                LicenseWarning.UNKNOWN,
                LicenseWarning.MISSING,
            ]
        )

    @property
    def has_blocking_warnings(self) -> bool:
        """Check if there are warnings that block derivative works."""
        return LicenseWarning.NO_DERIVATIVES in self.warnings

    @property
    def display_name(self) -> str:
        """Get display name for the license."""
        if self.normalized_name:
            return self.normalized_name
        if self.license_text:
            # Truncate long license text
            if len(self.license_text) > 50:
                return self.license_text[:47] + "..."
            return self.license_text
        return "No license specified"

    @property
    def warning_message(self) -> str:
        """Get a human-readable warning message."""
        messages = []

        if LicenseWarning.NO_DERIVATIVES in self.warnings:
            messages.append(
                "NO DERIVATIVES: This license prohibits creating derivative works. "
                "Splitting and using these tiles may violate the license."
            )

        if LicenseWarning.NON_COMMERCIAL in self.warnings:
            messages.append(
                "NON-COMMERCIAL: This license restricts commercial use. "
                "Ensure your intended use complies."
            )

        if LicenseWarning.SHARE_ALIKE in self.warnings:
            messages.append(
                "SHARE-ALIKE: Derivatives must use the same license."
            )

        if LicenseWarning.UNKNOWN in self.warnings:
            messages.append(
                "UNKNOWN LICENSE: Could not parse license terms. "
                "Please verify manually."
            )

        if LicenseWarning.MISSING in self.warnings:
            messages.append(
                "NO LICENSE: No license information found. "
                "Assume all rights reserved unless you can verify otherwise."
            )

        return "\n\n".join(messages) if messages else ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "license": self.license_text,
            "license_url": self.license_url,
            "author": self.author,
            "source_url": self.source_url,
            "normalized_name": self.normalized_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LicenseInfo":
        """Create from dictionary."""
        return cls(
            license_text=data.get("license", ""),
            license_url=data.get("license_url", ""),
            author=data.get("author", ""),
            source_url=data.get("source_url", ""),
            normalized_name=data.get("normalized_name"),
        )

    def is_empty(self) -> bool:
        """Check if license info is essentially empty."""
        return not (self.license_text or self.license_url or self.author)
