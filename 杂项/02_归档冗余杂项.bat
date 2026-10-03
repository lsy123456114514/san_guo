@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "DEST=归档杂项"

echo.
echo ==========================================================
echo   [脚本 02 / 02] 冗余清理 -^> %DEST%\
echo   AI 冗余代码 / 重复打包脚本 / 开发辅助工具 / 文档 / 日志
echo ==========================================================
echo   (主项目保留: main.py ASSET data *.spec[主] 启动器 等)
echo ==========================================================
echo.

if not exist "%DEST%" (
    mkdir "%DEST%"
    echo [创建] %DEST%\
)

set "LIST="
set "LIST=%LIST% hello.py build_all.py setup_new.py upload_tool.py UploadTool.spec"
set "LIST=%LIST% github_branch_tool.py GitHub_Branch_Tool_README.md push_to_github.bat setup_ssh.bat"
set "LIST=%LIST% game.log game_website.html game_update.patch SOLUTION.md"
set "LIST=%LIST% map_data_lsy.json map_data_weqwqewq.json"
set "LIST=%LIST% ThreeKingdomsGame.spec ThreeKingdomsGame_v2.spec ThreeKingdomsGame_x86.spec"
set "LIST=%LIST% SangoHeroesSimple.spec SangoHeroes_fixed.spec GamePacker.spec complete_game.spec"
set "LIST=%LIST% 3D主城.spec APK构建教程.md 性能优化建议.md 打包工具使用说明.md"
set "LIST=%LIST% 打包工具.py 启动打包工具.bat 性能测试.py 性能测试_simple.py"
set "LIST=%LIST% 网络诊断.bat 下载OLLAMA模型.bat 启动OLLAMA模型.bat"

echo [1/2] 显式归档清单
for %%F in (%LIST%) do call :MOVEITEM "%%F"

echo.
echo [2/2] 0 字节垃圾文件 (乱码名等)
powershell -NoProfile -Command "$d=$env:DEST; Get-ChildItem -File | Where-Object {$_.Length -eq 0} | ForEach-Object { $n=$_.Name; git mv -- $n (Join-Path $d $n) 2>$null; if($LASTEXITCODE -ne 0){ Move-Item -LiteralPath $n -Destination $d -Force }; Write-Host ('    [0-byte]  ' + $n) }"

echo.
echo ==========================================================
echo   完成 -^> %DEST%\
echo ==========================================================
dir /b "%DEST%"
echo.
echo (文件数:)
powershell -NoProfile -Command "$d=$env:DEST; (Get-ChildItem -LiteralPath $d -File -Force).Count"
echo.
pause
exit /b 0

rem ------------------------------------------------------------
rem 移动单项: 优先 git mv (保留历史), 失败则回退普通 move
rem ------------------------------------------------------------
:MOVEITEM
set "SRC=%~1"
if "%SRC%"=="" exit /b 0
if not exist "%SRC%" exit /b 0
git mv -- "%SRC%" "%DEST%\%~nx1" >nul 2>&1
if not errorlevel 1 (
    echo     [git-mv]  %~nx1
    exit /b 0
)
move "%SRC%" "%DEST%\" >nul 2>&1
if errorlevel 1 (
    echo     [失败]    %~nx1
    exit /b 1
)
echo     [move]     %~nx1
exit /b 0
