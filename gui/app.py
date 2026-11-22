"""
Main PySide6 window for Godot Shield v1.2.1
"""

from __future__ import annotations

import sys
from pathlib import Path

def resource_path(relative_path):
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(__file__).resolve().parent.parent
    return base_path / relative_path

ICONS_DIR = resource_path("assets/icons")

import os
import platform
import subprocess
import webbrowser
from typing import Optional

from PySide6.QtCore import Qt, Slot, QSize, QSettings
from PySide6.QtGui import QAction, QFont, QIcon
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QProgressBar, QPushButton, QSpinBox,
    QVBoxLayout, QWidget, QStackedWidget, QFrame, QFormLayout
)

from core.i18n import APP_VERSION, LANGUAGE_OPTIONS, SUPPORTED_LANGUAGES, get_text
from core.protector import ProtectionResult
from core.updater import FALLBACK_RELEASE_URL
from core.utils import (
    bool_from_setting,
    find_obfuscator_script,
    int_from_setting,
    is_valid_godot_project,
)
from gui.widgets import ColoredLogView
from gui.workers import ProtectionWorker, UpdateCheckerWorker


def rtl_qss(qss: str) -> str:
    """Mirror the directional bits of a stylesheet for right-to-left layouts."""
    return (
        qss.replace("text-align: left", "text-align: __ALIGN__")
           .replace("border-right:", "border-__SIDE__:")
           .replace("border-left:", "border-right:")
           .replace("border-__SIDE__:", "border-left:")
           .replace("padding: 6px 24px 6px 12px", "padding: 6px 12px 6px 24px")
           .replace("text-align: __ALIGN__", "text-align: right")
    )


def tr(key: str, lang: str = "en") -> str:
    """Shortcut used while widgets are first being constructed."""
    return get_text(lang, key)

def get_icon(name: str) -> QIcon:
    path = ICONS_DIR / f"{name}.svg"
    if path.exists():
        return QIcon(str(path))
    return QIcon()

# --- Human-Crafted Dark Theme (Ruby Red Accent) ---
DARK_QSS = """
QMainWindow { background-color: #1e1e1e; }
QWidget { color: #d4d4d4; font-family: "Segoe UI", "Inter", sans-serif; font-size: 13px; }
QLabel { background: transparent; }

QMenuBar { background-color: #1e1e1e; color: #d4d4d4; padding: 2px; border-bottom: 1px solid #333333; }
QMenuBar::item { background: transparent; padding: 6px 10px; }
QMenuBar::item:selected { background-color: #333333; color: #ffffff; }
QMenu { background-color: #252526; border: 1px solid #3e3e42; padding: 4px; }
QMenu::item { padding: 6px 24px 6px 12px; color: #d4d4d4; }
QMenu::item:selected { background-color: #333333; color: #ffffff; }

QWidget#Sidebar { background-color: #181818; border-right: 1px solid #2d2d30; }
QLabel#LogoTitle { font-size: 16px; font-weight: 700; color: #ffffff; padding: 20px 10px; letter-spacing: 1px; }
QPushButton#SidebarBtn { background-color: transparent; border: none; border-radius: 4px; padding: 10px 12px; text-align: left; font-size: 13px; color: #858585; icon-size: 16px; }
QPushButton#SidebarBtn:hover { background-color: #252526; color: #d4d4d4; }
QPushButton#SidebarBtn:checked { background-color: #2d2d30; color: #ffffff; border-left: 3px solid #e06c75; }

QLabel#PageTitle { font-size: 22px; font-weight: 600; color: #ffffff; margin-bottom: 10px; }
QFrame#HLine { background-color: #333333; max-height: 1px; margin: 10px 0; }

QLineEdit, QComboBox { background-color: #2d2d30; border: 1px solid #3e3e42; border-radius: 4px; padding: 6px 10px; color: #d4d4d4; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #e06c75; }
QComboBox::drop-down { border: none; }

QPushButton#PrimaryButton { background-color: #e06c75; color: #ffffff; border: none; border-radius: 4px; font-size: 14px; font-weight: 600; padding: 12px; icon-size: 18px; }
QPushButton#PrimaryButton:hover { background-color: #c75b63; }
QPushButton#PrimaryButton:disabled { background-color: #4a2a2d; color: #8a5a5d; }

QPushButton { background-color: #2d2d30; border: 1px solid #3e3e42; border-radius: 4px; padding: 6px 12px; color: #d4d4d4; icon-size: 14px; }
QPushButton:hover { background-color: #3e3e42; }
QPushButton:disabled { color: #555555; background-color: #1e1e1e; border: 1px solid #2d2d30; }
QPushButton#DangerButton { background-color: #8b2635; border: 1px solid #a13042; color: #ffffff; }
QPushButton#DangerButton:hover { background-color: #a13042; }

QProgressBar { background-color: #2d2d30; border: 1px solid #3e3e42; border-radius: 4px; text-align: center; color: transparent; height: 8px; }
QProgressBar::chunk { background-color: #e06c75; border-radius: 3px; }

QPlainTextEdit { background-color: #1e1e1e; border: 1px solid #333333; border-radius: 4px; font-family: "Consolas", monospace; color: #d4d4d4; padding: 10px; }
"""

