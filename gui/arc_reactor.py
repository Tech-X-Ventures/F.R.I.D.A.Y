import math
import tkinter as tk
from typing import Optional

class ArcReactorCanvas(tk.Canvas):
    """
    Animated Holographic Arc Reactor widget with rotating segments,
    pulsing core, and real-time state feedback (IDLE, LISTENING, ANALYZING, SPEAKING).
    """
    def __init__(self, master, size: int = 240, bg_color: str = "#0b111e", **kwargs):
        super().__init__(master, width=size, height=size, bg=bg_color, highlightthickness=0, **kwargs)
        self.size = size
        self.center = size / 2
        self.angle_outer = 0.0
        self.angle_inner = 0.0
        self.pulse_val = 0.0
        self.pulse_dir = 1
        self.state = "IDLE"
        self.audio_level = 0.0

        # Futuristic sci-fi color palette
        self.COLOR_CORE = "#00e5ff"
        self.COLOR_GLOW = "#0088ff"
        self.COLOR_RING = "#103254"
        self.COLOR_ACTIVE = "#00ffd5"
        self.COLOR_WARN = "#ff3366"

        self._running = True
        self._animate()

    def set_state(self, state: str):
        self.state = state

    def set_audio_level(self, level: float):
        self.audio_level = max(0.0, min(1.0, level))

    def _animate(self):
        if not self._running:
            return

        self.delete("all")
        cx, cy = self.center, self.center

        # Determine rotation speeds and colors based on state
        if self.state == "LISTENING":
            speed_outer = 3.5
            speed_inner = -4.5
            pulse_step = 0.08
            accent_color = self.COLOR_ACTIVE
        elif self.state == "ANALYZING":
            speed_outer = 6.0
            speed_inner = -8.0
            pulse_step = 0.12
            accent_color = "#00a8ff"
        elif self.state == "SPEAKING":
            speed_outer = 2.0
            speed_inner = -2.5
            pulse_step = 0.09
            accent_color = "#38ef7d"
        else: # IDLE
            speed_outer = 0.8
            speed_inner = -1.0
            pulse_step = 0.03
            accent_color = self.COLOR_CORE

        self.angle_outer = (self.angle_outer + speed_outer) % 360
        self.angle_inner = (self.angle_inner + speed_inner) % 360

        # Pulse breathing calculation
        self.pulse_val += pulse_step * self.pulse_dir
        if self.pulse_val >= 1.0:
            self.pulse_val = 1.0
            self.pulse_dir = -1
        elif self.pulse_val <= 0.0:
            self.pulse_val = 0.0
            self.pulse_dir = 1

        # Dynamic core radius
        extra_radius = (self.audio_level * 18.0) if self.state == "LISTENING" else (self.pulse_val * 6.0)
        base_r = 75

        # 1. Outer ambient glow ring
        outer_glow_r = base_r + 28 + extra_radius
        self.create_oval(
            cx - outer_glow_r, cy - outer_glow_r,
            cx + outer_glow_r, cy + outer_glow_r,
            outline="#0c233d", width=2
        )

        # 2. Segmented rotating outer ring
        outer_r = base_r + 14
        num_outer_segments = 12
        seg_len = 18
        for i in range(num_outer_segments):
            start_deg = (self.angle_outer + (i * (360 / num_outer_segments))) % 360
            self.create_arc(
                cx - outer_r, cy - outer_r,
                cx + outer_r, cy + outer_r,
                start=start_deg, extent=seg_len,
                style=tk.ARC, outline=accent_color, width=3
            )

        # 3. Inner counter-rotating ring with ticker notches
        inner_r = base_r - 12
        num_inner_segments = 8
        for i in range(num_inner_segments):
            start_deg = (self.angle_inner + (i * (360 / num_inner_segments))) % 360
            self.create_arc(
                cx - inner_r, cy - inner_r,
                cx + inner_r, cy + inner_r,
                start=start_deg, extent=24,
                style=tk.ARC, outline=self.COLOR_GLOW, width=2
            )

        # 4. Central Reactor Core circles
        core_r1 = 40 + (extra_radius * 0.7)
        self.create_oval(
            cx - core_r1, cy - core_r1,
            cx + core_r1, cy + core_r1,
            outline=accent_color, width=3, fill="#07192b"
        )

        core_r2 = 22 + (extra_radius * 0.4)
        self.create_oval(
            cx - core_r2, cy - core_r2,
            cx + core_r2, cy + core_r2,
            outline="#ffffff", width=2, fill=accent_color
        )

        # 5. Core bright center pip
        center_pip = 8
        self.create_oval(
            cx - center_pip, cy - center_pip,
            cx + center_pip, cy + center_pip,
            outline="#ffffff", fill="#ffffff"
        )

        # 6. Sci-Fi Radiating Crosshairs / Guidemarks
        for deg in [0, 90, 180, 270]:
            rad = math.radians(deg)
            x1 = cx + math.cos(rad) * (base_r + 20)
            y1 = cy + math.sin(rad) * (base_r + 20)
            x2 = cx + math.cos(rad) * (base_r + 32)
            y2 = cy + math.sin(rad) * (base_r + 32)
            self.create_line(x1, y1, x2, y2, fill=self.COLOR_GLOW, width=2)

        # Loop at ~40 FPS (25ms)
        self.after(25, self._animate)

    def destroy(self):
        self._running = False
        super().destroy()
