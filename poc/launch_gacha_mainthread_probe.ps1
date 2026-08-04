[CmdletBinding()]
param(
    [switch] $Elevated,
    [switch] $Restart
)

$ErrorActionPreference = 'Stop'

$taskRoot = $PSScriptRoot
$gameRoot = 'C:\Program Files (x86)\bloodstrike'
$gameExe = Join-Path $gameRoot 'Engine\Binaries\Win64\BloodStrike.exe'
$gameWorkDir = Split-Path -Parent $gameExe
$source = Join-Path $taskRoot 'ctf_gacha_mainthread_probe.py'
$destination = Join-Path $gameRoot 'LocalData\Patch\ctf_gacha_mainthread_probe.py'

if (-not (Test-Path -LiteralPath $gameExe)) {
    throw "Game executable not found: $gameExe"
}

if (-not $Elevated) {
    $args = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PSCommandPath, '-Elevated')
    if ($Restart) {
        $args += '-Restart'
    }
    Start-Process -Verb RunAs -FilePath "$PSHOME\powershell.exe" -ArgumentList $args
    return
}

if (-not $Restart) {
    throw 'Use -Restart so the entry module is loaded at game startup.'
}

$existing = Get-Process -Name BloodStrike -ErrorAction SilentlyContinue
foreach ($process in $existing) {
    Stop-Process -Id $process.Id -Force
}
if ($existing) {
    $existing | Wait-Process -Timeout 10
}

Copy-Item -LiteralPath $source -Destination $destination -Force

$env:PYTHONPATH = $taskRoot
$env:MessiahLauncherInfo = '\Device\HarddiskVolume2\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
$env:MessiahAppName = 'hyxd'

$child = Start-Process -PassThru -FilePath $gameExe -WorkingDirectory $gameWorkDir -ArgumentList @(
    '--load', 'Python',
    '--start', 'Python',
    '--console',
    '--python-args', 'innerdesktop',
    '--python-entry', 'ctf_gacha_mainthread_probe',
    '--python-debug'
)

Write-Output "Started main-thread gacha probe PID $($child.Id)."
