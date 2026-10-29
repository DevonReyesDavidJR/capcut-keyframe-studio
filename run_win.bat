@echo off
REM CapCut Keyframe Studio Pro - Windows Launcher
title CapCut Keyframe Studio Pro

cd /d "%~dp0"

echo =======================================================
echo  CapCut Keyframe Studio Pro (Windows)
echo =======================================================

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python run.py
    goto end
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py run.py
    goto end
)

echo [ERROR] Khong tim thay Python. Vui long cai dat Python 3 tu https://www.python.org/
pause

:end
