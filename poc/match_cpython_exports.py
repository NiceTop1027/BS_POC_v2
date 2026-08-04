from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path

import pefile


DEFAULT_NAMES = [
    "PyRun_SimpleStringFlags",
    "PyRun_StringFlags",
    "Py_CompileStringObject",
    "PyObject_Call",
    "PyObject_CallObject",
    "PyObject_GetAttr",
    "PyObject_GetAttrString",
    "PyUnicode_FromString",
    "PyTuple_New",
    "PyTuple_SetItem",
    "PyTuple_Pack",
    "PyDict_New",
    "PyDict_SetItemString",
    "PyModule_GetDict",
    "PyImport_ImportModule",
    "PyGILState_Ensure",
    "PyGILState_Release",
]


def section_containing(pe: pefile.PE, rva: int):
    for section in pe.sections:
        start = section.VirtualAddress
        end = start + max(section.Misc_VirtualSize, section.SizeOfRawData)
        if start <= rva < end:
            return section
    return None


def read_rva(pe: pefile.PE, rva: int, size: int) -> bytes:
    offset = pe.get_offset_from_rva(rva)
    return pe.__data__[offset : offset + size]


def pdata_ranges(pe: pefile.PE) -> dict[int, int]:
    out: dict[int, int] = {}
    try:
        entries = pe.DIRECTORY_ENTRY_EXCEPTION
    except AttributeError:
        return out
    for entry in entries:
        begin = int(entry.struct.BeginAddress)
        end = int(entry.struct.EndAddress)
        if end > begin:
            out[begin] = end
    return out


def exports(pe: pefile.PE) -> dict[str, int]:
    out: dict[str, int] = {}
    for symbol in pe.DIRECTORY_ENTRY_EXPORT.symbols:
        if symbol.name:
            out[symbol.name.decode("ascii", "ignore")] = int(symbol.address)
    return out


def find_target_section(pe: pefile.PE):
    text = next((s for s in pe.sections if s.Name.rstrip(b"\0") == b".text"), None)
    if text is not None:
        return text
    return max(pe.sections, key=lambda s: s.SizeOfRawData)


def score_function(
    src_body: bytes,
    target_blob: bytes,
    target_section_rva: int,
    chunk_size: int,
    max_scan: int,
) -> list[tuple[int, int, list[int]]]:
    body = src_body[:max_scan]
    candidates: Counter[int] = Counter()
    offsets_by_start: dict[int, list[int]] = defaultdict(list)
    seen_chunks: set[bytes] = set()

    for off in range(0, max(0, len(body) - chunk_size + 1), 4):
        chunk = body[off : off + chunk_size]
        if chunk in seen_chunks:
            continue
        seen_chunks.add(chunk)
        if chunk.count(0) > chunk_size // 2 or chunk.count(0xCC) > chunk_size // 2:
            continue

        pos = target_blob.find(chunk)
        while pos != -1:
            start_rva = target_section_rva + pos - off
            candidates[start_rva] += 1
            offsets_by_start[start_rva].append(off)
            pos = target_blob.find(chunk, pos + 1)

    return [
        (start_rva, score, offsets_by_start[start_rva])
        for start_rva, score in candidates.most_common(8)
        if score > 0
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dll", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--names", nargs="*", default=DEFAULT_NAMES)
    parser.add_argument("--chunk-size", type=int, default=24)
    parser.add_argument("--max-scan", type=int, default=512)
    args = parser.parse_args()

    src = pefile.PE(str(args.dll), fast_load=False)
    dst = pefile.PE(str(args.target), fast_load=False)
    dst_text = find_target_section(dst)
    dst_blob = dst_text.get_data()
    dst_base = int(dst.OPTIONAL_HEADER.ImageBase)

    src_exports = exports(src)
    src_pdata = pdata_ranges(src)
    section_name = dst_text.Name.rstrip(b"\0")
    print(f"target_text={section_name!r} target_base={dst_base:#x}")

    for name in args.names:
        rva = src_exports.get(name)
        if rva is None:
            print(f"{name}: missing export")
            continue
        end = src_pdata.get(rva)
        if end is None:
            sec = section_containing(src, rva)
            if sec is None:
                print(f"{name}: no section")
                continue
            end = min(sec.VirtualAddress + sec.SizeOfRawData, rva + args.max_scan)
        body = read_rva(src, rva, min(end - rva, args.max_scan))
        hits = score_function(
            body,
            dst_blob,
            int(dst_text.VirtualAddress),
            args.chunk_size,
            args.max_scan,
        )
        if not hits:
            print(f"{name}: no raw chunk match")
            continue
        formatted = []
        for start_rva, score, offsets in hits[:4]:
            formatted.append(
                f"va={dst_base + start_rva:#x} rva={start_rva:#x} score={score} offs={offsets[:8]}"
            )
        print(f"{name}: " + " | ".join(formatted))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
