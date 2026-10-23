# Godot Shield 
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Automated protection for Godot games — obfuscation + encryption.**

> **Disclaimer:** No tool can prevent 100% reverse engineering. Godot Shield applies industry best practices (GDScript obfuscation + AES-256 PCK encryption + debug symbol removal) automatically, raising the bar for casual attackers. Determined reverse engineers with sufficient time and resources can still decompile or analyze your game. Use this as one layer of defense, not a guarantee.

---

## Features

- **GDScript Obfuscation** — Renames variables, functions, strips comments and whitespace using [June-Tree/Godot-Source-Code-Obfuscator](https://github.com/June-Tree/Godot-Source-Code-Obfuscator).
- **AES-256 PCK Encryption** — Exports with `GODOT_SCRIPT_ENCRYPTION_KEY` for encrypted `.pck` data.
- **Windows Export** — One-click export to `Windows Desktop` preset via Godot headless.
- **Two Protection Levels:**
  - `Basic`: Obfuscation only (fast, no Godot needed for export).
  - `Standard`: Obfuscation + encrypted export (requires Godot 4.x + templates).
- **CLI + GUI** — Use `main.py` for automation/CI or `run_gui.py` for desktop UX.
- **Cross-Platform** — Primary target Windows, works on Linux/macOS.
- **Dark Themed GUI** — PySide6 with Figma blue accent, progress bar, colored logs, cancel support.

## Screenshots

*Placeholder — add your screenshots here:*

- `screenshots/gui_main.png` — Main window with project selection
- `screenshots/gui_logs.png` — Logs during protection
- `screenshots/cli_example.png` — CLI usage example

## Installation

```bash
# Clone the repo
git clone <your-repo-url> godot-shield
cd godot-shield

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Or on Unix/macOS
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Clone the external obfuscator (required)
git clone https://github.com/June-Tree/Godot-Source-Code-Obfuscator.git obfuscator

# Verify installation
python main.py version
# Should print: Godot Shield v1.0.0 — MIT License
```

## Usage

### CLI

```bash
# Basic protection (obfuscation only)
python main.py protect /path/to/your/godot/project --level basic

# Standard protection (obfuscation + encrypted export)
python main.py protect /path/to/your/godot/project --level standard --output /path/to/build/game.exe

# Default output for standard is <project>/build/game.exe if --output not specified
python main.py protect ./my-game --level standard

# Show version
python main.py version
```

**CLI Output Example:**
```
 Godot Shield — Protection Pipeline 
Project: C:\Users\Dev\MyGame
Level: standard

[  5%] Validating project
[INFO] Validating Godot project: ...
[SUCCESS] Encryption key generated (64-char hex, 256-bit).
[ 25%] Obfuscating GDScript
...
✓ Protection completed successfully!
```

### GUI

```bash
python run_gui.py
```

1. Click **Browse...** and select your Godot project folder (must contain `project.godot`).
2. Choose protection level:
   - **Basic**: Obfuscates GDScript in place.
   - **Standard**: Obfuscates + exports encrypted `.exe`.
3. For Standard, select output `.exe` path (default: `<project>/build/game.exe`).
4. Click **Protect Game**.
5. Watch progress bar and colored logs. Use **Cancel** to stop.
6. On success, click **Open Folder** to view build.

## Requirements

- **Python 3.10+**
- **Godot 4.x** installed and in PATH (`godot` or `godot4` executable):
  - Windows: Add Godot folder to system PATH or rename binary to `godot.exe`.
  - Linux/macOS: Ensure `godot` is executable and in `/usr/local/bin` or similar.
- **Export Templates** installed in Godot:
  - In Godot Editor: `Editor > Manage Export Templates > Download`.
- **Windows Desktop Export Preset** configured in your project:
  - In Godot Editor: `Project > Export > Add... > Windows Desktop`, name it exactly `Windows Desktop`, configure output.
- **External Obfuscator** cloned:
  ```bash
  git clone https://github.com/June-Tree/Godot-Source-Code-Obfuscator.git obfuscator
  ```
  The tool looks for `obfuscator/scripts/gdscript_obfuscator.py`.

## Project Structure

```
godot-shield/
├── main.py                     # CLI entry point (Typer)
├── run_gui.py                  # GUI entry point
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── core/
│   ├── __init__.py
│   ├── protector.py            # Orchestrates full pipeline
│   ├── obfuscator.py           # GDScript obfuscation wrapper
│   ├── exporter.py             # Godot export wrapper
│   └── utils.py                # Shared helpers
├── gui/
│   ├── __init__.py
│   ├── app.py                  # Main PySide6 window + dark QSS
│   ├── widgets.py              # ColoredLogView, FolderPicker
│   └── workers.py              # QThread worker
└── obfuscator/                 # Cloned external repo (gitignored)
```

## Limitations

- **Not bulletproof:** Obfuscation and PCK encryption raise the bar but do not stop determined attackers. Debug symbols are removed, but strings and some logic can still be recovered.
- **Godot version:** Tested with Godot 4.x. Godot 3.x projects may need adaptation (different export preset names).
- **Export preset name:** Must be exactly `Windows Desktop` for automatic export. If you use a custom name, export manually.
- **Overwrite behavior:** Obfuscation overwrites GDScript files in place. **Back up your project or use version control (git) before running.** The tool does not create automatic backups.
- **Binary protection:** This tool does not pack or protect the `.exe` itself beyond what Godot provides. For additional `.exe` protection, consider external packers (not included).
- **Open source obfuscator:** The obfuscator is community-maintained; results may vary per project.

## Troubleshooting

- **"Obfuscator script not found"** — Clone the repo into `obfuscator/` as described in Installation.
- **"Godot executable not found"** — Install Godot 4.x and add to PATH. On Windows, ensure `godot.exe` is in PATH or rename.
- **Export fails with "export templates missing"** — Open Godot Editor and download export templates.
- **Export fails with "preset not found"** — Create a Windows Desktop preset named exactly `Windows Desktop` in Project > Export.
- **GUI freezes** — Should not happen; protection runs in QThread. If it does, check logs and report issue.

## License

MIT License — see [LICENSE](LICENSE). Copyright (c) 2026 Godot Shield.

## Credits

- **Obfuscation engine:** [June-Tree/Godot-Source-Code-Obfuscator](https://github.com/June-Tree/Godot-Source-Code-Obfuscator) — MIT License.
- **Engine:** [Godot Engine](https://godotengine.org) — MIT License.
- **UI Framework:** [PySide6](https://doc.qt.io/qtforpython/) — LGPL.
- **CLI Framework:** [Typer](https://typer.tiangolo.com/) + [Rich](https://rich.readthedocs.io/).

---

Made with care for Godot developers who want to protect their games with minimal friction.
