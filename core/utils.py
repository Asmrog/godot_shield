"""
Utility helpers for Godot Shield.
"""

from __future__ import annotations

import secrets
import shutil
import sys
import hashlib
from pathlib import Path
from typing import Optional


def generate_encryption_key() -> str:
    # Generate a 256-bit AES encryption key (64-char hex).
    return secrets.token_hex(32)


def generate_key_from_password(password: str) -> str:
    # Derives a 64-char hex key (256-bit) from a user password using SHA-256.
    if not password:
        return secrets.token_hex(32)  # fallback to random
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def is_valid_godot_project(path: Path) -> bool:
    # Return True if path/project.godot exists.
    try:
        p = Path(path).resolve()
        return p.is_dir() and (p / "project.godot").is_file()
    except Exception:
        return False


def find_godot_executable() -> Optional[Path]:
    # Search PATH for godot or godot4.
    try:
        for name in ["godot", "godot4"]:
            found = shutil.which(name)
            if found:
                return Path(found).resolve()
        return None
    except Exception:
        return None


def find_obfuscator_script() -> Optional[Path]:
    # Locate obfuscator/scripts/gdscript_obfuscator.py relative to project.
    # Handles both running from source and running as a compiled EXE.
    try:
        if getattr(sys, 'frozen', False):
            # Running as compiled EXE (PyInstaller)
            base_dir = Path(sys.executable).parent
        else:
            # Running from source code
            base_dir = Path(__file__).resolve().parent.parent

        candidates = [
            Path.cwd() / "obfuscator",
            base_dir / "obfuscator",
        ]

        for base in candidates:
            script = base / "scripts" / "gdscript_obfuscator.py"
            if script.is_file():
                return script.resolve()
        return None
    except Exception:
        return None


def find_python_executable() -> Optional[str]:
    # Find a valid Python executable to run external scripts.
    if not getattr(sys, 'frozen', False):
        return sys.executable
    
    # If running as EXE, find Python in the system PATH
    for name in ["python", "python3"]:
        found = shutil.which(name)
        if found:
            return found
            
    return None


def format_size(num_bytes) -> str:
    # Human-readable file size.
    try:
        size = float(num_bytes)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if abs(size) < 1024.0:
                return f"{int(size)} {unit}" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    except Exception:
        return f"{num_bytes} B"


def ensure_output_dir(path: Path) -> Path:
    # Ensure parent dir of a file path exists.
    target = Path(path).resolve()
    (target.parent if target.suffix else target).mkdir(parents=True, exist_ok=True)
    return target
