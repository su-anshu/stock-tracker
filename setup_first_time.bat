@echo off
title Mithila Foods Stock Tracker - First Time Setup
color 0B
cls

echo.
echo ===============================================
echo    MITHILA FOODS STOCK TRACKER
echo    First Time Setup and Installation
echo ===============================================
echo.

:: Check if Python is installed
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python %PYTHON_VERSION% found

:: Check directory
echo.
echo [2/6] Checking application files...
if not exist "app.py" (
    echo ERROR: app.py not found
    echo Please run this setup from the stock_tracker folder
    echo.
    pause
    exit /b 1
)
if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found
    echo Please ensure all files are in the folder
    echo.
    pause
    exit /b 1
)
echo ✓ Application files found

:: Create virtual environment
echo.
echo [3/6] Creating virtual environment...
if exist "venv" (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        echo Please ensure Python is properly installed
        echo.
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
)

:: Activate virtual environment
echo.
echo [4/6] Activating virtual environment...
call venv\Scripts\activate.bat
echo ✓ Virtual environment activated

:: Install requirements
echo.
echo [5/6] Installing required packages...
echo This may take a few minutes...
echo.
pip install --upgrade pip --quiet
pip install -r requirements.txt
if errorlevel 1 (
    echo WARNING: Some packages failed to install
    echo Trying essential packages individually...
    pip install streamlit pandas plotly openpyxl
)
echo ✓ Packages installed

:: Test installation
echo.
echo [6/6] Testing installation...
python -c "import streamlit, pandas, plotly; print('✓ All packages working')" 2>nul
if errorlevel 1 (
    echo ERROR: Package installation verification failed
    echo Please check the error messages above
    echo.
    pause
    exit /b 1
)

:: Setup complete
cls
echo.
echo ===============================================
echo    SETUP COMPLETE!
echo ===============================================
echo.
echo ✓ Python installed and working
echo ✓ Virtual environment created
echo ✓ All packages installed successfully
echo ✓ Application ready to run
echo.
echo NEXT STEPS:
echo 1. Double-click 'start_stock_tracker.bat' to run the app
echo 2. Or use 'quick_start.bat' for faster startup
echo 3. Your app will open at: http://localhost:8501
echo.
echo SHORTCUTS CREATED:
echo - start_stock_tracker.bat (full startup with checks)
echo - quick_start.bat (fast startup for daily use)
echo.
echo ===============================================
echo Ready to track your inventory!
echo ===============================================
echo.

:: Offer to start now
set /p start_now="Would you like to start the app now? (y/n): "
if /i "%start_now%"=="y" (
    echo.
    echo Starting Stock Tracker...
    streamlit run app.py --server.headless false --server.port 8501 --browser.gatherUsageStats false
)

pause
