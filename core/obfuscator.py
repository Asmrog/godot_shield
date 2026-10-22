"""
GDScript obfuscation wrapper.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Callable

from .utils import find_obfuscator_script


def run_obfuscation(project_path: Path, logger: Callable[[str, str], None]) -> bool:
    """Run the external obfuscator on the project."""
    try:
        script_path = find_obfuscator_script()
        if script_path is None:
            logger(
                "Obfuscator not found. Clone it with: git clone "
                "https://github.com/June-Tree/Godot-Source-Code-Obfuscator.git obfuscator",
                "error",
            )
            return False

        logger(f"Found obfuscator: {script_path}", "info")
        project_path = Path(project_path).resolve()
        if not project_path.exists():
            logger(f"Project path does not exist: {project_path}", "error")
            return False

        cmd = [sys.executable, str(script_path)]
        logger(f"Running: {' '.join(cmd)}", "info")

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(script_path.parent.parent),
            bufsize=1,
        )

        # الإجابات الثلاثة المطلوبة:
        # 1. مسار المشروع
        # 2. تأكيد الكتابة فوق الملفات (yes)
        # 3. طول الأسماء الجديدة (8 أحرف)
        stdin_input = f"{project_path}\nyes\n8\n"
        
        try:
            stdout, stderr = process.communicate(input=stdin_input, timeout=300)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
                process.communicate()
            except Exception:
                pass
            logger("Obfuscation timed out after 300 seconds.", "error")
            return False

        if stdout:
            for line in stdout.splitlines():
                s = line.strip()
                if s:
                    sev = "success" if ("success" in s.lower() or "completed" in s.lower()) else "info"
                    logger(s, sev)
        if stderr:
            for line in stderr.splitlines():
                s = line.strip()
                if s:
                    logger(s, "warning")

        if process.returncode != 0:
            logger(f"Obfuscator exited with code {process.returncode}.", "error")
            return False

        logger("GDScript obfuscation completed successfully.", "success")
        return True

    except Exception as exc:
        logger(f"Critical error in obfuscator: {exc}", "error")
        return False
