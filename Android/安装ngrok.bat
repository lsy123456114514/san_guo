@echo off
chcp 65001 >nul
title 安装ngrok内网穿透工具

setlocal enabledelayedexpansion

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                    📥 安装ngrok内网穿透工具                    ║
echo ╠═══════════════════════════════════════════════════════════════╣
echo ║  ngrok可以让你的游戏实现公网联机，像陶瓦联机一样！             ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

:: 检查是否已安装
ngrok version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ ngrok已安装！
    ngrok version
    pause
    exit /b 0
)

echo ⚠️  ngrok未安装，正在下载...
echo.

:: 创建临时目录
set "TEMP_DIR=%TEMP%\ngrok_install"
mkdir "%TEMP_DIR%" 2>nul

:: 检测系统位数
set "ARCH=amd64"
if "%PROCESSOR_ARCHITECTURE%"=="x86" set "ARCH=386"

echo 系统架构: %ARCH%

:: 下载ngrok
powershell -Command "Invoke-WebRequest -Uri 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-%ARCH%.zip' -OutFile '%TEMP_DIR%\ngrok.zip'"

if not exist "%TEMP_DIR%\ngrok.zip" (
    echo ❌ 下载失败！请手动下载: https://ngrok.com/download
    pause
    exit /b 1
)

echo ✅ 下载成功！

:: 解压
powershell -Command "Expand-Archive -Path '%TEMP_DIR%\ngrok.zip' -DestinationPath '%TEMP_DIR%'"

if not exist "%TEMP_DIR%\ngrok.exe" (
    echo ❌ 解压失败！
    pause
    exit /b 1
)

echo ✅ 解压成功！

:: 复制到游戏目录
copy "%TEMP_DIR%\ngrok.exe" "%~dp0ngrok.exe"
echo ✅ ngrok已复制到游戏目录！

:: 清理临时文件
rd /s /q "%TEMP_DIR%"

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                    🎉 安装完成！                               ║
echo ╠═══════════════════════════════════════════════════════════════╣
echo ║  使用方法:                                                    ║
echo ║    1. 启动游戏 -> 公网P2P对战 -> 创建房间                      ║
echo ║    2. 复制显示的公网地址给朋友                                 ║
echo ║    3. 朋友输入地址即可连接                                     ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

pause
