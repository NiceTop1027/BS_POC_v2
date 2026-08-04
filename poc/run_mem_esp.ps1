[CmdletBinding()]
param(
    [switch] $Elevated,
    [switch] $Restart,
    [switch] $NoOverlay,
    [double] $WaitSeconds = 20,
    [string] $Entry = 'ctf_esp'
)

$ErrorActionPreference = 'Stop'

$pocRoot = Split-Path -Parent $PSCommandPath
$launcher = Join-Path $pocRoot 'mem_patch_esp_launcher.py'

if (-not (Test-Path -LiteralPath $launcher)) {
    throw "Launcher not found: $launcher"
}

if (-not $Elevated) {
    $args = @(
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', $PSCommandPath,
        '-Elevated',
        '-WaitSeconds', ([string]$WaitSeconds)
    )
    if ($Restart) { $args += '-Restart' }
    if ($NoOverlay) { $args += '-NoOverlay' }
    if ($Entry) { $args += @('-Entry', $Entry) }
    Start-Process -Verb RunAs -FilePath "$PSHOME\powershell.exe" -ArgumentList $args
    return
}

$python = (Get-Command python.exe -ErrorAction Stop).Source
$pyArgs = @($launcher, '--wait', ([string]$WaitSeconds), '--entry', $Entry)
if ($Restart) { $pyArgs += '--restart' }
if ($NoOverlay) { $pyArgs += '--no-overlay' }

Push-Location $pocRoot
try {
    & $python @pyArgs
    if ($LASTEXITCODE -ne 0) {
        throw "mem_patch_esp_launcher.py failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}
