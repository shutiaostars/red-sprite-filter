@echo off
REM ============================================================================
REM  Build red-sprite-filter.exe (single portable file) on Windows.
REM
REM  Prerequisites:
REM    - Python 3.10+ installed and on PATH (python --version)
REM    - Internet access (to download ffmpeg once)
REM
REM  What this does:
REM    1. Create an isolated venv so we never touch your system Python
REM    2. Install runtime + PyInstaller from requirements.txt
REM    3. Download Windows ffmpeg/ffprobe into red_sprite_app\bin\windows
REM    4. Run PyInstaller using windows\red_sprite_filter.spec
REM
REM  Output: dist\red-sprite-filter.exe  (double-click to run, no install)
REM ============================================================================

setlocal
cd /d "%~dp0\.." || exit /b 1

echo [1/4] Creating virtual environment (venv)...
python -m venv venv || exit /b 1
call venv\Scripts\activate.bat || exit /b 1

echo [2/4] Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt || exit /b 1

echo [3/4] Downloading Windows ffmpeg/ffprobe binaries...
python windows\get_ffmpeg.py || exit /b 1

echo [4/4] Building single-file executable with PyInstaller...
pyinstaller windows\red_sprite_filter.spec --noconfirm || exit /b 1

echo.
echo ============================================================
echo  Done. Portable executable:
echo    %CD%\dist\red-sprite-filter.exe
echo  (double-click to run; no installation required)
echo ============================================================
endlocal
