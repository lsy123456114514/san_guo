@echo off
chcp 65001 > nul
echo ========================================
echo    SSH 密钥配置工具
echo ========================================
echo.

echo [1/5] 生成 SSH 密钥...
ssh-keygen -t ed25519 -C "Eric_20142014@163.com" -N "" -f "%USERPROFILE%\.ssh\id_ed25519"
if %ERRORLEVEL% EQU 0 (
    echo [完成] SSH 密钥生成成功
) else (
    echo [错误] 密钥生成失败
    pause
    exit /b 1
)
echo.

echo [2/5] 显示公钥内容...
type "%USERPROFILE%\.ssh\id_ed25519.pub"
echo.
echo ========================================
echo    请复制上面的公钥内容
echo    然后粘贴到 GitHub 的 SSH keys 设置中
echo    地址: https://github.com/settings/ssh/new
echo ========================================
echo.

echo [3/5] 启动 SSH 代理...
start ssh-agent
echo [完成] SSH 代理已启动
echo.

echo [4/5] 添加私钥到代理...
ssh-add "%USERPROFILE%\.ssh\id_ed25519"
if %ERRORLEVEL% EQU 0 (
    echo [完成] 私钥已添加到代理
) else (
    echo [警告] 私钥添加失败，请手动执行: ssh-add ~/.ssh/id_ed25519
)
echo.

echo [5/5] 测试 SSH 连接...
ssh -T git@github.com
echo.

echo ========================================
echo    配置完成！
echo ========================================
echo.
echo 如果显示 "Hi lsy123456114514! You've successfully authenticated..."
echo 就说明 SSH 配置成功了，可以运行推送命令了。
echo.
pause
