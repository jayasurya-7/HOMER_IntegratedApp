# import tkinter as tk
# from tkinter import messagebox
# import subprocess
# import os

# # Game Paths
# GAME1_PATH = r"C:\HOMER_PLUTO\PLUTO.exe"
# GAME2_PATH = r"D:\HOMER_MARS\MARS.exe"

# def launch_game(path):
#     if os.path.exists(path):
#         subprocess.Popen([path])
#         root.destroy()
#     else:
#         messagebox.showerror("Error", f"Game not found:\n{path}")

# root = tk.Tk()
# root.title("Game Launcher")
# root.attributes("-fullscreen", True)
# root.protocol("WM_DELETE_WINDOW", lambda: None)

# # === Load images ===
# pluto_img = tk.PhotoImage(file=r"D:\mobbo1\New NRS\Homer7\plutoBg.png")
# mars_img = tk.PhotoImage(file=r"D:\mobbo1\New NRS\Homer7\marsBg.png")

# # === Configure grid ===
# root.grid_rowconfigure(0, weight=1)
# root.grid_columnconfigure(0, weight=1)
# root.grid_columnconfigure(1, weight=1)

# # === Create canvases ===
# canvas1 = tk.Canvas(root, highlightthickness=0, bd=0)
# canvas2 = tk.Canvas(root, highlightthickness=0, bd=0)
# canvas1.grid(row=0, column=0, sticky="nsew")
# canvas2.grid(row=0, column=1, sticky="nsew")

# canvas1_img = canvas1.create_image(0, 0, image=pluto_img, anchor="nw")
# canvas2_img = canvas2.create_image(0, 0, image=mars_img, anchor="nw")


# def rgb(r, g, b):
#     return f"#{r:02x}{g:02x}{b:02x}"

# pluto_text = canvas1.create_text(0, 0, text="PLUTO", font=("Arial", 90, "bold"), fill=rgb(255, 142, 85))
# mars_text  = canvas2.create_text(0, 0, text="MARS",  font=("Arial", 90, "bold"), fill=rgb(36, 106, 73))

# # # Add text placeholders
# # pluto_text = canvas1.create_text(0, 0, text="PLUTO", font=("Arial", 90, "bold"), fill="orange")
# # mars_text = canvas2.create_text(0, 0, text="MARS", font=("Arial", 90, "bold"), fill="green")

# # keep text in centre of the screen
# def resize(event):
#     w1 = canvas1.winfo_width()
#     h1 = canvas1.winfo_height()
#     w2 = canvas2.winfo_width()
#     h2 = canvas2.winfo_height()
#     # Center the text horizontally, place near bottom vertically
#     canvas1.coords(pluto_text, w1/2, h1*0.5)
#     canvas2.coords(mars_text, w2/2, h2*0.5)

# canvas1.bind("<Configure>", resize)
# canvas2.bind("<Configure>", resize)

# # click buttons
# canvas1.bind("<Button-1>", lambda e: launch_game(GAME1_PATH))
# canvas2.bind("<Button-1>", lambda e: launch_game(GAME2_PATH))

# root.mainloop()




import tkinter as tk
from tkinter import messagebox
import subprocess
import os, sys

# === Utility for PyInstaller path handling ===
def resource_path(relative_path):
    """Get absolute path to resource (works for .exe or .py)"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# === Game paths (keep absolute if external .exe) ===
GAME1_PATH = r"C:\HOMER_PLUTO\PLUTO.exe"
GAME2_PATH = r"C:\HOMER_MARS\MARS.exe"

def launch_game(path):
    if os.path.exists(path):
        subprocess.Popen([path])
        root.destroy()
    else:
        messagebox.showerror("Error", f"Game not found:\n{path}")

root = tk.Tk()
root.title("Game Launcher")
root.attributes("-fullscreen", True)
root.protocol("WM_DELETE_WINDOW", lambda: None)

# === Load images (works in .exe too) ===
pluto_img = tk.PhotoImage(file=resource_path("plutoBg.png"))
mars_img  = tk.PhotoImage(file=resource_path("marsBg.png"))

# === Grid setup ===
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

canvas1 = tk.Canvas(root, highlightthickness=0, bd=0)
canvas2 = tk.Canvas(root, highlightthickness=0, bd=0)
canvas1.grid(row=0, column=0, sticky="nsew")
canvas2.grid(row=0, column=1, sticky="nsew")

canvas1_img = canvas1.create_image(0, 0, image=pluto_img, anchor="nw")
canvas2_img = canvas2.create_image(0, 0, image=mars_img, anchor="nw")

def rgb(r, g, b):
    return f"#{r:02x}{g:02x}{b:02x}"

pluto_text = canvas1.create_text(0, 0, text="PLUTO", font=("Arial", 90, "bold"), fill=rgb(255, 142, 85))
mars_text  = canvas2.create_text(0, 0, text="MARS",  font=("Arial", 90, "bold"), fill=rgb(36, 106, 73))

def resize(event):
    w1 = canvas1.winfo_width()
    h1 = canvas1.winfo_height()
    w2 = canvas2.winfo_width()
    h2 = canvas2.winfo_height()
    canvas1.coords(pluto_text, w1/2, h1/2)
    canvas2.coords(mars_text, w2/2, h2/2)

canvas1.bind("<Configure>", resize)
canvas2.bind("<Configure>", resize)

canvas1.bind("<Button-1>", lambda e: launch_game(GAME1_PATH))
canvas2.bind("<Button-1>", lambda e: launch_game(GAME2_PATH))

root.mainloop()
