@echo off
REM Run the test suite on Windows

echo === Running Tests ===
echo.

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found. Run setup.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
pip install -r requirements-dev.txt --quiet
pytest tests/ -v
echo.
pause
