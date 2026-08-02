@echo off
chcp 65001
echo ============================================
echo 正在打包 GitHub 分支管理工具...
echo ============================================

cd /d "%~dp0"

echo 检查 PyInstaller 是否安装...
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo 安装 PyInstaller...
    pip install pyinstaller
)

echo 开始打包...
pyinstaller --onefile --windowed --icon=data/icon.png ^
    --name=GitHubBranchTool ^
    --distpath=dist ^
    --workpath=build ^
    github_branch_tool.py

if %errorlevel% equ 0 (
    echo ============================================
