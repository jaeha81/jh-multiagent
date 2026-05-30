@echo off
chcp 65001 >nul
title JH-MultiAgent Launcher
cd /d "D:\ai프로젝트\JH-MultiAgent"
if errorlevel 1 (
    echo [ERROR] 경로를 찾을 수 없습니다: D:\ai프로젝트\JH-MultiAgent
    pause
    exit /b 1
)

:menu
cls
echo.
echo ====================================
echo   JH-MultiAgent Launcher
echo   %CD%
echo ====================================
echo.
echo   [1] 대시보드 보기
echo   [2] Claude 오케스트레이터 시작
echo   [3] 종료
echo.
set /p choice=선택 (1/2/3):

if "%choice%"=="1" (
    python dashboard.py
    pause
    goto menu
)
if "%choice%"=="2" (
    echo.
    echo Claude Code 시작합니다. CLAUDE.md 자동 로드됨.
    echo.
    claude
    goto :EOF
)
if "%choice%"=="3" (
    exit /b 0
)
echo 잘못된 입력입니다.
pause
goto menu
