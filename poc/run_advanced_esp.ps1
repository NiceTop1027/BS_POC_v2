$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$pidValue = (Get-Process -Name BloodStrike -ErrorAction Stop | Select-Object -First 1 -ExpandProperty Id)
$python = (Get-Command python.exe -ErrorAction Stop).Source

$runner = (Resolve-Path .\remote_py_run.py).Path
$code = (Resolve-Path .\ctf_live_esp_code.py).Path
$out = Join-Path $Root "remote-py-run-box-esp-install.json"

python -m py_compile .\remote_py_run.py .\ctf_live_esp_code.py

Start-Process -Verb RunAs -FilePath $python -WorkingDirectory $Root -ArgumentList @(
    $runner,
    "--pid", [string]$pidValue,
    "--code-file", $code,
    "--out", $out
) -Wait

Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -like "*esp_hud_overlay.py*" -and $_.Name -match "python" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

Write-Host "Box ESP installed for BloodStrike PID $pidValue"
Write-Host "Evidence: $Root\ctf_live_esp.log"
