
import tkinter as tk
from tkinter import messagebox
import subprocess
import os, sys
from datetime import datetime
from PIL import Image, ImageTk

# === Config file for password ===
CONFIG_FILE = r"C:\DeviceSetups\config.ini"

def get_password():
    """Get stored password from config file"""
    print(f"[DEBUG] Looking for config at: {CONFIG_FILE}")
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                pwd = f.read().strip()
                print(f"[DEBUG] Password found in config file")
                return pwd
        except Exception as e:
            print(f"[ERROR] Failed to read config: {e}")
            return None
    print(f"[DEBUG] Config file not found")
    return None

def save_password(password):
    """Save password to config file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            f.write(password)
        print(f"[DEBUG] Password saved to: {CONFIG_FILE}")
    except Exception as e:
        print(f"[ERROR] Failed to save password: {e}")
        messagebox.showerror("Error", f"Failed to save password:\n{e}")

def ask_password():
    """Ask for password dialog - professional centered design"""
    dialog = tk.Toplevel(root)
    dialog.title("Security Check")
    dialog.transient(root)
    dialog.grab_set()
    dialog.resizable(False, False)
    
    # Get screen dimensions and center the dialog
    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()
    dialog_width = 420
    dialog_height = 220
    x = (screen_width - dialog_width) // 2
    y = (screen_height - dialog_height) // 2
    dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    # Modern color scheme
    BG_COLOR = "#1a1a2e"
    FG_COLOR = "#ffffff"
    ACCENT_COLOR = "#16213e"
    BUTTON_COLOR = "#0f3460"
    BUTTON_HOVER = "#e94560"
    
    dialog.configure(bg=BG_COLOR)
    
    # Header
    header_frame = tk.Frame(dialog, bg=BG_COLOR, height=60)
    header_frame.pack(fill=tk.X, pady=(20, 10))
    header_frame.pack_propagate(False)
    
    # Lock icon (using text)
    lock_label = tk.Label(
        header_frame, 
        text="🔒", 
        font=("Segoe UI", 28),
        bg=BG_COLOR,
        fg=FG_COLOR
    )
    lock_label.pack(side=tk.LEFT, padx=(30, 15))
    
    # Title
    title_label = tk.Label(
        header_frame,
        text="Authentication Required",
        font=("Segoe UI", 16, "bold"),
        bg=BG_COLOR,
        fg=FG_COLOR
    )
    title_label.pack(side=tk.LEFT)
    
    # Subtitle
    subtitle = tk.Label(
        dialog,
        text="Enter your password to continue",
        font=("Segoe UI", 10),
        bg=BG_COLOR,
        fg="#888888"
    )
    subtitle.pack(pady=(0, 15))
    
    # Entry frame
    entry_frame = tk.Frame(dialog, bg=BG_COLOR)
    entry_frame.pack(pady=10)
    
    entry = tk.Entry(
        entry_frame, 
        show="●", 
        font=("Segoe UI", 14),
        width=25,
        bd=0,
        bg=ACCENT_COLOR,
        fg=FG_COLOR,
        insertbackground=FG_COLOR,
        highlightthickness=2,
        highlightcolor=BUTTON_HOVER,
        highlightbackground=ACCENT_COLOR
    )
    entry.pack(pady=5, ipady=8)
    entry.focus()
    
    result = [False]
    
    def check_password():
        pwd = entry.get()
        if pwd == "BIOREHAB":
            save_password(pwd)
            result[0] = True
            dialog.destroy()
        else:
            entry.delete(0, tk.END)
            entry.configure(highlightcolor="#ff0000")
            entry.focus()
    
    def cancel():
        dialog.destroy()
    
    # Button frame
    btn_frame = tk.Frame(dialog, bg=BG_COLOR)
    btn_frame.pack(pady=20)
    
    # Styled buttons
    def create_button(text, command, is_primary=True):
        btn = tk.Button(
            btn_frame,
            text=text,
            command=command,
            font=("Segoe UI", 11, "bold"),
            width=12,
            bd=0,
            bg=BUTTON_HOVER if is_primary else ACCENT_COLOR,
            fg=FG_COLOR,
            activebackground="#ff6b6b" if is_primary else BUTTON_COLOR,
            activeforeground=FG_COLOR,
            cursor="hand2",
            relief=tk.FLAT
        )
        return btn
    
    ok_btn = create_button("Unlock", check_password, True)
    ok_btn.pack(side=tk.LEFT, padx=10)
    
    cancel_btn = create_button("Cancel", cancel, False)
    cancel_btn.pack(side=tk.LEFT, padx=10)
    
    # Bind Enter key
    dialog.bind("<Return>", lambda e: check_password())
    dialog.bind("<Escape>", lambda e: cancel())
    
    root.wait_window(dialog)
    return result[0]

# === Utility for PyInstaller path handling ===
def resource_path(relative_path):
    """Get absolute path to resource (works for .exe or .py)"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# === Game paths (keep absolute if external .exe) ===
