[CmdletBinding()]
param(
    [switch] $Elevated,
    [int] $PidValue = 0,
    [string] $Module = 'ctf_esp',
    [string] $Out = 'remote-py-import-path.json',
    [string] $Stdout = 'remote-py-import-path.stdout.txt',
    [string] $SysPath = ''
)

$ErrorActionPreference = 'Stop'
$pocRoot = Split-Path -Parent $PSCommandPath

if ($PidValue -eq 0) {
    $PidValue = Get-Process -Name BloodStrike -ErrorAction Stop |
        Select-Object -First 1 -ExpandProperty Id
}

if (-not $Elevated) {
    $args = @(
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', $PSCommandPath,
        '-Elevated',
        '-PidValue', ([string] $PidValue),
        '-Module', $Module,
        '-Out', $Out,
        '-Stdout', $Stdout
    )
    if ($SysPath) {
        $args += @('-SysPath', $SysPath)
    }
    Start-Process -Verb RunAs -FilePath "$PSHOME\powershell.exe" -ArgumentList $args
    return
}

$python = (Get-Command python.exe -ErrorAction Stop).Source
$script = Join-Path $pocRoot 'remote_py_import.py'
$outPath = Join-Path $pocRoot $Out
$stdoutPath = Join-Path $pocRoot $Stdout

$pyArgs = @($script, '--pid', ([string] $PidValue), '--module', $Module, '--out', $outPath)
if ($SysPath) {
    $pyArgs += @('--sys-path', $SysPath)
}

Push-Location $pocRoot
try {
    & $python @pyArgs *> $stdoutPath
} finally {
    Pop-Location
}
