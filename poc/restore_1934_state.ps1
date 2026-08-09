[CmdletBinding()]
param(
    [switch] $Elevated
)

$ErrorActionPreference = 'Stop'

$pocRoot = Split-Path -Parent $PSCommandPath
$cppRoot = Join-Path $pocRoot 'cpp_overlay'
$report = Join-Path $pocRoot 'restore_1934_state_report.txt'

function Test-IsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not $Elevated -and -not (Test-IsAdmin)) {
    Set-Content -LiteralPath $report -Encoding UTF8 -Value "requesting_admin $(Get-Date -Format o)"
    Start-Process -Verb RunAs -WindowStyle Hidden -FilePath "$PSHOME\powershell.exe" -ArgumentList @(
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', "`"$PSCommandPath`"",
        '-Elevated'
    ) | Out-Null
    exit 0
}

Set-Content -LiteralPath $report -Encoding UTF8 -Value "start $(Get-Date -Format o)"

$targetExe = Join-Path $cppRoot 'BloodStrikeCTFESP.exe'
$baselineExe = Join-Path $cppRoot 'BloodStrikeCTFESP_playerhitbox_final.exe'
$payloadBaseline = Join-Path $pocRoot 'upload_fps_esp_maker_playerhitbox_final\ctf_native_snapshot_code.py'
$configBaseline = Join-Path $pocRoot 'upload_fps_esp_maker_playerhitbox_final\ctf_native_esp_config.txt'
$settingsBaseline = Join-Path $pocRoot 'upload_fps_esp_maker_playerhitbox_final\ctf_overlay_settings.ini'
$banBackup = Join-Path $pocRoot 'ban_report_bypass_code.py.before_server_repair_heartbeat_20260809_150910.bak'

foreach ($process in @(Get-Process -Name BloodStrikeCTFESP -ErrorAction SilentlyContinue)) {
    if ($process.ProcessName -ne 'BloodStrikeCTFESP') {
        throw "Refusing to stop unexpected process PID $($process.Id): $($process.ProcessName)"
    }
    Stop-Process -Id $process.Id -Force
}
Start-Sleep -Seconds 1

Copy-Item -LiteralPath $baselineExe -Destination $targetExe -Force
Copy-Item -LiteralPath $payloadBaseline -Destination (Join-Path $pocRoot 'ctf_native_snapshot_code.py') -Force
Copy-Item -LiteralPath $configBaseline -Destination (Join-Path $pocRoot 'ctf_native_esp_config.txt') -Force
Copy-Item -LiteralPath $settingsBaseline -Destination (Join-Path $pocRoot 'ctf_overlay_settings.ini') -Force
if (Test-Path -LiteralPath $banBackup) {
    Copy-Item -LiteralPath $banBackup -Destination (Join-Path $pocRoot 'ban_report_bypass_code.py') -Force
}

$currentPid = [System.Diagnostics.Process]::GetCurrentProcess().Id
$watchers = Get-CimInstance Win32_Process |
    Where-Object {
        $_.Name -match 'powershell' -and
        $_.CommandLine -match 'watch_ban_report_bypass\.ps1' -and
        [int]$_.ProcessId -ne $currentPid
    }
foreach ($watcher in $watchers) {
    Stop-Process -Id ([int]$watcher.ProcessId) -Force -ErrorAction SilentlyContinue
}

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $pocRoot 'restart_ctf_instance.ps1') |
    Add-Content -LiteralPath $report -Encoding UTF8
Start-Sleep -Seconds 6

Start-Process -WindowStyle Hidden -FilePath $targetExe -WorkingDirectory $cppRoot -ArgumentList @(
    '--max-distance=800',
    '--duration=0'
) | Out-Null

Start-Sleep -Seconds 12

Add-Content -LiteralPath $report -Encoding UTF8 -Value "after_start $(Get-Date -Format o)"
Get-Process -Name BloodStrike,BloodStrikeCTFESP -ErrorAction SilentlyContinue |
    Select-Object Id,ProcessName,StartTime,Responding |
    Format-Table -AutoSize |
    Out-String |
    Add-Content -LiteralPath $report -Encoding UTF8

Add-Content -LiteralPath $report -Encoding UTF8 -Value "hashes"
Get-FileHash -Algorithm SHA256 -LiteralPath @(
    $targetExe,
    (Join-Path $pocRoot 'ctf_native_snapshot_code.py'),
    (Join-Path $pocRoot 'ctf_native_esp_config.txt'),
    (Join-Path $pocRoot 'ctf_overlay_settings.ini')
) |
    Format-Table -AutoSize |
    Out-String |
    Add-Content -LiteralPath $report -Encoding UTF8

Add-Content -LiteralPath $report -Encoding UTF8 -Value "config"
Get-Content -LiteralPath (Join-Path $pocRoot 'ctf_native_esp_config.txt') |
    Add-Content -LiteralPath $report -Encoding UTF8

Add-Content -LiteralPath $report -Encoding UTF8 -Value "done $(Get-Date -Format o)"
