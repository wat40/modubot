@echo off
setlocal EnableDelayedExpansion

echo.
echo ╔═══════════════════════════════════════════════╗
echo ║                   ModuBot                     ║
echo ║                                               ║
echo ║     Discord Bot Launcher Script               ║
echo ║     Version: 1.1.0                            ║
echo ║                                               ║
echo ║     Now with Slash Commands!                  ║
echo ║     Type /help to see all available commands  ║
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

REM Check if virtual environment exists, if not create it
if not exist .venv\ (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist .venv\Lib\site-packages\discord\ (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
)

REM Run the bot
echo.
echo Starting ModuBot...
echo Use Ctrl+C to stop the bot
echo.
python bot.py

REM Deactivate virtual environment
call .venv\Scripts\deactivate.bat

echo.
pause 