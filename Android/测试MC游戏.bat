@echo off
chcp 65001 >nul
echo ======================================
echo 测试MC游戏启动
echo ======================================
echo.
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo 启动失败，按任意键退出...
    pause >nul
) else (
    echo.
    echo 游戏已退出
)
