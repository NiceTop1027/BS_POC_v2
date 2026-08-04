[CmdletBinding()]
param(
    [switch] $Elevated,
    [int] $TargetPid = 0
)

$ErrorActionPreference = 'Stop'
$pocRoot = Split-Path -Parent $PSCommandPath
$scanner = Join-Path $pocRoot 'entity_memory_scan.py'
$out = Join-Path $pocRoot 'entity-memory-scan.json'

if (-not $TargetPid) {
    $proc = Get-Process BloodStrike -ErrorAction Stop | Select-Object -First 1
    $TargetPid = $proc.Id
}

if (-not $Elevated) {
    Start-Process -Verb RunAs -FilePath "$PSHOME\powershell.exe" -ArgumentList @(
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', $PSCommandPath,
        '-Elevated',
        '-TargetPid', ([string]$TargetPid)
    )
    return
}

$python = (Get-Command python.exe -ErrorAction Stop).Source
Push-Location $pocRoot
try {
    & $python $scanner --pid $TargetPid --out $out
    if ($LASTEXITCODE -ne 0) {
        throw "entity_memory_scan.py failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}
