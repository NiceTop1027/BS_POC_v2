#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif

#include <windows.h>
#include <commctrl.h>
#include <shellapi.h>
#include <mmsystem.h>
#include <tlhelp32.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cwchar>
#include <fstream>
#include <iomanip>
#include <limits>
#include <sstream>
#include <string>
#include <vector>

namespace {

#ifndef CREATE_WAITABLE_TIMER_HIGH_RESOLUTION
#define CREATE_WAITABLE_TIMER_HIGH_RESOLUTION 0x00000002
#endif

constexpr UINT_PTR kTrackTimer = 1;
constexpr UINT kTrackIntervalMs = 8;
constexpr UINT kTrackMessage = WM_APP + 0x31;
constexpr int kToggleControlsHotkey = 1;
constexpr COLORREF kTransparentColor = RGB(0, 0, 0);
constexpr double kDefaultAimFovHeightFraction = 0.20;
constexpr double kAimWorldHeadHeightFraction = 0.84;
// Stop issuing integer mouse corrections for sub-pixel bone/camera noise.
constexpr double kAimDeadzonePixels = 2.50;
constexpr double kAimFineControlWindowPixels = 18.0;
constexpr double kAimFineGain = 0.58;
constexpr double kAimCoarseGain = 0.82;
// The exporter is sampled at 120 Hz.  One command per fresh sample prevents
// duplicate corrections from fighting each other between camera frames.
constexpr double kAimMinInputIntervalSeconds = 0.0085;
constexpr double kAimMaxRelativeVelocity = 14.0;
constexpr double kAimSnapshotLeadSeconds = 0.025;
constexpr double kAimMaxSnapshotLeadSeconds = 0.085;
constexpr double kAimMaxLeadMeters = 1.15;
constexpr double kAimMaxLeadScreenPixels = 72.0;
constexpr double kAimDirectRangeMeters = 12.0;
constexpr double kAimWorldAngleCorrectionDistanceMeters = 20.0;
constexpr double kAimMinProjectileSpeed = 10.0;
constexpr double kAimMaxProjectileSpeed = 10000.0;
constexpr double kAimMaxBallisticFlightSeconds = 3.0;
constexpr double kAimMaxBallisticHorizontalLeadMeters = 48.0;
constexpr double kAimMaxBallisticDropMeters = 48.0;
constexpr double kAimMaxBallisticLeadScreenPixels = 240.0;
constexpr double kAimLatencyCompensationSeconds = 0.026;
constexpr double kAimMaxLatencyCompensationSeconds = 0.052;
constexpr double kAimMaxLatencyCompensationMeters = 0.85;
constexpr double kAimMinLatencyCompensationSpeed = 1.20;
// Preserve the selected target through short entity/visibility gaps.
constexpr double kAimLockRetentionSeconds = 0.75;
constexpr double kAimLockVisibilityGraceSeconds = 0.18;
constexpr LONG kAimMaxCalibratedMouseDelta = 4000;
constexpr LONG kAimMaxHipMouseStep = 720;
constexpr LONG kAimMaxScopedMouseStep = 520;
constexpr double kAimVerticalGain = 0.50;
constexpr double kAimScopedVerticalGain = 0.42;
constexpr double kAimVerticalDeadzonePixels = 3.00;
constexpr LONG kAimMaxHipVerticalStep = 320;
constexpr LONG kAimMaxScopedVerticalStep = 200;
constexpr double kDefaultHipRadiansPerRawMouse = -0.00135;
constexpr double kDefaultScopedRadiansPerRawMouse = -0.00055;
constexpr double kAimCalibrationCooldownSeconds = 0.06;
constexpr double kAimSyntheticEchoWindowSeconds = 0.10;
constexpr LONG kAimBootstrapRawMouseDelta = 4;
constexpr double kAimBootstrapScaleLimitRadians = 0.020;
constexpr double kScopedFovThresholdDegrees = 50.0;
constexpr double kScopedMovementInputLeadSeconds = 0.008;
constexpr double kScopedMovementMinSpeedMetersPerSecond = 0.75;
// The game exporter is sampled at roughly 30 Hz.  Keep camera prediction
// inside the current snapshot interval: predicting into the next interval
// makes a stopped camera recoil and detaches boxes from model bounds.
constexpr double kCameraPredictionSeconds = 0.040;
constexpr double kEntityPredictionMaxMetersPerSecond = 45.0;
constexpr double kRawMouseScaleLimitRadians = 0.08;
constexpr double kRawMouseMaxCameraRadians = 1.20;
constexpr LONG kRawMouseAccumulationLimit = 100000;
constexpr double kSnapshotStaleSeconds = 0.60;
constexpr double kExporterRetrySeconds = 1.0;
constexpr double kDefaultMaxTargetDistanceMeters = 800.0;
constexpr double kMinTargetDistanceMeters = 50.0;
constexpr double kMaxTargetDistanceMeters = 800.0;
constexpr int kControlEsp = 1001;
constexpr int kControlTracers = 1002;
constexpr int kControlAim = 1003;
constexpr int kControlVisibility = 1004;
constexpr int kControlLead = 1005;
constexpr int kControlFovVisible = 1006;
constexpr int kControlFov = 1007;
constexpr int kControlTargetRange = 1008;
constexpr int kControlExit = 1009;
constexpr int kResourceRemotePyRun = 101;
constexpr int kResourceSnapshotCode = 102;

struct Vec3 {
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
};

struct Target {
    std::string key;
    Vec3 position;
    Vec3 min;
    Vec3 max;
    Vec3 head;
    bool hasHead = false;
    bool visible = false;
    bool isRobot = false;
    int teamRelation = 0;
    double hp = 0.0;
    double maxHp = 1.0;
    double armor = 0.0;
    double maxArmor = 0.0;
    bool dead = false;
};

struct Snapshot {
    bool valid = false;
    double timestamp = 0.0;
    int gameWidth = 0;
    int gameHeight = 0;
    Vec3 camera;
    double yaw = 0.0;
    double pitch = 0.0;
    double roll = 0.0;
    double fov = 75.0;
    Vec3 player;
    int weaponItemId = 0;
    double projectileSpeed = 0.0;
    double projectileGravity = 0.0;
    int playerTargetCount = 0;
    int robotTargetCount = 0;
    int culledTargetCount = 0;
    bool hasTargetCounts = false;
    bool hasExporterStatus = false;
    bool exporterReady = true;
    std::vector<Target> targets;
};

struct ScreenBox {
    double left = 0.0;
    double top = 0.0;
    double right = 0.0;
    double bottom = 0.0;
};

struct StateFileVersion {
    ULONGLONG writeTime = 0;
    ULONGLONG size = 0;
    bool valid = false;
};

struct AimCandidate {
    const Target* target = nullptr;
    double x = 0.0;
    double y = 0.0;
    Vec3 world;
    double distanceToCrosshair = std::numeric_limits<double>::infinity();
};

struct AimCalibrationProbe {
    bool active = false;
    LONG rawX = 0;
    LONG rawY = 0;
    double yaw = 0.0;
    double pitch = 0.0;
    double fov = 0.0;
    double timestamp = 0.0;
};

struct MouseCalibration {
    double yawRadiansPerRawMouse = 0.0;
    double pitchRadiansPerRawMouse = 0.0;
    int yawSamples = 0;
    int pitchSamples = 0;
};

struct BoxSmoothing {
    std::string key;
    RECT box = {};
    double timestamp = 0.0;
};

HWND g_target = nullptr;
HWND g_overlayWindow = nullptr;
HWND g_controlWindow = nullptr;
HWND g_espCheckbox = nullptr;
HWND g_tracerCheckbox = nullptr;
HWND g_aimCheckbox = nullptr;
HWND g_visibilityCheckbox = nullptr;
HWND g_leadCheckbox = nullptr;
HWND g_fovVisibleCheckbox = nullptr;
HWND g_fovSlider = nullptr;
HWND g_fovLabel = nullptr;
HWND g_targetRangeSlider = nullptr;
HWND g_targetRangeLabel = nullptr;
HWND g_weaponLabel = nullptr;
HWND g_liveDiagnosticsLabel = nullptr;
HFONT g_controlFont = nullptr;
HFONT g_overlayFont = nullptr;
HPEN g_boxShadowPen = nullptr;
HPEN g_boxAccentPen = nullptr;
HPEN g_fovPen = nullptr;
HPEN g_fovDisabledPen = nullptr;
HBRUSH g_transparentBrush = nullptr;
HANDLE g_trackingTimer = nullptr;
HANDLE g_trackingStopEvent = nullptr;
HANDLE g_trackingThread = nullptr;
std::atomic<bool> g_trackingMessageQueued = false;
std::wstring g_titleNeedle = L"BloodStrike";
std::wstring g_statePath;
std::wstring g_configPath;
std::wstring g_aimTriggerPath;
int g_durationSeconds = 0;
DWORD g_targetPid = 0;
DWORD g_exporterPid = 0;
bool g_exporterInstallRequested = true;
Snapshot g_snapshot;
Snapshot g_previousSnapshot;
StateFileVersion g_snapshotFileVersion;
auto g_started = std::chrono::steady_clock::now();
auto g_lastExporterAttempt = std::chrono::steady_clock::time_point::min();
bool g_espEnabled = true;
bool g_tracersEnabled = true;
bool g_aimEnabled = true;
bool g_visibilityEnabled = true;
bool g_predictionEnabled = true;
bool g_fovVisible = true;
bool g_autoInject = true;
bool g_controlsHotkeyRegistered = false;
double g_aimFovRadiusPixels = 0.0;
double g_maxTargetDistanceMeters = kDefaultMaxTargetDistanceMeters;
std::string g_aimLockedKey;
double g_aimLockLastSeenTime = 0.0;
double g_aimLockLastVisibleTime = 0.0;
LONG g_aimInputAwaitingX = 0;
LONG g_aimInputAwaitingY = 0;
double g_aimInputAwaitingUntil = 0.0;
AimCalibrationProbe g_aimCalibrationProbe;
std::wstring g_lastWeaponText;
std::wstring g_lastDiagnosticsText;
LONG g_rawMouseXSinceSnapshot = 0;
LONG g_rawMouseYSinceSnapshot = 0;
MouseCalibration g_hipMouseCalibration;
MouseCalibration g_scopedMouseCalibration;
double g_calibrationBlockedUntil = 0.0;
double g_aimResidualRawX = 0.0;
double g_aimResidualRawY = 0.0;
double g_lastAimInputTime = 0.0;
double g_lastAimSnapshotTimestamp = 0.0;
double g_lastAimTargetSwitchTime = 0.0;
double g_lastAimTriggerWriteTime = 0.0;
bool g_lastAimTriggerState = false;
std::wstring g_runtimeRootOverride;
std::vector<BoxSmoothing> g_boxSmoothing;

double UnixNow() {
    const auto now = std::chrono::system_clock::now().time_since_epoch();
    return std::chrono::duration<double>(now).count();
}

LONG AddClampedRawMouse(LONG current, LONG delta) {
    const long long sum = static_cast<long long>(current) + static_cast<long long>(delta);
    return static_cast<LONG>(std::clamp(sum,
                                        -static_cast<long long>(kRawMouseAccumulationLimit),
                                        static_cast<long long>(kRawMouseAccumulationLimit)));
}

LONG ConsumeSyntheticRawMouse(LONG* pending, LONG delivered) {
    if (*pending == 0 || delivered == 0 || ((*pending < 0) != (delivered < 0))) {
        return 0;
    }
    const long long magnitude = std::min(
        std::abs(static_cast<long long>(delivered)),
        std::abs(static_cast<long long>(*pending)));
    const LONG consumed = *pending < 0
        ? -static_cast<LONG>(magnitude)
        : static_cast<LONG>(magnitude);
    *pending -= consumed;
    return consumed;
}

std::wstring ModuleDir() {
    wchar_t path[MAX_PATH] = {};
    const DWORD length = GetModuleFileNameW(nullptr, path, MAX_PATH);
    if (length == 0 || length >= MAX_PATH) {
        return L".";
    }
    std::wstring result(path, length);
    const auto slash = result.find_last_of(L"\\/");
    return slash == std::wstring::npos ? L"." : result.substr(0, slash);
}

std::wstring ParentDir(const std::wstring& path) {
    const auto slash = path.find_last_of(L"\\/");
    return slash == std::wstring::npos ? L"." : path.substr(0, slash);
}

bool PathExists(const std::wstring& path) {
    const DWORD attributes = GetFileAttributesW(path.c_str());
    return attributes != INVALID_FILE_ATTRIBUTES && (attributes & FILE_ATTRIBUTE_DIRECTORY) == 0;
}

void DebugLog(const std::wstring& message) {
    const std::wstring line = L"[BloodStrikeCTFESP] " + message + L"\n";
    OutputDebugStringW(line.c_str());
}

std::wstring DefaultRuntimeRoot() {
    wchar_t temp[MAX_PATH] = {};
    const DWORD length = GetTempPathW(static_cast<DWORD>(std::size(temp)), temp);
    const std::wstring base = (length > 0 && length < std::size(temp))
        ? std::wstring(temp, length)
        : ModuleDir() + L"\\";
    return base + L"BloodStrikeCTFESP";
}

bool EnsureDirectory(const std::wstring& path) {
    const DWORD attributes = GetFileAttributesW(path.c_str());
    if (attributes != INVALID_FILE_ATTRIBUTES) {
        return (attributes & FILE_ATTRIBUTE_DIRECTORY) != 0;
    }
    return CreateDirectoryW(path.c_str(), nullptr) != FALSE ||
           GetLastError() == ERROR_ALREADY_EXISTS;
}

bool WriteResourceToFile(int resourceId, const std::wstring& path, std::wstring* error) {
    HRSRC resource = FindResourceW(nullptr, MAKEINTRESOURCEW(resourceId), RT_RCDATA);
    if (!resource) {
        *error = L"embedded helper resource not found: " + std::to_wstring(resourceId);
        return false;
    }
    HGLOBAL loaded = LoadResource(nullptr, resource);
    const DWORD size = SizeofResource(nullptr, resource);
    const void* data = loaded ? LockResource(loaded) : nullptr;
    if (!data || size == 0) {
        *error = L"embedded helper resource could not be loaded: " + std::to_wstring(resourceId);
        return false;
    }

    const std::wstring temporaryPath = path + L".tmp";
    HANDLE file = CreateFileW(temporaryPath.c_str(), GENERIC_WRITE, 0, nullptr,
                              CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) {
        *error = L"could not create helper file: " + temporaryPath;
        return false;
    }
    DWORD written = 0;
    const BOOL ok = WriteFile(file, data, size, &written, nullptr);
    CloseHandle(file);
    if (!ok || written != size ||
        !MoveFileExW(temporaryPath.c_str(), path.c_str(),
                     MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) {
        DeleteFileW(temporaryPath.c_str());
        *error = L"could not write helper file: " + path;
        return false;
    }
    return true;
}

bool EnsureEmbeddedRuntime(std::wstring* error) {
    const std::wstring moduleDir = ModuleDir();
    if (PathExists(moduleDir + L"\\remote_py_run.py") &&
        PathExists(moduleDir + L"\\ctf_native_snapshot_code.py")) {
        g_runtimeRootOverride = moduleDir;
        return true;
    }

    const std::wstring parentDir = ParentDir(moduleDir);
    if (PathExists(parentDir + L"\\remote_py_run.py") &&
        PathExists(parentDir + L"\\ctf_native_snapshot_code.py")) {
        g_runtimeRootOverride = parentDir;
        return true;
    }

    const std::wstring root = DefaultRuntimeRoot();
    if (!EnsureDirectory(root)) {
        *error = L"could not create runtime directory: " + root;
        return false;
    }
    if (!WriteResourceToFile(kResourceRemotePyRun, root + L"\\remote_py_run.py", error) ||
        !WriteResourceToFile(kResourceSnapshotCode, root + L"\\ctf_native_snapshot_code.py", error)) {
        return false;
    }
    g_runtimeRootOverride = root;
    return true;
}

std::wstring RuntimeRoot() {
    if (!g_runtimeRootOverride.empty()) {
        return g_runtimeRootOverride;
    }
    const std::wstring moduleDir = ModuleDir();
    if (PathExists(moduleDir + L"\\remote_py_run.py") &&
        PathExists(moduleDir + L"\\ctf_native_snapshot_code.py")) {
        return moduleDir;
    }
    const std::wstring parentDir = ParentDir(moduleDir);
    if (PathExists(parentDir + L"\\remote_py_run.py") &&
        PathExists(parentDir + L"\\ctf_native_snapshot_code.py")) {
        return parentDir;
    }
    return DefaultRuntimeRoot();
}

void ParseCommandLine() {
    int argc = 0;
    LPWSTR* argv = CommandLineToArgvW(GetCommandLineW(), &argc);
    if (!argv) {
        return;
    }

    for (int index = 1; index < argc; ++index) {
        const std::wstring argument(argv[index]);
        constexpr wchar_t kDurationPrefix[] = L"--duration=";
        constexpr wchar_t kTitlePrefix[] = L"--title=";
        constexpr wchar_t kStatePrefix[] = L"--state=";
        constexpr wchar_t kRangePrefix[] = L"--max-distance=";
        constexpr wchar_t kNoInject[] = L"--no-inject";
        if (argument.rfind(kDurationPrefix, 0) == 0) {
            const int value = _wtoi(argument.c_str() + wcslen(kDurationPrefix));
            if (value > 0 && value <= 86400) {
                g_durationSeconds = value;
            }
        } else if (argument.rfind(kTitlePrefix, 0) == 0) {
            g_titleNeedle = argument.substr(wcslen(kTitlePrefix));
        } else if (argument.rfind(kStatePrefix, 0) == 0) {
            g_statePath = argument.substr(wcslen(kStatePrefix));
        } else if (argument.rfind(kRangePrefix, 0) == 0) {
            const double value = _wtof(argument.c_str() + wcslen(kRangePrefix));
            if (std::isfinite(value)) {
                g_maxTargetDistanceMeters = std::clamp(
                    value, kMinTargetDistanceMeters, kMaxTargetDistanceMeters);
            }
        } else if (argument == kNoInject) {
            g_autoInject = false;
        }
    }
    LocalFree(argv);

    if (g_statePath.empty()) {
        g_statePath = RuntimeRoot() + L"\\ctf_native_esp_state.txt";
    }
    g_configPath = RuntimeRoot() + L"\\ctf_native_esp_config.txt";
    g_aimTriggerPath = RuntimeRoot() + L"\\ctf_native_aim_trigger.txt";
}

bool WriteExporterConfig() {
    if (g_configPath.empty()) {
        return false;
    }
    const std::wstring temporaryPath = g_configPath + L".tmp";
    std::ostringstream stream;
    stream << "max_distance=" << static_cast<int>(std::lround(g_maxTargetDistanceMeters)) << "\n"
           << "native_aim=0\n"
           << "aim_fov_px=" << static_cast<int>(std::lround(g_aimFovRadiusPixels)) << "\n"
           << "visible_only=" << (g_visibilityEnabled ? 1 : 0) << "\n";
    const std::string contents = stream.str();
    HANDLE file = CreateFileW(temporaryPath.c_str(), GENERIC_WRITE, 0, nullptr,
                              CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) {
        return false;
    }
    DWORD written = 0;
    const BOOL wrote = WriteFile(file, contents.data(), static_cast<DWORD>(contents.size()),
                                 &written, nullptr);
    CloseHandle(file);
    if (!wrote || written != contents.size() ||
        !MoveFileExW(temporaryPath.c_str(), g_configPath.c_str(),
                     MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) {
        DeleteFileW(temporaryPath.c_str());
        return false;
    }
    return true;
}

bool WriteAimTriggerState(bool active, bool force = false) {
    if (g_aimTriggerPath.empty()) {
        return false;
    }
    const double now = UnixNow();
    if (!force && active == g_lastAimTriggerState && now - g_lastAimTriggerWriteTime < 0.050) {
        return true;
    }
    const std::wstring temporaryPath = g_aimTriggerPath + L".tmp";
    const char* contents = active ? "1\n" : "0\n";
    HANDLE file = CreateFileW(temporaryPath.c_str(), GENERIC_WRITE, 0, nullptr,
                              CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) {
        return false;
    }
    DWORD written = 0;
    const BOOL wrote = WriteFile(file, contents, 2, &written, nullptr);
    CloseHandle(file);
    if (!wrote || written != 2 ||
        !MoveFileExW(temporaryPath.c_str(), g_aimTriggerPath.c_str(),
                     MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) {
        DeleteFileW(temporaryPath.c_str());
        return false;
    }
    g_lastAimTriggerState = active;
    g_lastAimTriggerWriteTime = now;
    return true;
}

BOOL CALLBACK EnumWindowsProc(HWND hwnd, LPARAM lparam) {
    if (!IsWindowVisible(hwnd)) {
        return TRUE;
    }
    wchar_t title[512] = {};
    GetWindowTextW(hwnd, title, static_cast<int>(std::size(title)));
    if (std::wstring(title).find(g_titleNeedle) == std::wstring::npos) {
        return TRUE;
    }
    RECT client = {};
    if (!GetClientRect(hwnd, &client) ||
        client.right - client.left < 320 ||
        client.bottom - client.top < 200) {
        return TRUE;
    }
    *reinterpret_cast<HWND*>(lparam) = hwnd;
    return FALSE;
}

HWND FindTargetWindow() {
    HWND target = nullptr;
    EnumWindows(EnumWindowsProc, reinterpret_cast<LPARAM>(&target));
    return target;
}

HWND WaitForTargetWindow(int timeoutSeconds) {
    const bool waitIndefinitely = timeoutSeconds <= 0;
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(timeoutSeconds);
    while (waitIndefinitely || std::chrono::steady_clock::now() < deadline) {
        if (const HWND target = FindTargetWindow()) {
            return target;
        }
        Sleep(250);
    }
    return nullptr;
}

bool TargetClientRect(RECT* output) {
    if (!g_target || !IsWindow(g_target) || !IsWindowVisible(g_target) || IsIconic(g_target)) {
        return false;
    }
    RECT client = {};
    if (!GetClientRect(g_target, &client)) {
        return false;
    }
    POINT topLeft = {0, 0};
    POINT bottomRight = {client.right, client.bottom};
    if (!ClientToScreen(g_target, &topLeft) || !ClientToScreen(g_target, &bottomRight)) {
        return false;
    }
    output->left = topLeft.x;
    output->top = topLeft.y;
    output->right = bottomRight.x;
    output->bottom = bottomRight.y;
    return output->right > output->left && output->bottom > output->top;
}

bool GetStateFileVersion(StateFileVersion* output) {
    WIN32_FILE_ATTRIBUTE_DATA attributes = {};
    if (!GetFileAttributesExW(g_statePath.c_str(), GetFileExInfoStandard, &attributes)) {
        return false;
    }
    ULARGE_INTEGER writeTime = {};
    writeTime.LowPart = attributes.ftLastWriteTime.dwLowDateTime;
    writeTime.HighPart = attributes.ftLastWriteTime.dwHighDateTime;
    ULARGE_INTEGER size = {};
    size.LowPart = attributes.nFileSizeLow;
    size.HighPart = attributes.nFileSizeHigh;
    *output = {writeTime.QuadPart, size.QuadPart, true};
    return true;
}

bool HasNewStateFileVersion(StateFileVersion* version) {
    if (!GetStateFileVersion(version)) {
        return false;
    }
    return !g_snapshotFileVersion.valid ||
           version->writeTime != g_snapshotFileVersion.writeTime ||
           version->size != g_snapshotFileVersion.size;
}

bool ReadSnapshot(Snapshot* output) {
    HANDLE handle = CreateFileW(
        g_statePath.c_str(), GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, nullptr,
        OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (handle == INVALID_HANDLE_VALUE) {
        return false;
    }
    LARGE_INTEGER length = {};
    if (!GetFileSizeEx(handle, &length) || length.QuadPart <= 0 || length.QuadPart > 1024 * 1024) {
        CloseHandle(handle);
        return false;
    }
    std::string text(static_cast<size_t>(length.QuadPart), '\0');
    DWORD read = 0;
    const BOOL readOk = ReadFile(handle, text.data(), static_cast<DWORD>(text.size()), &read, nullptr);
    CloseHandle(handle);
    if (!readOk || read != text.size()) {
        return false;
    }
    std::istringstream input(text);

    Snapshot candidate;
    std::string magic;
    int targetCount = 0;
    if (!(input >> magic >> candidate.timestamp >> candidate.gameWidth >> candidate.gameHeight >>
          candidate.camera.x >> candidate.camera.y >> candidate.camera.z >> candidate.yaw >>
          candidate.pitch >> candidate.roll >> candidate.fov >> candidate.player.x >>
          candidate.player.y >> candidate.player.z >> targetCount) ||
        magic != "ESP1" || candidate.gameWidth <= 0 || candidate.gameHeight <= 0 ||
        targetCount < 0 || targetCount > 128) {
        return false;
    }

    candidate.targets.reserve(static_cast<size_t>(targetCount));
    for (int index = 0; index < targetCount; ++index) {
        std::string tag;
        Target target;
        int dead = 0;
        int hasHead = 0;
        int visible = 0;
        int isRobot = 0;
        int teamRelation = 0;
        if (!(input >> tag >> target.key >> target.position.x >> target.position.y >>
              target.position.z >> target.min.x >> target.min.y >> target.min.z >>
              target.max.x >> target.max.y >> target.max.z >> target.hp >> target.maxHp >>
              target.armor >> target.maxArmor >> dead >> hasHead >> target.head.x >>
              target.head.y >> target.head.z >> visible >> isRobot >> teamRelation) ||
            tag != "T" || (isRobot != 0 && isRobot != 1) ||
            teamRelation < 0 || teamRelation > 2) {
            return false;
        }
        target.dead = dead != 0;
        target.hasHead = hasHead != 0 && std::isfinite(target.head.x) &&
                         std::isfinite(target.head.y) && std::isfinite(target.head.z);
        target.visible = visible != 0;
        target.isRobot = isRobot != 0;
        target.teamRelation = teamRelation;
        if (target.max.y <= target.min.y) {
            continue;
        }
        candidate.targets.push_back(target);
    }
    std::string trailer;
    if (input >> trailer && trailer == "W") {
        if (!(input >> candidate.weaponItemId >> candidate.projectileSpeed)) {
            return false;
        }
        // Gravity was added after the initial two-field W trailer.  Consume
        // only this line so older live snapshots remain parse-compatible.
        std::string weaponRest;
        std::getline(input, weaponRest);
        std::istringstream weaponFields(weaponRest);
        double gravity = 0.0;
        if (weaponFields >> gravity && std::isfinite(gravity) &&
            gravity >= 0.0 && gravity <= 30.0) {
            candidate.projectileGravity = gravity;
        }
    }
    std::string countsTag;
    if (input >> countsTag && countsTag == "C") {
        if (!(input >> candidate.playerTargetCount >> candidate.robotTargetCount >>
              candidate.culledTargetCount) ||
            candidate.playerTargetCount < 0 || candidate.robotTargetCount < 0 ||
            candidate.culledTargetCount < 0 ||
            candidate.playerTargetCount + candidate.robotTargetCount !=
                static_cast<int>(candidate.targets.size())) {
            return false;
        }
        candidate.hasTargetCounts = true;
    }
    std::string exporterTag;
    if (input >> exporterTag && exporterTag == "S") {
        int ready = 0;
        if (!(input >> ready) || (ready != 0 && ready != 1)) {
            return false;
        }
        candidate.hasExporterStatus = true;
        candidate.exporterReady = ready != 0;
    }
    candidate.valid = true;
    *output = std::move(candidate);
    return true;
}

Vec3 operator-(const Vec3& left, const Vec3& right) {
    return {left.x - right.x, left.y - right.y, left.z - right.z};
}

Vec3 operator+(const Vec3& left, const Vec3& right) {
    return {left.x + right.x, left.y + right.y, left.z + right.z};
}

Vec3 operator*(const Vec3& value, double scale) {
    return {value.x * scale, value.y * scale, value.z * scale};
}

double Dot(const Vec3& left, const Vec3& right) {
    return left.x * right.x + left.y * right.y + left.z * right.z;
}

Vec3 Cross(const Vec3& left, const Vec3& right) {
    return {
        left.y * right.z - left.z * right.y,
        left.z * right.x - left.x * right.z,
        left.x * right.y - left.y * right.x,
    };
}

double Length(const Vec3& value) {
    return std::sqrt(Dot(value, value));
}

bool ProjectPoint(const Snapshot& snapshot, const Vec3& point, double* x, double* y) {
    constexpr double kPi = 3.14159265358979323846;
    const double yaw = snapshot.yaw;
    const double pitch = snapshot.pitch;
    const double cosPitch = std::cos(pitch);

    // Sunshine's CameraFrame uses yaw=0 toward -Z.  This basis matches the
    // active camera and projects model bounds rather than distance heuristics.
    const Vec3 forward = {
        -std::sin(yaw) * cosPitch,
        std::sin(pitch),
        -std::cos(yaw) * cosPitch,
    };
    const Vec3 baseRight = {std::cos(yaw), 0.0, -std::sin(yaw)};
    const Vec3 baseUp = Cross(baseRight, forward);
    const double cosRoll = std::cos(snapshot.roll);
    const double sinRoll = std::sin(snapshot.roll);
    const Vec3 right = {
        baseRight.x * cosRoll + baseUp.x * sinRoll,
        baseRight.y * cosRoll + baseUp.y * sinRoll,
        baseRight.z * cosRoll + baseUp.z * sinRoll,
    };
    const Vec3 up = {
        baseUp.x * cosRoll - baseRight.x * sinRoll,
        baseUp.y * cosRoll - baseRight.y * sinRoll,
        baseUp.z * cosRoll - baseRight.z * sinRoll,
    };
    const Vec3 relative = point - snapshot.camera;
    const double depth = Dot(relative, forward);
    if (depth <= 0.08) {
        return false;
    }

    // Scoped weapons report narrow FOVs (for example 9.07 degrees).  Do not
    // clamp those values to a hip-fire minimum or every projected box expands.
    const double fovRadians = std::clamp(snapshot.fov, 1.0, 150.0) * kPi / 180.0;
    const double focalY = static_cast<double>(snapshot.gameHeight) / (2.0 * std::tan(fovRadians * 0.5));
    *x = static_cast<double>(snapshot.gameWidth) * 0.5 + Dot(relative, right) * focalY / depth;
    *y = static_cast<double>(snapshot.gameHeight) * 0.5 - Dot(relative, up) * focalY / depth;
    return std::isfinite(*x) && std::isfinite(*y);
}

double WrapAngleDelta(double from, double to) {
    constexpr double kPi = 3.14159265358979323846;
    double delta = std::fmod(to - from + kPi, kPi * 2.0);
    if (delta < 0.0) {
        delta += kPi * 2.0;
    }
    return delta - kPi;
}

bool IsScopedFov(double fov) {
    return std::isfinite(fov) && fov <= kScopedFovThresholdDegrees;
}

MouseCalibration& CalibrationForFov(double fov) {
    return IsScopedFov(fov) ? g_scopedMouseCalibration : g_hipMouseCalibration;
}

bool HasRawMouseCameraCalibration(double fov) {
    const MouseCalibration& calibration = CalibrationForFov(fov);
    return calibration.yawSamples >= 2 && calibration.pitchSamples >= 2 &&
           std::isfinite(calibration.yawRadiansPerRawMouse) &&
           std::isfinite(calibration.pitchRadiansPerRawMouse);
}

MouseCalibration EffectiveCalibrationForFov(double fov) {
    MouseCalibration calibration = CalibrationForFov(fov);
    if (calibration.yawSamples < 2 || !std::isfinite(calibration.yawRadiansPerRawMouse) ||
        std::abs(calibration.yawRadiansPerRawMouse) < 1e-7) {
        calibration.yawRadiansPerRawMouse = IsScopedFov(fov)
            ? kDefaultScopedRadiansPerRawMouse
            : kDefaultHipRadiansPerRawMouse;
    }
    if (calibration.pitchSamples < 2 || !std::isfinite(calibration.pitchRadiansPerRawMouse) ||
        std::abs(calibration.pitchRadiansPerRawMouse) < 1e-7) {
        calibration.pitchRadiansPerRawMouse = IsScopedFov(fov)
            ? kDefaultScopedRadiansPerRawMouse
            : kDefaultHipRadiansPerRawMouse;
    }
    return calibration;
}

void ResetRawMouseCameraState() {
    g_rawMouseXSinceSnapshot = 0;
    g_rawMouseYSinceSnapshot = 0;
    g_hipMouseCalibration = {};
    g_scopedMouseCalibration = {};
    g_calibrationBlockedUntil = 0.0;
}

void CalibrateRawMouseCamera(const Snapshot& previous, const Snapshot& current,
                             LONG rawMouseX, LONG rawMouseY) {
    MouseCalibration& calibration = CalibrationForFov(current.fov);
    const auto updateScale = [](double sample, double* scale, int* samples) {
        if (!std::isfinite(sample) || std::abs(sample) > kRawMouseScaleLimitRadians) {
            return;
        }
        if (*samples == 0) {
            *scale = sample;
        } else {
            // A camera snapshot can also contain recoil, camera animation, or a
            // synthetic aim move.  Never let one such frame reverse or wildly
            // rescale a learned mouse axis.
            if (sample * *scale <= 0.0) {
                return;
            }
            const double ratio = std::abs(sample / *scale);
            if (!std::isfinite(ratio) || ratio < 0.40 || ratio > 2.50) {
                return;
            }
            *scale = *scale * 0.85 + sample * 0.15;
        }
        *samples = std::min(*samples + 1, 32);
    };

    if (std::abs(rawMouseX) >= 2) {
        updateScale(WrapAngleDelta(previous.yaw, current.yaw) /
                        static_cast<double>(rawMouseX),
                    &calibration.yawRadiansPerRawMouse, &calibration.yawSamples);
    }
    if (std::abs(rawMouseY) >= 2) {
        updateScale((current.pitch - previous.pitch) /
                        static_cast<double>(rawMouseY),
                    &calibration.pitchRadiansPerRawMouse, &calibration.pitchSamples);
    }
}

void CompleteAimCalibrationProbe(const Snapshot& current) {
    if (!g_aimCalibrationProbe.active ||
        current.timestamp <= g_aimCalibrationProbe.timestamp + 0.000001) {
        return;
    }
    const AimCalibrationProbe probe = g_aimCalibrationProbe;
    g_aimCalibrationProbe = {};
    if (std::abs(current.fov - probe.fov) > 0.08) {
        return;
    }
    MouseCalibration& calibration = CalibrationForFov(current.fov);
    const auto acceptScale = [](double sample, double* scale, int* samples) {
        if (!std::isfinite(sample) ||
            std::abs(sample) < 1e-7 ||
            std::abs(sample) > kAimBootstrapScaleLimitRadians) {
            return;
        }
        if (*samples > 0 && sample * *scale <= 0.0) {
            return;
        }
        if (*samples == 0) {
            *scale = sample;
        } else {
            *scale = *scale * 0.70 + sample * 0.30;
        }
        *samples = std::min(*samples + 1, 32);
    };
    if (probe.rawX != 0) {
        acceptScale(WrapAngleDelta(probe.yaw, current.yaw) /
                        static_cast<double>(probe.rawX),
                    &calibration.yawRadiansPerRawMouse, &calibration.yawSamples);
    }
    if (probe.rawY != 0) {

        acceptScale((current.pitch - probe.pitch) /
                        static_cast<double>(probe.rawY),
                    &calibration.pitchRadiansPerRawMouse, &calibration.pitchSamples);
    }
}
Vec3 Extrapolate(const Vec3& previous, const Vec3& current, double factor) {
    return {
        current.x + (current.x - previous.x) * factor,
        current.y + (current.y - previous.y) * factor,
        current.z + (current.z - previous.z) * factor,
    };
}

const Target* FindTargetByKey(const Snapshot& snapshot, const std::string& key);

Snapshot PredictedSnapshot() {
    Snapshot predicted = g_snapshot;
    bool appliedRawMouseCamera = false;
    if (g_rawMouseXSinceSnapshot != 0 || g_rawMouseYSinceSnapshot != 0) {
        const MouseCalibration calibration = EffectiveCalibrationForFov(g_snapshot.fov);
        const double yawOffset = static_cast<double>(g_rawMouseXSinceSnapshot) *
                                 calibration.yawRadiansPerRawMouse;
        const double pitchOffset = static_cast<double>(g_rawMouseYSinceSnapshot) *
                                   calibration.pitchRadiansPerRawMouse;
        if (std::isfinite(yawOffset) && std::isfinite(pitchOffset) &&
            std::abs(yawOffset) <= kRawMouseMaxCameraRadians &&
            std::abs(pitchOffset) <= kRawMouseMaxCameraRadians) {
            predicted.yaw = g_snapshot.yaw + yawOffset;
            predicted.pitch = std::clamp(g_snapshot.pitch + pitchOffset, -1.55, 1.55);
            appliedRawMouseCamera = true;
        }
    }
    if (!g_previousSnapshot.valid) {
        return predicted;
    }
    // During the ADS zoom animation, camera orientation and FOV must come from
    // the same captured frame.  Interpolating only the orientation offsets ESP.
    const bool fovStable = std::abs(g_snapshot.fov - g_previousSnapshot.fov) <= 0.08;
    const double interval = g_snapshot.timestamp - g_previousSnapshot.timestamp;
    if (interval < 0.002 || interval > 0.20) {
        return predicted;
    }
    const double snapshotAge = std::max(0.0, UnixNow() - g_snapshot.timestamp);
    const double cameraLead = std::min(
        interval, std::clamp(snapshotAge, 0.0, kCameraPredictionSeconds));
    const double cameraFactor = cameraLead / interval;
    predicted.camera = Extrapolate(g_previousSnapshot.camera, g_snapshot.camera, cameraFactor);
    if (!appliedRawMouseCamera && fovStable) {
        predicted.yaw = g_snapshot.yaw +
            WrapAngleDelta(g_previousSnapshot.yaw, g_snapshot.yaw) * cameraFactor;
        predicted.pitch = g_snapshot.pitch +
            (g_snapshot.pitch - g_previousSnapshot.pitch) * cameraFactor;
        predicted.roll = g_snapshot.roll +
            WrapAngleDelta(g_previousSnapshot.roll, g_snapshot.roll) * cameraFactor;
    }

    // Do not carry model animation or network position past the capture time.
    // This keeps close sprinting targets from vibrating while camera rotation
    // remains visually current.
    const double entityLead = std::min(interval, snapshotAge);
    const double entityFactor = entityLead / interval;
    // Advance a target as one rigid body.  Extrapolating its min/max bounds
    // independently magnifies animation noise, especially at close range.
    for (Target& target : predicted.targets) {
        const Target* previous = FindTargetByKey(g_previousSnapshot, target.key);
        if (!previous) {
            continue;
        }
        const Vec3 delta = target.position - previous->position;
        const double speed = Length(delta) / interval;
        if (!std::isfinite(speed) || speed > kEntityPredictionMaxMetersPerSecond) {
            continue;
        }
        const Vec3 offset = {delta.x * entityFactor, delta.y * entityFactor,
                             delta.z * entityFactor};
        target.position = {target.position.x + offset.x, target.position.y + offset.y,
                           target.position.z + offset.z};
        target.min = {target.min.x + offset.x, target.min.y + offset.y, target.min.z + offset.z};
        target.max = {target.max.x + offset.x, target.max.y + offset.y, target.max.z + offset.z};
        if (target.hasHead) {
            target.head = {target.head.x + offset.x, target.head.y + offset.y,
                           target.head.z + offset.z};
        }
    }
    return predicted;
}

Snapshot AimControlSnapshot() {
    Snapshot predicted = g_snapshot;
    if (g_rawMouseXSinceSnapshot == 0 && g_rawMouseYSinceSnapshot == 0) {
        return predicted;
    }
    const MouseCalibration calibration = EffectiveCalibrationForFov(g_snapshot.fov);
    const double yawOffset = static_cast<double>(g_rawMouseXSinceSnapshot) *
                             calibration.yawRadiansPerRawMouse;
    const double pitchOffset = static_cast<double>(g_rawMouseYSinceSnapshot) *
                               calibration.pitchRadiansPerRawMouse;
    if (std::isfinite(yawOffset) && std::isfinite(pitchOffset) &&
        std::abs(yawOffset) <= kRawMouseMaxCameraRadians &&
        std::abs(pitchOffset) <= kRawMouseMaxCameraRadians) {
        predicted.yaw = g_snapshot.yaw + yawOffset;
        predicted.pitch = std::clamp(g_snapshot.pitch + pitchOffset, -1.55, 1.55);
    }
    return predicted;
}

bool ProjectBounds(const Snapshot& snapshot, const Target& target, ScreenBox* output) {
    double minX = std::numeric_limits<double>::infinity();
    double minY = std::numeric_limits<double>::infinity();
    double maxX = -std::numeric_limits<double>::infinity();
    double maxY = -std::numeric_limits<double>::infinity();
    int projectedCount = 0;

    for (const double x : {target.min.x, target.max.x}) {
        for (const double y : {target.min.y, target.max.y}) {
            for (const double z : {target.min.z, target.max.z}) {
                double screenX = 0.0;
                double screenY = 0.0;
                if (!ProjectPoint(snapshot, {x, y, z}, &screenX, &screenY)) {
                    continue;
                }
                minX = std::min(minX, screenX);
                minY = std::min(minY, screenY);
                maxX = std::max(maxX, screenX);
                maxY = std::max(maxY, screenY);
                ++projectedCount;
            }
        }
    }
    // Distant models can quantize to only a few visible bounds corners.
    if (projectedCount < 2 || maxX - minX < 0.15 || maxY - minY < 0.30) {
        return false;
    }
    const double horizontalPad = std::max(1.0, (maxX - minX) * 0.035);
    const double verticalPad = std::max(1.0, (maxY - minY) * 0.018);
    output->left = minX - horizontalPad;
    output->top = minY - verticalPad;
    output->right = maxX + horizontalPad;
    output->bottom = maxY + verticalPad;
    return true;
}

bool ScaledTargetBox(const Snapshot& snapshot, const Target& target, const RECT& client, RECT* output) {
    if (snapshot.gameWidth <= 0 || snapshot.gameHeight <= 0 ||
        client.right <= client.left || client.bottom <= client.top) {
        return false;
    }

    ScreenBox projected = {};
    if (!ProjectBounds(snapshot, target, &projected)) {
        return false;
    }

    const double scaleX = static_cast<double>(client.right - client.left) / static_cast<double>(snapshot.gameWidth);
    const double scaleY = static_cast<double>(client.bottom - client.top) / static_cast<double>(snapshot.gameHeight);
    const ScreenBox scaled = {
        projected.left * scaleX,
        projected.top * scaleY,
        projected.right * scaleX,
        projected.bottom * scaleY,
    };
    const LONG left = static_cast<LONG>(std::lround(scaled.left));
    const LONG top = static_cast<LONG>(std::lround(scaled.top));
    *output = {
        left,
        top,
        std::max(left + 1, static_cast<LONG>(std::lround(scaled.right))),
        std::max(top + 2, static_cast<LONG>(std::lround(scaled.bottom))),
    };
    return true;
}

RECT SmoothTargetBox(const std::string& key, const RECT& raw, const RECT& client) {
    const double now = UnixNow();
    const auto width = [](const RECT& box) {
        return std::max(1L, box.right - box.left);
    };
    const auto height = [](const RECT& box) {
        return std::max(1L, box.bottom - box.top);
    };
    const auto centerX = [](const RECT& box) {
        return (static_cast<double>(box.left) + static_cast<double>(box.right)) * 0.5;
    };
    const auto centerY = [](const RECT& box) {
        return (static_cast<double>(box.top) + static_cast<double>(box.bottom)) * 0.5;
    };
    const auto blendEdge = [](LONG oldValue, LONG newValue, double alpha) {
        return static_cast<LONG>(std::lround(
            static_cast<double>(oldValue) * (1.0 - alpha) +
            static_cast<double>(newValue) * alpha));
    };

    for (auto it = g_boxSmoothing.begin(); it != g_boxSmoothing.end();) {
        if (now - it->timestamp > 1.0) {
            it = g_boxSmoothing.erase(it);
        } else {
            ++it;
        }
    }

    for (BoxSmoothing& entry : g_boxSmoothing) {
        if (entry.key != key) {
            continue;
        }
        const double age = std::max(0.0, now - entry.timestamp);
        const double jump = std::hypot(centerX(raw) - centerX(entry.box),
                                       centerY(raw) - centerY(entry.box));
        const double rawSize = static_cast<double>(std::max(width(raw), height(raw)));
        const double oldSize = static_cast<double>(std::max(width(entry.box), height(entry.box)));
        const bool discontinuity = age > 0.35 ||
            jump > std::max(140.0, rawSize * 2.4) ||
            rawSize > oldSize * 3.0 ||
            oldSize > rawSize * 3.0 ||
            raw.right < -client.right || raw.left > client.right * 2 ||
            raw.bottom < -client.bottom || raw.top > client.bottom * 2;
        if (discontinuity) {
            entry.box = raw;
            entry.timestamp = now;
            return raw;
        }

        const double alpha = std::clamp(age * 12.0, 0.18, 0.42);
        RECT smoothed = {
            blendEdge(entry.box.left, raw.left, alpha),
            blendEdge(entry.box.top, raw.top, alpha),
            blendEdge(entry.box.right, raw.right, alpha),
            blendEdge(entry.box.bottom, raw.bottom, alpha),
        };
        if (smoothed.right <= smoothed.left) {
            smoothed.right = smoothed.left + width(raw);
        }
        if (smoothed.bottom <= smoothed.top) {
            smoothed.bottom = smoothed.top + height(raw);
        }
        entry.box = smoothed;
        entry.timestamp = now;
        return smoothed;
    }

    g_boxSmoothing.push_back({key, raw, now});
    return raw;
}

double AimFovRadius(const RECT& client) {
    if (g_aimFovRadiusPixels > 0.0) {
        return g_aimFovRadiusPixels;
    }
    return std::max(78.0, static_cast<double>(client.bottom - client.top) * kDefaultAimFovHeightFraction);
}

const Target* FindTargetByKey(const Snapshot& snapshot, const std::string& key) {
    for (const Target& target : snapshot.targets) {
        if (target.key == key) {
            return &target;
        }
    }
    return nullptr;
}

Vec3 EstimatedRelativeVelocity(const Target& target) {
    if (!g_snapshot.valid || !g_previousSnapshot.valid) {
        return {};
    }
    const double interval = g_snapshot.timestamp - g_previousSnapshot.timestamp;
    if (interval < 0.002 || interval > 0.20) {
        return {};
    }
    const Target* latest = FindTargetByKey(g_snapshot, target.key);
    const Target* previous = FindTargetByKey(g_previousSnapshot, target.key);
    if (!latest || !previous) {
        return {};
    }
    const Vec3 targetVelocity = {
        (latest->position.x - previous->position.x) / interval,
        (latest->position.y - previous->position.y) / interval,
        (latest->position.z - previous->position.z) / interval,
    };
    const Vec3 cameraVelocity = {
        (g_snapshot.camera.x - g_previousSnapshot.camera.x) / interval,
        (g_snapshot.camera.y - g_previousSnapshot.camera.y) / interval,
        (g_snapshot.camera.z - g_previousSnapshot.camera.z) / interval,
    };
    return targetVelocity - cameraVelocity;
}
double EstimatedLocalHorizontalSpeed() {
    if (!g_snapshot.valid || !g_previousSnapshot.valid) {
        return 0.0;
    }
    const double interval = g_snapshot.timestamp - g_previousSnapshot.timestamp;
    if (interval < 0.002 || interval > 0.20) {
        return 0.0;
    }
    const double velocityX =
        (g_snapshot.player.x - g_previousSnapshot.player.x) / interval;
    const double velocityZ =
        (g_snapshot.player.z - g_previousSnapshot.player.z) / interval;
    return std::hypot(velocityX, velocityZ);
}


Vec3 ClampMagnitude(const Vec3& value, double maximum) {
    const double length = Length(value);
    if (!std::isfinite(length) || length <= maximum || length <= 0.0001) {
        return value;
    }
    const double scale = maximum / length;
    return {value.x * scale, value.y * scale, value.z * scale};
}

Vec3 TargetHeadPoint(const Target& target);
Vec3 EstimatedHeadCameraRelativeVelocity(const Target& target);

bool HasValidProjectileBallistics(const Snapshot& snapshot) {
    return std::isfinite(snapshot.projectileSpeed) &&
           snapshot.projectileSpeed >= kAimMinProjectileSpeed &&
           snapshot.projectileSpeed <= kAimMaxProjectileSpeed &&
           std::isfinite(snapshot.projectileGravity) &&
           snapshot.projectileGravity >= 0.0 &&
           snapshot.projectileGravity <= 30.0;
}

double SolveNoGravityFlightTime(const Vec3& relativePosition,
                                const Vec3& relativeVelocity,
                                double projectileSpeed) {
    const double a = Dot(relativeVelocity, relativeVelocity) -
                     projectileSpeed * projectileSpeed;
    const double b = 2.0 * Dot(relativePosition, relativeVelocity);
    const double c = Dot(relativePosition, relativePosition);
    double best = std::numeric_limits<double>::infinity();
    const auto consider = [&best](double value) {
        if (std::isfinite(value) && value > 0.000001) {
            best = std::min(best, value);
        }
    };

    if (std::abs(a) < 1e-9) {
        if (std::abs(b) >= 1e-9) {
            consider(-c / b);
        }
        return best;
    }

    const double discriminant = b * b - 4.0 * a * c;
    if (discriminant < 0.0 || !std::isfinite(discriminant)) {
        return best;
    }
    const double root = std::sqrt(std::max(0.0, discriminant));
    consider((-b - root) / (2.0 * a));
    consider((-b + root) / (2.0 * a));
    return best;
}

double BallisticResidual(const Vec3& relativePosition,
                         const Vec3& relativeVelocity,
                         double projectileSpeed,
                         double projectileGravity,
                         double time) {
    // Y is world-up in the game coordinate system.  The projectile must be
    // aimed above the future head by the amount gravity will remove in flight.
    const Vec3 requiredDisplacement = relativePosition + relativeVelocity * time +
        Vec3{0.0, 0.5 * projectileGravity * time * time, 0.0};
    return Dot(requiredDisplacement, requiredDisplacement) -
           projectileSpeed * projectileSpeed * time * time;
}

bool SolveBallisticFlightTime(const Vec3& relativePosition,
                              const Vec3& relativeVelocity,
                              double projectileSpeed,
                              double projectileGravity,
                              double* flightTime) {
    if (!flightTime || !std::isfinite(projectileSpeed) ||
        projectileSpeed < kAimMinProjectileSpeed ||
        projectileSpeed > kAimMaxProjectileSpeed ||
        !std::isfinite(projectileGravity) || projectileGravity < 0.0 ||
        projectileGravity > 30.0) {
        return false;
    }
    const double distance = Length(relativePosition);
    if (!std::isfinite(distance) || distance <= 0.05) {
        return false;
    }
    const double noGravityTime = SolveNoGravityFlightTime(
        relativePosition, relativeVelocity, projectileSpeed);
    const double initialTime = std::isfinite(noGravityTime)
        ? noGravityTime
        : distance / projectileSpeed;
    if (!std::isfinite(initialTime) || initialTime <= 0.0) {
        return false;
    }
    if (projectileGravity <= 0.001) {
        *flightTime = initialTime;
        return true;
    }

    const double maximumTime = std::clamp(
        std::max(distance / projectileSpeed * 3.0 + 0.25,
                 initialTime * 3.0 + 0.25),
        0.05, kAimMaxBallisticFlightSeconds);
    const double initialGuess = std::clamp(initialTime, 0.000001, maximumTime);
    const auto residual = [relativePosition, relativeVelocity, projectileSpeed,
                           projectileGravity](double time) {
        return BallisticResidual(relativePosition, relativeVelocity,
                                 projectileSpeed, projectileGravity, time);
    };
    const auto bisectFirstCrossing = [&residual](double low, double high) {
        for (int iteration = 0; iteration < 48; ++iteration) {
            const double middle = (low + high) * 0.5;
            const double value = residual(middle);
            if (!std::isfinite(value) || value > 0.0) {
                low = middle;
            } else {
                high = middle;
            }
        }
        return (low + high) * 0.5;
    };

    const double initialResidual = residual(initialGuess);
    if (std::isfinite(initialResidual) && initialResidual <= 0.0) {
        *flightTime = bisectFirstCrossing(0.0, initialGuess);
        return std::isfinite(*flightTime) && *flightTime > 0.0;
    }

    // Gravity normally moves the low trajectory slightly later than the
    // no-gravity solution.  Grow in small relative steps so a short-lived
    // feasible interval is not skipped at close range.
    double previousTime = initialGuess;
    double previousResidual = initialResidual;
    for (int iteration = 0; iteration < 256; ++iteration) {
        const double step = std::max(0.000001, previousTime * 0.08);
        const double nextTime = std::min(maximumTime, previousTime + step);
        if (nextTime <= previousTime) {
            break;
        }
        const double nextResidual = residual(nextTime);
        if (std::isfinite(previousResidual) && previousResidual >= 0.0 &&
            std::isfinite(nextResidual) && nextResidual <= 0.0) {
            *flightTime = bisectFirstCrossing(previousTime, nextTime);
            return std::isfinite(*flightTime) && *flightTime > 0.0;
        }
        previousTime = nextTime;
        previousResidual = nextResidual;
        if (nextTime >= maximumTime) {
            break;
        }
    }
    return false;
}

bool BuildBallisticAimPoint(const Snapshot& snapshot, const Target& target,
                            Vec3* output) {
    if (!output || !g_predictionEnabled ||
        !HasValidProjectileBallistics(snapshot)) {
        return false;
    }
    const Vec3 head = TargetHeadPoint(target);
    Vec3 relativeVelocity = ClampMagnitude(
        EstimatedHeadCameraRelativeVelocity(target), kAimMaxRelativeVelocity);
    if (!std::isfinite(relativeVelocity.x) ||
        !std::isfinite(relativeVelocity.y) ||
        !std::isfinite(relativeVelocity.z)) {
        relativeVelocity = {};
    }
    const double relativeSpeed = Length(relativeVelocity);
    if (!std::isfinite(relativeSpeed) ||
        relativeSpeed < kAimMinLatencyCompensationSpeed) {
        return false;
    }
    // Keep the vertical target component authoritative.  Only projectile drop
    // supplies a vertical offset; this avoids reintroducing jump/crouch sway.
    relativeVelocity.y = 0.0;
    const double snapshotAge = std::clamp(
        std::max(0.0, UnixNow() - snapshot.timestamp),
        0.0, kAimMaxSnapshotLeadSeconds);
    const Vec3 relativePosition = head - snapshot.camera +
        relativeVelocity * snapshotAge;
    double flightTime = 0.0;
    if (!SolveBallisticFlightTime(relativePosition, relativeVelocity,
                                  snapshot.projectileSpeed,
                                  snapshot.projectileGravity, &flightTime)) {
        return false;
    }

    const double totalLeadTime = snapshotAge + flightTime;
    Vec3 compensation = relativeVelocity * totalLeadTime;
    const double horizontalLead = std::hypot(compensation.x, compensation.z);
    if (horizontalLead > kAimMaxBallisticHorizontalLeadMeters &&
        horizontalLead > 0.0001) {
        const double scale = kAimMaxBallisticHorizontalLeadMeters / horizontalLead;
        compensation.x *= scale;
        compensation.z *= scale;
    }
    compensation.y = std::clamp(
        0.5 * snapshot.projectileGravity * flightTime * flightTime,
        0.0, kAimMaxBallisticDropMeters);
    *output = head + compensation;
    return std::isfinite(output->x) && std::isfinite(output->y) &&
           std::isfinite(output->z);
}

void ClearAimLock() {
    g_aimLockedKey.clear();
    g_aimLockLastSeenTime = 0.0;
    g_aimLockLastVisibleTime = 0.0;
    g_aimInputAwaitingX = 0;
    g_aimInputAwaitingY = 0;
    g_aimInputAwaitingUntil = 0.0;
    g_aimCalibrationProbe = {};
    g_aimResidualRawX = 0.0;
    g_aimResidualRawY = 0.0;
    g_lastAimInputTime = 0.0;
    g_lastAimSnapshotTimestamp = 0.0;
    g_lastAimTargetSwitchTime = 0.0;
}

Vec3 TargetHeadPoint(const Target& target) {
    if (target.hasHead && std::isfinite(target.head.x) &&
        std::isfinite(target.head.y) && std::isfinite(target.head.z)) {
        return target.head;
    }
    const double height = std::max(0.1, target.max.y - target.min.y);
    return {
        (target.min.x + target.max.x) * 0.5,
        target.min.y + height * kAimWorldHeadHeightFraction,
        (target.min.z + target.max.z) * 0.5,
    };
}

bool TryGetAuthoritativeHead(const Target& target, Vec3* output) {
    if (!target.hasHead || !std::isfinite(target.head.x) ||
        !std::isfinite(target.head.y) || !std::isfinite(target.head.z)) {
        return false;
    }
    *output = target.head;
    return true;
}

Vec3 EstimatedHeadRelativeVelocity(const Target& target) {
    if (!g_snapshot.valid || !g_previousSnapshot.valid) {
        return {};
    }
    const double interval = g_snapshot.timestamp - g_previousSnapshot.timestamp;
    if (interval < 0.006 || interval > 0.18) {
        return {};
    }
    const Target* latest = FindTargetByKey(g_snapshot, target.key);
    const Target* previous = FindTargetByKey(g_previousSnapshot, target.key);
    if (!latest || !previous) {
        return {};
    }
    const Vec3 latestHead = TargetHeadPoint(*latest);
    const Vec3 previousHead = TargetHeadPoint(*previous);
    const Vec3 headVelocity = {
        (latestHead.x - previousHead.x) / interval,
        (latestHead.y - previousHead.y) / interval,
        (latestHead.z - previousHead.z) / interval,
    };
    return headVelocity;
}

Vec3 EstimatedHeadCameraRelativeVelocity(const Target& target) {
    Vec3 headVelocity = EstimatedHeadRelativeVelocity(target);
    if (!g_snapshot.valid || !g_previousSnapshot.valid) {
        return headVelocity;
    }
    const double interval = g_snapshot.timestamp - g_previousSnapshot.timestamp;
    if (interval < 0.006 || interval > 0.18) {
        return headVelocity;
    }
    const Vec3 cameraVelocity = {
        (g_snapshot.camera.x - g_previousSnapshot.camera.x) / interval,
        (g_snapshot.camera.y - g_previousSnapshot.camera.y) / interval,
        (g_snapshot.camera.z - g_previousSnapshot.camera.z) / interval,
    };
    return headVelocity - cameraVelocity;
}

bool HeadMatchesProjectedBounds(const Snapshot& snapshot, const Target& target) {
    ScreenBox bounds = {};
    double headX = 0.0;
    double headY = 0.0;
    const Vec3 head = TargetHeadPoint(target);
    if (!ProjectPoint(snapshot, head, &headX, &headY)) {
        return false;
    }
    if (!ProjectBounds(snapshot, target, &bounds)) {
        return target.hasHead && Length(head - snapshot.camera) >= 35.0;
    }
    if (!std::isfinite(headX) || !std::isfinite(headY)) {
        return false;
    }
    const double tolerance = std::max(3.0, static_cast<double>(snapshot.gameHeight) * 0.004);
    return headX >= bounds.left - tolerance && headX <= bounds.right + tolerance &&
           headY >= bounds.top - tolerance && headY <= bounds.bottom + tolerance;
}

Vec3 LeadAimPoint(const Snapshot& snapshot, const Target& target) {
    const Vec3 head = TargetHeadPoint(target);
    if (!g_predictionEnabled) {
        return head;
    }

    // Prefer the equipped weapon's authoritative projectile data.  This uses
    // the measured flight time for horizontal target motion and applies the
    // exact vertical drop needed to place the projectile on the head.
    Vec3 ballisticAimPoint = {};
    if (BuildBallisticAimPoint(snapshot, target, &ballisticAimPoint)) {
        return ballisticAimPoint;
    }
    if (!g_snapshot.valid || !g_previousSnapshot.valid) {
        return head;
    }

    // Compensate only the measured authoritative head motion.  This follows
    // slide/jump animation and snapshot delay without extrapolating bounds or
    // inventing a target position when the bone is stationary.
    Vec3 relativeVelocity = ClampMagnitude(
        EstimatedHeadCameraRelativeVelocity(target), kAimMaxRelativeVelocity);
    const double speed = Length(relativeVelocity);
    if (!std::isfinite(speed) || speed < kAimMinLatencyCompensationSpeed) {
        return head;
    }

    const double snapshotAge = std::max(0.0, UnixNow() - snapshot.timestamp);
    double compensationTime = std::clamp(
        snapshotAge + kAimSnapshotLeadSeconds,
        0.0,
        kAimMaxSnapshotLeadSeconds);
    const double distance = Length(head - snapshot.camera);
    if (std::isfinite(distance) && distance <= kAimDirectRangeMeters) {
        // Close targets are already large on screen; keep the bone point
        // nearly current instead of leading past a crouch transition.
        compensationTime = std::min(compensationTime, 0.018);
    }
    if (IsScopedFov(snapshot.fov)) {
        if (speed < kScopedMovementMinSpeedMetersPerSecond) {
            return head;
        }
        // A narrow scope magnifies small lead errors.  Compensate only the
        // input/snapshot delay, then lock the projected point to the bone.
        compensationTime = std::min(
            compensationTime, kScopedMovementInputLeadSeconds);
    }

    Vec3 compensation = ClampMagnitude(
        relativeVelocity * compensationTime, kAimMaxLeadMeters);
    // Do not lead the vertical bone.  Jump/crouch height is read from the
    // current authoritative frame; vertical prediction is a common source of
    // visible up/down oscillation.
    compensation.y = 0.0;
    return head + compensation;
}

bool ProjectAimPoint(const Snapshot& snapshot, const Target& target, const RECT& client,
                     double* x, double* y, Vec3* world) {
    const Vec3 currentHead = TargetHeadPoint(target);
    double currentGameX = 0.0;
    double currentGameY = 0.0;
    if (!ProjectPoint(snapshot, currentHead, &currentGameX, &currentGameY)) {
        return false;
    }
    Vec3 leadingHead = LeadAimPoint(snapshot, target);
    double gameX = 0.0;
    double gameY = 0.0;
    if (!ProjectPoint(snapshot, leadingHead, &gameX, &gameY)) {
        leadingHead = currentHead;
        gameX = currentGameX;
        gameY = currentGameY;
    }
    const double leadScreenDistance = std::hypot(gameX - currentGameX, gameY - currentGameY);
    const double maxLeadScreenPixels = HasValidProjectileBallistics(snapshot)
        ? kAimMaxBallisticLeadScreenPixels
        : kAimMaxLeadScreenPixels;
    if (!std::isfinite(leadScreenDistance) || leadScreenDistance > maxLeadScreenPixels) {
        leadingHead = currentHead;
        gameX = currentGameX;
        gameY = currentGameY;
    }
    const double scaleX = static_cast<double>(client.right - client.left) / static_cast<double>(snapshot.gameWidth);
    const double scaleY = static_cast<double>(client.bottom - client.top) / static_cast<double>(snapshot.gameHeight);
    *x = gameX * scaleX;
    *y = gameY * scaleY;
    if (world) {
        *world = leadingHead;
    }
    return std::isfinite(*x) && std::isfinite(*y);
}

bool AimVisibilityDataUnavailable(const Snapshot& snapshot) {
    // The isolated range can expose robot rows before it exposes the local
    // combat avatar.  In that state a failed physics raycast is not evidence
    // that the authoritative head is blocked; keep aim acquisition alive
    // until the local-player count returns.
    return snapshot.hasTargetCounts && snapshot.playerTargetCount == 0 &&
           snapshot.robotTargetCount > 0;
}

bool BuildAimCandidate(const Snapshot& snapshot, const Target& target, const RECT& client,
                       double maximumDistance, AimCandidate* output,
                       bool lockedMode = false, bool allowInvisible = false) {
    const bool visibilityUnavailable = AimVisibilityDataUnavailable(snapshot);
    if (target.dead ||
        (g_visibilityEnabled && !target.visible && !allowInvisible &&
         !visibilityUnavailable)) {
        return false;
    }
    Vec3 currentHead = {};
    // The aim path only accepts the bone returned by the injected runtime.
    // Bounds-derived head estimates are suitable for display fallback, not
    // for firing decisions.
    if (!TryGetAuthoritativeHead(target, &currentHead)) {
        return false;
    }
    const double headDistance = Length(currentHead - snapshot.camera);
    if (!std::isfinite(headDistance) || headDistance <= 0.10 ||
        headDistance > g_maxTargetDistanceMeters + 2.0) {
        return false;
    }
    double headGameX = 0.0;
    double headGameY = 0.0;
    if (!ProjectPoint(snapshot, currentHead, &headGameX, &headGameY)) {
        return false;
    }
    const double scaleX = static_cast<double>(client.right - client.left) / static_cast<double>(snapshot.gameWidth);
    const double scaleY = static_cast<double>(client.bottom - client.top) / static_cast<double>(snapshot.gameHeight);
    const double headX = headGameX * scaleX;
    const double headY = headGameY * scaleY;
    const double width = static_cast<double>(client.right - client.left);
    const double height = static_cast<double>(client.bottom - client.top);
    if (!lockedMode &&
        (headX < 1.0 || headY < 1.0 || headX > width - 1.0 || headY > height - 1.0)) {
        return false;
    }
    const double selectDeltaX = headX - width * 0.5;
    const double selectDeltaY = headY - height * 0.5;
    const double selectionDistance = std::hypot(selectDeltaX, selectDeltaY);
    if (!lockedMode && selectionDistance > maximumDistance) {
        return false;
    }

    Vec3 aimWorld = {};
    double aimX = headX;
    double aimY = headY;
    if (!ProjectAimPoint(snapshot, target, client, &aimX, &aimY, &aimWorld)) {
        return false;
    }
    if (aimX < 1.0 || aimY < 1.0 || aimX > width - 1.0 || aimY > height - 1.0) {
        aimWorld = currentHead;
        aimX = headX;
        aimY = headY;
    }
    *output = {&target, aimX, aimY, aimWorld, selectionDistance};
    return true;
}

bool FindAimCandidate(const Snapshot& snapshot, const RECT& client, AimCandidate* output) {
    const double maxDistance = AimFovRadius(client);
    const double now = UnixNow();

    // Once a target is acquired, keep that identity until it is dead or has
    // genuinely disappeared.  A temporary off-screen projection, crouch pose,
    // visibility miss, or another player crossing the reticle must not switch
    // the lock to a different target.
    if (!g_aimLockedKey.empty()) {
        for (const Target& target : snapshot.targets) {
            if (target.key != g_aimLockedKey) {
                continue;
            }
            if (target.dead) {
                ClearAimLock();
                return false;
            }
            const bool visibilityUnavailable = AimVisibilityDataUnavailable(snapshot);
            g_aimLockLastSeenTime = now;
            if (target.visible || !g_visibilityEnabled || visibilityUnavailable) {
                g_aimLockLastVisibleTime = now;
            }
            const bool allowInvisible = !g_visibilityEnabled || target.visible ||
                visibilityUnavailable ||
                now - g_aimLockLastVisibleTime <= kAimLockVisibilityGraceSeconds;
            AimCandidate locked;
            if (BuildAimCandidate(snapshot, target, client, maxDistance, &locked,
                                  true, allowInvisible)) {
                *output = locked;
                return true;
            }
            return false;
        }
        if (now - g_aimLockLastSeenTime <= kAimLockRetentionSeconds) {
            return false;
        }
        ClearAimLock();
        return false;
    }

    AimCandidate best;
    for (const Target& target : snapshot.targets) {
        AimCandidate candidate;
        if (!BuildAimCandidate(snapshot, target, client, maxDistance, &candidate)) {
            continue;
        }
        // The primary ordering is always the current head's distance from the
        // screen center.  Key order only breaks exact ties between overlaps.
        if (candidate.distanceToCrosshair < best.distanceToCrosshair ||
            (std::abs(candidate.distanceToCrosshair - best.distanceToCrosshair) < 0.25 &&
             best.target && candidate.target->key < best.target->key)) {
            best = candidate;
        }
    }

    if (!best.target) {
        ClearAimLock();
        return false;
    }
    g_aimLockedKey = best.target->key;
    g_aimLockLastSeenTime = now;
    g_aimLockLastVisibleTime = now;
    g_lastAimTargetSwitchTime = now;
    *output = best;
    return true;
}

bool BuildCalibratedAimMouseDelta(const Snapshot& snapshot, const RECT& client,
                                  const Vec3& aimWorld, const POINT& aimPoint,
                                  LONG* deltaX, LONG* deltaY) {
    MouseCalibration calibration;
    const double defaultRadiansPerRawMouse = IsScopedFov(snapshot.fov)
        ? kDefaultScopedRadiansPerRawMouse
        : kDefaultHipRadiansPerRawMouse;
    calibration.yawRadiansPerRawMouse = defaultRadiansPerRawMouse;
    calibration.pitchRadiansPerRawMouse = defaultRadiansPerRawMouse;
    // Use camera/raw-input measurements only after enough consistent samples;
    // one recoil or synthetic-input frame must not change aim sensitivity.
    const MouseCalibration learned = CalibrationForFov(snapshot.fov);
    const auto validLearnedScale = [defaultRadiansPerRawMouse](double value) {
        if (!std::isfinite(value) || value * defaultRadiansPerRawMouse <= 0.0) {
            return false;
        }
        const double ratio = std::abs(value / defaultRadiansPerRawMouse);
        return std::isfinite(ratio) && ratio >= 0.55 && ratio <= 1.80;
    };
    const int minimumLearnedSamples = IsScopedFov(snapshot.fov) ? 2 : 6;
    if (learned.yawSamples >= minimumLearnedSamples &&
        learned.pitchSamples >= minimumLearnedSamples &&
        validLearnedScale(learned.yawRadiansPerRawMouse) &&
        validLearnedScale(learned.pitchRadiansPerRawMouse)) {
        calibration.yawRadiansPerRawMouse = learned.yawRadiansPerRawMouse;
        calibration.pitchRadiansPerRawMouse = learned.pitchRadiansPerRawMouse;
    }
    constexpr double kPi = 3.14159265358979323846;
    const double clientHeight = static_cast<double>(client.bottom - client.top);
    const double clientWidth = static_cast<double>(client.right - client.left);
    const double gameHeight = static_cast<double>(snapshot.gameHeight);
    const double gameWidth = static_cast<double>(snapshot.gameWidth);
    if (clientHeight <= 1.0 || clientWidth <= 1.0 ||
        gameHeight <= 1.0 || gameWidth <= 1.0) {
        return false;
    }
    const double fovRadians = std::clamp(snapshot.fov, 1.0, 150.0) * kPi / 180.0;
    const double focalLength = gameHeight / (2.0 * std::tan(fovRadians * 0.5));
    if (!std::isfinite(focalLength) || focalLength <= 1.0 ||
        std::abs(calibration.yawRadiansPerRawMouse) < 1e-7 ||
        std::abs(calibration.pitchRadiansPerRawMouse) < 1e-7) {
        return false;
    }

    const double pixelX = static_cast<double>(aimPoint.x) - clientWidth * 0.5;
    double pixelY = static_cast<double>(aimPoint.y) - clientHeight * 0.5;
    if (std::abs(pixelY) <= kAimVerticalDeadzonePixels) {
        pixelY = 0.0;
    }
    const double gamePixelX = pixelX * gameWidth / clientWidth;
    const double gamePixelY = pixelY * gameHeight / clientHeight;
    double requiredYaw = -std::atan(gamePixelX / focalLength);
    double requiredPitch = -std::atan(gamePixelY / focalLength);
    const Vec3 aimRelative = aimWorld - snapshot.camera;
    const double aimDistance = Length(aimRelative);
    const double horizontalDistance = std::hypot(aimRelative.x, aimRelative.z);
    const bool useWorldAngles = std::isfinite(aimDistance) &&
        aimDistance >= kAimWorldAngleCorrectionDistanceMeters &&
        std::isfinite(horizontalDistance) && horizontalDistance > 0.01 &&
        std::abs(snapshot.roll) < 0.15;
    if (useWorldAngles) {
        // At long range, derive the correction directly from the authoritative
        // world head and camera angles.  This avoids losing sub-pixel head
        // movement through window scaling or narrow-scope projection.
        const double desiredYaw = std::atan2(-aimRelative.x, -aimRelative.z);
        const double desiredPitch = std::atan2(aimRelative.y, horizontalDistance);
        requiredYaw = WrapAngleDelta(snapshot.yaw, desiredYaw);
        requiredPitch = desiredPitch - snapshot.pitch;
    }
    const double pixelDistance = std::hypot(pixelX, pixelY);
    double gain = kAimFineGain;
    if (pixelDistance > kAimFineControlWindowPixels) {
        const double blend = std::clamp(
            (pixelDistance - kAimFineControlWindowPixels) / 90.0, 0.0, 1.0);
        gain = kAimFineGain + (kAimCoarseGain - kAimFineGain) * blend;
    }
    if (IsScopedFov(snapshot.fov)) {
        gain *= 1.08;
    }

    const double rawX = requiredYaw / calibration.yawRadiansPerRawMouse;
    const double rawY = requiredPitch / calibration.pitchRadiansPerRawMouse;
    if (!std::isfinite(rawX) || !std::isfinite(rawY) ||
        std::abs(rawX) > kAimMaxCalibratedMouseDelta ||
        std::abs(rawY) > kAimMaxCalibratedMouseDelta) {
        return false;
    }
    // Do not carry fractional input into the next frame.  The residual
    // integrator turns one-pixel rounding into alternating left/right or
    // up/down commands when the authoritative head moves by a fraction of a
    // pixel.
    const double commandRawX = rawX * gain;
    const double verticalGain = IsScopedFov(snapshot.fov)
        ? kAimScopedVerticalGain
        : kAimVerticalGain;
    const double commandRawY = rawY * gain * verticalGain;
    const LONG maxHorizontalStep = IsScopedFov(snapshot.fov)
        ? kAimMaxScopedMouseStep
        : kAimMaxHipMouseStep;
    const LONG maxVerticalStep = IsScopedFov(snapshot.fov)
        ? kAimMaxScopedVerticalStep
        : kAimMaxHipVerticalStep;
    const double clampedRawX = std::clamp(commandRawX,
                                          -static_cast<double>(maxHorizontalStep),
                                          static_cast<double>(maxHorizontalStep));
    const double clampedRawY = std::clamp(commandRawY,
                                          -static_cast<double>(maxVerticalStep),
                                          static_cast<double>(maxVerticalStep));
    *deltaX = static_cast<LONG>(std::lround(clampedRawX));
    *deltaY = static_cast<LONG>(std::lround(clampedRawY));
    g_aimResidualRawX = 0.0;
    g_aimResidualRawY = 0.0;
    return true;
}

bool FindAimPoint(const Snapshot& snapshot, const RECT& client, POINT* output, Vec3* world) {
    AimCandidate candidate;
    if (!FindAimCandidate(snapshot, client, &candidate) || !candidate.target) {
        g_aimResidualRawX = 0.0;
        g_aimResidualRawY = 0.0;
        return false;
    }
    output->x = static_cast<LONG>(std::lround(candidate.x));
    output->y = static_cast<LONG>(std::lround(candidate.y));
    if (world) {
        *world = candidate.world;
    }
    return true;
}

void DrawLine(HDC hdc, int x1, int y1, int x2, int y2);

void DrawAimFov(HDC hdc, const RECT& client) {
    if (!g_fovVisible) {
        return;
    }
    const int centerX = (client.right - client.left) / 2;
    const int centerY = (client.bottom - client.top) / 2;
    const int radius = static_cast<int>(std::lround(AimFovRadius(client)));
    const HGDIOBJ oldBrush = SelectObject(hdc, GetStockObject(HOLLOW_BRUSH));
    if (!g_fovPen) {
        g_fovPen = CreatePen(PS_SOLID, 1, RGB(242, 242, 242));
    }
    if (!g_fovDisabledPen) {
        g_fovDisabledPen = CreatePen(PS_SOLID, 1, RGB(130, 130, 130));
    }
    HPEN pen = g_aimEnabled ? g_fovPen : g_fovDisabledPen;
    const HGDIOBJ oldPen = SelectObject(hdc, pen);
    Ellipse(hdc, centerX - radius, centerY - radius, centerX + radius, centerY + radius);
    SelectObject(hdc, oldBrush);
    SelectObject(hdc, oldPen);
}

void ApplyControlFont(HWND control) {
    if (control && g_controlFont) {
        SendMessageW(control, WM_SETFONT, reinterpret_cast<WPARAM>(g_controlFont), TRUE);
    }
}

void UpdateFovLabel() {
    if (!g_fovLabel) {
        return;
    }
    const int radius = static_cast<int>(std::lround(g_aimFovRadiusPixels));
    const std::wstring label = L"FOV radius: " + std::to_wstring(radius) + L" px";
    SetWindowTextW(g_fovLabel, label.c_str());
}

void UpdateTargetRangeLabel() {
    if (!g_targetRangeLabel) {
        return;
    }
    const int distance = static_cast<int>(std::lround(g_maxTargetDistanceMeters));
    const std::wstring label = L"Detection range: " + std::to_wstring(distance) + L" m";
    SetWindowTextW(g_targetRangeLabel, label.c_str());
}

void UpdateWeaponLabel() {
    if (!g_weaponLabel) {
        return;
    }
    std::wstring label = L"Weapon data: waiting";
    if (g_snapshot.valid && g_snapshot.weaponItemId > 0) {
        label = L"Weapon #" + std::to_wstring(g_snapshot.weaponItemId) + L"  |  " +
                std::to_wstring(static_cast<int>(std::lround(g_snapshot.projectileSpeed))) + L" m/s";
        if (g_snapshot.projectileGravity > 0.0) {
            std::wostringstream gravity;
            gravity << std::fixed << std::setprecision(1) << g_snapshot.projectileGravity;
            label += L"  |  drop " + gravity.str();
        }
    }
    if (label != g_lastWeaponText) {
        SetWindowTextW(g_weaponLabel, label.c_str());
        g_lastWeaponText = label;
    }
}

void UpdateLiveDiagnostics() {
    if (!g_liveDiagnosticsLabel) {
        return;
    }
    std::wostringstream details;
    if (!g_snapshot.valid) {
        details << L"Live: waiting for exporter";
    } else if (g_snapshot.hasExporterStatus && !g_snapshot.exporterReady) {
        details << L"Live: waiting for match entity";
    } else {
        details << L"Live: " << g_snapshot.targets.size() << L" targets | 30 Hz source";
        const Target* target = FindTargetByKey(g_snapshot, g_aimLockedKey);
        if (target) {
            const double distance = Length(TargetHeadPoint(*target) - g_snapshot.camera);
            const double speed = Length(EstimatedRelativeVelocity(*target));
            const double flight = g_snapshot.projectileSpeed > 1.0
                ? distance / g_snapshot.projectileSpeed : 0.0;
            details << std::fixed << std::setprecision(1)
                    << L"\nAim: " << distance << L" m | " << speed << L" m/s | "
                    << std::setprecision(0) << flight * 1000.0 << L" ms";
        }
    }
    const std::wstring text = details.str();
    if (text != g_lastDiagnosticsText) {
        SetWindowTextW(g_liveDiagnosticsLabel, text.c_str());
        g_lastDiagnosticsText = text;
    }
}

void SyncControlWindow() {
    if (!g_controlWindow) {
        return;
    }
    if (g_espCheckbox) {
        SendMessageW(g_espCheckbox, BM_SETCHECK, g_espEnabled ? BST_CHECKED : BST_UNCHECKED, 0);
    }
    if (g_tracerCheckbox) {
        SendMessageW(g_tracerCheckbox, BM_SETCHECK, g_tracersEnabled ? BST_CHECKED : BST_UNCHECKED, 0);
    }
    if (g_aimCheckbox) {
        SendMessageW(g_aimCheckbox, BM_SETCHECK, g_aimEnabled ? BST_CHECKED : BST_UNCHECKED, 0);
    }
    if (g_visibilityCheckbox) {
        SendMessageW(g_visibilityCheckbox, BM_SETCHECK, g_visibilityEnabled ? BST_CHECKED : BST_UNCHECKED, 0);
    }
    if (g_leadCheckbox) {
        SendMessageW(g_leadCheckbox, BM_SETCHECK, g_predictionEnabled ? BST_CHECKED : BST_UNCHECKED, 0);
    }
    if (g_fovVisibleCheckbox) {
        SendMessageW(g_fovVisibleCheckbox, BM_SETCHECK, g_fovVisible ? BST_CHECKED : BST_UNCHECKED, 0);
    }
    if (g_fovSlider) {
        SendMessageW(g_fovSlider, TBM_SETPOS, TRUE, static_cast<LPARAM>(std::lround(g_aimFovRadiusPixels)));
    }
    if (g_targetRangeSlider) {
        SendMessageW(g_targetRangeSlider, TBM_SETPOS, TRUE,
                     static_cast<LPARAM>(std::lround(g_maxTargetDistanceMeters)));
    }
    UpdateFovLabel();
    UpdateTargetRangeLabel();
    UpdateWeaponLabel();
    UpdateLiveDiagnostics();
}

void PositionControlWindow() {
    if (!g_controlWindow) {
        return;
    }
    constexpr int kWidth = 306;
    constexpr int kHeight = 468;
    RECT game = {};
    int left = 24;
    int top = 24;
    if (TargetClientRect(&game)) {
        left = game.right + 12;
        top = game.top + 24;
        if (left + kWidth > GetSystemMetrics(SM_CXSCREEN)) {
            left = std::max(0, static_cast<int>(game.left) - kWidth - 12);
        }
    }
    top = std::clamp(top, 0, std::max(0, GetSystemMetrics(SM_CYSCREEN) - kHeight));
    SetWindowPos(g_controlWindow, HWND_TOPMOST, left, top, kWidth, kHeight,
                 SWP_NOACTIVATE | SWP_SHOWWINDOW);
}

void ToggleControlWindow() {
    if (!g_controlWindow) {
        return;
    }
    if (IsWindowVisible(g_controlWindow)) {
        ShowWindow(g_controlWindow, SW_HIDE);
        if (g_target) {
            SetForegroundWindow(g_target);
        }
        return;
    }
    SyncControlWindow();
    PositionControlWindow();
    SetForegroundWindow(g_controlWindow);
}

LRESULT CALLBACK ControlWindowProc(HWND hwnd, UINT message, WPARAM wparam, LPARAM lparam) {
    switch (message) {
        case WM_CREATE: {
            const HINSTANCE instance = GetModuleHandleW(nullptr);
            g_controlFont = CreateFontW(-15, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
                                        DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
                                        CLEARTYPE_QUALITY, DEFAULT_PITCH | FF_DONTCARE, L"Segoe UI");
            HWND title = CreateWindowExW(0, L"STATIC", L"CTF ESP / AIM", WS_CHILD | WS_VISIBLE,
                                          16, 12, 260, 22, hwnd, nullptr, instance, nullptr);
            g_weaponLabel = CreateWindowExW(0, L"STATIC", L"Weapon data: waiting", WS_CHILD | WS_VISIBLE,
                                              16, 37, 250, 20, hwnd, nullptr, instance, nullptr);
            g_espCheckbox = CreateWindowExW(0, L"BUTTON", L"ESP boxes", WS_CHILD | WS_VISIBLE | BS_AUTOCHECKBOX,
                                              16, 64, 220, 24, hwnd,
                                              reinterpret_cast<HMENU>(static_cast<INT_PTR>(kControlEsp)), instance, nullptr);
            g_tracerCheckbox = CreateWindowExW(0, L"BUTTON", L"Tracer lines", WS_CHILD | WS_VISIBLE | BS_AUTOCHECKBOX,
                                                 16, 88, 220, 24, hwnd,
                                                 reinterpret_cast<HMENU>(static_cast<INT_PTR>(kControlTracers)), instance, nullptr);
            g_aimCheckbox = CreateWindowExW(0, L"BUTTON", L"Aim assist (hold RMB)", WS_CHILD | WS_VISIBLE | BS_AUTOCHECKBOX,
                                              16, 112, 220, 24, hwnd,
                                              reinterpret_cast<HMENU>(static_cast<INT_PTR>(kControlAim)), instance, nullptr);
            g_visibilityCheckbox = CreateWindowExW(0, L"BUTTON", L"Visible targets only", WS_CHILD | WS_VISIBLE | BS_AUTOCHECKBOX,
                                                     16, 136, 230, 24, hwnd,
                                                     reinterpret_cast<HMENU>(static_cast<INT_PTR>(kControlVisibility)), instance, nullptr);
            g_leadCheckbox = CreateWindowExW(0, L"BUTTON", L"Distance / velocity lead", WS_CHILD | WS_VISIBLE | BS_AUTOCHECKBOX,
                                               16, 160, 230, 24, hwnd,
                                               reinterpret_cast<HMENU>(static_cast<INT_PTR>(kControlLead)), instance, nullptr);
            g_fovVisibleCheckbox = CreateWindowExW(0, L"BUTTON", L"Show aim FOV", WS_CHILD | WS_VISIBLE | BS_AUTOCHECKBOX,
                                                     16, 184, 220, 24, hwnd,
                                                     reinterpret_cast<HMENU>(static_cast<INT_PTR>(kControlFovVisible)), instance, nullptr);
            HWND fovCaption = CreateWindowExW(0, L"STATIC", L"Aim FOV", WS_CHILD | WS_VISIBLE,
                                               16, 214, 100, 20, hwnd, nullptr, instance, nullptr);
            g_fovSlider = CreateWindowExW(0, TRACKBAR_CLASSW, L"", WS_CHILD | WS_VISIBLE | TBS_AUTOTICKS,
                                            16, 232, 266, 28, hwnd,
                                            reinterpret_cast<HMENU>(static_cast<INT_PTR>(kControlFov)), instance, nullptr);
            g_fovLabel = CreateWindowExW(0, L"STATIC", L"FOV radius", WS_CHILD | WS_VISIBLE,
                                          16, 266, 170, 20, hwnd, nullptr, instance, nullptr);
            HWND rangeCaption = CreateWindowExW(0, L"STATIC", L"Detection range", WS_CHILD | WS_VISIBLE,
                                                 16, 290, 160, 20, hwnd, nullptr, instance, nullptr);
            g_targetRangeSlider = CreateWindowExW(0, TRACKBAR_CLASSW, L"", WS_CHILD | WS_VISIBLE | TBS_AUTOTICKS,
                                                    16, 308, 266, 28, hwnd,
                                                    reinterpret_cast<HMENU>(static_cast<INT_PTR>(kControlTargetRange)), instance, nullptr);
            g_targetRangeLabel = CreateWindowExW(0, L"STATIC", L"Detection range", WS_CHILD | WS_VISIBLE,
                                                  16, 342, 190, 20, hwnd, nullptr, instance, nullptr);
            g_liveDiagnosticsLabel = CreateWindowExW(0, L"STATIC", L"Live: waiting for exporter",
                                                       WS_CHILD | WS_VISIBLE,
                                                       16, 366, 266, 36, hwnd, nullptr, instance, nullptr);
            HWND exitButton = CreateWindowExW(0, L"BUTTON", L"Exit tool", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
                                               190, 410, 92, 28, hwnd,
                                               reinterpret_cast<HMENU>(static_cast<INT_PTR>(kControlExit)), instance, nullptr);
            for (HWND control : {title, g_weaponLabel, g_espCheckbox, g_tracerCheckbox, g_aimCheckbox,
                                  g_visibilityCheckbox, g_leadCheckbox, g_fovVisibleCheckbox,
                                  fovCaption, g_fovSlider, g_fovLabel, rangeCaption, g_targetRangeSlider,
                                  g_targetRangeLabel, g_liveDiagnosticsLabel, exitButton}) {
                ApplyControlFont(control);
            }
            SendMessageW(g_fovSlider, TBM_SETRANGE, TRUE, MAKELONG(70, 320));
            SendMessageW(g_fovSlider, TBM_SETTICFREQ, 25, 0);
            SendMessageW(g_targetRangeSlider, TBM_SETRANGE, TRUE,
                         MAKELONG(static_cast<int>(kMinTargetDistanceMeters),
                                  static_cast<int>(kMaxTargetDistanceMeters)));
            SendMessageW(g_targetRangeSlider, TBM_SETTICFREQ, 50, 0);
            return 0;
        }
        case WM_COMMAND: {
            switch (LOWORD(wparam)) {
                case kControlEsp:
                    g_espEnabled = SendMessageW(g_espCheckbox, BM_GETCHECK, 0, 0) == BST_CHECKED;
                    break;
                case kControlTracers:
                    g_tracersEnabled = SendMessageW(g_tracerCheckbox, BM_GETCHECK, 0, 0) == BST_CHECKED;
                    break;
                case kControlAim:
                    g_aimEnabled = SendMessageW(g_aimCheckbox, BM_GETCHECK, 0, 0) == BST_CHECKED;
                    break;
                case kControlVisibility:
                    g_visibilityEnabled = SendMessageW(g_visibilityCheckbox, BM_GETCHECK, 0, 0) == BST_CHECKED;
                    break;
                case kControlLead:
                    g_predictionEnabled = SendMessageW(g_leadCheckbox, BM_GETCHECK, 0, 0) == BST_CHECKED;
                    break;
                case kControlFovVisible:
                    g_fovVisible = SendMessageW(g_fovVisibleCheckbox, BM_GETCHECK, 0, 0) == BST_CHECKED;
                    break;
                case kControlExit:
                    if (g_overlayWindow) {
                        DestroyWindow(g_overlayWindow);
                    }
                    return 0;
                default:
                    return 0;
            }
            if (g_overlayWindow) {
                InvalidateRect(g_overlayWindow, nullptr, FALSE);
            }
            WriteExporterConfig();
            return 0;
        }
        case WM_HSCROLL:
            if (reinterpret_cast<HWND>(lparam) == g_fovSlider) {
                g_aimFovRadiusPixels = static_cast<double>(SendMessageW(g_fovSlider, TBM_GETPOS, 0, 0));
                UpdateFovLabel();
                WriteExporterConfig();
                if (g_overlayWindow) {
                    InvalidateRect(g_overlayWindow, nullptr, FALSE);
                }
            } else if (reinterpret_cast<HWND>(lparam) == g_targetRangeSlider) {
                g_maxTargetDistanceMeters = static_cast<double>(
                    SendMessageW(g_targetRangeSlider, TBM_GETPOS, 0, 0));
                WriteExporterConfig();
                UpdateTargetRangeLabel();
            }
            return 0;
        case WM_CLOSE:
            ShowWindow(hwnd, SW_HIDE);
            if (g_target) {
                SetForegroundWindow(g_target);
            }
            return 0;
        case WM_DESTROY:
            g_controlWindow = nullptr;
            g_espCheckbox = nullptr;
            g_tracerCheckbox = nullptr;
            g_aimCheckbox = nullptr;
            g_visibilityCheckbox = nullptr;
            g_leadCheckbox = nullptr;
            g_fovVisibleCheckbox = nullptr;
            g_fovSlider = nullptr;
            g_fovLabel = nullptr;
            g_targetRangeSlider = nullptr;
            g_targetRangeLabel = nullptr;
            g_weaponLabel = nullptr;
            g_liveDiagnosticsLabel = nullptr;
            if (g_controlFont) {
                DeleteObject(g_controlFont);
                g_controlFont = nullptr;
            }
            return 0;
        default:
            return DefWindowProcW(hwnd, message, wparam, lparam);
    }
}

void ApplyAimAssist(const Snapshot& snapshot, const RECT& client) {
    if (!g_aimEnabled || GetForegroundWindow() != g_target) {
        return;
    }
    if ((GetAsyncKeyState(VK_RBUTTON) & 0x8000) == 0) {
        ClearAimLock();
        return;
    }
    // Never steer from an old camera/entity frame after the exporter pauses.
    if (!std::isfinite(snapshot.timestamp) ||
        UnixNow() - snapshot.timestamp > 0.14) {
        // Preserve the target identity across a short exporter pause; only
        // discard motion/calibration state so stale input is never emitted.
        g_aimInputAwaitingX = 0;
        g_aimInputAwaitingY = 0;
        g_aimInputAwaitingUntil = 0.0;
        g_aimCalibrationProbe = {};
        g_aimResidualRawX = 0.0;
        g_aimResidualRawY = 0.0;
        g_lastAimInputTime = 0.0;
        g_lastAimSnapshotTimestamp = 0.0;
        return;
    }
    // Aim input itself changes camera angles.  Exclude it (and the next few
    // capture frames) from the passive raw-mouse calibration so vertical
    // sensitivity cannot drift into an inverted skyward correction.
    g_calibrationBlockedUntil = UnixNow() + kAimCalibrationCooldownSeconds;
    const double now = UnixNow();
    if (now >= g_aimInputAwaitingUntil) {
        g_aimInputAwaitingX = 0;
        g_aimInputAwaitingY = 0;
        g_aimInputAwaitingUntil = 0.0;
    }
    if (now - g_lastAimInputTime < kAimMinInputIntervalSeconds) {
        return;
    }
    POINT aimPoint = {};
    Vec3 aimWorld = {};
    if (!FindAimPoint(snapshot, client, &aimPoint, &aimWorld)) {
        return;
    }

    // A camera frame is the acknowledgement boundary for the previous mouse
    // command.  Never apply another command from the same frame: doing so
    // feeds stale error back into the game and produces visible oscillation.
    if (snapshot.timestamp <= g_lastAimSnapshotTimestamp + 0.000001) {
        return;
    }
    const double centerX = static_cast<double>(client.right - client.left) * 0.5;
    const double centerY = static_cast<double>(client.bottom - client.top) * 0.5;
    const double remainingX = static_cast<double>(aimPoint.x) - centerX;
    const double remainingY = static_cast<double>(aimPoint.y) - centerY;
    const double remainingDistance = std::hypot(remainingX, remainingY);
    if (remainingDistance <= kAimDeadzonePixels) {
        g_lastAimSnapshotTimestamp = snapshot.timestamp;
        g_aimResidualRawX = 0.0;
        g_aimResidualRawY = 0.0;
        return;
    }
    LONG deltaX = 0;
    LONG deltaY = 0;
    bool bootstrapCalibration = false;
    if (!BuildCalibratedAimMouseDelta(snapshot, client, aimWorld, aimPoint, &deltaX, &deltaY)) {
        if (g_aimCalibrationProbe.active) {
            return;
        }
        // Keep this fallback bounded; normal frames use the default sensitivity
        // immediately and refine it from later raw-input samples.
        deltaX = remainingX >= 0.0 ? kAimBootstrapRawMouseDelta : -kAimBootstrapRawMouseDelta;
        deltaY = remainingY >= 0.0 ? kAimBootstrapRawMouseDelta : -kAimBootstrapRawMouseDelta;
        bootstrapCalibration = true;
    }
    if (deltaX == 0 && deltaY == 0) {
        g_lastAimSnapshotTimestamp = snapshot.timestamp;
        return;
    }

    INPUT input = {};
    input.type = INPUT_MOUSE;
    input.mi.dx = deltaX;
    input.mi.dy = deltaY;
    input.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_MOVE_NOCOALESCE;
    if (SendInput(1, &input, sizeof(input)) == 1) {
        g_lastAimSnapshotTimestamp = snapshot.timestamp;
        g_lastAimInputTime = now;
        g_rawMouseXSinceSnapshot = AddClampedRawMouse(g_rawMouseXSinceSnapshot, deltaX);
        g_rawMouseYSinceSnapshot = AddClampedRawMouse(g_rawMouseYSinceSnapshot, deltaY);
        g_aimInputAwaitingX = AddClampedRawMouse(g_aimInputAwaitingX, deltaX);
        g_aimInputAwaitingY = AddClampedRawMouse(g_aimInputAwaitingY, deltaY);
        g_aimInputAwaitingUntil = now + kAimSyntheticEchoWindowSeconds;
        const MouseCalibration& calibration = CalibrationForFov(snapshot.fov);
        const bool needsScopedCalibration = IsScopedFov(snapshot.fov) &&
            (calibration.yawSamples < 8 || calibration.pitchSamples < 8) &&
            std::max(std::abs(deltaX), std::abs(deltaY)) <= 96;
        if ((bootstrapCalibration || needsScopedCalibration) &&
            g_snapshot.valid && !g_aimCalibrationProbe.active) {
            g_aimCalibrationProbe = {true, deltaX, deltaY, g_snapshot.yaw,
                                     g_snapshot.pitch, g_snapshot.fov, g_snapshot.timestamp};
        }
    }
}

void DrawLine(HDC hdc, int x1, int y1, int x2, int y2) {
    MoveToEx(hdc, x1, y1, nullptr);
    LineTo(hdc, x2, y2);
}

void DrawCornerBox(HDC hdc, const RECT& box, COLORREF color) {
    const int width = std::max(1L, box.right - box.left);
    const int height = std::max(1L, box.bottom - box.top);
    const int cornerWidth = std::max(5, static_cast<int>(width * 0.24));
    const int cornerHeight = std::max(7, static_cast<int>(height * 0.16));
    const auto drawCorners = [&](HPEN pen) {
        const HGDIOBJ oldPen = SelectObject(hdc, pen);
        DrawLine(hdc, box.left, box.top, box.left + cornerWidth, box.top);
        DrawLine(hdc, box.left, box.top, box.left, box.top + cornerHeight);
        DrawLine(hdc, box.right, box.top, box.right - cornerWidth, box.top);
        DrawLine(hdc, box.right, box.top, box.right, box.top + cornerHeight);
        DrawLine(hdc, box.left, box.bottom, box.left + cornerWidth, box.bottom);
        DrawLine(hdc, box.left, box.bottom, box.left, box.bottom - cornerHeight);
        DrawLine(hdc, box.right, box.bottom, box.right - cornerWidth, box.bottom);
        DrawLine(hdc, box.right, box.bottom, box.right, box.bottom - cornerHeight);
        SelectObject(hdc, oldPen);
    };
    if (!g_boxShadowPen) {
        g_boxShadowPen = CreatePen(PS_SOLID, 3, RGB(18, 3, 3));
    }
    if (!g_boxAccentPen) {
        g_boxAccentPen = CreatePen(PS_SOLID, 1, color);
    }
    drawCorners(g_boxShadowPen);
    drawCorners(g_boxAccentPen);
}

void DrawTracer(HDC hdc, const RECT& box, const RECT& client, COLORREF color) {
    const int startX = (client.right - client.left) / 2;
    const int startY = client.bottom - 16;
    const int endX = (box.left + box.right) / 2;
    const int endY = box.bottom;
    if (!g_boxAccentPen) {
        g_boxAccentPen = CreatePen(PS_SOLID, 1, color);
    }
    HGDIOBJ oldPen = SelectObject(hdc, g_boxAccentPen);
    DrawLine(hdc, startX, startY, endX, endY);
    SelectObject(hdc, oldPen);
}

void DrawTextShadow(HDC hdc, int x, int y, const std::wstring& text, COLORREF color) {
    SetTextColor(hdc, RGB(0, 0, 0));
    TextOutW(hdc, x + 1, y + 1, text.c_str(), static_cast<int>(text.size()));
    SetTextColor(hdc, color);
    TextOutW(hdc, x, y, text.c_str(), static_cast<int>(text.size()));
}

void DrawDetectionSummary(HDC hdc, const Snapshot& snapshot) {
    std::wstring text;
    if (snapshot.hasTargetCounts) {
        text = L"Players: " + std::to_wstring(snapshot.playerTargetCount) +
               L"  Bots: " + std::to_wstring(snapshot.robotTargetCount);
        if (snapshot.culledTargetCount > 0) {
            text += L"  Out of range: " + std::to_wstring(snapshot.culledTargetCount);
        }
    } else {
        text = L"Targets: " + std::to_wstring(snapshot.targets.size());
    }
    text += L"  Range: " +
            std::to_wstring(static_cast<int>(std::lround(g_maxTargetDistanceMeters))) + L"m";
    DrawTextShadow(hdc, 14, 14, text, RGB(242, 242, 242));
}

void DrawTarget(HDC hdc, const Snapshot& snapshot, const Target& target, const RECT& client) {
    if (target.dead) {
        return;
    }
    RECT box = {
        0, 0, 0, 0,
    };
    if (!ScaledTargetBox(snapshot, target, client, &box)) {
        return;
    }
    if (box.right < -100 || box.bottom < -100 || box.left > client.right + 100 || box.top > client.bottom + 100) {
        return;
    }

    const COLORREF boxColor = RGB(242, 242, 242);
    const COLORREF labelColor = RGB(242, 242, 242);
    if (g_tracersEnabled) {
        DrawTracer(hdc, box, client, RGB(242, 242, 242));
    }
    DrawCornerBox(hdc, box, boxColor);

    const int boxWidth = box.right - box.left;
    const int boxHeight = box.bottom - box.top;
    const bool showDistance = boxWidth >= 8 && boxHeight >= 18;
    const bool showHp = boxWidth >= 12 && boxHeight >= 34;

    std::wstring relationLabel;
    COLORREF relationColor = RGB(242, 242, 242);
    if (target.teamRelation == 1) {
        relationLabel = L"TEAM";
        relationColor = RGB(96, 226, 126);
    } else if (target.teamRelation == 2) {
        relationLabel = L"ENEMY";
        relationColor = RGB(255, 112, 112);
    }
    const std::wstring typeLabel = target.isRobot ? L"AI" : L"PLAYER";
    const std::wstring roleLabel = relationLabel.empty()
        ? typeLabel
        : relationLabel + L" | " + typeLabel;
    SIZE roleSize = {};
    GetTextExtentPoint32W(hdc, roleLabel.c_str(), static_cast<int>(roleLabel.size()), &roleSize);
    DrawTextShadow(hdc, (box.left + box.right - roleSize.cx) / 2,
                   box.top - roleSize.cy - 3, roleLabel, relationColor);

    if (!showDistance) {
        return;
    }

    const double distance = Length(target.position - snapshot.player);
    const std::wstring topLabel = std::to_wstring(static_cast<int>(std::lround(distance))) + L"m";

    SIZE topSize = {};
    GetTextExtentPoint32W(hdc, topLabel.c_str(), static_cast<int>(topLabel.size()), &topSize);
    const int roleOffset = roleSize.cy > 0 ? roleSize.cy + 3 : 0;
    DrawTextShadow(hdc, (box.left + box.right - topSize.cx) / 2,
                   box.top - topSize.cy - 3 - roleOffset, topLabel, labelColor);

    if (!showHp) {
        return;
    }

    const int hp = static_cast<int>(std::lround(std::max(0.0, target.hp)));
    const std::wstring bottomLabel = std::to_wstring(hp) + L" HP";
    SIZE bottomSize = {};
    GetTextExtentPoint32W(hdc, bottomLabel.c_str(), static_cast<int>(bottomLabel.size()), &bottomSize);
    DrawTextShadow(hdc, (box.left + box.right - bottomSize.cx) / 2, box.bottom + 3, bottomLabel, labelColor);
}

void DrawOverlay(HWND hwnd, HDC hdc) {
    RECT client = {};
    GetClientRect(hwnd, &client);
    if (!g_transparentBrush) {
        g_transparentBrush = CreateSolidBrush(kTransparentColor);
    }
    FillRect(hdc, &client, g_transparentBrush);

    if (!g_snapshot.valid || UnixNow() - g_snapshot.timestamp > kSnapshotStaleSeconds) {
        return;
    }
    const Snapshot current = g_snapshot;
    SetBkMode(hdc, TRANSPARENT);
    if (!g_overlayFont) {
        g_overlayFont = CreateFontW(-12, 0, 0, 0, FW_SEMIBOLD, FALSE, FALSE, FALSE,
                                    DEFAULT_CHARSET, OUT_OUTLINE_PRECIS, CLIP_DEFAULT_PRECIS,
                                    CLEARTYPE_QUALITY, DEFAULT_PITCH | FF_DONTCARE, L"Arial");
    }
    const HGDIOBJ oldFont = SelectObject(hdc, g_overlayFont);
    DrawAimFov(hdc, client);
    DrawDetectionSummary(hdc, current);
    if (g_espEnabled) {
        for (const Target& target : current.targets) {
            DrawTarget(hdc, current, target, client);
        }
    }
    SelectObject(hdc, oldFont);
}

bool IsOverlayContextActive() {
    const HWND foreground = GetForegroundWindow();
    if (foreground == g_target) {
        return true;
    }
    return g_controlWindow &&
           (foreground == g_controlWindow || IsChild(g_controlWindow, foreground));
}

bool InstallSnapshotExporter(std::wstring* error);

void ResetSnapshotState() {
    g_snapshot = {};
    g_previousSnapshot = {};
    g_snapshotFileVersion = {};
    ResetRawMouseCameraState();
    ClearAimLock();
    g_boxSmoothing.clear();
    g_lastWeaponText.clear();
    g_lastDiagnosticsText.clear();
}

bool RegisterRawMouseInput(HWND hwnd) {
    RAWINPUTDEVICE device = {};
    device.usUsagePage = 0x01;
    device.usUsage = 0x02;
    device.dwFlags = RIDEV_INPUTSINK;
    device.hwndTarget = hwnd;
    return RegisterRawInputDevices(&device, 1, sizeof(device)) != FALSE;
}

void UnregisterRawMouseInput() {
    RAWINPUTDEVICE device = {};
    device.usUsagePage = 0x01;
    device.usUsage = 0x02;
    device.dwFlags = RIDEV_REMOVE;
    RegisterRawInputDevices(&device, 1, sizeof(device));
}

void HandleRawMouseInput(LPARAM lparam) {
    if (GetForegroundWindow() != g_target) {
        return;
    }
    UINT size = 0;
    if (GetRawInputData(reinterpret_cast<HRAWINPUT>(lparam), RID_INPUT, nullptr, &size,
                        sizeof(RAWINPUTHEADER)) == static_cast<UINT>(-1) ||
        size < sizeof(RAWINPUT)) {
        return;
    }
    std::vector<BYTE> buffer(size);
    if (GetRawInputData(reinterpret_cast<HRAWINPUT>(lparam), RID_INPUT, buffer.data(), &size,
                        sizeof(RAWINPUTHEADER)) != size) {
        return;
    }
    const RAWINPUT* input = reinterpret_cast<const RAWINPUT*>(buffer.data());
    if (input->header.dwType != RIM_TYPEMOUSE ||
        (input->data.mouse.usFlags & MOUSE_MOVE_ABSOLUTE) != 0) {
        return;
    }
    LONG rawX = input->data.mouse.lLastX;
    LONG rawY = input->data.mouse.lLastY;
    if (UnixNow() < g_aimInputAwaitingUntil) {
        rawX -= ConsumeSyntheticRawMouse(&g_aimInputAwaitingX, rawX);
        rawY -= ConsumeSyntheticRawMouse(&g_aimInputAwaitingY, rawY);
        if (g_aimInputAwaitingX == 0 && g_aimInputAwaitingY == 0) {
            g_aimInputAwaitingUntil = 0.0;
        }
    } else {
        g_aimInputAwaitingX = 0;
        g_aimInputAwaitingY = 0;
        g_aimInputAwaitingUntil = 0.0;
    }
    g_rawMouseXSinceSnapshot = AddClampedRawMouse(g_rawMouseXSinceSnapshot, rawX);
    g_rawMouseYSinceSnapshot = AddClampedRawMouse(g_rawMouseYSinceSnapshot, rawY);
}

bool SnapshotIsFresh() {
    return g_snapshot.valid && UnixNow() - g_snapshot.timestamp <= kSnapshotStaleSeconds;
}

bool SnapshotFileIsFresh() {
    WIN32_FILE_ATTRIBUTE_DATA attributes = {};
    if (!GetFileAttributesExW(g_statePath.c_str(), GetFileExInfoStandard, &attributes)) {
        return false;
    }
    ULARGE_INTEGER written = {};
    written.LowPart = attributes.ftLastWriteTime.dwLowDateTime;
    written.HighPart = attributes.ftLastWriteTime.dwHighDateTime;
    FILETIME nowFileTime = {};
    GetSystemTimeAsFileTime(&nowFileTime);
    ULARGE_INTEGER now = {};
    now.LowPart = nowFileTime.dwLowDateTime;
    now.HighPart = nowFileTime.dwHighDateTime;
    if (now.QuadPart < written.QuadPart) {
        return true;
    }
    constexpr ULONGLONG kTicksPerSecond = 10'000'000ULL;
    return now.QuadPart - written.QuadPart <=
           static_cast<ULONGLONG>(kSnapshotStaleSeconds * kTicksPerSecond);
}

void EnsureSnapshotExporter() {
    if (!g_autoInject || !g_target || !IsWindow(g_target)) {
        return;
    }
    DWORD gamePid = 0;
    GetWindowThreadProcessId(g_target, &gamePid);
    if (gamePid == 0) {
        return;
    }
    if (gamePid != g_exporterPid) {
        g_exporterPid = 0;
    }
    const bool readySnapshot = SnapshotIsFresh() &&
        (!g_snapshot.hasExporterStatus || g_snapshot.exporterReady);
    if (!g_exporterInstallRequested && readySnapshot) {
        g_exporterPid = gamePid;
        return;
    }
    const auto now = std::chrono::steady_clock::now();
    if (g_lastExporterAttempt != std::chrono::steady_clock::time_point::min() &&
        std::chrono::duration<double>(now - g_lastExporterAttempt).count() < kExporterRetrySeconds) {
        return;
    }
    g_lastExporterAttempt = now;
    std::wstring ignored;
    if (InstallSnapshotExporter(&ignored)) {
        g_exporterPid = gamePid;
        g_exporterInstallRequested = false;
    }
}

void TrackTarget(HWND hwnd) {
    if (!g_target || !IsWindow(g_target)) {
        g_target = FindTargetWindow();
    }
    DWORD currentPid = 0;
    if (g_target) {
        GetWindowThreadProcessId(g_target, &currentPid);
    }
    if (currentPid != g_targetPid) {
        g_targetPid = currentPid;
        g_exporterPid = 0;
        g_exporterInstallRequested = true;
        g_lastExporterAttempt = std::chrono::steady_clock::time_point::min();
        ResetSnapshotState();
    }

    // Parse before deciding whether to reinject.  A status-aware exporter can
    // explicitly report that it has not found a fresh match entity yet.
    // The native exporter writes at about 30 Hz while this window repaints at
    // 125 Hz.  Avoid reparsing an unchanged text snapshot on every paint tick;
    // this keeps the high-frequency renderer from taking a CPU core away from
    // the game.
    StateFileVersion stateVersion = {};
    if (HasNewStateFileVersion(&stateVersion)) {
        Snapshot latest;
        if (ReadSnapshot(&latest)) {
            g_snapshotFileVersion = stateVersion;
            if (!g_snapshot.valid || latest.timestamp > g_snapshot.timestamp) {
                const LONG rawMouseX = g_rawMouseXSinceSnapshot;
                const LONG rawMouseY = g_rawMouseYSinceSnapshot;
                g_rawMouseXSinceSnapshot = 0;
                g_rawMouseYSinceSnapshot = 0;
                CompleteAimCalibrationProbe(latest);
                const bool stableCameraFrame = g_snapshot.valid &&
                    std::abs(g_snapshot.fov - latest.fov) <= 0.08 &&
                    UnixNow() >= g_calibrationBlockedUntil;
                if (stableCameraFrame) {
                    CalibrateRawMouseCamera(g_snapshot, latest, rawMouseX, rawMouseY);
                }
                g_previousSnapshot = g_snapshot;
                g_snapshot = std::move(latest);
                UpdateWeaponLabel();
                UpdateLiveDiagnostics();
            }
        }
    }
    EnsureSnapshotExporter();
    RECT rect = {};
    if (!TargetClientRect(&rect)) {
        WriteAimTriggerState(false);
        ShowWindow(hwnd, SW_HIDE);
        return;
    }
    if (!IsOverlayContextActive()) {
        WriteAimTriggerState(false);
        ShowWindow(hwnd, SW_HIDE);
        return;
    }

    SetWindowPos(hwnd, HWND_TOPMOST, rect.left, rect.top, rect.right - rect.left,
                 rect.bottom - rect.top, SWP_NOACTIVATE | SWP_SHOWWINDOW);
    if (g_controlWindow && IsWindowVisible(g_controlWindow)) {
        SetWindowPos(g_controlWindow, HWND_TOPMOST, 0, 0, 0, 0,
                     SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW);
    }
    if ((GetAsyncKeyState(VK_F6) & 1) != 0) {
        g_aimEnabled = !g_aimEnabled;
        WriteExporterConfig();
        SyncControlWindow();
    }
    if (!g_controlsHotkeyRegistered && (GetAsyncKeyState(VK_INSERT) & 1) != 0) {
        ToggleControlWindow();
    }
    const bool aimTriggerActive = g_aimEnabled && (GetAsyncKeyState(VK_RBUTTON) & 0x8000) != 0;
    WriteAimTriggerState(aimTriggerActive);
    if (SnapshotIsFresh()) {
        RECT client = {};
        GetClientRect(hwnd, &client);
        ApplyAimAssist(AimControlSnapshot(), client);
        UpdateLiveDiagnostics();
    }
    InvalidateRect(hwnd, nullptr, FALSE);

    const auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(
                             std::chrono::steady_clock::now() - g_started)
                             .count();
    if ((g_durationSeconds > 0 && elapsed >= g_durationSeconds) ||
        (GetAsyncKeyState(VK_F8) & 1) != 0) {
        DestroyWindow(hwnd);
    }
}

DWORD WINAPI TrackingClockThread(void*) {
    const HANDLE waits[] = {g_trackingStopEvent, g_trackingTimer};
    while (true) {
        const DWORD wait = WaitForMultipleObjects(static_cast<DWORD>(std::size(waits)), waits,
                                                  FALSE, INFINITE);
        if (wait == WAIT_OBJECT_0) {
            return 0;
        }
        if (wait != WAIT_OBJECT_0 + 1) {
            return 0;
        }
        // Keep at most one tick pending.  This avoids message-queue buildup if
        // the compositor is busy, while still taking every fresh opportunity.
        if (g_trackingMessageQueued.exchange(true, std::memory_order_acq_rel)) {
            continue;
        }
        if (!g_overlayWindow || !PostMessageW(g_overlayWindow, kTrackMessage, 0, 0)) {
            g_trackingMessageQueued.store(false, std::memory_order_release);
            return 0;
        }
    }
}

void StopTrackingClock() {
    if (g_trackingStopEvent) {
        SetEvent(g_trackingStopEvent);
    }
    if (g_trackingTimer) {
        CancelWaitableTimer(g_trackingTimer);
    }
    if (g_trackingThread) {
        WaitForSingleObject(g_trackingThread, 2000);
        CloseHandle(g_trackingThread);
        g_trackingThread = nullptr;
    }
    if (g_trackingTimer) {
        CloseHandle(g_trackingTimer);
        g_trackingTimer = nullptr;
    }
    if (g_trackingStopEvent) {
        CloseHandle(g_trackingStopEvent);
        g_trackingStopEvent = nullptr;
    }
    g_trackingMessageQueued.store(false, std::memory_order_release);
}

bool StartTrackingClock() {
    g_trackingStopEvent = CreateEventW(nullptr, TRUE, FALSE, nullptr);
    if (!g_trackingStopEvent) {
        return false;
    }
    g_trackingTimer = CreateWaitableTimerExW(nullptr, nullptr,
                                              CREATE_WAITABLE_TIMER_HIGH_RESOLUTION,
                                              TIMER_ALL_ACCESS);
    if (!g_trackingTimer) {
        // Older Windows builds do not expose high-resolution waitable timers.
        g_trackingTimer = CreateWaitableTimerW(nullptr, FALSE, nullptr);
    }
    if (!g_trackingTimer) {
        StopTrackingClock();
        return false;
    }
    LARGE_INTEGER due = {};
    due.QuadPart = -10'000LL;  // First tick in one millisecond.
    if (!SetWaitableTimer(g_trackingTimer, &due, kTrackIntervalMs, nullptr, nullptr, FALSE)) {
        StopTrackingClock();
        return false;
    }
    g_trackingThread = CreateThread(nullptr, 0, TrackingClockThread, nullptr, 0, nullptr);
    if (!g_trackingThread) {
        StopTrackingClock();
        return false;
    }
    SetThreadPriority(g_trackingThread, THREAD_PRIORITY_ABOVE_NORMAL);
    return true;
}

LRESULT CALLBACK WindowProc(HWND hwnd, UINT message, WPARAM wparam, LPARAM lparam) {
    switch (message) {
        case WM_CREATE:
            g_overlayWindow = hwnd;
            g_controlsHotkeyRegistered = RegisterHotKey(hwnd, kToggleControlsHotkey, MOD_NOREPEAT, VK_INSERT) != FALSE;
            RegisterRawMouseInput(hwnd);
            if (!StartTrackingClock()) {
                SetTimer(hwnd, kTrackTimer, kTrackIntervalMs, nullptr);
            }
            TrackTarget(hwnd);
            return 0;
        case kTrackMessage:
            g_trackingMessageQueued.store(false, std::memory_order_release);
            TrackTarget(hwnd);
            return 0;
        case WM_TIMER:
            if (wparam == kTrackTimer) {
                TrackTarget(hwnd);
            }
            return 0;
        case WM_HOTKEY:
            if (wparam == kToggleControlsHotkey) {
                ToggleControlWindow();
            }
            return 0;
        case WM_INPUT:
            HandleRawMouseInput(lparam);
            return 0;
        case WM_PAINT: {
            PAINTSTRUCT paint = {};
            HDC hdc = BeginPaint(hwnd, &paint);
            DrawOverlay(hwnd, hdc);
            EndPaint(hwnd, &paint);
            return 0;
        }
        case WM_DESTROY:
            StopTrackingClock();
            UnregisterRawMouseInput();
            if (g_controlWindow) {
                DestroyWindow(g_controlWindow);
            }
            g_overlayWindow = nullptr;
            if (g_controlsHotkeyRegistered) {
                UnregisterHotKey(hwnd, kToggleControlsHotkey);
                g_controlsHotkeyRegistered = false;
            }
            if (g_overlayFont) {
                DeleteObject(g_overlayFont);
                g_overlayFont = nullptr;
            }
            if (g_boxShadowPen) {
                DeleteObject(g_boxShadowPen);
                g_boxShadowPen = nullptr;
            }
            if (g_boxAccentPen) {
                DeleteObject(g_boxAccentPen);
                g_boxAccentPen = nullptr;
            }
            if (g_fovPen) {
                DeleteObject(g_fovPen);
                g_fovPen = nullptr;
            }
            if (g_fovDisabledPen) {
                DeleteObject(g_fovDisabledPen);
                g_fovDisabledPen = nullptr;
            }
            if (g_transparentBrush) {
                DeleteObject(g_transparentBrush);
                g_transparentBrush = nullptr;
            }
            KillTimer(hwnd, kTrackTimer);
            PostQuitMessage(0);
            return 0;
        default:
            return DefWindowProcW(hwnd, message, wparam, lparam);
    }
}

std::wstring QuoteArgument(const std::wstring& value) {
    return L"\"" + value + L"\"";
}

bool InstallSnapshotExporter(std::wstring* error) {
    DWORD gamePid = 0;
    GetWindowThreadProcessId(g_target, &gamePid);
    if (gamePid == 0) {
        *error = L"Could not resolve the game process.";
        return false;
    }

    const std::wstring root = RuntimeRoot();
    const std::wstring runner = root + L"\\remote_py_run.py";
    const std::wstring code = root + L"\\ctf_native_snapshot_code.py";
    const std::wstring output = root + L"\\remote-py-run-native-exe.json";
    if (!PathExists(runner) || !PathExists(code)) {
        *error = L"Missing remote_py_run.py or ctf_native_snapshot_code.py next to the CTF workspace.";
        return false;
    }

    std::array<wchar_t, 32768> pythonPath = {};
    const DWORD pythonLength = SearchPathW(nullptr, L"python.exe", nullptr,
                                            static_cast<DWORD>(pythonPath.size()), pythonPath.data(), nullptr);
    if (pythonLength == 0 || pythonLength >= pythonPath.size()) {
        *error = L"python.exe was not found on PATH.";
        return false;
    }

    const std::wstring command = QuoteArgument(std::wstring(pythonPath.data(), pythonLength)) + L" " +
        QuoteArgument(runner) + L" --pid " + std::to_wstring(gamePid) + L" --code-file " +
        QuoteArgument(code) + L" --out " + QuoteArgument(output) + L" --timeout-ms 7000";
    std::vector<wchar_t> commandBuffer(command.begin(), command.end());
    commandBuffer.push_back(L'\0');

    STARTUPINFOW startup = {};
    startup.cb = sizeof(startup);
    PROCESS_INFORMATION process = {};
    if (!CreateProcessW(nullptr, commandBuffer.data(), nullptr, nullptr, FALSE, CREATE_NO_WINDOW,
                        nullptr, root.c_str(), &startup, &process)) {
        *error = L"Could not start the snapshot exporter.";
        return false;
    }
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    return true;
}

void ShowAppliedNotification() {
    using MessageBoxTimeoutWFn = int (WINAPI*)(HWND, LPCWSTR, LPCWSTR, UINT, WORD, DWORD);
    const HMODULE user32 = GetModuleHandleW(L"user32.dll");
    const auto messageBoxTimeout = reinterpret_cast<MessageBoxTimeoutWFn>(
        user32 ? GetProcAddress(user32, "MessageBoxTimeoutW") : nullptr
    );
    constexpr UINT flags = MB_OK | MB_TOPMOST | MB_SETFOREGROUND | MB_ICONINFORMATION;
    if (messageBoxTimeout) {
        messageBoxTimeout(g_target, L"CTF ESP active.\nPress Insert for controls.",
                          L"CTF ESP", flags, 0, 1600);
        return;
    }
    MessageBoxW(g_target, L"CTF ESP active.\nPress Insert for controls.", L"CTF ESP", flags);
}

void ShowStartupMessage(const wchar_t* text, DWORD milliseconds = 2200) {
    using MessageBoxTimeoutWFn = int (WINAPI*)(HWND, LPCWSTR, LPCWSTR, UINT, WORD, DWORD);
    const HMODULE user32 = GetModuleHandleW(L"user32.dll");
    const auto messageBoxTimeout = reinterpret_cast<MessageBoxTimeoutWFn>(
        user32 ? GetProcAddress(user32, "MessageBoxTimeoutW") : nullptr
    );
    constexpr UINT flags = MB_OK | MB_TOPMOST | MB_SETFOREGROUND | MB_ICONINFORMATION;
    if (messageBoxTimeout) {
        messageBoxTimeout(nullptr, text, L"BloodStrike CTF ESP", flags, 0, milliseconds);
        return;
    }
    MessageBoxW(nullptr, text, L"BloodStrike CTF ESP", flags);
}

bool IsProcessRunning(const wchar_t* processName) {
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snapshot == INVALID_HANDLE_VALUE) {
        return false;
    }
    PROCESSENTRY32W entry = {};
    entry.dwSize = sizeof(entry);
    for (BOOL ok = Process32FirstW(snapshot, &entry); ok; ok = Process32NextW(snapshot, &entry)) {
        if (_wcsicmp(entry.szExeFile, processName) == 0) {
            CloseHandle(snapshot);
            return true;
        }
    }
    CloseHandle(snapshot);
    return false;
}

bool StartBloodStrikeCtfInstance(std::wstring* error) {
    const std::wstring gameRoot = L"C:\\Program Files (x86)\\bloodstrike";
    const std::wstring gameExe = gameRoot + L"\\Engine\\Binaries\\Win64\\BloodStrike.exe";
    const std::wstring gameWorkDir = gameRoot + L"\\Engine\\Binaries\\Win64";
    if (!PathExists(gameExe)) {
        *error = L"Game executable not found:\n" + gameExe;
        return false;
    }

    SetEnvironmentVariableW(L"MessiahLauncherInfo",
                            L"\\Device\\HarddiskVolume2\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe");
    SetEnvironmentVariableW(L"MessiahAppName", L"hyxd");
    SetEnvironmentVariableW(L"PYTHONPATH", RuntimeRoot().c_str());

    std::wstring command = QuoteArgument(gameExe) +
        L" --load Python --start Python --console --python-args innerdesktop --python-debug";
    std::vector<wchar_t> commandBuffer(command.begin(), command.end());
    commandBuffer.push_back(L'\0');

    STARTUPINFOW startup = {};
    startup.cb = sizeof(startup);
    PROCESS_INFORMATION process = {};
    if (!CreateProcessW(gameExe.c_str(), commandBuffer.data(), nullptr, nullptr, FALSE, 0,
                        nullptr, gameWorkDir.c_str(), &startup, &process)) {
        *error = L"Could not start BloodStrike.exe.";
        return false;
    }
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    return true;
}

HWND EnsureTargetWindowReady() {
    if (HWND target = FindTargetWindow()) {
        return target;
    }

    if (!IsProcessRunning(L"BloodStrike.exe")) {
        MessageBoxW(nullptr,
                    L"Start the BloodStrike CTF instance first, then run this EXE.",
                    L"BloodStrike CTF ESP",
                    MB_OK | MB_TOPMOST | MB_SETFOREGROUND | MB_ICONERROR);
        return nullptr;
    }

    ShowStartupMessage(L"BloodStrike is running. Waiting for the game window...");
    HWND target = WaitForTargetWindow(90);
    if (!target) {
        MessageBoxW(nullptr,
                    L"BloodStrike window was not found within 90 seconds.\nStart the CTF instance, then run this EXE again.",
                    L"BloodStrike CTF ESP",
                    MB_OK | MB_TOPMOST | MB_SETFOREGROUND | MB_ICONERROR);
    }
    return target;
}

bool CreateControlWindow(HINSTANCE instance) {
    INITCOMMONCONTROLSEX commonControls = {};
    commonControls.dwSize = sizeof(commonControls);
    commonControls.dwICC = ICC_BAR_CLASSES;
    InitCommonControlsEx(&commonControls);

    WNDCLASSW controlClass = {};
    controlClass.lpfnWndProc = ControlWindowProc;
    controlClass.hInstance = instance;
    controlClass.lpszClassName = L"CtfNativeEspControls";
    controlClass.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    if (!RegisterClassW(&controlClass) && GetLastError() != ERROR_CLASS_ALREADY_EXISTS) {
        return false;
    }

    g_controlWindow = CreateWindowExW(
        WS_EX_TOOLWINDOW | WS_EX_TOPMOST,
        controlClass.lpszClassName,
        L"CTF ESP controls",
        WS_POPUP | WS_CAPTION | WS_SYSMENU,
        0, 0, 306, 360,
        nullptr, nullptr, instance, nullptr);
    if (!g_controlWindow) {
        return false;
    }
    SyncControlWindow();
    ShowWindow(g_controlWindow, SW_HIDE);
    return true;
}

void TerminateSiblingOverlays() {
    const DWORD currentPid = GetCurrentProcessId();
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snapshot == INVALID_HANDLE_VALUE) {
        return;
    }

    PROCESSENTRY32W entry = {};
    entry.dwSize = sizeof(entry);
    for (BOOL ok = Process32FirstW(snapshot, &entry); ok; ok = Process32NextW(snapshot, &entry)) {
        if (entry.th32ProcessID == currentPid) {
            continue;
        }
        if (_wcsicmp(entry.szExeFile, L"BloodStrikeCTFESP.exe") != 0 &&
            _wcsicmp(entry.szExeFile, L"BloodStrikeCTFESP_fixed.exe") != 0 &&
            _wcsicmp(entry.szExeFile, L"BloodStrikeCTFESP_live.exe") != 0 &&
            _wcsicmp(entry.szExeFile, L"BloodStrikeCTFESP_perf.exe") != 0 &&
            _wcsicmp(entry.szExeFile, L"BloodStrikeCTFESP_final.exe") != 0 &&
            _wcsicmp(entry.szExeFile, L"BloodStrikeCTFESP_tracking.exe") != 0 &&
            _wcsicmp(entry.szExeFile, L"BloodStrikeCTFESP_instant.exe") != 0 &&
            _wcsicmp(entry.szExeFile, L"BloodStrikeCTFESP_instant_final.exe") != 0 &&
            _wcsicmp(entry.szExeFile, L"BloodStrikeCTFESP_precision.exe") != 0 &&
            _wcsicmp(entry.szExeFile, L"BloodStrikeCTFESP_session.exe") != 0 &&
            _wcsicmp(entry.szExeFile, L"BloodStrikeCTFESP_scoped.exe") != 0 &&
            _wcsicmp(entry.szExeFile, L"BloodStrikeCTFESP_motion.exe") != 0 &&
            _wcsicmp(entry.szExeFile, L"BloodStrikeCTFESP_fast.exe") != 0 &&
            _wcsicmp(entry.szExeFile, L"BloodStrikeCTFESP_trigger.exe") != 0 &&
            _wcsicmp(entry.szExeFile, L"BloodStrikeCTFESP_render.exe") != 0) {
            continue;
        }
        HANDLE process = OpenProcess(PROCESS_TERMINATE, FALSE, entry.th32ProcessID);
        if (process) {
            TerminateProcess(process, 0);
            CloseHandle(process);
        }
    }
    CloseHandle(snapshot);
}

}  // namespace

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int) {
    SetProcessDPIAware();
    timeBeginPeriod(1);
    DebugLog(L"startup");
    TerminateSiblingOverlays();
    ParseCommandLine();
    DebugLog(L"parsed command line");
    WriteExporterConfig();
    g_target = EnsureTargetWindowReady();
    if (!g_target) {
        DebugLog(L"target window not ready");
        timeEndPeriod(1);
        return 1;
    }
    DebugLog(L"target window ready");
    WNDCLASSW windowClass = {};
    windowClass.lpfnWndProc = WindowProc;
    windowClass.hInstance = instance;
    windowClass.lpszClassName = L"CtfNativeProjectedEsp";
    windowClass.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    if (!RegisterClassW(&windowClass)) {
        DebugLog(L"RegisterClass failed: " + std::to_wstring(GetLastError()));
        timeEndPeriod(1);
        return 1;
    }
    DebugLog(L"overlay class registered");

    RECT rect = {};
    if (!TargetClientRect(&rect)) {
        DebugLog(L"TargetClientRect failed");
        timeEndPeriod(1);
        return 1;
    }
    DebugLog(L"target client rect ready");
    const RECT initialClient = {0, 0, rect.right - rect.left, rect.bottom - rect.top};
    g_aimFovRadiusPixels = std::clamp(AimFovRadius(initialClient), 70.0, 320.0);
    WriteExporterConfig();
    WriteAimTriggerState(false, true);
    HWND overlay = CreateWindowExW(
        WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_TOPMOST | WS_EX_NOACTIVATE,
        windowClass.lpszClassName, L"", WS_POPUP, rect.left, rect.top,
        rect.right - rect.left, rect.bottom - rect.top, nullptr, nullptr, instance, nullptr);
    if (!overlay) {
        DebugLog(L"CreateWindowEx overlay failed: " + std::to_wstring(GetLastError()));
        return 1;
    }
    DebugLog(L"overlay window created");
    SetLayeredWindowAttributes(overlay, kTransparentColor, 255, LWA_COLORKEY);
    if (!CreateControlWindow(instance)) {
        DebugLog(L"CreateControlWindow failed: " + std::to_wstring(GetLastError()));
        DestroyWindow(overlay);
        timeEndPeriod(1);
        return 1;
    }
    DebugLog(L"control window created");
    g_started = std::chrono::steady_clock::now();
    ShowWindow(overlay, SW_SHOWNOACTIVATE);
    SyncControlWindow();
    PositionControlWindow();
    ShowWindow(g_controlWindow, SW_SHOWNOACTIVATE);
    ShowAppliedNotification();
    DebugLog(L"message loop entered");

    MSG message = {};
    while (GetMessageW(&message, nullptr, 0, 0) > 0) {
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }
    timeEndPeriod(1);
    return 0;
}
