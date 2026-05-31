@echo off
chcp 65001 >nul
title JH-MultiAgent Launcher
set "ROOT=%~dp0"
cd /d "%ROOT%"
if errorlevel 1 (
    echo [ERROR] Project path was not found: %ROOT%
    pause
    exit /b 1
)

powershell -ExecutionPolicy Bypass -File "%ROOT%launch.ps1"
if errorlevel 1 (
    echo.
    echo [ERROR] launch.ps1 failed.
    pause
    exit /b 1
)
