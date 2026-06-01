@echo off
chcp 65001 >nul
echo ======================================
echo MC风格三国 - WSL自动打包
echo ======================================
echo.

:: 检查WSL是否安装
echo [1/5] 检查WSL状态...
wsl --list --verbose >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] WSL未安装，正在安装...
    wsl --install
    echo 请重启电脑后再次运行此脚本
    pause
    exit /b 1
)
echo [OK] WSL已安装

:: 检查buildozer
echo.
echo [2/5] 检查buildozer...
wsl -d kali-linux -e bash -c "which buildozer" >nul 2>&1
if %errorlevel% neq 0 (
    echo [3/5] 安装buildozer依赖...
    echo 这可能需要几分钟，请耐心等待...
    wsl -d kali-linux -e bash -c "sudo apt update && sudo apt install -y python3.8-venv python3-dev git zlib1g-dev libncurses5-dev libncursesw5-dev libssl-dev libsqlite3-dev libffi-dev make build-essential libtool" 2>&1 | findstr /C:"完成" /C:"done" /C:"Setting up"
    
    echo.
    echo [4/5] 安装Python包...
    wsl -d kali-linux -e bash -c "pip3 install --upgrade pip setuptools wheel cython" 2>&1 | findstr /C:"Successfully installed"
    wsl -d kali-linux -e bash -c "pip3 install buildozer" 2>&1 | findstr /C:"Successfully installed"
    
    echo [OK] buildozer安装完成
) else (
    echo [OK] buildozer已安装
)

:: 开始打包
echo.
echo [5/5] 开始打包APK...
echo.
echo 正在编译，可能需要10-30分钟...
echo.

:: 运行buildozer打包
wsl -d kali-linux -e bash -c "cd /mnt/e/san_guo/Android && buildozer android debug 2>&1"

if %errorlevel% equ 0 (
    echo.
    echo ======================================
    echo 打包成功！
    echo APK文件位于: bin\ 目录
    echo ======================================
) else (
    echo.
    echo ======================================
    echo 打包失败！
    echo 请查看上方错误信息
    echo ======================================
)

echo.
pause
