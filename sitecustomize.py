"""Harmless probe for the embedded Python startup path.

If the CTF game imports this module through PYTHONPATH, it records only that
fact in the task folder.  It does not inspect or modify target memory.
"""

from pathlib import Path

Path(r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\python-startup.marker").write_text(
    "sitecustomize imported\n", encoding="utf-8"
)
