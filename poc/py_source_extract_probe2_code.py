out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_source_extract_probe2.log"
dump = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\dumped_sources_probe2"


def log(s):
    open(out, "a", encoding="utf-8").write(str(s) + "\n")


def short(v, n=500):
    try:
        s = repr(v)
    except BaseException as e:
        s = "<repr failed %r>" % (e,)
    return s[:n] + ("..." if len(s) > n else "")


def save(label, data):
    try:
        import os

        os.makedirs(dump, exist_ok=True)
        b = data if isinstance(data, bytes) else bytes(data) if not isinstance(data, str) else data.encode("utf-8", "replace")
        path = dump + "\\" + label.replace("/", "_").replace("\\", "_").replace(":", "") + ".bin"
        open(path, "wb").write(b)
        log("SAVE " + label + " len=" + str(len(b)) + " head=" + repr(b[:100]))
    except BaseException as e:
        log("SAVE FAIL " + label + " " + repr(e))


log("BEGIN")
try:
    import MImporter, MLauncher

    for k in ("REALROOT", "LOGICROOT", "PATCHROOT", "SALT", "USE_CACHE", "FILL_CACHE"):
        try:
            log("MImporter." + k + "=" + short(getattr(MImporter, k)))
        except BaseException as e:
            log("MImporter." + k + " FAIL " + repr(e))
    for k in ("PKGROOT", "PATCHROOT"):
        try:
            log("MLauncher." + k + "=" + short(getattr(MLauncher, k)))
        except BaseException as e:
            log("MLauncher." + k + " FAIL " + repr(e))

    paths = [
        "engine/common/EntityManager.py",
        "Script/Python/engine/common/EntityManager.py",
        "Resources/Script/Python/engine/common/EntityManager.py",
        "gclient/entitylist.py",
        "Script/Python/gclient/entitylist.py",
    ]
    expanded = []
    for p in paths:
        expanded.append(p)
        try:
            expanded.append(MImporter.filename_encrypt(p))
        except BaseException as e:
            log("filename_encrypt " + p + " FAIL " + repr(e))
    for p in expanded:
        if not p:
            continue
        for fname, func in (
            ("MLauncher.OpenFileData", MLauncher.OpenFileData),
            ("MLauncher.OpenFileDataInPackage", MLauncher.OpenFileDataInPackage),
            ("MImporter.open_file_data_in_package", MImporter.open_file_data_in_package),
        ):
            try:
                r = func(p)
                log(fname + " " + short(p, 160) + " => " + short(r, 160))
                if r:
                    save(fname + "_" + str(p), r)
            except BaseException as e:
                log(fname + " " + short(p, 160) + " FAIL " + repr(e))
except BaseException as e:
    log("importer block fail " + repr(e))

try:
    import common.EntityManager as em

    loader = getattr(em, "__loader__", None)
    for obj in (em, getattr(em, "__spec__", None)):
        for meth in ("get_module_data", "get_module"):
            try:
                f = getattr(loader, meth)
                r = f(obj)
                log("loader." + meth + "(" + short(obj, 120) + ") => " + short(r, 200))
                if r:
                    save("loader_" + meth, r)
            except BaseException as e:
                log("loader." + meth + "(" + short(obj, 120) + ") FAIL " + repr(e))
except BaseException as e:
    log("loader block fail " + repr(e))
log("END")
