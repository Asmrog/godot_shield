"""
GUI entry point for Godot Shield.

Creates QApplication, applies Fusion style and dark QSS, shows MainWindow.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from gui.app import DARK_QSS, MainWindow


def main() -> None:
    """
    Launch the Godot Shield GUI application.

    Initializes QApplication, sets Fusion style for consistent cross-platform
    look, applies dark stylesheet, and shows the main window.
    """
    try:
        # Enable high DPI scaling (Qt 6 handles this automatically, but set attribute for safety)
        # QApplication.setHighDpiScaleFactorRoundingPolicy is default in Qt6
        app = QApplication(sys.argv)

        # Apply Fusion style for consistent appearance across platforms
        try:
            app.setStyle("Fusion")
        except Exception:
            # If Fusion not available, keep default style
            pass

        # Apply dark QSS globally
        try:
            app.setStyleSheet(DARK_QSS)
        except Exception:
            pass

        # Create and show main window
        window = MainWindow()
        window.show()

        # Run event loop
        sys.exit(app.exec())

    except Exception as exc:
        # Last resort error handling for GUI startup
        try:
            print(f"Failed to start Godot Shield GUI: {exc}", file=sys.stderr)
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
