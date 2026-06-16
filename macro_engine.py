import time
import threading
import json
import ctypes
from ctypes import wintypes
from pynput import mouse, keyboard

# --- Win32 SendInput (better Roblox compatibility, especially right-mouse drag) ---
INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x0100
MOUSEEVENTF_ABSOLUTE = 0x8000
WHEEL_DELTA = 120

_BUTTON_DOWN = {
    "left": MOUSEEVENTF_LEFTDOWN,
    "right": MOUSEEVENTF_RIGHTDOWN,
    "middle": MOUSEEVENTF_MIDDLEDOWN,
}
_BUTTON_UP = {
    "left": MOUSEEVENTF_LEFTUP,
    "right": MOUSEEVENTF_RIGHTUP,
    "middle": MOUSEEVENTF_MIDDLEUP,
}


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", INPUT_UNION)]


_extra_info = ctypes.c_ulong(0)
_extra_info_ptr = ctypes.pointer(_extra_info)
_send_input = ctypes.windll.user32.SendInput


def _send_mouse(flags, dx=0, dy=0, mouse_data=0):
    inp = INPUT(
        type=INPUT_MOUSE,
        union=INPUT_UNION(
            mi=MOUSEINPUT(
                dx=dx,
                dy=dy,
                mouseData=mouse_data,
                dwFlags=flags,
                time=0,
                dwExtraInfo=_extra_info_ptr,
            )
        ),
    )
    _send_input(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def win32_move_absolute(x, y):
    screen_w = ctypes.windll.user32.GetSystemMetrics(0)
    screen_h = ctypes.windll.user32.GetSystemMetrics(1)
    if screen_w <= 1 or screen_h <= 1:
        return
    nx = int(x * 65535 / max(screen_w - 1, 1))
    ny = int(y * 65535 / max(screen_h - 1, 1))
    _send_mouse(MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, nx, ny)


def win32_move_relative(dx, dy):
    if dx == 0 and dy == 0:
        return
    _send_mouse(MOUSEEVENTF_MOVE, int(dx), int(dy))


def win32_button(button_name, pressed):
    flags = _BUTTON_DOWN if pressed else _BUTTON_UP
    flag = flags.get(button_name)
    if flag is not None:
        _send_mouse(flag)


def win32_click(button_name, count=1):
    for _ in range(max(count, 1)):
        win32_button(button_name, True)
        time.sleep(0.01)
        win32_button(button_name, False)
        if count > 1:
            time.sleep(0.02)


def _scroll_delta(value):
    value = int(value)
    if value == 0:
        return 0
    if abs(value) < 20:
        return value * WHEEL_DELTA
    return value


def win32_scroll(dx=0, dy=0):
    dy_delta = _scroll_delta(dy)
    if dy_delta != 0:
        _send_mouse(MOUSEEVENTF_WHEEL, 0, 0, dy_delta)
    dx_delta = _scroll_delta(dx)
    if dx_delta != 0:
        _send_mouse(MOUSEEVENTF_HWHEEL, 0, 0, dx_delta)


def button_name_from_event(event):
    return event.get("button", "Button.left").split(".")[1]

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

# --- Win32 Background Inputs Helper ---
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]

def find_roblox_hwnd():
    hwnd = ctypes.windll.user32.FindWindowW("ROBLOXCLASS", None)
    if not hwnd:
        hwnd = ctypes.windll.user32.FindWindowW(None, "Roblox")
    return hwnd

def screen_to_client(hwnd, x, y):
    pt = POINT(int(x), int(y))
    ctypes.windll.user32.ScreenToClient(hwnd, ctypes.byref(pt))
    return pt.x, pt.y

def get_window_rect(hwnd):
    rect = RECT()
    ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect))
    w = rect.right - rect.left
    h = rect.bottom - rect.top
    return w, h

