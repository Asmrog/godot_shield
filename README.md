# 🛡️ Godot Shield

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/badge/Release-v1.2.2-success.svg)](https://github.com/Asmrog/godot_shield/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

**Automated protection for Godot games — GDScript Obfuscation + AES-256 PCK Encryption.**

Godot Shield is a modern, open-source desktop tool that helps indie developers protect their games from casual reverse engineering and asset ripping. It provides a simple one-click pipeline to obfuscate your code and encrypt your game assets.

> **Demo:** *(Insert your video/GIF here)*


> `![Godot Shield Demo](screenshot.png)`

---

## ✨ Features (v1.2.2)

* 🖥️ **Standalone EXE:** No Python installation required for the GUI. Just download and run.
* 🌍 **Multi-Language Support:** Fully translated UI (English, Arabic, Chinese, Korean, German) with native RTL support for Arabic.
* 🎨 **Modern UI:** A sleek, developer-focused interface with Dark and Light themes.
* 🔐 **Custom Encryption:** Generate a strong AES-256 key or use your own custom password.
* 💾 **Auto-Backups:** Automatically creates a full backup of your project before touching any files.
* 🔄 **Auto-Updater:** Checks for new releases on startup so you never miss an update.
* 🛡️ **Safe Mapping:** The obfuscation mapping file is securely moved to a hidden folder so you never ship it by accident.

---

## 📦 How to Install & Use (Recommended)

1. Go to the **[Releases](https://github.com/Asmrog/godot_shield/releases)** page.
2. Download the latest `GodotShield_vX.X.X.zip` file.
3. Extract the ZIP file to a folder of your choice.
4. Double-click `GodotShield.exe`.
5. Select your Godot project folder, choose your protection level, and click **Protect Game**.

*Note: The `obfuscator` folder must stay in the same directory as `GodotShield.exe`.*

### 🛠️ Running from Source (For Developers)
```bash
git clone https://github.com/Asmrog/godot_shield.git
cd godot_shield
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
git clone https://github.com/June-Tree/Godot-Source-Code-Obfuscator.git obfuscator
python run_gui.py

⚠️ Requirements for "Standard" Export

To export an encrypted .exe file, you must have:

    Godot 4.x installed and added to your system PATH (or set a custom path in Settings).

    Export Templates downloaded in the Godot Editor.

    A "Windows Desktop" export preset configured in your Godot project.

(If these are missing, Godot Shield will still perform the "Basic" obfuscation and warn you about the export failure).
⚠️ The Honest Truth (Disclaimer)

No local software encryption is 100% bulletproof. If the game engine can read the code to run it, a skilled reverse engineer can extract it. Godot Shield is designed to stop 95% of casual asset rippers and script kiddies, raising the barrier significantly without requiring you to rewrite your entire game in C++.
🙏 Credits

    Obfuscation Engine: June-Tree/Godot-Source-Code-Obfuscator

    UI Framework: PySide6

    License: MIT License Ibrahim Anouer 

Made with ❤️ for the Godot community.
