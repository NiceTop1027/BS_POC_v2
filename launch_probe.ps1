[CmdletBinding()]
param(
    [switch] $Elevated
)

$ErrorActionPreference = 'Stop'

$taskRoot = Split-Path -Parent $PSCommandPath
$gameRoot = 'C:\Program Files (x86)\bloodstrike'
$gameExe = Join-Path $gameRoot 'Engine\Binaries\Win64\BloodStrike.exe'
$gameWorkDir = Split-Path -Parent $gameExe

if (-not (Test-Path -LiteralPath $gameExe)) {
    throw "Game executable not found: $gameExe"
}

if (-not $Elevated) {
    $existing = Get-Process -Name BloodStrike -ErrorAction SilentlyContinue
    if ($existing) {
        $ids = ($existing | Select-Object -ExpandProperty Id) -join ', '
        throw "BloodStrike is already running (PID $ids). Close it first; this script never force-closes the game."
    }

    Start-Process -Verb RunAs -FilePath "$PSHOME\powershell.exe" -ArgumentList @(
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', $PSCommandPath,
        '-Elevated'
    )
    return
}

# These are the launcher-created process invariants observed from the local CTF instance.
$env:PYTHONPATH = $taskRoot
$env:MessiahLauncherInfo = '\Device\HarddiskVolume2\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
$env:MessiahAppName = 'hyxd'

$child = Start-Process -PassThru -FilePath $gameExe -WorkingDirectory $gameWorkDir -ArgumentList @(
    '--load', 'Python',
    '--start', 'Python',
    '--console',
    '--python-args', 'innerdesktop',
    '--python-debug'
)

Write-Host "Started probe process PID $($child.Id)."
Write-Host "The only staged startup effect is $taskRoot\sitecustomize.py writing python-startup.marker."
