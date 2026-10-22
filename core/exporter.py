"""
Godot export wrapper with AES-256 PCK encryption.

This module handles exporting a Godot project to an encrypted Windows build
using the Godot headless export functionality and the GODOT_SCRIPT_ENCRYPTION_KEY
environment variable.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Callable

from .utils import ensure_output_dir, find_godot_executable


def export_game(
    project_path: Path,
    output_exe: Path,
    encryption_key: str,
    logger: Callable[[str, str], None],
) -> bool:
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

    Returns:
        True if export succeeded and output file exists, False otherwise.
    """
    try:
        project_path = Path(project_path).resolve()
        output_exe = Path(output_exe).resolve()

        # Step 1: Locate Godot executable
        godot_exe = find_godot_executable()
        if godot_exe is None:
            logger(
                "Godot executable not found in PATH. Searched for 'godot' and 'godot4'. "
                "Export will be skipped. Please install Godot 4.x and add it to PATH.",
                "warning",
            )
            return False

        logger(f"Found Godot executable: {godot_exe}", "info")

        # Step 2: Ensure output directory exists
        try:
            ensure_output_dir(output_exe)
            logger(f"Output directory ensured: {output_exe.parent}", "info")
        except OSError as ose:
            logger(f"Failed to create output directory: {ose}", "error")
            return False

        # Step 3: Prepare environment with encryption key
        env = os.environ.copy()
        env["GODOT_SCRIPT_ENCRYPTION_KEY"] = encryption_key
        logger("Encryption key injected into environment (AES-256).", "info")
        # Do not log the actual key for security

        # Step 4: Build export command
        # Command: godot --headless --path <project> --export-release "Windows Desktop" <output>
        cmd = [
            str(godot_exe),
            "--headless",
            "--path",
            str(project_path),
            "--export-release",
            "Windows Desktop",
            str(output_exe),
        ]

        logger(f"Running export command: {' '.join(cmd)}", "info")
        logger(f"Export preset: 'Windows Desktop' -> {output_exe}", "info")

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

            try:
                stdout, stderr = process.communicate(timeout=600)
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                    process.communicate()
                except Exception:
                    pass
                logger("Game export timed out after 600 seconds.", "error")
                return False

            # Step 6: Stream logs
            if stdout:
                for line in stdout.splitlines():
                    stripped = line.strip()
                    if stripped:
                        if "error" in stripped.lower():
                            logger(stripped, "error")
                        elif "warning" in stripped.lower():
                            logger(stripped, "warning")
                        else:
                            logger(stripped, "info")

            if stderr:
                for line in stderr.splitlines():
                    stripped = line.strip()
                    if stripped:
                        # Godot often prints progress to stderr
                        if "error" in stripped.lower():
                            logger(stripped, "error")
                        else:
                            logger(stripped, "info")

            # Step 7: Validate output
            if process.returncode != 0:
                logger(
                    f"Godot export failed with exit code {process.returncode}. "
                    "Ensure you have export templates installed and a 'Windows Desktop' "
                    "preset configured in your project.",
                    "error",
                )
                return False

            if not output_exe.exists():
                logger(
                    f"Export command finished but output file not found: {output_exe}. "
                    "Check Godot export preset configuration.",
                    "error",
                )
                return False

            # Success: report file size
            try:
                size = output_exe.stat().st_size
                from .utils import format_size

                size_str = format_size(size)
                logger(
                    f"Export successful: {output_exe} ({size_str})", "success"
                )
                # Also check for .pck file that Godot may create alongside
                pck_path = output_exe.with_suffix(".pck")
                if pck_path.exists():
                    pck_size = format_size(pck_path.stat().st_size)
                    logger(f"PCK file created: {pck_path} ({pck_size})", "info")
            except Exception:
                logger(f"Export successful: {output_exe}", "success")

            return True

        except FileNotFoundError as fnf:
            logger(f"Failed to launch Godot executable: {fnf}", "error")
            return False
        except PermissionError as perm:
            logger(f"Permission denied running Godot: {perm}", "error")
            return False
        except Exception as exc:
            logger(f"Unexpected error during export: {exc}", "error")
            return False

    except Exception as exc:
        try:
            logger(f"Critical error in exporter wrapper: {exc}", "error")
        except Exception:
            pass
        return False
