"""Read-only live-process probe for the CTF BloodStrike instance.

Run this from an elevated PowerShell because BloodStrike.exe requests
requireAdministrator.  It never writes to or injects into the target process;
the output is limited to module/region metadata and addresses of static marker
strings in readable image regions.
"""

from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import json
import struct
from pathlib import Path


PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000
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


def command_line(pid: int) -> str | None:
    ntdll = ctypes.WinDLL("ntdll")
    ntdll.NtQueryInformationProcess.argtypes = [
        wt.HANDLE,
        wt.ULONG,
        ctypes.c_void_p,
        wt.ULONG,
        ctypes.POINTER(wt.ULONG),
    ]
    ntdll.NtQueryInformationProcess.restype = wt.LONG
    handle = kernel32.OpenProcess(0x1000, False, pid)
    if not handle:
        return None
    try:
        # ProcessCommandLineInformation (60) returns a UNICODE_STRING followed
        # by the string buffer for same-user query-limited callers.
        buf = ctypes.create_string_buffer(0x4000)
        length = wt.ULONG()
        status = ntdll.NtQueryInformationProcess(
            handle, 60, buf, len(buf), ctypes.byref(length)
        )
        if status != 0 or length.value < 16:
            return None
        text_length = struct.unpack_from("<H", buf.raw, 0)[0]
        return buf.raw[16 : 16 + text_length].decode("utf-16le", "replace")
    finally:
        kernel32.CloseHandle(handle)


def startup_context(handle: int) -> dict[str, object] | None:
    """Read only the target's PEB startup fields needed for launcher parity."""
    ntdll = ctypes.WinDLL("ntdll")
    ntdll.NtQueryInformationProcess.argtypes = [
        wt.HANDLE,
        wt.ULONG,
        ctypes.c_void_p,
        wt.ULONG,
        ctypes.POINTER(wt.ULONG),
    ]
    ntdll.NtQueryInformationProcess.restype = wt.LONG

    # Asking for the exact 64-bit PROCESS_BASIC_INFORMATION size avoids the
    # Windows extended form (which prepends a Size field and shifts the PEB).
    pbi = ctypes.create_string_buffer(0x30)
    returned = wt.ULONG()
    status = ntdll.NtQueryInformationProcess(
        handle, 0, pbi, len(pbi), ctypes.byref(returned)
    )
    if status != 0:
        return {"error": f"NtQueryInformationProcess(0)={status:#x}"}
    peb = struct.unpack_from("<Q", pbi.raw, 8)[0]
    peb_data = read_at(handle, peb + 0x20, 8)
    if len(peb_data) != 8:
        return {
            "error": "could not read PEB.ProcessParameters",
            "peb": f"0x{peb:x}",
            "pbi_returned": returned.value,
            "pbi_head": pbi.raw[:48].hex(),
        }
    params = struct.unpack("<Q", peb_data)[0]
    raw = read_at(handle, params, 0x100)
    if len(raw) < 0x88:
        return {
            "error": "could not read RTL_USER_PROCESS_PARAMETERS",
            "peb": f"0x{peb:x}",
            "process_parameters": f"0x{params:x}",
        }

    def remote_unicode(offset: int) -> str | None:
        length, _maximum, ptr = struct.unpack_from("<HHQ", raw, offset)
        if not ptr or not length:
            return ""
        data = read_at(handle, ptr, length)
        if len(data) != length:
            return None
        return data.decode("utf-16le", "replace")

    # Offsets are the x64 RTL_USER_PROCESS_PARAMETERS layout used by this PE.
    current_directory = remote_unicode(0x38)
    image_path = remote_unicode(0x60)
    process_command_line = remote_unicode(0x70)
    environment_ptr = struct.unpack_from("<Q", raw, 0x80)[0]
    env_data = read_at(handle, environment_ptr, 0x10000) if environment_ptr else b""
    selected_env: dict[str, str] = {}
    for item in env_data.decode("utf-16le", "replace").split("\0"):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        if key.upper() in {
            "MESSIAHLAUNCHERINFO",
            "MESSIAHAPPNAME",
            "PYTHONPATH",
            "PYTHONHOME",
            "PYTHONSAFEPATH",
            "PYTHONNOUSERSITE",
        }:
            selected_env[key] = value
    return {
        "peb": f"0x{peb:x}",
        "process_parameters": f"0x{params:x}",
        "current_directory": current_directory,
        "image_path": image_path,
        "command_line_from_peb": process_command_line,
        "launcher_environment": selected_env,
    }


def pe_image_size(blob: bytes) -> int | None:
    if len(blob) < 0x100 or blob[:2] != b"MZ":
        return None
    peoff = struct.unpack_from("<I", blob, 0x3C)[0]
    if peoff + 0x60 > len(blob) or blob[peoff : peoff + 4] != b"PE\0\0":
        return None
    optional = peoff + 24
    magic = struct.unpack_from("<H", blob, optional)[0]
    if magic not in (0x10B, 0x20B):
        return None
    return struct.unpack_from("<I", blob, optional + 56)[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, default=35156)
    ap.add_argument("--output", type=Path)
    ap.add_argument(
        "--startup-only",
        action="store_true",
        help="collect only PEB startup context; do not enumerate memory regions",
    )
    args = ap.parse_args()

    access = PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
    handle = kernel32.OpenProcess(access, False, args.pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())

    markers = [
        b"BoneName",
        b"MainPlayer_POS",
        b"PlayerPos",
        b"GetBoneWorldTransform",
        b"GetBoneVisualTransform",
        b"EntityID",
        b"IEntity",
        b"RpcServerPort",
        b"debug_dangerous_get_object",
    ]
    regions: list[dict[str, int]] = []
    images: list[dict[str, int | str]] = []
    marker_hits: dict[str, list[str]] = {m.decode(): [] for m in markers}
    context = startup_context(handle)
    if args.startup_only:
        kernel32.CloseHandle(handle)
        report = {
            "pid": args.pid,
            "command_line": command_line(args.pid),
            "startup_context": context,
        }
        encoded = json.dumps(report, indent=2, ensure_ascii=False)
        print(encoded)
        if args.output:
            args.output.write_text(encoded + "\n", encoding="utf-8")
        return 0
    mbi = MEMORY_BASIC_INFORMATION()
    address = 0
    try:
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
                head = read_at(handle, base, min(size, 0x1000))
                image_size = pe_image_size(head)
                if image_size:
                    images.append(
                        {
                            "base": f"0x{base:x}",
                            "region_size": size,
                            "image_size": image_size,
                            "type": int(mbi.Type),
                        }
                    )
                # Only scan image regions and bounded private regions.  This is
                # enough for static markers without dumping the whole process.
                if (mbi.Type == MEM_IMAGE or image_size) and size <= 0x20000000:
                    data = read_at(handle, base, size)
                    for marker in markers:
                        start = 0
                        while len(marker_hits[marker.decode()]) < 40:
                            pos = data.find(marker, start)
                            if pos < 0:
                                break
                            marker_hits[marker.decode()].append(hex(base + pos))
                            start = pos + 1
                regions.append(
                    {
                        "base": base,
                        "size": size,
                        "protect": int(mbi.Protect),
                        "type": int(mbi.Type),
                    }
                )
            address = base + size
    finally:
        kernel32.CloseHandle(handle)

    report = {
        "pid": args.pid,
        "command_line": command_line(args.pid),
        "startup_context": context,
        "images": images,
        "readable_region_count": len(regions),
        "marker_hits": marker_hits,
    }
    encoded = json.dumps(report, indent=2, ensure_ascii=False)
    print(encoded)
    if args.output:
        args.output.write_text(encoded + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