def key_to_vk(key):
    if isinstance(key, str):
        if key.startswith("Key."):
            key_name = key.split(".")[1].lower()
        elif key.startswith("vk."):
            try:
                return int(key.split(".")[1])
            except ValueError:
                return None
        else:
            key_name = key.lower()
    elif isinstance(key, keyboard.Key):
        key_name = key.name.lower()
    elif hasattr(key, 'char') and key.char is not None:
        key_name = key.char.lower()
    elif hasattr(key, 'vk') and key.vk is not None:
        return key.vk
    else:
        key_name = str(key).lower()

    vk_map = {
        "space": 0x20,
        "enter": 0x0D,
        "return": 0x0D,
        "shift": 0x10,
        "ctrl": 0x11,
        "alt": 0x12,
        "tab": 0x09,
        "esc": 0x1B,
        "escape": 0x1B,
        "backspace": 0x08,
        "delete": 0x2E,
        "up": 0x26,
        "down": 0x28,
        "left": 0x25,
        "right": 0x27,
    }
    
    if key_name.startswith('f') and key_name[1:].isdigit():
        f_num = int(key_name[1:])
        if 1 <= f_num <= 12:
            return 0x6F + f_num
            
    if key_name in vk_map:
        return vk_map[key_name]
        
    if len(key_name) == 1:
        vk = ctypes.windll.user32.VkKeyScanW(ord(key_name))
        if vk != -1:
            return vk & 0xFF
            
    return None

def send_background_key(hwnd, vk_code, duration=0.01):
    if not hwnd or vk_code is None:
        return
    ctypes.windll.user32.PostMessageW(hwnd, 0x0100, vk_code, 0)
    time.sleep(duration)
    ctypes.windll.user32.PostMessageW(hwnd, 0x0101, vk_code, 0xC0000001)

def send_background_click(hwnd, button_name, x, y, double_click=False):
    if not hwnd:
        return
    if button_name == "right":
        msg_down = 0x0204
        msg_up = 0x0205
        wparam = 0x0002
    elif button_name == "middle":
        msg_down = 0x0207
        msg_up = 0x0208
        wparam = 0x0010
    else:
        msg_down = 0x0201
        msg_up = 0x0202
        wparam = 0x0001

    lparam = (int(y) << 16) | (int(x) & 0xFFFF)
    
    ctypes.windll.user32.PostMessageW(hwnd, msg_down, wparam, lparam)
    time.sleep(0.01)
    ctypes.windll.user32.PostMessageW(hwnd, msg_up, 0, lparam)
    
    if double_click:
        time.sleep(0.02)
        ctypes.windll.user32.PostMessageW(hwnd, msg_down, wparam, lparam)
        time.sleep(0.01)
        ctypes.windll.user32.PostMessageW(hwnd, msg_up, 0, lparam)

def send_background_move(hwnd, x, y):
    if not hwnd:
        return
    lparam = (int(y) << 16) | (int(x) & 0xFFFF)
    ctypes.windll.user32.PostMessageW(hwnd, 0x0200, 0, lparam)

