@echo off
setlocal EnableDelayedExpansion

echo.
echo ╔═══════════════════════════════════════════════╗
echo ║                   ModuBot                     ║
echo ║                                               ║
echo ║     Website Local Development Server          ║
echo ║                                               ║
echo ╚═══════════════════════════════════════════════╝
echo.

REM Check if Python exists
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher.
    echo.
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%I in ('python --version 2^>^&1') do set pyver=%%I
echo Python version: %pyver%

REM Run the local webserver
echo.
echo Starting website server...
python website/server.py

echo.
pause 