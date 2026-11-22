"""
GDScript obfuscation wrapper.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

from .utils import find_obfuscator_script, find_python_executable


def run_obfuscation(
    project_path: Path,
    logger: Callable[[str, str], None],
    name_length: int = 8,
) -> bool:
    """Run the external obfuscator on the project.

    name_length controls the generated identifier length and is clamped to the
    same 3-20 range exposed by the Settings spin box.
    """
    try:
        try:
            name_length = max(3, min(20, int(name_length)))
        except (TypeError, ValueError):
            name_length = 8

        script_path = find_obfuscator_script()
        if script_path is None:
            logger(
                "Obfuscator not found. Make sure the 'obfuscator' folder is next to the EXE.",
                "error",
            )
            return False

        python_exe = find_python_executable()
        if python_exe is None:
            logger(
                "Python executable not found in PATH! The obfuscator requires Python to run. "
                "Please install Python and add it to your system PATH.",
                "error",
            )
            return False

        logger(f"Found obfuscator: {script_path}", "info")
        project_path = Path(project_path).resolve()

        if not project_path.exists():
            logger(f"Project path does not exist: {project_path}", "error")
            return False

        cmd = [python_exe, str(script_path)]
        logger(f"Running: {' '.join(cmd)}", "info")

        obfuscator_dir = script_path.parent.parent

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(obfuscator_dir),
            bufsize=1,
        )

        # Provide inputs: 1. Path, 2. Overwrite confirmation, 3. Name length
        stdin_input = f"{project_path}\nyes\n{name_length}\n"

        try:
            stdout, stderr = process.communicate(input=stdin_input, timeout=300)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
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
