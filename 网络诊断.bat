@echo off
chcp 65001 > nul
echo ========================================
echo    网络诊断工具
echo ========================================
echo.

echo [1/4] 检查 DNS 解析...
nslookup github.com
echo.

echo [2/4] 测试网络连接...
ping github.com -n 4
echo.

echo [3/4] 测试端口 443 连接...
powershell -Command "Test-NetConnection -ComputerName github.com -Port 443"
echo.

echo [4/4] 检查代理设置...
git config --global --get http.proxy
git config --global --get https.proxy
echo.

echo ========================================
echo    诊断完成
echo ========================================
echo.
echo 常见问题解决方案:
echo.
echo 1. 如果 DNS 解析失败:
echo    - 检查网络连接
echo    - 尝试更换 DNS: 8.8.8.8
echo.
echo 2. 如果 ping 失败但能解析 DNS:
echo    - GitHub 可能被防火墙拦截
echo    - 尝试使用代理或 VPN
echo.
echo 3. 如果需要配置代理:
echo    git config --global http.proxy http://127.0.0.1:端口号
echo    git config --global https.proxy http://127.0.0.1:端口号
echo.
echo 4. 如果不需要代理想清除:
echo    git config --global --unset http.proxy
echo    git config --global --unset https.proxy
echo.
pause
