@echo off

rem 构建游戏安装程序
rem 需要先安装Inno Setup (https://jrsoftware.org/isinfo.php)

echo 开始构建游戏安装程序...
echo.

rem 检查iscc.exe是否存在
if exist "C:\Program Files (x86)\Inno Setup 6\iscc.exe" (
    echo 找到Inno Setup 6，开始编译安装脚本...
    "C:\Program Files (x86)\Inno Setup 6\iscc.exe" game_installer.iss
) else if exist "C:\Program Files\Inno Setup 6\iscc.exe" (
    echo 找到Inno Setup 6，开始编译安装脚本...
    "C:\Program Files\Inno Setup 6\iscc.exe" game_installer.iss
) else (
    echo 错误：未找到Inno Setup 6
    echo 请先下载并安装Inno Setup 6：https://jrsoftware.org/isinfo.php
    pause
    exit /b 1
)

echo.
echo 安装程序构建完成！
echo 安装程序位于：Output目录

echo.
echo 按任意键退出...
pause >nul
exit /b 0
