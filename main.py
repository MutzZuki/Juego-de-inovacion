import customtkinter as ctk
import tkinter as tk
import math
import time
import ctypes
import threading

# ==============================================================================
# ALEXANDER'S QUEST: PERMANENT DECISION LOCK ENGINE
# Programmed & Created By: Armando Misael Mata Hernández
# Feature: Decisions are PERMANENT and LOCKED once answered (No repeats!)
# Mobility: ONLY via Xbox Left Analog Stick (Palanca) / WASD
# Menu Selection: ONLY via Xbox D-Pad (Cruceta) / Up & Down Arrow Keys
# 100% GBA Pokémon Pixel Art Sprite Engine & Xbox Controller Support
# ==============================================================================

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# --- XINPUT CTYPES STRUCTURES FOR XBOX CONTROLLERS ---
class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", ctypes.c_ushort),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short)
    ]

class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", ctypes.c_ulong),
        ("Gamepad", XINPUT_GAMEPAD)
    ]

# XInput Constants
XINPUT_GAMEPAD_DPAD_UP    = 0x0001
XINPUT_GAMEPAD_DPAD_DOWN  = 0x0002
XINPUT_GAMEPAD_DPAD_LEFT  = 0x0004
XINPUT_GAMEPAD_DPAD_RIGHT = 0x0008
XINPUT_GAMEPAD_START      = 0x0010
XINPUT_GAMEPAD_BACK       = 0x0020
XINPUT_GAMEPAD_A          = 0x1000
XINPUT_GAMEPAD_B          = 0x2000
XINPUT_GAMEPAD_X          = 0x4000
XINPUT_GAMEPAD_Y          = 0x8000
THUMB_DEADZONE            = 12000

# Load Windows XInput DLL
xinput_dll = None
for dll_name in ['xinput1_4', 'xinput1_3', 'xinput9_1_0']:
    try:
        xinput_dll = ctypes.windll.LoadLibrary(dll_name)
        break
    except Exception:
        pass


