# 🎮 Roblox TDS Macro - Tower Defense Simulator Automation Tool

**Roblox TDS Macro** is a modern, high-performance, and feature-rich desktop automation app built using Python, CustomTkinter, and Pynput. It features a sleek Catppuccin Mocha dark theme with emerald green, neon cyan, and rose accents, tailored specifically for Roblox TDS (Tower Defense Simulator) gamers.

> [!IMPORTANT]
> 💻 **Platform Support**: **Windows Only**. This tool relies on Windows active window APIs (`ctypes.windll.user32`) for Roblox process targeting and is configured with Windows batch launch scripts.

### 🛠️ Languages, Frameworks & Tools
<p align="left">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/CustomTkinter-2d2d2d?style=for-the-badge&logo=python&logoColor=89dceb" />
  <img src="https://img.shields.io/badge/pynput-4F5D75?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" />
</p>

### 📋 Requirements
- **Operating System**: Windows 10 or 11 (64-bit).
- **Python Version**: Python 3.9+ (make sure it's added to System PATH).
- **Required Packages**:
  - `customtkinter` (for modern dark GUI)
  - `pynput` (for mouse & keyboard interaction)

---

## ✨ Features

### 1. 🖱️ Auto Clicker
- **Clicks Per Second (CPS)**: Adjust from 1 to 100 CPS.
- **Mouse Button**: Choose Left Click, Right Click, or Middle Click.
- **Double Click**: Toggle double clicking mode.
- **Roblox Integration**: Check "Only Active in Roblox" to auto-pause clicks if you Alt+Tab out of the game.
- **Default Hotkey**: **`F6`** (Global Toggle).

### 2. ⌨️ Key Spammer
- **Spam Mode**: Spam single keys (e.g. `space`, `e`) or sequences (e.g., `w,s` to walk back and forth).
- **Interval**: Set custom delays from 0.01s to 10.0s between key presses.
- **Default Hotkey**: **`F7`** (Global Toggle).

### 3. ⏺️ Macro Recorder & Player
- **Separate Controls**:
  - **🔴 Start Recording** (Hotkey: **`F8`**): Begins recording mouse/keyboard events.
  - **⏹️ Stop Recording** (Hotkey: **`F8`**): Finishes recording.
  - **▶️ Start Playback** (Hotkey: **`F9`**): Starts playing back recorded events.
  - **⏹️ Stop Playback** (Hotkey: **`F9`**): Halts playback.
- **Movement Tracking**: Toggle recording mouse coordinates (`x`/`y`).
- **Loop Option**: Toggle looping the macro indefinitely.
- **Speed Control**: Adjust playback speed from **0.1x** to **10.0x**.
- **Save/Load**: Save recorded paths to `.json` files.

### 🌟 TDS Game Presets
- **TDS Anti-AFK**: Spams Jump (`space`) every 30s to stay active in long matches.
- **TDS Auto Skip Wave**: Spams `f` key every 1.0s to auto skip waves.
- **TDS Commander/DJ Ability Chain**: Spams `1,2,3` keys sequentially every 10.0s to chain DJ/Commander abilities.
- **TDS Fast Upgrade/Placement**: Left clicker set to 100 CPS for rapid tower upgrades/placement.

---

## 🚀 How to Run
1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   - On Windows: Double-click `run.bat` or run:
     ```bash
     python main.py
     ```
