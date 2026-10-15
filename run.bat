@echo off
cd /d "%~dp0"

REM Check venv exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found.
    pause
    exit /b 1
)

REM Activate venv and launch FRYDAY GUI (no banner, no pause)
call "venv\Scripts\activate.bat"
start /min "" venv\Scripts\pythonw.exe main.py
exit
