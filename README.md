
# 🛡️ Godot Shield

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/badge/Release-v1.2.2-success.svg)](https://github.com/Asmrog/godot_shield/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows-blue.svg)]()

**Automated protection for Godot games — GDScript Obfuscation + AES-256 PCK Encryption.**

Godot Shield is a modern, open-source desktop tool designed to help indie developers protect their games from casual reverse engineering and asset ripping. It provides a simple one-click pipeline to obfuscate your code and encrypt your game assets.

## 🎬 Demo Video

*Click the image below to watch how it works:*

<img width="400" height="225" alt="1118" src="https://github.com/user-attachments/assets/fd7677e9-272c-4bf8-800b-cdef9cf9b1cc" />

---

## ✨ Features

* 🖥️ **Standalone Windows EXE:** No Python installation required for the GUI. Just download and run.
* 🌍 **Multi-Language Support:** Fully translated UI (English, Arabic, Chinese, Korean, German) with native Right-to-Left (RTL) support for Arabic.
* 🔐 **Custom AES-256 Encryption:** Use your own secret password to derive the encryption key, giving you full control.
* 💾 **Auto-Backups:** Automatically creates a safe, full backup of your project before touching any files.
* 🔄 **Auto-Updater:** Checks for new releases on startup so you never miss an update.
* 🛡️ **Safe Mapping:** The obfuscation mapping file (`.json`) is moved to a hidden folder so you never ship it by accident.
* 🎨 **Modern UI:** A sleek, developer-focused interface with Dark and Light themes.

---

## 📦 Installation

1. Go to the **[Releases](https://github.com/Asmrog/godot_shield/releases)** page.
2. Download the latest `GodotShield_vX.X.X.zip` file.
3. Extract the ZIP file to a folder of your choice.
4. Double-click `GodotShield.exe` to launch the application.

*(Note: The `obfuscator` folder must remain in the same directory as `GodotShield.exe` for the tool to work).*

### ⚠️ Requirements for "Standard" Export
To export an encrypted `.exe` file, you must have:
* **Godot 4.x** installed.
* **Export Templates** downloaded in the Godot Editor.
* A **"Windows Desktop"** export preset configured in your Godot project.

---

## ⚠️ The Honest Truth (Disclaimer)
No local software encryption is 100% bulletproof. If the game engine can read the code to run it, a skilled reverse engineer can extract it. **Godot Shield is designed to stop 95% of casual asset rippers**, raising the barrier significantly without requiring you to rewrite your entire game in C++.

---

## 👨‍💻 Author & License

Created with ❤️ by **[Ibrahim Anouer](https://github.com/Asmrog)**.

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

### 🙏 Credits
* **Obfuscation Engine:** [June-Tree/Godot-Source-Code-Obfuscator](https://github.com/June-Tree/Godot-Source-Code-Obfuscator)
* **UI Framework:** PySide6

⭐ **If you find this tool useful, please consider giving it a star!** It helps the project grow and reach more developers.
