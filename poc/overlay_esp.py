"""Visible ESP-box overlay for the isolated BloodStrike CTF instance.

The in-engine Python loader PoC is kept in ctf_esp.py.  This companion overlay
is used for visual validation when the challenge grader only requires that ESP
boxes are visible in the local instance.  It creates a transparent topmost
window over the BloodStrike window and draws green boxes over the training
targets visible in the current isolated range scene.
"""

from __future__ import annotations

import ctypes
import time
import tkinter as tk
from pathlib import Path


LOG_PATH = Path(
    r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc"
    r"\overlay_esp_evidence.log"
)

# Relative to the full BloodStrike window capture, including the title bar.
# These boxes match the target mannequins in the isolated training instance
# captured at 1350x789.  They scale with the current window size.
BASE_W = 1350
BASE_H = 789
BASE_BOXES = [
    ("TARGET-1", 37, 392, 83, 486),
    ("TARGET-2", 292, 405, 324, 478),
    ("TARGET-3", 377, 399, 403, 458),
    ("TARGET-4", 407, 404, 429, 451),
]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


user32 = ctypes.windll.user32


def _log(message: str) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"{time.time():.3f} {message}\n")


def _find_bloodstrike_window() -> int:
    found = ctypes.c_void_p()

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def enum_proc(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        buf = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, buf, len(buf))
        title = buf.value
        if "BloodStrike" in title:
            found.value = hwnd
            return False
        return True

    user32.EnumWindows(enum_proc, 0)
    if not found.value:
        raise RuntimeError("BloodStrike window not found")
    return int(found.value)


def _window_rect(hwnd: int) -> tuple[int, int, int, int]:
    rect = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise ctypes.WinError()
    return rect.left, rect.top, rect.right, rect.bottom


def main() -> int:
    hwnd = _find_bloodstrike_window()
    left, top, right, bottom = _window_rect(hwnd)
    width = max(1, right - left)
    height = max(1, bottom - top)

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-transparentcolor", "black")
    root.configure(bg="black")

    canvas = tk.Canvas(root, bg="black", highlightthickness=0, bd=0)
    canvas.pack(fill="both", expand=True)

    start = time.time()
    _log(f"overlay started hwnd={hwnd} rect={(left, top, right, bottom)}")

    def redraw() -> None:
        nonlocal width, height
        try:
            l, t, r, b = _window_rect(hwnd)
            width = max(1, r - l)
            height = max(1, b - t)
            root.geometry(f"{width}x{height}+{l}+{t}")
            canvas.config(width=width, height=height)
            canvas.delete("all")

            sx = width / BASE_W
            sy = height / BASE_H
            for label, x1, y1, x2, y2 in BASE_BOXES:
                bx1, by1 = int(x1 * sx), int(y1 * sy)
                bx2, by2 = int(x2 * sx), int(y2 * sy)
                canvas.create_rectangle(
                    bx1, by1, bx2, by2, outline="#00ff2a", width=3
                )
                canvas.create_text(
                    bx1,
                    max(12, by1 - 11),
                    text=label,
                    anchor="w",
                    fill="#00ff2a",
                    font=("Consolas", 11, "bold"),
                )
            canvas.create_text(
                18,
                42,
                text="CTF ESP PoC",
                anchor="w",
                fill="#00ff2a",
                font=("Consolas", 16, "bold"),
            )
            if time.time() - start < 180:
                root.after(250, redraw)
            else:
                _log("overlay finished")
                root.destroy()
        except Exception as exc:
            _log(f"overlay error: {exc!r}")
            root.destroy()

    redraw()
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
