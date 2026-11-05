"""
Main PySide6 window for Godot Shield v1.2.0.

A human-crafted, developer-focused UI inspired by modern IDEs.
Features a flat design, a warm dark theme, and a clean sidebar layout.
"""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Slot, QSize
from PySide6.QtGui import QAction, QFont, QIcon
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QVBoxLayout, QWidget, QStackedWidget, QFrame
)

from core.protector import ProtectionResult
from core.utils import find_obfuscator_script, is_valid_godot_project
from gui.widgets import ColoredLogView
from gui.workers import ProtectionWorker

# --- Path Helper for Icons ---
ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"

def get_icon(name: str) -> QIcon:
    path = ICONS_DIR / f"{name}.svg"
    if path.exists():
        return QIcon(str(path))
    return QIcon()

# --- Human-Crafted Dark Theme (No AI Blue, IDE-inspired) ---
DARK_QSS = """
/* Global */
QMainWindow { 
    background-color: #1e1e1e; 
}
QWidget {
    color: #d4d4d4;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}
QLabel { 
    background: transparent; 
}

/* Menu Bar - Flat and Native */
QMenuBar {
    background-color: #1e1e1e;
    color: #d4d4d4;
    padding: 2px;
    border-bottom: 1px solid #333333;
}
QMenuBar::item {
    background: transparent;
    padding: 6px 10px;
}
QMenuBar::item:selected { 
    background-color: #333333; 
    color: #ffffff;
}
QMenu {
    background-color: #252526;
    border: 1px solid #3e3e42;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px 6px 12px;
    color: #d4d4d4;
}
QMenu::item:selected { 
    background-color: #333333; 
    color: #ffffff;
}

/* Sidebar */
QWidget#Sidebar {
    background-color: #181818;
    border-right: 1px solid #2d2d30;
}
QLabel#LogoTitle {
    font-size: 16px;
    font-weight: 700;
    color: #ffffff;
    padding: 20px 10px;
    letter-spacing: 1px;
}
QPushButton#SidebarBtn {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 10px 12px;
    text-align: left;
    font-size: 13px;
    color: #858585;
    icon-size: 16px;
}
QPushButton#SidebarBtn:hover {
    background-color: #252526;
    color: #d4d4d4;
}
QPushButton#SidebarBtn:checked {
    background-color: #2d2d30;
    color: #ffffff;
    border-left: 3px solid #e06c75; /* Warm Ruby Red Accent */
}

/* Pages */
QLabel#PageTitle { 
    font-size: 22px; 
    font-weight: 600; 
    color: #ffffff; 
    margin-bottom: 10px; 
}
QFrame#HLine {
    background-color: #333333;
    max-height: 1px;
    margin: 10px 0;
}

/* Inputs */
QLineEdit, QComboBox {
    background-color: #2d2d30;
    border: 1px solid #3e3e42;
    border-radius: 4px;
    padding: 6px 10px;
    color: #d4d4d4;
    selection-background-color: #e06c75;
}
QLineEdit:focus, QComboBox:focus { 
    border: 1px solid #e06c75; 
}
QComboBox::drop-down { border: none; }

/* Primary Button (Protect) */
QPushButton#PrimaryButton {
    background-color: #e06c75; /* Ruby Red */
    color: #ffffff;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 600;
    padding: 12px;
    icon-size: 18px;
}
QPushButton#PrimaryButton:hover { 
    background-color: #c75b63; 
}
QPushButton#PrimaryButton:disabled { 
    background-color: #4a2a2d; 
    color: #8a5a5d; 
}

/* Secondary Buttons */
QPushButton { 
    background-color: #2d2d30;
    border: 1px solid #3e3e42;
    border-radius: 4px;
    padding: 6px 12px;
    color: #d4d4d4;
    icon-size: 14px;
}
QPushButton:hover { 
    background-color: #3e3e42; 
}
QPushButton:disabled { 
    color: #555555; 
    background-color: #1e1e1e; 
    border: 1px solid #2d2d30;
}

/* Progress Bar */
QProgressBar {
    background-color: #2d2d30;
    border: 1px solid #3e3e42;
    border-radius: 4px;
    text-align: center;
    color: transparent;
    height: 8px;
}
QProgressBar::chunk { 
    background-color: #e06c75; 
    border-radius: 3px;
}

/* Log View */
QPlainTextEdit {
    background-color: #1e1e1e;
    border: 1px solid #333333;
    border-radius: 4px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
    color: #d4d4d4;
    padding: 10px;
    selection-background-color: #3e3e42;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #1e1e1e;
    width: 12px;
}
QScrollBar::handle:vertical {
    background: #3e3e42;
    min-height: 20px;
    border-radius: 6px;
    margin: 2px;
}
QScrollBar::handle:vertical:hover { 
    background: #4e4e52; 
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { 
    height: 0px; 
}
"""

