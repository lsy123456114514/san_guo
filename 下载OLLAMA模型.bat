@echo off

:: OLLAMA Model Download Script
:: This script downloads the lightweight gemma:2b model for low-end devices

chcp 65001 >nul

echo ===================================
echo OLLAMA Model Download Script
echo ===================================
echo.
echo This script will download the gemma:2b model (about 1GB)
echo Suitable for devices with 2GB+ VRAM
echo.
echo Disclaimer:
echo 1. Download requires internet connection
echo 2. Model file will take about 1GB of disk space
echo 3. Please ensure OLLAMA client is installed
echo 4. This script only provides download functionality
echo.
echo Press any key to start download...
pause >nul

echo Checking if OLLAMA is installed...
ollama --version >nul 2>nul

if %errorlevel% neq 0 (
    echo Error: OLLAMA command not found
    echo Please install OLLAMA client first: https://ollama.com/
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo Downloading model...
echo Please wait, first download may take several minutes...
echo.

:: Download model
ollama pull gemma:2b

if %errorlevel% equ 0 (
    echo.
    echo Download successful!
    echo Model has been saved to OLLAMA default storage location
    echo You can now use this model in the game's AI system
) else (
    echo.
    echo Download failed!
    echo Please check:
    echo 1. OLLAMA service is running
    echo 2. Network connection is normal
    echo 3. Sufficient disk space is available
)

echo.
echo Press any key to exit...
pause >nul