class PokemonGBAPermanentDecisionEngine(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ALEXANDER'S QUEST: DECISIONES PERMANENTES (ARMANDO MISAEL MATA HERNÁNDEZ)")

        # ----------------------------------------------------------------------
        # 100% TRUE BORDERLESS FULLSCREEN MODE (HIDES WINDOWS TASKBAR & ICONS)
        # ----------------------------------------------------------------------
        self.attributes('-fullscreen', True)
        self.bind("<F11>", lambda e: self.attributes('-fullscreen', not self.attributes('-fullscreen')))
        self.bind("<Escape>", lambda e: self.toggle_fullscreen_off())

        # Palette
        self.COLOR_CYAN = "#00f0ff"
        self.COLOR_GOLD = "#ffd700"
        self.COLOR_GRASS = "#70c060"
        self.COLOR_PATH = "#e0c068"
        self.COLOR_PATH_BORDER = "#b89848"
        self.COLOR_TREE_LEAF = "#287038"
        self.COLOR_TREE_HIGH = "#50a048"
        self.COLOR_TREE_TRUNK = "#684828"
        self.COLOR_FLOWER_RED = "#e03838"

        self.COLOR_WOOD = "#a87040"
        self.COLOR_DESK = "#704828"
        self.COLOR_BLACKBOARD = "#183828"
        self.COLOR_ASPHALT = "#383840"
        self.COLOR_RACE_RED = "#e02828"
        self.COLOR_GT_BLUE = "#1e40af"
        self.COLOR_SKIN = "#ffcc99"

        self.configure(fg_color="#000000")

        # Game & Intro / Ending Video States
        self.in_intro_video = True
        self.in_ending_video = False
        self.ending_video_frame = 0
        self.in_start_screen = False
        self.intro_progress = 0

        self.current_map = 0  # 0: Salón, 1: Calle, 2: Empresa, 3: Final Autódromo/Trabajo
        self.player_x = 300
        self.player_y = 350
        self.player_speed = 16
        self.player_dir = "down"
        self.anim_frame = 0

        self.company_score = 50
        self.capital = 10000
        self.completed_modules = {0: False, 1: False, 2: False, 3: False}
        self.inventory_items = []
        self.decisions_log = []
        self.locked_decisions = {}  # Tracks locked permanent answers: {npc_id: choice_summary}

        self.active_npc = None
        self.in_dialogue = False
        self.timer_seconds = 0
        self.timer_running = True

        # Interactive Decision Option Focus Index & Phase Engine
        self.decision_focused_index = 0
        self.current_choice_a_func = None
        self.current_choice_b_func = None
        self.opt_btn_a = None
        self.opt_btn_b = None
        self.has_active_options = False

        # Xbox Controller Debounce State
        self.last_a_state = False
        self.last_b_state = False
        self.last_x_state = False
        self.last_y_state = False
        self.last_dpad_up_state = False
        self.last_dpad_down_state = False

        # Build Layouts
        self.create_hud_header()
        self.create_game_canvas()
        self.create_gba_dialogue_box()

        # Hide HUD and Prompt during Intro!
        self.hud_frame.pack_forget()
        self.prompt_lbl.pack_forget()

        # Keyboard Bindings: WASD for Mobility, Arrow Keys Exclusively for Menu Options!
        self.bind("<w>", lambda e: self.move_player(0, -self.player_speed, "up"))
        self.bind("<s>", lambda e: self.move_player(0, self.player_speed, "down"))
        self.bind("<a>", lambda e: self.move_player(-self.player_speed, 0, "left"))
        self.bind("<d>", lambda e: self.move_player(self.player_speed, 0, "right"))

        # Arrow Keys EXCLUSIVELY Navigate Menu Options!
        self.bind("<Up>", lambda e: self.navigate_menu_up())
        self.bind("<Down>", lambda e: self.navigate_menu_down())

        self.bind("<e>", lambda e: self.interact_action())
        self.bind("<space>", lambda e: self.interact_action())
        self.bind("<Return>", lambda e: self.interact_action())

        self.bind("<i>", lambda e: self.toggle_inventory())
        self.bind("<m>", lambda e: self.toggle_professor_report())

        # Resize Event Binding for Responsiveness
        self.canvas.bind("<Configure>", lambda e: self.on_canvas_resize())

        # Start Video Animation Loop & Xbox Controller Thread
        self.animate_video_loops()
        self.run_timer()
        self.xbox_thread_running = True
        self.start_xbox_controller_thread()

    def toggle_fullscreen_off(self):
        if self.in_dialogue:
            self.close_dialogue()
        else:
            self.attributes('-fullscreen', False)

    def on_canvas_resize(self):
        self.draw_current_map()

    # --- VIDEO ANIMATOR LOOPS ---
    def animate_video_loops(self):
        if self.in_intro_video:
            self.intro_progress += 1.5
            if self.intro_progress >= 100:
                self.finish_intro_and_start_game()
                return
            self.draw_current_map()

        elif self.in_ending_video:
            self.ending_video_frame += 1
            self.draw_current_map()

        self.after(40, self.animate_video_loops)

    def finish_intro_and_start_game(self):
        if self.in_intro_video:
            self.in_intro_video = False
            self.in_start_screen = False
            self.hud_frame.pack(side="top", fill="x")
            self.prompt_lbl.pack(side="bottom", pady=2)
            self.draw_current_map()

    def trigger_ending_video(self):
        self.close_dialogue()
        self.in_ending_video = True
        self.ending_video_frame = 0
        self.hud_frame.pack_forget()
        self.prompt_lbl.pack_forget()
        self.draw_current_map()

    # --- MENU NAVIGATION HANDLERS ---
    def navigate_menu_up(self):
        if self.in_dialogue and self.has_active_options:
            self.decision_focused_index = max(0, self.decision_focused_index - 1)
            self.update_option_focus_styles()

    def navigate_menu_down(self):
        if self.in_dialogue and self.has_active_options:
            max_idx = getattr(self, 'max_option_index', 1)
            self.decision_focused_index = min(max_idx, self.decision_focused_index + 1)
            self.update_option_focus_styles()

    def update_option_focus_styles(self):
        if not self.has_active_options or not self.opt_btn_a or not self.opt_btn_b:
            return

        if self.decision_focused_index == 0:
            self.opt_btn_a.configure(fg_color="#103028", border_color="#00ffaa", border_width=2, text_color="#00ffaa")
            self.opt_btn_b.configure(fg_color="#1d2636", border_color="#3a4a66", border_width=1, text_color="#8e9bb4")
            if getattr(self, 'opt_btn_c', None):
                self.opt_btn_c.configure(fg_color="#1d2636", border_color="#3a4a66", border_width=1, text_color="#ff007a")
        elif self.decision_focused_index == 1:
            self.opt_btn_a.configure(fg_color="#1d2636", border_color="#3a4a66", border_width=1, text_color="#8e9bb4")
            self.opt_btn_b.configure(fg_color="#103028", border_color="#00ffaa", border_width=2, text_color="#00ffaa")
            if getattr(self, 'opt_btn_c', None):
                self.opt_btn_c.configure(fg_color="#1d2636", border_color="#3a4a66", border_width=1, text_color="#ff007a")
        elif self.decision_focused_index == 2 and getattr(self, 'opt_btn_c', None):
            self.opt_btn_a.configure(fg_color="#1d2636", border_color="#3a4a66", border_width=1, text_color="#8e9bb4")
            self.opt_btn_b.configure(fg_color="#1d2636", border_color="#3a4a66", border_width=1, text_color="#8e9bb4")
            self.opt_btn_c.configure(fg_color="#3d1515", border_color="#ff007a", border_width=2, text_color="#ff007a")

    # --------------------------------------------------------------------------
    # NATIVE XBOX CONTROLLER POLLING THREAD
    # Mobility = ONLY Left Stick (Palanca)
    # Menu Selection = D-Pad (Cruceta)
    # --------------------------------------------------------------------------
    def start_xbox_controller_thread(self):
        t = threading.Thread(target=self.poll_xbox_controller, daemon=True)
        t.start()

    def poll_xbox_controller(self):
        state = XINPUT_STATE()
        while self.xbox_thread_running:
            if xinput_dll:
                res = xinput_dll.XInputGetState(0, ctypes.byref(state))
                if res == 0:
                    pad = state.Gamepad
                    buttons = pad.wButtons

                    # --- 1. MOBILITY: ONLY ANALOG LEFT STICK (PALANCA IZQUIERDA) ---
                    dx, dy = 0, 0
                    direction = None

                    if pad.sThumbLY > THUMB_DEADZONE:
                        dy = -self.player_speed
                        direction = "up"
                    elif pad.sThumbLY < -THUMB_DEADZONE:
                        dy = self.player_speed
                        direction = "down"

                    if pad.sThumbLX < -THUMB_DEADZONE:
                        dx = -self.player_speed
                        direction = "left"
                    elif pad.sThumbLX > THUMB_DEADZONE:
                        dx = self.player_speed
                        direction = "right"

                    if (dx != 0 or dy != 0) and not self.in_dialogue and not self.in_intro_video and not self.in_ending_video:
                        self.after(0, lambda x=dx, y=dy, d=direction: self.move_player(x, y, d))

                    # --- 2. MENU NAVIGATION: D-PAD (CRUCETA) ONLY ---
                    dpad_up = bool(buttons & XINPUT_GAMEPAD_DPAD_UP)
                    if dpad_up and not self.last_dpad_up_state:
                        self.after(0, self.navigate_menu_up)
                    self.last_dpad_up_state = dpad_up

                    dpad_down = bool(buttons & XINPUT_GAMEPAD_DPAD_DOWN)
                    if dpad_down and not self.last_dpad_down_state:
                        self.after(0, self.navigate_menu_down)
                    self.last_dpad_down_state = dpad_down

                    # --- 3. BUTTONS: A (CONFIRM / START / SKIP VIDEO) ---
                    a_pressed = bool(buttons & (XINPUT_GAMEPAD_A | XINPUT_GAMEPAD_START))
                    if a_pressed and not self.last_a_state:
                        self.after(0, self.interact_action)
                    self.last_a_state = a_pressed

                    y_pressed = bool(buttons & XINPUT_GAMEPAD_Y)
                    if y_pressed and not self.last_y_state:
                        self.after(0, self.toggle_inventory)
                    self.last_y_state = y_pressed

                    x_pressed = bool(buttons & XINPUT_GAMEPAD_X)
                    if x_pressed and not self.last_x_state:
                        self.after(0, self.toggle_professor_report)
                    self.last_x_state = x_pressed

            time.sleep(0.04)

    # --------------------------------------------------------------------------
    # HUD HEADER
    # --------------------------------------------------------------------------
    def create_hud_header(self):
        self.hud_frame = ctk.CTkFrame(self, fg_color="#0b101c", height=54, corner_radius=0)

        title_lbl = ctk.CTkLabel(
            self.hud_frame,
            text="🎮 PROGRAMADO POR ARMANDO MISAEL MATA HERNÁNDEZ",
            font=ctk.CTkFont(family="Outfit", size=13, weight="bold"),
            text_color=self.COLOR_CYAN
        )
        title_lbl.pack(side="left", padx=16, pady=10)

        self.map_name_lbl = ctk.CTkLabel(
            self.hud_frame,
            text="📍 MAPA 1/4: El Salón de Clases",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=self.COLOR_GOLD
        )
        self.map_name_lbl.pack(side="left", padx=16, pady=10)

        btn_inv = ctk.CTkButton(
            self.hud_frame,
            text="🎒 Mochila (Y / I)",
            width=110,
            height=28,
            fg_color="#18233c",
            hover_color="#1a2744",
            text_color=self.COLOR_CYAN,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.toggle_inventory
        )
        btn_inv.pack(side="left", padx=8)

        btn_rep = ctk.CTkButton(
            self.hud_frame,
            text="📊 Reporte (X / M)",
            width=120,
            height=28,
            fg_color="#102520",
            hover_color="#1a3d35",
            text_color="#00ffaa",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.toggle_professor_report
        )
        btn_rep.pack(side="left", padx=5)

        self.score_lbl = ctk.CTkLabel(
            self.hud_frame,
            text="📊 Viabilidad: 50%",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color="#00ffaa"
        )
        self.score_lbl.pack(side="right", padx=14, pady=10)

        self.capital_lbl = ctk.CTkLabel(
            self.hud_frame,
            text="💰 Capital: $10,000",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=self.COLOR_GOLD
        )
        self.capital_lbl.pack(side="right", padx=14, pady=10)

    def update_metrics(self, score_delta, capital_delta):
        self.company_score = max(0, min(100, self.company_score + score_delta))
        self.capital = max(0, self.capital + capital_delta)

        color_score = "#00ffaa" if self.company_score >= 60 else "#ff007a"
        self.score_lbl.configure(text=f"📊 Viabilidad: {self.company_score}%", text_color=color_score)
        self.capital_lbl.configure(text=f"💰 Capital: ${self.capital:,}")

    def run_timer(self):
        if self.timer_running:
            self.timer_seconds += 1
            self.after(1000, self.run_timer)

    # --------------------------------------------------------------------------
    # CANVAS ENGINE
    # --------------------------------------------------------------------------
    def create_game_canvas(self):
        self.canvas_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.canvas_frame.pack(fill="both", expand=True, padx=0, pady=0)

        self.canvas = tk.Canvas(self.canvas_frame, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.prompt_lbl = ctk.CTkLabel(
            self.canvas_frame,
            text="🕹️ Movilidad: Palanca Izquierda de Xbox / WASD  |  Menús: Cruceta D-Pad / Flechas  |  Pantalla Completa: [F11]",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.COLOR_CYAN
        )

    def move_player(self, dx, dy, direction):
        if self.in_intro_video or self.in_ending_video or self.in_start_screen or self.in_dialogue:
            return

        new_x = self.player_x + dx
        new_y = self.player_y + dy

        w = self.canvas.winfo_width() or 1400
        h = self.canvas.winfo_height() or 800

        if 30 <= new_x <= w - 30 and 30 <= new_y <= h - 30:
            self.player_x = new_x
            self.player_y = new_y
            self.player_dir = direction
            self.anim_frame = 1 if self.anim_frame == 0 else 0

            self.check_map_transitions(w, h)
            self.draw_current_map()

    def check_map_transitions(self, w, h):
        if self.current_map == 0 and self.player_y >= h - 70 and self.completed_modules[0]:
            self.current_map = 1
            self.player_x = w // 2
            self.player_y = 80
            self.map_name_lbl.configure(text="📍 MAPA 2/4: La Calle & Distrito Tech")

        elif self.current_map == 1 and self.player_y >= h - 70 and self.completed_modules[1]:
            self.current_map = 2
            self.player_x = w // 2
            self.player_y = 80
            self.map_name_lbl.configure(text="📍 MAPA 3/4: Sede Corporativa AlexTech")

        elif self.current_map == 2 and self.player_y >= h - 70 and self.completed_modules[2]:
            self.current_map = 3
            self.player_x = 100
            self.player_y = h // 2
            
            if self.company_score >= 65 and self.capital >= 60000:
                self.map_name_lbl.configure(text="📍 MAPA 4/4: Autódromo F1 & GT World — ¡ÉXITO TOTAL!")
            elif self.company_score < 45 or self.capital <= 5000:
                self.map_name_lbl.configure(text="📍 MAPA 4/4: La Calle — EMPLEO SECUNDARIO NO DESEADO")
            else:
                self.map_name_lbl.configure(text="📍 MAPA 4/4: Taller Local — EMPRESA PEQUEÑA")

    # --------------------------------------------------------------------------
    # MAP & FULLSCREEN VIDEO RENDERERS
    # --------------------------------------------------------------------------
    def draw_current_map(self):
        c = self.canvas
        c.delete("all")
        w = c.winfo_width() or 1400
        h = c.winfo_height() or 800

        if self.in_intro_video:
            self.draw_pure_cinematic_intro(c, w, h)
            return

        if self.in_ending_video:
            self.draw_fullscreen_ending_video(c, w, h)
            return

        if self.in_start_screen:
            self.draw_start_screen(c, w, h)
            return

        if self.current_map == 0:
            self.draw_map_classroom(c, w, h)
        elif self.current_map == 1:
            self.draw_map_street(c, w, h)
        elif self.current_map == 2:
            self.draw_map_company(c, w, h)
        elif self.current_map == 3:
            if self.company_score >= 65 and self.capital >= 60000:
                self.draw_map_racetrack_success(c, w, h)
            elif self.company_score < 45 or self.capital <= 5000:
                self.draw_map_street_failure_job(c, w, h)
            else:
                self.draw_map_small_shop(c, w, h)

        self.draw_alexander_pixel_sprite(c, self.player_x, self.player_y, self.player_dir, self.anim_frame)

    # --- PURE CINEMATIC INTRO SCREEN ---
    def draw_pure_cinematic_intro(self, c, w, h):
        c.create_rectangle(0, 0, w, h, fill="#000000", outline="")

        glow = self.COLOR_GOLD if (int(self.intro_progress) // 5) % 2 == 0 else self.COLOR_CYAN
        c.create_text(w//2, h * 0.22, text="✨ UN VIDEOJUEGO CREADO Y PROGRAMADO POR ✨", fill=glow, font=("Outfit", 16, "bold"))

        box_w = min(int(w * 0.82), 950)
        c.create_rectangle(w//2 - box_w//2, h * 0.32, w//2 + box_w//2, h * 0.58, fill="#0a0f1d", outline=self.COLOR_CYAN, width=3)
        c.create_rectangle(w//2 - box_w//2 + 6, h * 0.32 + 6, w//2 + box_w//2 - 6, h * 0.58 - 6, fill="#050812", outline=self.COLOR_GOLD, width=1)

        c.create_text(w//2, h * 0.40, text="ARMANDO MISAEL MATA HERNÁNDEZ", fill="#ffffff", font=("Outfit", 30, "bold"))
        c.create_text(w//2, h * 0.49, text="DESARROLLADOR & PROGRAMADOR PRINCIPAL", fill=self.COLOR_GOLD, font=("Outfit", 14, "bold"))
        c.create_text(w//2, h * 0.53, text="PROYECTO ACADÉMICO: INNOVACIÓN EMPRESARIAL 2026", fill=self.COLOR_CYAN, font=("Outfit", 12))

        c.create_text(w//2, h * 0.67, text="ALEXANDER'S RACING QUEST", fill="#ff007a", font=("Outfit", 20, "bold"))
        c.create_text(w//2, h * 0.72, text="De Estudiante de TI a Patrocinador Oficial de la Fórmula 1 y GT World Challenge", fill="#ffffff", font=("Outfit", 12))

        bar_w = min(int(w * 0.65), 700)
        curr_bar_w = int((self.intro_progress / 100.0) * bar_w)
        c.create_rectangle(w//2 - bar_w//2, h * 0.82, w//2 + bar_w//2, h * 0.82 + 16, fill="#121826", outline="#3a4a66")
        c.create_rectangle(w//2 - bar_w//2, h * 0.82, w//2 - bar_w//2 + curr_bar_w, h * 0.82 + 16, fill="#00ffaa", outline="")

        pct = min(100, int(self.intro_progress))
        c.create_text(w//2, h * 0.87, text=f"⏳ CARGANDO RECURSOS Y MAPAS DEL JUEGO... {pct}%", fill="#00ffaa", font=("Consolas", 11, "bold"))
        c.create_text(w//2, h * 0.94, text="[ PRESIONA ENTER O BOTÓN A DE XBOX PARA ENTRAR DIRECTAMENTE AL JUEGO ]", fill="#8e9bb4", font=("Outfit", 11, "bold"))

    # --- FULLSCREEN ENDING VIDEO CUTSCENE PLAYER ENGINE ---
    def draw_fullscreen_ending_video(self, c, w, h):
        c.create_rectangle(0, 0, w, h, fill="#04060d", outline="")

        if self.company_score >= 65 and self.capital >= 60000:
            c.create_rectangle(0, 0, w, 55, fill="#0d1828", outline="")
            c.create_text(w//2, 28, text="🎬 VIDEO CINEMÁTICO DE FINAL 1: ¡ALEXANDER FELIZ Y SALTANDO DE ALEGRÍA EN LA F1!", fill=self.COLOR_GOLD, font=("Outfit", 14, "bold"))

            box_w = min(int(w * 0.88), 1050)
            box_h = min(int(h * 0.72), 520)
            c.create_rectangle(w//2 - box_w//2, h//2 - box_h//2, w//2 + box_w//2, h//2 + box_h//2, fill="#0c1626", outline=self.COLOR_GOLD, width=3)

            jump_y = h//2 - 40 - (15 if (self.ending_video_frame // 8) % 2 == 0 else 0)
            self.draw_alexander_jumping_happy_sprite(c, w//2, jump_y)

            c.create_text(w//2, h//2 + 80, text="👨‍💻 CREADOR Y PROGRAMADOR DEL PROYECTO: ARMANDO MISAEL MATA HERNÁNDEZ", fill=self.COLOR_CYAN, font=("Outfit", 13, "bold"))
            c.create_text(w//2, h//2 + 115, text="🏆 ¡LOGRO ALCANZADO: PATROCINADOR OFICIAL DE LA FÓRMULA 1 Y GT WORLD CHALLENGE!", fill=self.COLOR_GOLD, font=("Outfit", 15, "bold"))
            c.create_text(w//2, h//2 + 150, text="🎉 Alexander salta de emoción al recordar su inicio en las clases de la Profesora Estefanía Franco.\n¡Las 4 Factibilidades, Curva S, TRIZ, PNL y MVP llevaron a AlexTech a la cima deportiva mundial!", fill="#ffffff", font=("Outfit", 11), justify="center")

            scrub_w = box_w - 60
            progress = (self.ending_video_frame * 8) % scrub_w
            c.create_rectangle(w//2 - scrub_w//2, h//2 + box_h//2 - 45, w//2 + scrub_w//2, h//2 + box_h//2 - 37, fill="#1c2b42", outline="")
            c.create_rectangle(w//2 - scrub_w//2, h//2 + box_h//2 - 45, w//2 - scrub_w//2 + progress, h//2 + box_h//2 - 37, fill=self.COLOR_GOLD, outline="")
            c.create_text(w//2, h//2 + box_h//2 - 20, text="▶ 02:48 / 03:00  [ 🔴 REPRODUCIENDO CINE DE FINAL EN VIVO ]", fill=self.COLOR_GOLD, font=("Consolas", 10, "bold"))

        elif self.company_score < 45 or self.capital <= 5000:
            c.create_rectangle(0, 0, w, 55, fill="#240c14", outline="")
            c.create_text(w//2, 28, text="🎬 VIDEO CINEMÁTICO DE FINAL 2: ¡ALEXANDER LLORANDO AMARGAMENTE SOBRE SUS DECISIONES!", fill="#ff007a", font=("Outfit", 14, "bold"))

            box_w = min(int(w * 0.88), 1050)
            box_h = min(int(h * 0.72), 520)
            c.create_rectangle(w//2 - box_w//2, h//2 - box_h//2, w//2 + box_w//2, h//2 + box_h//2, fill="#1c0b12", outline="#ff007a", width=3)

            for i in range(25):
                rx = (w//2 - box_w//2 + 30 + (i * 40) + (self.ending_video_frame * 12)) % (box_w - 60) + (w//2 - box_w//2 + 30)
                ry = (h//2 - box_h//2 + 40 + (i * 20) + (self.ending_video_frame * 18)) % (box_h - 120) + (h//2 - box_h//2 + 40)
                c.create_line(rx, ry, rx - 4, ry + 12, fill="#00f0ff", width=1)

            self.draw_alexander_crying_sad_sprite(c, w//2, h//2 - 30)

            c.create_text(w//2, h//2 + 80, text="👨‍💻 CREADOR Y PROGRAMADOR DEL PROYECTO: ARMANDO MISAEL MATA HERNÁNDEZ", fill=self.COLOR_CYAN, font=("Outfit", 13, "bold"))
            c.create_text(w//2, h//2 + 115, text="❌ DESENLACE: ALEXTECH QUEBRÓ Y ALEXANDER TERMINÓ EN UN EMPLEO SECUNDARIO NO DESEADO", fill="#ff007a", font=("Outfit", 14, "bold"))
            c.create_text(w//2, h//2 + 150, text="😭 Alexander llora desconsoladamente sobre el pavimento bajo la lluvia.\nReflexiona con dolor sobre cómo las distracciones y decisiones impulsivas lo dejaron atrapado en la calle.", fill="#ffffff", font=("Outfit", 11), justify="center")

            scrub_w = box_w - 60
            progress = (self.ending_video_frame * 8) % scrub_w
            c.create_rectangle(w//2 - scrub_w//2, h//2 + box_h//2 - 45, w//2 + scrub_w//2, h//2 + box_h//2 - 37, fill="#381522", outline="")
            c.create_rectangle(w//2 - scrub_w//2, h//2 + box_h//2 - 45, w//2 - scrub_w//2 + progress, h//2 + box_h//2 - 37, fill="#ff007a", outline="")
            c.create_text(w//2, h//2 + box_h//2 - 20, text="▶ 01:15 / 03:00  [ 🔴 REPRODUCIENDO CINE DE FINAL EN VIVO ]", fill="#ff007a", font=("Consolas", 10, "bold"))

        else:
            c.create_rectangle(0, 0, w, 55, fill="#121a2b", outline="")
            c.create_text(w//2, 28, text="🎬 VIDEO CINEMÁTICO DE FINAL 3: TALLER LOCAL PEQUEÑO", fill=self.COLOR_CYAN, font=("Outfit", 14, "bold"))

            box_w = min(int(w * 0.88), 1050)
            box_h = min(int(h * 0.72), 520)
            c.create_rectangle(w//2 - box_w//2, h//2 - box_h//2, w//2 + box_w//2, h//2 + box_h//2, fill="#0f1726", outline=self.COLOR_CYAN, width=3)
            c.create_text(w//2, h//2, text="🔧 AlexTech sobrevivió como PyME local, pero no acumuló capital para F1 ni GT World.", fill="#ffffff", font=("Outfit", 14, "bold"))

        c.create_rectangle(w//2 - 280, h - 55, w//2 + 280, h - 15, fill="#16233c", outline=self.COLOR_CYAN, width=2)
        c.create_text(w//2, h - 35, text="[ PRESIONA BOTÓN A DE XBOX O ENTER PARA REPORTE ACADÉMICO (M) ]", fill=self.COLOR_CYAN, font=("Outfit", 11, "bold"))

    # --- PANTALLA DE INICIO ---
    def draw_start_screen(self, c, w, h):
        c.create_rectangle(0, 0, w, h, fill="#070c18", outline="")

        box_w = min(int(w * 0.75), 900)
        c.create_rectangle(w//2 - box_w//2, h//2 - 180, w//2 + box_w//2, h//2 - 30, fill="#121929", outline=self.COLOR_CYAN, width=3)
        c.create_text(w//2, h//2 - 140, text="🔴 PROGRAMADO POR: ARMANDO MISAEL MATA HERNÁNDEZ", fill="#ff007a", font=("Outfit", 15, "bold"))
        c.create_text(w//2, h//2 - 100, text="ALEXANDER'S RACING QUEST", fill=self.COLOR_CYAN, font=("Outfit", 26, "bold"))
        c.create_text(w//2, h//2 - 65, text="Mueve a Alexander con la Palanca Izquierda. En los menús usa el D-Pad (Cruceta) para elegir.", fill="#ffffff", font=("Outfit", 12))

        btn_w = min(int(w * 0.5), 550)
        c.create_rectangle(w//2 - btn_w//2, h//2 + 40, w//2 + btn_w//2, h//2 + 100, fill="#18233c", outline="#00ffaa", width=2)
        c.create_text(w//2, h//2 + 70, text="[ PRESIONA BOTÓN A DE XBOX O ENTER PARA EMPEZAR ]", fill="#00ffaa", font=("Outfit", 13, "bold"))
        c.create_text(w//2, h - 45, text="Controles: Mueve el personaje con la Palanca Izquierda de Xbox / WASD | Hablar y Seleccionar: [Botón A]", fill="#8e9bb4", font=("Outfit", 11))

    # --- MAP 0: SALÓN ---
    def draw_map_classroom(self, c, w, h):
        c.create_rectangle(0, 0, w, h, fill=self.COLOR_WOOD, outline="")
        for y in range(0, h, 40):
            c.create_line(0, y, w, y, fill="#885830", width=1)

        c.create_rectangle(w * 0.05, 25, w * 0.95, 105, fill=self.COLOR_BLACKBOARD, outline="#e0c068", width=3)
        c.create_text(w//2, 65, text="AULA 1: LA IDEA INICIAL — MUEVETE CON LA PALANCA DE XBOX", fill="#ffffff", font=("Outfit", 14, "bold"))

        for row in range(2):
            for col in range(4):
                dx = int(w * 0.15) + col * int(w * 0.2)
                dy = int(h * 0.28) + row * int(h * 0.22)
                c.create_rectangle(dx, dy, dx+110, dy+55, fill=self.COLOR_DESK, outline="#4a2e18", width=2)
                c.create_text(dx+55, dy+27, text="Pupitre", fill="#e0c068", font=("Arial", 11, "bold"))

        door_color = "#00ffaa" if self.completed_modules[0] else "#ff007a"
        door_text = "PUERTA A LA CALLE [ABIERTA]" if self.completed_modules[0] else "PUERTA [BLOQUEADA - TOMA UNA DECISIÓN CON LA PROFESORA]"
        text_w = max(380, len(door_text) * 11 + 48)
        c.create_rectangle(w//2 - text_w//2, h - 65, w//2 + text_w//2, h, fill=door_color, outline="#ffffff", width=2)
        c.create_text(w//2, h - 32, text=door_text, fill="#000000", font=("Outfit", 13, "bold"))

        npc_x, npc_y = w//2, int(h * 0.22)
        self.draw_npc_pixel_sprite(c, npc_x, npc_y, "profesor", "Profesora Estefanía Franco", "Módulo 1: Ideación")

        dist_x, dist_y = int(w * 0.22), int(h * 0.52)
        self.draw_npc_pixel_sprite(c, dist_x, dist_y, "distractor", "Compañero Lucas", "Compañero de Clase")

        d1 = math.hypot(self.player_x - npc_x, self.player_y - npc_y)
        d_lucas = math.hypot(self.player_x - dist_x, self.player_y - dist_y)

        if d1 < 65:
            self.active_npc = {"id": 1, "name": "Profesora Estefanía Franco", "role": "Módulo 1: Decisión Inicial de Factibilidad"}
            c.create_rectangle(npc_x-115, npc_y-50, npc_x+115, npc_y-22, fill="#00f0ff", outline="#ffffff", width=2)
            c.create_text(npc_x, npc_y-36, text="[ Presiona Botón A / E ]", fill="#000000", font=("Outfit", 12, "bold"))
        elif d_lucas < 65:
            self.active_npc = {"id": 101, "name": "Compañero Lucas", "role": "Compañero de Clase"}
            c.create_rectangle(dist_x-115, dist_y-50, dist_x+115, dist_y-22, fill="#ff007a", outline="#ffffff", width=2)
            c.create_text(dist_x, dist_y-36, text="[ Presiona Botón A / E ]", fill="#ffffff", font=("Outfit", 12, "bold"))
        else:
            self.active_npc = None

    # --- MAP 1: LA CALLE ---
    def draw_map_street(self, c, w, h):
        c.create_rectangle(0, 0, w, h, fill=self.COLOR_GRASS, outline="")
        for x in range(20, w, 60):
            self.draw_gba_tree(c, x, 30)
        for y in range(80, h-80, 60):
            self.draw_gba_tree(c, 30, y)
            self.draw_gba_tree(c, w-40, y)

        c.create_rectangle(int(w * 0.12), 60, int(w * 0.88), h-60, fill=self.COLOR_PATH, outline=self.COLOR_PATH_BORDER, width=2)

        nx2, ny2 = int(w * 0.28), int(h * 0.42)
        self.draw_npc_pixel_sprite(c, nx2, ny2, "elena", "Dra. Elena", "Módulo 2: Curva S")

        nx3, ny3 = int(w * 0.72), int(h * 0.42)
        self.draw_npc_pixel_sprite(c, nx3, ny3, "genrich", "Máster Genrich", "Módulo 3: TRIZ")

        dist_x, dist_y = int(w * 0.5), int(h * 0.6)
        self.draw_npc_pixel_sprite(c, dist_x, dist_y, "distractor", "Vendedor Urbano", "Propuesta en Calle")

        gate_color = "#00ffaa" if self.completed_modules[1] else "#ff007a"
        gate_text = "ENTRADA A EMPRESA ALEXTECH [ABIERTA]" if self.completed_modules[1] else "PORTÓN A EMPRESA [BLOQUEADO - RESUELVE CON DRA. ELENA O MÁSTER GENRICH]"
        text_w = max(400, len(gate_text) * 11 + 48)
        c.create_rectangle(w//2 - text_w//2, h - 65, w//2 + text_w//2, h, fill=gate_color, outline="#ffffff", width=2)
        c.create_text(w//2, h - 32, text=gate_text, fill="#000000", font=("Outfit", 13, "bold"))

        d2 = math.hypot(self.player_x - nx2, self.player_y - ny2)
        d3 = math.hypot(self.player_x - nx3, self.player_y - ny3)
        d_vendedor = math.hypot(self.player_x - dist_x, self.player_y - dist_y)

        if d2 < 65:
            self.active_npc = {"id": 2, "name": "Dra. Elena", "role": "Módulo 2: Estrategia Curva S"}
            c.create_rectangle(nx2-115, ny2-50, nx2+115, ny2-22, fill="#00f0ff", outline="#ffffff", width=2)
            c.create_text(nx2, ny2-36, text="[ Presiona Botón A / E ]", fill="#000000", font=("Outfit", 12, "bold"))
        elif d3 < 65:
            self.active_npc = {"id": 3, "name": "Máster Genrich", "role": "Módulo 3: Método TRIZ"}
            c.create_rectangle(nx3-115, ny3-50, nx3+115, ny3-22, fill="#00f0ff", outline="#ffffff", width=2)
            c.create_text(nx3, ny3-36, text="[ Presiona Botón A / E ]", fill="#000000", font=("Outfit", 12, "bold"))
        elif d_vendedor < 65:
            self.active_npc = {"id": 102, "name": "Vendedor Urbano", "role": "Propuesta en la Calle"}
            c.create_rectangle(dist_x-115, dist_y-50, dist_x+115, dist_y-22, fill="#ff007a", outline="#ffffff", width=2)
            c.create_text(dist_x, dist_y-36, text="[ Presiona Botón A / E ]", fill="#ffffff", font=("Outfit", 12, "bold"))
        else:
            self.active_npc = None

    # --- MAP 2: EMPRESA ---
    def draw_map_company(self, c, w, h):
        c.create_rectangle(0, 0, w, h, fill="#101828", outline="")
        for x in range(0, w, 60):
            c.create_line(x, 0, x, h, fill="#1e293b", width=1)

        c.create_text(w//2, 40, text="🏢 SEDE CORPORATIVA ALEXTECH — CONSECUENCIAS ACUMULADAS", fill=self.COLOR_CYAN, font=("Outfit", 15, "bold"))

        nx4, ny4 = int(w * 0.28), int(h * 0.42)
        self.draw_npc_pixel_sprite(c, nx4, ny4, "sofia", "Coach Sofía", "Módulo 4: PNL & Liderazgo")

        nx5, ny5 = int(w * 0.72), int(h * 0.42)
        self.draw_npc_pixel_sprite(c, nx5, ny5, "fundadores", "Fundadores Reales", "Módulo 5: Modelo de Mercado")

        dist_x, dist_y = int(w * 0.5), int(h * 0.6)
        self.draw_npc_pixel_sprite(c, dist_x, dist_y, "distractor", "Don Ramiro", "Asesor Interno")

        limo_color = "#00ffaa" if self.completed_modules[2] else "#ff007a"
        limo_text = "🏎️ AVANZAR AL DESTINO FINAL [LISTO]" if self.completed_modules[2] else "DESTINO FINAL [BLOQUEADO - RESUELVE CON COACH SOFÍA O FUNDADORES]"
        text_w = max(420, len(limo_text) * 11 + 48)
        c.create_rectangle(w//2 - text_w//2, h - 65, w//2 + text_w//2, h, fill=limo_color, outline="#ffffff", width=2)
        c.create_text(w//2, h - 32, text=limo_text, fill="#000000", font=("Outfit", 13, "bold"))

        d4 = math.hypot(self.player_x - nx4, self.player_y - ny4)
        d5 = math.hypot(self.player_x - nx5, self.player_y - ny5)
        d_ramiro = math.hypot(self.player_x - dist_x, self.player_y - dist_y)

        if d4 < 65:
            self.active_npc = {"id": 4, "name": "Coach Sofía", "role": "Módulo 4: PNL & 7 Hábitos"}
            c.create_rectangle(nx4-115, ny4-50, nx4+115, ny4-22, fill="#00f0ff", outline="#ffffff", width=2)
            c.create_text(nx4, ny4-36, text="[ Presiona Botón A / E ]", fill="#000000", font=("Outfit", 12, "bold"))
        elif d5 < 65:
            self.active_npc = {"id": 5, "name": "Fundadores Reales", "role": "Módulo 5: Modelo MVP vs Masivo"}
            c.create_rectangle(nx5-115, ny5-50, nx5+115, ny5-22, fill="#00f0ff", outline="#ffffff", width=2)
            c.create_text(nx5, ny5-36, text="[ Presiona Botón A / E ]", fill="#000000", font=("Outfit", 12, "bold"))
        elif d_ramiro < 65:
            self.active_npc = {"id": 103, "name": "Don Ramiro", "role": "Asesor Interno"}
            c.create_rectangle(dist_x-115, dist_y-50, dist_x+115, dist_y-22, fill="#ff007a", outline="#ffffff", width=2)
            c.create_text(dist_x, dist_y-36, text="[ Presiona Botón A / E ]", fill="#ffffff", font=("Outfit", 12, "bold"))
        else:
            self.active_npc = None

    # --- ENDING 1: ÉXITO ABSOLUTO ---
    def draw_map_racetrack_success(self, c, w, h):
        c.create_rectangle(0, 0, w, h, fill=self.COLOR_ASPHALT, outline="")
        for i in range(0, h, 20):
            fill1 = "#ffffff" if (i//20)%2==0 else "#000000"
            fill2 = "#000000" if (i//20)%2==0 else "#ffffff"
            c.create_rectangle(w//2 - 20, i, w//2, i+20, fill=fill1, outline="")
            c.create_rectangle(w//2, i, w//2 + 20, i+20, fill=fill2, outline="")

        car1_x, car1_y = int(w * 0.75), int(h * 0.38)
        c.create_rectangle(car1_x-95, car1_y-35, car1_x+95, car1_y+35, fill=self.COLOR_RACE_RED, outline="#ffffff", width=2)
        c.create_rectangle(car1_x-35, car1_y-20, car1_x+35, car1_y+20, fill="#111111", outline="")
        c.create_text(car1_x, car1_y, text="🏎️ ALEXTECH FÓRMULA 1", fill=self.COLOR_CYAN, font=("Outfit", 11, "bold"))

        car2_x, car2_y = int(w * 0.75), int(h * 0.62)
        c.create_rectangle(car2_x-110, car2_y-35, car2_x+110, car2_y+35, fill=self.COLOR_GT_BLUE, outline="#ffffff", width=2)
        c.create_rectangle(car2_x-40, car2_y-22, car2_x+40, car2_y+22, fill="#111111", outline="")
        c.create_text(car2_x, car2_y, text="🏁 ALEXTECH GT WORLD CHALLENGE", fill=self.COLOR_GOLD, font=("Outfit", 10, "bold"))

        c.create_rectangle(w * 0.05, 20, w * 0.95, 90, fill="#1e293b", outline=self.COLOR_GOLD, width=3)
        c.create_text(w//2, 55, text="🏆 FINAL 1: ÉXITO ABSOLUTO — PATROCINADOR OFICIAL DE LA FÓRMULA 1 Y GT WORLD CHALLENGE!", fill=self.COLOR_GOLD, font=("Outfit", 14, "bold"))

        nx6, ny6 = int(w * 0.58), h//2
        self.draw_npc_pixel_sprite(c, nx6, ny6, "piloto", "Director Escudería", "F1 & GT World")

        if math.hypot(self.player_x - nx6, self.player_y - ny6) < 65:
            self.active_npc = {"id": 6, "name": "Director de Escudería", "role": "🏆 FINAL 1: PATROCINIO OFICIAL FIRMADO"}
            c.create_rectangle(nx6-115, ny6-50, nx6+115, ny6-22, fill="#00f0ff", outline="#ffffff", width=2)
            c.create_text(nx6, ny6-36, text="[ Presiona Botón A / E ]", fill="#000000", font=("Outfit", 12, "bold"))
        else:
            self.active_npc = None

    # --- ENDING 2: FRACASO - TRABAJO EN LA CALLE ---
    def draw_map_street_failure_job(self, c, w, h):
        c.create_rectangle(0, 0, w, h, fill="#2a1a1a", outline="")
        c.create_rectangle(w * 0.05, 30, w * 0.95, 95, fill="#3d1515", outline="#ff007a", width=3)
        c.create_text(w//2, 62, text="❌ FINAL 2: ALEXTECH QUEBRÓ — TRABAJO DE MANTENIMIENTO EN LA CALLE QUE ALEXANDER NO QUERÍA", fill="#ff007a", font=("Outfit", 13, "bold"))

        for i in range(15):
            rx = (int(w * 0.1) + (i * 70) + (self.timer_seconds * 15)) % int(w * 0.8) + int(w * 0.1)
            ry = (110 + (i * 35) + (self.timer_seconds * 20)) % (h - 150) + 110
            c.create_line(rx, ry, rx - 4, ry + 12, fill="#00f0ff", width=1)

        c.create_rectangle(w//2 - 160, h//2 - 70, w//2 + 160, h//2 + 70, fill="#1c1212", outline="#ff007a", width=2)
        c.create_text(w//2, h//2 - 35, text="🛠️ Puesto de Reparaciones de Cables Usados", fill="#ffffff", font=("Outfit", 13, "bold"))
        c.create_text(w//2, h//2 + 10, text="Trabajo de 12 Horas Diarias para Pagar Deudas", fill="#8e9bb4", font=("Outfit", 11, "bold"))

        boss_x, boss_y = w//2 + 200, h//2
        self.draw_npc_pixel_sprite(c, boss_x, boss_y, "distractor", "Jefe de Contrata", "Supervisando a Alexander")

        if math.hypot(self.player_x - boss_x, self.player_y - boss_y) < 65:
            self.active_npc = {"id": 104, "name": "Jefe de Contrata", "role": "❌ FINAL 2: TRABAJO NO DESEADO EN LA CALLE"}
            c.create_rectangle(boss_x-115, boss_y-50, boss_x+115, boss_y-22, fill="#ff007a", outline="#ffffff", width=2)
            c.create_text(boss_x, boss_y-36, text="[ Presiona Botón A / E ]", fill="#ffffff", font=("Outfit", 12, "bold"))
        else:
            self.active_npc = None

    # --- ENDING 3: EMPRESA PEQUEÑA ---
    def draw_map_small_shop(self, c, w, h):
        c.create_rectangle(0, 0, w, h, fill="#1e222a", outline="")
        c.create_rectangle(w * 0.1, 40, w * 0.9, 100, fill="#283244", outline=self.COLOR_CYAN, width=3)
        c.create_text(w//2, 70, text="⚖️ FINAL 3: TALLER LOCAL PEQUEÑO — ALEXTECH SOBREVIVE PERO SIN LLEGAR A LA F1 NI GT WORLD", fill=self.COLOR_CYAN, font=("Outfit", 11, "bold"))

        c.create_rectangle(w//2 - 140, h//2 - 70, w//2 + 140, h//2 + 70, fill="#121824", outline=self.COLOR_CYAN, width=2)
        c.create_text(w//2, h//2 - 20, text="🔧 AlexTech Local Repairs", fill="#ffffff", font=("Outfit", 13, "bold"))
        c.create_text(w//2, h//2 + 18, text="Genera para pagar renta, pero no hubo capital para F1 ni GT World", fill="#8e9bb4", font=("Outfit", 10))

    # --- EMOTION CUTSCENE SPRITE RENDERERS ---
    def draw_alexander_jumping_happy_sprite(self, c, x, y):
        colors = ["#ff007a", "#00ffaa", "#ffd700", "#00f0ff"]
        for i in range(8):
            cx = x - 40 + (i * 12)
            cy = y - 35 - ((self.timer_seconds * 10 + i * 5) % 25)
            c.create_rectangle(cx, cy, cx+4, cy+4, fill=colors[i % 4], outline="")

        c.create_rectangle(x-7, y+8, x-1, y+16, fill="#1c3b70", outline="#000")
        c.create_rectangle(x+1, y+8, x+7, y+16, fill="#1c3b70", outline="#000")
        c.create_rectangle(x-10, y-6, x+10, y+9, fill="#e03838", outline="#000")
        c.create_rectangle(x-8, y-20, x+8, y-5, fill=self.COLOR_SKIN, outline="#000")
        
        c.create_text(x, y-12, text="😄", font=("Segoe UI Emoji", 10))

        c.create_line(x-10, y-2, x-18, y-16, fill=self.COLOR_SKIN, width=3)
        c.create_line(x+10, y-2, x+18, y-16, fill=self.COLOR_SKIN, width=3)

        c.create_rectangle(x-10, y-25, x+10, y-18, fill="#00f0ff", outline="#000")

        c.create_rectangle(x-120, y-60, x+120, y-35, fill="#103028", outline="#00ffaa", width=2)
        c.create_text(x, y-47, text="🎉 ¡ALEXANDER ESTÁ FELIZ Y SALTANDO DE ALEGRÍA!", fill="#00ffaa", font=("Outfit", 10, "bold"))

    def draw_alexander_crying_sad_sprite(self, c, x, y):
        c.create_rectangle(x-12, y+4, x+12, y+14, fill="#1c3b70", outline="#000")
        c.create_rectangle(x-10, y-8, x+10, y+5, fill="#ff6600", outline="#000")
        c.create_rectangle(x-8, y-22, x+8, y-7, fill=self.COLOR_SKIN, outline="#000")

        c.create_text(x, y-14, text="😭", font=("Segoe UI Emoji", 11))

        drop_y = y - 10 + (self.timer_seconds % 3) * 6
        c.create_oval(x-9, drop_y, x-6, drop_y+4, fill="#00f0ff", outline="")
        c.create_oval(x+6, drop_y, x+9, drop_y+4, fill="#00f0ff", outline="")

        c.create_rectangle(x-140, y-60, x+140, y-35, fill="#3d1515", outline="#ff007a", width=2)
        c.create_text(x, y-47, text="😭 ALEXANDER LLORA SOBRE SUS MALAS DECISIONES...", fill="#ff007a", font=("Outfit", 9, "bold"))

    def draw_gba_tree(self, c, x, y):
        c.create_rectangle(x-4, y+10, x+4, y+22, fill=self.COLOR_TREE_TRUNK, outline="")
        c.create_oval(x-20, y-15, x+20, y+15, fill=self.COLOR_TREE_LEAF, outline="")
        c.create_oval(x-12, y-12, x+12, y+5, fill=self.COLOR_TREE_HIGH, outline="")

    # Pixel Character Sprites Renderers
    def draw_alexander_pixel_sprite(self, c, x, y, direction, frame):
        c.create_oval(x-12, y+14, x+12, y+22, fill="#000000", outline="", stipple="gray50")
        leg_l = -3 if frame == 0 else 3
        leg_r = 3 if frame == 0 else -3

        shirt_color = "#ff6600" if (self.current_map == 3 and (self.company_score < 45 or self.capital <= 5000)) else "#e03838"

        if direction == "down":
            c.create_rectangle(x-7+leg_l, y+8, x-1, y+18, fill="#1c3b70", outline="#000")
            c.create_rectangle(x+1, y+8, x+7+leg_r, y+18, fill="#1c3b70", outline="#000")
            c.create_rectangle(x-10, y-6, x+10, y+9, fill=shirt_color, outline="#000")
            c.create_rectangle(x-3, y-6, x+3, y+9, fill="#ffffff", outline="")
            c.create_rectangle(x-8, y-20, x+8, y-5, fill=self.COLOR_SKIN, outline="#000")
            c.create_rectangle(x-6, y-14, x-2, y-10, fill="#111", outline="")
            c.create_rectangle(x+2, y-14, x+6, y-10, fill="#111", outline="")
            c.create_rectangle(x-10, y-25, x+10, y-18, fill="#00f0ff", outline="#000")

        elif direction == "up":
            c.create_rectangle(x-7+leg_l, y+8, x-1, y+18, fill="#1c3b70", outline="#000")
            c.create_rectangle(x+1, y+8, x+7+leg_r, y+18, fill="#1c3b70", outline="#000")
            c.create_rectangle(x-10, y-6, x+10, y+9, fill=shirt_color, outline="#000")
            c.create_rectangle(x-7, y-4, x+7, y+6, fill="#f0c030", outline="#000")
            c.create_rectangle(x-8, y-20, x+8, y-5, fill="#4a2e18", outline="#000")
            c.create_rectangle(x-10, y-25, x+10, y-18, fill="#00f0ff", outline="#000")

        elif direction == "left":
            c.create_rectangle(x-5+leg_l, y+8, x+2, y+18, fill="#1c3b70", outline="#000")
            c.create_rectangle(x-8, y-6, x+6, y+9, fill=shirt_color, outline="#000")
            c.create_rectangle(x-8, y-20, x+4, y-5, fill=self.COLOR_SKIN, outline="#000")
            c.create_rectangle(x-6, y-14, x-3, y-10, fill="#111", outline="")
            c.create_rectangle(x-9, y-25, x+7, y-18, fill="#00f0ff", outline="#000")

        elif direction == "right":
            c.create_rectangle(x-2, y+8, x+5+leg_r, y+18, fill="#1c3b70", outline="#000")
            c.create_rectangle(x-6, y-6, x+8, y+9, fill=shirt_color, outline="#000")
            c.create_rectangle(x-4, y-20, x+8, y-5, fill=self.COLOR_SKIN, outline="#000")
            c.create_rectangle(x+3, y-14, x+6, y-10, fill="#111", outline="")
            c.create_rectangle(x-7, y-25, x+9, y-18, fill="#00f0ff", outline="#000")

        lbl_text = "Alexander (Técnico)" if (self.current_map == 3 and (self.company_score < 45 or self.capital <= 5000)) else "Alexander"
        c.create_text(x, y+26, text=lbl_text, fill="#00f0ff", font=("Outfit", 9, "bold"))

    def draw_npc_pixel_sprite(self, c, x, y, npc_type, name, role):
        c.create_oval(x-12, y+14, x+12, y+22, fill="#000000", outline="", stipple="gray50")

        if npc_type == "distractor":
            c.create_rectangle(x-6, y+8, x+6, y+18, fill="#1a1028", outline="#000")
            c.create_rectangle(x-9, y-6, x+9, y+9, fill="#ff007a", outline="#000")
            c.create_rectangle(x-7, y-20, x+7, y-5, fill=self.COLOR_SKIN, outline="#000")
            c.create_rectangle(x-9, y-25, x+9, y-18, fill="#ff007a", outline="#000")

        elif npc_type == "profesor":
            c.create_rectangle(x-6, y+8, x+6, y+18, fill="#4a1525", outline="#000")
            c.create_rectangle(x-9, y-6, x+9, y+9, fill="#e03868", outline="#000")
            c.create_rectangle(x-7, y-20, x+7, y-5, fill=self.COLOR_SKIN, outline="#000")
            c.create_rectangle(x-9, y-25, x+9, y-17, fill="#381808", outline="#000")
            c.create_rectangle(x-11, y-18, x-7, y-4, fill="#381808", outline="")
            c.create_rectangle(x+7, y-18, x+11, y-4, fill="#381808", outline="")

        elif npc_type == "elena":
            c.create_rectangle(x-6, y+8, x+6, y+18, fill="#202030", outline="#000")
            c.create_rectangle(x-9, y-6, x+9, y+9, fill="#7000ff", outline="#000")
            c.create_rectangle(x-7, y-20, x+7, y-5, fill=self.COLOR_SKIN, outline="#000")

        elif npc_type == "genrich":
            c.create_rectangle(x-6, y+8, x+6, y+18, fill="#151520", outline="#000")
            c.create_rectangle(x-9, y-6, x+9, y+9, fill="#ff007a", outline="#000")
            c.create_rectangle(x-7, y-20, x+7, y-5, fill=self.COLOR_SKIN, outline="#000")

        elif npc_type == "sofia":
            c.create_rectangle(x-6, y+8, x+6, y+18, fill="#102018", outline="#000")
            c.create_rectangle(x-9, y-6, x+9, y+9, fill="#00ffaa", outline="#000")
            c.create_rectangle(x-7, y-20, x+7, y-5, fill=self.COLOR_SKIN, outline="#000")

        elif npc_type == "fundadores":
            c.create_rectangle(x-6, y+8, x+6, y+18, fill="#18233c", outline="#000")
            c.create_rectangle(x-9, y-6, x+9, y+9, fill="#ffaa00", outline="#000")
            c.create_rectangle(x-7, y-20, x+7, y-5, fill=self.COLOR_SKIN, outline="#000")

        elif npc_type == "piloto":
            c.create_rectangle(x-6, y+8, x+6, y+18, fill="#e02828", outline="#000")
            c.create_rectangle(x-9, y-6, x+9, y+9, fill="#e02828", outline="#000")
            c.create_oval(x-9, y-24, x+9, y-5, fill="#e02828", outline="#ffffff", width=2)
            c.create_rectangle(x-6, y-18, x+6, y-12, fill="#000000", outline="")

        c.create_text(x, y+26, text=f"{name}\n({role})", fill="#ffffff", font=("Outfit", 8, "bold"), justify="center")

    # --------------------------------------------------------------------------
    # HUD HEADER
    # --------------------------------------------------------------------------
    def create_hud_header(self):
        self.hud_frame = ctk.CTkFrame(self, fg_color="#0b101c", height=58, corner_radius=0)

        title_lbl = ctk.CTkLabel(
            self.hud_frame,
            text="🎮 PROGRAMADO POR ARMANDO MISAEL MATA HERNÁNDEZ",
            font=ctk.CTkFont(family="Outfit", size=14, weight="bold"),
            text_color=self.COLOR_CYAN
        )
        title_lbl.pack(side="left", padx=16, pady=10)

        self.map_name_lbl = ctk.CTkLabel(
            self.hud_frame,
            text="📍 MAPA 1/4: El Salón de Clases",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color=self.COLOR_GOLD
        )
        self.map_name_lbl.pack(side="left", padx=16, pady=10)

        btn_inv = ctk.CTkButton(
            self.hud_frame,
            text="🎒 Mochila (Y / I)",
            width=120,
            height=32,
            fg_color="#18233c",
            hover_color="#1a2744",
            text_color=self.COLOR_CYAN,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.toggle_inventory
        )
        btn_inv.pack(side="left", padx=8)

        btn_rep = ctk.CTkButton(
            self.hud_frame,
            text="📊 Reporte (X / M)",
            width=130,
            height=32,
            fg_color="#102520",
            hover_color="#1a3d35",
            text_color="#00ffaa",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.toggle_professor_report
        )
        btn_rep.pack(side="left", padx=5)

        self.score_lbl = ctk.CTkLabel(
            self.hud_frame,
            text="📊 Viabilidad: 50%",
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            text_color="#00ffaa"
        )
        self.score_lbl.pack(side="right", padx=14, pady=10)

        self.capital_lbl = ctk.CTkLabel(
            self.hud_frame,
            text="💰 Capital: $10,000",
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            text_color=self.COLOR_GOLD
        )
        self.capital_lbl.pack(side="right", padx=14, pady=10)

    # --------------------------------------------------------------------------
    # DIALOGUE & PERMANENT DECISION LOCK ENGINE
    # --------------------------------------------------------------------------
    def create_gba_dialogue_box(self):
        self.dialogue_frame = ctk.CTkFrame(self, fg_color="#182030", border_color=self.COLOR_FLOWER_RED, border_width=3, corner_radius=16)

    def interact_action(self):
        if self.in_intro_video:
            self.finish_intro_and_start_game()
            return

        if self.in_ending_video:
            self.in_ending_video = False
            self.in_start_screen = True
            self.current_map = 0
            self.company_score = 50
            self.capital = 10000
            self.player_x = 700
            self.player_y = 450
            self.completed_modules = [False, False, False]
            self.inventory_items = []
            self.decisions_log = []
            self.locked_decisions = {}
            self.active_npc = None
            self.update_metrics(0, 0)
            self.draw_current_map()
            return

        if self.in_start_screen:
            self.in_start_screen = False
            self.draw_current_map()
            return

        if self.in_dialogue and self.has_active_options:
            if self.decision_focused_index == 0 and self.current_choice_a_func:
                self.current_choice_a_func()
            elif self.decision_focused_index == 1 and self.current_choice_b_func:
                self.current_choice_b_func()
            elif self.decision_focused_index == 2 and getattr(self, 'current_choice_c_func', None):
                self.current_choice_c_func()
            return

        if not self.active_npc:
            return

        self.in_dialogue = True
        npc = self.active_npc
        m_id = npc["id"]

        self.dialogue_frame.place(relx=0.5, rely=0.76, anchor="center", relwidth=0.92, relheight=0.44)

        for widget in self.dialogue_frame.winfo_children():
            widget.destroy()

        h_frame = ctk.CTkFrame(self.dialogue_frame, fg_color="transparent")
        h_frame.pack(fill="x", padx=18, pady=(10, 4))

        ctk.CTkLabel(h_frame, text=f"🔴 {npc['name']} — {npc['role']}", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.COLOR_CYAN).pack(side="left")
        ctk.CTkButton(h_frame, text="✖ [Cerrar (B)]", width=95, height=30, font=ctk.CTkFont(size=12, weight="bold"), fg_color="transparent", hover_color="#2b0a18", text_color="#ff007a", command=self.close_dialogue).pack(side="right")

        body_frame = ctk.CTkFrame(self.dialogue_frame, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=18, pady=4)

        # CHECK IF DECISION IS ALREADY PERMANENTLY LOCKED FOR THIS NPC!
        if m_id in self.locked_decisions:
            self.has_active_options = False
            choice_text, response_text = self.locked_decisions[m_id]

            ctk.CTkLabel(
                body_frame,
                text=f"📌 TU ELECCIÓN REGISTRADA PERMANENTEMENTE:\n{choice_text}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=self.COLOR_CYAN,
                justify="left",
                wraplength=1000
            ).pack(anchor="w", pady=(2, 6))

            ctk.CTkLabel(
                body_frame,
                text=f"{response_text}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#ffffff",
                justify="left",
                wraplength=1000
            ).pack(anchor="w", pady=(0, 6))

            ctk.CTkLabel(
                body_frame,
                text="🔒 DECISIÓN FIJA EN EL HISTORIAL DE ALEXTECH (NO SE PUEDE CAMBIAR)",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=self.COLOR_GOLD
            ).pack(anchor="w", pady=2)

            ctk.CTkButton(
                body_frame,
                text="✅ ENTENDIDO (BOTÓN A / ENTER)",
                font=ctk.CTkFont(size=12, weight="bold"),
                height=34,
                fg_color="#18233c",
                command=self.close_dialogue
            ).pack(pady=8)
            return

        if m_id == 1:
            self.decision_m1(body_frame)
        elif m_id == 2:
            self.decision_m2(body_frame)
        elif m_id == 3:
            self.decision_m3(body_frame)
        elif m_id == 4:
            self.decision_m4(body_frame)
        elif m_id == 5:
            self.decision_m5(body_frame)
        elif m_id == 6:
            self.dialogue_m6(body_frame)
        elif m_id == 101:
            self.dialogue_distractor_lucas(body_frame)
        elif m_id == 102:
            self.dialogue_distractor_vendedor(body_frame)
        elif m_id == 103:
            self.dialogue_distractor_ramiro(body_frame)
        elif m_id == 104:
            self.dialogue_failure_job(body_frame)

    def close_dialogue(self):
        was_final_npc = (self.active_npc and self.active_npc["id"] in [6, 104])
        self.dialogue_frame.place_forget()
        self.in_dialogue = False
        self.has_active_options = False

        if was_final_npc:
            self.after(300, self.trigger_ending_video)

    def setup_decision_options(self, parent, label_a_text, choice_a_fn, label_b_text, choice_b_fn, label_c_text=None, choice_c_fn=None):
        self.has_active_options = True
        self.max_option_index = 2 if choice_c_fn else 1
        self.decision_focused_index = 0
        self.current_choice_a_func = choice_a_fn
        self.current_choice_b_func = choice_b_fn
        self.current_choice_c_func = choice_c_fn

        btn_f = ctk.CTkFrame(parent, fg_color="transparent")
        btn_f.pack(fill="x", pady=6)

        ctk.CTkLabel(btn_f, text="👉 Usa la Cruceta D-Pad o Flechas [▲ / ▼] para seleccionar y [Botón A / Enter] para confirmar:", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.COLOR_CYAN).pack(anchor="w", pady=(0, 4))

        self.opt_btn_a = ctk.CTkButton(
            btn_f,
            text=f"A) {label_a_text}",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            fg_color="#103028",
            border_color="#00ffaa",
            border_width=2,
            text_color="#00ffaa",
            anchor="w",
            command=choice_a_fn
        )
        self.opt_btn_a.pack(fill="x", pady=3)

        self.opt_btn_b = ctk.CTkButton(
            btn_f,
            text=f"B) {label_b_text}",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            fg_color="#1d2636",
            border_color="#3a4a66",
            border_width=1,
            text_color="#8e9bb4",
            anchor="w",
            command=choice_b_fn
        )
        self.opt_btn_b.pack(fill="x", pady=3)

        if label_c_text and choice_c_fn:
            self.opt_btn_c = ctk.CTkButton(
                btn_f,
                text=f"C) {label_c_text}",
                font=ctk.CTkFont(size=12, weight="bold"),
                height=36,
                fg_color="#3d1515",
                border_color="#ff007a",
                border_width=1,
                text_color="#ff007a",
                anchor="w",
                command=choice_c_fn
            )
            self.opt_btn_c.pack(fill="x", pady=3)
        else:
            self.opt_btn_c = None

        self.update_option_focus_styles()

    # --- PERMANENT DECISION HANDLERS ---
    def decision_m1(self, parent):
        t = "Profesora Estefanía Franco: 'Alexander, tienes la idea de crear AlexTech para patrocinar a la Fórmula 1 y GT World Challenge. ¿Cómo decides asignar tu capital inicial?'"
        ctk.CTkLabel(parent, text=t, font=ctk.CTkFont(size=13, weight="bold"), text_color="#fff", wraplength=1000, justify="left").pack(anchor="w")

        res_lbl = ctk.CTkLabel(parent, text="", font=ctk.CTkFont(size=13, weight="bold"), wraplength=1000, justify="left")
        res_lbl.pack(anchor="w", pady=4)

        def choice_a():
            self.has_active_options = False
            self.update_metrics(-25, -4000)
            self.completed_modules[0] = True
            c_text = "A) Apostar todo el capital al desarrollo inmediato de la idea sin hacer estudios"
            r_text = "💬 REACCIÓN DE LA PROFESORA ESTEFANÍA FRANCO:\n'¡Cuidado Alexander! Apostar todo sin analizar las 4 Factividades provocó pérdidas de $4,000 USD por imprevistos legales...'"
            self.locked_decisions[1] = (c_text, r_text)
            self.decisions_log.append("M1: Apostó todo sin estudio de factibilidad.")
            res_lbl.configure(text=r_text, text_color="#ff007a")
            self.after(2800, self.close_dialogue)
            self.draw_current_map()

        def choice_b():
            self.has_active_options = False
            self.update_metrics(+25, +15000)
            self.completed_modules[0] = True
            c_text = "B) Ejecutar un análisis de Factibilidad de Mercado, Técnica, Financiera y Legal"
            r_text = "💬 REACCIÓN DE LA PROFESORA ESTEFANÍA FRANCO:\n'¡Excelente pensamiento ejecutivo, Alexander! Evaluaste las 4 Factividades. Aseguraste $25,000 USD y tu idea es sólida.'"
            self.locked_decisions[1] = (c_text, r_text)
            if "📜 Plan de Factibilidad M1" not in self.inventory_items:
                self.inventory_items.append("📜 Plan de Factibilidad M1")
            self.decisions_log.append("M1: Ejecutó evaluación de las 4 Factibilidades.")
            res_lbl.configure(text=r_text, text_color="#00ffaa")
            self.after(2800, self.close_dialogue)
            self.draw_current_map()

        def choice_c():
            self.has_active_options = False
            self.update_metrics(-30, 0)
            self.completed_modules[0] = True
            c_text = "C) No hacer caso a la clase, no hacer tareas ni prestar atención e irme a la calle"
            r_text = (
                "💬 REACCIÓN DE LA PROFESORA ESTEFANÍA FRANCO (REGAÑANDO MOLESTA):\n"
                "'¡Alexander, qué falta de respeto y de responsabilidad! Decidiste no hacer tus tareas, "
                "ignorar mi clase de Innovación Empresarial y salirte a la calle sin bases académicas. "
                "¡Vete de mi salón! Te abro la puerta pero asumirás la pérdida de viabilidad por rebelde (-30% Viabilidad).'"
            )
            self.locked_decisions[1] = (c_text, r_text)
            self.decisions_log.append("M1: No hizo caso a la Profesora Estefanía Franco, no hizo tareas y se salió de clase.")
            res_lbl.configure(text=r_text, text_color="#ff007a")
            self.after(3000, self.close_dialogue)
            self.draw_current_map()

        self.setup_decision_options(
            parent,
            "Apostar todo el capital al desarrollo inmediato de la idea sin hacer estudios",
            choice_a,
            "Ejecutar un análisis de Factibilidad de Mercado, Técnica, Financiera y Legal",
            choice_b,
            "🚪 No hacer caso a la clase, no hacer tareas ni prestar atención e irme a la calle",
            choice_c
        )

    def decision_m2(self, parent):
        t = "Dra. Elena: 'Alexander, para posicionar el producto tecnológico de AlexTech en el mercado compitiendo con marcas globales, ¿cuál es tu estrategia de producto?'"
        ctk.CTkLabel(parent, text=t, font=ctk.CTkFont(size=13, weight="bold"), text_color="#fff", wraplength=1000, justify="left").pack(anchor="w")

        res_lbl = ctk.CTkLabel(parent, text="", font=ctk.CTkFont(size=13, weight="bold"), wraplength=1000, justify="left")
        res_lbl.pack(anchor="w", pady=4)

        def choice_a():
            self.has_active_options = False
            self.update_metrics(-15, -3000)
            c_text = "A) Lanzar una réplica exacta del producto dominante a menor precio"
            r_text = "💬 REACCIÓN DE LA DRA. ELENA:\n'Te equivocaste Alexander. Al copiar una tecnología madura entraste en la fase plana de la Curva S. Caíste en guerra de precios que redujo tus ganancias.'"
            self.locked_decisions[2] = (c_text, r_text)
            self.decisions_log.append("M2: Copió el producto maduro existente.")
            res_lbl.configure(text=r_text, text_color="#ff007a")
            self.after(2800, self.close_dialogue)

        def choice_b():
            self.has_active_options = False
            self.update_metrics(+20, +25000)
            c_text = "B) Invertir en I+D para posicionarnos en el punto de inflexión de la Curva S tecnológica"
            r_text = "💬 REACCIÓN DE LA DRA. ELENA:\n'¡Brillante visión tecnológica! Innovaste justo en el punto de inflexión de la Curva S. Obtuviste monopolio temporal y tu capital subió a $25,000 USD adicional.'"
            self.locked_decisions[2] = (c_text, r_text)
            if "📈 Gráfico de Curva S M2" not in self.inventory_items:
                self.inventory_items.append("📈 Gráfico de Curva S M2")
            self.decisions_log.append("M2: Innovó en el punto de inflexión de la Curva S.")
            res_lbl.configure(text=r_text, text_color="#00ffaa")
            self.after(2800, self.close_dialogue)

        self.setup_decision_options(
            parent,
            "Lanzar una réplica exacta del producto dominante a menor precio",
            choice_a,
            "Invertir en I+D para posicionarnos en la Curva S tecnológica",
            choice_b
        )

    def decision_m3(self, parent):
        t = "Máster Genrich: 'Alexander, se presenta un conflicto técnico: el cliente requiere mayor velocidad pero el sistema genera consumo energético insostenible. ¿Cómo lo resuelves?'"
        ctk.CTkLabel(parent, text=t, font=ctk.CTkFont(size=13, weight="bold"), text_color="#fff", wraplength=1000, justify="left").pack(anchor="w")

        res_lbl = ctk.CTkLabel(parent, text="", font=ctk.CTkFont(size=13, weight="bold"), wraplength=1000, justify="left")
        res_lbl.pack(anchor="w", pady=4)

        def choice_a():
            self.has_active_options = False
            self.update_metrics(-20, -6000)
            self.completed_modules[1] = True
            c_text = "A) Adquirir servidores físicos de alta gama gastando el presupuesto disponible"
            r_text = "💬 REACCIÓN DEL MÁSTER GENRICH:\n'Cometiste un error de ingeniería. Forzaste la solución comprando servidores físicos costosos en lugar de resolver la contradicción. Tu capital cayó. Portón Abierto.'"
            self.locked_decisions[3] = (c_text, r_text)
            self.decisions_log.append("M3: Compró hardware costoso.")
            res_lbl.configure(text=r_text, text_color="#ff007a")
            self.after(2800, self.close_dialogue)
            self.draw_current_map()

        def choice_b():
            self.has_active_options = False
            self.update_metrics(+25, +40000)
            self.completed_modules[1] = True
            c_text = "B) Aplicar la Matriz TRIZ e Idealidad para optimizar por algoritmos de software"
            r_text = "💬 REACCIÓN DEL MÁSTER GENRICH:\n'¡Maestría en TRIZ! Usaste el Principio de Idealidad para resolver la contradicción mediante software. Maximizaste la velocidad sin consumir energía ni dinero sobrante. Portón Abierto.'"
            self.locked_decisions[3] = (c_text, r_text)
            if "🧩 Matriz TRIZ & Idealidad M3" not in self.inventory_items:
                self.inventory_items.append("🧩 Matriz TRIZ & Idealidad M3")
            self.decisions_log.append("M3: Aplicó Idealidad y TRIZ por software.")
            res_lbl.configure(text=r_text, text_color="#00ffaa")
            self.after(2800, self.close_dialogue)
            self.draw_current_map()

        self.setup_decision_options(
            parent,
            "Adquirir servidores físicos de alta gama gastando el presupuesto disponible",
            choice_a,
            "Aplicar la Matriz TRIZ e Idealidad para optimizar por algoritmos de software",
            choice_b
        )

    def decision_m4(self, parent):
        t = "Coach Sofía: 'Alexander, los ejecutivos tradicionales de la junta directiva temen migrar al modelo digital por miedo al fracaso. ¿Cómo reaccionas?'"
        ctk.CTkLabel(parent, text=t, font=ctk.CTkFont(size=13, weight="bold"), text_color="#fff", wraplength=1000, justify="left").pack(anchor="w")

        res_lbl = ctk.CTkLabel(parent, text="", font=ctk.CTkFont(size=13, weight="bold"), wraplength=1000, justify="left")
        res_lbl.pack(anchor="w", pady=4)

        def choice_a():
            self.has_active_options = False
            self.update_metrics(-15, -2000)
            c_text = "A) Exigir la adopción inmediata del modelo digital mediante orden ejecutiva"
            r_text = "💬 REACCIÓN DE COACH SOFÍA:\n'La imposición genera resistencia. Tu agresividad creó pánico y huelga interna en la junta directiva. Perdiste credibilidad de liderazgo.'"
            self.locked_decisions[4] = (c_text, r_text)
            self.decisions_log.append("M4: Reaccionó con lenguaje agresivo.")
            res_lbl.configure(text=r_text, text_color="#ff007a")
            self.after(2800, self.close_dialogue)

        def choice_b():
            self.has_active_options = False
            self.update_metrics(+20, +50000)
            c_text = "B) Utilizar el Reencuadre PNL y la Rueda de 7 Hábitos para alinear a la directiva"
            r_text = "💬 REACCIÓN DE COACH SOFÍA:\n'¡Liderazgo empático extraordinario! El Reencuadre PNL transformó el miedo en visión de protección patrimonial. La directiva aprobó $50,000 USD de presupuesto adicional.'"
            self.locked_decisions[4] = (c_text, r_text)
            if "🛡️ Escudo de Reencuadre PNL M4" not in self.inventory_items:
                self.inventory_items.append("🛡️ Escudo de Reencuadre PNL M4")
            self.decisions_log.append("M4: Usó Reencuadre PNL y 7 Hábitos.")
            res_lbl.configure(text=r_text, text_color="#00ffaa")
            self.after(2800, self.close_dialogue)

        self.setup_decision_options(
            parent,
            "Exigir la adopción inmediata del modelo digital mediante orden ejecutiva",
            choice_a,
            "Utilizar el Reencuadre PNL y la Rueda de 7 Hábitos para alinear a la directiva",
            choice_b
        )

    def decision_m5(self, parent):
        t = "Fundadores: 'Alexander, tenemos el prototipo listo. Para acumular el capital final necesario para los patrocinios deportivos, ¿cómo lanzamos?'"
        ctk.CTkLabel(parent, text=t, font=ctk.CTkFont(size=13, weight="bold"), text_color="#fff", wraplength=1000, justify="left").pack(anchor="w")

        res_lbl = ctk.CTkLabel(parent, text="", font=ctk.CTkFont(size=13, weight="bold"), wraplength=1000, justify="left")
        res_lbl.pack(anchor="w", pady=4)

        def choice_a():
            self.has_active_options = False
            self.update_metrics(-25, -20000)
            self.completed_modules[2] = True
            c_text = "A) Producir a escala masiva 500,000 unidades para reducir costos por economía de escala"
            r_text = "💬 REACCIÓN DE LOS FUNDADORES REALES:\n'¡Desastre de mercado! Producir 500,000 unidades a ciegas generó un sobrestock invendible. Pérdidas masivas de $20,000 USD. Limusina de Destino Final Lista.'"
            self.locked_decisions[5] = (c_text, r_text)
            self.decisions_log.append("M5: Fabricó masivamente a ciegas.")
            res_lbl.configure(text=r_text, text_color="#ff007a")
            self.after(2800, self.close_dialogue)
            self.draw_current_map()

        def choice_b():
            self.has_active_options = False
            self.update_metrics(+25, +100000)
            self.completed_modules[2] = True
            c_text = "B) Lanzar un Producto Mínimo Viable (MVP EcoBox) y aplicar mejora continua Kaizen"
            r_text = "💬 REACCIÓN DE LOS FUNDADORES REALES:\n'¡Estrategia de Silicon Valley impecable! El Producto Mínimo Viable (MVP EcoBox) validó la demanda real y el bucle Kaizen multiplicó las ventas acumulando $100,000 USD. ¡Avanza al Autódromo!'"
            self.locked_decisions[5] = (c_text, r_text)
            if "📦 Prototipo MVP EcoBox M5" not in self.inventory_items:
                self.inventory_items.append("📦 Prototipo MVP EcoBox M5")
            self.decisions_log.append("M5: Lanzó MVP (EcoBox) con bucle Kaizen.")
            res_lbl.configure(text=r_text, text_color=self.COLOR_GOLD)
            self.after(2800, self.close_dialogue)
            self.draw_current_map()

        self.setup_decision_options(
            parent,
            "Producir a escala masiva 500,000 unidades para reducir costos por economía de escala",
            choice_a,
            "Lanzar un Producto Mínimo Viable (MVP EcoBox) y aplicar mejora continua Kaizen",
            choice_b
        )

    def dialogue_m6(self, parent):
        self.has_active_options = False
        t = f"Director de Escudería: ¡ALEXANDER! Gracias a las decisiones acumuladas en AlexTech (Viabilidad {self.company_score}%, Capital ${self.capital:,}), ¡NUESTRA ESCUDERÍA FIRMÓ EL PATROCINIO PRINCIPAL EN LA FÓRMULA 1 Y EN LA GT WORLD CHALLENGE!"
        ctk.CTkLabel(parent, text=t, font=ctk.CTkFont(size=13, weight="bold"), text_color="#fff", wraplength=1000, justify="left").pack(anchor="w")
        
        ctk.CTkButton(
            parent,
            text="✅ CONTINUAR Y REPRODUCIR VIDEO DE ÉXITO (BOTÓN A / ENTER)",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            fg_color="#103028",
            border_color="#00ffaa",
            border_width=2,
            text_color="#00ffaa",
            command=self.close_dialogue
        ).pack(pady=10)

    def dialogue_failure_job(self, parent):
        self.has_active_options = False
        t = f"Jefe de Contrata: 'Oye Alexander, deja de pensar en la Fórmula 1 y GT World Challenge. AlexTech quebró porque tus decisiones acumularon pérdidas (Viabilidad {self.company_score}%, Capital ${self.capital:,}). Ahora tienes que terminar tu turno de 12 horas en la calle reparando cables para pagar tus deudas.'"
        ctk.CTkLabel(parent, text=t, font=ctk.CTkFont(size=13, weight="bold"), text_color="#fff", wraplength=1000, justify="left").pack(anchor="w")
        
        ctk.CTkButton(
            parent,
            text="✅ CONTINUAR Y REPRODUCIR VIDEO DE FRACASO (BOTÓN A / ENTER)",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            fg_color="#3d1515",
            border_color="#ff007a",
            border_width=2,
            text_color="#ff007a",
            command=self.close_dialogue
        ).pack(pady=10)

    # DISTRACTOR HANDLERS WITH PERMANENT LOCK
    def dialogue_distractor_lucas(self, parent):
        t = "Compañero Lucas: '¡Oye Alexander! Olvídate de fundar AlexTech. Eso de la Fórmula 1 y GT World es un sueño difícil. Mejor ven a platicar y jugar videojuegos.'"
        ctk.CTkLabel(parent, text=t, font=ctk.CTkFont(size=13, weight="bold"), text_color="#fff", wraplength=1000, justify="left").pack(anchor="w")

        prof_warning = (
            "👩‍🏫 PROFESORA ESTEFANÍA FRANCO (Gritando desde el escritorio):\n"
            "¡ALEXANDER Y LUCAS! ¡DEJEN DE PLATICAR EN CLASE O LOS SACO A LOS DOS DEL SALÓN AHORA MISMO!"
        )
        ctk.CTkLabel(parent, text=prof_warning, font=ctk.CTkFont(size=13, weight="bold"), text_color="#ff007a", wraplength=1000, justify="left").pack(anchor="w", pady=4)

        res_lbl = ctk.CTkLabel(parent, text="", font=ctk.CTkFont(size=13, weight="bold"), wraplength=1000, justify="left")
        res_lbl.pack(anchor="w", pady=4)

        def choice_a():
            self.has_active_options = False
            self.update_metrics(-15, -1000)
            c_text = "A) Seguir platicando con Lucas e ignorar la advertencia de la profesora"
            r_text = "💬 REACCIÓN DE LA PROFESORA ESTEFANÍA FRANCO:\n'¡Se acabó! Los dos quedan sancionados por platicar en clase e ignorar mi advertencia (-15% Viabilidad). ¡Presten atención!'"
            self.locked_decisions[101] = (c_text, r_text)
            res_lbl.configure(text=r_text, text_color="#ff007a")
            self.after(2800, self.close_dialogue)

        def choice_b():
            self.has_active_options = False
            self.update_metrics(+10, 0)
            c_text = "B) Pedir disculpas a la Profesora Estefanía Franco y volver a poner atención"
            r_text = "💬 REACCIÓN DE LUCAS:\n'Tienes razón Alexander, mejor pidamos disculpas a la profesora Estefanía Franco y pongamos atención para no reprobar (+10% Viabilidad).'"
            self.locked_decisions[101] = (c_text, r_text)
            res_lbl.configure(text=r_text, text_color="#00ffaa")
            self.after(2800, self.close_dialogue)

        self.setup_decision_options(
            parent,
            "Seguir platicando con Lucas e ignorar la advertencia de la profesora",
            choice_a,
            "Pedir disculpas a la Profesora Estefanía Franco y volver a poner atención",
            choice_b
        )

    def dialogue_distractor_vendedor(self, parent):
        t = "Vendedor Urbano: '¡Oye joven! Dame tu dinero y te prometo multiplicarlo por 1,000 en un esquema financiero sin estudios ni tecnología.'"
        ctk.CTkLabel(parent, text=t, font=ctk.CTkFont(size=13, weight="bold"), text_color="#fff", wraplength=1000, justify="left").pack(anchor="w")

        res_lbl = ctk.CTkLabel(parent, text="", font=ctk.CTkFont(size=13, weight="bold"), wraplength=1000, justify="left")
        res_lbl.pack(anchor="w", pady=4)

        def choice_a():
            self.has_active_options = False
            self.update_metrics(-10, -4000)
            c_text = "A) Entregar $4,000 de capital esperando el retorno mágico"
            r_text = "💬 REACCIÓN DEL VENDEDOR:\n'¡Me quedo tus $4,000 USD! Caíste en una estafa urbana por falta de pensamiento crítico.'"
            self.locked_decisions[102] = (c_text, r_text)
            res_lbl.configure(text=r_text, text_color="#ff007a")
            self.after(2200, self.close_dialogue)

        def choice_b():
            self.has_active_options = False
            self.update_metrics(+10, +5000)
            c_text = "B) Desconfiar y priorizar la inversión en la empresa AlexTech"
            r_text = "💬 REACCIÓN DEL VENDEDOR:\n'Maldición... tienes buen ojo crítico. Sabes proteger el patrimonio de AlexTech.'"
            self.locked_decisions[102] = (c_text, r_text)
            res_lbl.configure(text=r_text, text_color="#00ffaa")
            self.after(2200, self.close_dialogue)

        self.setup_decision_options(
            parent,
            "Entregar $4,000 de capital esperando el retorno mágico",
            choice_a,
            "Desconfiar y priorizar la inversión en la empresa AlexTech",
            choice_b
        )

    def dialogue_distractor_ramiro(self, parent):
        t = "Don Ramiro: 'Alexander, patrocinar la Fórmula 1 y GT World Challenge es muy arriesgado. Congelemos los proyectos e inversiones.'"
        ctk.CTkLabel(parent, text=t, font=ctk.CTkFont(size=13, weight="bold"), text_color="#fff", wraplength=1000, justify="left").pack(anchor="w")

        res_lbl = ctk.CTkLabel(parent, text="", font=ctk.CTkFont(size=13, weight="bold"), wraplength=1000, justify="left")
        res_lbl.pack(anchor="w", pady=4)

        def choice_a():
            self.has_active_options = False
            self.update_metrics(-15, -2000)
            c_text = "A) Aceptar congelar los planes de expansión por temor al riesgo"
            r_text = "💬 REACCIÓN DE DON RAMIRO:\n'Así es mejor, nos quedamos estancados por miedo al fracaso (-15% Viabilidad).'"
            self.locked_decisions[103] = (c_text, r_text)
            res_lbl.configure(text=r_text, text_color="#ff007a")
            self.after(2200, self.close_dialogue)

        def choice_b():
            self.has_active_options = False
            self.update_metrics(+15, +10000)
            c_text = "B) Presentar proyecciones financieras para continuar innovando"
            r_text = "💬 REACCIÓN DE DON RAMIRO:\n'Me has demostrado con datos que la tecnología innovadora reduce riesgos. Continuemos.'"
            self.locked_decisions[103] = (c_text, r_text)
            res_lbl.configure(text=r_text, text_color="#00ffaa")
            self.after(2200, self.close_dialogue)

        self.setup_decision_options(
            parent,
            "Aceptar congelar los planes de expansión por temor al riesgo",
            choice_a,
            "Presentar proyecciones financieras para continuar innovando",
            choice_b
        )

    # MODALS FOR INVENTORY & REPORT
    def toggle_inventory(self):
        modal = ctk.CTkToplevel(self)
        modal.title("🎒 Mochila de Ítems de Innovación - Alexander")
        modal.geometry("540x420")
        modal.attributes("-topmost", True)
        modal.configure(fg_color="#0d1424")

        ctk.CTkLabel(modal, text="🎒 HERRAMIENTAS Y MATRICES RECOLECTADAS", font=ctk.CTkFont(size=15, weight="bold"), text_color=self.COLOR_CYAN).pack(pady=(16, 8))

        if not self.inventory_items:
            ctk.CTkLabel(modal, text="Tu mochila está vacía. Toma decisiones estratégicas con los Mentores para recolectar herramientas.", font=ctk.CTkFont(size=12), text_color="#8e9bb4", wraplength=440).pack(pady=40)
        else:
            list_frame = ctk.CTkFrame(modal, fg_color="transparent")
            list_frame.pack(fill="both", expand=True, padx=20, pady=10)

            for item in self.inventory_items:
                item_box = ctk.CTkFrame(list_frame, fg_color="#18233c", border_color=self.COLOR_CYAN, border_width=1, corner_radius=10)
                item_box.pack(fill="x", pady=5)
                ctk.CTkLabel(item_box, text=item, font=ctk.CTkFont(size=13, weight="bold"), text_color="#ffffff").pack(anchor="w", padx=15, pady=10)

        ctk.CTkButton(modal, text="Cerrar Mochila", fg_color=self.COLOR_CYAN, text_color="#000", font=ctk.CTkFont(weight="bold"), command=modal.destroy).pack(pady=12)

    def toggle_professor_report(self):
        modal = ctk.CTkToplevel(self)
        modal.title("📊 Certificado de Evaluación Ejecutiva para el Profesor")
        modal.geometry("680x620")
        modal.attributes("-topmost", True)
        modal.configure(fg_color="#090f1d")

        ctk.CTkLabel(modal, text="🎓 CERTIFICADO DE EVALUACIÓN DE INNOVACIÓN", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.COLOR_GOLD).pack(pady=(16, 4))
        ctk.CTkLabel(modal, text="Informe de Desempeño Académico del Desarrollador Armando Misael Mata Hernández", font=ctk.CTkFont(size=12), text_color="#8e9bb4").pack(pady=(0, 12))

        report_card = ctk.CTkFrame(modal, fg_color="#121a2d", border_color=self.COLOR_CYAN, border_width=1, corner_radius=14)
        report_card.pack(fill="both", expand=True, padx=20, pady=5)

        log_str = "\n".join([f"  • {log}" for log in self.decisions_log]) if self.decisions_log else "  • No se han tomado decisiones aún."

        if self.company_score >= 65 and self.capital >= 60000:
            status_text = "🏆 DESENLACE 1: PATROCINADOR OFICIAL DE FÓRMULA 1 Y GT WORLD CHALLENGE"
        elif self.company_score < 45 or self.capital <= 5000:
            status_text = "❌ DESENLACE 2: FRACASO TOTAL — EMPLEO SECUNDARIO NO DESEADO EN LA CALLE"
        else:
            status_text = "⚖️ DESENLACE 3: TALLER LOCAL PEQUEÑO (SIN PATROCINIO F1/GT WORLD)"

        r_text = (
            f"• CREADOR Y DESARROLLADOR: ARMANDO MISAEL MATA HERNÁNDEZ\n"
            f"• Protagonista del Juego: Alexander (Estudiante de TI)\n"
            f"• Empresa Fundada: AlexTech Headquarters\n"
            f"• Meta Inicial: Patrocinar la Fórmula 1 & GT World Challenge\n"
            f"• Puntuación de Viabilidad Global: {self.company_score}%\n"
            f"• Capital Acumulado: ${self.capital:,} USD\n\n"
            f"--------------------------------------------------\n"
            f"HISTORIAL DE DECISIONES TOMADAS POR EL JUGADOR:\n"
            f"{log_str}\n\n"
            f"ESTATUS DEL DESENLACE FINAL:\n"
            f"{status_text}"
        )

        ctk.CTkLabel(report_card, text=r_text, font=ctk.CTkFont(family="Consolas", size=10), text_color="#ffffff", justify="left").pack(padx=20, pady=15)

        ctk.CTkButton(modal, text="Cerrar Reporte", fg_color=self.COLOR_GOLD, text_color="#000", font=ctk.CTkFont(weight="bold"), command=modal.destroy).pack(pady=12)


if __name__ == "__main__":
    app = PokemonGBAPermanentDecisionEngine()
    app.mainloop()
