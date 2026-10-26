"""
QThread worker for Godot Shield GUI.

Runs the protection pipeline in a background thread to prevent
the UI from freezing. Emits signals for progress, logging, and
completion.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal

from core.protector import ProtectionResult, protect_project


class ProtectionWorker(QThread):
    """
    Background worker thread that runs the protection pipeline.

    This worker ensures the GUI remains responsive while obfuscation
    and export (which can take minutes) are executed.

    Signals:
        progress: Emitted with (step_name: str, percent: int)
        log: Emitted with (message: str, severity: str)
        protection_finished: Emitted with ProtectionResult when done
    """

    progress = Signal(str, int)
    log = Signal(str, str)
    protection_finished = Signal(object)

    def __init__(
        self,
        project_path: Path,
        level: str,
        output_path: Optional[Path] = None,
        custom_password: Optional[str] = None,
        parent=None,
    ) -> None:
        """
        Initialize the worker.

        Args:
            project_path: Path to Godot project root.
            level: Protection level ("basic" or "standard").
            output_path: Optional output exe path for standard level.
            custom_password: Optional password for AES encryption.
            parent: Optional parent QObject.
        """
        super().__init__(parent)
        self.project_path = Path(project_path)
        self.level = level
        self.output_path = Path(output_path) if output_path else None
        self.custom_password = custom_password  # <--- إضافة جديدة
        # Cooperative cancellation flag — checked between pipeline steps
        self._cancelled = False

    def cancel(self) -> None:
        """
        Request cancellation of the protection pipeline.

        This is cooperative: it sets a flag checked between steps.
        It does not forcibly kill subprocesses to avoid corrupting files.
        """
        self._cancelled = True
        try:
            self.log.emit("Cancellation requested — finishing current step...", "warning")
        except Exception:
            pass

    def run(self) -> None:
        """
        Execute the protection pipeline.

        This method runs in a separate thread. It binds callbacks that emit
        Qt signals to update the GUI safely from the background thread.
        """
        try:
            # Define callbacks that emit signals (thread-safe via Qt signal/slot)
            def progress_callback(step_name: str, percent: int) -> None:
                try:
                    if self._cancelled:
                        self.progress.emit("Cancelling...", percent)
                        return
                    self.progress.emit(step_name, percent)
                except Exception:
                    pass

            def logger_callback(message: str, severity: str) -> None:
                try:
                    self.log.emit(message, severity)
                except Exception:
                    pass

            # Check if cancelled before starting
            if self._cancelled:
                result = ProtectionResult(
                    success=False,
                    key_generated=False,
                    obfuscated=False,
                    exported=False,
                    output_path=self.output_path,
                    error_message="Operation cancelled by user.",
                )
                self.protection_finished.emit(result)
                return

            # Call the core protection function with bound callbacks
            result: ProtectionResult = protect_project(
                project_path=self.project_path,
                level=self.level,
                output_path=self.output_path,
                custom_password=self.custom_password, 
                progress=progress_callback,
                logger=logger_callback,
            )

            # If cancellation was requested during run, override result
            if self._cancelled:
                result.error_message = (result.error_message or "") + " (Cancelled by user)"
                result.success = False
                self.log.emit("Operation cancelled by user.", "warning")

            # Emit final result
            try:
                self.protection_finished.emit(result)
            except Exception:
                pass

        except Exception as exc:
            # Handle any uncaught exception in worker thread
            try:
                self.log.emit(f"Worker thread crashed: {exc}", "error")
                fail_result = ProtectionResult(
                    success=False,
                    key_generated=False,
                    obfuscated=False,
                    exported=False,
                    output_path=self.output_path,
                    error_message=f"Worker error: {exc}",
                )
                self.protection_finished.emit(fail_result)
            except Exception:
                pass
