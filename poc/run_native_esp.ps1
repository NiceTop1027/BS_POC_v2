[CmdletBinding()]
param(
    [switch] $Elevated,
    [ValidateRange(0, 86400)]
    [int] $DurationSeconds = 0,
    [ValidateRange(50, 800)]
    [int] $MaxDistance = 800
)

$ErrorActionPreference = 'Stop'

if (-not $Elevated) {
    $args = @(
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', $PSCommandPath,
        '-Elevated',
        '-DurationSeconds', ([string] $DurationSeconds),
        '-MaxDistance', ([string] $MaxDistance)
    )
    Start-Process -Verb RunAs -FilePath "$PSHOME\powershell.exe" -ArgumentList $args -Wait
    exit $LASTEXITCODE
}

$pocRoot = Split-Path -Parent $PSCommandPath
$buildScript = Join-Path $pocRoot 'build_cpp_overlay.ps1'
$overlay = Join-Path $pocRoot 'cpp_overlay\BloodStrikeCTFESP.exe'

@('BloodStrikeCTFESP', 'native_esp_overlay', 'native_esp_aim_fov', 'native_esp_aim_test') | ForEach-Object {
    Get-Process -Name $_ -ErrorAction SilentlyContinue | Stop-Process -Force
}

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $buildScript -OutputName 'BloodStrikeCTFESP.exe'
if ($LASTEXITCODE -ne 0) {
    throw "C++ overlay build failed with exit code $LASTEXITCODE"
}

Start-Process -WindowStyle Hidden -FilePath $overlay -WorkingDirectory (Split-Path -Parent $overlay) -ArgumentList @(
    "--duration=$DurationSeconds",
    "--max-distance=$MaxDistance"
)

Write-Output "BloodStrikeCTFESP is running. It reconnects after a game or match transition; Insert opens controls, RMB tracks, F6 toggles aim, F7 toggles no recoil, and F8 exits."
