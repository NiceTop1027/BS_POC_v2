import time
import traceback

LOG = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_screen_text_probe3.log"


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def v2(x, y):
    import MType
    return MType.Vector2(float(x), float(y))


def v3(x, y, z):
    import MType
    return MType.Vector3(float(x), float(y), float(z))


def main():
    log("BEGIN " + str(time.time()))
    try:
        import MUI
        green = v3(0.1, 1.0, 0.2)
        white = v3(1.0, 1.0, 1.0)
        candidates = [
            ("ctf_hud_probe_10", "ESP HUD 10", v2(32, 145), 0, green, 20),
            ("ctf_hud_probe_11", "ESP HUD 11", v2(32, 175), 0, green, 20.0),
            ("ctf_hud_probe_12", "ESP HUD 12", v2(32, 205), 0, green, True),
            ("ctf_hud_probe_13", "ESP HUD 13", v2(32, 235), 20, green, 0),
            ("ctf_hud_probe_14", "ESP HUD 14", v2(32, 265), 20, green, 1),
            ("ctf_hud_probe_15", "ESP HUD 15", v2(32, 295), 0, green, white),
            ("ctf_hud_probe_16", "ESP HUD 16", v2(32, 325), 1, green, 18),
        ]
        for args in candidates:
            try:
                res = MUI.CreateScreenText(*args)
                log(f"CreateScreenText{args!r} => OK {res!r}")
                try:
                    up = MUI.UpdateScreenText(res, v2(60, 145))
                    log(f"UpdateScreenText({res!r}, vec2) => OK {up!r}")
                except Exception as exc:
                    log(f"UpdateScreenText({res!r}, vec2) FAIL {exc!r}")
            except Exception as exc:
                log(f"CreateScreenText{args!r} => FAIL {exc!r}")
    except Exception:
        log("EXC\n" + traceback.format_exc())
    finally:
        log("END")


main()
