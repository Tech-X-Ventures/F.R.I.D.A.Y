"""
FRYDAY Boot Sequence — Iron Man "Daddy's Home" style.
Displays a fullscreen HUD overlay that types out system boot lines,
then hands off to the main app for a short greeting. Saved memories are not
treated as pending tasks or read aloud automatically.
"""
import threading
import tkinter as tk
from datetime import datetime
from typing import Callable, List


# ── Boot lines that scroll in one-by-one ──────────────────────────────────────
BOOT_LINES = [
    ("//", "FRYDAY ADVANCED TACTICAL INTERFACE"),
    (">>", "LOADING KERNEL MODULES              "),
    (">>", "INITIALIZING NEURAL CORE            "),
    (">>", "VOICE ENGINE          [ ONLINE ]    "),
    (">>", "MEMORY SYSTEMS        [ ONLINE ]    "),
    (">>", "SYSTEM CONTROL        [ ONLINE ]    "),
    (">>", "THREAT ANALYSIS       [ STANDBY ]   "),
    (">>", "ALL SYSTEMS NOMINAL                 "),
    ("//", "WELCOME BACK, SIR.                  "),
]

# Timing (ms)
LINE_DELAY   = 280   # gap between lines appearing
CHAR_DELAY   = 18    # typewriter speed per character
HOLD_AFTER   = 900   # pause after last line before closing


class BootSequenceOverlay(tk.Toplevel):
    """
    Full-screen boot overlay drawn on top of the main window.
    Calls `on_complete()` when the animation finishes.
    """

    def __init__(self, master: tk.Misc, on_complete: Callable):
        super().__init__(master)
        self.on_complete = on_complete
        self._destroyed = False

        # ── Window setup ──────────────────────────────────────────────────────
        self.overrideredirect(True)          # no title bar
        self.attributes("-topmost", True)
        self.configure(bg="#020912")

        # Cover the whole screen
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{sw}x{sh}+0+0")

        self._build_ui(sw, sh)
        self.after(400, self._start_sequence)

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self, sw: int, sh: int):
        # Scanline-style top label
        tk.Label(
            self, text="FRYDAY  //  BOOT SEQUENCE v3.1",
            font=("Consolas", 14, "bold"),
            fg="#00e5ff", bg="#020912"
        ).place(x=60, y=40)

        # Live clock
        self._clock_var = tk.StringVar()
        tk.Label(
            self, textvariable=self._clock_var,
            font=("Consolas", 12), fg="#0088ff", bg="#020912"
        ).place(x=sw - 260, y=40)
        self._tick_clock()

        # Main boot log canvas (left half)
        self._log_frame = tk.Frame(self, bg="#020912")
        self._log_frame.place(x=60, y=120, width=sw // 2 - 80)

        self._line_labels: List[tk.Label] = []

        # Horizontal separator
        tk.Frame(self, bg="#0d2a40", height=2).place(
            x=0, y=sh - 80, relwidth=1.0
        )

        # Bottom status bar
        self._status_var = tk.StringVar(value="INITIALIZING...")
        tk.Label(
            self, textvariable=self._status_var,
            font=("Consolas", 11), fg="#38ef7d", bg="#020912"
        ).place(x=60, y=sh - 55)

        # Arc / pulse indicator (simple animated dot)
        self._pulse_canvas = tk.Canvas(
            self, width=180, height=180, bg="#020912", highlightthickness=0
        )
        self._pulse_canvas.place(x=sw // 2 + 60, y=sh // 2 - 200)
        self._pulse_r   = 30
        self._pulse_dir = 1
        self._draw_pulse()

    # ── Clock ─────────────────────────────────────────────────────────────────
    def _tick_clock(self):
        if self._destroyed:
            return
        self._clock_var.set(datetime.now().strftime("%A  %d %b %Y   %H:%M:%S"))
        self.after(500, self._tick_clock)

    # ── Pulse ring animation ───────────────────────────────────────────────────
    def _draw_pulse(self):
        if self._destroyed:
            return
        c = self._pulse_canvas
        c.delete("all")
        cx, cy = 90, 90
        r = self._pulse_r
        # Outer glow
        c.create_oval(cx-r-12, cy-r-12, cx+r+12, cy+r+12,
                      outline="#0d2540", width=2)
        # Main ring
        c.create_oval(cx-r, cy-r, cx+r, cy+r,
                      outline="#00e5ff", width=3)
        # Core
        c.create_oval(cx-14, cy-14, cx+14, cy+14,
                      outline="#ffffff", fill="#00e5ff", width=2)
        # Crosshairs
        c.create_line(cx, cy-r-16, cx, cy-r-6, fill="#0088ff", width=2)
        c.create_line(cx, cy+r+6,  cx, cy+r+16, fill="#0088ff", width=2)
        c.create_line(cx-r-16, cy, cx-r-6, cy,  fill="#0088ff", width=2)
        c.create_line(cx+r+6,  cy, cx+r+16, cy, fill="#0088ff", width=2)

        # Breathe
        self._pulse_r += 0.4 * self._pulse_dir
        if self._pulse_r > 45:
            self._pulse_dir = -1
        elif self._pulse_r < 22:
            self._pulse_dir = 1
        self.after(30, self._draw_pulse)

    # ── Boot sequence logic ───────────────────────────────────────────────────
    def _start_sequence(self):
        self._seq_index = 0
        self._show_next_line()

    def _show_next_line(self):
        if self._destroyed:
            return
        if self._seq_index >= len(BOOT_LINES):
            # All lines done — hold then finish
            self._status_var.set("ALL SYSTEMS ONLINE  ✔")
            self.after(HOLD_AFTER, self._finish)
            return

        prefix, text = BOOT_LINES[self._seq_index]

        # Color by prefix
        color = "#00e5ff" if prefix == "//" else "#a0c8e8"
        if "ONLINE" in text:
            color = "#38ef7d"
        if "STANDBY" in text:
            color = "#f0a500"

        lbl = tk.Label(
            self._log_frame,
            text="",
            font=("Consolas", 13),
            fg=color, bg="#020912",
            anchor="w"
        )
        lbl.pack(anchor="w", pady=2)
        self._line_labels.append(lbl)

        full_text = f"  {prefix}  {text}"
        self._typewrite(lbl, full_text, 0)

        self._seq_index += 1
        self.after(LINE_DELAY, self._show_next_line)

    def _typewrite(self, label: tk.Label, text: str, index: int):
        if self._destroyed:
            return
        if index <= len(text):
            label.config(text=text[:index] + ("█" if index < len(text) else ""))
            self.after(CHAR_DELAY, lambda: self._typewrite(label, text, index + 1))

    def _finish(self):
        if self._destroyed:
            return
        self._destroyed = True
        try:
            self.destroy()
        except Exception:
            pass
        self.on_complete()