# Demo games (no authentication required)
DEMO_GAME1_PATH = r"C:\HOMER_DEMO_PLUTO\PLUTO.exe"
DEMO_GAME2_PATH = r"C:\HOMER_DEMO_MARS\MARS.exe"

# Real training games (authentication required)
GAME1_PATH = r"C:\HOMER_PLUTO\PLUTO.exe"
GAME2_PATH = r"C:\HOMER_MARS\MARS.exe"
MARS_SETUP = r"C:\DeviceSetups\Mars\uploadStatus.txt"
PLUTO_SETUP = r"C:\DeviceSetups\Pluto\uploadStatus.txt"

# Demo completion flag files
MARS_DEMO_DONE = r"C:\DeviceSetups\Mars\mars_demo_done.txt"
PLUTO_DEMO_DONE = r"C:\DeviceSetups\Pluto\pluto_demo_done.txt"

def is_demo_completed(flag_file):
    """Check if demo game has been completed (flag file exists)"""
    return os.path.exists(flag_file)

def is_training_completed(setup_file):
    """
    Check if training is completed (EndDate has passed).
    
    Args:
        setup_file: Path to uploadStatus.txt
    
    Returns:
        bool: True if training is completed, False otherwise
    """
    try:
        # Check if setup file exists
        if not os.path.exists(setup_file):
            return False
        
        # Read uploadStatus.txt and extract project path
        with open(setup_file, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
        
        if not first_line:
            return False
        
        project_path = first_line.split(',')[0].strip()
        if not project_path:
            return False
        
        # Construct configdata.csv path
        config_path = os.path.join(project_path, "data", "configdata.csv")
        
        if not os.path.exists(config_path):
            return False
        
        # Read last row of configdata.csv
        with open(config_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if not lines:
                return False
            last_row = lines[-1].strip()
        
        if not last_row:
            return False
        
        # Extract endDate (3rd column - index 2)
        try:
            end_date_str = last_row.split(',')[2].strip()
        except IndexError:
            return False
        
        if not end_date_str:
            return False
        
        # Parse date
        end_date = None
        date_formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%m/%d/%Y",
            "%Y/%m/%d",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%d-%m-%Y %H:%M:%S"
        ]
        
        for fmt in date_formats:
            try:
                end_date = datetime.strptime(end_date_str, fmt)
                break
            except ValueError:
                continue
        
        if end_date is None:
            return False
        
        # Check if training is completed (now > endDate)
        now = datetime.now()
        return now > end_date
    
    except Exception:
        return False



def show_animation_then_auth():
    """Show HOMER animation with premium healthcare-focused design"""
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # Animation screen with professional gradient background
    anim_frame = tk.Frame(root, bg="#0a1829")
    anim_frame.grid(row=0, column=0, sticky="nsew")

    # Create canvas for animation
    anim_canvas = tk.Canvas(
        anim_frame,
        bg="#0a1829",
        highlightthickness=0,
        bd=0
    )
    anim_canvas.pack(fill=tk.BOTH, expand=True)

    # Animation state
    anim_state = {
        "title_id": None,
        "tagline_id": None,
        "top_bar_id": None,
        "bottom_bar_id": None,
        "stage": "fade_in",
        "frame": 0
    }

    text = "HOMER"
    tagline = "Rehabilitation Training"
    fade_in_frames = 50
    hold_frames = 80
    fade_out_frames = 60

    # Professional healthcare colors
    PRIMARY_COLOR = "#00a8e8"  # Professional healthcare blue
    ACCENT_COLOR = "#00d9ff"   # Bright accent
    TEXT_COLOR = "#ffffff"     # White text

    def create_elements():
        """Create all animation elements"""
        w = anim_canvas.winfo_width()
        h = anim_canvas.winfo_height()

        # Top accent bar
        top_bar_id = anim_canvas.create_line(
            w/2 - 200, h/2 - 110,
            w/2 - 200, h/2 - 110,
            fill=PRIMARY_COLOR,
            width=3
        )

        # Bottom accent bar
        bottom_bar_id = anim_canvas.create_line(
            w/2 + 200, h/2 + 110,
            w/2 + 200, h/2 + 110,
            fill=PRIMARY_COLOR,
            width=3
        )

        # Main title
        title_id = anim_canvas.create_text(
            w/2, h/2 - 20,
            text=text,
            font=("Arial", 160, "bold"),
            fill=TEXT_COLOR,
            anchor="center"
        )

        # Tagline
        tagline_id = anim_canvas.create_text(
            w/2, h/2 + 90,
            text=tagline,
            font=("Arial", 18),
            fill=ACCENT_COLOR,
            anchor="center"
        )

        anim_state["title_id"] = title_id
        anim_state["tagline_id"] = tagline_id
        anim_state["top_bar_id"] = top_bar_id
        anim_state["bottom_bar_id"] = bottom_bar_id

    def fade_in_animate():
        """Fade in all elements with staggered timing"""
        frame = anim_state["frame"]
        progress = frame / fade_in_frames

        # Smooth easing
        eased = progress * progress * (3 - 2 * progress)
        opacity = int(255 * eased)

        # Fade in title
        title_color = f"#{opacity:02x}{opacity:02x}{opacity:02x}"
        anim_canvas.itemconfig(anim_state["title_id"], fill=title_color)

        # Fade in tagline
        tagline_opacity = int(255 * eased * 0.9)
        tagline_color = f"#{tagline_opacity:02x}{int(217 + (255-217)*eased):02x}{255:02x}"
        anim_canvas.itemconfig(anim_state["tagline_id"], fill=tagline_color)

        # Animate bars growing outward
        w = anim_canvas.winfo_width()
        h = anim_canvas.winfo_height()
        bar_width = 200 + (150 * eased)

        # Top bar - grows left
        anim_canvas.coords(
            anim_state["top_bar_id"],
            w/2 - bar_width, h/2 - 110,
            w/2 - 200, h/2 - 110
        )

        # Bottom bar - grows right
        anim_canvas.coords(
            anim_state["bottom_bar_id"],
            w/2 + 200, h/2 + 110,
            w/2 + bar_width, h/2 + 110
        )

        # Update bar color with opacity
        bar_color = f"#{int(0 * (1-eased) + opacity * eased):02x}{int(168 * eased):02x}{int(232 * eased):02x}"
        anim_canvas.itemconfig(anim_state["top_bar_id"], fill=bar_color)
        anim_canvas.itemconfig(anim_state["bottom_bar_id"], fill=bar_color)

        anim_state["frame"] += 1

        if anim_state["frame"] < fade_in_frames:
            root.after(16, fade_in_animate)
        else:
            # Fade in complete, hold
            anim_state["stage"] = "hold"
            anim_state["frame"] = 0
            root.after(800, hold_animate)

    def hold_animate():
        """Hold all elements at full opacity"""
        anim_state["frame"] += 1
        if anim_state["frame"] < hold_frames:
            root.after(16, hold_animate)
        else:
            # Start fade out
            anim_state["stage"] = "fade_out"
            anim_state["frame"] = 0
            fade_out_animate()

    def fade_out_animate():
        """Fade out all elements"""
        frame = anim_state["frame"]
        progress = frame / fade_out_frames

        # Smooth easing for fade out
        eased = progress * progress * (3 - 2 * progress)
        opacity = int(255 * (1 - eased))

        # Fade out title
        title_color = f"#{opacity:02x}{opacity:02x}{opacity:02x}"
        anim_canvas.itemconfig(anim_state["title_id"], fill=title_color)

        # Fade out tagline
        tagline_opacity = int(opacity * 0.9)
        tagline_color = f"#{tagline_opacity:02x}{int(217 * (1-eased)):02x}{int(255 * (1-eased)):02x}"
        anim_canvas.itemconfig(anim_state["tagline_id"], fill=tagline_color)

        # Bars shrink inward
        w = anim_canvas.winfo_width()
        h = anim_canvas.winfo_height()
        bar_width = 200 + (150 * (1 - eased))

        anim_canvas.coords(
            anim_state["top_bar_id"],
            w/2 - bar_width, h/2 - 110,
            w/2 - 200, h/2 - 110
        )

        anim_canvas.coords(
            anim_state["bottom_bar_id"],
            w/2 + 200, h/2 + 110,
            w/2 + bar_width, h/2 + 110
        )

        bar_color = f"#{int(opacity * 0.3):02x}{int(168 * (1-eased)):02x}{int(232 * (1-eased)):02x}"
        anim_canvas.itemconfig(anim_state["top_bar_id"], fill=bar_color)
        anim_canvas.itemconfig(anim_state["bottom_bar_id"], fill=bar_color)

        anim_state["frame"] += 1

        if anim_state["frame"] < fade_out_frames:
            root.after(16, fade_out_animate)
        else:
            # Fade out complete, show next screen
            root.after(200, show_demo_games)

    def on_canvas_configure(_):
        """Handle canvas resize and initial setup"""
        if anim_state["title_id"] is None:
            create_elements()
            root.after(300, fade_in_animate)

    anim_canvas.bind("<Configure>", on_canvas_configure)

def show_demo_games():
    """Show demo game selection (no authentication required)"""
    # Check if both demos are already completed
    if is_demo_completed(MARS_DEMO_DONE) and is_demo_completed(PLUTO_DEMO_DONE):
        show_auth_or_games()
        return

    # Clear animation
    for widget in root.winfo_children():
        widget.destroy()

    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # Colors
    BG_COLOR = "#1A1A30"
    ACCENT_DARK = "#1a1a3e"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#888888"
    PLUTO_COLOR = "#2bd887"
    MARS_COLOR = "#ff8e55"

    root.configure(bg=BG_COLOR)

    # Main container
    main_frame = tk.Frame(root, bg=BG_COLOR)
    main_frame.grid(row=0, column=0, sticky="nsew")

    # Header
    header = tk.Frame(main_frame, bg=ACCENT_DARK, height=100)
    header.pack(fill=tk.X)
    header.pack_propagate(False)

    robot_icon = tk.Label(
        header,
        text="🎮",
        font=("Segoe UI", 48),
        bg=ACCENT_DARK,
        fg="#00d9a5"
    )
    robot_icon.pack(side=tk.LEFT, padx=20, pady=10)

    header_label = tk.Label(
        header,
        text="Demo Mode - Try Before Training",
        font=("Segoe UI", 28, "bold"),
        bg=ACCENT_DARK,
        fg=TEXT_PRIMARY
    )
    header_label.pack(side=tk.LEFT, padx=10, pady=10)

    # Content area
    content = tk.Frame(main_frame, bg=BG_COLOR)
    content.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)

    # Card container
    cards_frame = tk.Frame(content, bg=BG_COLOR)
    cards_frame.pack(expand=True, anchor="center")

    # Load images (larger)
    try:
        pluto_pil = Image.open(resource_path("Pluto.png"))
        pluto_pil = pluto_pil.resize((200, 200), Image.Resampling.LANCZOS)
        pluto_img = ImageTk.PhotoImage(pluto_pil)

        mars_pil = Image.open(resource_path("Mars.png"))
        mars_pil = mars_pil.resize((200, 240), Image.Resampling.LANCZOS)
        mars_img = ImageTk.PhotoImage(mars_pil)
    except Exception as e:
        messagebox.showerror("Error", f"Could not load images: {e}")
        pluto_img = None
        mars_img = None

    def create_demo_card(parent, name, color, image, game_path, flag_file):
        """Create a professional demo game card with completion status"""
        is_completed = is_demo_completed(flag_file)

        card = tk.Frame(
            parent,
            bg=ACCENT_DARK,
            highlightthickness=2,
            highlightbackground=color,
            highlightcolor=color
        )
        card.pack(side=tk.LEFT, padx=30, ipadx=0, ipady=0, expand=True, fill=tk.BOTH)

        # Card size
        card.configure(width=450, height=520)
        card.pack_propagate(False)

        def on_enter(_):
            if not is_completed:
                card.configure(highlightthickness=4)

        def on_leave(_):
            card.configure(highlightthickness=2)

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

        inner = tk.Frame(card, bg=ACCENT_DARK)
        inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Image section
        if image:
            img_label = tk.Label(inner, image=image, bg=ACCENT_DARK)
            img_label.image = image
            img_label.pack(expand=False, pady=(0, 15))

        # Title
        title = tk.Label(
            inner,
            text=name,
            font=("Segoe UI", 36, "bold"),
            bg=ACCENT_DARK,
            fg=color
        )
        title.pack(expand=False, pady=(0, 5))

        # Subtitle
        if is_completed:
            subtitle = tk.Label(
                inner,
                text="✓ Demo Completed",
                font=("Segoe UI", 11, "bold"),
                bg=ACCENT_DARK,
                fg="#2bd887"
            )
        else:
            subtitle = tk.Label(
                inner,
                text="Try Before Training",
                font=("Segoe UI", 11),
                bg=ACCENT_DARK,
                fg="#00d9a5"
            )
        subtitle.pack(expand=False, pady=(0, 5))

        # Content section
        content_frame = tk.Frame(inner, bg=ACCENT_DARK)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

      
        # Button section (at bottom)
        btn_frame = tk.Frame(inner, bg=ACCENT_DARK)
        btn_frame.pack(expand=False, fill=tk.X, pady=(0, 0))

        btn_text = "✓ COMPLETED" if is_completed else "▶ LAUNCH DEMO"
        btn_bg = "#888888" if is_completed else color
        btn_fg = "#cccccc" if is_completed else "white"

        btn = tk.Button(
            btn_frame,
            text=btn_text,
            font=("Segoe UI", 13, "bold"),
            bg=btn_bg,
            fg=btn_fg,
            activebackground="#ffffff" if not is_completed else "#888888",
            activeforeground=color if not is_completed else "#cccccc",
            command=lambda:launch_game (game_path, name) if not is_completed else None,
            bd=0,
            highlightthickness=0,
            cursor="hand2" if not is_completed else "arrow",
            width=18,
            padx=15,
            pady=8,
            state=tk.DISABLED if is_completed else tk.NORMAL
        )
        btn.pack()

        if not is_completed:
            card.bind("<Button-1>", lambda _: launch_game(game_path, name))
            inner.bind("<Button-1>", lambda _: launch_game(game_path, name))

    # Create demo cards
    create_demo_card(cards_frame, "PLUTO", PLUTO_COLOR, pluto_img, DEMO_GAME1_PATH, PLUTO_DEMO_DONE)
    create_demo_card(cards_frame, "MARS", MARS_COLOR, mars_img, DEMO_GAME2_PATH, MARS_DEMO_DONE)





