[CmdletBinding()]
param(
    [switch] $Elevated
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSCommandPath

if (-not $Elevated) {
    Start-Process -Verb RunAs -FilePath "$PSHOME\powershell.exe" -ArgumentList @(
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', $PSCommandPath,
        '-Elevated'
    )
    return
}

$gamePid = Get-Process -Name BloodStrike -ErrorAction Stop |
    Select-Object -First 1 -ExpandProperty Id
$python = (Get-Command python.exe -ErrorAction Stop).Source

& $python (Join-Path $root 'remote_py_run.py') `
    --pid $gamePid `
    --code-file (Join-Path $root 'ctf_filter_probe_code.py') `
    --out (Join-Path $root 'remote-py-run-filter-probe-current.json') `
    --timeout-ms 20000 `
    *> (Join-Path $root 'remote-py-run-filter-probe-current.stdout.txt')
