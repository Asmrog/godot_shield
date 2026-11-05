"""
GUI entry point for Godot Shield v1.2.0.

Creates QApplication, applies Fusion style, shows an Animated Splash Screen
(Fade-in + Loading Bar), and launches the MainWindow.
"""

from __future__ import annotations

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap, QColor, QPainter, QFont, QIcon, QPen, QBrush
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF

from gui.app import DARK_QSS, MainWindow

# --- Path Helpers ---
BASE_DIR = Path(__file__).resolve().parent
ICON_PNG = BASE_DIR / "icon.png"
ICON_ICO = BASE_DIR / "icon.ico"
ASSET_SVG = BASE_DIR / "assets" / "icons" / "shield.svg"

def get_logo_pixmap(size: int) -> QPixmap:
    """Loads the best available logo and scales it to the given size."""
    if ICON_PNG.exists():
        return QPixmap(str(ICON_PNG)).scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    elif ICON_ICO.exists():
        return QPixmap(str(ICON_ICO)).scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    elif ASSET_SVG.exists():
        return QIcon(str(ASSET_SVG)).pixmap(size, size)
    return QPixmap()


class AnimatedSplashScreen(QSplashScreen):
    """Custom splash screen with fade-in animation and a loading bar."""
    
    def __init__(self, pixmap: QPixmap):
        super().__init__(pixmap)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        
        self._progress = 0
        self._status_text = "Initializing..."
        
        # Fade-in animation
        self._animation = QPropertyAnimation(self, b"windowOpacity")
        self._animation.setDuration(800) # 0.8 seconds
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._animation.start()
        
        # Timer to simulate loading progress
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_progress)
        self._timer.start(50) # Update every 50ms

    def _update_progress(self):
        self._progress += 2
        if self._progress <= 30:
            self._status_text = "Loading modules..."
        elif self._progress <= 60:
            self._status_text = "Checking dependencies..."
        elif self._progress <= 90:
            self._status_text = "Preparing interface..."
        elif self._progress >= 100:
            self._progress = 100
            self._status_text = "Ready."
            self._timer.stop()
            self.close()
            
        self.repaint()

    def drawContents(self, painter: QPainter):
        """Override to draw the dynamic loading bar and text."""
        super().drawContents(painter)
        
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw Loading Text
        painter.setPen(QColor("#858585"))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(
            QRectF(0, 310, 600, 20), 
            Qt.AlignmentFlag.AlignCenter, 
            self._status_text
        )
        
        # Draw Progress Bar Background
        bar_width = 300
        bar_height = 4
        bar_x = (600 - bar_width) / 2
        bar_y = 340
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#2d2d30"))
        painter.drawRoundedRect(QRectF(bar_x, bar_y, bar_width, bar_height), 2, 2)
        
        # Draw Progress Bar Fill
        fill_width = (self._progress / 100.0) * bar_width
        if fill_width > 0:
            painter.setBrush(QColor("#e06c75")) # Ruby Red accent
            painter.drawRoundedRect(QRectF(bar_x, bar_y, fill_width, bar_height), 2, 2)


def main() -> None:
    """Launch the application with the animated splash screen."""
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

        # --- Create Base Splash Pixmap ---
        splash_pix = QPixmap(600, 400)
        splash_pix.fill(QColor("#1e1e1e"))
        
        painter = QPainter(splash_pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Draw Logo
        logo = get_logo_pixmap(120)
        if not logo.isNull():
            x = (600 - logo.width()) // 2
            y = 60
            painter.drawPixmap(x, y, logo)
        
        # Draw Title
        painter.setPen(QColor("#ffffff"))
        title_font = QFont("Segoe UI", 28, QFont.Weight.Bold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        painter.setFont(title_font)
        painter.drawText(splash_pix.rect().adjusted(0, 120, 0, 0), Qt.AlignmentFlag.AlignCenter, "GODOT SHIELD")
        
        # Draw Subtitle
        painter.setPen(QColor("#858585"))
        painter.setFont(QFont("Segoe UI", 12))
        painter.drawText(splash_pix.rect().adjusted(0, 170, 0, 0), Qt.AlignmentFlag.AlignCenter, "Automated Game Protection")
        
        # Draw Version
        painter.setPen(QColor("#555555"))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(splash_pix.rect().adjusted(0, 370, 0, 0), Qt.AlignmentFlag.AlignCenter, "v1.2.0")
        painter.end()

        # --- Show Animated Splash ---
        splash = AnimatedSplashScreen(splash_pix)
        splash.show()
        app.processEvents() 

        # --- Load Main Window ---
        window = MainWindow()
        
        # Show main window after ~2.5 seconds (when loading bar finishes)
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
