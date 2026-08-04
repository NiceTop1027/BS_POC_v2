import time
import traceback

LOG = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_vector_probe.log"


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def inspect_obj(label, obj):
    log(f"{label}: obj={obj!r} type={type(obj)!r} dir={[n for n in dir(obj) if not n.startswith('__')][:120]!r}")
    for name in ("x", "y", "z", "r", "g", "b", "a", "X", "Y", "Z"):
        try:
            log(f"{label}.{name}={getattr(obj, name)!r}")
        except Exception as exc:
            log(f"{label}.{name} FAIL {exc!r}")
    try:
        log(f"{label}[0]={obj[0]!r}")
    except Exception as exc:
        log(f"{label}[0] FAIL {exc!r}")


def try_set(label, obj):
    for style in ("attrs", "items"):
        try:
            if style == "attrs":
                setattr(obj, "x", 1.25)
                setattr(obj, "y", 2.5)
                if hasattr(obj, "z"):
                    setattr(obj, "z", 3.75)
            else:
                obj[0] = 1.25
                obj[1] = 2.5
                try:
                    obj[2] = 3.75
                except Exception:
                    pass
            log(f"{label} set {style} OK -> {obj!r}")
        except Exception as exc:
            log(f"{label} set {style} FAIL {exc!r}")


def main():
    log("BEGIN " + str(time.time()))
    try:
        import MUI
        p = MUI.HarmTextParam()
        for label, obj in (
            ("worldPos", p.worldPos),
            ("color", p.color),
            ("strokeColor", p.strokeColor),
            ("offset", p.offset),
        ):
            inspect_obj(label, obj)
            try_set(label, obj)
            inspect_obj(label + "_after", obj)

        for modname in ("MType", "MMath", "MVec", "MCore", "MUI"):
            try:
                mod = __import__(modname)
                names = [n for n in dir(mod) if any(t in n.lower() for t in ("vec", "vector", "color"))]
                log(f"MOD {modname} names={names[:120]!r}")
                for name in names[:40]:
                    obj = getattr(mod, name)
                    log(f"  {modname}.{name}={obj!r} type={type(obj)!r}")
            except Exception as exc:
                log(f"MOD {modname} FAIL {exc!r}")
    except Exception:
        log("EXC\n" + traceback.format_exc())
    finally:
        log("END")


main()
