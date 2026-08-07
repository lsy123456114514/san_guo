@echo off

:: 三国游戏 - OLLAMA模型启动脚本
:: 免责声明：
:: 1. 本脚本仅用于启动OLLAMA服务和加载模型
:: 2. 运行前请确保已安装OLLAMA
:: 3. 模型下载可能需要较长时间和较大磁盘空间
:: 4. 本脚本不保证模型的可用性和性能
:: 5. 使用本脚本即表示您同意上述免责条款

echo 正在启动OLLAMA服务...
echo 请稍候，正在检查OLLAMA服务状态...

:: 启动OLLAMA服务（如果未运行）
start "OLLAMA服务" cmd /c "ollama serve"

:: 等待服务启动
echo 等待OLLAMA服务启动...
timeout /t 5 /nobre