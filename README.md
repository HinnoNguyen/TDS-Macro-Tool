# 🎮 Roblox TDS Macro - Tower Defense Simulator Automation Tool

[Tiếng Việt bên dưới](#tiếng-việt)

**Roblox TDS Macro** is a modern, high-performance, and feature-rich desktop automation app built using Python, CustomTkinter, and Pynput. It features a sleek Catppuccin Mocha dark theme with emerald green, neon cyan, and rose accents, tailored specifically for Roblox TDS (Tower Defense Simulator) gamers.

> [!IMPORTANT]
> 💻 **Platform Support**: **Windows Only**. This tool relies on Windows active window APIs (`ctypes.windll.user32`) for Roblox process targeting and is configured with Windows batch launch scripts.

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

## 🛠️ Languages & Frameworks
- **Python**: Core programming language.
- **CustomTkinter**: GUI library for a modern dark-themed user interface.
- **Pynput**: For global mouse and keyboard listener and controller APIs.
- **ctypes**: Windows User32 APIs for Roblox active window checking and precise input simulation.

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

---
---

## Tiếng Việt

**Roblox TDS Macro** là ứng dụng tự động hóa dành cho máy tính được phát triển bằng Python, CustomTkinter và Pynput với giao diện tối tối hiện đại màu Catppuccin Mocha cực kỳ đẹp mắt, tối ưu hóa riêng cho các game thủ Roblox TDS (Tower Defense Simulator).

> [!IMPORTANT]
> 💻 **Hỗ trợ hệ điều hành**: **Chỉ hỗ trợ Windows**. Công cụ này sử dụng API kiểm tra cửa sổ hoạt động của Windows (`ctypes.windll.user32`) để tự động nhận diện game Roblox và đi kèm tệp khởi chạy nhanh `.bat` riêng cho Windows.

---

## ✨ Tính năng nổi bật

### 1. 🖱️ Tự động click chuột (Auto Clicker)
- **Clicks Per Second (CPS)**: Tốc độ từ 1 đến 100 lần click/giây.
- **Nút chuột**: Hỗ trợ Click Trái, Click Phải và Click Giữa.
- **Chế độ**: Chọn click đơn hoặc click đúp chuột.
- **Tự động dừng thông minh**: Tự động tạm dừng click khi bạn Alt+Tab chuyển cửa sổ khỏi Roblox.
- **Phím tắt mặc định**: **`F6`** (Bật/Tắt toàn hệ thống).

### 2. ⌨️ Tự động gõ phím (Key Spammer)
- **Chuỗi ký tự**: Gõ một phím đơn (ví dụ: `space`, `e`) hoặc chuỗi phím cách nhau bởi dấu phẩy (ví dụ: `w,s`).
- **Độ trễ**: Chỉnh từ 0.01 giây đến 10.0 giây giữa các lần nhấn phím.
- **Phím tắt mặc định**: **`F7`** (Bật/Tắt toàn hệ thống).

### 3. ⏺️ Ghi & Phát lại Macro (Macro Recorder & Player)
- **Nút điều khiển riêng biệt**:
  - **🔴 Start Recording** (Phím tắt: **`F8`**): Bắt đầu ghi thao tác chuột/phím.
  - **⏹️ Stop Recording** (Phím tắt: **`F8`**): Dừng ghi thao tác.
  - **▶️ Start Playback** (Phím tắt: **`F9`**): Bắt đầu phát lại macro.
  - **⏹️ Stop Playback** (Phím tắt: **`F9`**): Dừng phát lại macro lập tức.
- **Tọa độ chuột**: Tùy chọn bật/tắt ghi lại chuyển động chuột.
- **Lặp vô hạn (Loop)**: Giúp macro lặp lại liên tục cho đến khi nhấn dừng.
- **Tốc độ phát**: Điều chỉnh tốc độ phát từ **0.1x** đến **10.0x**.
- **Xuất/Nhập tệp**: Lưu các macro dưới dạng file `.json` để tải lại khi cần.

### 🌟 Cài đặt sẵn (Presets)
- **TDS Anti-AFK**: Tự động nhảy mỗi 30 giây tránh bị Roblox kích do treo máy trong trận đấu TDS kéo dài.
- **TDS Auto Skip Wave**: Tự động nhấn phím `f` mỗi 1.0 giây để tự động bỏ qua lượt (skip wave).
- **TDS Commander/DJ Ability Chain**: Tự động nhấn chuỗi phím `1, 2, 3` mỗi 10.0 giây để tự động kích hoạt kỹ năng Commander/DJ liên tục.
- **TDS Fast Upgrade/Placement**: Auto clicker chuột trái 100 CPS để nâng cấp hoặc đặt lính cực nhanh.

---

## 🛠️ Ngôn ngữ & Thư viện (Languages & Frameworks)
- **Python**: Ngôn ngữ lập trình chính.
- **CustomTkinter**: Thư viện thiết kế giao diện đồ họa (GUI) hiện đại với giao diện Dark theme.
- **Pynput**: Thư viện theo dõi và giả lập các thao tác bấm phím/click chuột toàn hệ thống.
- **ctypes**: Sử dụng Win32 API để kiểm tra cửa sổ Roblox đang hoạt động và truyền tín hiệu mô phỏng chính xác.

---

## 🚀 Hướng dẫn khởi chạy
1. Cài đặt các thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```
2. Chạy ứng dụng:
   - Trên Windows: Double-click file `run.bat` hoặc chạy lệnh:
     ```bash
     python main.py
     ```
