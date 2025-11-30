#!/usr/bin/env python
"""Run Tile Splitter application."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.app import create_application
from src.main_window import MainWindow


def main() -> int:
    """Run the application."""
    app = create_application()
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
