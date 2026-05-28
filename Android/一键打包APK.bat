@echo off
chcp 65001 >nul
echo ======================================
echo MC风格三国 - Android打包
echo ======================================
echo.
echo 正在启动WSL并打包...
echo.
wsl -e bash -c "cd /mnt/e/san_guo/Android && bash build_android.sh"
echo.
echo 按任意键退出...
pause >nul
