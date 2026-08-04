"""Live HUD overlay backed by ctf_live_esp_state.json from the game process."""

from __future__ import annotations

import ctypes
import json
import time
import tkinter as tk
from pathlib import Path


STATE_PATH = Path(
    r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc"
    r"\ctf_live_esp_state.json"
)
LOG_PATH = Path(
    r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc"
    r"\esp_hud_overlay.log"
)

TRANSPARENT = "black"
PANEL = "#111827"
TEXT = "#e5e7eb"
MUTED = "#94a3b8"
GREEN = "#22c55e"
YELLOW = "#facc15"
RED = "#ef4444"
CYAN = "#38bdf8"


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


user32 = ctypes.windll.user32
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080


def log(message: str) -> None:
    try:
        with LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(f"{time.time():.3f} {message}\n")
    except Exception:
        pass


def find_window() -> int:
    found = ctypes.c_void_p()

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def enum_proc(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buf, len(buf))
        if buf.value == "BloodStrike SexMaster_18":
            found.value = hwnd
            return False
        return True

    user32.EnumWindows(enum_proc, 0)
    return int(found.value or 0)


def window_rect(hwnd: int) -> tuple[int, int, int, int]:
    rect = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise ctypes.WinError()
    return rect.left, rect.top, rect.right, rect.bottom


def make_clickthrough(root: tk.Tk) -> None:
    hwnd = root.winfo_id()
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    style |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)


def load_state() -> dict:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def color_hex(row: dict) -> str:
    tier = row.get("tier")
    if tier == "NEAR":
        return RED
    if tier == "MID":
        return YELLOW
    if tier == "FAR":
        return GREEN
    return TEXT


def fmt_dist(value) -> str:
    if value is None:
        return "??.?m"
    return f"{float(value):04.1f}m"


def fmt_hp(row: dict) -> str:
    hp = row.get("hp")
    maxhp = row.get("maxhp")
    if hp is None:
        return "HP ?"
    if maxhp:
        return f"HP {int(round(hp))}/{int(round(maxhp))}"
    return f"HP {int(round(hp))}"


def draw_bar(canvas: tk.Canvas, x: int, y: int, w: int, h: int, ratio: float, color: str) -> None:
    canvas.create_rectangle(x, y, x + w, y + h, outline="#334155", fill="#0f172a", width=1)
    fill_w = max(0, min(w, int(w * ratio)))
    canvas.create_rectangle(x, y, x + fill_w, y + h, outline="", fill=color)


def draw(canvas: tk.Canvas, width: int, height: int) -> None:
    canvas.delete("all")
    state = load_state()
    targets = state.get("targets") or []
    updated = float(state.get("updated") or 0)
    fresh = time.time() - updated < 2.5

    panel_x, panel_y = 0, 0
    panel_w = width - 2
    row_h = 34
    panel_h = 72 + max(1, len(targets)) * row_h

    canvas.create_rectangle(
        panel_x,
        panel_y,
        panel_x + panel_w,
        panel_y + panel_h,
        fill=PANEL,
        outline="#334155",
        width=2,
    )
    canvas.create_text(
        panel_x + 14,
        panel_y + 16,
        anchor="w",
        text="BLOODSTRIKE CTF ESP",
        fill=CYAN,
        font=("Consolas", 15, "bold"),
    )
    status = "LIVE" if fresh else "STALE"
    status_color = GREEN if fresh else RED
    canvas.create_text(
        panel_x + panel_w - 14,
        panel_y + 16,
        anchor="e",
        text=f"{status}  T:{len(targets)}",
        fill=status_color,
        font=("Consolas", 12, "bold"),
    )
    canvas.create_text(
        panel_x + 14,
        panel_y + 40,
        anchor="w",
        text="tier   dist    health        armor",
        fill=MUTED,
        font=("Consolas", 11),
    )

    for i, row in enumerate(targets[:10]):
        y = panel_y + 62 + i * row_h
        color = color_hex(row)
        hp = row.get("hp")
        maxhp = row.get("maxhp") or 125
        armor = row.get("armor") or 0
        maxarmor = row.get("maxarmor") or max(armor, 1)
        hp_ratio = 0 if hp is None else float(hp) / float(maxhp or 1)
        ar_ratio = 0 if not armor else float(armor) / float(maxarmor or armor or 1)

        canvas.create_rectangle(panel_x + 10, y - 3, panel_x + panel_w - 10, y + row_h - 6, fill="#0b1220", outline="")
        canvas.create_text(
            panel_x + 18,
            y + 8,
            anchor="w",
            text=f"T{row.get('idx', i + 1)} {row.get('tier', 'UNK'):<4} {fmt_dist(row.get('distance'))}",
            fill=color,
            font=("Consolas", 12, "bold"),
        )
        canvas.create_text(
            panel_x + 160,
            y + 8,
            anchor="w",
            text=fmt_hp(row),
            fill=TEXT,
            font=("Consolas", 12, "bold"),
        )
        canvas.create_text(
            panel_x + 280,
            y + 8,
            anchor="w",
            text=f"AR {int(round(armor))}",
            fill=MUTED,
            font=("Consolas", 12, "bold"),
        )
        draw_bar(canvas, panel_x + 160, y + 20, 92, 7, hp_ratio, color)
        draw_bar(canvas, panel_x + 280, y + 20, 50, 7, ar_ratio, "#60a5fa")


def main() -> int:
    hwnd = find_window()
    if not hwnd:
        log("BloodStrike window not found")
        return 1

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.94)
    root.configure(bg=PANEL)

    canvas = tk.Canvas(root, bg=PANEL, highlightthickness=0, bd=0)
    canvas.pack(fill="both", expand=True)
    root.update_idletasks()
    log(f"overlay started hwnd={hwnd}")

    def redraw() -> None:
        try:
            left, top, right, bottom = window_rect(hwnd)
            width = 388
            height = 306
            root.geometry(f"{width}x{height}+{left + 22}+{top + 118}")
            canvas.config(width=width, height=height)
            draw(canvas, width, height)
            root.after(250, redraw)
        except Exception as exc:
            log(f"overlay error: {exc!r}")
            root.after(1000, redraw)

    redraw()
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
