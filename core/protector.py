"""
Protection pipeline orchestrator for Godot Shield.

This module ties together validation, key generation, obfuscation,
and encrypted export into a single high-level workflow. It is used
by both the CLI and GUI entry points.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from .exporter import export_game
from .obfuscator import run_obfuscation
from .utils import (
    ensure_output_dir,
    find_godot_executable,
    find_obfuscator_script,
    generate_encryption_key,
    is_valid_godot_project,
)


@dataclass
class ProtectionResult:
    """
    Result of the protection pipeline.

    Attributes:
        success: Overall success flag (obfuscation succeeded, and export if requested).
        key_generated: Whether an encryption key was generated.
        obfuscated: Whether GDScript obfuscation succeeded.
        exported: Whether encrypted export succeeded (only relevant for standard level).
        output_path: Path to exported executable if available.
        error_message: Human-readable error message if success is False.
    """

    success: bool
    key_generated: bool
    obfuscated: bool
    exported: bool
    output_path: Optional[Path]
    error_message: Optional[str] = None


def protect_project(
    project_path: Path,
    level: str = "basic",
    output_path: Optional[Path] = None,
    progress: Optional[Callable[[str, int], None]] = None,
    logger: Optional[Callable[[str, str], None]] = None,
) -> ProtectionResult:
    """
    Run the full protection pipeline for a Godot project.

    Pipeline steps:
      1. Validate project path
      2. Generate AES-256 encryption key
      3. Obfuscate GDScript source (always)
      4. Export encrypted build only if level == "standard"

    Args:
        project_path: Path to the Godot project root.
        level: Protection level, either "basic" (obfuscation only) or "standard"
               (obfuscation + encrypted export).
        output_path: Desired output .exe path for standard level.
                     If None, defaults to <project>/build/game.exe.
        progress: Callback accepting (step_name, percent) for UI updates.
        logger: Callback accepting (message, severity) where severity is
                "info", "success", "warning", "error".

    Returns:
        ProtectionResult dataclass summarizing the outcome.
    """
    # Provide no-op defaults for callbacks if not supplied
    if progress is None:

        def progress(_step: str, _percent: int) -> None:
            pass

    if logger is None:

        def logger(_msg: str, _sev: str) -> None:
            pass

    # Normalize inputs
    try:
        project_path = Path(project_path).resolve()
    except Exception as exc:
        error_msg = f"Invalid project path: {exc}"
        logger(error_msg, "error")
        return ProtectionResult(
            success=False,
            key_generated=False,
            obfuscated=False,
            exported=False,
            output_path=None,
            error_message=error_msg,
        )

    level = level.lower().strip()
    if level not in ("basic", "standard"):
        logger(f"Invalid level '{level}', defaulting to 'basic'.", "warning")
        level = "basic"

    if output_path is not None:
        try:
            output_path = Path(output_path).resolve()
        except Exception as exc:
            error_msg = f"Invalid output path: {exc}"
            logger(error_msg, "error")
            return ProtectionResult(
                success=False,
                key_generated=False,
                obfuscated=False,
                exported=False,
                output_path=None,
                error_message=error_msg,
            )

    # Initialize result flags
    key_generated = False
    obfuscated = False
    exported = False
    encryption_key = ""

    try:
        # ------------------------------------------------------------------
        # Step 1: Validate project
        # ------------------------------------------------------------------
        progress("Validating project", 5)
        logger(f"Validating Godot project: {project_path}", "info")

        if not is_valid_godot_project(project_path):
            error_msg = (
                f"Not a valid Godot project: {project_path}. "
                "Missing project.godot file."
            )
            logger(error_msg, "error")
            return ProtectionResult(
                success=False,
                key_generated=False,
                obfuscated=False,
                exported=False,
                output_path=None,
                error_message=error_msg,
            )

        # Check obfuscator availability early for better UX
        obfuscator_script = find_obfuscator_script()
        if obfuscator_script is None:
            logger(
                "Obfuscator not found, but continuing check. "
                "If obfuscation is attempted it will fail.",
                "warning",
            )
        else:
            logger(f"Obfuscator script ready: {obfuscator_script}", "info")

        progress("Project validated", 10)

        # ------------------------------------------------------------------
        # Step 2: Generate encryption key
        # ------------------------------------------------------------------
        progress("Generating encryption key", 15)
        logger("Generating AES-256 encryption key...", "info")
        try:
            encryption_key = generate_encryption_key()
            key_generated = True
            logger("Encryption key generated (64-char hex, 256-bit).", "success")
            # Never log the actual key value
        except Exception as exc:
            error_msg = f"Failed to generate encryption key: {exc}"
            logger(error_msg, "error")
            return ProtectionResult(
                success=False,
                key_generated=False,
                obfuscated=False,
                exported=False,
                output_path=None,
                error_message=error_msg,
            )

        progress("Key generated", 20)

        # ------------------------------------------------------------------
        # Step 3: Obfuscate GDScript
        # ------------------------------------------------------------------
        progress("Obfuscating GDScript", 25)
        logger("Starting GDScript obfuscation...", "info")

        try:
            obfuscated = run_obfuscation(project_path, logger)
        except Exception as exc:
            logger(f"Exception during obfuscation: {exc}", "error")
            obfuscated = False

        if not obfuscated:
            error_msg = "Obfuscation failed. Check logs for details."
            logger(error_msg, "error")
            progress("Obfuscation failed", 100)
            return ProtectionResult(
                success=False,
                key_generated=key_generated,
                obfuscated=False,
                exported=False,
                output_path=None,
                error_message=error_msg,
            )

        progress("Obfuscation completed", 60)
        logger("Obfuscation step completed.", "success")
        
        # Cleanup: Move obfuscation mapping file to a safe backup folder
        map_file = project_path.parent / f"{project_path.name}_obfuscation_data.json"
        if map_file.exists():
            try:
                backup_dir = project_path.parent / ".godot_shield_backups"
                backup_dir.mkdir(exist_ok=True)
                import shutil
                safe_map_path = backup_dir / map_file.name
                shutil.move(str(map_file), str(safe_map_path))
                logger(f"Security: Mapping file moved to safe backup: {safe_map_path}", "success")
            except Exception as e:
                logger(f"Warning: Could not secure mapping file {map_file}: {e}", "warning") 
        # ------------------------------------------------------------------
        # Step 4: Export (only for standard level)
        # ------------------------------------------------------------------
        if level == "standard":
            progress("Preparing export", 65)
            logger("Protection level is 'standard' — proceeding to encrypted export.", "info")

            # Resolve default output path if not provided
            if output_path is None:
                output_path = project_path / "build" / "game.exe"
                logger(f"Using default output path: {output_path}", "info")

            # Ensure output dir exists (for default case)
            try:
                ensure_output_dir(output_path)
            except OSError as ose:
                error_msg = f"Failed to create output directory: {ose}"
                logger(error_msg, "error")
                return ProtectionResult(
                    success=False,
                    key_generated=key_generated,
                    obfuscated=obfuscated,
                    exported=False,
                    output_path=output_path,
                    error_message=error_msg,
                )

            # Check if Godot executable exists; if not, treat as warning and return partial success
            godot_exe = find_godot_executable()
            if godot_exe is None:
                # Per spec: if Godot not installed, still obfuscate and tell user export was skipped
                logger(
                    "Godot executable not found. Export skipped. "
                    "Obfuscation was successful, but no encrypted build was created. "
                    "Install Godot 4.x and ensure 'godot' is in your PATH to enable export.",
                    "warning",
                )
                progress("Export skipped (Godot not found)", 100)
                # Partial success: obfuscation succeeded, export skipped
                return ProtectionResult(
                    success=True,
                    key_generated=key_generated,
                    obfuscated=True,
                    exported=False,
                    output_path=output_path,
                    error_message="Export skipped: Godot executable not found.",
                )

            progress("Exporting encrypted build", 70)
            logger("Starting encrypted export...", "info")

            try:
                exported = export_game(project_path, output_path, encryption_key, logger)
            except Exception as exc:
                logger(f"Exception during export: {exc}", "error")
                exported = False

            if not exported:
                error_msg = "Export failed. Check that export templates are installed and 'Windows Desktop' preset exists."
                logger(error_msg, "error")
                progress("Export failed", 100)
                return ProtectionResult(
                    success=False,
                    key_generated=key_generated,
                    obfuscated=obfuscated,
                    exported=False,
                    output_path=output_path,
                    error_message=error_msg,
                )

            progress("Export completed", 100)
            logger("Encrypted export completed successfully.", "success")

            return ProtectionResult(
                success=True,
                key_generated=key_generated,
                obfuscated=True,
                exported=True,
                output_path=output_path,
                error_message=None,
            )

        else:
            # Basic level: obfuscation only
            progress("Protection completed (basic level)", 100)
            logger(
                "Basic protection completed: GDScript obfuscation done. "
                "No export performed (basic level).",
                "success",
            )
            return ProtectionResult(
                success=True,
                key_generated=key_generated,
                obfuscated=True,
                exported=False,
                output_path=None,
                error_message=None,
            )

    except Exception as exc:
        # Global catch-all for unexpected errors
        error_msg = f"Unexpected error in protection pipeline: {exc}"
        try:
            logger(error_msg, "error")
        except Exception:
            pass
        progress("Protection failed", 100)
        return ProtectionResult(
            success=False,
            key_generated=key_generated,
            obfuscated=obfuscated,
            exported=exported,
            output_path=output_path,
            error_message=error_msg,
        )
