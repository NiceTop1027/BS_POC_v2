"""Targeted pointer scanner for the isolated BloodStrike CTF instance.

The broad scanner finds many useful strings, but a string hit is not an ESP.
This script follows references to selected runtime strings and reports the
nearby pointer/float layout so we can distinguish Python constants from live
entity state.
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


DEFAULT_TERMS = [
    "HP_Dummy",
    "shootingrange_target",
    "RobotCombatAvatarShootingRange",
    "target_entity_id",
    "controlling_target",
    "recon_drone_mark_ent_ids",
    "DrawEnemyReconMarkFrames",
    "EnemyMarkComp",
    "ShowEnemyToplogo",
    "ShowEnemyBar",
    "GetBoneWorldTransform",
    "GetWorldBound",
    "SetIsOutlined",
]

PY_OBJECT_OFFSETS = (0, 0x18, 0x20, 0x28, 0x30, 0x38, 0x40, 0x48)


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


def clean_context(raw: bytes, limit: int = 320) -> str:
    text = raw.replace(b"\x00", b" ")
    text = re.sub(rb"[^\x20-\x7e]+", b" ", text)
    return text[:limit].decode("ascii", "replace")


def plausible_vec3(vals: tuple[float, float, float]) -> bool:
    if not all(math.isfinite(v) for v in vals):
        return False
    if not all(-50000.0 <= v <= 50000.0 for v in vals):
        return False
    mag = math.sqrt(sum(v * v for v in vals))
    return 1.0 <= mag <= 100000.0 and any(abs(v) > 2.0 for v in vals)


def find_vec3s(raw: bytes, base: int, max_hits: int = 24):
    hits = []
    for pos in range(0, max(0, len(raw) - 12), 4):
        try:
            vals = struct.unpack_from("<fff", raw, pos)
        except struct.error:
            break
        if plausible_vec3(vals):
            hits.append(
                {
                    "address": f"0x{base + pos:x}",
                    "vec3": [round(v, 4) for v in vals],
                }
            )
            if len(hits) >= max_hits:
                break
    return hits


def load_seed_hits(path: Path, terms: list[str], max_seeds: int):
    report = json.loads(path.read_text(encoding="utf-8"))
    selected = []
    seen = set()
    for hit in report.get("string_hits", []):
        context = str(hit.get("context", ""))
        needle = str(hit.get("needle", ""))
        haystack = f"{needle}\n{context}".lower()
        if not any(term.lower() in haystack for term in terms):
            continue
        address = int(str(hit["address"]), 16)
        key = (address, needle, context[:80])
        if key in seen:
            continue
        seen.add(key)
        selected.append(
            {
                "address": address,
                "needle": needle,
                "encoding": hit.get("encoding"),
                "context": context,
            }
        )
        if len(selected) >= max_seeds:
            break
    return selected


def build_targets(seed_hits):
    targets = {}
    for index, hit in enumerate(seed_hits):
        for offset in PY_OBJECT_OFFSETS:
            value = hit["address"] - offset
            if value <= 0:
                continue
            targets.setdefault(value, []).append(
                {
                    "seed_index": index,
                    "seed_address": f"0x{hit['address']:x}",
                    "object_offset_guess": offset,
                    "needle": hit["needle"],
                    "context": hit["context"][:180],
                }
            )
    return targets


def describe_qwords(raw: bytes, base: int, readable_ranges, max_items: int = 48):
    items = []
    aligned_start = (8 - (base % 8)) % 8
    for pos in range(aligned_start, max(0, len(raw) - 8), 8):
        value = struct.unpack_from("<Q", raw, pos)[0]
        if not any(lo <= value < hi for lo, hi in readable_ranges):
            continue
        item = {"address": f"0x{base + pos:x}", "value": f"0x{value:x}"}
        peek = raw[max(0, pos - 16) : min(len(raw), pos + 64)]
        item["local_context"] = clean_context(peek, 120)
        items.append(item)
        if len(items) >= max_items:
            break
    return items


def scan_references(handle: int, targets: dict[int, list[dict]], args):
    readable = []
    regions = []
    for base, size, protect, region_type in iter_regions(handle):
        readable.append((base, base + size))
        if region_type == MEM_IMAGE and not args.include_image:
            continue
        if region_type not in (MEM_PRIVATE, MEM_MAPPED, MEM_IMAGE):
            continue
        if size > args.max_region:
            continue
        regions.append((base, size, protect, region_type))

    patterns = {struct.pack("<Q", value): value for value in targets}
    compiled = re.compile(b"|".join(re.escape(p) for p in patterns))
    results = []
    scanned = 0

    for base, size, protect, region_type in regions:
        data = read_at(handle, base, size)
        if not data:
            continue
        scanned += len(data)
        for match in compiled.finditer(data):
            pos = match.start()
            target_value = patterns[match.group(0)]
            ref_address = base + pos
            window_base = max(base, ref_address - args.window)
            window_end = min(base + len(data), ref_address + args.window)
            window = data[window_base - base : window_end - base]
            result = {
                "ref_address": f"0x{ref_address:x}",
                "points_to": f"0x{target_value:x}",
                "region_base": f"0x{base:x}",
                "region_size": f"0x{size:x}",
                "region_type": region_type,
                "target_seeds": targets[target_value],
                "ascii_context": clean_context(window),
                "nearby_pointers": describe_qwords(window, window_base, readable),
                "nearby_vec3": find_vec3s(window, window_base),
            }
            results.append(result)
            if len(results) >= args.max_refs:
                return results, len(regions), scanned
    return results, len(regions), scanned


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--seed-json", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--terms", default=",".join(DEFAULT_TERMS))
    parser.add_argument("--max-seeds", type=int, default=96)
    parser.add_argument("--max-refs", type=int, default=600)
    parser.add_argument("--max-region", type=lambda value: int(value, 0), default=0x4000000)
    parser.add_argument("--window", type=lambda value: int(value, 0), default=0x300)
    parser.add_argument("--include-image", action="store_true")
    args = parser.parse_args()

    terms = [term.strip() for term in args.terms.split(",") if term.strip()]
    seed_hits = load_seed_hits(args.seed_json, terms, args.max_seeds)
    targets = build_targets(seed_hits)
    if not targets:
        raise SystemExit("no seed targets selected")

    handle = kernel32.OpenProcess(
        PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, args.pid
    )
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())

    started = time.time()
    try:
        refs, regions_scanned, bytes_scanned = scan_references(handle, targets, args)
    finally:
        kernel32.CloseHandle(handle)

    report = {
        "pid": args.pid,
        "started": started,
        "finished": time.time(),
        "terms": terms,
        "seed_hits": [
            {
                "address": f"0x{hit['address']:x}",
                "needle": hit["needle"],
                "encoding": hit["encoding"],
                "context": hit["context"],
            }
            for hit in seed_hits
        ],
        "target_count": len(targets),
        "regions_scanned": regions_scanned,
        "bytes_scanned": bytes_scanned,
        "reference_hits": refs,
    }
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "pid": args.pid,
                "out": str(args.out),
                "seed_hits": len(seed_hits),
                "target_count": len(targets),
                "regions_scanned": regions_scanned,
                "bytes_scanned": bytes_scanned,
                "reference_hits": len(refs),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
