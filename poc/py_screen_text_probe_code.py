import time
import traceback

LOG = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_screen_text_probe.log"


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def make_vec2(x, y):
    import MType
    v = MType.Vector2()
    v.x = float(x)
    v.y = float(y)
    return v


def make_vec3(x, y, z):
    import MType
    v = MType.Vector3()
    v.x = float(x)
    v.y = float(y)
    v.z = float(z)
    return v


def main():
    log("BEGIN " + str(time.time()))
    try:
        import MUI
        import MType
        log(f"Vector2 ctor={MType.Vector2!r} Vector3 ctor={MType.Vector3!r}")
        for cls, args in (
            (MType.Vector2, (32, 140)),
            (MType.Vector3, (0.1, 1.0, 0.2)),
        ):
            for a in ((), args):
                try:
                    log(f"{cls.__name__}{a!r} => {cls(*a)!r}")
                except Exception as exc:
                    log(f"{cls.__name__}{a!r} FAIL {exc!r}")

        pos = make_vec2(32, 160)
        color = make_vec3(0.1, 1.0, 0.2)
        black = make_vec3(0.0, 0.0, 0.0)
        candidates = [
            ("ctf_screen_probe", "ESP HUD TEST", pos, color, 20.0, 0),
            ("ctf_screen_probe", "ESP HUD TEST", pos, color, 20, True),
            ("ESP HUD TEST", pos, color, 20.0, 0, True),
            ("ESP HUD TEST", "Arial", pos, color, 20.0, 0),
            ("ctf_screen_probe", "ESP HUD TEST", "Arial", pos, color, 20.0),
            ("ctf_screen_probe", pos, "ESP HUD TEST", color, 20.0, 0),
            ("ctf_screen_probe", "ESP HUD TEST", pos, color, black, 20.0),
            ("ctf_screen_probe", "ESP HUD TEST", pos, 20.0, color, black),
            ("ctf_screen_probe", "ESP HUD TEST", 32.0, 160.0, color, 20.0),
            ("ESP HUD TEST", 32.0, 160.0, 0.1, 1.0, 0.2),
        ]
        for args in candidates:
            try:
                res = MUI.CreateScreenText(*args)
                log(f"CreateScreenText{args!r} => OK {res!r}")
                try:
                    up = MUI.UpdateScreenText(res, make_vec2(32, 190))
                    log(f"UpdateScreenText({res!r}, vec2) => {up!r}")
                except Exception as exc:
                    log(f"UpdateScreenText res FAIL {exc!r}")
            except Exception as exc:
                log(f"CreateScreenText{args!r} => FAIL {exc!r}")
    except Exception:
        log("EXC\n" + traceback.format_exc())
    finally:
        log("END")


main()