def launch_game(path, _):
    """Launch game - close for training, wait for demo"""
    if os.path.exists(path):
        import threading

        process = subprocess.Popen([path])

        # Check if this is a training game (not demo)
        is_training_game = (path == GAME1_PATH or path == GAME2_PATH)

        print(f"[DEBUG] Game path: {path}")
        print(f"[DEBUG] GAME1_PATH: {GAME1_PATH}")
        print(f"[DEBUG] GAME2_PATH: {GAME2_PATH}")
        print(f"[DEBUG] Is training game: {is_training_game}")

        if is_training_game:
            # For training games, close the launcher immediately
            print("[DEBUG] Training game launched, closing launcher")
            root.destroy()
            sys.exit()
        else:
            # For demo games, wait for game to close
            def wait_for_game_close():
                """Wait for game to close, then check if both demos are done"""
                import time
                process.wait()
                time.sleep(2)  # Wait 2 seconds for flag files to be written

                # Game closed, check if both demos are completed
                mars_demo_done = is_demo_completed(MARS_DEMO_DONE)
                pluto_demo_done = is_demo_completed(PLUTO_DEMO_DONE)

                print(f"[DEBUG] Game closed. Mars done: {mars_demo_done}, Pluto done: {pluto_demo_done}")
                print(f"[DEBUG] Mars flag file: {MARS_DEMO_DONE}")
                print(f"[DEBUG] Pluto flag file: {PLUTO_DEMO_DONE}")

                if mars_demo_done and pluto_demo_done:
                    # Both demos completed, shutdown system immediately
                    print("[DEBUG] Both demos completed, shutting down system immediately")
                    shutdown_system(delay=0)
                else:
                    # One or both demos not complete, go back to demo screen
                    print("[DEBUG] Not all demos completed, returning to demo screen")
                    root.after(100, show_demo_games)

            # Launch in background thread so UI stays responsive
            threading.Thread(target=wait_for_game_close, daemon=True).start()
    else:
        messagebox.showerror("Error", f"Game not found:\n{path}")


