@echo off
REM Setup script for Windows development/testing
REM Creates a virtual environment, installs dependencies, and prepares .env

echo === Discord Video Downloader Bot - Windows Setup ===
echo.

REM Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.11+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists.
)

REM Activate and install dependencies
echo Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

REM Create .env from example if it doesn't exist
if not exist ".env" (
    echo.
    echo Creating .env from .env.example...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit .env and set your DISCORD_TOKEN before running the bot.
) else (
    echo .env file already exists.
)

echo.
echo === Setup complete! ===
echo.
echo Next steps:
echo   1. Edit .env and set your DISCORD_TOKEN
echo   2. Run start.bat to start the bot
echo   3. Run run_tests.bat to run the test suite
echo.
pause
