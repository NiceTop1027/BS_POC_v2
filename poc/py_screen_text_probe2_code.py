import time
import traceback

LOG = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_screen_text_probe2.log"


def log(message):
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def v2(x, y):
    import MType
    return MType.Vector2(float(x), float(y))


def main():
    log("BEGIN " + str(time.time()))
    try:
        import MUI
        candidates = [
            ("ctf_hud_probe_1", "ESP HUD 1", v2(32, 150), 0, 20, 0),
            ("ctf_hud_probe_2", "ESP HUD 2", v2(32, 180), 0, 20.0, 0),
            ("ctf_hud_probe_3", "ESP HUD 3", v2(32, 210), 20, 0, 0),
            ("ctf_hud_probe_4", "ESP HUD 4", v2(32, 240), 20, 0, 1),
            ("ctf_hud_probe_5", "ESP HUD 5", v2(32, 270), 0x00FF00, 20, 0),
            ("ctf_hud_probe_6", "ESP HUD 6", v2(32, 300), 0, 0x00FF00, 20),
            ("ctf_hud_probe_7", "ESP HUD 7", v2(32, 330), 0, 0, 20),
            ("ESP HUD 8", v2(32, 360), 0, 20, 0, "ctf_hud_probe_8"),
            (v2(32, 390), "ESP HUD 9", 0, 20, 0, "ctf_hud_probe_9"),
        ]
        for args in candidates:
            try:
                res = MUI.CreateScreenText(*args)
                log(f"CreateScreenText{args!r} => OK {res!r}")
                for first in (res, args[0]):
                    try:
                        up = MUI.UpdateScreenText(first, v2(52, 150))
                        log(f"UpdateScreenText({first!r}, vec2) => OK {up!r}")
                    except Exception as exc:
                        log(f"UpdateScreenText({first!r}, vec2) FAIL {exc!r}")
            except Exception as exc:
                log(f"CreateScreenText{args!r} => FAIL {exc!r}")
    except Exception:
        log("EXC\n" + traceback.format_exc())
    finally:
        log("END")


main()
