from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("entry")
    args = parser.parse_args()

    items = json.loads(args.manifest.read_text(encoding="utf-8"))
    if args.entry not in items:
        items.append(args.entry)
        args.manifest.write_text(
            json.dumps(items, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        print(f"added {args.entry}")
    else:
        print(f"present {args.entry}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
