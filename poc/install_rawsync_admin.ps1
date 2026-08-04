$ErrorActionPreference = 'Stop'

$pocRoot = Split-Path -Parent $PSCommandPath
$overlayDir = Join-Path $pocRoot 'cpp_overlay'
$source = Join-Path $overlayDir 'BloodStrikeCTFESP_scopeaim_test.exe'
$target = Join-Path $overlayDir 'BloodStrikeCTFESP.exe'

if (-not (Test-Path -LiteralPath $source)) {
    throw "Raw camera synchronization build is missing: $source"
}

Get-Process -Name BloodStrikeCTFESP -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 750
Copy-Item -LiteralPath $source -Destination $target -Force
Start-Process -FilePath $target -ArgumentList '--max-distance=800'