def show_auth_or_games():
    """Show authentication, then game selection"""
    # Create new root if needed
    global root
    if not root.winfo_exists():
        root = tk.Tk()
        root.title("HOMER Training System")
        root.attributes("-fullscreen", True)
        root.protocol("WM_DELETE_WINDOW", lambda: None)

    # Clear any existing widgets
    for widget in root.winfo_children():
        widget.destroy()

    # Check password on first time
    if not get_password():
        if not ask_password():
            root.destroy()
            sys.exit()

    # Show game selection screen
    show_game_selection()

def show_game_selection():
    """Show professional game selection UI with image icons"""
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    
    # Colors
    BG_COLOR = "#0f0f23"
    ACCENT_DARK = "#1a1a3e"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#888888"
    PLUTO_COLOR = "#2bd887"
    MARS_COLOR = "#ff8e55"
    
    root.configure(bg=BG_COLOR)
    
    # Main container
    main_frame = tk.Frame(root, bg=BG_COLOR)
    main_frame.grid(row=0, column=0, sticky="nsew")
    
    # Header with robot icon
    header = tk.Frame(main_frame, bg=ACCENT_DARK, height=100)
    header.pack(fill=tk.X)
    header.pack_propagate(False)
    
    # Robot icon in header
    robot_icon = tk.Label(
        header,
        text="🤖",
        font=("Segoe UI", 48),
        bg=ACCENT_DARK,
        fg="#00d9a5"
    )
    robot_icon.pack(side=tk.LEFT, padx=20, pady=10)
    
    header_label = tk.Label(
        header,
        text="HOMER Training System",
        font=("Segoe UI", 28, "bold"),
        bg=ACCENT_DARK,
        fg=TEXT_PRIMARY
    )
    header_label.pack(side=tk.LEFT, padx=10, pady=10)
    
    # Content area
    content = tk.Frame(main_frame, bg=BG_COLOR)
    content.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
    
    # Card container
    cards_frame = tk.Frame(content, bg=BG_COLOR)
    cards_frame.pack(expand=True, anchor="center")
    
    # Load and resize images
    try:
        # Load and resize Pluto image (larger)
        pluto_pil = Image.open(resource_path("Pluto.png"))
        pluto_pil = pluto_pil.resize((200, 240), Image.Resampling.LANCZOS)
        pluto_img = ImageTk.PhotoImage(pluto_pil)

        # Load and resize Mars image (larger)
        mars_pil = Image.open(resource_path("Mars.png"))
        mars_pil = mars_pil.resize((200, 240), Image.Resampling.LANCZOS)
        mars_img = ImageTk.PhotoImage(mars_pil)
    except Exception as e:
        messagebox.showerror("Error", f"Could not load images: {e}")
        pluto_img = None
        mars_img = None
    
    def create_game_card(parent, name, color, image, command):
        """Create a professional training game selection card"""
        card = tk.Frame(
            parent,
            bg=ACCENT_DARK,
            highlightthickness=2,
            highlightbackground=color,
            highlightcolor=color
        )
        card.pack(side=tk.LEFT, padx=30, ipadx=0, ipady=0, expand=True, fill=tk.BOTH)

        # Card size
        card.configure(width=450, height=520)
        card.pack_propagate(False)

        # Hover effect
        def on_enter(_):
            card.configure(highlightthickness=4)

        def on_leave(_):
            card.configure(highlightthickness=2)

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

        # Content
        inner = tk.Frame(card, bg=ACCENT_DARK)
        inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Image section (no frame)
        if image:
            img_label = tk.Label(
                inner,
                image=image,
                bg=ACCENT_DARK
            )
            img_label.image = image
            img_label.pack(expand=False, pady=(0, 15))

        # Title
        title = tk.Label(
            inner,
            text=name,
            font=("Segoe UI", 36, "bold"),
            bg=ACCENT_DARK,
            fg=color
        )
        title.pack(expand=False, pady=(0, 5))

        # Subtitle
        subtitle = tk.Label(
            inner,
            text="Advanced Training Module",
            font=("Segoe UI", 11),
            bg=ACCENT_DARK,
            fg="#00d9a5"
        )
        subtitle.pack(expand=False, pady=(0, 5))

        # Content section
        content_frame = tk.Frame(inner, bg=ACCENT_DARK)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

      
        # Button section (at bottom)
        btn_frame = tk.Frame(inner, bg=ACCENT_DARK)
        btn_frame.pack(expand=False, fill=tk.X, pady=(0, 0))

        btn = tk.Button(
            btn_frame,
            text="▶ START TRAINING",
            font=("Segoe UI", 13, "bold"),
            bg=color,
            fg="white",
            activebackground="#ffffff",
            activeforeground=color,
            command=command,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            width=18,
            padx=15,
            pady=8
        )
        btn.pack()

        # Make entire card clickable
        card.bind("<Button-1>", lambda _: command())
        inner.bind("<Button-1>", lambda _: command())
    
    # Create cards
    create_game_card(
        cards_frame,
        "PLUTO",
        PLUTO_COLOR,
        pluto_img,
        lambda: launch_game(GAME1_PATH, "Pluto")
    )
    
    create_game_card(
        cards_frame,
        "MARS",
        MARS_COLOR,
        mars_img,
        lambda: launch_game(GAME2_PATH, "Mars")
    )

