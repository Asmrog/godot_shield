"""
Main PySide6 window for Godot Shield.

This module defines the primary GUI: a dark-themed QMainWindow with
project selection, protection level, output configuration, progress,
and colored log view. It orchestrates the ProtectionWorker thread.
"""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.protector import ProtectionResult
from core.utils import find_obfuscator_script, is_valid_godot_project
from gui.widgets import ColoredLogView
from gui.workers import ProtectionWorker

# Dark theme QSS stylesheet
DARK_QSS = """
QMainWindow {
    background-color: #1E1E1E;
}
QWidget {
    background-color: #1E1E1E;
    color: #D4D4D4;
    font-family: "Segoe UI";
    font-size: 12px;
}
QLabel {
    background-color: transparent;
}
QLabel#HeaderTitle {
    font-size: 22px;
    font-weight: bold;
    color: #FFFFFF;
}
QLabel#HeaderSubtitle {
    font-size: 12px;
    color: #A0A0A0;
}
QLabel#InvalidLabel {
    color: #F44747;
    font-size: 11px;
}
QLabel#HintLabel {
    color: #8A8A8A;
    font-size: 11px;
}
QLabel#FooterLabel {
    color: #6A6A6A;
    font-size: 10px;
}
QFrame, QGroupBox {
    background-color: #2C2C2C;
    border: 1px solid #3A3A3A;
    border-radius: 6px;
}
QLineEdit {
    background-color: #2C2C2C;
    border: 1px solid #3A3A3A;
    border-radius: 4px;
    padding: 6px 8px;
    color: #D4D4D4;
}
QLineEdit:focus {
    border: 1px solid #0D99FF;
}
QLineEdit:disabled {
    background-color: #252525;
    color: #6A6A6A;
}
QComboBox {
    background-color: #2C2C2C;
    border: 1px solid #3A3A3A;
    border-radius: 4px;
    padding: 6px 8px;
    min-height: 18px;
}
QComboBox:hover {
    border: 1px solid #0D99FF;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #2C2C2C;
    border: 1px solid #3A3A3A;
    selection-background-color: #0D99FF;
}
QPushButton {
    background-color: #3A3A3A;
    border: 1px solid #4A4A4A;
    border-radius: 6px;
    padding: 8px 16px;
    color: #D4D4D4;
}
QPushButton:hover {
    background-color: #4A4A4A;
    border: 1px solid #5A5A5A;
}
QPushButton:pressed {
    background-color: #2A2A2A;
}
QPushButton:disabled {
    background-color: #252525;
    color: #6A6A6A;
    border: 1px solid #2A2A2A;
}
QPushButton#PrimaryButton {
    background-color: #0D99FF;
    color: #FFFFFF;
    font-weight: bold;
    border: 1px solid #0D99FF;
    padding: 10px 20px;
    font-size: 13px;
}
QPushButton#PrimaryButton:hover {
    background-color: #1AA3FF;
    border: 1px solid #1AA3FF;
}
QPushButton#PrimaryButton:pressed {
    background-color: #0A7ACC;
}
QPushButton#PrimaryButton:disabled {
    background-color: #2A4A5A;
    color: #6A8A9A;
    border: 1px solid #2A4A5A;
}
QProgressBar {
    background-color: #2C2C2C;
    border: 1px solid #3A3A3A;
    border-radius: 4px;
    text-align: center;
    color: #D4D4D4;
    height: 18px;
}
QProgressBar::chunk {
    background-color: #0D99FF;
    border-radius: 3px;
}
QPlainTextEdit {
    background-color: #1E1E1E;
    border: 1px solid #3A3A3A;
    border-radius: 6px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11px;
    color: #D4D4D4;
    padding: 4px;
}
"""


