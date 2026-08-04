open(r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\ctf_min_imported.log", "a").write("imported\n")


def Entry(*args):
    open(r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\ctf_min_imported.log", "a").write(
        f"Entry {args!r}\n"
    )
    return True
