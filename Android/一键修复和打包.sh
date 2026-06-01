#!/bin/bash
# MC风格三国 - 一键修复Git代理并打包

echo "======================================"
echo "MC风格三国 - 一键打包"
echo "======================================"
echo ""

# 步骤1：修复Git代理
echo "[1/4] 修复Git代理配置..."
git config --global --unset http.proxy 2>/dev/null
git config --global --unset https.proxy 2>/dev/null
git config --global --unset url."https://github.com/".insteadOf 2>/dev/null
git config --global --unset url."https://github.com.cnpmjs.org/".insteadOf 2>/dev/null
echo "   [OK] Git代理已清除"

# 步骤2：清理旧的buildozer配置
echo ""
echo "[2/4] 清理旧配置..."
cd /mnt/e/san_guo/Android
rm -rf .buildozer/android/platform/python-for-android 2>/dev/null
mkdir -p .buildozer/android/platform 2>/dev/null
echo "   [OK] 旧配置已清理"

# 步骤3：手动克隆python-for-android
echo ""
echo "[3/4] 下载python-for-android..."
cd .buildozer/android/platform
git clone https://github.com/kivy/python-for-android.git 2>&1 | grep -E "(Cloning|Receiving|Resolving|Connecting|warning)" || echo "   [OK] 下载完成"

# 步骤4：开始打包
echo ""
echo "[4/4] 开始打包APK..."
echo ""
cd /mnt/e/san_guo/Android
source ~/venv/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null

# 打包（显示进度）
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
