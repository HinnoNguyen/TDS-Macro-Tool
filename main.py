import sys
import os

# Ensure the script directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui import RobloxMacroApp

def main():
    try:
        app = RobloxMacroApp()
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()
    except Exception as e:
        print(f"Failed to launch Roblox Neo Macro: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
