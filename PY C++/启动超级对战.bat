@echo off
chcp 65001 >nul
title 三国游戏 - 超级对战大厅

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                    🎮 三国游戏 - 超级对战大厅                 ║
echo ╠═══════════════════════════════════════════════════════════════╣
echo ║  功能列表:                                                     ║
echo ║    1. 🌍 世界聊天 (需要中央服务器)                            ║
echo ║    2. 🌐 公网P2P (需要ngrok)                                  ║
echo ║    3. 🏠 局域网对战                                            ║
echo ║    4. 🤖 模拟对战 (单机)                                      ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

python -c "import pygame" >nul 2>&1
if errorlevel 1 (
    echo [提示] 首次运行，正在安装依赖...
    pip install -r requirements.txt
    echo.
)

echo 正在启动...
python -c "from ASSET.pvp_super import main; main()"

if errorlevel 1 (
    echo.
    echo [错误] 启动失败！
    pause
)
