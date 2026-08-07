@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ========================================
echo    GitHub 代码推送工具 v2.0
echo ========================================
echo.

echo [1/3] 检查 Git 状态...
git status > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 不是 Git 仓库或 Git 未安装
    goto :error
)
echo [完成] Git 状态正常
echo.

echo [2/3] 检查远程仓库配置...
git remote -v
echo.

echo [3/3] 尝试推送代码...
echo.
echo 提示: 如果推送失败，请检查:
echo   - 网络连接是否正常
echo   - GitHub 仓库是否存在
echo   - 个人访问令牌是否有 repo 权限
echo.

git push -u origin master --force

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo    推送成功！ 
    echo ========================================
    echo.
    echo 请访问: https://github.com/lsy123456114514/san_guo
    echo.
    echo 如果页面显示 404，请先在 GitHub 上创建仓库：
    echo   1. 访问 https://github.com/new
    echo   2. Repository name 填写: san_guo
    echo   3. 点击 Create repository
    echo   4. 然后重新运行此脚本
    echo.
) else (
    echo.
    echo ========================================
    echo    推送失败！
    echo ========================================
    echo.
    echo 可能的原因:
    echo   1. 网络连接问题 - 请检查网络
    echo   2. 仓库不存在 - 请先在 GitHub 创建 san_guo 仓库
    echo   3. 令牌权限不足 - 需要 repo 权限
    echo.
    echo 常见解决方案:
    echo   - 重试推送命令: git push -u origin master
    echo   - 检查网络: ping github.com
    echo   - 使用代理(如果有): git config --global http.proxy http://127.0.0.1:端口号
    echo.
)

:error
echo.
echo 按任意键退出...
pause > nul
