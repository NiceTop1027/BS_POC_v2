"""Harmless Patch-import probe for the local CTF instance.

Its only effect is writing a marker under this task directory.  It does not
inspect target memory, modify game data, or make network requests.
"""

with open(
    r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\ctf-import.marker",
    "w",
    encoding="utf-8",
) as marker:
    marker.write("ctf_marker imported\n")
