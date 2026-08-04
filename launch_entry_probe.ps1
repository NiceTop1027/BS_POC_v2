[CmdletBinding()]
param(
    [switch] $Elevated,
    [switch] $Restart
)

$ErrorActionPreference = 'Stop'

$taskRoot = Split-Path -Parent $PSCommandPath
$gameRoot = 'C:\Program Files (x86)\bloodstrike'
$gameExe = Join-Path $gameRoot 'Engine\Binaries\Win64\BloodStrike.exe'
$gameWorkDir = Split-Path -Parent $gameExe
$source = Join-Path $taskRoot 'ctf_marker.py'
$destination = Join-Path $gameRoot 'LocalData\Patch\ctf_marker.py'
$marker = Join-Path $taskRoot 'ctf-import.marker'

if (-not (Test-Path -LiteralPath $gameExe)) {
    throw "Game executable not found: $gameExe"
}

if (-not $Elevated) {
    $existing = Get-Process -Name BloodStrike -ErrorAction SilentlyContinue
    if ($existing -and -not $Restart) {
        $ids = ($existing | Select-Object -ExpandProperty Id) -join ', '
        throw "BloodStrike is already running (PID $ids). Close it first, or rerun with -Restart for this scoped entry-probe restart."
    }

    $elevatedArgs = @(
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', $PSCommandPath,
        '-Elevated'
    )
    if ($Restart) {
        $elevatedArgs += '-Restart'
    }

    Start-Process -Verb RunAs -FilePath "$PSHOME\powershell.exe" -ArgumentList @(
        $elevatedArgs
    )
    return
}

if ($Restart) {
    $existing = Get-Process -Name BloodStrike -ErrorAction SilentlyContinue
    foreach ($process in $existing) {
        if ($process.ProcessName -ne 'BloodStrike') {
            throw "Refusing to stop unexpected process PID $($process.Id): $($process.ProcessName)"
        }
        Stop-Process -Id $process.Id -Force
    }
    if ($existing) {
        $existing | Wait-Process -Timeout 10
    }
} elseif (Get-Process -Name BloodStrike -ErrorAction SilentlyContinue) {
    throw 'BloodStrike is already running. This elevated probe will not create a second instance.'
}

Remove-Item -LiteralPath $marker -Force -ErrorAction SilentlyContinue
Copy-Item -LiteralPath $source -Destination $destination -Force

# Launcher-parity invariants observed from the normal local CTF instance.
$env:PYTHONPATH = $taskRoot
$env:MessiahLauncherInfo = '\Device\HarddiskVolume2\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
$env:MessiahAppName = 'hyxd'

$child = Start-Process -PassThru -FilePath $gameExe -WorkingDirectory $gameWorkDir -ArgumentList @(
    '--load', 'Python',
    '--start', 'Python',
    '--console',
    '--python-args', 'innerdesktop',
    '--python-entry', 'ctf_marker',
    '--python-debug'
)

Write-Host "Started entry probe PID $($child.Id)."
Write-Host "Expected harmless proof: $marker"
