"""Call CPython import APIs inside the isolated BloodStrike CTF process.

This is a narrow remote-thread probe.  It acquires the embedded Python GIL,
calls PyImport_ImportModule("<module>"), stores the returned PyObject pointer,
then releases the GIL.  A successful import of ctf_esp.py should create
ctf_esp_evidence.log from the module top level.
"""

from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import json
import struct
import time
from pathlib import Path


PROCESS_CREATE_THREAD = 0x0002
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
MEM_RELEASE = 0x8000
PAGE_EXECUTE_READWRITE = 0x40
WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010
MAX_MODULE_NAME32 = 255

PREFERRED_IMAGE_BASE = 0x140000000
PY_GILSTATE_ENSURE_VA = 0x142AA_FBE0
PY_GILSTATE_RELEASE_VA = 0x142AA_FCB0
PY_IMPORT_IMPORTMODULE_VA = 0x142A8_C1F0
PY_SYS_SETPATH_VA = 0x142A7_89F0


class MODULEENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wt.DWORD),
        ("th32ModuleID", wt.DWORD),
        ("th32ProcessID", wt.DWORD),
        ("GlblcntUsage", wt.DWORD),
        ("ProccntUsage", wt.DWORD),
        ("modBaseAddr", ctypes.POINTER(ctypes.c_byte)),
        ("modBaseSize", wt.DWORD),
        ("hModule", wt.HMODULE),
        ("szModule", wt.WCHAR * (MAX_MODULE_NAME32 + 1)),
        ("szExePath", wt.WCHAR * wt.MAX_PATH),
    ]


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
kernel32.OpenProcess.restype = wt.HANDLE
kernel32.VirtualAllocEx.argtypes = [
    wt.HANDLE,
    wt.LPVOID,
    ctypes.c_size_t,
    wt.DWORD,
    wt.DWORD,
]
kernel32.VirtualAllocEx.restype = wt.LPVOID
kernel32.VirtualFreeEx.argtypes = [wt.HANDLE, wt.LPVOID, ctypes.c_size_t, wt.DWORD]
kernel32.WriteProcessMemory.argtypes = [
    wt.HANDLE,
    wt.LPVOID,
    wt.LPCVOID,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
kernel32.WriteProcessMemory.restype = wt.BOOL
kernel32.ReadProcessMemory.argtypes = [
    wt.HANDLE,
    wt.LPCVOID,
    wt.LPVOID,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
kernel32.ReadProcessMemory.restype = wt.BOOL
kernel32.CreateRemoteThread.argtypes = [
    wt.HANDLE,
    wt.LPVOID,
    ctypes.c_size_t,
    wt.LPVOID,
    wt.LPVOID,
    wt.DWORD,
    ctypes.POINTER(wt.DWORD),
]
kernel32.CreateRemoteThread.restype = wt.HANDLE
kernel32.WaitForSingleObject.argtypes = [wt.HANDLE, wt.DWORD]
kernel32.WaitForSingleObject.restype = wt.DWORD
kernel32.GetExitCodeThread.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
kernel32.GetExitCodeThread.restype = wt.BOOL
kernel32.CloseHandle.argtypes = [wt.HANDLE]
kernel32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
kernel32.CreateToolhelp32Snapshot.restype = wt.HANDLE
kernel32.Module32FirstW.argtypes = [wt.HANDLE, ctypes.POINTER(MODULEENTRY32W)]
kernel32.Module32FirstW.restype = wt.BOOL
kernel32.Module32NextW.argtypes = [wt.HANDLE, ctypes.POINTER(MODULEENTRY32W)]
kernel32.Module32NextW.restype = wt.BOOL


def winerr() -> OSError:
    return ctypes.WinError(ctypes.get_last_error())


def read_process(handle: int, address: int, size: int) -> bytes:
    buf = ctypes.create_string_buffer(size)
    got = ctypes.c_size_t()
    ok = kernel32.ReadProcessMemory(
        handle, ctypes.c_void_p(address), buf, size, ctypes.byref(got)
    )
    if not ok:
        raise winerr()
    return buf.raw[: got.value]


def write_process(handle: int, address: int, data: bytes) -> None:
    got = ctypes.c_size_t()
    ok = kernel32.WriteProcessMemory(
        handle,
        ctypes.c_void_p(address),
        ctypes.c_char_p(data),
        len(data),
        ctypes.byref(got),
    )
    if not ok or got.value != len(data):
        raise winerr()


def module_base(pid: int, module_suffix: str = "BloodStrike.exe") -> int:
    snapshot = kernel32.CreateToolhelp32Snapshot(
        TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid
    )
    if snapshot == wt.HANDLE(-1).value:
        raise winerr()
    try:
        entry = MODULEENTRY32W()
        entry.dwSize = ctypes.sizeof(entry)
        ok = kernel32.Module32FirstW(snapshot, ctypes.byref(entry))
        while ok:
            if entry.szModule.lower().endswith(module_suffix.lower()):
                return ctypes.addressof(entry.modBaseAddr.contents)
            ok = kernel32.Module32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)
    raise RuntimeError(f"module not found: {module_suffix}")


class Asm:
    def __init__(self) -> None:
        self.buf = bytearray()
        self.labels: dict[str, int] = {}
        self.fixups: list[tuple[int, str]] = []

    def emit(self, data: bytes) -> None:
        self.buf.extend(data)

    def label(self, name: str) -> None:
        self.labels[name] = len(self.buf)

    def rel32(self, label: str) -> None:
        pos = len(self.buf)
        self.buf.extend(b"\x00\x00\x00\x00")
        self.fixups.append((pos, label))

    def finish(self) -> bytes:
        for pos, label in self.fixups:
            target = self.labels[label]
            rel = target - (pos + 4)
            self.buf[pos : pos + 4] = struct.pack("<i", rel)
        return bytes(self.buf)


def build_shellcode(
    module: str, image_base: int, sys_path: str | None
) -> tuple[bytes, dict[str, int]]:
    ensure = image_base + (PY_GILSTATE_ENSURE_VA - PREFERRED_IMAGE_BASE)
    release = image_base + (PY_GILSTATE_RELEASE_VA - PREFERRED_IMAGE_BASE)
    import_module = image_base + (PY_IMPORT_IMPORTMODULE_VA - PREFERRED_IMAGE_BASE)
    set_path = image_base + (PY_SYS_SETPATH_VA - PREFERRED_IMAGE_BASE)

    asm = Asm()
    asm.emit(b"\x48\x83\xec\x28")  # sub rsp, 0x28
    asm.emit(b"\x48\xb8" + struct.pack("<Q", ensure))
    asm.emit(b"\xff\xd0")  # call rax
    asm.emit(b"\x89\x05")
    asm.rel32("state")
    if sys_path:
        asm.emit(b"\x48\x8d\x0d")
        asm.rel32("sys_path")
        asm.emit(b"\x48\xb8" + struct.pack("<Q", set_path))
        asm.emit(b"\xff\xd0")
    asm.emit(b"\x48\x8d\x0d")
    asm.rel32("module_name")
    asm.emit(b"\x48\xb8" + struct.pack("<Q", import_module))
    asm.emit(b"\xff\xd0")
    asm.emit(b"\x48\x89\x05")
    asm.rel32("result")
    asm.emit(b"\x8b\x0d")
    asm.rel32("state")
    asm.emit(b"\x48\xb8" + struct.pack("<Q", release))
    asm.emit(b"\xff\xd0")
    asm.emit(b"\x48\x83\xc4\x28")
    asm.emit(b"\xc3")
    while len(asm.buf) % 8:
        asm.emit(b"\x90")
    asm.label("state")
    asm.emit(b"\x00\x00\x00\x00")
    asm.emit(b"\x00\x00\x00\x00")
    asm.label("result")
    asm.emit(b"\x00" * 8)
    asm.label("module_name")
    asm.emit(module.encode("ascii") + b"\x00")
    if sys_path:
        while len(asm.buf) % 2:
            asm.emit(b"\x00")
        asm.label("sys_path")
        asm.emit(sys_path.encode("utf-16le") + b"\x00\x00")
    return asm.finish(), {
        "ensure": ensure,
        "release": release,
        "import_module": import_module,
        "set_path": set_path,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--module", default="ctf_esp")
    parser.add_argument("--base", type=lambda value: int(value, 0), default=None)
    parser.add_argument("--out", type=Path, default=Path("remote-py-import.json"))
    parser.add_argument("--sys-path", default=None)
    parser.add_argument("--timeout-ms", type=int, default=8000)
    args = parser.parse_args()

    access = (
        PROCESS_CREATE_THREAD
        | PROCESS_QUERY_INFORMATION
        | PROCESS_VM_OPERATION
        | PROCESS_VM_WRITE
        | PROCESS_VM_READ
    )
    handle = kernel32.OpenProcess(access, False, args.pid)
    if not handle:
        raise winerr()
    remote = None
    thread = None
    report = {"pid": args.pid, "module": args.module, "started": time.time()}
    try:
        base = args.base if args.base is not None else module_base(args.pid)
        shellcode, addresses = build_shellcode(args.module, base, args.sys_path)
        remote = kernel32.VirtualAllocEx(
            handle, None, len(shellcode), MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE
        )
        if not remote:
            raise winerr()
        remote_addr = int(remote)
        write_process(handle, remote_addr, shellcode)
        tid = wt.DWORD()
        thread = kernel32.CreateRemoteThread(
            handle, None, 0, ctypes.c_void_p(remote_addr), None, 0, ctypes.byref(tid)
        )
        if not thread:
            raise winerr()
        wait = kernel32.WaitForSingleObject(thread, args.timeout_ms)
        exit_code = wt.DWORD()
        kernel32.GetExitCodeThread(thread, ctypes.byref(exit_code))
        state_off = shellcode.index(b"\x00" * 16)
        raw_state_result = read_process(handle, remote_addr + state_off, 16)
        state = struct.unpack_from("<I", raw_state_result, 0)[0]
        result = struct.unpack_from("<Q", raw_state_result, 8)[0]
        report.update(
            {
                "image_base": f"0x{base:x}",
                "remote_code": f"0x{remote_addr:x}",
                "thread_id": int(tid.value),
                "wait": int(wait),
                "wait_name": "timeout" if wait == WAIT_TIMEOUT else "signaled" if wait == WAIT_OBJECT_0 else "other",
                "exit_code": int(exit_code.value),
                "state": int(state),
                "result": f"0x{result:x}",
                "addresses": {key: f"0x{value:x}" for key, value in addresses.items()},
                "sys_path_set": args.sys_path,
            }
        )
    finally:
        if thread:
            kernel32.CloseHandle(thread)
        if remote:
            kernel32.VirtualFreeEx(handle, remote, 0, MEM_RELEASE)
        kernel32.CloseHandle(handle)

    report["finished"] = time.time()
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
