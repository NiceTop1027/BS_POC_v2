[CmdletBinding()]
param(
    [switch] $Elevated,
    [switch] $Restart,
    [switch] $NoStart
)

$ErrorActionPreference = 'Stop'

$taskRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$pocRoot = Split-Path -Parent $PSCommandPath
$gameRoot = 'C:\Program Files (x86)\bloodstrike'
$gameExe = Join-Path $gameRoot 'Engine\Binaries\Win64\BloodStrike.exe'
$gameWorkDir = Split-Path -Parent $gameExe
$source = Join-Path $pocRoot 'ctf_esp.py'
$overlayExe = Join-Path $pocRoot 'cpp_overlay\esp_overlay.exe'
$overlayBuild = Join-Path $pocRoot 'build_cpp_overlay.ps1'
$patchScriptDir = Join-Path $gameRoot 'LocalData\Patch\Script\Python'
$destination = Join-Path $patchScriptDir 'ctf_esp.py'
$evidence = Join-Path $pocRoot 'ctf_esp_evidence.log'
$overlayEvidence = Join-Path $pocRoot 'cpp_esp_overlay_evidence.log'

if (-not (Test-Path -LiteralPath $gameExe)) {
    throw "Game executable not found: $gameExe"
}
if (-not (Test-Path -LiteralPath $source)) {
    throw "PoC module not found: $source"
}
if (-not (Test-Path -LiteralPath $overlayBuild)) {
    throw "Overlay build script not found: $overlayBuild"
}

if (-not $Elevated) {
    $args = @(
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', $PSCommandPath,
        '-Elevated'
    )
    if ($Restart) { $args += '-Restart' }
    if ($NoStart) { $args += '-NoStart' }
    Start-Process -Verb RunAs -FilePath "$PSHOME\powershell.exe" -ArgumentList $args
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
    throw 'BloodStrike is already running. Use -Restart for the isolated CTF instance.'
}

New-Item -ItemType Directory -Force -Path $patchScriptDir | Out-Null
Copy-Item -LiteralPath $source -Destination $destination -Force
Remove-Item -LiteralPath $evidence -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $overlayEvidence -Force -ErrorAction SilentlyContinue

if (-not (Test-Path -LiteralPath $overlayExe)) {
    Write-Host "Building C++ ESP overlay..."
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $overlayBuild
}

Write-Host "Staged PoC module:"
Write-Host "  $destination"
Write-Host "Evidence log:"
Write-Host "  $evidence"
Write-Host "Overlay evidence log:"
Write-Host "  $overlayEvidence"

if ($NoStart) {
    return
}

# Launcher-parity invariants observed from a normal BloodStrike CTF instance.
$env:MessiahLauncherInfo = '\Device\HarddiskVolume2\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
$env:MessiahAppName = 'hyxd'

$arguments = @(
    '--load', 'Python',
    '--start', 'Python',
    '--console',
    '--useReloadImporter',
    '--setImporterPath', 'Script/Python',
    '--python-args', 'innerdesktop',
    '--python-entry', 'ctf_esp',
    '--python-debug'
)

$child = Start-Process -PassThru -FilePath $gameExe -WorkingDirectory $gameWorkDir -ArgumentList $arguments
Write-Host "Started BloodStrike PoC PID $($child.Id)."
Start-Sleep -Seconds 4

Start-Process -FilePath $overlayExe -ArgumentList @(
    '--duration=180',
    '--title=BloodStrike',
    "--log=$overlayEvidence"
)
Write-Host "Started C++ visible ESP overlay."
Write-Host 'Wait 5-10 seconds, then inspect cpp_esp_overlay_evidence.log and capture the BloodStrike window.'
