@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "DEST=独立项目"

echo.
echo ==========================================================
echo   [脚本 01 / 02] 保护性归档 -^> %DEST%\
echo   语音识别 voice_*  +  圆周率 pi_*  +  C++ 校验 _*
echo ==========================================================
echo.

if not exist "%DEST%" (
    mkdir "%DEST%"
    echo [创建] %DEST%\
)

echo [1/4] voice_recognition*.py
for %%F in (voice_recognition*.py) do call :MOVEITEM "%%F"

echo [2/4] voice_data_gui   voice_data_ultimate
if exist "voice_data_gui" call :MOVEITEM "voice_data_gui"
if exist "voice_data_ultimate" call :MOVEITEM "voice_data_ultimate"

echo [3/4] pi_calculator*   Pi.txt
for %%F in (pi_calculator*) do call :MOVEITEM "%%F"
if exist "Pi.txt" call :MOVEITEM "Pi.txt"

echo [4/4] _cpp_test.txt  _gm_import.txt  _verify_cpp_out.txt  _verify_cpp_render.py
for %%F in (_cpp_test.txt _gm_import.txt _verify_cpp_out.txt _verify_cpp_render.py) do call :MOVEITEM "%%F"

echo.
echo ==========================================================
echo   完成 -^> %DEST%\
echo ==========================================================
dir /b "%DEST%"
echo.
echo (目录数 / 文件数:)
powershell -NoProfile -Command "$d=$env:DEST; $i=Get-ChildItem -LiteralPath $d -Recurse -Force; '  dir=' + (($i | ? PSIsContainer).Count) + '  file=' + (($i | ? {-not $_.PSIsContainer}).Count)"
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
