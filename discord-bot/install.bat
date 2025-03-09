@echo off
echo ====================================
echo ModuBot Installation Helper
echo ====================================
echo.

REM Check if Python is installed
python --version 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo Installing dependencies...
echo.

REM Install dependencies using pip with the --only-binary option for problematic packages
python -m pip install --upgrade pip
python -m pip install discord.py==2.3.1 python-dotenv==1.0.0 supabase==1.0.3 requests==2.31.0 pytz==2023.3 python-dateutil==2.8.2
python -m pip install --only-binary :all: pillow aiohttp asyncpg

echo.
echo Installation completed! You can now run the bot with: python bot.py
echo.
pause 