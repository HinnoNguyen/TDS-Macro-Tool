import time
import threading
import json
import ctypes
from pynput import mouse, keyboard

# Helper to check active window
def get_active_window_title():
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value
    except Exception:
        return ""

def is_roblox_active():
    title = get_active_window_title()
    return "Roblox" in title

# Global controllers
mouse_controller = mouse.Controller()
keyboard_controller = keyboard.Controller()

# Serialization helpers
def serialize_key(key):
    if isinstance(key, keyboard.Key):
        return f"Key.{key.name}"
    elif hasattr(key, 'char') and key.char is not None:
        return key.char
    elif hasattr(key, 'vk') and key.vk is not None:
        return f"vk.{key.vk}"
    else:
        return str(key)

def deserialize_key(key_str):
    if key_str.startswith("Key."):
        key_name = key_str.split(".")[1]
        try:
            return getattr(keyboard.Key, key_name)
        except AttributeError:
            return keyboard.Key.space # Fallback
    elif key_str.startswith("vk."):
        vk_code = int(key_str.split(".")[1])
        return keyboard.KeyCode.from_vk(vk_code)
    else:
        # Check if single character
        if len(key_str) == 1:
            return keyboard.KeyCode.from_char(key_str)
        else:
            # Fallback for named keys that might not start with Key.
            try:
                return getattr(keyboard.Key, key_str.lower())
            except AttributeError:
                return keyboard.KeyCode.from_char(key_str[0])

def serialize_button(button):
    return f"Button.{button.name}"

def deserialize_button(button_str):
    button_name = button_str.split(".")[1]
    return getattr(mouse.Button, button_name)


class AutoClicker:
    def __init__(self):
        self.interval = 0.1
        self.button = mouse.Button.left
        self.double_click = False
        self.roblox_only = True
        self.running = False
        self._thread = None
        self.lock = threading.Lock()

    def start(self, cps=10.0, button_name="left", double_click=False, roblox_only=True):
        with self.lock:
            if self.running:
                return
            self.interval = 1.0 / max(cps, 0.1)
            # Set button
            if button_name == "left":
                self.button = mouse.Button.left
            elif button_name == "right":
                self.button = mouse.Button.right
            else:
                self.button = mouse.Button.middle
            self.double_click = double_click
            self.roblox_only = roblox_only
            self.running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        with self.lock:
            self.running = False

    def _run(self):
        while self.running:
            if not self.roblox_only or is_roblox_active():
                try:
                    if self.double_click:
                        mouse_controller.click(self.button, 2)
                    else:
                        mouse_controller.click(self.button, 1)
                except Exception as e:
                    print(f"Auto-clicker error: {e}")
            time.sleep(self.interval)


class KeySpammer:
    def __init__(self):
        self.interval = 0.1
        self.keys_to_spam = []
        self.roblox_only = True
        self.running = False
        self._thread = None
        self.lock = threading.Lock()

    def start(self, keys_str, interval=0.1, roblox_only=True):
        with self.lock:
            if self.running:
                return
            # Parse keys_str: can be like "space", "e", "w,a,s,d"
            # Split by comma or treat as single characters
            if ',' in keys_str:
                self.keys_to_spam = [k.strip() for k in keys_str.split(',') if k.strip()]
            else:
                # If it's a known special key like "space", "enter", etc.
                special_keys = ["space", "enter", "shift", "ctrl", "alt", "tab", "esc", "backspace"]
                if keys_str.lower() in special_keys:
                    self.keys_to_spam = [f"Key.{keys_str.lower()}"]
                else:
                    self.keys_to_spam = list(keys_str)

            self.interval = max(interval, 0.01)
            self.roblox_only = roblox_only
            self.running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        with self.lock:
            self.running = False

    def _run(self):
        while self.running:
            if not self.roblox_only or is_roblox_active():
                for key in self.keys_to_spam:
                    if not self.running:
                        break
                    try:
                        k = deserialize_key(key)
                        keyboard_controller.press(k)
                        time.sleep(0.01) # Short press duration
                        keyboard_controller.release(k)
                    except Exception as e:
                        print(f"Spammer error: {e}")
                    time.sleep(self.interval)
            else:
                time.sleep(0.1) # Cool down when inactive