root = tk.Tk()
root.title("HOMER Training System")
root.attributes("-fullscreen", True)
root.protocol("WM_DELETE_WINDOW", lambda: None)

# Disable window controls (minimize, maximize, close button)
root.attributes("-toolwindow", False)
root.resizable(False, False)

# Magic button: Shift+Escape to close application
def magic_close(event=None):
    """Secret button to close application"""
    root.destroy()
    sys.exit()

root.bind("<Shift-Escape>", magic_close)

# === Check if training is completed for both devices ===
mars_completed = is_training_completed(MARS_SETUP)
pluto_completed = is_training_completed(PLUTO_SETUP)
both_completed = mars_completed and pluto_completed


def shutdown_system(delay=0):
    """Shutdown system with optional delay (in seconds)"""
    print(f"[DEBUG] System will shutdown in {delay} seconds...")
    import time
    time.sleep(delay)
    os.system(f"shutdown /s /t 0")
    root.destroy()
    sys.exit()
   
    
# === If training is completed for both, show completion message with shutdown ===
if both_completed:
    # Professional completion screen
    COMP_BG = "#0f0f23"
    COMP_ACCENT = "#1a1a3e"
    COMP_TEXT = "#ffffff"
    COMP_GREEN = "#00d9a5"
    
    root.configure(bg=COMP_BG)
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    
    # Center frame
    center_frame = tk.Frame(root, bg=COMP_BG)
    center_frame.place(relx=0.5, rely=0.5, anchor="center")
    
    # Checkmark icon
    checkmark = tk.Label(
        center_frame,
        text="✓",
        font=("Segoe UI", 80),
        bg=COMP_BG,
        fg=COMP_GREEN
    )
    checkmark.pack(pady=(0, 20))
    
    # Title
    title = tk.Label(
        center_frame,
        text="TRAINING COMPLETED",
        font=("Segoe UI", 42, "bold"),
        bg=COMP_BG,
        fg=COMP_TEXT
    )
    title.pack(pady=(0, 10))
    
    # Subtitle
    subtitle = tk.Label(
        center_frame,
        text="All training sessions have been completed successfully",
        font=("Segoe UI", 14),
        bg=COMP_BG,
        fg="#888888"
    )
    subtitle.pack(pady=(0, 40))
    
    # Shutdown button
    shutdown_btn = tk.Button(
        center_frame, 
        text="⏻  Shutdown", 
        font=("Segoe UI", 14, "bold"),
        bg="#e94560",
        fg="white",
        activebackground="#ff6b6b",
        activeforeground="white",
        command=shutdown_system,
        bd=0,
        highlightthickness=0,
        cursor="hand2",
        width=18,
        height=1
    )
    shutdown_btn.pack(pady=10)
    # shutdown_system(delay=10)  # Auto shutdown after 30 seconds
else:
    # Start with animation
    show_animation_then_auth()

root.mainloop()
