#!/bin/bash
# MC风格三国 - 使用国内镜像打包

echo "======================================"
echo "MC风格三国 - 国内镜像打包"
echo "======================================"
echo ""

# 步骤1：设置Git代理为国内镜像
echo "[1/5] 设置GitHub国内镜像..."
git config --global url."https://ghproxy.com/https://github.com/".insteadOf "https://github.com/"
echo "   [OK] 已设置为ghproxy镜像"

# 步骤2：清理旧配置
echo ""
echo "[2/5] 清理旧配置..."
cd /mnt/e/san_guo/Android
rm -rf .buildozer/android/platform/python-for-android 2>/dev/null
mkdir -p .buildozer/android/platform 2>/dev/null
echo "   [OK] 旧配置已清理"

# 步骤3：使用镜像克隆python-for-android
echo ""
echo "[3/5] 下载python-for-android（使用镜像）..."
cd .buildozer/android/platform

# 方法1: ghproxy镜像
git clone https://ghproxy.com/https://github.com/kivy/python-for-android.git 2>&1 | tail -5

# 检查是否成功
if [ ! -d "python-for-android" ]; then
    echo "   ghproxy镜像失败，尝试备用镜像..."
    # 方法2: 备用镜像
    git clone https://gh.llkk.cc/https://github.com/kivy/python-for-android.git 2>&1 | tail -5
fi

if [ -d "python-for-android" ]; then
    echo "   [OK] 下载成功"
else
    echo "   [错误] 下载失败"
    exit 1
fi

# 步骤4：激活虚拟环境
echo ""
echo "[4/5] 激活Python环境..."
cd /mnt/e/san_guo/Android
source ~/venv/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null
echo "   [OK] 环境已激活"

# 步骤5：开始打包
echo ""
echo "[5/5] 开始打包APK..."
echo ""
echo "正在编译，可能需要10-30分钟..."
echo ""

buildozer android debug 2>&1

# 检查结果
if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "打包成功！"
    echo "APK文件位于: /mnt/e/san_guo/Android/bin/"
    echo "======================================"
else
    echo ""
    echo "======================================"
    echo "打包失败！"
    echo "请查看上方错误信息"
    echo "======================================"
    exit 1
fi