class MacroRecorder:
    def __init__(self):
        self.events = []
        self.is_recording = False
        self.start_time = None
        self.mouse_listener = None
        self.keyboard_listener = None
        self.record_mouse_move = False
        self.lock = threading.Lock()

    def start(self, record_mouse_move=False):
        with self.lock:
            if self.is_recording:
                return
            self.events = []
            self.record_mouse_move = record_mouse_move
            self.start_time = time.time()
            self.is_recording = True

            self.mouse_listener = mouse.Listener(
                on_click=self._on_click,
                on_move=self._on_move if self.record_mouse_move else None
            )
            self.keyboard_listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )

            self.mouse_listener.start()
            self.keyboard_listener.start()

    def stop(self):
        with self.lock:
            if not self.is_recording:
                return
            self.is_recording = False
            if self.mouse_listener:
                self.mouse_listener.stop()
                self.mouse_listener = None
            if self.keyboard_listener:
                self.keyboard_listener.stop()
                self.keyboard_listener = None

    def _on_click(self, x, y, button, pressed):
        if not self.is_recording:
            return
        elapsed = time.time() - self.start_time
        self.events.append({
            "type": "mouse_click",
            "x": x,
            "y": y,
            "button": serialize_button(button),
            "pressed": pressed,
            "time": elapsed
        })

    def _on_move(self, x, y):
        if not self.is_recording:
            return
        elapsed = time.time() - self.start_time
        self.events.append({
            "type": "mouse_move",
            "x": x,
            "y": y,
            "time": elapsed
        })

    def _on_press(self, key):
        if not self.is_recording:
            return
        elapsed = time.time() - self.start_time
        self.events.append({
            "type": "key_press",
            "key": serialize_key(key),
            "time": elapsed
        })

    def _on_release(self, key):
        if not self.is_recording:
            return
        elapsed = time.time() - self.start_time
        self.events.append({
            "type": "key_release",
            "key": serialize_key(key),
            "time": elapsed
        })

    def save_to_file(self, filepath):
        with open(filepath, 'w') as f:
            json.dump(self.events, f, indent=4)

    def load_from_file(self, filepath):
        with open(filepath, 'r') as f:
            self.events = json.load(f)
        return self.events


class MacroPlayer:
    def __init__(self):
        self.events = []
        self.running = False
        self.roblox_only = True
        self.loop = False
        self.speed = 1.0
        self._thread = None
        self.lock = threading.Lock()

    def start(self, events, loop=False, speed=1.0, roblox_only=True):
        with self.lock:
            if self.running:
                return
            self.events = events
            self.loop = loop
            self.speed = max(speed, 0.1)
            self.roblox_only = roblox_only
            self.running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        with self.lock:
            self.running = False

    def _run(self):
        while self.running:
            if not self.events:
                break

            start_play_time = time.time()
            event_idx = 0
            
            while event_idx < len(self.events) and self.running:
                if self.roblox_only and not is_roblox_active():
                    time.sleep(0.1)
                    continue

                event = self.events[event_idx]
                target_time = event["time"] / self.speed
                elapsed = time.time() - start_play_time

                # Check if we need to sleep
                if elapsed < target_time:
                    sleep_time = target_time - elapsed
                    if sleep_time > 0.05:
                        time.sleep(0.01)
                        continue
                    else:
                        time.sleep(sleep_time)

                try:
                    self._execute_event(event)
                except Exception as e:
                    print(f"Playback execute error: {e}")

                event_idx += 1

            if not self.loop or not self.running:
                self.running = False
                break

    def _execute_event(self, event):
        etype = event["type"]
        if etype == "mouse_click":
            x, y = event["x"], event["y"]
            button = deserialize_button(event["button"])
            pressed = event["pressed"]
            mouse_controller.position = (x, y)
            if pressed:
                mouse_controller.press(button)
            else:
                mouse_controller.release(button)
        elif etype == "mouse_move":
            x, y = event["x"], event["y"]
            mouse_controller.position = (x, y)
        elif etype == "key_press":
            key = deserialize_key(event["key"])
            keyboard_controller.press(key)
        elif etype == "key_release":
            key = deserialize_key(event["key"])
            keyboard_controller.release(key)
