[CmdletBinding()]
param(
    [switch] $Clean,
    [string] $OutputName = 'BloodStrikeCTFESP.exe'
)

$ErrorActionPreference = 'Stop'

$pocRoot = Split-Path -Parent $PSCommandPath
$src = Join-Path $pocRoot 'cpp_overlay\esp_overlay.cpp'
$outDir = Join-Path $pocRoot 'cpp_overlay'
$exe = Join-Path $outDir $OutputName

if (-not (Test-Path -LiteralPath $src)) {
    throw "C++ source not found: $src"
}

if ($Clean) {
    Remove-Item -LiteralPath $exe -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath (Join-Path $outDir 'esp_overlay.obj') -Force -ErrorAction SilentlyContinue
}

$vsDev = 'C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat'
if (Test-Path -LiteralPath $vsDev) {
    $cmd = @(
        "`"$vsDev`" -arch=x64 -host_arch=x64 >nul",
        "cl /nologo /EHsc /std:c++17 /O2 /DUNICODE /D_UNICODE /Fe:`"$exe`" `"$src`" user32.lib gdi32.lib shell32.lib winmm.lib comctl32.lib /link /SUBSYSTEM:WINDOWS /MANIFESTUAC:`"level='requireAdministrator' uiAccess='false'`""
    ) -join ' && '
    cmd.exe /d /s /c $cmd
    if ($LASTEXITCODE -ne 0) {
        throw "cl.exe build failed with exit code $LASTEXITCODE"
    }
} else {
    $zig = Get-Command zig.exe -ErrorAction SilentlyContinue
    if (-not $zig) {
        throw 'No Visual Studio developer prompt or zig.exe compiler found.'
    }
    & $zig.Source c++ -target x86_64-windows-gnu -municode -O2 -DUNICODE -D_UNICODE `
        -o $exe $src -luser32 -lgdi32 -lshell32 -lwinmm -lcomctl32
    if ($LASTEXITCODE -ne 0) {
        throw "zig c++ build failed with exit code $LASTEXITCODE"
    }
}

Get-Item -LiteralPath $exe | Select-Object FullName, Length, LastWriteTime
