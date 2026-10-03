@echo off

rem 三国霸业游戏依赖安装脚本
rem 自动安装所有必要的Python库

echo ===============================================
echo 三国霸业游戏依赖安装脚本
echo ===============================================
echo 

rem 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未找到Python。请先安装Python 3.8或更高版本。
    pause
    exit /b 1
)

echo 正在更新pip...
python -m pip install --upgrade pip

if %errorlevel% neq 0 (
    echo 错误：pip更新失败。
    pause
    exit /b 1
)

echo 
echo 正在安装游戏依赖库...
echo ===============================================

rem 安装核心依赖
python -m pip install pygame

rem 安装其他可能需要的库
python -m pip install numpy
python -m pip install requests
python -m pip install pillow
python -m pip install pyinstaller

if %errorlevel% neq 0 (
    echo 错误：依赖安装失败。
    pause
    exit /b 1
)

echo 
echo ===============================================
echo 依赖安装完成！
echo ===============================================
echo 
echo 游戏现在可以正常运行了。
echo 您可以运行 main.py 来启动游戏。
echo 
pause