# --- Human-Crafted Light Theme (Soft Grays, Dark Text) ---
LIGHT_QSS = """
QMainWindow { background-color: #ffffff; }
QWidget { color: #333333; font-family: "Segoe UI", "Inter", sans-serif; font-size: 13px; }
QLabel { background: transparent; }

QMenuBar { background-color: #ffffff; color: #333333; padding: 2px; border-bottom: 1px solid #e5e5e5; }
QMenuBar::item { background: transparent; padding: 6px 10px; }
QMenuBar::item:selected { background-color: #f0f0f0; color: #000000; }
QMenu { background-color: #ffffff; border: 1px solid #e5e5e5; padding: 4px; }
QMenu::item { padding: 6px 24px 6px 12px; color: #333333; }
QMenu::item:selected { background-color: #f0f0f0; color: #000000; }

QWidget#Sidebar { background-color: #f8f8f8; border-right: 1px solid #e5e5e5; }
QLabel#LogoTitle { font-size: 16px; font-weight: 700; color: #111111; padding: 20px 10px; letter-spacing: 1px; }
QPushButton#SidebarBtn { background-color: transparent; border: none; border-radius: 4px; padding: 10px 12px; text-align: left; font-size: 13px; color: #666666; icon-size: 16px; }
QPushButton#SidebarBtn:hover { background-color: #eaeaea; color: #111111; }
QPushButton#SidebarBtn:checked { background-color: #e0e0e0; color: #111111; border-left: 3px solid #e06c75; }

QLabel#PageTitle { font-size: 22px; font-weight: 600; color: #111111; margin-bottom: 10px; }
QFrame#HLine { background-color: #e5e5e5; max-height: 1px; margin: 10px 0; }

QLineEdit, QComboBox { background-color: #ffffff; border: 1px solid #cccccc; border-radius: 4px; padding: 6px 10px; color: #333333; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #e06c75; }
QComboBox::drop-down { border: none; }

QPushButton#PrimaryButton { background-color: #e06c75; color: #ffffff; border: none; border-radius: 4px; font-size: 14px; font-weight: 600; padding: 12px; icon-size: 18px; }
QPushButton#PrimaryButton:hover { background-color: #c75b63; }
QPushButton#PrimaryButton:disabled { background-color: #f0c8cc; color: #ffffff; }

QPushButton { background-color: #f0f0f0; border: 1px solid #cccccc; border-radius: 4px; padding: 6px 12px; color: #333333; icon-size: 14px; }
QPushButton:hover { background-color: #e0e0e0; }
QPushButton:disabled { color: #999999; background-color: #f8f8f8; border: 1px solid #e5e5e5; }
QPushButton#DangerButton { background-color: #c0392b; border: 1px solid #a93226; color: #ffffff; }
QPushButton#DangerButton:hover { background-color: #a93226; }

QProgressBar { background-color: #f0f0f0; border: 1px solid #cccccc; border-radius: 4px; text-align: center; color: transparent; height: 8px; }
QProgressBar::chunk { background-color: #e06c75; border-radius: 3px; }

QPlainTextEdit { background-color: #1e1e1e; border: 1px solid #333333; border-radius: 4px; font-family: "Consolas", monospace; color: #d4d4d4; padding: 10px; }
"""

