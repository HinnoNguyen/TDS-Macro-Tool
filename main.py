import sys
import os
import ctypes

# Ensure the script directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Fix taskbar icon grouping/display on Windows
try:
    myappid = 'hinnonguyen.tdsmacro.tool.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

from gui import HinnoMacroApp

def main():
    try:
        app = HinnoMacroApp()
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()
    except Exception as e:
        print(f"Failed to launch Roblox Neo Macro: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
