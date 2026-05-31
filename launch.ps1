# JH-MultiAgent local launcher for Windows PowerShell 5.1+
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Write-Header {
    Clear-Host
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  JH-MultiAgent Launcher" -ForegroundColor Cyan
    Write-Host "  $Root" -ForegroundColor DarkGray
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Pause-Launcher {
    Write-Host ""
    Read-Host "Press Enter to return to the menu"
}

function Invoke-CheckedCommand {
    param(
        [string]$Name,
        [string]$Command,
        [string[]]$Arguments
    )

    $cmd = Get-Command $Command -ErrorAction SilentlyContinue
    if ($null -eq $cmd) {
        Write-Host "[ERROR] ${Name} command was not found: $Command" -ForegroundColor Red
        return $false
    }

    & $Command @Arguments
    return $true
}

while ($true) {
    Write-Header
    Write-Host "  [1] Open dashboard" -ForegroundColor White
    Write-Host "  [2] Run selfcheck" -ForegroundColor White
    Write-Host "  [3] Start Claude orchestrator" -ForegroundColor White
    Write-Host "  [4] Start Codex review session" -ForegroundColor White
    Write-Host "  [5] Open project folder" -ForegroundColor White
    Write-Host "  [6] Exit" -ForegroundColor White
    Write-Host ""
    Write-Host "Rule: stop for user approval before any worker call." -ForegroundColor Yellow
    Write-Host ""

    $choice = Read-Host "Select (1-6)"
    switch ($choice) {
        "1" {
            Invoke-CheckedCommand "dashboard" "python" @("-X", "utf8", "dashboard.py") | Out-Null
            Pause-Launcher
        }
        "2" {
            powershell -ExecutionPolicy Bypass -File "_shared\run-selfcheck.ps1"
            Pause-Launcher
        }
        "3" {
            Write-Host ""
            Write-Host "Starting Claude Code orchestrator." -ForegroundColor Green
            Write-Host "New tasks must follow the standard lifecycle and stop before worker calls." -ForegroundColor Yellow
            Write-Host ""
            Invoke-CheckedCommand "Claude Code" "claude" @() | Out-Null
            break
        }
        "4" {
            Write-Host ""
            Write-Host "Starting Codex review session." -ForegroundColor Green
            Write-Host ""
            Invoke-CheckedCommand "Codex" "codex" @() | Out-Null
            break
        }
        "5" {
            Start-Process explorer.exe -ArgumentList $Root
        }
        "6" {
            break
        }
        default {
            Write-Host "Invalid choice." -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    }
}