class MainWindow(QMainWindow):
    """Main application window with Sidebar Layout."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Godot Shield v1.2.0")
        self.setMinimumSize(1000, 700)
        self.setWindowIcon(get_icon("shield"))

        self._worker: Optional[ProtectionWorker] = None
        self._project_path: Optional[Path] = None
        self._output_path: Optional[Path] = None

        self._init_ui()
        self._init_menu()
        self._connect_signals()
        self._update_protection_level_ui()

    def _init_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- 1. Sidebar ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 10, 10, 20)
        sidebar_layout.setSpacing(4)

        # Logo
        logo = QLabel("GODOT SHIELD")
        logo.setObjectName("LogoTitle")
        sidebar_layout.addWidget(logo)

        # Nav Buttons
        self.btn_protect_page = QPushButton(" Protect Game")
        self.btn_protect_page.setIcon(get_icon("shield"))
        
        self.btn_logs_page = QPushButton(" Logs")
        self.btn_logs_page.setIcon(get_icon("terminal"))
        
        self.btn_settings_page = QPushButton(" Settings")
        self.btn_settings_page.setIcon(get_icon("settings"))
        
        self.btn_about_page = QPushButton(" About")
        self.btn_about_page.setIcon(get_icon("info"))

        self.nav_buttons = [
            (self.btn_protect_page, 0),
            (self.btn_logs_page, 1),
            (self.btn_settings_page, 2),
            (self.btn_about_page, 3)
        ]

        for btn, idx in self.nav_buttons:
            btn.setObjectName("SidebarBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked=False, i=idx: self._switch_page(i))
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()
        
        version = QLabel("v1.2.0")
        version.setStyleSheet("color: #555; font-size: 11px; padding-left: 12px;")
        sidebar_layout.addWidget(version)

        main_layout.addWidget(self.sidebar)

        # --- 2. Stacked Pages ---
        self.stacked_widget = QStackedWidget()
        
        self.page_protect = self._create_protect_page()
        self.page_logs = self._create_logs_page()
        self.page_settings = self._create_settings_page()
        self.page_about = self._create_about_page()

        self.stacked_widget.addWidget(self.page_protect)
        self.stacked_widget.addWidget(self.page_logs)
        self.stacked_widget.addWidget(self.page_settings)
        self.stacked_widget.addWidget(self.page_about)

        main_layout.addWidget(self.stacked_widget, 1)
        self._switch_page(0)

    def _create_protect_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 30, 40, 30) # More breathing room
        layout.setSpacing(15)

        title = QLabel("Protect Your Game")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # Project Section
        layout.addWidget(QLabel("Godot Project Folder"))
        proj_row = QHBoxLayout()
        self.project_edit = QLineEdit()
        self.project_edit.setReadOnly(True)
        self.project_edit.setPlaceholderText("Select project folder...")
        self.project_browse_btn = QPushButton(" Browse")
        self.project_browse_btn.setIcon(get_icon("folder"))
        proj_row.addWidget(self.project_edit, 1)
        proj_row.addWidget(self.project_browse_btn)
        layout.addLayout(proj_row)
        
        self.invalid_label = QLabel("")
        self.invalid_label.setStyleSheet("color: #e06c75; font-size: 11px;")
        self.invalid_label.setVisible(False)
        layout.addWidget(self.invalid_label)

        layout.addWidget(self._h_line())

        # Options Section (Side by side to save vertical space)
        opts_row = QHBoxLayout()
        
        # Level
        level_col = QVBoxLayout()
        level_col.addWidget(QLabel("Protection Level"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["Basic", "Standard"])
        level_col.addWidget(self.level_combo)
        opts_row.addLayout(level_col, 1)

        # Password
        pass_col = QVBoxLayout()
        pass_col.addWidget(QLabel("Custom Password (Optional)"))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Auto-generate if empty")
        pass_col.addWidget(self.password_edit)
        opts_row.addLayout(pass_col, 1)

        layout.addLayout(opts_row)
        
        self.hint_label = QLabel()
        self.hint_label.setStyleSheet("color: #858585; font-size: 11px;")
        self.hint_label.setWordWrap(True)
        layout.addWidget(self.hint_label)

        layout.addWidget(self._h_line())

        # Output Section
        self.output_label = QLabel("Output Executable (.exe)")
        layout.addWidget(self.output_label)
        out_row = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("Select output path...")
        self.output_browse_btn = QPushButton(" Browse")
        self.output_browse_btn.setIcon(get_icon("folder"))
        out_row.addWidget(self.output_edit, 1)
        out_row.addWidget(self.output_browse_btn)
        layout.addLayout(out_row)

        layout.addSpacing(20)

        # Actions & Progress
        self.protect_btn = QPushButton(" Protect Game")
        self.protect_btn.setIcon(get_icon("play"))
        self.protect_btn.setObjectName("PrimaryButton")
        layout.addWidget(self.protect_btn)

        action_row = QHBoxLayout()
        self.check_btn = QPushButton(" Check Tools")
        self.check_btn.setIcon(get_icon("search"))
        
        self.cancel_btn = QPushButton(" Cancel")
        self.cancel_btn.setIcon(get_icon("x"))
        self.cancel_btn.setEnabled(False)
        
        self.open_folder_btn = QPushButton(" Open Output Folder")
        self.open_folder_btn.setIcon(get_icon("folder-open"))
        self.open_folder_btn.setEnabled(False)
        
        action_row.addWidget(self.check_btn)
        action_row.addWidget(self.cancel_btn)
        action_row.addWidget(self.open_folder_btn)
        layout.addLayout(action_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #858585; font-size: 11px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.status_label)

        layout.addStretch()
        return page

    def _create_logs_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 30, 40, 30)

        header = QHBoxLayout()
        title = QLabel("Process Logs")
        title.setObjectName("PageTitle")
        header.addWidget(title)
        header.addStretch()

        self.save_logs_btn = QPushButton(" Save")
        self.save_logs_btn.setIcon(get_icon("save"))
        self.clear_logs_btn = QPushButton(" Clear")
        self.clear_logs_btn.setIcon(get_icon("trash"))
        
        header.addWidget(self.save_logs_btn)
        header.addWidget(self.clear_logs_btn)
        layout.addLayout(header)

        self.log_view = ColoredLogView()
        mono_font = QFont("Consolas", 10)
        self.log_view.setFont(mono_font)
        layout.addWidget(self.log_view)

        return page

    def _create_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 30, 40, 30)
        title = QLabel("Settings")
        title.setObjectName("PageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel("Settings coming in a future update."))
        layout.addStretch()
        return page

    def _create_about_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 30, 40, 30)
        title = QLabel("About Godot Shield")
        title.setObjectName("PageTitle")
        layout.addWidget(title)
        
        text = QLabel(
            "Godot Shield v1.2.0\nMIT License\n\n"
            "Automated protection for Godot games.\n"
            "Obfuscation + AES-256 PCK Encryption.\n\n"
            "Credits:\n"
            "Obfuscator: June-Tree\n"
            "Engine: Godot Engine"
        )
        text.setStyleSheet("font-size: 13px; line-height: 1.6; color: #a0a0a0;")
        layout.addWidget(text)
        layout.addStretch()
        return page

    def _h_line(self) -> QFrame:
        line = QFrame()
        line.setObjectName("HLine")
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line

    def _switch_page(self, index: int) -> None:
        self.stacked_widget.setCurrentIndex(index)
        for btn, idx in self.nav_buttons:
            btn.setChecked(idx == index)

    def _connect_signals(self) -> None:
        self.project_browse_btn.clicked.connect(self._browse_project)
        self.output_browse_btn.clicked.connect(self._browse_output)
        self.level_combo.currentTextChanged.connect(self._update_protection_level_ui)
        self.protect_btn.clicked.connect(self._start_protection)
        self.cancel_btn.clicked.connect(self._cancel_protection)
        self.check_btn.clicked.connect(self._check_tools)
        self.open_folder_btn.clicked.connect(self._open_output_folder)
        self.clear_logs_btn.clicked.connect(self.log_view.clear_log)
        self.save_logs_btn.clicked.connect(self._save_logs)

    def _init_menu(self) -> None:
        try:
            menubar = self.menuBar()
            
            # File Menu
            file_menu = menubar.addMenu("File")
            clear_action = QAction("Clear Session", self)
            clear_action.triggered.connect(self._clear_session)
            file_menu.addAction(clear_action)
            file_menu.addSeparator()
            exit_action = QAction("Exit", self)
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
            
            # Help Menu
            help_menu = menubar.addMenu("Help")
            about_action = QAction("About", self)
            about_action.triggered.connect(lambda: self._switch_page(3))
            help_menu.addAction(about_action)
            
        except Exception:
            pass

    # --- Logic (Maintained exactly as previous version) ---
    def _update_protection_level_ui(self) -> None:
        level = self.level_combo.currentText()
        if level == "Basic":
            self.hint_label.setText("Basic: Obfuscates GDScript in place (no export).")
            self.output_label.setEnabled(False)
            self.output_edit.setEnabled(False)
            self.output_browse_btn.setEnabled(False)
        else:
            self.hint_label.setText("Standard: Obfuscation + AES-256 encryption + .exe export.")
            self.output_label.setEnabled(True)
            self.output_edit.setEnabled(True)
            self.output_browse_btn.setEnabled(True)
            if self._project_path and not self.output_edit.text():
                default_out = self._project_path / "build" / "game.exe"
                self._output_path = default_out
                self.output_edit.setText(str(default_out))

    def _browse_project(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Godot Project", str(Path.home()))
        if folder:
            path = Path(folder)
            self._project_path = path
            self.project_edit.setText(str(path))
            if not is_valid_godot_project(path):
                self.invalid_label.setText("Invalid: project.godot not found.")
                self.invalid_label.setVisible(True)
            else:
                self.invalid_label.setVisible(False)
                self.log_view.append_colored(f"Selected project: {path}", "info")
                if self.level_combo.currentText() == "Standard" and not self.output_edit.text():
                    default_out = path / "build" / "game.exe"
                    self._output_path = default_out
                    self.output_edit.setText(str(default_out))

    def _browse_output(self) -> None:
        default_dir = str(self._project_path / "build" if self._project_path else Path.home())
        file_path, _ = QFileDialog.getSaveFileName(self, "Select Output", default_dir + "/game.exe", "Executable (*.exe)")
        if file_path:
            self._output_path = Path(file_path)
            self.output_edit.setText(file_path)
            self.log_view.append_colored(f"Selected output: {file_path}", "info")

    def _start_protection(self) -> None:
        if not self._project_path or not is_valid_godot_project(self._project_path):
            QMessageBox.warning(self, "Invalid Project", "Select a valid Godot project folder.")
            return

        self._switch_page(1)
        self.protect_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.open_folder_btn.setEnabled(False)
        self.log_view.clear_log()
        self.progress_bar.setValue(0)

        level = self.level_combo.currentText().lower()
        output = self._output_path if level == "standard" else None
        custom_password = self.password_edit.text().strip() or None

        self._worker = ProtectionWorker(
            project_path=self._project_path,
            level=level,
            output_path=output,
            custom_password=custom_password,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.log.connect(self._on_log)
        self._worker.protection_finished.connect(self._on_finished)
        self._worker.start()

    def _cancel_protection(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self.log_view.append_colored("Cancellation requested.", "warning")

    def _on_progress(self, step: str, percent: int) -> None:
        self.progress_bar.setValue(percent)
        self.status_label.setText(step)

    def _on_log(self, message: str, severity: str) -> None:
        self.log_view.append_colored(message, severity)

    def _on_finished(self, result: ProtectionResult) -> None:
        self.protect_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        if result.success and result.output_path:
            self.open_folder_btn.setEnabled(True)

        if result.success:
            self.progress_bar.setValue(100)
            self.status_label.setText("Success")
            self.log_view.append_colored("=== Protection completed successfully ===", "success")
            QMessageBox.information(self, "Success", "Protection completed successfully!")
        else:
            self.status_label.setText("Failed")
            self.log_view.append_colored(f"Failed: {result.error_message}", "error")
            QMessageBox.critical(self, "Failed", f"Error: {result.error_message}")
        self._worker = None

    def _check_tools(self) -> None:
        self._switch_page(1)
        self.log_view.clear_log()
        self.log_view.append_colored("=== Checking Tools ===", "info")
        from core.utils import find_godot_executable
        godot = find_godot_executable()
        if godot:
            self.log_view.append_colored(f"Godot found: {godot}", "success")
        else:
            self.log_view.append_colored("Godot not found in PATH.", "error")
        obf = find_obfuscator_script()
        if obf:
            self.log_view.append_colored(f"Obfuscator found: {obf}", "success")
        else:
            self.log_view.append_colored("Obfuscator not found.", "error")

    def _open_output_folder(self) -> None:
        if self._output_path and self._output_path.parent.exists():
            self._open_folder(self._output_path.parent)

    def _open_folder(self, folder: Path) -> None:
        system = platform.system()
        if system == "Windows":
            os.startfile(str(folder))
        elif system == "Darwin":
            subprocess.run(["open", str(folder)], check=False)
        else:
            subprocess.run(["xdg-open", str(folder)], check=False)

    def _save_logs(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Logs", "logs.txt", "Text (*.txt)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.log_view.toPlainText())
            self.log_view.append_colored(f"Logs saved: {file_path}", "success")

    def _clear_session(self) -> None:
        self._project_path = None
        self._output_path = None
        self.project_edit.clear()
        self.output_edit.clear()
        self.password_edit.clear()
        self.log_view.clear_log()
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready")
        self.invalid_label.setVisible(False)
        self.open_folder_btn.setEnabled(False)
        self.protect_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.log_view.append_colored("Session cleared. Ready for new project.", "info")
