@echo off
chcp 65001 > nul
title 三国游戏 - 打包工具

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║          🎮 三国游戏 - 打包工具 v1.0                      ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未检测到 Python！
    echo.
    echo 请先安装 Python: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: 检查 tkinter
python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: tkinter 未安装！
    echo.
    echo 请安装 tkinter (通常随 Python 一起安装)
    echo 或运行: pip install tk
    echo.
    pause
    exit /b 1
)

:: 检查 pyinstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 提示: PyInstaller 未安装，正在安装...
    pip install pyinstaller
    if errorlevel 1 (
        echo ❌ 安装失败！
        pause
        exit /b 1
    )
    echo ✅ 安装成功！
    echo.
)

echo 🚀 启动打包工具...
echo.
python "%~dp0打包工具.py"

if errorlevel 1 (
    echo.
    echo ❌ 打包工具遇到错误
    pause
)
