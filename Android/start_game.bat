@echo off

rem 三国游戏智能启动器
rem 会自动选择最佳的运行方式

echo ====================================
echo    三国游戏 - 智能启动器
echo ====================================
echo.

echo 正在检查运行环境...

rem 检查Python是否可用
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [√] 检测到Python环境
    echo.
    echo 推荐使用Python直接运行游戏，避免依赖问题。
    echo.
    set /p choice="是否直接运行Python版本? (Y/N): "
    
    if /i "%choice%"=="Y" (
        echo.
        echo 正在启动游戏...
        python main.py
        goto end
    )
)

echo.
echo 尝试运行打包好的exe文件...

rem 尝试运行几个可能的exe文件
if exist "dist\SangoHeroes_v2.exe" (
    echo [√] 找到 SangoHeroes_v2.exe
    start "" "dist\SangoHeroes_v2.exe"
    goto end
)

if exist "dist\SangoHeroes.exe" (
    echo [√] 找到 SangoHeroes.exe
    start "" "dist\SangoHeroes.exe"
    goto end
)

if exist "dist\ThreeKingdomsGame.exe" (
    echo [√] 找到 ThreeKingdomsGame.exe
    start "" "dist\ThreeKingdomsGame.exe"
    goto end
)

echo.
echo [×] 未找到游戏可执行文件！
echo.
echo 请先安装依赖，然后运行Python版本：
echo 1. 运行 install_dependencies_full.bat
echo 2. 运行 run_game.bat
echo.

:end
echo.
echo 按任意键退出...
pause >nul
