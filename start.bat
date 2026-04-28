@echo off
echo ================================
echo Hima Informatika Web App
echo ================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found.
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies if needed
echo Checking dependencies...
pip install -r requirements.txt >nul 2>&1

REM Initialize database if it doesn't exist
if not exist "instance\hima.db" (
    echo Initializing database...
    python init_db.py
    echo.
)

echo Starting Flask development server...
echo.
python run.py

pause
