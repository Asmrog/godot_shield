"""
Custom widgets for Godot Shield GUI.

This module defines reusable UI components: a colored log view that
displays messages with severity-based colors, and a folder/file picker
composite widget.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QTextCharFormat
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QWidget,
)


class ColoredLogView(QPlainTextEdit):
    """
    Read-only log view with colored lines based on severity.

    Supports severities: info (white), success (green), warning (yellow),
    error (red). Uses monospace font for readability.
    """

    # Mapping severity to color
    COLORS = {
        "info": "#D4D4D4",
        "success": "#4EC9B0",
        "warning": "#DCDCAA",
        "error": "#F44747",
    }

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the colored log view.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setReadOnly(True)
        # Set monospace font via stylesheet will be applied, but ensure
        # plain text edit is suitable for logs
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        # Set placeholder
        self.setPlaceholderText("Logs will appear here...")

    def append_colored(self, message: str, severity: str = "info") -> None:
        """
        Append a colored line to the log view.

        Args:
            message: Text to append.
            severity: One of "info", "success", "warning", "error".
        """
        try:
            severity = severity.lower() if severity else "info"
            color_hex = self.COLORS.get(severity, self.COLORS["info"])

            # Create text format with color
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color_hex))

            # Move cursor to end and apply format
            cursor = self.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            cursor.setCharFormat(fmt)
            cursor.insertText(message + "\n")

            # Auto-scroll to bottom
            self.setTextCursor(cursor)
            self.ensureCursorVisible()

        except Exception:
            # Fallback: append without color if formatting fails
            try:
                self.appendPlainText(message)
            except Exception:
                pass

    def clear_log(self) -> None:
        """Clear all log contents."""
        try:
            self.clear()
        except Exception:
            pass


class FolderPicker(QWidget):
    """
    Composite widget: read-only line edit + browse button.

    Emits path_changed signal when a path is selected. Can operate in
    folder mode or file mode (for exe output).
    """

    path_changed = Signal(str)

    def __init__(
        self,
        placeholder: str = "Select a path...",
        mode: str = "folder",
        file_filter: str = "Executable (*.exe);;All Files (*)",
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize FolderPicker.

        Args:
            placeholder: Placeholder text for the line edit.
            mode: Either "folder" or "file". Folder opens directory chooser,
                  file opens file save dialog.
            file_filter: File filter string for file dialog.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self._mode = mode
        self._file_filter = file_filter
        self._current_path: Optional[Path] = None

        # Create UI elements
        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)
        self.line_edit.setPlaceholderText(placeholder)

        self.browse_button = QPushButton("Browse...")

        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.line_edit, 1)
        layout.addWidget(self.browse_button)

        # Connections
        self.browse_button.clicked.connect(self._on_browse)

    def _on_browse(self) -> None:
        """Open file/folder dialog and update path."""
        try:
            from PySide6.QtWidgets import QFileDialog

            selected = ""
            if self._mode == "folder":
                selected = QFileDialog.getExistingDirectory(
                    self, "Select Folder", str(self._current_path or Path.home())
                )
            else:
                # File save dialog
                selected, _ = QFileDialog.getSaveFileName(
                    self,
                    "Select Output File",
                    str(self._current_path or Path.home() / "game.exe"),
                    self._file_filter,
                )

            if selected:
                self.set_path(Path(selected))
        except Exception:
            # Dialog failures should not crash the widget
            pass

    def set_path(self, path: Path | str) -> None:
        """
        Set the current path programmatically.

        Args:
            path: Path to set.
        """
        try:
            p = Path(path)
            self._current_path = p
            self.line_edit.setText(str(p))
            self.path_changed.emit(str(p))
        except Exception:
            pass

    @property
    def path(self) -> Optional[Path]:
        """
        Get the current path.

        Returns:
            Path if set, None otherwise.
        """
        if self._current_path is None:
            text = self.line_edit.text().strip()
            if not text:
                return None
            try:
                return Path(text)
            except Exception:
                return None
        return self._current_path

    def clear(self) -> None:
        """Clear the current path."""
        try:
            self._current_path = None
            self.line_edit.clear()
            self.path_changed.emit("")
        except Exception:
            pass

    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the widget.

        Args:
            enabled: True to enable, False to disable.
        """
        try:
            self.line_edit.setEnabled(enabled)
            self.browse_button.setEnabled(enabled)
        except Exception:
            pass
