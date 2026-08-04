out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_source_extract_probe.log"
dump = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\dumped_sources_probe"


def log(s):
    open(out, "a", encoding="utf-8").write(str(s) + "\n")


def save(label, data):
    try:
        import os

        os.makedirs(dump, exist_ok=True)
        if isinstance(data, str):
            b = data.encode("utf-8", "replace")
        else:
            b = bytes(data)
        path = dump + "\\" + label.replace("/", "_").replace("\\", "_").replace(":", "") + ".bin"
        open(path, "wb").write(b)
        log("SAVE " + label + " len=" + str(len(b)) + " head=" + repr(b[:80]))
    except BaseException as e:
        log("SAVE FAIL " + label + " " + repr(e))


log("BEGIN")
try:
    import MImporter

    paths = [
        "engine/common/EntityManager.py",
        "Script/Python/engine/common/EntityManager.py",
        "Package/Script/Python/engine/common/EntityManager.py",
        "gclient/entitylist.py",
        "Script/Python/gclient/entitylist.py",
    ]
    for p in paths:
        for fname, func in (
            ("open_pkg", MImporter.open_file_data_in_package),
            ("open_patch", MImporter.open_file_data_in_patch),
            ("exists_pkg", MImporter.path_exists_in_package),
            ("exists_patch", MImporter.path_exists_in_patch),
        ):
            try:
                r = func(p)
                log(fname + " " + p + " => " + repr(r if isinstance(r, (bool, int, type(None))) else type(r)))
                if fname.startswith("open") and r:
                    save(fname + "_" + p, r)
            except BaseException as e:
                log(fname + " " + p + " FAIL " + repr(e))
except BaseException as e:
    log("MImporter block fail " + repr(e))

try:
    import common.EntityManager as em

    loader = getattr(em, "__loader__", None)
    for args in (
        ("common.EntityManager",),
        ("engine/common/EntityManager.py",),
        ("C:\\Program Files (x86)\\bloodstrike\\Package\\Script\\Python/engine/common/EntityManager.py",),
    ):
        for meth in ("get_module_data", "get_relpath", "get_relpath_with_path"):
            try:
                f = getattr(loader, meth)
                r = f(*args)
                log("loader." + meth + repr(args) + " => " + repr(r if isinstance(r, (str, bool, int, type(None))) else type(r)))
                if meth == "get_module_data" and r:
                    save("loader_" + meth + "_" + args[0], r)
            except BaseException as e:
                log("loader." + meth + repr(args) + " FAIL " + repr(e))
except BaseException as e:
    log("loader block fail " + repr(e))

log("END")
