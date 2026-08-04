"""Memory-patched ESP launcher for the isolated BloodStrike CTF instance.

The previous visible overlay PoC did not touch the game process.  This launcher
does: it creates BloodStrike.exe suspended, patches the embedded
MReloadImporter selector byte in the target process with WriteProcessMemory,
then resumes the game with ctf_esp.py as the Python entry module.

Scope: local CTF instance only.
"""

from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


GAME_ROOT = Path(r"C:\Program Files (x86)\bloodstrike")
GAME_EXE = GAME_ROOT / r"Engine\Binaries\Win64\BloodStrike.exe"
GAME_WORKDIR = GAME_EXE.parent

EXPECTED_SHA256 = "62AF2CDD3ABECB6A77A848ACD58F3E1F680950926B164B6C42EDEF9BF791E908"

PREFERRED_IMAGE_BASE = 0x140000000
RELOAD_IMPORTER_SELECTOR_VA = 0x148D5DBB8
RELOAD_IMPORTER_SELECTOR_RVA = RELOAD_IMPORTER_SELECTOR_VA - PREFERRED_IMAGE_BASE

CREATE_SUSPENDED = 0x00000004
PROCESS_BASIC_INFORMATION = 0
PAGE_READWRITE = 0x04


class STARTUPINFO(ctypes.Structure):
    _fields_ = [
        ("cb", wt.DWORD),
        ("lpReserved", wt.LPWSTR),
        ("lpDesktop", wt.LPWSTR),
        ("lpTitle", wt.LPWSTR),
        ("dwX", wt.DWORD),
        ("dwY", wt.DWORD),
        ("dwXSize", wt.DWORD),
        ("dwYSize", wt.DWORD),
        ("dwXCountChars", wt.DWORD),
        ("dwYCountChars", wt.DWORD),
        ("dwFillAttribute", wt.DWORD),
        ("dwFlags", wt.DWORD),
        ("wShowWindow", wt.WORD),
        ("cbReserved2", wt.WORD),
        ("lpReserved2", ctypes.POINTER(ctypes.c_byte)),
        ("hStdInput", wt.HANDLE),
        ("hStdOutput", wt.HANDLE),
        ("hStdError", wt.HANDLE),
    ]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wt.HANDLE),
        ("hThread", wt.HANDLE),
        ("dwProcessId", wt.DWORD),
        ("dwThreadId", wt.DWORD),
    ]


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
shell32 = ctypes.WinDLL("shell32", use_last_error=True)

