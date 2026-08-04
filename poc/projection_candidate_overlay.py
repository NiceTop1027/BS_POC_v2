"""Temporary world-to-screen calibration overlay for the local CTF instance."""

from __future__ import annotations

import ctypes
import json
import math
import tkinter as tk
from pathlib import Path


STATE_PATH = Path(__file__).with_name("projection_probe.json")
TITLE = "BloodStrike SexMaster_18"
TRANSPARENT = "#ff00ff"


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


user32 = ctypes.windll.user32
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080


def find_window() -> int:
    found = ctypes.c_void_p()

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def enum_proc(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buf, len(buf))
        if buf.value == TITLE:
            found.value = hwnd
            return False
        return True

    user32.EnumWindows(enum_proc, 0)
    return int(found.value or 0)


def client_geometry(hwnd: int) -> tuple[int, int, int, int]:
    rect = RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
        raise ctypes.WinError()
    point = POINT(0, 0)
    if not user32.ClientToScreen(hwnd, ctypes.byref(point)):
        raise ctypes.WinError()
    return point.x, point.y, rect.right - rect.left, rect.bottom - rect.top


def project(point: tuple[float, float, float], camera: dict, size: tuple[int, int], mode: int):
    yaw = float(camera["yaw"])
    pitch = float(camera["pitch"])
    pos = camera["position"]
    dx = point[0] - float(pos[0])
    dy = point[1] - float(pos[1])
    dz = point[2] - float(pos[2])

    # Four yaw conventions and their 180-degree counterparts.
    if mode % 4 in (0, 1):
        fx, fz = math.cos(yaw), math.sin(yaw)
    else:
        fx, fz = math.sin(yaw), math.cos(yaw)
    if mode % 2 == 1:
        fx, fz = -fx, -fz
    if mode >= 4:
        fx, fz = -fz, fx
    rx, rz = fz, -fx
    horizontal_depth = dx * fx + dz * fz
    horizontal_right = dx * rx + dz * rz
    cp = math.cos(pitch)
    sp = math.sin(pitch)
    depth = horizontal_depth * cp + dy * sp
    up = dy * cp - horizontal_depth * sp
    if depth <= 0.15:
        return None
    width, height = size
    focal_y = height / (2.0 * math.tan(math.radians(float(camera["fov"])) * 0.5))
    return (width * 0.5 + horizontal_right * focal_y / depth, height * 0.5 - up * focal_y / depth)


def bounds_corners(low, high):
    return [
        (x, y, z)
        for x in (float(low[0]), float(high[0]))
        for y in (float(low[1]), float(high[1]))
        for z in (float(low[2]), float(high[2]))
    ]


def main() -> int:
    payload = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    hwnd = find_window()
    if not hwnd:
        raise RuntimeError("BloodStrike window not found")
    left, top, width, height = client_geometry(hwnd)
    game_width, game_height = payload["screen"]
    scale_x = width / float(game_width)
    scale_y = height / float(game_height)

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.wm_attributes("-transparentcolor", TRANSPARENT)
    root.configure(bg=TRANSPARENT)
    root.geometry(f"{width}x{height}+{left}+{top}")
    canvas = tk.Canvas(root, bg=TRANSPARENT, highlightthickness=0, bd=0)
    canvas.pack(fill="both", expand=True)
    root.update_idletasks()
    style = user32.GetWindowLongW(root.winfo_id(), GWL_EXSTYLE)
    user32.SetWindowLongW(root.winfo_id(), GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW)

    colors = ("#ff1744", "#00e5ff", "#76ff03", "#ffea00", "#d500f9", "#ff9100", "#2979ff", "#ffffff")
    for mode, color in enumerate(colors):
        for row in payload.get("robots", []):
            if not row.get("min") or not row.get("max"):
                continue
            projected = [project(corner, payload["camera"], (game_width, game_height), mode) for corner in bounds_corners(row["min"], row["max"])]
            projected = [point for point in projected if point is not None]
            if len(projected) < 2:
                continue
            xs = [point[0] * scale_x for point in projected]
            ys = [point[1] * scale_y for point in projected]
            x0, x1 = min(xs), max(xs)
            y0, y1 = min(ys), max(ys)
            if x1 < -400 or y1 < -400 or x0 > width + 400 or y0 > height + 400:
                continue
            canvas.create_rectangle(x0, y0, x1, y1, outline=color, width=2)
            canvas.create_text(x0, y0 - 8, anchor="sw", text=f"{mode}", fill=color, font=("Consolas", 10, "bold"))

    root.after(12000, root.destroy)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
