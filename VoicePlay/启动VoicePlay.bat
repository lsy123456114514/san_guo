@echo off
REM ============================================
REM VoicePlay 快速启动脚本 (Windows) - 使用py启动器
REM ============================================

chcp 65001 > nul
title VoicePlay - 声音魔法乐园

echo.
echo ========================================
echo     🎵 VoicePlay - 声音魔法乐园
echo ========================================
echo.

REM 使用Python启动器(py)来运行
py --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python
    pause
    exit /b 1
)

echo [信息] 使用Python:
py --version
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

echo [提示] 检查依赖...
py -m pip list | findstr /i "numpy librosa sounddevice pygame scipy" >nul
if errorlevel 1 (
    echo.
    echo [提示] 发现依赖未安装，正在安装...
    echo.
    py -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [警告] 依赖安装可能有问题，但仍将尝试启动...
    )
)

echo.
echo [信息] 正在启动VoicePlay...
echo.

py main.py

if errorlevel 1 (
    echo.
    echo [错误] 程序运行失败！
    echo.
    echo 请尝试：
    echo   py -m pip install -r requirements.txt
    echo.
    pause
)
