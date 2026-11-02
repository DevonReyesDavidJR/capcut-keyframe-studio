@echo off
REM CapCut Keyframe Studio Pro - Windows Launcher
title CapCut Keyframe Studio Pro

cd /d "%~dp0"

echo =======================================================
echo  CapCut Keyframe Studio Pro (Windows)
echo =======================================================

set PY=
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 set PY=python
if not defined PY (
    where py >nul 2>nul
    if not errorlevel 1 set PY=py
)
if not defined PY (
    echo [ERROR] Khong tim thay Python. Vui long cai dat Python 3 tu https://www.python.org/
    pause
    goto end
)

REM Desktop mode needs Pillow; install it on first run if missing
%PY% -c "import PIL" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Dang cai dat thu vien can thiet [Pillow]...
    %PY% -m pip install --user -r requirements.txt
)

%PY% run.py

:end

