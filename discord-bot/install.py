#!/usr/bin/env python3
import os
import sys
import subprocess
import platform

def print_header():
    print("====================================")
    print("ModuBot Installation Helper")
    print("====================================")
    print()

def check_python_version():
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 8):
        print(f"Error: Python 3.8+ is required. You are using Python {major}.{minor}")
        print("Please upgrade your Python installation.")
        sys.exit(1)
    print(f"Using Python {major}.{minor}")

def install_dependencies():
    print("Installing dependencies...")
    
    # Upgrade pip first
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # Install non-problematic packages first
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "discord.py==2.3.1", 
        "python-dotenv==1.0.0", 
        "supabase==1.0.3", 
        "requests==2.31.0", 
        "pytz==2023.3", 
        "python-dateutil==2.8.2"
    ])
    
    # Add special handling for Python 3.13 on Windows
    if platform.system() == "Windows" and sys.version_info >= (3, 13):
        print("\nDetected Windows with Python 3.13+. Applying special configuration...")
        print("Installing packages with pre-compiled wheels...")
    
    # Install potentially problematic packages with --only-binary option if on Windows
    if platform.system() == "Windows":
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--only-binary", ":all:",
            "pillow", "aiohttp", "asyncpg"
        ])
    else:
        # On Unix systems, try normal install first
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                "pillow", "aiohttp", "asyncpg"
            ])
        except subprocess.CalledProcessError:
            # If that fails, try with --only-binary
            print("Normal installation failed, trying with pre-compiled wheels...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "--only-binary", ":all:",
                "pillow", "aiohttp", "asyncpg"
            ])

def main():
    print_header()
    check_python_version()
    install_dependencies()
    
    # Special note for Windows users with Python 3.13+
    if platform.system() == "Windows" and sys.version_info >= (3, 13):
        print("\nNOTE: Python 3.13+ on Windows uses ProactorEventLoop by default which can cause issues.")
        print("The bot has been configured to use SelectorEventLoop instead, which should fix these issues.")
    
    print("\nInstallation completed! You can now run the bot with: python bot.py")

if __name__ == "__main__":
    main()
    
    # Pause at the end on Windows
    if platform.system() == "Windows":
        input("\nPress Enter to exit...") 