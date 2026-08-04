out = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_dump_sources.log"
root = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\dumped_sources"


def log(s):
    open(out, "a", encoding="utf-8").write(str(s) + "\n")


def safe_name(name):
    return name.replace(".", "_").replace("\\", "_").replace("/", "_") + ".py"


def dump(name):
    try:
        mod = __import__(name, fromlist=["*"])
    except BaseException as e:
        log("IMPORT " + name + " FAIL " + repr(e))
        return
    data = None
    source = None
    file_name = getattr(mod, "__file__", None)
    loader = getattr(mod, "__loader__", None)
    log("MOD " + name + " file=" + repr(file_name) + " loader=" + repr(loader))
    if loader is not None and file_name:
        try:
            data = loader.get_data(file_name)
            if isinstance(data, bytes):
                source = data.decode("utf-8", "replace")
            else:
                source = str(data)
            log("loader.get_data OK " + name + " len=" + str(len(source)))
        except BaseException as e:
            log("loader.get_data FAIL " + name + " " + repr(e))
    if source is None and file_name:
        try:
            source = open(file_name, "r", encoding="utf-8", errors="replace").read()
            log("open OK " + name + " len=" + str(len(source)))
        except BaseException as e:
            log("open FAIL " + name + " " + repr(e))
    if source is None:
        try:
            import inspect

            source = inspect.getsource(mod)
            log("inspect OK " + name + " len=" + str(len(source)))
        except BaseException as e:
            log("inspect FAIL " + name + " " + repr(e))
    if source is not None:
        try:
            import os

            os.makedirs(root, exist_ok=True)
            path = root + "\\" + safe_name(name)
            open(path, "w", encoding="utf-8").write(source)
            log("WROTE " + path)
        except BaseException as e:
            log("WRITE FAIL " + name + " " + repr(e))


log("BEGIN")
for n in (
    "common.EntityManager",
    "common.Entity",
    "common.EntityFactory",
    "client.ClientEntity",
    "gclient.entitylist",
    "gclient.gameplay.logic_base.entities.combat_avatar",
    "gclient.gameplay.logic_base.comps.comp_toplogo",
    "gclient.gameplay.logic_base.comps.comp_enemy_show_distance",
    "gclient.gameplay.logic_base.comps.fsm_avatar_toplogo",
):
    dump(n)
log("END")
