@echo off
echo === VCDS Free - Setup ===
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

echo Creating virtual environment...
python -m venv venv

echo Activating and installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo === Setup complete ===
echo To start: run start.bat
pause
