"""Read-only offset discovery for the isolated CTF game's active ICamera."""

from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import json
import math
import struct
from pathlib import Path


PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
kernel32.OpenProcess.restype = wt.HANDLE
kernel32.ReadProcessMemory.argtypes = [
    wt.HANDLE,
    wt.LPCVOID,
    wt.LPVOID,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
kernel32.ReadProcessMemory.restype = wt.BOOL
kernel32.CloseHandle.argtypes = [wt.HANDLE]


def read_process(handle: int, address: int, size: int) -> bytes:
    buffer = ctypes.create_string_buffer(size)
    read = ctypes.c_size_t()
    if not kernel32.ReadProcessMemory(
        handle, ctypes.c_void_p(address), buffer, size, ctypes.byref(read)
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    return buffer.raw[: read.value]


def load_frame(path: Path) -> dict[str, float]:
    fields = path.read_text(encoding="ascii").splitlines()[0].split()
    if len(fields) < 11 or fields[0] != "ESP1":
        raise ValueError("invalid ESP state header")
    return {
        "x": float(fields[4]),
        "y": float(fields[5]),
        "z": float(fields[6]),
        "yaw": float(fields[7]),
        "pitch": float(fields[8]),
        "roll": float(fields[9]),
        "fov": float(fields[10]),
    }


def close_float(left: float, right: float, tolerance: float = 0.0008) -> bool:
    return math.isfinite(left) and abs(left - right) <= tolerance


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--camera", required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    camera = int(args.camera, 0)
    frame = load_frame(args.state)
    handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, args.pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        # ICamera contains a vtable and several nested native components.  A
        # small local window is enough to locate live float triples/matrices.
        base = camera - 0x200
        payload = read_process(handle, base, 0x4000)
    finally:
        kernel32.CloseHandle(handle)

    triples: list[dict[str, object]] = []
    values: dict[str, list[dict[str, object]]] = {key: [] for key in frame}
    for offset in range(0, len(payload) - 24, 4):
        floats = struct.unpack_from("<6f", payload, offset)
        if (
            close_float(floats[0], frame["x"])
            and close_float(floats[1], frame["y"])
            and close_float(floats[2], frame["z"])
        ):
            triples.append({
                "offset": hex(offset - 0x200),
                "address": hex(base + offset),
                "values": [round(value, 7) for value in floats],
            })
        for key, expected in frame.items():
            if len(values[key]) >= 24 or not close_float(floats[0], expected):
                continue
            values[key].append({
                "offset": hex(offset - 0x200),
                "address": hex(base + offset),
                "neighbors": [round(value, 7) for value in floats],
            })

    args.out.write_text(json.dumps({
        "pid": args.pid,
        "camera": hex(camera),
        "frame": frame,
        "scan_base": hex(base),
        "triples": triples,
        "values": values,
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
