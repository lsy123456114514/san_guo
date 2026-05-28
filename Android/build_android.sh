#!/bin/bash
# MC风格三国 - Android打包脚本
# 在WSL中运行此脚本

echo "======================================"
echo "MC风格三国 - Android打包"
echo "======================================"
echo ""

# 检查是否在WSL中
if [ ! -d "/mnt/e" ]; then
    echo "错误: 请在WSL中运行此脚本"
    exit 1
fi

# 切换到Android目录
cd /mnt/e/san_guo/Android

# 检查buildozer是否安装
if ! command -v buildozer &> /dev/null; then
    echo "错误: buildozer 未安装"
    echo "请运行: pip install buildozer"
    exit 1
fi

# 清理旧构建
echo "清理旧构建..."
buildozer android clean

# 开始打包
echo ""
echo "开始打包APK..."
echo ""
buildozer android debug

# 检查结果
if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "打包成功！"
    echo "APK文件位于: bin/ 目录"
    echo "======================================"
else
    echo ""
    echo "======================================"
    echo "打包失败！"
    echo "======================================"
    exit 1
fi
