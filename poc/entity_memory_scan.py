"""Runtime memory scanner for the isolated BloodStrike CTF instance.

This is a read-only scanner.  It searches the elevated game process for
runtime strings and compact float clusters that can lead to real entity
structures.  It deliberately does not draw boxes or claim ESP success.
"""

from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import json
import math
import re
import struct
import time
from pathlib import Path


PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000
MEM_PRIVATE = 0x20000
MEM_MAPPED = 0x40000
MEM_IMAGE = 0x1000000
PAGE_NOACCESS = 0x01
PAGE_GUARD = 0x100


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wt.DWORD),
        ("PartitionId", wt.WORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wt.DWORD),
        ("Protect", wt.DWORD),
        ("Type", wt.DWORD),
    ]


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
kernel32.OpenProcess.restype = wt.HANDLE
kernel32.VirtualQueryEx.argtypes = [
    wt.HANDLE,
    ctypes.c_void_p,
    ctypes.POINTER(MEMORY_BASIC_INFORMATION),
    ctypes.c_size_t,
]
kernel32.VirtualQueryEx.restype = ctypes.c_size_t
kernel32.ReadProcessMemory.argtypes = [
    wt.HANDLE,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
kernel32.ReadProcessMemory.restype = wt.BOOL
kernel32.CloseHandle.argtypes = [wt.HANDLE]


NEEDLES = [
    "Target",
    "target",
    "Dummy",
    "dummy",
    "Mannequin",
    "Training",
    "training",
    "Enemy",
    "enemy",
    "NPC",
    "Bot",
    "bot",
    "IEntity",
    "EntityID",
    "BoneName",
    "Head",
    "Spine",
    "Pelvis",
    "GetWorldBound",
    "GetPosition",
    "GetBoneWorldTransform",
    "SetIsOutlined",
    "SetIsThermalVisible",
    "asiocore",
    "entities",
    "MainPlayer_POS",
    "PlayerPos",
    "BloodStrike",
]


def read_at(handle: int, address: int, size: int) -> bytes:
    out = bytearray()
    cursor = address
    remaining = size
    while remaining:
        step = min(0x10000, remaining)
        buf = ctypes.create_string_buffer(step)
        got = ctypes.c_size_t()
        ok = kernel32.ReadProcessMemory(
            handle, ctypes.c_void_p(cursor), buf, step, ctypes.byref(got)
        )
        if not ok and not got.value:
            break
        out.extend(buf.raw[: got.value])
        if got.value == 0:
            break
        cursor += got.value
        remaining -= got.value
        if got.value < step:
            break
    return bytes(out)


def iter_regions(handle: int):
    mbi = MEMORY_BASIC_INFORMATION()
    address = 0
    while address < 0x7FFF_FFFF_FFFF:
        result = kernel32.VirtualQueryEx(
            handle,
            ctypes.c_void_p(address),
            ctypes.byref(mbi),
            ctypes.sizeof(mbi),
        )
        if not result:
            break
        base = int(mbi.BaseAddress or 0)
        size = int(mbi.RegionSize)
        if size <= 0:
            break
        readable = (
            mbi.State == MEM_COMMIT
            and not (mbi.Protect & PAGE_GUARD)
            and mbi.Protect != PAGE_NOACCESS
        )
        if readable:
            yield base, size, int(mbi.Protect), int(mbi.Type)
        address = base + size


def clean_context(raw: bytes) -> str:
    text = raw.replace(b"\x00", b" ")
    text = re.sub(rb"[^\x20-\x7e]+", b" ", text)
    return text[:240].decode("ascii", "replace")


def scan_strings(data: bytes, base: int, region_type: int, limit_per_needle: int):
    hits = []
    for needle in NEEDLES:
        encodings = [(needle.encode("ascii", "ignore"), "ascii")]
        encodings.append((needle.encode("utf-16le", "ignore"), "utf16"))
        for raw_needle, enc in encodings:
            if not raw_needle:
                continue
            start = 0
            found = 0
            while found < limit_per_needle:
                pos = data.find(raw_needle, start)
                if pos < 0:
                    break
                lo = max(0, pos - 96)
                hi = min(len(data), pos + len(raw_needle) + 144)
                hits.append(
                    {
                        "needle": needle,
                        "encoding": enc,
                        "address": f"0x{base + pos:x}",
                        "region_type": region_type,
                        "context": clean_context(data[lo:hi]),
                    }
                )
                found += 1
                start = pos + 1
    return hits


def plausible_vec3(a: float, b: float, c: float) -> bool:
    vals = (a, b, c)
    if not all(math.isfinite(v) for v in vals):
        return False
    if not all(-50000.0 <= v <= 50000.0 for v in vals):
        return False
    mag = math.sqrt(a * a + b * b + c * c)
    if mag < 1.0 or mag > 100000.0:
        return False
    # Human/target transforms usually have at least one horizontal component
    # outside the tiny [-1, 1] range; this drops normal vectors and colors.
    return any(abs(v) > 2.0 for v in vals)


def scan_float_clusters(data: bytes, base: int, max_hits: int):
    hits = []
    step = 4
    end = len(data) - 12
    for pos in range(0, end, step):
        try:
            a, b, c = struct.unpack_from("<fff", data, pos)
        except struct.error:
            break
        if not plausible_vec3(a, b, c):
            continue
        # A nearby identity-ish quaternion/matrix/scale value often marks
        # transform storage.  This is only a lead, not a final entity claim.
        nearby = data[pos : min(len(data), pos + 64)]
        score = 0
        for value in (0.0, 1.0):
            packed = struct.pack("<f", value)
            score += nearby.count(packed)
        if score < 2:
            continue
        hits.append(
            {
                "address": f"0x{base + pos:x}",
                "vec3": [round(a, 4), round(b, 4), round(c, 4)],
                "score": score,
            }
        )
        if len(hits) >= max_hits:
            break
    return hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-region", type=lambda x: int(x, 0), default=0x4000000)
    parser.add_argument("--string-limit", type=int, default=20)
    parser.add_argument("--float-limit", type=int, default=400)
    args = parser.parse_args()

    handle = kernel32.OpenProcess(
        PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, args.pid
    )
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())

    report = {
        "pid": args.pid,
        "started": time.time(),
        "regions_scanned": 0,
        "bytes_scanned": 0,
        "string_hits": [],
        "float_cluster_hits": [],
    }
    try:
        for base, size, protect, region_type in iter_regions(handle):
            if region_type == MEM_IMAGE:
                # Static strings are already known.  Runtime objects are in
                # private/mapped regions, so keep the scan focused.
                continue
            if region_type not in (MEM_PRIVATE, MEM_MAPPED):
                continue
            if size > args.max_region:
                continue
            data = read_at(handle, base, size)
            if not data:
                continue
            report["regions_scanned"] += 1
            report["bytes_scanned"] += len(data)
            report["string_hits"].extend(
                scan_strings(data, base, region_type, args.string_limit)
            )
            if len(report["float_cluster_hits"]) < args.float_limit:
                needed = args.float_limit - len(report["float_cluster_hits"])
                report["float_cluster_hits"].extend(
                    scan_float_clusters(data, base, needed)
                )
    finally:
        kernel32.CloseHandle(handle)

    report["finished"] = time.time()
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "pid": args.pid,
        "out": str(args.out),
        "regions_scanned": report["regions_scanned"],
        "bytes_scanned": report["bytes_scanned"],
        "string_hits": len(report["string_hits"]),
        "float_cluster_hits": len(report["float_cluster_hits"]),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
