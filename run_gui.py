"""
GUI entry point for Godot Shield v1.2.0.

Creates QApplication, applies Fusion style and dark QSS, shows Splash Screen
with the app logo, and launches the MainWindow.
"""

from __future__ import annotations

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap, QColor, QPainter, QFont, QIcon
from PySide6.QtCore import Qt, QTimer

from gui.app import DARK_QSS, MainWindow

# --- Path Helpers ---
BASE_DIR = Path(__file__).resolve().parent
ICON_PNG = BASE_DIR / "icon.png"          # Check for PNG first
ICON_ICO = BASE_DIR / "icon.ico"          # Fallback to ICO
ASSET_SVG = BASE_DIR / "assets" / "icons" / "shield.svg" # Fallback to SVG

def get_logo_pixmap(size: int) -> QPixmap:
    """Loads the best available logo and scales it to the given size."""
    if ICON_PNG.exists():
        return QPixmap(str(ICON_PNG)).scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    elif ICON_ICO.exists():
        return QPixmap(str(ICON_ICO)).scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    elif ASSET_SVG.exists():
        return QIcon(str(ASSET_SVG)).pixmap(size, size)
    return QPixmap() # Empty if nothing found

def main() -> None:
    """Launch the Godot Shield GUI application with a splash screen."""
    try:
        app = QApplication(sys.argv)
        try:
            app.setStyle("Fusion")
        except Exception:
            pass

        try:
            app.setStyleSheet(DARK_QSS)
        except Exception:
            pass

        # --- Create Splash Screen ---
        splash_pix = QPixmap(600, 400)
        splash_pix.fill(QColor("#1e1e1e"))
        
        painter = QPainter(splash_pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # 1. Draw Logo (Centered, Top Half)
        logo = get_logo_pixmap(120)
        if not logo.isNull():
            x = (600 - logo.width()) // 2
            y = 60
            painter.drawPixmap(x, y, logo)
        
        # 2. Draw Title (Matching the new IDE-like font)
        painter.setPen(QColor("#ffffff"))
        # Using Segoe UI / Inter for a clean look
        title_font = QFont("Segoe UI", 28, QFont.Weight.Bold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        painter.setFont(title_font)
        painter.drawText(splash_pix.rect().adjusted(0, 120, 0, 0), Qt.AlignmentFlag.AlignCenter, "GODOT SHIELD")
        
        # 3. Draw Subtitle
        painter.setPen(QColor("#858585"))
        painter.setFont(QFont("Segoe UI", 12))
        painter.drawText(splash_pix.rect().adjusted(0, 170, 0, 0), Qt.AlignmentFlag.AlignCenter, "Automated Game Protection")
        
        # 4. Draw Version (Bottom)
        painter.setPen(QColor("#555555"))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(splash_pix.rect().adjusted(0, 300, 0, 0), Qt.AlignmentFlag.AlignCenter, "v1.2.0")
        
        painter.end()

        splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
        splash.show()
        app.processEvents() # Ensure splash renders immediately

        # --- Load Main Window ---
        window = MainWindow()
        
        # Keep splash screen for 2 seconds, then show main window
        QTimer.singleShot(2000, splash.close)
        QTimer.singleShot(2000, window.show)

        sys.exit(app.exec())

    except Exception as exc:
        try:
            print(f"Failed to start Godot Shield GUI: {exc}", file=sys.stderr)
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
