@echo off
setlocal

cd /d "%~dp0"
title Build With Me #1
set "PYTHONDONTWRITEBYTECODE=1"

echo.
echo Build With Me #1 - Beginner Setup
echo ==================================
echo.

set "PYTHON_COMMAND="

where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
    if not errorlevel 1 set "PYTHON_COMMAND=py -3"
)

if not defined PYTHON_COMMAND (
    where python >nul 2>nul
    if not errorlevel 1 (
        python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
        if not errorlevel 1 set "PYTHON_COMMAND=python"
    )
)

if not defined PYTHON_COMMAND goto python_missing

echo [1/3] Preparing the private Python environment...
if not exist "_local\.venv\Scripts\python.exe" (
    if not exist "_local" mkdir "_local"
    %PYTHON_COMMAND% -m venv "_local\.venv"
    if errorlevel 1 goto setup_failed
) else (
    echo       Existing environment found.
)

echo.
echo [2/3] Installing the project packages...
"_local\.venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto setup_failed

echo.
echo [3/3] Running the pipeline...
"_local\.venv\Scripts\python.exe" run_pipeline.py
if errorlevel 1 goto pipeline_failed

echo.
echo Setup and pipeline completed successfully.
echo Database: _local\output\retail_pipeline.duckdb
echo Next, open step_01_data and follow the numbered folders through step_05_explore.
echo To browse the tables, double-click OPEN_DATA.bat after this run.
echo.
goto finish

:python_missing
echo Python 3.11 or newer was not found.
echo.
echo 1. Visit https://www.python.org/downloads/
echo 2. Install the latest Python 3 version.
echo 3. Enable "Add Python to PATH" during installation.
echo 4. Close this window, then double-click START_HERE.bat again.
echo.
goto failed

:setup_failed
echo.
echo Setup stopped before the pipeline could run.
echo Check your internet connection and the error message above, then try again.
echo.
goto failed

:pipeline_failed
echo.
echo The setup worked, but the pipeline could not finish.
echo Read the error message above. The most common cause is a missing or moved CSV file.
echo.
goto failed

:failed
if not defined BWM_NO_PAUSE pause
exit /b 1

:finish
if not defined BWM_NO_PAUSE pause
exit /b 0
