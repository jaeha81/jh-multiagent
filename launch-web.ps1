# Launch the JH-MultiAgent local web control panel.
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$LocalDir = Join-Path $Root "_local"
$UrlFile = Join-Path $LocalDir "web-control-panel-url.txt"
$OutLog = Join-Path $LocalDir "web-control-panel.out.log"
$ErrLog = Join-Path $LocalDir "web-control-panel.err.log"

if (-not (Test-Path $LocalDir)) {
    New-Item -ItemType Directory -Path $LocalDir | Out-Null
}

$python = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $python) {
    Write-Host "[ERROR] python command was not found." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8765/health" -TimeoutSec 2
    if ($health.ok -eq $true) {
        $url = "http://127.0.0.1:8765/"
        & cmd.exe /c start "" "$url"
        Write-Host "JH-MultiAgent web control panel opened: $url" -ForegroundColor Green
        exit 0
    }
} catch {
    # No existing server; start one below.
}

if (Test-Path $UrlFile) {
    Remove-Item -LiteralPath $UrlFile -Force
}

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $python.Source
$psi.Arguments = '-X utf8 web_control_panel.py --host 127.0.0.1 --port 8765'
$psi.WorkingDirectory = $Root
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.RedirectStandardOutput = $false
$psi.RedirectStandardError = $false
try {
    if ($psi.EnvironmentVariables.ContainsKey("PATH") -and $psi.EnvironmentVariables.ContainsKey("Path")) {
        $psi.EnvironmentVariables.Remove("PATH")
    }
} catch {
}

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $psi
[void]$process.Start()

$url = $null
for ($i = 0; $i -lt 50; $i++) {
    if (Test-Path $UrlFile) {
        $url = (Get-Content -LiteralPath $UrlFile -Encoding UTF8 | Select-Object -First 1).Trim()
        if ($url) { break }
    }
    Start-Sleep -Milliseconds 200
}

if (-not $url) {
    Write-Host "[ERROR] Web control panel did not start." -ForegroundColor Red
    Write-Host "stdout: $OutLog"
    Write-Host "stderr: $ErrLog"
    Read-Host "Press Enter to exit"
    exit 1
}

& cmd.exe /c start "" "$url"
Write-Host "JH-MultiAgent web control panel opened: $url" -ForegroundColor Green
Write-Host "Server PID: $($process.Id)" -ForegroundColor DarkGray