def send_background_scroll(hwnd, x, y, dx=0, dy=0):
    if not hwnd:
        return
    delta = int(dy) * 120
    wparam = (delta & 0xFFFF) << 16
    pt = POINT(int(x), int(y))
    ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(pt))
    lparam = (pt.y << 16) | (pt.x & 0xFFFF)
    ctypes.windll.user32.PostMessageW(hwnd, 0x020A, wparam, lparam)

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
        self.background_mode = False
        self.click_pos = None
        self.hwnd = None
        self.running = False
        self._thread = None
        self.lock = threading.Lock()

    def start(self, cps=10.0, button_name="left", double_click=False, roblox_only=True, background_mode=False):
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
            self.background_mode = background_mode
            self.hwnd = find_roblox_hwnd()
            
            if self.background_mode:
                if self.hwnd:
                    pt = POINT()
                    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
                    rx, ry = screen_to_client(self.hwnd, pt.x, pt.y)
                    w, h = get_window_rect(self.hwnd)
                    if 0 <= rx <= w and 0 <= ry <= h:
                        self.click_pos = (rx, ry)
                    else:
                        self.click_pos = (w // 2, h // 2)
                else:
                    self.click_pos = None
            else:
                self.click_pos = None

            self.running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        with self.lock:
            self.running = False

    def _run(self):
        while self.running:
            if self.background_mode:
                if self.hwnd:
                    try:
                        button_name = self.button.name
                        x, y = self.click_pos if self.click_pos else (0, 0)
                        send_background_click(self.hwnd, button_name, x, y, self.double_click)
                    except Exception as e:
                        print(f"Background Auto-clicker error: {e}")
                else:
                    self.hwnd = find_roblox_hwnd()
            else:
                if not self.roblox_only or is_roblox_active():
                    try:
                        button_name = self.button.name
                        if self.double_click:
                            win32_click(button_name, 2)
                        else:
                            win32_click(button_name, 1)
                    except Exception as e:
                        print(f"Auto-clicker error: {e}")
            time.sleep(self.interval)


class KeySpammer:
    def __init__(self):
        self.interval = 0.1
        self.keys_to_spam = []
        self.roblox_only = True
        self.background_mode = False
        self.hwnd = None
        self.running = False
        self._thread = None
        self.lock = threading.Lock()

    def start(self, keys_str, interval=0.1, roblox_only=True, background_mode=False):
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
            self.background_mode = background_mode
            self.hwnd = find_roblox_hwnd()
            self.running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        with self.lock:
            self.running = False

    def _run(self):
        while self.running:
            if self.background_mode:
                if self.hwnd:
                    for key in self.keys_to_spam:
                        if not self.running:
                            break
                        try:
                            vk = key_to_vk(key)
                            if vk is not None:
                                send_background_key(self.hwnd, vk, 0.01)
                        except Exception as e:
                            print(f"Background Spammer error: {e}")
                        time.sleep(self.interval)
                else:
                    self.hwnd = find_roblox_hwnd()
                    time.sleep(0.5)
            else:
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
                on_scroll=self._on_scroll,
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

    def _on_scroll(self, x, y, dx, dy):
        if not self.is_recording:
            return
        elapsed = time.time() - self.start_time
        self.events.append({
            "type": "mouse_scroll",
            "x": x,
            "y": y,
            "dx": dx,
            "dy": dy,
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
        self.background_mode = False
        self.hwnd = None
        self._thread = None
        self.lock = threading.Lock()

    def start(self, events, loop=False, speed=1.0, roblox_only=True, background_mode=False):
        with self.lock:
            if self.running:
                return
            self.events = events
            self.loop = loop
            self.speed = max(speed, 0.1)
            self.roblox_only = roblox_only
            self.background_mode = background_mode
            self.hwnd = find_roblox_hwnd()
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
            self._play_mouse_x = None
            self._play_mouse_y = None
            self._play_left_held = False
            self._play_right_held = False
            self._play_middle_held = False
            
            while event_idx < len(self.events) and self.running:
                if self.background_mode:
                    if not self.hwnd:
                        self.hwnd = find_roblox_hwnd()
                        time.sleep(0.1)
                        continue
                else:
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
                    next_event = (
                        self.events[event_idx + 1]
                        if event_idx + 1 < len(self.events)
                        else None
                    )
                    if (
                        not self.background_mode
                        and event.get("type") == "mouse_click"
                        and event.get("pressed") is True
                        and next_event is not None
                        and self._is_simple_click_pair(event, next_event)
                    ):
                        self._execute_event(event, next_event)
                        event_idx += 2
                        continue

                    self._execute_event(event)
                except Exception as e:
                    print(f"Playback execute error: {e}")

                event_idx += 1

            if not self.loop or not self.running:
                self.running = False
                break

    def _is_simple_click_pair(self, press_event, release_event):
        return (
            press_event.get("type") == "mouse_click"
            and press_event.get("pressed") is True
            and release_event.get("type") == "mouse_click"
            and release_event.get("pressed") is False
            and press_event.get("x") == release_event.get("x")
            and press_event.get("y") == release_event.get("y")
            and press_event.get("button") == release_event.get("button")
        )

    def _move_playback_cursor(self, x, y):
        is_held = self._play_left_held or self._play_right_held or self._play_middle_held
        if is_held and self._play_mouse_x is not None and self._play_mouse_y is not None:
            win32_move_relative(x - self._play_mouse_x, y - self._play_mouse_y)
        else:
            win32_move_absolute(x, y)
        self._play_mouse_x = x
        self._play_mouse_y = y

    def _execute_event(self, event, next_event=None):
        if self.background_mode and self.hwnd:
            self._execute_background_event(event, next_event)
            return

        etype = event["type"]
        if etype == "mouse_click":
            x, y = event["x"], event["y"]
            button_name = button_name_from_event(event)
            pressed = event["pressed"]

            if (
                pressed
                and next_event is not None
                and self._is_simple_click_pair(event, next_event)
            ):
                self._move_playback_cursor(x, y)
                win32_click(button_name, 1)
                return

            # Check if this button is currently held and we are releasing it
            is_held_button = False
            if button_name == "right" and self._play_right_held:
                is_held_button = True
            elif button_name == "left" and self._play_left_held:
                is_held_button = True
            elif button_name == "middle" and self._play_middle_held:
                is_held_button = True

            if not (is_held_button and not pressed):
                if self._play_mouse_x != x or self._play_mouse_y != y:
                    self._move_playback_cursor(x, y)

            win32_button(button_name, pressed)
            if button_name == "right":
                self._play_right_held = pressed
            elif button_name == "left":
                self._play_left_held = pressed
            elif button_name == "middle":
                self._play_middle_held = pressed
        elif etype == "mouse_move":
            self._move_playback_cursor(event["x"], event["y"])
        elif etype == "mouse_scroll":
            x, y = event["x"], event["y"]
            if self._play_mouse_x != x or self._play_mouse_y != y:
                self._move_playback_cursor(x, y)
            win32_scroll(event.get("dx", 0), event.get("dy", 0))
        elif etype == "key_press":
            key = deserialize_key(event["key"])
            keyboard_controller.press(key)
        elif etype == "key_release":
            key = deserialize_key(event["key"])
            keyboard_controller.release(key)

    def _execute_background_event(self, event, next_event=None):
        etype = event["type"]
        if etype in ["mouse_click", "mouse_move", "mouse_scroll"]:
            cx, cy = screen_to_client(self.hwnd, event["x"], event["y"])
            
            if etype == "mouse_click":
                button_name = button_name_from_event(event)
                pressed = event["pressed"]
                
                if pressed:
                    if button_name == "left":
                        msg = 0x0201
                        wparam = 0x0001
                    elif button_name == "right":
                        msg = 0x0204
                        wparam = 0x0002
                    else:
                        msg = 0x0207
                        wparam = 0x0010
                else:
                    if button_name == "left":
                        msg = 0x0202
                        wparam = 0
                    elif button_name == "right":
                        msg = 0x0205
                        wparam = 0
                    else:
                        msg = 0x0208
                        wparam = 0
                
                lparam = (cy << 16) | (cx & 0xFFFF)
                ctypes.windll.user32.PostMessageW(self.hwnd, msg, wparam, lparam)
                
            elif etype == "mouse_move":
                send_background_move(self.hwnd, cx, cy)
                
            elif etype == "mouse_scroll":
                send_background_scroll(self.hwnd, cx, cy, event.get("dx", 0), event.get("dy", 0))
                
        elif etype == "key_press":
            vk = key_to_vk(event["key"])
            if vk is not None:
                ctypes.windll.user32.PostMessageW(self.hwnd, 0x0100, vk, 0)
                
        elif etype == "key_release":
            vk = key_to_vk(event["key"])
            if vk is not None:
                ctypes.windll.user32.PostMessageW(self.hwnd, 0x0101, vk, 0xC0000001)
