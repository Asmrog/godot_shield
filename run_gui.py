"""
GUI entry point for Godot Shield.

Creates QApplication, applies Fusion style and dark QSS, shows Splash Screen,
and launches the MainWindow.
"""

from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap, QColor, QPainter, QFont,QIcon
from PySide6.QtCore import Qt, QTimer

from gui.app import DARK_QSS, MainWindow


def main() -> None:
    """Launch the Godot Shield GUI application with a splash screen."""
    try:
        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon("icon.ico"))
        try:
            app.setStyle("Fusion")
        except Exception:
            pass

        try:
            app.setStyleSheet(DARK_QSS)
        except Exception:
            pass

        # --- Create Splash Screen dynamically ---
        splash_pix = QPixmap(600, 350)
        splash_pix.fill(QColor("#1e1e1e"))
        
        painter = QPainter(splash_pix)
        painter.setPen(QColor("#0d99ff"))
        painter.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        painter.drawText(splash_pix.rect().adjusted(0, -40, 0, 0), Qt.AlignmentFlag.AlignCenter, "🛡 Godot Shield")
        
        painter.setPen(QColor("#cccccc"))
        painter.setFont(QFont("Segoe UI", 14))
        painter.drawText(splash_pix.rect().adjusted(0, 40, 0, 0), Qt.AlignmentFlag.AlignCenter, "Automated Game Protection")
        
        painter.setPen(QColor("#666666"))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(splash_pix.rect().adjusted(0, 100, 0, 0), Qt.AlignmentFlag.AlignCenter, "v1.1.3")
        painter.end()

        splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
        splash.show()
        app.processEvents()

        window = MainWindow()
        
        QTimer.singleShot(2500, splash.close)
        QTimer.singleShot(2500, window.show)

        sys.exit(app.exec())

    except Exception as exc:
        try:
            print(f"Failed to start Godot Shield GUI: {exc}", file=sys.stderr)
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
