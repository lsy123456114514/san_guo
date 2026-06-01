@echo off
chcp 65001 >nul
echo ======================================
echo MC风格三国 - WSL快速打包
echo ======================================
echo.

:: 检查WSL
echo 检查WSL状态...
wsl --list --verbose >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] WSL未安装
    echo 请先运行: WSL一键安装和打包.bat
    pause
    exit /b 1
)

:: 检查buildozer
wsl -d kali-linux -e bash -c "which buildozer" >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] buildozer未安装
    echo 请先运行: WSL一键安装和打包.bat
    pause
    exit /b 1
)

echo [OK] 环境就绪
echo.
echo 开始打包APK...
echo 编译时间约10-30分钟
echo.

:: 清理旧构建
echo [1/3] 清理旧构建...
wsl -d kali-linux -e bash -c "cd /mnt/e/san_guo/Android && buildozer android clean" 2>&1 | findstr /C:"cleaning" /C:"clean"

:: 开始打包
echo.
echo [2/3] 编译Python...
echo.
wsl -d kali-linux -e bash -c "cd /mnt/e/san_guo/Android && buildozer android debug 2>&1"

if %errorlevel% equ 0 (
    echo.
    echo [3/3] 打包完成！
    echo.
    echo ======================================
    echo 打包成功！
    echo APK文件位于: bin\ 目录
    echo ======================================
) else (
    echo.
    echo ======================================
    echo 打包失败！
    echo 请检查错误信息
    echo ======================================
)

echo.
pause
