"""Read-only check for the embedded Python importer's runtime selector.

The selector is an RVA in the analyzed CTF executable.  This tool only calls
OpenProcess/ReadProcessMemory and prints the byte; it never writes to the
target process.
"""

from __future__ import annotations

import argparse
import ctypes
import json

import live_probe


PREFERRED_IMAGE_BASE = 0x140000000
RELOAD_IMPORTER_SELECTOR_VA = 0x148D5DBB8
RELOAD_IMPORTER_SELECTOR_RVA = RELOAD_IMPORTER_SELECTOR_VA - PREFERRED_IMAGE_BASE


def integer(text: str) -> int:
    return int(text, 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--image-base", type=integer, required=True)
    args = parser.parse_args()

    handle = live_probe.kernel32.OpenProcess(
        live_probe.PROCESS_QUERY_INFORMATION | live_probe.PROCESS_VM_READ,
        False,
        args.pid,
    )
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        address = args.image_base + RELOAD_IMPORTER_SELECTOR_RVA
        raw = live_probe.read_at(handle, address, 1)
        if len(raw) != 1:
            raise RuntimeError(f"could not read selector at 0x{address:x}")
        enabled = raw[0] != 0
        print(
            json.dumps(
                {
                    "pid": args.pid,
                    "image_base": f"0x{args.image_base:x}",
                    "selector_address": f"0x{address:x}",
                    "selector_value": raw[0],
                    "reload_importer_selected": enabled,
                },
                indent=2,
            )
        )
    finally:
        live_probe.kernel32.CloseHandle(handle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
