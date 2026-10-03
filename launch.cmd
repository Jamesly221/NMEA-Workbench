@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 main.py
) else (
    python main.py
)
if errorlevel 1 (
    echo.
    echo Could not start NMEA Workbench. Install Python 3.11 or newer with Tcl/Tk enabled.
    echo See docs\GETTING_STARTED.md for setup instructions.
    pause
)
