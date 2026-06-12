import os
import time
import json
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from pynput import keyboard
from PIL import Image, ImageTk

# Import our macro classes
from macro_engine import (
    AutoClicker,
    KeySpammer,
    MacroRecorder,
    MacroPlayer,
    is_roblox_active,
    get_active_window_title
)

# Design System - Catppuccin Mocha Palette
BG_COLOR = "#1e1e2e"
SIDEBAR_COLOR = "#11111b"
FRAME_COLOR = "#181825"
TEXT_COLOR = "#cdd6f4"
SUBTEXT_COLOR = "#a6adc8"
CYAN = "#89dceb"
GREEN = "#a6e3a1"
RED = "#f38ba8"
BLUE = "#89b4fa"
LAVENDER = "#b4befe"
DARK_GRAY = "#313244"

ctk.set_appearance_mode("dark")

class RobloxMacroApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure Window
        self.title("Roblox TDS Macro - Tower Defense Simulator Automation")
        self.geometry("900x600")
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)

        # Set Window Icon
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(current_dir, "logo.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Failed to load window icon: {e}")

        # Initialize engines
        self.clicker = AutoClicker()
        self.spammer = KeySpammer()
        self.recorder = MacroRecorder()
        self.player = MacroPlayer()

        # UI Strings for hotkeys (defaults)
        self.hotkey_strings = {
            "clicker": "F6",
            "spammer": "F7",
            "recorder": "F8",
            "player": "F9"
        }
        
        # Parsed strings for pynput GlobalHotKeys
        self.hotkeys_parsed = {
            "clicker": "<f6>",
            "spammer": "<f7>",
            "recorder": "<f8>",
            "player": "<f9>"
        }

        # Keep track of hotkey listening state
        self.hotkey_listener = None
        self.start_hotkey_listener()

        # Layout Setup: Left Sidebar & Right Content Frame
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_content_area()

        # Active tab tracking
        self.active_tab = "recorder"
        self.select_tab("recorder")

        # Periodically check states and update status bar
        self.update_status_loop()

    def start_hotkey_listener(self):
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
            except Exception:
                pass
            self.hotkey_listener = None

        mapping = {
            self.hotkeys_parsed["clicker"]: self.toggle_clicker,
            self.hotkeys_parsed["spammer"]: self.toggle_spammer,
            self.hotkeys_parsed["recorder"]: self.toggle_recorder,
            self.hotkeys_parsed["player"]: self.toggle_player
        }

        # Safe tkinter wrapper to run callbacks in main thread
        def wrap_action(action_func):
            return lambda: self.after(0, action_func)

        wrapped_mapping = {k: wrap_action(v) for k, v in mapping.items()}

        try:
            self.hotkey_listener = keyboard.GlobalHotKeys(wrapped_mapping)
            self.hotkey_listener.start()
        except Exception as e:
            print(f"Error starting global hotkey listener: {e}")

    # ================= UI SETUP =================

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=SIDEBAR_COLOR, border_width=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)

        self.title_lbl = ctk.CTkLabel(
            self.sidebar, 
            text="🎮 TDS MACRO", 
            font=ctk.CTkFont(size=20, weight="bold"), 
            text_color=CYAN
        )
        self.title_lbl.grid(row=0, column=0, padx=20, pady=(30, 20), sticky="w")

        self.subtitle_lbl = ctk.CTkLabel(
            self.sidebar, 
            text="TDS Specialty Edition", 
            font=ctk.CTkFont(size=12, slant="italic"), 
            text_color=SUBTEXT_COLOR
        )
        self.subtitle_lbl.grid(row=0, column=0, padx=20, pady=(60, 20), sticky="w")

        self.nav_btns = {}
        tabs = [
            ("clicker", "🖱️  Auto Clicker"),
            ("spammer", "⌨️  Key Spammer"),
            ("recorder", "⏺️  Macro Recorder"),
            ("presets", "🌟  Game Presets"),
            ("settings", "⚙️  Settings")
        ]

        for i, (tab_id, label) in enumerate(tabs, start=1):
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                anchor="w",
                fg_color="transparent",
                text_color=TEXT_COLOR,
                hover_color=DARK_GRAY,
                font=ctk.CTkFont(size=14, weight="normal"),
                height=40,
                corner_radius=8,
                command=lambda tid=tab_id: self.select_tab(tid)
            )
            btn.grid(row=i, column=0, padx=15, pady=8, sticky="ew")
            self.nav_btns[tab_id] = btn

        self.status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.status_frame.grid(row=7, column=0, padx=20, pady=20, sticky="ew")
        
        self.status_dot = ctk.CTkLabel(
            self.status_frame, 
            text="●", 
            font=ctk.CTkFont(size=18), 
            text_color=RED
        )
        self.status_dot.grid(row=0, column=0, sticky="w")

        self.status_text = ctk.CTkLabel(
            self.status_frame, 
            text="Roblox Inactive", 
            font=ctk.CTkFont(size=12, weight="bold"), 
            text_color=TEXT_COLOR
        )
        self.status_text.grid(row=0, column=1, padx=8, sticky="w")

    def setup_content_area(self):
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)

        self.frames = {}
        self.frames["clicker"] = self.create_clicker_frame()
        self.frames["spammer"] = self.create_spammer_frame()
        self.frames["recorder"] = self.create_recorder_frame()
        self.frames["presets"] = self.create_presets_frame()
        self.frames["settings"] = self.create_settings_frame()

    # ================= TAB FRAMES CREATION =================

    def create_clicker_frame(self):
        frame = ctk.CTkFrame(self.content_container, fg_color=FRAME_COLOR, corner_radius=12, border_color=DARK_GRAY, border_width=1)
        
        lbl = ctk.CTkLabel(frame, text="Auto Clicker Config", font=ctk.CTkFont(size=18, weight="bold"), text_color=CYAN)
        lbl.pack(anchor="w", padx=25, pady=(20, 15))

        cps_card = ctk.CTkFrame(frame, fg_color=BG_COLOR, corner_radius=8)
        cps_card.pack(fill="x", padx=25, pady=10)

        cps_lbl = ctk.CTkLabel(cps_card, text="Clicks Per Second (CPS)", font=ctk.CTkFont(size=14, weight="bold"))
        cps_lbl.grid(row=0, column=0, padx=15, pady=10, sticky="w")

        self.cps_slider = ctk.CTkSlider(cps_card, from_=1, to=100, number_of_steps=99, button_color=CYAN, button_hover_color=BLUE, progress_color=CYAN)
        self.cps_slider.set(10)
        self.cps_slider.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")
        self.cps_slider.bind("<ButtonRelease-1>", lambda e: self.update_cps_val())
        self.cps_slider.bind("<B1-Motion>", lambda e: self.update_cps_val())

        self.cps_val_lbl = ctk.CTkLabel(cps_card, text="10 CPS", font=ctk.CTkFont(size=14, weight="bold"), text_color=CYAN)
        self.cps_val_lbl.grid(row=1, column=1, padx=15, pady=(0, 15), sticky="e")

        cps_card.grid_columnconfigure(0, weight=1)

        opts_card = ctk.CTkFrame(frame, fg_color="transparent")
        opts_card.pack(fill="x", padx=25, pady=10)

        btn_lbl = ctk.CTkLabel(opts_card, text="Mouse Button:", font=ctk.CTkFont(size=13, weight="bold"))
        btn_lbl.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="w")
        self.mouse_btn_opt = ctk.CTkOptionMenu(
            opts_card, 
            values=["Left Click", "Right Click", "Middle Click"],
            fg_color=DARK_GRAY,
            button_color=DARK_GRAY,
            button_hover_color=BLUE,
            dropdown_fg_color=FRAME_COLOR,
            dropdown_hover_color=DARK_GRAY
        )
        self.mouse_btn_opt.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.double_click_var = tk.BooleanVar(value=False)
        self.double_click_chk = ctk.CTkCheckBox(
            opts_card, 
            text="Double Click", 
            variable=self.double_click_var,
            checkmark_color=BG_COLOR,
            fg_color=CYAN,
            hover_color=BLUE
        )
        self.double_click_chk.grid(row=0, column=2, padx=20, pady=10, sticky="w")

        self.clicker_roblox_var = tk.BooleanVar(value=True)
        self.clicker_roblox_chk = ctk.CTkCheckBox(
            opts_card, 
            text="Only Active in Roblox", 
            variable=self.clicker_roblox_var,
            checkmark_color=BG_COLOR,
            fg_color=CYAN,
            hover_color=BLUE
        )
        self.clicker_roblox_chk.grid(row=1, column=0, columnspan=3, padx=(0, 10), pady=10, sticky="w")

        actions_card = ctk.CTkFrame(frame, fg_color="transparent")
        actions_card.pack(fill="both", expand=True, padx=25, pady=20)

        self.clicker_start_btn = ctk.CTkButton(
            actions_card, 
            text="START (F6)", 
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=GREEN,
            hover_color="#8ed189",
            text_color=BG_COLOR,
            height=50,
            command=self.toggle_clicker
        )
        self.clicker_start_btn.pack(fill="x", side="bottom")

        tips_lbl = ctk.CTkLabel(
            actions_card, 
            text="💡 Pro Tip: Toggle Auto Clicker at any time by pressing F6 on your keyboard.",
            text_color=SUBTEXT_COLOR,
            font=ctk.CTkFont(size=12)
        )
        tips_lbl.pack(pady=10)

        return frame

    def create_spammer_frame(self):
        frame = ctk.CTkFrame(self.content_container, fg_color=FRAME_COLOR, corner_radius=12, border_color=DARK_GRAY, border_width=1)
        
        lbl = ctk.CTkLabel(frame, text="Key Spammer Config", font=ctk.CTkFont(size=18, weight="bold"), text_color=CYAN)
        lbl.pack(anchor="w", padx=25, pady=(20, 15))

        inputs_card = ctk.CTkFrame(frame, fg_color=BG_COLOR, corner_radius=8)
        inputs_card.pack(fill="x", padx=25, pady=10)

        key_lbl = ctk.CTkLabel(inputs_card, text="Keys to Spam (e.g. 'e' or 'space' or 'w,a,s,d'):", font=ctk.CTkFont(size=13, weight="bold"))
        key_lbl.pack(anchor="w", padx=15, pady=(10, 5))

        self.spammer_keys_entry = ctk.CTkEntry(
            inputs_card, 
            placeholder_text="e.g. space (or e or w,s)",
            fg_color=FRAME_COLOR,
            border_color=DARK_GRAY,
            text_color=TEXT_COLOR
        )
        self.spammer_keys_entry.insert(0, "space")
        self.spammer_keys_entry.pack(fill="x", padx=15, pady=(0, 15))

        interval_lbl = ctk.CTkLabel(inputs_card, text="Spam Interval (seconds):", font=ctk.CTkFont(size=13, weight="bold"))
        interval_lbl.pack(anchor="w", padx=15, pady=(0, 5))

        self.spammer_interval_slider = ctk.CTkSlider(inputs_card, from_=0.01, to=10.0, number_of_steps=100, button_color=CYAN, button_hover_color=BLUE, progress_color=CYAN)
        self.spammer_interval_slider.set(0.1)
        self.spammer_interval_slider.pack(fill="x", padx=15, pady=(0, 5))
        self.spammer_interval_slider.bind("<ButtonRelease-1>", lambda e: self.update_interval_val())
        self.spammer_interval_slider.bind("<B1-Motion>", lambda e: self.update_interval_val())

        self.spammer_val_lbl = ctk.CTkLabel(inputs_card, text="0.10s", font=ctk.CTkFont(size=14, weight="bold"), text_color=CYAN)
        self.spammer_val_lbl.pack(anchor="e", padx=15, pady=(0, 15))

        opts_card = ctk.CTkFrame(frame, fg_color="transparent")
        opts_card.pack(fill="x", padx=25, pady=10)

        self.spammer_roblox_var = tk.BooleanVar(value=True)
        self.spammer_roblox_chk = ctk.CTkCheckBox(
            opts_card, 
            text="Only Active in Roblox", 
            variable=self.spammer_roblox_var,
            checkmark_color=BG_COLOR,
            fg_color=CYAN,
            hover_color=BLUE
        )
        self.spammer_roblox_chk.pack(anchor="w")

        actions_card = ctk.CTkFrame(frame, fg_color="transparent")
        actions_card.pack(fill="both", expand=True, padx=25, pady=15)

        self.spammer_start_btn = ctk.CTkButton(
            actions_card, 
            text="START (F7)", 
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=GREEN,
            hover_color="#8ed189",
            text_color=BG_COLOR,
            height=50,
            command=self.toggle_spammer
        )
        self.spammer_start_btn.pack(fill="x", side="bottom")

        tips_lbl = ctk.CTkLabel(
            actions_card, 
            text="💡 Pro Tip: Toggle Key Spammer at any time by pressing F7 on your keyboard.",
            text_color=SUBTEXT_COLOR,
            font=ctk.CTkFont(size=12)
        )
        tips_lbl.pack(pady=10)

        return frame

    def create_recorder_frame(self):
        frame = ctk.CTkFrame(self.content_container, fg_color=FRAME_COLOR, corner_radius=12, border_color=DARK_GRAY, border_width=1)
        
        lbl = ctk.CTkLabel(frame, text="Macro Recorder & Player", font=ctk.CTkFont(size=18, weight="bold"), text_color=CYAN)
        lbl.pack(anchor="w", padx=25, pady=(20, 15))

        cfg_card = ctk.CTkFrame(frame, fg_color=BG_COLOR, corner_radius=8)
        cfg_card.pack(fill="x", padx=25, pady=10)

        mouse_info = ctk.CTkLabel(
            cfg_card,
            text="Mouse clicks and scroll wheel are always recorded (position + direction). You must click/scroll in-game while recording.",
            font=ctk.CTkFont(size=12),
            text_color=SUBTEXT_COLOR,
            wraplength=780,
            justify="left",
        )
        mouse_info.pack(anchor="w", padx=15, pady=(10, 5))

        self.rec_mouse_move_var = tk.BooleanVar(value=True)
        self.rec_mouse_move_chk = ctk.CTkCheckBox(
            cfg_card, 
            text="Also record mouse movement between clicks (optional, larger files — for camera/drag paths)", 
            variable=self.rec_mouse_move_var,
            checkmark_color=BG_COLOR,
            fg_color=CYAN,
            hover_color=BLUE
        )
        self.rec_mouse_move_chk.pack(anchor="w", padx=15, pady=(0, 10))

        self.player_loop_var = tk.BooleanVar(value=True)
        self.player_loop_chk = ctk.CTkCheckBox(
            cfg_card, 
            text="Loop Playback", 
            variable=self.player_loop_var,
            checkmark_color=BG_COLOR,
            fg_color=CYAN,
            hover_color=BLUE
        )
        self.player_loop_chk.pack(anchor="w", padx=15, pady=(0, 10))

        speed_lbl = ctk.CTkLabel(cfg_card, text="Playback Speed:", font=ctk.CTkFont(size=13, weight="bold"))
        speed_lbl.pack(anchor="w", padx=15)
        
        self.speed_slider = ctk.CTkSlider(cfg_card, from_=0.1, to=10.0, number_of_steps=99, button_color=CYAN, button_hover_color=BLUE, progress_color=CYAN)
        self.speed_slider.set(1.0)
        self.speed_slider.pack(fill="x", padx=15, pady=(0, 5))
        self.speed_slider.bind("<ButtonRelease-1>", lambda e: self.update_speed_val())
        self.speed_slider.bind("<B1-Motion>", lambda e: self.update_speed_val())

        self.speed_val_lbl = ctk.CTkLabel(cfg_card, text="1.0x", font=ctk.CTkFont(size=14, weight="bold"), text_color=CYAN)
        self.speed_val_lbl.pack(anchor="e", padx=15, pady=(0, 10))

        action_row = ctk.CTkFrame(frame, fg_color="transparent")
        action_row.pack(fill="x", padx=25, pady=10)

        self.load_btn = ctk.CTkButton(
            action_row, 
            text="📂 Load Macro", 
            fg_color=DARK_GRAY,
            hover_color=BLUE,
            command=self.load_macro_dialog
        )
        self.load_btn.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.save_btn = ctk.CTkButton(
            action_row, 
            text="💾 Save Macro", 
            fg_color=DARK_GRAY,
            hover_color=BLUE,
            command=self.save_macro_dialog,
            state="disabled"
        )
        self.save_btn.grid(row=0, column=1, padx=10, sticky="ew")

        self.loaded_macro_lbl = ctk.CTkLabel(
            action_row, 
            text="No macro loaded (0 events)", 
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color=SUBTEXT_COLOR
        )
        self.loaded_macro_lbl.grid(row=0, column=2, padx=10, sticky="w")
        action_row.grid_columnconfigure(0, weight=1)
        action_row.grid_columnconfigure(1, weight=1)
        action_row.grid_columnconfigure(2, weight=2)

        ctrl_row = ctk.CTkFrame(frame, fg_color="transparent")
        ctrl_row.pack(fill="both", expand=True, padx=25, pady=10)

        # Recording Section
        rec_frame = ctk.CTkFrame(ctrl_row, fg_color=BG_COLOR, corner_radius=8)
        rec_frame.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="nsew")
        
        rec_lbl = ctk.CTkLabel(rec_frame, text="Macro Recording", font=ctk.CTkFont(size=14, weight="bold"), text_color=RED)
        rec_lbl.pack(pady=(10, 5))

        self.record_start_btn = ctk.CTkButton(
            rec_frame, 
            text="🔴 Start Recording (F8)", 
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=RED,
            hover_color="#f8a2b9",
            text_color=BG_COLOR,
            command=self.start_recording
        )
        self.record_start_btn.pack(fill="x", padx=15, pady=5)

        self.record_stop_btn = ctk.CTkButton(
            rec_frame, 
            text="⏹️ Stop Recording (F8)", 
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=DARK_GRAY,
            hover_color=BLUE,
            command=self.stop_recording,
            state="disabled"
        )
        self.record_stop_btn.pack(fill="x", padx=15, pady=(5, 15))

        # Playback Section
        play_frame = ctk.CTkFrame(ctrl_row, fg_color=BG_COLOR, corner_radius=8)
        play_frame.grid(row=0, column=1, padx=(10, 0), pady=5, sticky="nsew")

        play_lbl = ctk.CTkLabel(play_frame, text="Macro Playback", font=ctk.CTkFont(size=14, weight="bold"), text_color=GREEN)
        play_lbl.pack(pady=(10, 5))

        self.play_start_btn = ctk.CTkButton(
            play_frame, 
            text="▶️ Start Playback (F9)", 
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=GREEN,
            hover_color="#8ed189",
            text_color=BG_COLOR,
            command=self.start_playback,
            state="disabled"
        )
        self.play_start_btn.pack(fill="x", padx=15, pady=5)

        self.play_stop_btn = ctk.CTkButton(
            play_frame, 
            text="⏹️ Stop Playback (F9)", 
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=DARK_GRAY,
            hover_color=RED,
            command=self.stop_playback,
            state="disabled"
        )
        self.play_stop_btn.pack(fill="x", padx=15, pady=(5, 15))
        
        ctrl_row.grid_columnconfigure(0, weight=1)
        ctrl_row.grid_columnconfigure(1, weight=1)

        return frame

    def create_presets_frame(self):
        frame = ctk.CTkFrame(self.content_container, fg_color=FRAME_COLOR, corner_radius=12, border_color=DARK_GRAY, border_width=1)
        
        lbl = ctk.CTkLabel(frame, text="Roblox Game Presets", font=ctk.CTkFont(size=18, weight="bold"), text_color=CYAN)
        lbl.pack(anchor="w", padx=25, pady=(20, 15))

        desc_lbl = ctk.CTkLabel(
            frame, 
            text="Quick configurations for common Roblox scenarios. Select a preset to load it instantly.",
            text_color=SUBTEXT_COLOR,
            font=ctk.CTkFont(size=13)
        )
        desc_lbl.pack(anchor="w", padx=25, pady=(0, 15))

        presets_list = [
            {
                "title": "🛡️ TDS Anti-AFK (Keep Connected)",
                "desc": "Spams Jump (Space) every 30 seconds to prevent getting disconnected from long TDS matches.",
                "action": lambda: self.load_preset_anti_afk()
            },
            {
                "title": "⏩ TDS Auto Skip Wave (F-Spam)",
                "desc": "Configures Key Spammer to spam the 'f' key every 1.0s to instantly skip waves when voting is available.",
                "action": lambda: self.load_preset_tds_skip()
            },
            {
                "title": "📣 TDS Commander/DJ Ability Chain (1, 2, 3)",
                "desc": "Configures Key Spammer to spam keys '1, 2, 3' sequentially every 10.0s to chain DJ or Commander abilities.",
                "action": lambda: self.load_preset_tds_abilities()
            },
            {
                "title": "⚡ TDS Fast Upgrade/Placement (100 CPS)",
                "desc": "Configures the Auto Clicker for ultra-fast 100 clicks per second (Left Click) to spam tower placements/upgrades.",
                "action": lambda: self.load_preset_fast_click()
            }
        ]

        for p in presets_list:
            card = ctk.CTkFrame(frame, fg_color=BG_COLOR, corner_radius=8)
            card.pack(fill="x", padx=25, pady=6)

            card_title = ctk.CTkLabel(card, text=p["title"], font=ctk.CTkFont(size=14, weight="bold"), text_color=CYAN)
            card_title.grid(row=0, column=0, padx=15, pady=(8, 2), sticky="w")

            card_desc = ctk.CTkLabel(card, text=p["desc"], font=ctk.CTkFont(size=12), text_color=SUBTEXT_COLOR, justify="left", wraplength=450)
            card_desc.grid(row=1, column=0, padx=15, pady=(0, 8), sticky="w")

            card_btn = ctk.CTkButton(
                card, 
                text="Load Preset", 
                width=100, 
                fg_color=BLUE,
                hover_color=LAVENDER,
                text_color=BG_COLOR,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=p["action"]
            )
            card_btn.grid(row=0, column=1, rowspan=2, padx=15, pady=10, sticky="e")

            card.grid_columnconfigure(0, weight=1)

        return frame

    def create_settings_frame(self):
        frame = ctk.CTkFrame(self.content_container, fg_color=FRAME_COLOR, corner_radius=12, border_color=DARK_GRAY, border_width=1)
        
        lbl = ctk.CTkLabel(frame, text="Global Hotkeys & Configuration", font=ctk.CTkFont(size=18, weight="bold"), text_color=CYAN)
        lbl.pack(anchor="w", padx=25, pady=(20, 15))

        hk_card = ctk.CTkFrame(frame, fg_color=BG_COLOR, corner_radius=8)
        hk_card.pack(fill="x", padx=25, pady=10)

        hk_info = ctk.CTkLabel(
            hk_card, 
            text="Assign Hotkeys (Press the button and select the function key):", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        hk_info.pack(anchor="w", padx=15, pady=10)

        grid_frame = ctk.CTkFrame(hk_card, fg_color="transparent")
        grid_frame.pack(fill="x", padx=15, pady=(0, 15))

        actions = [
            ("clicker", "Toggle Auto Clicker", "F6"),
            ("spammer", "Toggle Key Spammer", "F7"),
            ("recorder", "Toggle Macro Recorder", "F8"),
            ("player", "Toggle Macro Playback", "F9")
        ]

        self.hotkey_buttons = {}

        for row, (action_id, label, default_str) in enumerate(actions):
            lbl_act = ctk.CTkLabel(grid_frame, text=label, font=ctk.CTkFont(size=13))
            lbl_act.grid(row=row, column=0, padx=10, pady=6, sticky="w")

            btn_hk = ctk.CTkButton(
                grid_frame, 
                text=self.hotkey_strings[action_id],
                width=100,
                fg_color=DARK_GRAY,
                hover_color=BLUE,
                command=lambda aid=action_id: self.change_hotkey_flow(aid)
            )
            btn_hk.grid(row=row, column=1, padx=10, pady=6, sticky="e")
            self.hotkey_buttons[action_id] = btn_hk

        grid_frame.grid_columnconfigure(0, weight=1)

        inst_card = ctk.CTkFrame(frame, fg_color="transparent")
        inst_card.pack(fill="both", expand=True, padx=25, pady=15)

        info_title = ctk.CTkLabel(inst_card, text="⚠️ Roblox Background Notice", font=ctk.CTkFont(size=14, weight="bold"), text_color=RED)
        info_title.pack(anchor="w", pady=5)

        info_text = ctk.CTkLabel(
            inst_card, 
            text="1. 'Only Active in Roblox' relies on checking active windows. Ensure Roblox runs in windowed or borderless mode for best compatibility.\n"
                 "2. First Person View: In first-person mode, mouse movement playback may not rotate the camera due to Roblox capturing the physical mouse lock. Play in Third-Person mode with Shift Lock if camera movement simulation is required.\n"
                 "3. DO NOT spam macros in public Roblox chat, as it may violate Roblox Terms of Service.",
            justify="left",
            text_color=SUBTEXT_COLOR,
            font=ctk.CTkFont(size=12),
            wraplength=600
        )
        info_text.pack(anchor="w", pady=5)

        return frame

    # ================= ACTION BINDINGS / PRESETS =================

    def update_cps_val(self):
        val = int(self.cps_slider.get())
        self.cps_val_lbl.configure(text=f"{val} CPS")

    def update_interval_val(self):
        val = self.spammer_interval_slider.get()
        self.spammer_val_lbl.configure(text=f"{val:.2f}s")

    def update_speed_val(self):
        val = self.speed_slider.get()
        self.speed_val_lbl.configure(text=f"{val:.1f}x")

    def select_tab(self, tab_id):
        if hasattr(self, 'active_tab'):
            self.nav_btns[self.active_tab].configure(fg_color="transparent")
            self.frames[self.active_tab].pack_forget()

        self.active_tab = tab_id
        self.nav_btns[tab_id].configure(fg_color=DARK_GRAY)
        self.frames[tab_id].pack(fill="both", expand=True)

    def change_hotkey_flow(self, action_id):
        # Stop main listener during capture
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None

        self.hotkey_buttons[action_id].configure(text="Press Keys...", fg_color=RED)

        # Temporary modifiers state
        self.temp_modifiers = {"ctrl": False, "alt": False, "shift": False}

        def on_press(key):
            # Track modifiers
            if key in [keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
                self.temp_modifiers["ctrl"] = True
                return
            if key in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr]:
                self.temp_modifiers["alt"] = True
                return
            if key in [keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r]:
                self.temp_modifiers["shift"] = True
                return

            # Cancel on Escape
            if key == keyboard.Key.esc:
                self.after(0, lambda: self.cancel_hotkey_change(action_id))
                return False

            # Retrieve key name
            key_name = ""
            if isinstance(key, keyboard.Key):
                key_name = key.name
            elif hasattr(key, 'char') and key.char is not None:
                key_name = key.char
            elif hasattr(key, 'vk') and key.vk is not None:
                key_name = f"vk_{key.vk}"
            else:
                key_name = str(key)

            display_parts = []
            parsed_parts = []

            # Add tracked modifiers
            if self.temp_modifiers["ctrl"]:
                display_parts.append("Ctrl")
                parsed_parts.append("<ctrl>")
            if self.temp_modifiers["alt"]:
                display_parts.append("Alt")
                parsed_parts.append("<alt>")
            if self.temp_modifiers["shift"]:
                display_parts.append("Shift")
                parsed_parts.append("<shift>")

            # Add base key
            if key_name:
                key_name_lower = key_name.lower()
                # If key is standard function key
                if key_name_lower.startswith('f') and key_name_lower[1:].isdigit():
                    display_parts.append(key_name.upper())
                    parsed_parts.append(f"<{key_name_lower}>")
                elif key_name_lower in ["space", "enter", "tab", "backspace", "delete"]:
                    display_parts.append(key_name.capitalize())
                    parsed_parts.append(f"<{key_name_lower}>")
                else:
                    display_parts.append(key_name.upper())
                    parsed_parts.append(key_name_lower)

            parsed_str = "+".join(parsed_parts)
            display_str = "+".join(display_parts)

            # Store mapping
            self.hotkeys_parsed[action_id] = parsed_str
            self.hotkey_strings[action_id] = display_str

            self.after(0, lambda: self.finalize_hotkey_change(action_id, display_str))
            return False

        def on_release(key):
            # Untrack modifiers on release
            if key in [keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
                self.temp_modifiers["ctrl"] = False
            elif key in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr]:
                self.temp_modifiers["alt"] = False
            elif key in [keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r]:
                self.temp_modifiers["shift"] = False

        self.temp_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.temp_listener.start()

    def cancel_hotkey_change(self, action_id):
        old_display = self.hotkey_strings[action_id]
        self.hotkey_buttons[action_id].configure(text=old_display, fg_color=DARK_GRAY)
        self.start_hotkey_listener()

    def finalize_hotkey_change(self, action_id, display_str):
        self.hotkey_buttons[action_id].configure(text=display_str, fg_color=DARK_GRAY)
        self.update_start_stop_button_hotkeys()
        self.start_hotkey_listener()

    def update_start_stop_button_hotkeys(self):
        c_hk = self.hotkey_strings["clicker"]
        s_hk = self.hotkey_strings["spammer"]
        r_hk = self.hotkey_strings["recorder"]
        p_hk = self.hotkey_strings["player"]

        if not self.clicker.running:
            self.clicker_start_btn.configure(text=f"START ({c_hk})")
        else:
            self.clicker_start_btn.configure(text=f"STOP ({c_hk})")

        if not self.spammer.running:
            self.spammer_start_btn.configure(text=f"START ({s_hk})")
        else:
            self.spammer_start_btn.configure(text=f"STOP ({s_hk})")

        self.record_start_btn.configure(text=f"🔴 Start Recording ({r_hk})")
        self.record_stop_btn.configure(text=f"⏹️ Stop Recording ({r_hk})")
        self.play_start_btn.configure(text=f"▶️ Start Playback ({p_hk})")
        self.play_stop_btn.configure(text=f"⏹️ Stop Playback ({p_hk})")

    # ================= TOGGLE ACTIONS =================

    def toggle_clicker(self):
        c_hk = self.hotkey_strings["clicker"]
        if not self.clicker.running:
            cps = self.cps_slider.get()
            btn_text = self.mouse_btn_opt.get()
            button_name = "left"
            if "Right" in btn_text:
                button_name = "right"
            elif "Middle" in btn_text:
                button_name = "middle"
            
            double_click = self.double_click_var.get()
            roblox_only = self.clicker_roblox_var.get()

            self.clicker.start(cps=cps, button_name=button_name, double_click=double_click, roblox_only=roblox_only)
            self.clicker_start_btn.configure(text=f"STOP ({c_hk})", fg_color=RED, hover_color="#f8a2b9")
        else:
            self.clicker.stop()
            self.clicker_start_btn.configure(text=f"START ({c_hk})", fg_color=GREEN, hover_color="#8ed189")

    def toggle_spammer(self):
        s_hk = self.hotkey_strings["spammer"]
        if not self.spammer.running:
            keys_str = self.spammer_keys_entry.get().strip()
            if not keys_str:
                messagebox.showwarning("Warning", "Spam keys input cannot be empty.")
                return
            interval = self.spammer_interval_slider.get()
            roblox_only = self.spammer_roblox_var.get()

            self.spammer.start(keys_str=keys_str, interval=interval, roblox_only=roblox_only)
            self.spammer_start_btn.configure(text=f"STOP ({s_hk})", fg_color=RED, hover_color="#f8a2b9")
        else:
            self.spammer.stop()
            self.spammer_start_btn.configure(text=f"START ({s_hk})", fg_color=GREEN, hover_color="#8ed189")

    def start_recording(self):
        if self.player.running:
            self.stop_playback()
        
        record_mouse = self.rec_mouse_move_var.get()
        self.recorder.start(record_mouse_move=record_mouse)
        
        self.record_start_btn.configure(state="disabled")
        self.record_stop_btn.configure(state="normal")
        self.play_start_btn.configure(state="disabled")
        self.play_stop_btn.configure(state="disabled")
        self.save_btn.configure(state="disabled")

    def stop_recording(self):
        self.recorder.stop()
        
        event_count = len(self.recorder.events)
        self.loaded_macro_lbl.configure(text=f"Recorded: {event_count} events")
        
        self.record_start_btn.configure(state="normal")
        self.record_stop_btn.configure(state="disabled")
        
        if event_count > 0:
            self.play_start_btn.configure(state="normal")
            self.save_btn.configure(state="normal")
        else:
            self.play_start_btn.configure(state="disabled")
            self.save_btn.configure(state="disabled")

    def start_playback(self):
        events = self.recorder.events
        if not events:
            messagebox.showwarning("Warning", "No macro events to play. Record or load a macro first.")
            return
        
        loop = self.player_loop_var.get()
        speed = self.speed_slider.get()
        roblox_only = self.clicker_roblox_var.get()
        
        self.player.start(events, loop=loop, speed=speed, roblox_only=roblox_only)
        
        self.record_start_btn.configure(state="disabled")
        self.record_stop_btn.configure(state="disabled")
        self.play_start_btn.configure(state="disabled")
        self.play_stop_btn.configure(state="normal")

    def stop_playback(self):
        self.player.stop()
        
        self.record_start_btn.configure(state="normal")
        self.record_stop_btn.configure(state="disabled")
        if len(self.recorder.events) > 0:
            self.play_start_btn.configure(state="normal")
        self.play_stop_btn.configure(state="disabled")

    def toggle_recorder(self):
        if not self.recorder.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def toggle_player(self):
        if not self.player.running:
            self.start_playback()
        else:
            self.stop_playback()

    # ================= LOAD/SAVE FILES =================

    def save_macro_dialog(self):
        if not self.recorder.events:
            messagebox.showwarning("Warning", "No macro events to save.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            title="Save Roblox Macro"
        )
        
        if file_path:
            try:
                self.recorder.save_to_file(file_path)
                messagebox.showinfo("Success", f"Macro successfully saved to:\n{os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save macro:\n{e}")

    def load_macro_dialog(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json")],
            title="Load Roblox Macro"
        )
        
        if file_path:
            try:
                events = self.recorder.load_from_file(file_path)
                event_count = len(events)
                self.loaded_macro_lbl.configure(text=f"Loaded: {os.path.basename(file_path)} ({event_count} events)")
                
                if event_count > 0:
                    self.play_btn.configure(state="normal")
                    self.save_btn.configure(state="normal")
                else:
                    self.play_btn.configure(state="disabled")
                    self.save_btn.configure(state="disabled")
                    
                messagebox.showinfo("Success", f"Loaded macro successfully with {event_count} events!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load macro:\n{e}")

    # ================= PRESETS LOAD =================

    def load_preset_anti_afk(self):
        self.select_tab("spammer")
        self.spammer_keys_entry.delete(0, tk.END)
        self.spammer_keys_entry.insert(0, "space")
        self.spammer_interval_slider.set(30.0)
        self.update_interval_val()
        self.spammer_roblox_chk.select()
        messagebox.showinfo("Preset Loaded", "Loaded 'TDS Anti-AFK' preset!\n- Key: space (Jump)\n- Interval: 30 seconds\nGo to the Key Spammer tab and press START or F7.")

    def load_preset_fast_click(self):
        self.select_tab("clicker")
        self.cps_slider.set(100.0)
        self.update_cps_val()
        self.mouse_btn_opt.set("Left Click")
        self.double_click_var.set(False)
        messagebox.showinfo("Preset Loaded", "Loaded 'TDS Fast Upgrade/Placement' preset!\n- Speed: 100 CPS\n- Button: Left Click\nGo to the Auto Clicker tab and press START or F6.")

    def load_preset_tds_skip(self):
        self.select_tab("spammer")
        self.spammer_keys_entry.delete(0, tk.END)
        self.spammer_keys_entry.insert(0, "f")
        self.spammer_interval_slider.set(1.0)
        self.update_interval_val()
        self.spammer_roblox_chk.select()
        messagebox.showinfo("Preset Loaded", "Loaded 'TDS Auto Skip Wave' preset!\n- Key: f\n- Interval: 1.0 second\nGo to the Key Spammer tab and press START or F7.")

    def load_preset_tds_abilities(self):
        self.select_tab("spammer")
        self.spammer_keys_entry.delete(0, tk.END)
        self.spammer_keys_entry.insert(0, "1,2,3")
        self.spammer_interval_slider.set(10.0)
        self.update_interval_val()
        self.spammer_roblox_chk.select()
        messagebox.showinfo("Preset Loaded", "Loaded 'TDS Commander/DJ Ability Chain' preset!\n- Keys: 1, 2, 3 (sequentially)\n- Interval: 10.0 seconds\nGo to the Key Spammer tab and press START or F7.")

    # ================= REPEATABLE STATUS CHECKS =================

    def update_status_loop(self):
        active = is_roblox_active()
        if active:
            self.status_dot.configure(text_color=GREEN)
            self.status_text.configure(text="Roblox Active", text_color=TEXT_COLOR)
        else:
            self.status_dot.configure(text_color=RED)
            self.status_text.configure(text="Roblox Inactive", text_color=SUBTEXT_COLOR)

        c_hk = self.hotkey_strings["clicker"]
        s_hk = self.hotkey_strings["spammer"]
        r_hk = self.hotkey_strings["recorder"]
        p_hk = self.hotkey_strings["player"]

        if self.clicker.running:
            self.clicker_start_btn.configure(text=f"STOP ({c_hk})", fg_color=RED, hover_color="#f8a2b9")
        else:
            self.clicker_start_btn.configure(text=f"START ({c_hk})", fg_color=GREEN, hover_color="#8ed189")

        if self.spammer.running:
            self.spammer_start_btn.configure(text=f"STOP ({s_hk})", fg_color=RED, hover_color="#f8a2b9")
        else:
            self.spammer_start_btn.configure(text=f"START ({s_hk})", fg_color=GREEN, hover_color="#8ed189")

        # Sync Recorder buttons state
        if self.recorder.is_recording:
            self.record_start_btn.configure(state="disabled")
            self.record_stop_btn.configure(state="normal")
            self.play_start_btn.configure(state="disabled")
            self.play_stop_btn.configure(state="disabled")
            self.save_btn.configure(state="disabled")
        else:
            self.record_start_btn.configure(state="disabled" if self.player.running else "normal")
            self.record_stop_btn.configure(state="disabled")
            
            event_count = len(self.recorder.events)
            if event_count > 0:
                self.play_start_btn.configure(state="disabled" if self.player.running else "normal")
                self.save_btn.configure(state="disabled" if self.player.running else "normal")
            else:
                self.play_start_btn.configure(state="disabled")
                self.save_btn.configure(state="disabled")

        # Sync Player buttons state
        if self.player.running:
            self.play_start_btn.configure(state="disabled")
            self.play_stop_btn.configure(state="normal")
            self.record_start_btn.configure(state="disabled")
            self.record_stop_btn.configure(state="disabled")
        else:
            self.play_stop_btn.configure(state="disabled")
            if not self.recorder.is_recording:
                self.record_start_btn.configure(state="normal")
                if len(self.recorder.events) > 0:
                    self.play_start_btn.configure(state="normal")

        self.after(500, self.update_status_loop)

    def on_closing(self):
        self.clicker.stop()
        self.spammer.stop()
        self.recorder.stop()
        self.player.stop()
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.destroy()

if __name__ == "__main__":
    app = RobloxMacroApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
