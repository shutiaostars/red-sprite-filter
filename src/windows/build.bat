@echo off
REM ============================================================================
REM  Build red-sprite-filter.exe (single portable file) on Windows.
REM
REM  This script NEVER auto-closes on error: it writes a full log to build.log
REM  and pauses at the end so you can read what went wrong.
REM
REM  Prerequisites:
REM    - Python 3.10+ installed and on PATH (python --version)
REM    - Internet access (to download ffmpeg once)
REM
REM  Output: dist\red-sprite-filter.exe  (double-click to run, no install)
REM ============================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0\.." || (echo [ERROR] Cannot locate project root & pause & exit /b 1)

set "PYTHONIOENCODING=utf-8"
set "LOG=%CD%\build.log"
echo [%date% %time%] Build started > "%LOG%"

REM --- Helper: log a line both to console and to build.log -------------------
set "STEP=init"
call :log "=== red-sprite-filter Windows build ==="

REM --- 0) Sanity: python available? ------------------------------------------
where python >nul 2>nul
if errorlevel 1 (
    call :log "[ERROR] 'python' not found on PATH. Install Python 3.10+ and tick 'Add python.exe to PATH'."
    goto :fail
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do call :log "[python] %%v"

REM --- 1) venv ----------------------------------------------------------------
set "STEP=venv"
call :log "[1/4] Creating virtual environment (venv)..."
python -m venv venv >> "%LOG%" 2>&1
if errorlevel 1 (call :log "[ERROR] venv creation failed (see build.log)"; goto :fail)
call venv\Scripts\activate.bat >> "%LOG%" 2>&1
if errorlevel 1 (call :log "[ERROR] could not activate venv (see build.log)"; goto :fail)

REM --- 2) dependencies --------------------------------------------------------
set "STEP=deps"
call :log "[2/4] Installing dependencies (numpy, Pillow, pywebview, PyInstaller)..."
python -m pip install --upgrade pip >> "%LOG%" 2>&1
pip install -r requirements.txt >> "%LOG%" 2>&1
if errorlevel 1 (call :log "[ERROR] dependency install failed (see build.log)"; goto :fail)

REM --- 3) ffmpeg (warning, not fatal) ----------------------------------------
set "STEP=ffmpeg"
call :log "[3/4] Downloading Windows ffmpeg/ffprobe binaries..."
python windows\get_ffmpeg.py >> "%LOG%" 2>&1
if errorlevel 1 (
    call :log "[WARN] ffmpeg download failed - the build will continue, but you must copy"
    call :log "       ffmpeg.exe and ffprobe.exe next to the final .exe (see build.log)."
) else (
    call :log "[ffmpeg] download OK"
)

REM --- 4) PyInstaller ---------------------------------------------------------
set "STEP=pyinstaller"
call :log "[4/4] Building single-file executable with PyInstaller..."
pyinstaller windows\red_sprite_filter.spec --noconfirm >> "%LOG%" 2>&1
if errorlevel 1 (call :log "[ERROR] PyInstaller build failed (see build.log)"; goto :fail)

REM --- 5) Copy ffmpeg next to the exe as a fallback ---------------------------
set "STEP=copy-bins"
if exist "red_sprite_app\bin\windows\ffmpeg.exe" (
    copy /Y "red_sprite_app\bin\windows\ffmpeg.exe" "dist\" >> "%LOG%" 2>&1
    copy /Y "red_sprite_app\bin\windows\ffprobe.exe" "dist\" >> "%LOG%" 2>&1
    call :log "[bins] copied ffmpeg/ffprobe next to the exe"
)

REM --- Verify ----------------------------------------------------------------
if exist "dist\red-sprite-filter.exe" (
    call :log ""
    call :log "============================================================"
    call :log "  DONE. Portable executable:"
    call :log "    %CD%\dist\red-sprite-filter.exe"
    call :log "  (double-click to run; no installation required)"
    call :log "============================================================"
    call :log ""
    goto :ok
) else (
    call :log "[ERROR] dist\red-sprite-filter.exe was NOT produced."
    call :log "        Check build.log for PyInstaller errors."
    goto :fail
)

:fail
call :log ""
call :log "[BUILD FAILED] See build.log for details, then fix and re-run build.bat."
echo.
echo Build failed. Press any key to close (details are in build.log).
pause
exit /b 1

:ok
echo.
echo Build succeeded. Press any key to close.
pause
exit /b 0

REM ---- subroutine: append a line to console AND build.log --------------------
:log
echo %*
echo %* >> "%LOG%"
goto :eof
