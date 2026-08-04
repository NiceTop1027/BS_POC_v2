[CmdletBinding()]
param(
    [switch] $Elevated
)

$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSCommandPath
$output = Join-Path $taskRoot 'entry-fileio.etl'
$launcher = Join-Path $taskRoot 'launch_entry_probe.ps1'
$wpr = Join-Path $env:WINDIR 'System32\wpr.exe'

if (-not $Elevated) {
    Start-Process -Verb RunAs -FilePath "$PSHOME\powershell.exe" -ArgumentList @(
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', $PSCommandPath,
        '-Elevated'
    )
    return
}

$status = & $wpr -status 2>&1 | Out-String
if ($status -notmatch 'not recording') {
    throw 'WPR is already recording; refusing to alter an existing trace.'
}

Remove-Item -LiteralPath $output -Force -ErrorAction SilentlyContinue
$recording = $false
try {
    & $wpr -start FileIO -filemode
    if ($LASTEXITCODE -ne 0) {
        throw "WPR FileIO start failed with exit code $LASTEXITCODE"
    }
    $recording = $true

    # This helper verifies BloodStrike before stopping only that named process,
    # stages the harmless marker, and launches the documented CTF entry probe.
    & $launcher -Elevated -Restart
    Start-Sleep -Seconds 18
} finally {
    if ($recording) {
        & $wpr -stop $output
        if ($LASTEXITCODE -ne 0) {
            throw "WPR stop failed with exit code $LASTEXITCODE"
        }
    }
}

Write-Host "Wrote File I/O trace: $output"
