"""Main entry point for Tile Splitter."""

import sys


def main() -> int:
    """Run the application."""
    from .app import create_application
    from .main_window import MainWindow

    app = create_application()

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
