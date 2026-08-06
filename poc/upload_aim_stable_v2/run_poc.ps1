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
$exe = Join-Path $root 'BloodStrikeCTFESP.exe'

if (-not (Test-Path -LiteralPath $exe)) {
    throw "BloodStrikeCTFESP.exe not found in $root"
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

Start-Process -WindowStyle Hidden -FilePath $exe -WorkingDirectory $root -ArgumentList @(
    "--max-distance=$MaxDistance",
    "--duration=$DurationSeconds"
)
