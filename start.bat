@echo off
REM Start the Discord video downloader bot on Windows

echo === Starting Discord Video Downloader Bot ===
echo.

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found. Run setup.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python bot.py
pause
