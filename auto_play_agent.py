import os
import time
import ctypes
import numpy as np
import cv2
from PIL import ImageGrab, Image
import macro_engine as me

# Define RECT structure for ctypes
class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long)
    ]

# --- Screen Grabber ---
def capture_roblox_window(hwnd):
    """
    Grabs the screen area of the Roblox window.
    Note: The window must be visible on the screen (not minimized).
    """
    if not hwnd:
        return None
    rect = RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
    # bbox format: (left, top, right, bottom)
    bbox = (rect.left, rect.top, rect.right, rect.bottom)
    
    # Ensure window is valid
    if bbox[2] - bbox[0] <= 0 or bbox[3] - bbox[1] <= 0:
        return None
        
    try:
        screenshot = ImageGrab.grab(bbox)
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"Error capturing window: {e}")
        return None

# --- CV Template Matching ---
def find_template_on_screen(screen_img, template_path, threshold=0.8):
    """
    Finds a template image (e.g. a button) on the screen.
    Returns (x, y) coordinates of the center of the match, or None if not found.
    """
    if screen_img is None or not os.path.exists(template_path):
        return None
        
    template = cv2.imread(template_path)
    if template is None:
        return None
        
    h, w = template.shape[:2]
    res = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    
    if max_val >= threshold:
        # Calculate center coordinates relative to Roblox client area
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        return center_x, center_y
    return None


