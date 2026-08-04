#include <windows.h>

#include <fstream>

namespace {
std::ofstream g_log("C:\\Users\\mista\\Documents\\Bugbounty\\bloodstrike-launcher\\poc\\raw_input_sendinput_probe.log");
bool g_sent = false;

LRESULT CALLBACK WindowProc(HWND hwnd, UINT message, WPARAM wparam, LPARAM lparam) {
    switch (message) {
        case WM_CREATE: {
            RAWINPUTDEVICE device = {};
            device.usUsagePage = 0x01;
            device.usUsage = 0x02;
            device.dwFlags = RIDEV_INPUTSINK;
            device.hwndTarget = hwnd;
            g_log << "registered=" << RegisterRawInputDevices(&device, 1, sizeof(device)) << "\n";
            SetTimer(hwnd, 1, 250, nullptr);
            return 0;
        }
        case WM_TIMER:
            if (wparam == 1 && !g_sent) {
                g_sent = true;
                INPUT input = {};
                input.type = INPUT_MOUSE;
                input.mi.dx = 17;
                input.mi.dy = -11;
                input.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_MOVE_NOCOALESCE;
                g_log << "send=" << SendInput(1, &input, sizeof(input)) << "\n";
                SetTimer(hwnd, 2, 350, nullptr);
            } else if (wparam == 2) {
                g_log.flush();
                DestroyWindow(hwnd);
            }
            return 0;
        case WM_INPUT: {
            UINT bytes = 0;
            GetRawInputData(reinterpret_cast<HRAWINPUT>(lparam), RID_INPUT, nullptr, &bytes,
                            sizeof(RAWINPUTHEADER));
            if (bytes >= sizeof(RAWINPUT)) {
                RAWINPUT input = {};
                const UINT read = GetRawInputData(reinterpret_cast<HRAWINPUT>(lparam), RID_INPUT,
                                                  &input, &bytes, sizeof(RAWINPUTHEADER));
                if (read == bytes && input.header.dwType == RIM_TYPEMOUSE) {
                    g_log << "raw=" << input.data.mouse.lLastX << ',' << input.data.mouse.lLastY << "\n";
                }
            }
            return 0;
        }
        case WM_DESTROY:
            PostQuitMessage(0);
            return 0;
        default:
            return DefWindowProcW(hwnd, message, wparam, lparam);
    }
}
}  // namespace

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int) {
    WNDCLASSW windowClass = {};
    windowClass.hInstance = instance;
    windowClass.lpfnWndProc = WindowProc;
    windowClass.lpszClassName = L"RawInputSendInputProbe";
    RegisterClassW(&windowClass);
    HWND window = CreateWindowExW(0, windowClass.lpszClassName, L"", WS_OVERLAPPEDWINDOW,
                                  0, 0, 1, 1, nullptr, nullptr, instance, nullptr);
    ShowWindow(window, SW_HIDE);
    MSG message = {};
    while (GetMessageW(&message, nullptr, 0, 0) > 0) {
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }
    return 0;
}
