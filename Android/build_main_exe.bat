@echo off
chcp 65001 >nul
echo ==============================================
echo      正在打包游戏主程序...
echo ==============================================

set "PYTHONPATH=%cd%"
set "APP_NAME=GameMain"
set "MAIN_SCRIPT=main.py"
set "DIST_DIR=dist"
set "BUILD_DIR=build"

echo 检查 PyInstaller 是否安装...
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo 安装 PyInstaller...
    pip install pyinstaller
)

echo 开始打包...
pyinstaller ^
    --name=%APP_NAME% ^
    --onefile ^
    --windowed ^
    --icon=data/icon.png ^
    --add-data="ASSET;ASSET" ^
    --add-data="data;data" ^
    --add-binary="opengl_renderer.dll;." ^
    --hidden-import=pygame ^
    --hidden-import=numpy ^
    --hidden-import=requests ^
    --hidden-import=pillow ^
    --hidden-import=ASSET ^