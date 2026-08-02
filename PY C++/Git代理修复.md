# Git代理修复

## 问题原因
Git代理指向了错误的地址：`github.com.cnpmjs.org`

## 解决方法

### 方法1：清除Git代理（推荐）
```bash
# 清除所有Git代理设置
git config --global --unset http.proxy
git config --global --unset https.proxy
git config --global --unset url."https://github.com/".insteadOf
git config --global --unset url."https://github.com.cnpmjs.org/".insteadOf
```

### 方法2：重新克隆python-for-android
```bash
# 先清理
cd /mnt/e/san_guo/Android
rm -rf .buildozer

# 重新设置Git
git config --global --unset http.proxy
git config --global --unset https.proxy

# 手动克隆python-for-android
mkdir -p .buildozer/android/platform
cd .buildozer/android/platform
git clone https://github.com/kivy/python-for-android.git
```

### 方法3：使用国内镜像（如果方法1不行）
```bash
# 设置GitHub镜像
git config --global url."https://ghproxy.com/https://github.com/".insteadOf "https://github.com/"
git config --global url."https://ghproxy.com/https://github.com/".insteadOf "https://github.com.cnpmjs.org/"
```

---

## 然后重新打包
```bash
cd /mnt/e/san_guo/Android
source ~/venv/bin/activate
buildozer android debug
```
