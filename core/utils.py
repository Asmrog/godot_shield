"""
Utility helpers for Godot Shield.

This module provides shared helper functions used across the protection
pipeline such as key generation, project validation, executable discovery,
and filesystem helpers. All functions are cross-platform and use pathlib.
"""

from __future__ import annotations

import secrets
import shutil
from pathlib import Path
from typing import Optional
import hashlib


def generate_encryption_key() -> str:
    """
    Generate a 256-bit AES encryption key for Godot PCK encryption.

    Returns:
        A 64-character hex string representing 32 random bytes (256 bits).
    """
    # secrets.token_hex is cryptographically secure and suitable for key generation
    return secrets.token_hex(32)


def is_valid_godot_project(path: Path) -> bool:
    """
    Check if the given path is a valid Godot project.

    A valid Godot project must contain a project.godot file at its root.

    Args:
        path: Path to the potential project directory.

    Returns:
        True if project.godot exists and is a file, False otherwise.
    """
    try:
        # Normalize path and check existence
        project_path = Path(path).resolve()
        if not project_path.is_dir():
            return False
        godot_file = project_path / "project.godot"
        return godot_file.is_file()
    except Exception:
        # Any exception (permission error, etc.) means invalid project
        return False


def find_godot_executable() -> Optional[Path]:
    """
    Search for the Godot executable in the system PATH.

    Looks for 'godot' first, then 'godot4' as fallback.
    This supports common installation names on Windows, Linux, and macOS.

    Returns:
        Path to the executable if found, None otherwise.
    """
    try:
        # Try common executable names in order
        for exe_name in ["godot", "godot4"]:
            found = shutil.which(exe_name)
            if found:
                return Path(found).resolve()
        return None
    except Exception:
        # shutil.which can fail in edge cases; treat as not found
        return None


def find_obfuscator_script() -> Optional[Path]:
    """
    Locate the external GDScript obfuscator script.

    The obfuscator is expected to be cloned from:
    https://github.com/June-Tree/Godot-Source-Code-Obfuscator
    into the 'obfuscator' directory at the project root.

    Search strategy:
      1. Check relative to current working directory
      2. Check relative to this file's location (core/utils.py -> ../obfuscator)
      3. Check parent of parent if nested

    Returns:
        Path to gdscript_obfuscator.py if found, None otherwise.
    """
    try:
        possible_bases = [
            Path.cwd() / "obfuscator",
            Path(__file__).resolve().parent.parent / "obfuscator",
            Path(__file__).resolve().parent.parent.parent / "obfuscator",
        ]

        for base in possible_bases:
            script_path = base / "scripts" / "gdscript_obfuscator.py"
            # Also check alternative layout (some versions put it at root)
            alt_path = base / "gdscript_obfuscator.py"
            if script_path.is_file():
                return script_path.resolve()
            if alt_path.is_file():
                return alt_path.resolve()

        return None
    except Exception:
        return None


def format_size(num_bytes: int | float) -> str:
    """
    Convert a byte count into a human-readable string.

    Args:
        num_bytes: Size in bytes.

    Returns:
        Human readable string like '1.2 MB' or '512 B'.
    """
    try:
        size = float(num_bytes)
        # Define units in ascending order
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if abs(size) < 1024.0:
                # For bytes, show no decimal; for larger, one decimal
                if unit == "B":
                    return f"{int(size)} {unit}"
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    except Exception:
        # Fallback if input is invalid
        return f"{num_bytes} B"

def generate_key_from_password(password: str) -> str:
    """Derives a 64-char hex key (256-bit) from a user password."""
    if not password:
        return secrets.token_hex(32) 
    # Use SHA-256 to hash the password into a 32-byte key
    return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
def ensure_output_dir(path: Path) -> Path:
    """
    Ensure the output directory exists, creating it if necessary.

    If the path appears to be a file (has a suffix), its parent directory
    is created. If it is a directory path, the directory itself is created.

    Args:
        path: File or directory path to ensure.

    Returns:
        The resolved Path that was ensured.

    Raises:
        OSError: If directory creation fails due to permissions or other errors.
    """
    try:
        target = Path(path).resolve()
        # If path has a file extension, treat it as file and create parent
        if target.suffix:
            dir_to_create = target.parent
        else:
            dir_to_create = target

        # Create directory recursively, no error if already exists
        dir_to_create.mkdir(parents=True, exist_ok=True)
        return target
    except Exception as exc:
        # Re-raise with clearer context
        raise OSError(f"Failed to create output directory for {path}: {exc}") from exc
