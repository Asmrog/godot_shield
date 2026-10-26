"""
CLI entry point for Godot Shield.

Provides a Typer-based command line interface with 'protect' and 'version'
commands, using Rich for colored output and progress reporting.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from core.protector import protect_project
from core.utils import is_valid_godot_project

# Initialize Typer app and Rich console
app = typer.Typer(
    help="Godot Shield — Automated protection for Godot games (obfuscation + encryption).",
    add_completion=False,
)
console = Console()


def _logger_callback(message: str, severity: str) -> None:
    """
    Logger callback that prints colored messages via Rich.

    Args:
        message: Log message.
        severity: Severity level (info, success, warning, error).
    """
    try:
        style_map = {
            "info": "white",
            "success": "bold green",
            "warning": "bold yellow",
            "error": "bold red",
        }
        style = style_map.get(severity.lower(), "white")
        # Prefix with severity for clarity
        prefix_map = {
            "info": "[INFO]",
            "success": "[SUCCESS]",
            "warning": "[WARN]",
            "error": "[ERROR]",
        }
        prefix = prefix_map.get(severity.lower(), "[INFO]")
        console.print(f"{prefix} {message}", style=style)
    except Exception:
        # Fallback to plain print if Rich fails
        try:
            print(f"[{severity.upper()}] {message}")
        except Exception:
            pass


def _progress_callback(step_name: str, percent: int) -> None:
    """
    Progress callback that prints progress updates.

    Args:
        step_name: Name of current step.
        percent: Completion percentage.
    """
    try:
        console.print(f"[cyan][{percent:3d}%] {step_name}[/cyan]")
    except Exception:
        try:
            print(f"[{percent}%] {step_name}")
        except Exception:
            pass


@app.command(name="protect")
def protect_command(
    project_path: Path = typer.Argument(
        ..., help="Path to Godot project folder (must contain project.godot)."
    ),
    level: str = typer.Option(
        "basic",
        "--level",
        "-l",
        help="Protection level: 'basic' (obfuscation only) or 'standard' (obfuscation + encrypted export).",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output .exe path for standard level (default: <project>/build/game.exe).",
    ),
) -> None:
    """
    Protect a Godot project by obfuscating GDScript and optionally exporting an encrypted build.
    """
    try:
        console.print("[bold blue]🛡 Godot Shield — Protection Pipeline[/bold blue]")
        console.print(f"Project: {project_path}")
        console.print(f"Level: {level}")
        if output:
            console.print(f"Output: {output}")
        console.print("")

        # Validate level
        level = level.lower().strip()
        if level not in ("basic", "standard"):
            console.print(
                f"[bold red]Invalid level '{level}'. Must be 'basic' or 'standard'.[/bold red]"
            )
            raise typer.Exit(code=1)

        # Validate project path exists
        project_path = Path(project_path).resolve()
        if not project_path.exists():
            console.print(f"[bold red]Project path does not exist: {project_path}[/bold red]")
            raise typer.Exit(code=1)

        if not is_valid_godot_project(project_path):
            console.print(
                f"[bold red]Not a valid Godot project (missing project.godot): {project_path}[/bold red]"
            )
            raise typer.Exit(code=1)

        # Resolve output path if provided
        if output is not None:
            output = Path(output).resolve()

        # Run protection pipeline
        result = protect_project(
            project_path=project_path,
            level=level,
            output_path=output,
            progress=_progress_callback,
            logger=_logger_callback,
        )

        console.print("")
        if result.success:
            console.print("[bold green]✓ Protection completed successfully![/bold green]")
            console.print(f"  Obfuscated: {result.obfuscated}")
            console.print(f"  Exported: {result.exported}")
            if result.output_path:
                console.print(f"  Output: {result.output_path}")
            if result.error_message:
                # This can happen when export is skipped due to missing Godot
                console.print(f"[yellow]Note: {result.error_message}[/yellow]")
            raise typer.Exit(code=0)
        else:
            console.print("[bold red]✗ Protection failed.[/bold red]")
            if result.error_message:
                console.print(f"[red]Error: {result.error_message}[/red]")
            raise typer.Exit(code=1)

    except typer.Exit:
        raise
    except Exception as exc:
        console.print(f"[bold red]Unexpected error: {exc}[/bold red]")
        raise typer.Exit(code=1)


@app.command(name="version")
def version_command() -> None:
    """
    Show version and license information.
    """
    try:
        console.print("Godot Shield v1.0.2 — MIT License")
    except Exception:
        # Fallback if Rich fails
        print("Godot Shield v1.0.2 — MIT License")


if __name__ == "__main__":
    app()
