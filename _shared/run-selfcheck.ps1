# JH-MultiAgent Self-Check (Windows PowerShell 5.1+)
# Run: powershell -ExecutionPolicy Bypass -File _shared\run-selfcheck.ps1
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$BASE = Split-Path $PSScriptRoot -Parent
$PASS = 0
$FAIL = 0
$WARN = 0

function Check {
    param([string]$label, $ok, [string]$note = "")
    $suffix = if ($note) { "  -- $note" } else { "" }
    if ($ok -eq $true) {
        Write-Host "  [OK]  $label$suffix" -ForegroundColor Green
        $script:PASS++
    } elseif ($ok -eq "warn") {
        Write-Host "  [WN]  $label$suffix" -ForegroundColor Yellow
        $script:WARN++
    } else {
        Write-Host "  [NG]  $label$suffix" -ForegroundColor Red
        $script:FAIL++
    }
}

Write-Host ""
Write-Host "=== JH-MultiAgent Self-Check ===" -ForegroundColor Cyan
Write-Host "Base: $BASE"
Write-Host ""

# -- Vault path from integrations.md ----------------------------------
$vaultPath = $null
$bridgePath = $null
$intFile = Join-Path $BASE "_shared\integrations.md"
if (Test-Path $intFile) {
    $intText = [System.IO.File]::ReadAllText($intFile, [System.Text.Encoding]::UTF8)
    if ($intText -match "obsidian-agent-brain-system") {
        # Extract drive root (everything up to obsidian-agent-brain-system)
        if ($intText -match '`([A-Z]:\\[^`]+obsidian-agent-brain-system)') {
            $vaultRoot = $Matches[1]
            $vaultPath = Join-Path $vaultRoot "ObsidianVault\03_Projects\tools\JH-MultiAgent.md"
            $bridgePath = Join-Path $vaultRoot "scripts\obsidian_agent_bridge.py"
        }
    }
}
# Fallback to hardcoded default if parsing failed
if (-not $vaultPath) {
    $defaultRoot = "G:\내 드라이브\obsidian-agent-brain-system"
    $vaultPath = "$defaultRoot\ObsidianVault\03_Projects\tools\JH-MultiAgent.md"
    $bridgePath = "$defaultRoot\scripts\obsidian_agent_bridge.py"
}

# -- Core files -------------------------------------------------------
Write-Host "[ Core Files ]" -ForegroundColor White
$files = @(
    "CLAUDE.md", "AGENTS.md", "README.md",
    "_shared/routing.md", "_shared/config.md",
    "_shared/integrations.md", "_shared/learnings.md",
    "_templates/task.md", "_templates/worker-brief.md"
)
foreach ($f in $files) {
    Check $f (Test-Path (Join-Path $BASE $f))
}

# -- tasks/ -----------------------------------------------------------
Write-Host ""
Write-Host "[ tasks/ ]" -ForegroundColor White
$tasksDir = Join-Path $BASE "tasks"
if (Test-Path $tasksDir) {
    $taskDirs = Get-ChildItem $tasksDir -Directory | Where-Object { $_.Name -ne ".gitkeep" }
    $taskCount = $taskDirs.Count
    Check "tasks/ exists" $true "$taskCount dir(s)"
    foreach ($td in $taskDirs) {
        $taskMd = Join-Path $td.FullName "task.md"
        Check "tasks/$($td.Name)/task.md" (Test-Path $taskMd)
    }
} else {
    Check "tasks/ exists" $false "folder missing"
}

# -- Tools ------------------------------------------------------------
Write-Host ""
Write-Host "[ Tools ]" -ForegroundColor White

$claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
if ($null -ne $claudeCmd) {
    Check "claude CLI" $true $claudeCmd.Source
} else {
    Check "claude CLI" $false "not installed"
}

$codexCmd = Get-Command codex -ErrorAction SilentlyContinue
if ($null -ne $codexCmd) {
    Check "codex CLI" $true $codexCmd.Source
} else {
    Check "codex CLI" $false "not installed"
}

$pyCmd = Get-Command python -ErrorAction SilentlyContinue
if ($null -ne $pyCmd) {
    $pyVer = (& python --version 2>&1) -join ""
    Check "python" $true $pyVer
} else {
    Check "python" $false "not installed"
}

# -- .mcp.json --------------------------------------------------------
Write-Host ""
Write-Host "[ MCP Config ]" -ForegroundColor White
$mcpFile = Join-Path $BASE ".mcp.json"
if (Test-Path $mcpFile) {
    Check ".mcp.json" $true $mcpFile
} else {
    Check ".mcp.json" $false "missing"
}

# -- Obsidian / Bucky -------------------------------------------------
Write-Host ""
Write-Host "[ Obsidian / Bucky Bridge ]" -ForegroundColor White

$brainLink = Join-Path $BASE "_local\brain-system-link.md"
if (Test-Path $brainLink) {
    Check "Registration (_local/brain-system-link.md)" $true "registered"
} else {
    Check "Registration (_local/brain-system-link.md)" "warn" "not registered"
}

if (Test-Path $vaultPath) {
    Check "Vault project file" $true $vaultPath
} else {
    Check "Vault project file" "warn" "not found: $vaultPath"
}

if (Test-Path $bridgePath) {
    $bridgeOut = & python -X utf8 $bridgePath --status 2>&1
    $bridgeOk = ($LASTEXITCODE -eq 0)
    $bridgeFirst = ($bridgeOut | Select-Object -First 1)
    Check "vault bridge (--status)" $bridgeOk "$bridgeFirst"
} else {
    Check "vault bridge script" "warn" "not present (OK if auto-sync=inactive)"
}

# -- config.md --------------------------------------------------------
Write-Host ""
Write-Host "[ Config ]" -ForegroundColor White
$configFile = Join-Path $BASE "_shared\config.md"
if (Test-Path $configFile) {
    $configText = [System.IO.File]::ReadAllText($configFile, [System.Text.Encoding]::UTF8)
    if ($configText -match "gemini_enabled\s*[:=]\s*(true|false)") {
        Check "gemini_enabled" $true "value: $($Matches[1])"
    } else {
        Check "gemini_enabled" "warn" "key not found in _shared/config.md"
    }
} else {
    Check "_shared/config.md" $false "missing"
}

# -- Summary ----------------------------------------------------------
Write-Host ""
Write-Host "---------------------------------" -ForegroundColor DarkGray
$total = $PASS + $FAIL + $WARN
Write-Host "Total: $total   " -NoNewline
Write-Host "OK $PASS" -ForegroundColor Green -NoNewline
Write-Host "  WN $WARN" -ForegroundColor Yellow -NoNewline
Write-Host "  NG $FAIL" -ForegroundColor Red
if ($FAIL -gt 0) {
    Write-Host "=> Fix NG items above." -ForegroundColor Red
} elseif ($WARN -gt 0) {
    Write-Host "=> WN items: expected if auto-sync/bridge are inactive." -ForegroundColor Yellow
} else {
    Write-Host "=> All invariants passed." -ForegroundColor Green
}
Write-Host ""