class MainWindow(QMainWindow):
    """Main application window for Godot Shield."""

    def __init__(self) -> None:
        """Initialize the main window and UI."""
        super().__init__()
        self.setWindowTitle("Godot Shield — Game Protection Tool")
        self.setMinimumSize(900, 680)

        # State
        self._worker: Optional[ProtectionWorker] = None
        self._project_path: Optional[Path] = None
        self._output_path: Optional[Path] = None

        # Build UI
        self._init_ui()
        self._init_menu()
        self._connect_signals()
        self._update_protection_level_ui()

    def _init_ui(self) -> None:
        """Build the main layout."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 1. Header
        header_title = QLabel("🛡 Godot Shield")
        header_title.setObjectName("HeaderTitle")
        header_subtitle = QLabel("Protect your Godot games")
        header_subtitle.setObjectName("HeaderSubtitle")
        main_layout.addWidget(header_title)
        main_layout.addWidget(header_subtitle)

        # 2. Project section
        project_label = QLabel("Godot Project Folder:")
        main_layout.addWidget(project_label)

        project_row = QHBoxLayout()
        self.project_edit = QLineEdit()
        self.project_edit.setReadOnly(True)
        self.project_edit.setPlaceholderText("Select your Godot project folder...")
        self.project_browse_btn = QPushButton("Browse...")
        project_row.addWidget(self.project_edit, 1)
        project_row.addWidget(self.project_browse_btn)
        main_layout.addLayout(project_row)

        self.invalid_label = QLabel("")
        self.invalid_label.setObjectName("InvalidLabel")
        self.invalid_label.setVisible(False)
        main_layout.addWidget(self.invalid_label)

        # 3. Protection level
        level_label = QLabel("Protection Level:")
        main_layout.addWidget(level_label)

        self.level_combo = QComboBox()
        self.level_combo.addItems(["Basic", "Standard"])
        main_layout.addWidget(self.level_combo)

        self.hint_label = QLabel()
        self.hint_label.setObjectName("HintLabel")
        self.hint_label.setWordWrap(True)
        main_layout.addWidget(self.hint_label)

        # 4. Output section
        self.output_label = QLabel("Output Executable (.exe):")
        main_layout.addWidget(self.output_label)

        output_row = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("Select output .exe path...")
        self.output_browse_btn = QPushButton("Browse...")
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(self.output_browse_btn)
        main_layout.addLayout(output_row)

        # 5. Action row
        action_row = QHBoxLayout()
        self.protect_btn = QPushButton("Protect Game")
        self.protect_btn.setObjectName("PrimaryButton")
        self.protect_btn.setMinimumHeight(40)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setMinimumHeight(40)
        action_row.addWidget(self.protect_btn, 1)
        action_row.addWidget(self.cancel_btn)
        main_layout.addLayout(action_row)

        # 6. Progress bar + status label
        progress_row = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("HintLabel")
        progress_row.addWidget(self.progress_bar, 1)
        progress_row.addWidget(self.status_label)
        main_layout.addLayout(progress_row)

        # 7. Log view
        log_label = QLabel("Logs:")
        main_layout.addWidget(log_label)
        self.log_view = ColoredLogView()
        mono_font = QFont("Consolas", 10)
        mono_font.setStyleHint(QFont.StyleHint.Monospace)
        self.log_view.setFont(mono_font)
        main_layout.addWidget(self.log_view, 1)

        # 8. Footer
        footer_layout = QHBoxLayout()
        footer_left = QLabel("Godot Shield v1.0.0 — MIT License")
        footer_left.setObjectName("FooterLabel")
        footer_right = QLabel(
            '<a href="https://github.com/June-Tree/Godot-Source-Code-Obfuscator" '
            'style="color:#0D99FF;">Obfuscator: June-Tree/Godot-Source-Code-Obfuscator</a>'
        )
        footer_right.setObjectName("FooterLabel")
        footer_right.setOpenExternalLinks(True)
        footer_layout.addWidget(footer_left)
        footer_layout.addStretch()
        footer_layout.addWidget(footer_right)
        main_layout.addLayout(footer_layout)

    def _init_menu(self) -> None:
        """Create menu bar with File and Help menus."""
        try:
            menubar = self.menuBar()

            file_menu = menubar.addMenu("File")
            exit_action = QAction("Exit", self)
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)

            help_menu = menubar.addMenu("Help")
            about_action = QAction("About", self)
            about_action.triggered.connect(self._show_about)
            help_menu.addAction(about_action)
        except Exception:
            pass

    def _connect_signals(self) -> None:
        """Connect UI signals to slots."""
        try:
            self.project_browse_btn.clicked.connect(self._browse_project)
            self.output_browse_btn.clicked.connect(self._browse_output)
            self.level_combo.currentTextChanged.connect(self._update_protection_level_ui)
            self.protect_btn.clicked.connect(self._start_protection)
            self.cancel_btn.clicked.connect(self._cancel_protection)
        except Exception:
            pass

    def _update_protection_level_ui(self) -> None:
        """Update hint label and enable/disable output section based on level."""
        try:
            level = self.level_combo.currentText()
            if level == "Basic":
                self.hint_label.setText(
                    "Basic: Obfuscates GDScript source code in place (no export). "
                    "Fast, good for testing."
                )
                self.output_label.setEnabled(False)
                self.output_edit.setEnabled(False)
                self.output_browse_btn.setEnabled(False)
            else:
                self.hint_label.setText(
                    "Standard: Obfuscation + AES-256 PCK encryption + export to Windows .exe. "
                    "Requires Godot 4.x and export templates."
                )
                self.output_label.setEnabled(True)
                self.output_edit.setEnabled(True)
                self.output_browse_btn.setEnabled(True)

                if self._project_path and not self.output_edit.text():
                    default_out = self._project_path / "build" / "game.exe"
                    self._output_path = default_out
                    self.output_edit.setText(str(default_out))
        except Exception:
            pass

    def _browse_project(self) -> None:
        """Open folder dialog for project selection."""
        try:
            folder = QFileDialog.getExistingDirectory(
                self, "Select Godot Project Folder", str(Path.home())
            )
            if folder:
                path = Path(folder)
                self._project_path = path
                self.project_edit.setText(str(path))

                if not is_valid_godot_project(path):
                    self.invalid_label.setText(
                        "Invalid: project.godot not found in this folder."
                    )
                    self.invalid_label.setVisible(True)
                else:
                    self.invalid_label.setVisible(False)
                    self.log_view.append_colored(f"Selected project: {path}", "info")

                    if (
                        self.level_combo.currentText() == "Standard"
                        and not self.output_edit.text()
                    ):
                        default_out = path / "build" / "game.exe"
                        self._output_path = default_out
                        self.output_edit.setText(str(default_out))
        except Exception as exc:
            try:
                self.log_view.append_colored(
                    f"Error selecting project folder: {exc}", "error"
                )
            except Exception:
                pass

    def _browse_output(self) -> None:
        """Open save file dialog for output exe."""
        try:
            default_dir = str(
                self._project_path / "build" if self._project_path else Path.home()
            )
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Select Output Executable",
                default_dir + "/game.exe",
                "Executable (*.exe);;All Files (*)",
            )
            if file_path:
                self._output_path = Path(file_path)
                self.output_edit.setText(file_path)
                self.log_view.append_colored(f"Selected output: {file_path}", "info")
        except Exception as exc:
            try:
                self.log_view.append_colored(f"Error selecting output: {exc}", "error")
            except Exception:
                pass

    def _validate_inputs(self) -> bool:
        """Validate inputs before starting protection."""
        try:
            if not self._project_path or not is_valid_godot_project(self._project_path):
                QMessageBox.warning(
                    self,
                    "Invalid Project",
                    "Please select a valid Godot project folder containing project.godot.",
                )
                return False

            obfuscator_script = find_obfuscator_script()
            if obfuscator_script is None:
                QMessageBox.warning(
                    self,
                    "Obfuscator Not Found",
                    "GDScript obfuscator not found.\n\n"
                    "Expected at: obfuscator/scripts/gdscript_obfuscator.py\n\n"
                    "Please run:\n"
                    "git clone https://github.com/June-Tree/Godot-Source-Code-Obfuscator.git obfuscator\n\n"
                    "in the Godot Shield root directory.",
                )
                return False

            if self.level_combo.currentText() == "Standard":
                if not self._output_path:
                    text = self.output_edit.text().strip()
                    if not text:
                        QMessageBox.warning(
                            self,
                            "Missing Output",
                            "Please select an output .exe path for Standard protection.",
                        )
                        return False
                    try:
                        self._output_path = Path(text)
                    except Exception:
                        QMessageBox.warning(self, "Invalid Output", "Output path is invalid.")
                        return False

            return True
        except Exception as exc:
            QMessageBox.critical(
                self, "Validation Error", f"Error validating inputs: {exc}"
            )
            return False

    def _start_protection(self) -> None:
        """Start the protection worker thread."""
        try:
            if not self._validate_inputs():
                return

            self.protect_btn.setEnabled(False)
            self.cancel_btn.setEnabled(True)
            self.project_browse_btn.setEnabled(False)
            self.output_browse_btn.setEnabled(False)
            self.level_combo.setEnabled(False)

            self.progress_bar.setValue(0)
            self.status_label.setText("Starting...")
            self.log_view.clear_log()
            self.log_view.append_colored("=== Starting protection pipeline ===", "info")

            level = self.level_combo.currentText().lower()
            output = self._output_path if level == "standard" else None

            self._worker = ProtectionWorker(
                project_path=self._project_path,
                level=level,
                output_path=output,
            )
            self._worker.progress.connect(self._on_progress)
            self._worker.log.connect(self._on_log)
            self._worker.protection_finished.connect(self._on_finished)
            self._worker.start()

        except Exception as exc:
            self.log_view.append_colored(f"Failed to start protection: {exc}", "error")
            self._reset_ui_after_finish()

    def _cancel_protection(self) -> None:
        """Request cancellation of running worker."""
        try:
            if self._worker and self._worker.isRunning():
                self._worker.cancel()
                self.status_label.setText("Cancelling...")
                self.log_view.append_colored("Cancellation requested by user.", "warning")
                self.cancel_btn.setEnabled(False)
        except Exception as exc:
            self.log_view.append_colored(f"Error cancelling: {exc}", "error")

    @Slot(str, int)
    def _on_progress(self, step: str, percent: int) -> None:
        """Handle progress updates from worker."""
        try:
            self.progress_bar.setValue(percent)
            self.status_label.setText(step)
        except Exception:
            pass

    @Slot(str, str)
    def _on_log(self, message: str, severity: str) -> None:
        """Handle log messages from worker."""
        try:
            self.log_view.append_colored(message, severity)
        except Exception:
            pass

    @Slot(object)
    def _on_finished(self, result: ProtectionResult) -> None:
        """Handle completion of protection pipeline."""
        try:
            self._reset_ui_after_finish()

            if result.success:
                self.progress_bar.setValue(100)
                self.status_label.setText("Protection successful")
                self.log_view.append_colored(
                    "=== Protection completed successfully ===", "success"
                )

                summary = "Protection completed successfully!\n\n"
                summary += f"Obfuscated: {'Yes' if result.obfuscated else 'No'}\n"
                summary += (
                    f"Exported: {'Yes' if result.exported else 'No (basic level or Godot not found)'}\n"
                )
                if result.output_path:
                    summary += f"Output: {result.output_path}\n"

                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Success")
                msg_box.setText(summary)
                msg_box.setIcon(QMessageBox.Icon.Information)

                if result.output_path and result.output_path.exists():
                    open_folder_btn = msg_box.addButton(
                        "Open Folder", QMessageBox.ButtonRole.ActionRole
                    )
                    msg_box.addButton(QMessageBox.StandardButton.Ok)
                    msg_box.exec()
                    if msg_box.clickedButton() == open_folder_btn:
                        self._open_folder(result.output_path.parent)
                else:
                    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                    msg_box.exec()

            else:
                self.status_label.setText("Protection failed")
                self.log_view.append_colored(
                    f"Protection failed: {result.error_message}", "error"
                )
                QMessageBox.critical(
                    self,
                    "Protection Failed",
                    f"Protection failed:\n{result.error_message or 'Unknown error'}\n\n"
                    "Check logs for details.",
                )
        except Exception as exc:
            try:
                self.log_view.append_colored(f"Error handling finish: {exc}", "error")
            except Exception:
                pass
            self._reset_ui_after_finish()

    def _reset_ui_after_finish(self) -> None:
        """Re-enable UI after worker finishes."""
        try:
            self.protect_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
            self.project_browse_btn.setEnabled(True)
            self.output_browse_btn.setEnabled(True)
            self.level_combo.setEnabled(True)
            self._update_protection_level_ui()
            self._worker = None
        except Exception:
            pass

    def _open_folder(self, folder: Path) -> None:
        """Open folder in file explorer (cross-platform)."""
        try:
            folder = Path(folder)
            system = platform.system()
            if system == "Windows":
                os.startfile(str(folder))  # type: ignore[attr-defined]
            elif system == "Darwin":
                subprocess.run(["open", str(folder)], check=False)
            else:
                subprocess.run(["xdg-open", str(folder)], check=False)
            self.log_view.append_colored(f"Opened folder: {folder}", "info")
        except Exception as exc:
            self.log_view.append_colored(f"Failed to open folder {folder}: {exc}", "error")

    def _show_about(self) -> None:
        """Show About dialog."""
        try:
            QMessageBox.about(
                self,
                "About Godot Shield",
                "Godot Shield v0.1.0\n"
                "MIT License\n\n"
                "Automated protection for Godot games — obfuscation + encryption.\n\n"
                "Features:\n"
                "- GDScript obfuscation\n"
                "- AES-256 PCK encryption\n"
                "- Windows export\n\n"
                "Credits:\n"
                "- Obfuscator: June-Tree/Godot-Source-Code-Obfuscator\n"
                "- Engine: Godot Engine\n\n"
                "https://github.com/June-Tree/Godot-Source-Code-Obfuscator\n"
                "https://godotengine.org",
            )
        except Exception:
            pass
