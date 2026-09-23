@echo off
setlocal
cd /d "%~dp0"
title Build With Me #1 - Explore Data
set "PYTHONDONTWRITEBYTECODE=1"
if not exist "_local\.venv\Scripts\python.exe" (
    echo Run START_HERE.bat first to set up Python and build the database.
    pause
    exit /b 1
)
"_local\.venv\Scripts\python.exe" -m step_05_explore.viewer
if errorlevel 1 (
    pause
    exit /b 1
)
