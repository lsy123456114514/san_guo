@echo off

rem 直接运行Python游戏脚本
rem 这样可以避免打包问题

echo 正在启动游戏...
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 游戏启动失败，请检查Python环境是否正确安装。
    echo.
    pause
)
