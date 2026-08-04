import inspect as _ctf_mcap_inspect
import time as _ctf_mcap_time
import traceback as _ctf_mcap_traceback


_ctf_mcap_log_path = r"C:\Users\mista\Documents\Bugbounty\bloodstrike-launcher\poc\py_mcamera_capture_probe.log"


def _ctf_mcap_write(value):
    with open(_ctf_mcap_log_path, "a", encoding="utf-8") as _ctf_mcap_handle:
        _ctf_mcap_handle.write(str(value) + "\n")


def _ctf_mcap_short(value, limit=2000):
    try:
        return repr(value)[:limit]
    except Exception:
        return "<repr failed>"


def _ctf_mcap_show(label, value):
    _ctf_mcap_write(label + " type=" + _ctf_mcap_short(type(value)) + " repr=" + _ctf_mcap_short(value))
    if value is None:
        return
    try:
        for _ctf_mcap_name in dir(value):
            if _ctf_mcap_name.startswith("__"):
                continue
            try:
                _ctf_mcap_child = getattr(value, _ctf_mcap_name)
                if not callable(_ctf_mcap_child):
                    _ctf_mcap_write(label + "." + _ctf_mcap_name + "=" + _ctf_mcap_short(_ctf_mcap_child))
            except Exception:
                pass
    except Exception:
        pass


def _ctf_mcap_call(label, function, *args):
    try:
        _ctf_mcap_value = function(*args)
        _ctf_mcap_show(label, _ctf_mcap_value)
        return _ctf_mcap_value
    except Exception as exc:
        _ctf_mcap_write(label + " FAIL " + repr(exc))
        return None


def _ctf_mcap_run():
    _ctf_mcap_write("BEGIN " + str(_ctf_mcap_time.time()))
    try:
        import MCamera as _ctf_mcap_camera
        import MUI as _ctf_mcap_ui
        _ctf_mcap_write("MUI.GetScreenSize=" + _ctf_mcap_short(_ctf_mcap_call("GetScreenSize", _ctf_mcap_ui.GetScreenSize)))
        for _ctf_mcap_name in ("CaptureFrame", "ApplyFrame"):
            _ctf_mcap_function = getattr(_ctf_mcap_camera, _ctf_mcap_name)
            try:
                _ctf_mcap_write(_ctf_mcap_name + ".signature=" + _ctf_mcap_short(_ctf_mcap_inspect.signature(_ctf_mcap_function)))
            except Exception as exc:
                _ctf_mcap_write(_ctf_mcap_name + ".signature FAIL " + repr(exc))
        _ctf_mcap_frame = _ctf_mcap_camera.CameraFrame()
        for _ctf_mcap_args in ((), (0,), (1,), (_ctf_mcap_frame,)):
            _ctf_mcap_call("CaptureFrame" + repr(_ctf_mcap_args), _ctf_mcap_camera.CaptureFrame, *_ctf_mcap_args)
            _ctf_mcap_show("frame after " + repr(_ctf_mcap_args), _ctf_mcap_frame)
    except Exception:
        _ctf_mcap_write("EXC\n" + _ctf_mcap_traceback.format_exc())
    finally:
        _ctf_mcap_write("END")


_ctf_mcap_run()
