import os
import time
import json
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import customtkinter as ctk
from PIL import Image, ImageTk

# Import macro engine functions
import macro_engine as me

# Color Palette matching the user's screenshot
BG_COLOR = "#0c0c0e"          # Very dark base background
SIDEBAR_COLOR = "#121214"     # Sleeker dark sidebar
CARD_COLOR = "#1c1c22"        # Dark gray cards
INPUT_BG = "#151518"          # Dark inputs
TEXT_MAIN = "#ffffff"         # White primary text
TEXT_MUTED = "#9999a3"        # Muted gray secondary text
BLUE_ACCENT = "#0a84ff"       # macOS Blue
GREEN_ACCENT = "#30d158"      # macOS Green
RED_ACCENT = "#ff453a"        # macOS Red
BORDER_COLOR = "#2c2c35"      # Subtle border

ctk.set_appearance_mode("dark")

class HinnoMacroApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Geometry and Window Config
        self.title("Hinno Macro Pro")
        self.geometry("1020x720")
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)

        # Set Window and Taskbar Icon
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(current_dir, "logo.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Failed to load window icon: {e}")

        # Active Macro and State Data
        self.active_macro = "coin"
        self.hotkey_record = "["
        self.hotkey_play = "]"
        self.macros = {
            "coin": {
                "desc": "Automates Victory/Defeat detection using template image matching. If victory: loops lobby + strategy steps. If defeat: restarts map directly (skips lobby).",
                "victory_img": "",
                "defeat_img": "",
                "play_again_x": 0,
                "play_again_y": 0,
                "section": "strategy",  # "lobby" or "strategy"
                "lobby_steps": [],
                "strategy_steps": []
            },
            "Militant": {
                "desc": "Strategy macro for Militant defense setup. Perfect for Solo and Duo placements.",
                "victory_img": "",
                "defeat_img": "",
                "play_again_x": 0,
                "play_again_y": 0,
                "section": "strategy",
                "lobby_steps": [],
                "strategy_steps": []
            },
            "gem": {
                "desc": "Gem farming loop strategy. Replays specific map loops to maximize gem rewards.",
                "victory_img": "",
                "defeat_img": "",
                "play_again_x": 0,
                "play_again_y": 0,
                "section": "strategy",
                "lobby_steps": [],
                "strategy_steps": []
            }
        }

        # Initialize engines
        self.running_thread = None
        self.playback_running = False
        self.recording_running = False
        self.recorder_thread = None

        # Build UI Elements
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_main_area()

        # Select initial tab/macro
        self.select_macro(self.active_macro)

        # Global Hotkey listener for F8 / F9 control
        self.start_global_listener()

    # ================= GLOBAL HOTKEYS =================
    def get_pynput_key(self, key_str):
        from pynput import keyboard
        key_str = key_str.lower()
        if key_str.startswith('f') and key_str[1:].isdigit():
            f_num = int(key_str[1:])
            return getattr(keyboard.Key, f"f{f_num}")
        if key_str == "space":
            return keyboard.Key.space
        if key_str == "caps lock" or key_str == "caps_lock":
            return keyboard.Key.caps_lock
        return keyboard.KeyCode.from_char(key_str[0])

    def start_global_listener(self):
        # Stop existing listener if running
        if hasattr(self, "listener") and self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass

        from pynput import keyboard
        
        rec_key = self.get_pynput_key(self.hotkey_record)
        play_key = self.get_pynput_key(self.hotkey_play)

        def on_press(key):
            if key == rec_key:
                self.after(0, self.toggle_recording)
            elif key == play_key:
                self.after(0, self.toggle_playback)

        self.listener = keyboard.Listener(on_press=on_press)
        self.listener.start()

    # ================= SIDEBAR UI =================
    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=260, fg_color=SIDEBAR_COLOR, corner_radius=0, border_width=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_columnconfigure(0, weight=1)
        
        # 1. Header Title with circle icon
        header_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 20), sticky="ew")
        
        # Load user's logo.jpg
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(current_dir, "logo.jpg")
        logo_loaded = False
        
        if os.path.exists(logo_path):
            try:
                pil_img = Image.open(logo_path)
                # Display logo as a clean 28x28 icon
                logo_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(28, 28))
                logo_lbl = ctk.CTkLabel(header_frame, image=logo_image, text="")
                logo_lbl.grid(row=0, column=0, sticky="w")
                logo_loaded = True
            except Exception as e:
                print(f"Error loading logo.jpg: {e}")
                
        if not logo_loaded:
            # Fallback blue circle icon containing white play icon
            icon_lbl = ctk.CTkLabel(
                header_frame, 
                text="▶", 
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="#ffffff",
                fg_color=BLUE_ACCENT,
                corner_radius=10,
                width=20,
                height=20
            )
            icon_lbl.grid(row=0, column=0, sticky="w")
        
        title_lbl = ctk.CTkLabel(
            header_frame, 
            text="Hinno Macro Pro", 
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT_MAIN
        )
        title_lbl.grid(row=0, column=1, padx=8, sticky="w")

        # 2. List Label
        list_lbl = ctk.CTkLabel(
            self.sidebar, 
            text="My Macros", 
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=TEXT_MUTED
        )
        list_lbl.grid(row=1, column=0, padx=20, pady=(5, 5), sticky="w")

        # 3. Macros Scroll List
        self.macros_scroll = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.macros_scroll.grid(row=2, column=0, padx=12, pady=5, sticky="nsew")
        self.macros_scroll.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(2, weight=1)

        self.macro_buttons = {}
        self.update_sidebar_list()

        # 4. Bottom Status Frame: System Access Granted
        status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        status_frame.grid(row=3, column=0, padx=20, pady=(5, 5), sticky="ew")
        
        status_dot = ctk.CTkLabel(status_frame, text="●", font=ctk.CTkFont(size=14), text_color=GREEN_ACCENT)
        status_dot.grid(row=0, column=0, sticky="w")
        
        status_txt = ctk.CTkLabel(status_frame, text="System Access Granted", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED)
        status_txt.grid(row=0, column=1, padx=8, sticky="w")

        # 5. Add New Macro Card/Button
        new_macro_card = ctk.CTkFrame(self.sidebar, fg_color=CARD_COLOR, corner_radius=10, border_color=BORDER_COLOR, border_width=1)
        new_macro_card.grid(row=4, column=0, padx=15, pady=(5, 15), sticky="ew")
        new_macro_card.grid_columnconfigure(0, weight=4)
        new_macro_card.grid_columnconfigure(1, weight=1)

        new_btn = ctk.CTkButton(
            new_macro_card,
            text="+ New Macro",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="transparent",
            hover_color=BORDER_COLOR,
            text_color=TEXT_MAIN,
            height=36,
            command=self.create_new_macro
        )
        new_btn.grid(row=0, column=0, sticky="ew", padx=(5, 2), pady=5)

        settings_btn = ctk.CTkButton(
            new_macro_card,
            text="⚙️",
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            hover_color=BORDER_COLOR,
            text_color=TEXT_MAIN,
            width=36,
            height=36,
            command=self.open_settings_dialog
        )
        settings_btn.grid(row=0, column=1, sticky="ew", padx=(2, 5), pady=5)

    def update_sidebar_list(self):
        # Clear old widgets
        for widget in self.macros_scroll.winfo_children():
            widget.destroy()

        self.macro_buttons = {}
        for row, macro_name in enumerate(self.macros.keys()):
            # Calculate total steps count
            total_steps = len(self.macros[macro_name]["lobby_steps"]) + len(self.macros[macro_name]["strategy_steps"])
            
            btn_frame = ctk.CTkFrame(
                self.macros_scroll, 
                fg_color=CARD_COLOR if macro_name == self.active_macro else "transparent", 
                corner_radius=8,
                height=45
            )
            btn_frame.grid(row=row, column=0, pady=4, padx=5, sticky="ew")
            btn_frame.grid_columnconfigure(0, weight=1)
            btn_frame.pack_propagate(False)

            # Left side icon
            lbl_icon = ctk.CTkLabel(btn_frame, text="⌨️", font=ctk.CTkFont(size=13))
            lbl_icon.pack(side="left", padx=10)

            # Macro Name
            lbl_name = ctk.CTkLabel(
                btn_frame, 
                text=macro_name, 
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold" if macro_name == self.active_macro else "normal"),
                text_color=TEXT_MAIN
            )
            lbl_name.pack(side="left")

            # Steps Count
            lbl_steps = ctk.CTkLabel(
                btn_frame, 
                text=f"{total_steps} steps", 
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=TEXT_MUTED
            )
            lbl_steps.pack(side="right", padx=12)

            # Click binding to select macro
            def make_select_func(name):
                return lambda e: self.select_macro(name)

            btn_frame.bind("<Button-1>", make_select_func(macro_name))
            for child in btn_frame.winfo_children():
                child.bind("<Button-1>", make_select_func(macro_name))

            self.macro_buttons[macro_name] = btn_frame

    # ================= MAIN AREA UI =================
    def setup_main_area(self):
        self.main_area = ctk.CTkFrame(self, fg_color=BG_COLOR, corner_radius=0, border_width=0)
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=25, pady=(15, 15))
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(3, weight=1)

        # 1. Top Bar: App Title
        app_title = ctk.CTkLabel(
            self.main_area, 
            text="HinnoMacroPro", 
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
            text_color=TEXT_MUTED
        )
        app_title.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # 2. Header Card (Macro Name, Status, Controls)
        header_card = ctk.CTkFrame(self.main_area, fg_color="transparent")
        header_card.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        header_card.grid_columnconfigure(0, weight=1)

        title_frame = ctk.CTkFrame(header_card, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w")
        
        self.lbl_active_macro = ctk.CTkLabel(
            title_frame, 
            text="coin", 
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=TEXT_MAIN
        )
        self.lbl_active_macro.grid(row=0, column=0, sticky="w")

        self.lbl_status = ctk.CTkLabel(
            title_frame, 
            text="Finished", 
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_MUTED
        )
        self.lbl_status.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Right aligned buttons
        btn_frame = ctk.CTkFrame(header_card, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")

        self.btn_record = ctk.CTkButton(
            btn_frame,
            text=f"● Record ({self.hotkey_record})",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="transparent",
            text_color=RED_ACCENT,
            border_color=RED_ACCENT,
            border_width=1,
            hover_color="#3a1c1a",
            width=110,
            height=34,
            command=self.toggle_recording
        )
        self.btn_record.grid(row=0, column=0, padx=10)

        self.btn_run = ctk.CTkButton(
            btn_frame,
            text=f"▶ Run Macro ({self.hotkey_play})",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=BLUE_ACCENT,
            text_color=TEXT_MAIN,
            hover_color="#0066cc",
            width=130,
            height=34,
            command=self.toggle_playback
        )
        self.btn_run.grid(row=0, column=1)

        # 3. Configuration Card (Description, Victory/Defeat selector)
        self.setup_config_card()

        # 4. Step Section Pill & Tab Frame
        self.setup_step_section()

    def setup_config_card(self):
        config_card = ctk.CTkFrame(self.main_area, fg_color=CARD_COLOR, corner_radius=12, border_color=BORDER_COLOR, border_width=1)
        config_card.grid(row=2, column=0, sticky="ew", pady=(5, 10), padx=2)
        config_card.grid_columnconfigure(1, weight=1)

        # Macro Description
        self.lbl_desc = ctk.CTkLabel(
            config_card,
            text="Automates Victory/Defeat detection using template image matching. If victory: loops lobby + strategy steps. If defeat: restarts map directly (skips lobby).",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_MUTED,
            wraplength=680,
            justify="left"
        )
        self.lbl_desc.grid(row=0, column=0, columnspan=3, padx=20, pady=(15, 12), sticky="w")

        # Form Divider
        divider = ctk.CTkFrame(config_card, height=1, fg_color=BORDER_COLOR)
        divider.grid(row=1, column=0, columnspan=3, sticky="ew", padx=20, pady=(0, 12))

        # Victory Image Row
        lbl_vic = ctk.CTkLabel(config_card, text="Victory Image:", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=TEXT_MUTED)
        lbl_vic.grid(row=2, column=0, padx=(20, 10), pady=6, sticky="w")

        self.ent_victory = ctk.CTkEntry(config_card, placeholder_text="Path to Victory image (PNG)", fg_color=INPUT_BG, border_color=BORDER_COLOR, height=28)
        self.ent_victory.grid(row=2, column=1, sticky="ew", pady=6)

        btn_choose_vic = ctk.CTkButton(config_card, text="Choose...", width=80, height=28, fg_color=BORDER_COLOR, text_color=TEXT_MAIN, hover_color="#33333d", command=lambda: self.choose_image("victory"))
        btn_choose_vic.grid(row=2, column=2, padx=(10, 20), pady=6, sticky="e")

        # Defeat Image Row
        lbl_def = ctk.CTkLabel(config_card, text="Defeat Image:", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=TEXT_MUTED)
        lbl_def.grid(row=3, column=0, padx=(20, 10), pady=6, sticky="w")

        self.ent_defeat = ctk.CTkEntry(config_card, placeholder_text="Path to Defeat image (PNG)", fg_color=INPUT_BG, border_color=BORDER_COLOR, height=28)
        self.ent_defeat.grid(row=3, column=1, sticky="ew", pady=6)

        btn_choose_def = ctk.CTkButton(config_card, text="Choose...", width=80, height=28, fg_color=BORDER_COLOR, text_color=TEXT_MAIN, hover_color="#33333d", command=lambda: self.choose_image("defeat"))
        btn_choose_def.grid(row=3, column=2, padx=(10, 20), pady=6, sticky="e")

        # Play Again coordinates
        coord_frame = ctk.CTkFrame(config_card, fg_color="transparent")
        coord_frame.grid(row=4, column=0, columnspan=3, padx=20, pady=(6, 15), sticky="w")
        
        lbl_play = ctk.CTkLabel(coord_frame, text="Play Again Button:  X:", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=TEXT_MUTED)
        lbl_play.grid(row=0, column=0, sticky="w")

        self.ent_play_x = ctk.CTkEntry(coord_frame, width=50, height=24, fg_color=INPUT_BG, border_color=BORDER_COLOR)
        self.ent_play_x.insert(0, "0")
        self.ent_play_x.grid(row=0, column=1, padx=5)

        lbl_y = ctk.CTkLabel(coord_frame, text="Y:", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=TEXT_MUTED)
        lbl_y.grid(row=0, column=2, padx=5)

        self.ent_play_y = ctk.CTkEntry(coord_frame, width=50, height=24, fg_color=INPUT_BG, border_color=BORDER_COLOR)
        self.ent_play_y.insert(0, "0")
        self.ent_play_y.grid(row=0, column=3, padx=5)

        # Crosshair Target Button
        target_btn = ctk.CTkButton(
            coord_frame, 
            text="🎯", 
            width=26, 
            height=26, 
            fg_color="transparent", 
            hover_color=BORDER_COLOR, 
            font=ctk.CTkFont(size=14),
            command=self.capture_coordinate_tool
        )
        target_btn.grid(row=0, column=4, padx=5)

    def setup_step_section(self):
        # Toggle Section (Lobby vs Strategy)
        sect_card = ctk.CTkFrame(self.main_area, fg_color="transparent")
        sect_card.grid(row=3, column=0, sticky="ew", pady=(5, 5))
        sect_card.grid_columnconfigure(1, weight=1)

        sect_lbl = ctk.CTkLabel(sect_card, text="Section", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color=TEXT_MAIN)
        sect_lbl.grid(row=0, column=0, padx=(2, 12), sticky="w")

        pill_frame = ctk.CTkFrame(sect_card, fg_color=CARD_COLOR, corner_radius=8, border_color=BORDER_COLOR, border_width=1)
        pill_frame.grid(row=0, column=1, sticky="w")

        self.btn_sect_lobby = ctk.CTkButton(
            pill_frame, 
            text="Lobby (Map/Modifier)", 
            width=160, 
            height=28, 
            corner_radius=6,
            fg_color="transparent", 
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=lambda: self.switch_section("lobby")
        )
        self.btn_sect_lobby.grid(row=0, column=0, padx=2, pady=2)

        self.btn_sect_strat = ctk.CTkButton(
            pill_frame, 
            text="Strategy (Strat)", 
            width=130, 
            height=28, 
            corner_radius=6,
            fg_color=GREEN_ACCENT, 
            text_color=BG_COLOR,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=lambda: self.switch_section("strategy")
        )
        self.btn_sect_strat.grid(row=0, column=1, padx=2, pady=2)

        # 5. List of Steps Frame (Main view)
        self.list_card = ctk.CTkFrame(self.main_area, fg_color=CARD_COLOR, corner_radius=12, border_color=BORDER_COLOR, border_width=1)
        self.list_card.grid(row=4, column=0, sticky="nsew", pady=(5, 10), padx=2)
        self.list_card.grid_columnconfigure(0, weight=1)
        self.list_card.grid_rowconfigure(1, weight=1)
        self.main_area.grid_rowconfigure(4, weight=1)

        self.lbl_steps_title = ctk.CTkLabel(
            self.list_card,
            text="Strategy (Strat) Steps (0)",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=TEXT_MAIN
        )
        self.lbl_steps_title.grid(row=0, column=0, padx=20, pady=(15, 10), sticky="w")

        # Scrollable container for steps
        self.steps_scroll = ctk.CTkScrollableFrame(self.list_card, fg_color="transparent")
        self.steps_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.steps_scroll.grid_columnconfigure(0, weight=1)

        # 6. Add Step Row (At the bottom of right pane)
        add_step_card = ctk.CTkFrame(self.main_area, fg_color=CARD_COLOR, corner_radius=12, border_color=BORDER_COLOR, border_width=1)
        add_step_card.grid(row=5, column=0, sticky="ew", pady=(5, 5), padx=2)
        add_step_card.grid_columnconfigure(0, weight=1)

        add_lbl = ctk.CTkLabel(add_step_card, text="Add Step", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=TEXT_MUTED)
        add_lbl.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="w")

        btn_row = ctk.CTkFrame(add_step_card, fg_color="transparent")
        btn_row.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")

        # Action Buttons row
        actions = [
            ("Click", lambda: self.add_step_dialog("click")),
            ("Move", lambda: self.add_step_dialog("move")),
            ("Drag / Drop", lambda: self.add_step_dialog("drag")),
            ("Type Text", lambda: self.add_step_dialog("type")),
            ("Key Press", lambda: self.add_step_dialog("keypress")),
            ("Delay", lambda: self.add_step_dialog("delay")),
            ("OCR Region", lambda: self.add_step_dialog("ocr"))
        ]

        for idx, (label, cmd) in enumerate(actions):
            btn = ctk.CTkButton(
                btn_row,
                text=label,
                width=90,
                height=30,
                fg_color=BORDER_COLOR,
                text_color=TEXT_MAIN,
                hover_color="#33333d",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                command=cmd
            )
            btn.grid(row=0, column=idx, padx=5, sticky="ew")
            btn_row.grid_columnconfigure(idx, weight=1)

        self.update_steps_view()

    # ================= STEP MANAGEMENT & RENDERING =================
    def update_steps_view(self):
        # Clean scrollable steps area
        for widget in self.steps_scroll.winfo_children():
            widget.destroy()

        macro = self.macros[self.active_macro]
        steps = macro["lobby_steps"] if macro["section"] == "lobby" else macro["strategy_steps"]

        # Update step count in heading
        sec_name = "Lobby" if macro["section"] == "lobby" else "Strategy (Strat)"
        self.lbl_steps_title.configure(text=f"{sec_name} Steps ({len(steps)})")

        if len(steps) == 0:
            # Render Empty State (Gamepad icon)
            empty_frame = ctk.CTkFrame(self.steps_scroll, fg_color="transparent")
            empty_frame.pack(expand=True, fill="both", pady=40)

            # Gamepad icon using unicode/emoji text in large size
            icon_game = ctk.CTkLabel(empty_frame, text="🎮", font=ctk.CTkFont(size=48))
            icon_game.pack(pady=5)

            lbl_empty1 = ctk.CTkLabel(
                empty_frame, 
                text=f"No {macro['section']} steps", 
                font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
                text_color=TEXT_MAIN
            )
            lbl_empty1.pack(pady=2)

            lbl_empty2 = ctk.CTkLabel(
                empty_frame, 
                text=f"Add gameplay {macro['section']} steps (place towers, upgrade, etc.) using the buttons below.", 
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=TEXT_MUTED
            )
            lbl_empty2.pack(pady=2)
        else:
            # Render Steps list
            for i, step in enumerate(steps):
                step_card = ctk.CTkFrame(self.steps_scroll, fg_color=INPUT_BG, corner_radius=8, border_color=BORDER_COLOR, border_width=1, height=45)
                step_card.pack(fill="x", pady=4, padx=5)
                step_card.pack_propagate(False)

                # Left side step index
                lbl_idx = ctk.CTkLabel(step_card, text=f"{i+1:02d}", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=BLUE_ACCENT, width=30)
                lbl_idx.pack(side="left", padx=10)

                # Icon based on type
                stype = step["type"]
                icon_map = {"click": "🖱️", "move": "📍", "drag": "↔️", "type": "✍️", "keypress": "⌨️", "delay": "⏱️", "ocr": "🔍"}
                lbl_sicon = ctk.CTkLabel(step_card, text=icon_map.get(stype, "📝"), font=ctk.CTkFont(size=13))
                lbl_sicon.pack(side="left", padx=5)

                # Description Text
                desc_text = self.get_step_description(step)
                lbl_desc = ctk.CTkLabel(step_card, text=desc_text, font=ctk.CTkFont(family="Segoe UI", size=12), text_color=TEXT_MAIN)
                lbl_desc.pack(side="left", padx=10)

                # Delete Button
                btn_delete = ctk.CTkButton(
                    step_card,
                    text="✕",
                    width=24,
                    height=24,
                    corner_radius=12,
                    fg_color="transparent",
                    text_color=RED_ACCENT,
                    hover_color="#3a1c1a",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    command=lambda idx=i: self.delete_step(idx)
                )
                btn_delete.pack(side="right", padx=15)

    def get_step_description(self, step):
        stype = step["type"]
        if stype == "click":
            return f"Left Click at coordinate ({step['x']}, {step['y']})"
        elif stype == "move":
            return f"Move cursor to coordinate ({step['x']}, {step['y']})"
        elif stype == "drag":
            return f"Drag from ({step['x1']}, {step['y1']}) to ({step['x2']}, {step['y2']})"
        elif stype == "type":
            return f"Type text string: \"{step['text']}\""
        elif stype == "keypress":
            return f"Press keyboard key: \"{step['key']}\""
        elif stype == "delay":
            return f"Delay sleep duration: {step['seconds']} seconds"
        elif stype == "ocr":
            return f"Perform OCR on box bounds: ({step['x1']},{step['y1']}) to ({step['x2']},{step['y2']})"
        return "Unknown macro action step"

    # ================= TAB / MACRO INTERACTIVE SWITCHING =================
    def select_macro(self, name):
        self.active_macro = name
        macro = self.macros[name]

        # Update headers and descriptions
        self.lbl_active_macro.configure(text=name)
        self.lbl_desc.configure(text=macro["desc"])

        # Update fields
        self.ent_victory.delete(0, tk.END)
        self.ent_victory.insert(0, macro["victory_img"])

        self.ent_defeat.delete(0, tk.END)
        self.ent_defeat.insert(0, macro["defeat_img"])

        self.ent_play_x.delete(0, tk.END)
        self.ent_play_x.insert(0, str(macro["play_again_x"]))

        self.ent_play_y.delete(0, tk.END)
        self.ent_play_y.insert(0, str(macro["play_again_y"]))

        # Toggle UI selected frame states
        self.update_sidebar_list()
        self.switch_section(macro["section"])

    def switch_section(self, section):
        self.macros[self.active_macro]["section"] = section
        if section == "lobby":
            self.btn_sect_lobby.configure(fg_color=GREEN_ACCENT, text_color=BG_COLOR, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
            self.btn_sect_strat.configure(fg_color="transparent", text_color=TEXT_MUTED, font=ctk.CTkFont(family="Segoe UI", size=12))
        else:
            self.btn_sect_lobby.configure(fg_color="transparent", text_color=TEXT_MUTED, font=ctk.CTkFont(family="Segoe UI", size=12))
            self.btn_sect_strat.configure(fg_color=GREEN_ACCENT, text_color=BG_COLOR, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))

        self.update_steps_view()

    # ================= ACTIONS & CALLBACKS =================
    def choose_image(self, img_type):
        path = filedialog.askopenfilename(filetypes=[("PNG Files", "*.png"), ("All Files", "*.*")])
        if path:
            if img_type == "victory":
                self.macros[self.active_macro]["victory_img"] = path
                self.ent_victory.delete(0, tk.END)
                self.ent_victory.insert(0, path)
            else:
                self.macros[self.active_macro]["defeat_img"] = path
                self.ent_defeat.delete(0, tk.END)
                self.ent_defeat.insert(0, path)

    def capture_coordinate_tool(self):
        # Simple instruction warning
        messagebox.showinfo(
            "Target Coordinates Tool",
            "Move your mouse cursor to the 'Play Again' button and press Spacebar on your keyboard to lock coordinates."
        )
        
        from pynput import keyboard, mouse
        m_ctrl = mouse.Controller()
        
        def on_press(key):
            if key == keyboard.Key.space:
                x, y = m_ctrl.position
                self.after(0, lambda: self.set_play_coordinates(x, y))
                return False # Stop listener

        listener = keyboard.Listener(on_press=on_press)
        listener.start()

    def set_play_coordinates(self, x, y):
        self.macros[self.active_macro]["play_again_x"] = x
        self.macros[self.active_macro]["play_again_y"] = y
        self.ent_play_x.delete(0, tk.END)
        self.ent_play_x.insert(0, str(x))
        self.ent_play_y.delete(0, tk.END)
        self.ent_play_y.insert(0, str(y))
        messagebox.showinfo("Locked Coordinates", f"Coordinates saved successfully:\n- X: {x}\n- Y: {y}")

    def open_settings_dialog(self):
        # Create a Toplevel settings window
        dialog = ctk.CTkToplevel(self)
        dialog.title("Settings")
        dialog.geometry("340x260")
        dialog.resizable(False, False)
        dialog.configure(fg_color=SIDEBAR_COLOR)
        
        # Ensure it appears on top and grabs focus
        dialog.transient(self)
        dialog.grab_set()
        
        # Title
        lbl_title = ctk.CTkLabel(
            dialog, 
            text="Hotkey Settings", 
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), 
            text_color=TEXT_MAIN
        )
        lbl_title.pack(pady=(15, 10))
        
        # Container frame
        frame = ctk.CTkFrame(dialog, fg_color=CARD_COLOR, corner_radius=10, border_color=BORDER_COLOR, border_width=1)
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        frame.grid_columnconfigure(1, weight=1)
        
        # Option values list (F1-F12 + [, ])
        f_keys = [f"F{i}" for i in range(1, 13)] + ["[", "]"]
        
        # Record Hotkey
        lbl_rec = ctk.CTkLabel(frame, text="Record Hotkey:", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=TEXT_MUTED)
        lbl_rec.grid(row=0, column=0, padx=15, pady=20, sticky="w")
        
        opt_rec = ctk.CTkOptionMenu(
            frame,
            values=f_keys,
            fg_color=INPUT_BG,
            button_color=BORDER_COLOR,
            button_hover_color=BLUE_ACCENT,
            dropdown_fg_color=CARD_COLOR,
            dropdown_hover_color=BORDER_COLOR,
            height=28
        )
        opt_rec.set(self.hotkey_record)
        opt_rec.grid(row=0, column=1, padx=15, pady=20, sticky="ew")
        
        # Run Hotkey
        lbl_play = ctk.CTkLabel(frame, text="Run Hotkey:", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=TEXT_MUTED)
        lbl_play.grid(row=1, column=0, padx=15, pady=(0, 20), sticky="w")
        
        opt_play = ctk.CTkOptionMenu(
            frame,
            values=f_keys,
            fg_color=INPUT_BG,
            button_color=BORDER_COLOR,
            button_hover_color=BLUE_ACCENT,
            dropdown_fg_color=CARD_COLOR,
            dropdown_hover_color=BORDER_COLOR,
            height=28
        )
        opt_play.set(self.hotkey_play)
        opt_play.grid(row=1, column=1, padx=15, pady=(0, 20), sticky="ew")
        
        # Save Button
        def save_settings():
            self.hotkey_record = opt_rec.get()
            self.hotkey_play = opt_play.get()
            
            # Re-register global listener
            self.start_global_listener()
            
            # Update GUI button texts
            self.btn_record.configure(text=f"● Record ({self.hotkey_record})")
            self.btn_run.configure(text=f"▶ Run Macro ({self.hotkey_play})")
            
            dialog.destroy()
            messagebox.showinfo("Success", "Settings saved successfully!")
            
        btn_save = ctk.CTkButton(
            frame,
            text="Save Settings",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=BLUE_ACCENT,
            text_color=TEXT_MAIN,
            hover_color="#0066cc",
            height=32,
            command=save_settings
        )
        btn_save.grid(row=2, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew")

    def create_new_macro(self):
        name = simpledialog.askstring("New Macro", "Enter macro name:")
        if name:
            name = name.strip()
            if name in self.macros:
                messagebox.showwarning("Warning", "Macro name already exists.")
                return
            self.macros[name] = {
                "desc": f"Custom macro strategy for {name}.",
                "victory_img": "",
                "defeat_img": "",
                "play_again_x": 0,
                "play_again_y": 0,
                "section": "strategy",
                "lobby_steps": [],
                "strategy_steps": []
            }
            self.select_macro(name)

    def delete_step(self, idx):
        macro = self.macros[self.active_macro]
        steps = macro["lobby_steps"] if macro["section"] == "lobby" else macro["strategy_steps"]
        if 0 <= idx < len(steps):
            steps.pop(idx)
        self.update_steps_view()
        self.update_sidebar_list()

    def add_step_dialog(self, stype):
        macro = self.macros[self.active_macro]
        steps = macro["lobby_steps"] if macro["section"] == "lobby" else macro["strategy_steps"]

        if stype == "click" or stype == "move":
            x = simpledialog.askinteger("Input Coordinate", "Enter X screen position:")
            y = simpledialog.askinteger("Input Coordinate", "Enter Y screen position:")
            if x is not None and y is not None:
                steps.append({"type": stype, "x": x, "y": y})
        
        elif stype == "drag":
            x1 = simpledialog.askinteger("Input", "Start position X1:")
            y1 = simpledialog.askinteger("Input", "Start position Y1:")
            x2 = simpledialog.askinteger("Input", "End position X2:")
            y2 = simpledialog.askinteger("Input", "End position Y2:")
            if None not in [x1, y1, x2, y2]:
                steps.append({"type": "drag", "x1": x1, "y1": y1, "x2": x2, "y2": y2})
        
        elif stype == "type":
            txt = simpledialog.askstring("Input Text", "Enter text to type:")
            if txt:
                steps.append({"type": "type", "text": txt})
        
        elif stype == "keypress":
            key = simpledialog.askstring("Input Keyboard Key", "Enter key to press (e.g. 'space', 'f', '1'):")
            if key:
                steps.append({"type": "keypress", "key": key.strip()})
        
        elif stype == "delay":
            secs = simpledialog.askfloat("Input Seconds", "Enter wait duration in seconds:")
            if secs is not None:
                steps.append({"type": "delay", "seconds": secs})
                
        elif stype == "ocr":
            x1 = simpledialog.askinteger("OCR Area", "Box bounds X1:")
            y1 = simpledialog.askinteger("OCR Area", "Box bounds Y1:")
            x2 = simpledialog.askinteger("OCR Area", "Box bounds X2:")
            y2 = simpledialog.askinteger("OCR Area", "Box bounds Y2:")
            if None not in [x1, y1, x2, y2]:
                steps.append({"type": "ocr", "x1": x1, "y1": y1, "x2": x2, "y2": y2})

        self.update_steps_view()
        self.update_sidebar_list()

    # ================= RECORDING & RUNNING BACKEND BRIDGING =================
    def toggle_recording(self):
        if self.playback_running:
            return
            
        if not self.recording_running:
            self.log_status("Recording...", color=RED_ACCENT)
            self.btn_record.configure(text=f"⏹️ Stop ({self.hotkey_record})", fg_color=RED_ACCENT, hover_color="#3a1c1a")
            self.btn_run.configure(state="disabled")
            
            # Start low-level recorder
            self.recording_running = True
            
            # Use a thread to record clicks and keys
            self.recorder_events = []
            self.record_start_time = time.time()
            
            from pynput import mouse, keyboard
            
            def on_click(x, y, button, pressed):
                if not self.recording_running:
                    return False # stop listener
                if pressed:
                    self.recorder_events.append({
                        "type": "click", 
                        "x": x, 
                        "y": y,
                        "time": time.time() - self.record_start_time
                    })
                    
            def on_press(key):
                if not self.recording_running:
                    return False # stop listener
                
                # Check for stop key
                # Convert string key to pynput Key
                rec_key = self.get_pynput_key(self.hotkey_record)
                if key == rec_key:
                    return False
                
                key_name = ""
                if hasattr(key, 'char') and key.char is not None:
                    key_name = key.char
                else:
                    key_name = key.name
                
                self.recorder_events.append({
                    "type": "keypress",
                    "key": key_name,
                    "time": time.time() - self.record_start_time
                })

            self.m_listener = mouse.Listener(on_click=on_click)
            self.k_listener = keyboard.Listener(on_press=on_press)
            
            self.m_listener.start()
            self.k_listener.start()
        else:
            self.recording_running = False
            try:
                self.m_listener.stop()
                self.k_listener.stop()
            except Exception:
                pass
                
            self.log_status("Finished", color=TEXT_MUTED)
            self.btn_record.configure(text=f"● Record ({self.hotkey_record})", fg_color="transparent")
            self.btn_run.configure(state="normal")
            
            # Convert recorded events into step list!
            macro = self.macros[self.active_macro]
            steps = macro["lobby_steps"] if macro["section"] == "lobby" else macro["strategy_steps"]
            
            if self.recorder_events:
                # Add recorded actions into steps
                for event in self.recorder_events:
                    steps.append(event)
                messagebox.showinfo("Recording Finished", f"Recorded {len(self.recorder_events)} steps into current macro!")
            
            self.update_steps_view()
            self.update_sidebar_list()

    def toggle_playback(self):
        if self.recording_running:
            return
            
        if not self.playback_running:
            macro = self.macros[self.active_macro]
            steps = macro["lobby_steps"] if macro["section"] == "lobby" else macro["strategy_steps"]
            if len(steps) == 0:
                messagebox.showwarning("Warning", "No steps in this section to play.")
                return

            self.log_status("Running...", color=GREEN_ACCENT)
            self.btn_run.configure(text=f"⏹️ Stop ({self.hotkey_play})", fg_color=RED_ACCENT, hover_color="#3a1c1a")
            self.btn_record.configure(state="disabled")
            self.playback_running = True
            
            # Run steps in a separate thread so the GUI doesn't freeze
            self.running_thread = threading.Thread(target=self._run_steps, args=(steps,), daemon=True)
            self.running_thread.start()
        else:
            self.playback_running = False
            self.log_status("Finished", color=TEXT_MUTED)
            self.btn_run.configure(text=f"▶ Run Macro ({self.hotkey_play})", fg_color=BLUE_ACCENT, hover_color="#0066cc")
            self.btn_record.configure(state="normal")

    def _run_steps(self, steps):
        for step in steps:
            if not self.playback_running:
                break
                
            stype = step["type"]
            self.log_status(f"Executing: {self.get_step_description(step)}", color=BLUE_ACCENT)
            
            try:
                # Ensure Roblox is active or use background post-message
                hwnd = me.find_roblox_hwnd()
                
                if stype == "click":
                    if hwnd:
                        # Convert to relative client coords or use absolute
                        cx, cy = me.screen_to_client(hwnd, step["x"], step["y"])
                        me.send_background_click(hwnd, "left", cx, cy)
                    else:
                        me.win32_move_absolute(step["x"], step["y"])
                        me.win32_click("left")
                    time.sleep(0.5)
                    
                elif stype == "move":
                    if hwnd:
                        cx, cy = me.screen_to_client(hwnd, step["x"], step["y"])
                        me.send_background_move(hwnd, cx, cy)
                    else:
                        me.win32_move_absolute(step["x"], step["y"])
                    time.sleep(0.5)
                    
                elif stype == "keypress":
                    if hwnd:
                        vk = me.key_to_vk(step["key"])
                        me.send_background_key(hwnd, vk, 0.05)
                    else:
                        k = me.deserialize_key(step["key"])
                        me.keyboard_controller.press(k)
                        time.sleep(0.05)
                        me.keyboard_controller.release(k)
                    time.sleep(0.3)
                    
                elif stype == "type":
                    # Type text
                    for char in step["text"]:
                        if not self.playback_running:
                            break
                        if hwnd:
                            vk = me.key_to_vk(char)
                            me.send_background_key(hwnd, vk, 0.02)
                        else:
                            me.keyboard_controller.type(char)
                        time.sleep(0.05)
                    time.sleep(0.5)
                    
                elif stype == "delay":
                    time.sleep(step["seconds"])
            except Exception as e:
                print(f"Error executing step: {e}")
                
        # Finished playing all steps
        self.after(0, self.stop_playback_gui)

    def stop_playback_gui(self):
        self.playback_running = False
        self.log_status("Finished", color=TEXT_MUTED)
        self.btn_run.configure(text=f"▶ Run Macro ({self.hotkey_play})", fg_color=BLUE_ACCENT, hover_color="#0066cc")
        self.btn_record.configure(state="normal")

    def log_status(self, text, color=TEXT_MUTED):
        def _update():
            self.lbl_status.configure(text=text, text_color=color)
        self.after(0, _update)

    def on_closing(self):
        self.playback_running = False
        self.recording_running = False
        try:
            self.listener.stop()
        except Exception:
            pass
        self.destroy()

if __name__ == "__main__":
    app = HinnoMacroApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