kernel32.CreateProcessW.argtypes = [
    wt.LPCWSTR,
    wt.LPWSTR,
    wt.LPVOID,
    wt.LPVOID,
    wt.BOOL,
    wt.DWORD,
    wt.LPVOID,
    wt.LPCWSTR,
    ctypes.POINTER(STARTUPINFO),
    ctypes.POINTER(PROCESS_INFORMATION),
]
kernel32.CreateProcessW.restype = wt.BOOL
kernel32.ReadProcessMemory.argtypes = [
    wt.HANDLE,
    wt.LPCVOID,
    wt.LPVOID,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
kernel32.ReadProcessMemory.restype = wt.BOOL
kernel32.WriteProcessMemory.argtypes = [
    wt.HANDLE,
    wt.LPVOID,
    wt.LPCVOID,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
kernel32.WriteProcessMemory.restype = wt.BOOL
kernel32.VirtualProtectEx.argtypes = [
    wt.HANDLE,
    wt.LPVOID,
    ctypes.c_size_t,
    wt.DWORD,
    ctypes.POINTER(wt.DWORD),
]
kernel32.VirtualProtectEx.restype = wt.BOOL
kernel32.ResumeThread.argtypes = [wt.HANDLE]
kernel32.ResumeThread.restype = wt.DWORD
kernel32.TerminateProcess.argtypes = [wt.HANDLE, wt.UINT]
kernel32.CloseHandle.argtypes = [wt.HANDLE]
ntdll.NtQueryInformationProcess.argtypes = [
    wt.HANDLE,
    wt.ULONG,
    wt.LPVOID,
    wt.ULONG,
    ctypes.POINTER(wt.ULONG),
]
ntdll.NtQueryInformationProcess.restype = wt.LONG
shell32.IsUserAnAdmin.argtypes = []
shell32.IsUserAnAdmin.restype = wt.BOOL


def quote(value: Path | str) -> str:
    text = str(value)
    return '"' + text.replace('"', r'\"') + '"'


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def read_process(handle: int, address: int, size: int) -> bytes:
    buf = ctypes.create_string_buffer(size)
    got = ctypes.c_size_t()
    ok = kernel32.ReadProcessMemory(
        handle, ctypes.c_void_p(address), buf, size, ctypes.byref(got)
    )
    if not ok or got.value != size:
        raise ctypes.WinError(ctypes.get_last_error())
    return buf.raw[: got.value]


def write_process(handle: int, address: int, data: bytes) -> None:
    written = ctypes.c_size_t()
    ok = kernel32.WriteProcessMemory(
        handle,
        ctypes.c_void_p(address),
        ctypes.create_string_buffer(data),
        len(data),
        ctypes.byref(written),
    )
    if ok and written.value == len(data):
        return

    old_protect = wt.DWORD()
    if not kernel32.VirtualProtectEx(
        handle, ctypes.c_void_p(address), len(data), PAGE_READWRITE, ctypes.byref(old_protect)
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        written = ctypes.c_size_t()
        ok = kernel32.WriteProcessMemory(
            handle,
            ctypes.c_void_p(address),
            ctypes.create_string_buffer(data),
            len(data),
            ctypes.byref(written),
        )
        if not ok or written.value != len(data):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        ignored = wt.DWORD()
        kernel32.VirtualProtectEx(
            handle, ctypes.c_void_p(address), len(data), old_protect.value, ctypes.byref(ignored)
        )


def remote_image_base(process: int) -> int:
    pbi = ctypes.create_string_buffer(0x30)
    returned = wt.ULONG()
    status = ntdll.NtQueryInformationProcess(
        process,
        PROCESS_BASIC_INFORMATION,
        pbi,
        len(pbi),
        ctypes.byref(returned),
    )
    if status != 0:
        raise OSError(f"NtQueryInformationProcess(ProcessBasicInformation)={status:#x}")
    peb = int.from_bytes(pbi.raw[8:16], "little")
    return int.from_bytes(read_process(process, peb + 0x10, 8), "little")


def create_suspended(
    game_exe: Path, workdir: Path, arg_style: str, entry_module: str
) -> PROCESS_INFORMATION:
    if arg_style == "equals":
        args = [
            quote(game_exe),
            "--load=Python",
            "--start=Python",
            "--console",
            "--useReloadImporter",
            "--setImporterPath=Script/Python",
            "--python-args=innerdesktop",
            f"--python-entry={entry_module}",
            "--python-debug",
        ]
    else:
        args = [
            quote(game_exe),
            "--load",
            "Python",
            "--start",
            "Python",
            "--console",
            "--useReloadImporter",
            "--setImporterPath",
            "Script/Python",
            "--python-args",
            "innerdesktop",
            "--python-entry",
            entry_module,
            "--python-debug",
        ]
    cmdline = ctypes.create_unicode_buffer(" ".join(args))
    startup = STARTUPINFO()
    startup.cb = ctypes.sizeof(startup)
    proc = PROCESS_INFORMATION()
    ok = kernel32.CreateProcessW(
        str(game_exe),
        cmdline,
        None,
        None,
        False,
        CREATE_SUSPENDED,
        None,
        str(workdir),
        ctypes.byref(startup),
        ctypes.byref(proc),
    )
    if not ok:
        raise ctypes.WinError(ctypes.get_last_error())
    return proc


def stage_module(poc_root: Path, game_root: Path, aliases: list[str]) -> dict[str, object]:
    source = poc_root / "ctf_esp.py"
    destination_dirs = [
        game_root / r"LocalData\Patch\Script\Python",
        game_root / r"Package\Script\Python",
        game_root,
        game_root / r"Engine\Binaries\Win64",
    ]
    destinations = []
    for destination_dir in destination_dirs:
        destination_dir.mkdir(parents=True, exist_ok=True)
        for alias in ["ctf_esp", *aliases]:
            destination = destination_dir / f"{alias}.py"
            shutil.copy2(source, destination)
            destinations.append(str(destination))
    return {"source": str(source), "destinations": destinations}


def patch_packagefilelist(game_root: Path, module_names: list[str]) -> dict[str, object]:
    packagefilelist = game_root / r"LocalData\Patch\packagefilelist"
    backup = packagefilelist.with_name("packagefilelist.ctf_backup")
    entries = [f"Script/Python/{name}.py" for name in module_names]
    if not packagefilelist.exists():
        return {"path": str(packagefilelist), "error": "missing"}

    original = packagefilelist.read_text(encoding="utf-8")
    package_entries = json.loads(original)
    if not isinstance(package_entries, list):
        return {"path": str(packagefilelist), "error": "not a JSON list"}

    added = [entry for entry in entries if entry not in package_entries]
    if added:
        if not backup.exists():
            backup.write_text(original, encoding="utf-8")
        package_entries.extend(added)
        packagefilelist.write_text(
            json.dumps(package_entries, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

    return {
        "path": str(packagefilelist),
        "backup": str(backup),
        "added": added,
        "present": entries,
        "total": len(package_entries),
    }


def remove_logs(poc_root: Path) -> None:
    for name in (
        "ctf_esp_evidence.log",
        "mem_patch_esp_evidence.log",
        "cpp_esp_overlay_evidence.log",
    ):
        try:
            (poc_root / name).unlink()
        except FileNotFoundError:
            pass


def stop_existing() -> None:
    subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "Get-Process BloodStrike,esp_overlay -ErrorAction SilentlyContinue | Stop-Process -Force",
        ],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1.0)


def wait_for_log(path: Path, seconds: float) -> list[str]:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if path.exists() and path.stat().st_size:
            return path.read_text(encoding="utf-8", errors="replace").splitlines()[-40:]
        time.sleep(0.5)
    return []


def append_json_log(path: Path, record: dict[str, object]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, indent=2))
        handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--restart", action="store_true")
    parser.add_argument("--wait", type=float, default=20.0)
    parser.add_argument("--game-exe", type=Path, default=GAME_EXE)
    parser.add_argument("--arg-style", choices=("equals", "separated"), default="equals")
    parser.add_argument("--entry", default="ctf_esp")
    parser.add_argument("--no-overlay", action="store_true")
    parser.add_argument("--overlay-duration", type=int, default=180)
    parser.add_argument(
        "--alias",
        action="append",
        default=["MLauncher"],
        help="Also stage ctf_esp.py under this module name in the Python script roots.",
    )
    parser.add_argument("--no-packagefilelist", action="store_true")
    args = parser.parse_args()

    poc_root = Path(__file__).resolve().parent
    patch_log = poc_root / "mem_patch_esp_evidence.log"
    esp_log = poc_root / "ctf_esp_evidence.log"
    overlay_log = poc_root / "cpp_esp_overlay_evidence.log"
    overlay_exe = poc_root / r"cpp_overlay\mem_esp_overlay.exe"

    if not shell32.IsUserAnAdmin():
        raise SystemExit("Run elevated: BloodStrike.exe requires administrator integrity.")
    if not args.game_exe.exists():
        raise SystemExit(f"Game executable not found: {args.game_exe}")

    digest = sha256(args.game_exe)
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"Unexpected BloodStrike.exe SHA-256: {digest}")

    if args.restart:
        stop_existing()

    remove_logs(poc_root)
    staged = stage_module(poc_root, GAME_ROOT, args.alias)
    package_patch: dict[str, object] | None = None
    if not args.no_packagefilelist:
        package_patch = patch_packagefilelist(GAME_ROOT, ["ctf_esp", *args.alias])

    os.environ["MessiahLauncherInfo"] = r"\Device\HarddiskVolume2\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
    os.environ["MessiahAppName"] = "hyxd"

    proc = create_suspended(args.game_exe, args.game_exe.parent, args.arg_style, args.entry)
    patch_record: dict[str, object] = {
        "pid": int(proc.dwProcessId),
        "tid": int(proc.dwThreadId),
        "game_exe": str(args.game_exe),
        "sha256": digest,
        "staged_module": staged,
        "selector_rva": f"0x{RELOAD_IMPORTER_SELECTOR_RVA:x}",
        "arg_style": args.arg_style,
        "entry": args.entry,
        "aliases": args.alias,
        "packagefilelist": package_patch,
    }

    should_resume = False
    try:
        image_base = remote_image_base(proc.hProcess)
        selector = image_base + RELOAD_IMPORTER_SELECTOR_RVA
        before = read_process(proc.hProcess, selector, 1)[0]
        write_process(proc.hProcess, selector, b"\x01")
        after = read_process(proc.hProcess, selector, 1)[0]
        should_resume = after == 1
        patch_record.update(
            {
                "image_base": f"0x{image_base:x}",
                "selector_address": f"0x{selector:x}",
                "selector_before": before,
                "selector_after": after,
                "patched": should_resume,
            }
        )
        append_json_log(patch_log, patch_record)
    except Exception as exc:
        patch_record.update({"error": repr(exc)})
        append_json_log(patch_log, patch_record)
        kernel32.TerminateProcess(proc.hProcess, 1)
        raise
    finally:
        if should_resume:
            resume_result = kernel32.ResumeThread(proc.hThread)
            if resume_result == 0xFFFFFFFF:
                raise ctypes.WinError(ctypes.get_last_error())
        kernel32.CloseHandle(proc.hThread)
        kernel32.CloseHandle(proc.hProcess)

    if not args.no_overlay:
        if overlay_exe.exists():
            time.sleep(4.0)
            subprocess.Popen(
                [
                    str(overlay_exe),
                    f"--duration={args.overlay_duration}",
                    "--title=BloodStrike",
                    f"--log={overlay_log}",
                ],
                close_fds=True,
            )
            append_json_log(
                patch_log,
                {
                    "pid": int(proc.dwProcessId),
                    "overlay_started": True,
                    "overlay_exe": str(overlay_exe),
                    "overlay_log": str(overlay_log),
                },
            )
        else:
            append_json_log(
                patch_log,
                {
                    "pid": int(proc.dwProcessId),
                    "overlay_started": False,
                    "error": f"missing overlay: {overlay_exe}",
                },
            )

    print(json.dumps(patch_record, ensure_ascii=False, indent=2))
    tail = wait_for_log(esp_log, args.wait)
    if tail:
        print("\nctf_esp_evidence.log tail:")
        print("\n".join(tail))
    else:
        print(f"\nNo {esp_log.name} output within {args.wait:.1f}s.")
        print(f"Patch evidence: {patch_log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
