"""
Godot export wrapper with AES-256 PCK encryption.

This module handles exporting a Godot project to an encrypted Windows build
using the Godot headless export functionality and the GODOT_SCRIPT_ENCRYPTION_KEY
environment variable.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from .i18n import get_text
from .utils import ensure_output_dir, find_godot_executable


@dataclass
class ExportResult:
    """Outcome of an export attempt.

    ``bool(result)`` mirrors ``result.success`` so existing ``if export_game(...)``
    call sites keep working, while callers that care about the details can read
    ``error_message`` / ``error_key``.
    """

    success: bool
    error_message: Optional[str] = None
    error_key: Optional[str] = None
    stderr: str = ""

    def __bool__(self) -> bool:
        return self.success


def _log(logger: Callable[[str, str], None], message: str, severity: str) -> None:
    try:
        logger(message, severity)
    except Exception:
        pass


def _failure(error_key: str, detail: str = "", stderr: str = "") -> ExportResult:
    """Build a user-friendly failure result, keeping the raw Godot output."""
    message = get_text("en", error_key)
    detail = (detail or "").strip()
    if detail and detail.lower() not in message.lower():
        message = f"{message}\nGodot said: {detail}"
    return ExportResult(
        success=False,
        error_message=message,
        error_key=error_key,
        stderr=stderr or detail,
    )


def _classify_failure(output: str) -> str:
    """Map Godot's stderr/stdout onto the most helpful i18n error message."""
    text = (output or "").lower()
    if "permission denied" in text or "access is denied" in text:
        return "export_error_output_path"
    if "template" in text or "preset" in text:
        return "export_error_templates"
    # Godot's generic export failure is almost always templates/preset related.
    return "export_error_templates"


def export_game(
    project_path: Path,
    output_exe: Path,
    encryption_key: str,
    logger: Callable[[str, str], None],
    godot_path: Optional[str] = None,
) -> ExportResult:
    """
    Export the Godot project with AES-256 PCK encryption.

    Uses the Godot executable in headless mode to perform a release export
    for the "Windows Desktop" preset. The encryption key is passed via
    environment variable GODOT_SCRIPT_ENCRYPTION_KEY.

    Args:
        project_path: Path to the Godot project root.
        output_exe: Desired output .exe path (e.g., build/game.exe).
        encryption_key: 64-char hex string for AES-256 encryption.
        logger: Callback accepting (message, severity).
        godot_path: Optional custom Godot executable path from Settings.
                    Empty or invalid values fall back to the system PATH.

    Returns:
        ExportResult. Truthy on success; on failure ``error_message`` holds a
        clear, user-friendly explanation (including Godot's stderr details).
    """
    try:
        project_path = Path(project_path).resolve()
        output_exe = Path(output_exe).resolve()
    except Exception as exc:
        return _failure("export_error_output_path", str(exc))

    if output_exe.is_dir():
        return _failure(
            "export_error_output_path", f"Output path is a directory: {output_exe}"
        )

    # Step 1: Locate Godot executable. A valid custom path wins; an invalid or
    # empty one makes find_godot_executable() fall back to the system PATH.
    godot_exe = find_godot_executable(godot_path)
    if godot_exe is None:
        detail = (
            f"Custom Godot path is invalid: {godot_path}. "
            if godot_path
            else ""
        ) + "No 'godot' or 'godot4' executable found on PATH."
        _log(logger, detail, "error")
        return _failure("export_error_godot_missing", detail)

    _log(logger, f"Found Godot executable: {godot_exe}", "info")

    # Step 2: Ensure output directory exists
    try:
        ensure_output_dir(output_exe)
        _log(logger, f"Output directory ensured: {output_exe.parent}", "info")
    except OSError as ose:
        return _failure("export_error_output_path", str(ose))

    # Step 3: Prepare environment with encryption key
    env = os.environ.copy()
    env["GODOT_SCRIPT_ENCRYPTION_KEY"] = encryption_key
    _log(logger, "Encryption key injected into environment (AES-256).", "info")
    # Do not log the actual key for security

    # Step 4: Build export command
    cmd = [
        str(godot_exe),
        "--headless",
        "--path",
        str(project_path),
        "--export-release",
        "Windows Desktop",
        str(output_exe),
    ]

    _log(logger, f"Running export command: {' '.join(cmd)}", "info")
    _log(logger, f"Export preset: 'Windows Desktop' -> {output_exe}", "info")

    # Step 5: Execute export process
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=str(project_path),
            bufsize=1,
        )
    except (FileNotFoundError, PermissionError, OSError) as exc:
        return _failure("export_error_launch", str(exc))

    try:
        stdout, stderr = process.communicate(timeout=600)
    except subprocess.TimeoutExpired:
        try:
            process.kill()
            process.communicate()
        except Exception:
            pass
        return _failure("export_error_timeout", "Exceeded the 600 second limit.")

    stdout = stdout or ""
    stderr = stderr or ""

    # Step 6: Stream logs (Godot writes progress to stderr as well as stdout).
    for stream in (stdout, stderr):
        for line in stream.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            severity = (
                "error" if "error" in stripped.lower()
                else "warning" if "warning" in stripped.lower()
                else "info"
            )
            _log(logger, stripped, severity)

    # Step 7: Validate the result.
    if process.returncode != 0:
        detail = stderr.strip() or stdout.strip() or f"exit code {process.returncode}"
        _log(logger, f"Godot export failed with exit code {process.returncode}.", "error")
        return _failure(_classify_failure(f"{stdout}\n{stderr}"), detail, stderr)

    if not output_exe.exists():
        detail = f"Export command finished but output file not found: {output_exe}"
        _log(logger, detail, "error")
        return _failure("export_error_output_path", detail, stderr)

    # Success: report file size
    try:
        from .utils import format_size

        size_str = format_size(output_exe.stat().st_size)
        _log(logger, f"Export successful: {output_exe} ({size_str})", "success")
        pck_path = output_exe.with_suffix(".pck")
        if pck_path.exists():
            pck_size = format_size(pck_path.stat().st_size)
            _log(logger, f"PCK file created: {pck_path} ({pck_size})", "info")
    except Exception:
        _log(logger, f"Export successful: {output_exe}", "success")

    return ExportResult(success=True)
