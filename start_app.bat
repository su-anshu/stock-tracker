@echo off
echo Starting Mithila Foods Stock Tracker...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo Installing/updating requirements...
pip install -r requirements.txt

REM Check if streamlit is installed
streamlit --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Streamlit...
    pip install streamlit
)

REM Start the application
echo.
echo Starting Stock Tracker Application...
echo Open your browser and go to: http://localhost:8501
echo.
echo Press Ctrl+C to stop the application
echo.

streamlit run app.py

pause
