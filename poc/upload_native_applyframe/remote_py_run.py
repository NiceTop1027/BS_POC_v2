"""Run a short Python code string inside the isolated BloodStrike CTF process."""

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
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010
MAX_MODULE_NAME32 = 255

PREFERRED_IMAGE_BASE = 0x140000000
PY_GILSTATE_ENSURE_VA = 0x142AA_FBE0
PY_GILSTATE_RELEASE_VA = 0x142AA_FCB0
PY_RUN_SIMPLESTRINGFLAGS_VA = 0x142A7_1900


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
            rel = self.labels[label] - (pos + 4)
            self.buf[pos : pos + 4] = struct.pack("<i", rel)
        return bytes(self.buf)


def build_shellcode(code: str, image_base: int, run_va: int) -> tuple[bytes, dict[str, int]]:
    ensure = image_base + (PY_GILSTATE_ENSURE_VA - PREFERRED_IMAGE_BASE)
    release = image_base + (PY_GILSTATE_RELEASE_VA - PREFERRED_IMAGE_BASE)
    run = image_base + (run_va - PREFERRED_IMAGE_BASE)

    asm = Asm()
    asm.emit(b"\x48\x83\xec\x28")  # sub rsp, 0x28
    asm.emit(b"\x48\xb8" + struct.pack("<Q", ensure))
    asm.emit(b"\xff\xd0")  # call rax
    asm.emit(b"\x89\x05")
    asm.rel32("state")
    asm.emit(b"\x48\x8d\x0d")
    asm.rel32("code")
    asm.emit(b"\x48\x31\xd2")  # rdx = NULL PyCompilerFlags*
    asm.emit(b"\x48\xb8" + struct.pack("<Q", run))
    asm.emit(b"\xff\xd0")  # call PyRun_SimpleStringFlags
    asm.emit(b"\x89\x05")
    asm.rel32("result")
    asm.emit(b"\x8b\x0d")
    asm.rel32("state")
    asm.emit(b"\x48\xb8" + struct.pack("<Q", release))
    asm.emit(b"\xff\xd0")
    asm.emit(b"\x8b\x05")
    asm.rel32("result")
    asm.emit(b"\x48\x83\xc4\x28")
    asm.emit(b"\xc3")
    while len(asm.buf) % 8:
        asm.emit(b"\x90")
    asm.label("state")
    asm.emit(b"\x00\x00\x00\x00")
    asm.label("result")
    asm.emit(b"\x00\x00\x00\x00")
    asm.label("code")
    asm.emit(code.encode("utf-8") + b"\x00")
    return asm.finish(), {"ensure": ensure, "release": release, "run": run}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--code", default=None)
    parser.add_argument("--code-file", type=Path, default=None)
    parser.add_argument("--base", type=lambda value: int(value, 0), default=None)
    parser.add_argument("--run-va", type=lambda value: int(value, 0), default=PY_RUN_SIMPLESTRINGFLAGS_VA)
    parser.add_argument("--out", type=Path, default=Path("remote-py-run.json"))
    parser.add_argument("--timeout-ms", type=int, default=8000)
    args = parser.parse_args()

    if args.code_file is not None:
        code_path = args.code_file.resolve()
        code = "__file__ = {!r}\n".format(str(code_path)) + code_path.read_text(encoding="utf-8")
    elif args.code is not None:
        code = args.code
    else:
        raise SystemExit("--code or --code-file is required")

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
    report = {"pid": args.pid, "started": time.time(), "run_va": hex(args.run_va)}
    try:
        base = args.base if args.base is not None else module_base(args.pid)
        shellcode, addresses = build_shellcode(code, base, args.run_va)
        remote = kernel32.VirtualAllocEx(
            handle, None, len(shellcode), MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE
        )
        if not remote:
            raise winerr()
        write_process(handle, int(remote), shellcode)
        tid = wt.DWORD()
        thread = kernel32.CreateRemoteThread(
            handle, None, 0, ctypes.c_void_p(int(remote)), None, 0, ctypes.byref(tid)
        )
        if not thread:
            raise winerr()
        wait = kernel32.WaitForSingleObject(thread, args.timeout_ms)
        exit_code = wt.DWORD(0)
        kernel32.GetExitCodeThread(thread, ctypes.byref(exit_code))
        data = read_process(handle, int(remote), len(shellcode))
        state_off = shellcode.index(b"\x00\x00\x00\x00", shellcode.index(b"\xc3") + 1)
        result_off = state_off + 4
        report.update(
            {
                "image_base": hex(base),
                "remote_code": hex(int(remote)),
                "thread_id": int(tid.value),
                "wait": int(wait),
                "exit_code": int(exit_code.value),
                "state": struct.unpack_from("<I", data, state_off)[0],
                "result": struct.unpack_from("<i", data, result_off)[0],
                "addresses": {key: hex(value) for key, value in addresses.items()},
                "finished": time.time(),
            }
        )
    finally:
        if thread:
            kernel32.CloseHandle(thread)
        if remote:
            kernel32.VirtualFreeEx(handle, remote, 0, MEM_RELEASE)
        kernel32.CloseHandle(handle)

    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