class TDSAutoPlayAgent:
    def __init__(self):
        self.hwnd = None
        self.state = "INIT"
        self.running = False
        self.wave = 0
        self.game_start_time = 0
        self.action_index = 0
        
        # Path to private templates (ignored by git)
        self.template_dir = r"D:\Tools\Macro\templates"
        os.makedirs(self.template_dir, exist_ok=True)
        
        # Template paths
        self.t_lobby_sign = os.path.join(self.template_dir, "lobby_sign.png")
        self.t_ready_btn = os.path.join(self.template_dir, "ready_btn.png")
        self.t_confirm_btn = os.path.join(self.template_dir, "confirm_btn.png")
        self.t_skip_btn = os.path.join(self.template_dir, "skip_btn.png")
        self.t_victory = os.path.join(self.template_dir, "victory.png")
        self.t_defeat = os.path.join(self.template_dir, "defeat.png")
        self.t_relobby_btn = os.path.join(self.template_dir, "relobby_btn.png")

        # --- Game Plan / Placement Sequence ---
        # Modify this to fit your map, towers, and upgrades strategy
        # Format: (delay_seconds_from_start, action_type, details)
        self.game_plan = [
            # Time (s), Action, Details (e.g., place tower '1' at relative coordinates)
            (10, "place", {"key": "1", "x": 400, "y": 300}), # Place Tower 1
            (30, "place", {"key": "1", "x": 450, "y": 300}), # Place Tower 2
            (60, "upgrade", {"x": 400, "y": 300}),          # Select Tower 1 and upgrade
            (90, "place", {"key": "2", "x": 500, "y": 320}), # Place Tower 3 (e.g. Farm)
            (120, "upgrade", {"x": 450, "y": 300}),         # Select Tower 2 and upgrade
            (180, "upgrade", {"x": 400, "y": 300}),         # Upgrade Tower 1 again
        ]

    def log(self, message):
        print(f"[{time.strftime('%H:%M:%S')}] [TDS-Agent] {message}")

    def click_relative(self, x, y):
        """Clicks at coordinates relative to the client area of the Roblox window."""
        if self.hwnd:
            me.send_background_click(self.hwnd, "left", x, y)
            time.sleep(0.1)

    def press_key(self, key_str):
        """Sends a keystroke to Roblox in the background."""
        if self.hwnd:
            vk = me.key_to_vk(key_str)
            if vk is not None:
                me.send_background_key(self.hwnd, vk, 0.05)
                time.sleep(0.1)

    def select_map_and_lobby_sequence(self, screen):
        """Handles selecting map, modifier, timescale and hitting play."""
        self.log("Handling Lobby / Map Selection Sequence...")
        
        # 1. Click Map Button (Modify coordinates based on your resolution)
        # Or search for map template
        self.click_relative(250, 400) # Mock click map
        time.sleep(1.0)
        
        # 2. Click Modifiers (Mock click)
        self.click_relative(300, 450)
        time.sleep(1.0)
        
        # 3. Click Speed/Timescale
        self.click_relative(350, 450)
        time.sleep(1.0)
        
        # 4. Click Confirm/Play button using Template Match
        confirm_coords = find_template_on_screen(screen, self.t_confirm_btn)
        if confirm_coords:
            self.log(f"Confirm button found at {confirm_coords}, clicking...")
            self.click_relative(confirm_coords[0], confirm_coords[1])
            time.sleep(2.0)
            self.state = "WAIT_IN_GAME"
        else:
            # Fallback hardcoded click if template matching isn't configured
            self.click_relative(450, 500)
            self.state = "WAIT_IN_GAME"

    def start(self):
        self.running = True
        self.state = "LOBBY"
        self.log("TDS AutoPlay Agent Started!")
        
        while self.running:
            self.hwnd = me.find_roblox_hwnd()
            if not self.hwnd:
                self.log("Roblox window not found. Waiting...")
                time.sleep(5)
                continue
            
            # Capture current frame
            screen = capture_roblox_window(self.hwnd)
            if screen is None:
                time.sleep(1)
                continue
                
            # Check for win/lose screen at any point
            if self.state not in ["LOBBY", "WAIT_IN_GAME", "INIT"]:
                victory_coords = find_template_on_screen(screen, self.t_victory)
                defeat_coords = find_template_on_screen(screen, self.t_defeat)
                if victory_coords or defeat_coords:
                    self.log("Game Over screen detected! (Victory or Defeat)")
                    self.state = "RESET"

            # --- State Machine ---
            if self.state == "LOBBY":
                # Detect if in lobby
                # Or proceed directly if we are sure we just spawned
                self.select_map_and_lobby_sequence(screen)
                
            elif self.state == "WAIT_IN_GAME":
                self.log("Waiting to spawn into the game map...")
                # Search for the "Ready" button template or "Skip Wave" button template indicating we are in-game
                ready_coords = find_template_on_screen(screen, self.t_ready_btn)
                if ready_coords:
                    self.log(f"Ready button detected at {ready_coords}! Clicking and starting match.")
                    self.click_relative(ready_coords[0], ready_coords[1])
                    time.sleep(1)
                    
                    self.state = "PLAYING"
                    self.game_start_time = time.time()
                    self.action_index = 0
                else:
                    time.sleep(3) # Wait and check screen again
                    
            elif self.state == "PLAYING":
                # 1. Check if we have actions to run in our game plan
                elapsed_time = time.time() - self.game_start_time
                
                if self.action_index < len(self.game_plan):
                    next_time, action_type, details = self.game_plan[self.action_index]
                    
                    if elapsed_time >= next_time:
                        self.log(f"Executing plan action {self.action_index}: {action_type} - {details}")
                        if action_type == "place":
                            # Press hotkey to select tower
                            self.press_key(details["key"])
                            time.sleep(0.5)
                            # Click on map coordinate to place it
                            self.click_relative(details["x"], details["y"])
                            time.sleep(0.5)
                            # Press esc or click empty space to deselect placement mode
                            self.press_key("Key.esc")
                        elif action_type == "upgrade":
                            # Click tower to select it
                            self.click_relative(details["x"], details["y"])
                            time.sleep(0.5)
                            # Click upgrade button (can also use template matching to find the upgrade button on GUI)
                            # Mock click upgrade coordinate (e.g. upgrade button position on sidebar)
                            self.click_relative(100, 500) 
                            time.sleep(0.5)
                            # Deselect
                            self.press_key("Key.esc")
                            
                        self.action_index += 1

                # 2. Auto-Skip waves (Spam key 'f' / click skip button if template matches)
                skip_coords = find_template_on_screen(screen, self.t_skip_btn)
                if skip_coords:
                    self.log("Skip wave button detected! Clicking to skip wave.")
                    self.click_relative(skip_coords[0], skip_coords[1])
                else:
                    # Alternately spam 'f' key
                    self.press_key("f")
                    
                time.sleep(1.0)
                
            elif self.state == "RESET":
                self.log("Handling Game Reset / Re-lobby...")
                relobby_coords = find_template_on_screen(screen, self.t_relobby_btn)
                if relobby_coords:
                    self.log(f"Re-lobby button found at {relobby_coords}. Clicking...")
                    self.click_relative(relobby_coords[0], relobby_coords[1])
                    time.sleep(10) # Wait for lobby loading
                    self.state = "LOBBY"
                else:
                    # Hardcoded backup click for Re-lobby
                    self.click_relative(450, 450)
                    time.sleep(10)
                    self.state = "LOBBY"
                    
            time.sleep(1.0)

    def stop(self):
        self.running = False
        self.log("Agent stopped.")


if __name__ == "__main__":
    # To run this script: python auto_play_agent.py
    # Please add your template images in D:\Tools\Macro\templates\ directory.
    # Templates needed:
    # 1. ready_btn.png (Screenshot of 'Ready' button inside the match)
    # 2. confirm_btn.png (Screenshot of lobby 'Play'/'Confirm' button)
    # 3. skip_btn.png (Screenshot of 'Skip Wave' button)
    # 4. relobby_btn.png (Screenshot of 'Re-lobby' or 'Return to Lobby' button at end game)
    # 5. victory.png & defeat.png (Screenshots of end-game banners)
    
    agent = TDSAutoPlayAgent()
    try:
        agent.start()
    except KeyboardInterrupt:
        agent.stop()
