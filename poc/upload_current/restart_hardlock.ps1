[CmdletBinding()]
param(
    [switch] $Elevated,
    [ValidateRange(50, 800)]
    [int] $MaxDistance = 800,
    [ValidateRange(0, 86400)]
    [int] $DurationSeconds = 0
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSCommandPath
$canonicalExe = Join-Path $root 'BloodStrikeCTFESP.exe'
$hardlockExe = Join-Path $root 'BloodStrikeCTFESP_fast.exe'

if (-not (Test-Path -LiteralPath $hardlockExe)) {
    throw "Hard-lock build not found: $hardlockExe"
}

if (-not $Elevated) {
    $args = @(
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', $PSCommandPath,
        '-Elevated',
        '-MaxDistance', ([string] $MaxDistance),
        '-DurationSeconds', ([string] $DurationSeconds)
    )
    Start-Process -Verb RunAs -FilePath "$PSHOME\powershell.exe" -ArgumentList $args
    return
}

Get-Process -Name BloodStrikeCTFESP -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 400

Copy-Item -LiteralPath $hardlockExe -Destination $canonicalExe -Force

Start-Process -WindowStyle Hidden -FilePath $canonicalExe -WorkingDirectory $root -ArgumentList @(
    "--max-distance=$MaxDistance",
    "--duration=$DurationSeconds"
)
