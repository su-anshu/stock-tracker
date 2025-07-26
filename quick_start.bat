@echo off
title Stock Tracker - Quick Start
cls

echo Starting Mithila Foods Stock Tracker...
echo.

:: Quick check and start
cd /d "%~dp0"
if exist "venv\Scripts\activate.bat" call venv\Scripts\activate.bat
streamlit run app.py --server.headless false --server.port 8501 --browser.gatherUsageStats false

pause
