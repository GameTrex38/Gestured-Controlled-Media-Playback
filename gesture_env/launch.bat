@echo off
echo Starting Gesture Media Player...
cd /d "%~dp0"
if exist "gesture_env\Scripts\activate.bat" (
    call gesture_env\Scripts\activate.bat
    python main_app.py
) else (
    echo Virtual environment not found.
    echo Please run setup.py first.
    pause
)
