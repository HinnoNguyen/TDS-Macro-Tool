@echo off
cd /d "%~dp0"
start "" pythonw.exe main.py
if %errorlevel% neq 0 (
    echo Pythonw.exe failed, attempting to run with python.exe...
    python main.py
    pause
)