class MainWindow(QMainWindow):
    """Main application window with Sidebar Layout."""

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(1000, 700)
        self.setWindowIcon(get_icon("shield"))

        self._worker: Optional[ProtectionWorker] = None
        self._update_worker: Optional[UpdateCheckerWorker] = None
        self._project_path: Optional[Path] = None
        self._output_path: Optional[Path] = None
        self._status_key = "ready"

        # Settings Manager (Saves to registry/ini automatically)
        self.settings = QSettings("Asmrog", "GodotShield")
        saved_lang = str(self.settings.value("language", "en") or "en")
        self.current_lang = saved_lang if saved_lang in SUPPORTED_LANGUAGES else "en"
        self._ensure_default_settings()

        self._init_ui()
        self._init_menu()
        self._connect_signals()
        self._load_theme()
        self.update_ui_language()
        self._update_protection_level_ui()
        # Kick off the optional startup update check once the UI is ready.
        self._start_update_check(manual=False)

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

        self.logo_label = QLabel(tr("app_title_short", self.current_lang))
        self.logo_label.setObjectName("LogoTitle")
        sidebar_layout.addWidget(self.logo_label)

        self.btn_protect_page = QPushButton(" " + tr("protect_game", self.current_lang))
        self.btn_protect_page.setIcon(get_icon("shield"))
        self.btn_logs_page = QPushButton(" " + tr("logs", self.current_lang))
        self.btn_logs_page.setIcon(get_icon("terminal"))
        self.btn_settings_page = QPushButton(" " + tr("settings", self.current_lang))
        self.btn_settings_page.setIcon(get_icon("settings"))
        self.btn_about_page = QPushButton(" " + tr("about", self.current_lang))
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
        
        self.version_label = QLabel(APP_VERSION)
        self.version_label.setObjectName("VersionLabel")
        self.version_label.setStyleSheet("color: #888; font-size: 11px; padding-left: 12px;")
        sidebar_layout.addWidget(self.version_label)

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
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(15)

        self.page_protect_title = QLabel(tr("page_protect_title", self.current_lang))
        self.page_protect_title.setObjectName("PageTitle")
        layout.addWidget(self.page_protect_title)

        self.project_folder_label = QLabel(tr("project_folder", self.current_lang))
        layout.addWidget(self.project_folder_label)
        proj_row = QHBoxLayout()
        self.project_edit = QLineEdit()
        self.project_edit.setReadOnly(True)
        self.project_edit.setPlaceholderText(tr("select_project", self.current_lang))
        self.project_browse_btn = QPushButton(" " + tr("browse", self.current_lang))
        self.project_browse_btn.setIcon(get_icon("folder"))
        proj_row.addWidget(self.project_edit, 1)
        proj_row.addWidget(self.project_browse_btn)
        layout.addLayout(proj_row)
        
        self.invalid_label = QLabel("")
        self.invalid_label.setStyleSheet("color: #e06c75; font-size: 11px;")
        self.invalid_label.setVisible(False)
        layout.addWidget(self.invalid_label)

        layout.addWidget(self._h_line())

        opts_row = QHBoxLayout()
        level_col = QVBoxLayout()
        self.protection_level_label = QLabel(tr("protection_level", self.current_lang))
        level_col.addWidget(self.protection_level_label)
        self.level_combo = QComboBox()
        self.level_combo.addItem(tr("basic", self.current_lang), "basic")
        self.level_combo.addItem(tr("standard", self.current_lang), "standard")
        level_col.addWidget(self.level_combo)
        opts_row.addLayout(level_col, 1)

        pass_col = QVBoxLayout()
        self.password_label = QLabel(tr("custom_password", self.current_lang))
        pass_col.addWidget(self.password_label)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText(tr("auto_generate", self.current_lang))
        pass_col.addWidget(self.password_edit)
        opts_row.addLayout(pass_col, 1)

        layout.addLayout(opts_row)
        
        self.hint_label = QLabel()
        self.hint_label.setStyleSheet("color: #858585; font-size: 11px;")
        self.hint_label.setWordWrap(True)
        layout.addWidget(self.hint_label)

        layout.addWidget(self._h_line())

        self.output_label = QLabel(tr("output_exe", self.current_lang))
        layout.addWidget(self.output_label)
        out_row = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText(tr("select_output", self.current_lang))
        self.output_browse_btn = QPushButton(" " + tr("browse", self.current_lang))
        self.output_browse_btn.setIcon(get_icon("folder"))
        out_row.addWidget(self.output_edit, 1)
        out_row.addWidget(self.output_browse_btn)
        layout.addLayout(out_row)

        layout.addSpacing(20)

        self.protect_btn = QPushButton(" " + tr("protect_game", self.current_lang))
        self.protect_btn.setIcon(get_icon("play"))
        self.protect_btn.setObjectName("PrimaryButton")
        layout.addWidget(self.protect_btn)

        action_row = QHBoxLayout()
        self.check_btn = QPushButton(" " + tr("check_tools", self.current_lang))
        self.check_btn.setIcon(get_icon("search"))
        self.cancel_btn = QPushButton(" " + tr("cancel", self.current_lang))
        self.cancel_btn.setIcon(get_icon("x"))
        self.cancel_btn.setEnabled(False)
        self.open_folder_btn = QPushButton(" " + tr("open_output_folder", self.current_lang))
        self.open_folder_btn.setIcon(get_icon("folder-open"))
        self.open_folder_btn.setEnabled(False)
        
        action_row.addWidget(self.check_btn)
        action_row.addWidget(self.cancel_btn)
        action_row.addWidget(self.open_folder_btn)
        layout.addLayout(action_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel(tr("ready", self.current_lang))
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
        self.page_logs_title = QLabel(tr("page_logs_title", self.current_lang))
        self.page_logs_title.setObjectName("PageTitle")
        header.addWidget(self.page_logs_title)
        header.addStretch()

        self.save_logs_btn = QPushButton(" " + tr("save", self.current_lang))
        self.save_logs_btn.setIcon(get_icon("save"))
        self.clear_logs_btn = QPushButton(" " + tr("clear", self.current_lang))
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
        layout.setSpacing(20)

        self.page_settings_title = QLabel(tr("settings", self.current_lang))
        self.page_settings_title.setObjectName("PageTitle")
        layout.addWidget(self.page_settings_title)

        settings_group = QWidget()
        form = QFormLayout(settings_group)
        form.setContentsMargins(0, 0, 0, 0)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem(tr("dark", self.current_lang), "dark")
        self.theme_combo.addItem(tr("light", self.current_lang), "light")
        self.settings_theme_label = QLabel(tr("settings_theme", self.current_lang) + ":")
        form.addRow(self.settings_theme_label, self.theme_combo)

        self.language_combo = QComboBox()
        for code, label in LANGUAGE_OPTIONS:
            self.language_combo.addItem(label, code)
        self.settings_language_label = QLabel(tr("settings_language", self.current_lang) + ":")
        form.addRow(self.settings_language_label, self.language_combo)

        self.backup_check = QCheckBox(tr("settings_backup", self.current_lang))
        self.backup_check.setChecked(bool_from_setting(self.settings.value("auto_backup", True)))
        form.addRow(self.backup_check)

        self.splash_check = QCheckBox(tr("settings_splash", self.current_lang))
        self.splash_check.setChecked(bool_from_setting(self.settings.value("show_splash", True)))
        form.addRow(self.splash_check)

        self.updates_check = QCheckBox(tr("settings_check_updates", self.current_lang))
        self.updates_check.setChecked(bool_from_setting(self.settings.value("check_updates", True)))
        form.addRow(self.updates_check)

        self.check_updates_now_btn = QPushButton(" " + tr("check_updates_now", self.current_lang))
        self.check_updates_now_btn.setIcon(get_icon("search"))
        form.addRow(self.check_updates_now_btn)

        # Custom Godot executable path (empty means use the system PATH).
        self.settings_godot_path_label = QLabel(
            tr("settings_godot_path", self.current_lang) + ":"
        )
        self.godot_path_edit = QLineEdit()
        self.godot_path_edit.setReadOnly(True)
        self.godot_path_edit.setText(str(self.settings.value("godot_path", "") or ""))
        self.godot_path_edit.setPlaceholderText(tr("settings_godot_path_hint", self.current_lang))
        self.godot_path_edit.setToolTip(tr("settings_godot_path_hint", self.current_lang))
        self.godot_browse_btn = QPushButton(" " + tr("browse", self.current_lang))
        self.godot_browse_btn.setIcon(get_icon("folder"))
        godot_field = QWidget()
        godot_row = QHBoxLayout(godot_field)
        godot_row.setContentsMargins(0, 0, 0, 0)
        godot_row.addWidget(self.godot_path_edit, 1)
        godot_row.addWidget(self.godot_browse_btn)
        form.addRow(self.settings_godot_path_label, godot_field)

        # Obfuscator-generated identifier length.
        self.settings_name_length_label = QLabel(
            tr("settings_name_length", self.current_lang) + ":"
        )
        self.name_length_spin = QSpinBox()
        self.name_length_spin.setRange(3, 20)
        self.name_length_spin.setValue(
            int_from_setting(self.settings.value("name_length", 8), 8, 3, 20)
        )
        form.addRow(self.settings_name_length_label, self.name_length_spin)

        # Default folder used for standard-level exports.
        self.settings_default_output_label = QLabel(
            tr("settings_default_output", self.current_lang) + ":"
        )
        self.default_output_edit = QLineEdit()
        self.default_output_edit.setReadOnly(True)
        self.default_output_edit.setText(str(self.settings.value("default_output", "") or ""))
        self.default_output_edit.setPlaceholderText(tr("select_output", self.current_lang))
        self.default_output_browse_btn = QPushButton(" " + tr("browse", self.current_lang))
        self.default_output_browse_btn.setIcon(get_icon("folder"))
        output_field = QWidget()
        output_row = QHBoxLayout(output_field)
        output_row.setContentsMargins(0, 0, 0, 0)
        output_row.addWidget(self.default_output_edit, 1)
        output_row.addWidget(self.default_output_browse_btn)
        form.addRow(self.settings_default_output_label, output_field)

        form.addRow(self._h_line())
        self.reset_btn = QPushButton(" " + tr("settings_reset", self.current_lang))
        self.reset_btn.setObjectName("DangerButton")
        form.addRow(self.reset_btn)

        layout.addWidget(settings_group)
        layout.addWidget(self._h_line())
        self.more_settings_label = QLabel(tr("more_settings", self.current_lang))
        layout.addWidget(self.more_settings_label)

        layout.addStretch()
        return page

    def _create_about_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 30, 40, 30)
        self.page_about_title = QLabel(tr("about_title", self.current_lang))
        self.page_about_title.setObjectName("PageTitle")
        layout.addWidget(self.page_about_title)

        self.about_text_label = QLabel(
            tr("about_text", self.current_lang).format(version=APP_VERSION)
        )
        self.about_text_label.setStyleSheet("font-size: 13px; line-height: 1.6; color: #888888;")
        self.about_text_label.setWordWrap(True)
        layout.addWidget(self.about_text_label)
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
        self.level_combo.currentIndexChanged.connect(self._update_protection_level_ui)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        self.backup_check.toggled.connect(self._on_backup_toggled)
        self.splash_check.toggled.connect(self._on_splash_toggled)
        self.updates_check.toggled.connect(self._on_updates_toggled)
        self.check_updates_now_btn.clicked.connect(self._check_updates_now)
        self.godot_browse_btn.clicked.connect(self._browse_godot_path)
        self.name_length_spin.valueChanged.connect(self._on_name_length_changed)
        self.default_output_browse_btn.clicked.connect(self._browse_default_output)
        self.reset_btn.clicked.connect(self._on_reset_settings)
        self.protect_btn.clicked.connect(self._start_protection)
        self.cancel_btn.clicked.connect(self._cancel_protection)
        self.check_btn.clicked.connect(self._check_tools)
        self.open_folder_btn.clicked.connect(self._open_output_folder)
        self.clear_logs_btn.clicked.connect(self.log_view.clear_log)
        self.save_logs_btn.clicked.connect(self._save_logs)

    def _init_menu(self) -> None:
        try:
            menubar = self.menuBar()
            self.menu_file = menubar.addMenu(tr("menu_file", self.current_lang))
            self.clear_action = QAction(tr("menu_clear_session", self.current_lang), self)
            self.clear_action.triggered.connect(self._clear_session)
            self.menu_file.addAction(self.clear_action)
            self.menu_file.addSeparator()
            self.exit_action = QAction(tr("menu_exit", self.current_lang), self)
            self.exit_action.triggered.connect(self.close)
            self.menu_file.addAction(self.exit_action)

            self.menu_help = menubar.addMenu(tr("menu_help", self.current_lang))
            self.about_action = QAction(tr("about", self.current_lang), self)
            self.about_action.triggered.connect(lambda: self._switch_page(3))
            self.menu_help.addAction(self.about_action)
        except Exception:
            pass

    # --- Theme, language and settings logic ---
    def _ensure_default_settings(self) -> None:
        """Persist first-run defaults without overwriting any saved preference."""
        defaults = {
            "language": self.current_lang,
            "theme": "dark",
            "auto_backup": True,
            "show_splash": True,
            "check_updates": True,
            "godot_path": "",
            "name_length": 8,
            "default_output": "",
        }
        for key, value in defaults.items():
            if not self.settings.contains(key):
                self.settings.setValue(key, value)

    def _load_theme(self) -> None:
        """Loads the saved theme; legacy "Dark"/"Light" values are accepted."""
        saved = str(self.settings.value("theme", "dark") or "dark").lower()
        if saved not in ("dark", "light"):
            saved = "dark"
        index = self.theme_combo.findData(saved)
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentIndex(index if index >= 0 else 0)
        self.theme_combo.blockSignals(False)
        self._apply_theme(saved)

    def _on_theme_changed(self, _index: int = 0) -> None:
        theme = self.theme_combo.currentData() or "dark"
        self._apply_theme(theme)
        self.settings.setValue("theme", theme)

    def _apply_theme(self, theme_name: str) -> None:
        qss = LIGHT_QSS if theme_name == "light" else DARK_QSS
        if self.current_lang == "ar":
            qss = rtl_qss(qss)
        self.setStyleSheet(qss)

    def _on_language_changed(self, _index: int = 0) -> None:
        code = self.language_combo.currentData()
        if code not in SUPPORTED_LANGUAGES:
            code = "en"
        self.current_lang = code
        self.settings.setValue("language", code)
        self.update_ui_language()

    def _on_backup_toggled(self, checked: bool) -> None:
        self.settings.setValue("auto_backup", bool(checked))

    def _on_splash_toggled(self, checked: bool) -> None:
        self.settings.setValue("show_splash", bool(checked))

    def _on_updates_toggled(self, checked: bool) -> None:
        self.settings.setValue("check_updates", bool(checked))

    def _check_updates_now(self) -> None:
        self._start_update_check(manual=True)

    def _start_update_check(self, manual: bool = False) -> None:
        if not manual and not bool_from_setting(self.settings.value("check_updates", True)):
            return
        if self._update_worker is not None and self._update_worker.isRunning():
            return
        self.check_updates_now_btn.setEnabled(False)
        worker = UpdateCheckerWorker(current_version=APP_VERSION, manual=manual)
        self._update_worker = worker
        worker.update_checked.connect(
            lambda result, is_manual=manual: self._on_update_checked(result, is_manual)
        )
        worker.finished.connect(
            lambda w=worker: self._on_update_worker_finished(w)
        )
        worker.start()

    def _on_update_worker_finished(self, worker: UpdateCheckerWorker) -> None:
        self.check_updates_now_btn.setEnabled(True)
        if self._update_worker is worker:
            self._update_worker = None

    def _on_update_checked(self, result, manual: bool = False) -> None:
        t = lambda key: get_text(self.current_lang, key)

        # Startup checks stay silent unless something new is actually available.
        if getattr(result, "error", None):
            if manual:
                QMessageBox.warning(self, t("update_error_title"), t("update_error_msg"))
            return

        if not getattr(result, "available", False):
            if manual:
                QMessageBox.information(self, t("update_latest_title"), t("update_latest_msg"))
            return

        latest = getattr(result, "latest_version", "") or ""
        url = getattr(result, "release_url", "") or FALLBACK_RELEASE_URL
        answer = QMessageBox.question(
            self,
            t("update_available_title"),
            t("update_available_msg").format(latest=latest),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            try:
                webbrowser.open(url)
            except Exception:
                pass

    def _browse_godot_path(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            get_text(self.current_lang, "settings_godot_path"),
            str(Path.home()),
            "Executable (*.exe);;All Files (*)",
        )
        if path:
            self.godot_path_edit.setText(path)
            self.settings.setValue("godot_path", path)

    def _on_name_length_changed(self, value: int) -> None:
        self.settings.setValue("name_length", int(value))

    def _browse_default_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            get_text(self.current_lang, "settings_default_output"),
            str(Path.home()),
        )
        if folder:
            self.default_output_edit.setText(folder)
            self.settings.setValue("default_output", folder)
            if (
                self._project_path
                and self.level_combo.currentData() == "standard"
                and not self.output_edit.text()
            ):
                self._apply_default_output_path(self._project_path)

    def _default_output_path(self, project: Path) -> Path:
        folder = str(self.settings.value("default_output", "") or "").strip()
        if folder:
            return Path(folder).expanduser() / f"{project.name}.exe"
        return project / "build" / "game.exe"

    def _apply_default_output_path(self, project: Path) -> None:
        default_out = self._default_output_path(project)
        self._output_path = default_out
        self.output_edit.setText(str(default_out))

    def _on_reset_settings(self) -> None:
        answer = QMessageBox.question(
            self,
            get_text(self.current_lang, "settings_reset"),
            get_text(self.current_lang, "reset_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.settings.clear()
        self.settings.sync()
        QMessageBox.information(
            self,
            get_text(self.current_lang, "settings_reset"),
            get_text(self.current_lang, "reset_success"),
        )
        self.close()

    def update_ui_language(self) -> None:
        """Refresh every translated element and mirror the layout for Arabic."""
        lang = self.current_lang
        rtl = lang == "ar"
        t = lambda key: get_text(lang, key)

        direction = Qt.LayoutDirection.RightToLeft if rtl else Qt.LayoutDirection.LeftToRight
        self.setLayoutDirection(direction)
        if self.centralWidget() is not None:
            self.centralWidget().setLayoutDirection(direction)
        menubar = self.menuBar()
        if menubar is not None:
            menubar.setLayoutDirection(direction)

        self.setWindowTitle(f"{t('app_title')} {APP_VERSION}")
        self.logo_label.setText(t("app_title_short"))
        self.version_label.setText(APP_VERSION)
        self.version_label.setStyleSheet(
            "color: #888; font-size: 11px; "
            + ("padding-right: 12px;" if rtl else "padding-left: 12px;")
        )

        self.btn_protect_page.setText(" " + t("protect_game"))
        self.btn_logs_page.setText(" " + t("logs"))
        self.btn_settings_page.setText(" " + t("settings"))
        self.btn_about_page.setText(" " + t("about"))

        self.page_protect_title.setText(t("page_protect_title"))
        self.project_folder_label.setText(t("project_folder"))
        self.project_edit.setPlaceholderText(t("select_project"))
        self.project_browse_btn.setText(" " + t("browse"))
        self.protection_level_label.setText(t("protection_level"))
        self.password_label.setText(t("custom_password"))
        self.password_edit.setPlaceholderText(t("auto_generate"))
        self.output_label.setText(t("output_exe"))
        self.output_edit.setPlaceholderText(t("select_output"))
        self.output_browse_btn.setText(" " + t("browse"))
        self.protect_btn.setText(" " + t("protect_game"))
        self.check_btn.setText(" " + t("check_tools"))
        self.cancel_btn.setText(" " + t("cancel"))
        self.open_folder_btn.setText(" " + t("open_output_folder"))

        self.page_logs_title.setText(t("page_logs_title"))
        self.save_logs_btn.setText(" " + t("save"))
        self.clear_logs_btn.setText(" " + t("clear"))

        self.page_settings_title.setText(t("settings"))
        self.settings_theme_label.setText(t("settings_theme") + ":")
        self.settings_language_label.setText(t("settings_language") + ":")
        self.backup_check.setText(t("settings_backup"))
        self.splash_check.setText(t("settings_splash"))
        self.updates_check.setText(t("settings_check_updates"))
        self.check_updates_now_btn.setText(" " + t("check_updates_now"))
        self.settings_godot_path_label.setText(t("settings_godot_path") + ":")
        self.godot_path_edit.setPlaceholderText(t("settings_godot_path_hint"))
        self.godot_path_edit.setToolTip(t("settings_godot_path_hint"))
        self.godot_browse_btn.setText(" " + t("browse"))
        self.settings_name_length_label.setText(t("settings_name_length") + ":")
        self.settings_default_output_label.setText(t("settings_default_output") + ":")
        self.default_output_edit.setPlaceholderText(t("select_output"))
        self.default_output_browse_btn.setText(" " + t("browse"))
        self.reset_btn.setText(" " + t("settings_reset"))
        self.more_settings_label.setText(t("more_settings"))

        self.page_about_title.setText(t("about_title"))
        self.about_text_label.setText(t("about_text").format(version=APP_VERSION))

        if hasattr(self, "menu_file"):
            self.menu_file.setTitle(t("menu_file"))
            self.menu_help.setTitle(t("menu_help"))
            self.clear_action.setText(t("menu_clear_session"))
            self.exit_action.setText(t("menu_exit"))
            self.about_action.setText(t("about"))

        # Rebuild the value-based combos without losing the current selection.
        current_level = self.level_combo.currentData() or "basic"
        self.level_combo.blockSignals(True)
        self.level_combo.clear()
        self.level_combo.addItem(t("basic"), "basic")
        self.level_combo.addItem(t("standard"), "standard")
        index = self.level_combo.findData(current_level)
        self.level_combo.setCurrentIndex(index if index >= 0 else 0)
        self.level_combo.blockSignals(False)

        current_theme = self.theme_combo.currentData() or "dark"
        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()
        self.theme_combo.addItem(t("dark"), "dark")
        self.theme_combo.addItem(t("light"), "light")
        index = self.theme_combo.findData(current_theme)
        self.theme_combo.setCurrentIndex(index if index >= 0 else 0)
        self.theme_combo.blockSignals(False)

        index = self.language_combo.findData(lang)
        self.language_combo.blockSignals(True)
        self.language_combo.setCurrentIndex(index if index >= 0 else 0)
        self.language_combo.blockSignals(False)

        # Mirror static text alignment so labels never crowd the sidebar edge.
        text_align = Qt.AlignmentFlag.AlignRight if rtl else Qt.AlignmentFlag.AlignLeft
        for label in (
            self.page_protect_title, self.page_logs_title, self.page_settings_title,
            self.page_about_title, self.about_text_label, self.hint_label,
            self.invalid_label, self.logo_label,
        ):
            label.setAlignment(text_align)
        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft if rtl else Qt.AlignmentFlag.AlignRight
        )
        if self._status_key in ("ready", "status_success", "status_failed"):
            self.status_label.setText(t(self._status_key))

        self._apply_theme(self.theme_combo.currentData() or "dark")
        # The level hint is translated here too, not just the widgets above.
        self._update_protection_level_ui()

    # --- Logic (Maintained) ---
    def _update_protection_level_ui(self) -> None:
        level = self.level_combo.currentData() or "basic"
        if level == "basic":
            self.hint_label.setText(get_text(self.current_lang, "hint_basic"))
            self.output_label.setEnabled(False)
            self.output_edit.setEnabled(False)
            self.output_browse_btn.setEnabled(False)
        else:
            self.hint_label.setText(get_text(self.current_lang, "hint_standard"))
            self.output_label.setEnabled(True)
            self.output_edit.setEnabled(True)
            self.output_browse_btn.setEnabled(True)
            if self._project_path and not self.output_edit.text():
                self._apply_default_output_path(self._project_path)

    def _browse_project(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, get_text(self.current_lang, "project_folder"), str(Path.home())
        )
        if folder:
            path = Path(folder)
            self._project_path = path
            self.project_edit.setText(str(path))
            if not is_valid_godot_project(path):
                self.invalid_label.setText(get_text(self.current_lang, "invalid_project"))
                self.invalid_label.setVisible(True)
            else:
                self.invalid_label.setVisible(False)
                self.log_view.append_colored(f"Selected project: {path}", "info")
                if self.level_combo.currentData() == "standard" and not self.output_edit.text():
                    self._apply_default_output_path(path)

    def _browse_output(self) -> None:
        default_dir = str(self._project_path / "build" if self._project_path else Path.home())
        file_path, _ = QFileDialog.getSaveFileName(
            self, get_text(self.current_lang, "select_output"),
            default_dir + "/game.exe", "Executable (*.exe)"
        )
        if file_path:
            self._output_path = Path(file_path)
            self.output_edit.setText(file_path)
            self.log_view.append_colored(f"Selected output: {file_path}", "info")

    def _start_protection(self) -> None:
        if not self._project_path or not is_valid_godot_project(self._project_path):
            QMessageBox.warning(
                self,
                get_text(self.current_lang, "invalid_project_title"),
                get_text(self.current_lang, "invalid_project_msg"),
            )
            return
        self._switch_page(1)
        self.protect_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.open_folder_btn.setEnabled(False)
        self.log_view.clear_log()
        self.progress_bar.setValue(0)

        level = self.level_combo.currentData() or "basic"
        output = self._output_path if level == "standard" else None
        custom_password = self.password_edit.text().strip() or None

        self._worker = ProtectionWorker(
            project_path=self._project_path,
            level=level,
            output_path=output,
            custom_password=custom_password,
            auto_backup=self.backup_check.isChecked(),
            name_length=self.name_length_spin.value(),
            godot_path=self.godot_path_edit.text().strip(),
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
        self._status_key = ""

    def _on_log(self, message: str, severity: str) -> None:
        self.log_view.append_colored(message, severity)

    def _on_finished(self, result: ProtectionResult) -> None:
        self.protect_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        if result.success and result.output_path:
            self.open_folder_btn.setEnabled(True)

        if result.success:
            self.progress_bar.setValue(100)
            self._status_key = "status_success"
            self.status_label.setText(get_text(self.current_lang, "status_success"))
            self.log_view.append_colored("=== Protection completed successfully ===", "success")
            QMessageBox.information(
                self,
                get_text(self.current_lang, "success_title"),
                get_text(self.current_lang, "success_msg"),
            )
        else:
            self._status_key = "status_failed"
            self.status_label.setText(get_text(self.current_lang, "status_failed"))
            self.log_view.append_colored(f"Failed: {result.error_message}", "error")
            QMessageBox.critical(
                self,
                get_text(self.current_lang, "failed_title"),
                f"{get_text(self.current_lang, 'error_prefix')} {result.error_message}",
            )
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
        file_path, _ = QFileDialog.getSaveFileName(
            self, get_text(self.current_lang, "save"), "logs.txt", "Text (*.txt)"
        )
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
        self._status_key = "ready"
        self.status_label.setText(get_text(self.current_lang, "ready"))
        self.invalid_label.setVisible(False)
        self.open_folder_btn.setEnabled(False)
        self.protect_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.log_view.append_colored("Session cleared. Ready for new project.", "info")
