"""License extraction service for fetching license info from URLs."""

import re
from typing import Optional

import requests

from ..models import LicenseInfo


class LicenseExtractor:
    """Service for extracting license information from web pages."""

    # Timeout for HTTP requests
    REQUEST_TIMEOUT = 10

    # Common license URL patterns
    LICENSE_URL_PATTERNS = [
        # Creative Commons
        (
            r"creativecommons\.org/licenses/([a-z\-]+)/(\d\.\d)",
            lambda m: f"CC {m.group(1).upper()} {m.group(2)}"
        ),
        (
            r"creativecommons\.org/publicdomain/zero",
            lambda m: "CC0 (Public Domain)"
        ),
        # OpenGameArt specific
        (
            r"opengameart\.org/content/([^\"'\s]+)",
            None  # Will need to fetch page
        ),
    ]

    # Patterns to find license info in HTML
    HTML_LICENSE_PATTERNS = [
        # OpenGameArt license field
        r'<span class="field-name">License.*?</span>.*?<a[^>]*>([^<]+)</a>',
        # Generic license link
        r'license["\s>][^<]*<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',
        # Meta tags
        r'<meta[^>]*name=["\']?(?:license|rights|dc\.rights)["\']?[^>]*content=["\']([^"\']+)["\']',
        # Creative Commons badge
        r'<a[^>]*rel=["\']license["\'][^>]*href=["\']([^"\']+)["\']',
        # Plain text after "License:"
        r'(?:License|Licensed under)[:\s]+([A-Z]{2}[\w\s\-\.]+\d\.\d)',
    ]

    # Patterns to find author info in HTML
    HTML_AUTHOR_PATTERNS = [
        # OpenGameArt author
        r'<span class="username">([^<]+)</span>',
        r'<a[^>]*class="username"[^>]*>([^<]+)</a>',
        # Generic author patterns
        r'(?:Author|Artist|Creator|By)[:\s]+([^<\n]+)',
        r'<meta[^>]*name=["\']?(?:author|dc\.creator)["\']?[^>]*content=["\']([^"\']+)["\']',
    ]

    def fetch_license_from_url(self, url: str) -> LicenseInfo:
        """Fetch and extract license information from a URL.

        Args:
            url: URL to fetch (typically an OpenGameArt page or similar).

        Returns:
            LicenseInfo with extracted data.
        """
        try:
            response = requests.get(
                url,
                timeout=self.REQUEST_TIMEOUT,
                headers={"User-Agent": "TileSplitter/0.1"}
            )
            response.raise_for_status()
            html = response.text

            license_text = self._extract_license_from_html(html)
            license_url = self._extract_license_url_from_html(html)
            author = self._extract_author_from_html(html)

            return LicenseInfo(
                license_text=license_text,
                license_url=license_url,
                author=author,
                source_url=url,
            )

        except requests.RequestException:
            return LicenseInfo(source_url=url)

    def _extract_license_from_html(self, html: str) -> str:
        """Extract license text from HTML content."""
        for pattern in self.HTML_LICENSE_PATTERNS:
            match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
            if match:
                # Get the most relevant group
                for group in match.groups():
                    if group and not group.startswith("http"):
                        # Clean up the text
                        text = re.sub(r"<[^>]+>", "", group)
                        text = text.strip()
                        if text and len(text) < 200:  # Sanity check
                            return text
        return ""

    def _extract_license_url_from_html(self, html: str) -> str:
        """Extract license URL from HTML content."""
        # Look for Creative Commons links
        cc_match = re.search(
            r'href=["\']?(https?://creativecommons\.org/[^"\'\s>]+)',
            html,
            re.IGNORECASE
        )
        if cc_match:
            return cc_match.group(1)

        # Look for rel="license" links
        rel_match = re.search(
            r'<a[^>]*rel=["\']license["\'][^>]*href=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE
        )
        if rel_match:
            return rel_match.group(1)

        return ""

    def _extract_author_from_html(self, html: str) -> str:
        """Extract author information from HTML content."""
        for pattern in self.HTML_AUTHOR_PATTERNS:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                author = match.group(1).strip()
                # Clean up HTML entities
                author = author.replace("&amp;", "&")
                author = author.replace("&lt;", "<")
                author = author.replace("&gt;", ">")
                if author and len(author) < 100:  # Sanity check
                    return author
        return ""

    def is_valid_url(self, url: str) -> bool:
        """Check if a string is a valid URL."""
        return bool(re.match(r"https?://", url, re.IGNORECASE))

    def get_opengameart_url(self, asset_name: str) -> str:
        """Generate an OpenGameArt URL from an asset name.

        This is a convenience method for the common case of
        OpenGameArt assets.
        """
        # Clean up the name
        slug = asset_name.lower()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        return f"https://opengameart.org/content/{slug}"
