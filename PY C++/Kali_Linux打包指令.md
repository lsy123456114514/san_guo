# MC风格三国 - Kali Linux打包指令

## 问题1：包名修正
```bash
# 替换这些包名
libncurses5-dev → libncurses-dev
libncursesw5-dev → 已包含在 libncurses-dev 中
python3.8-venv → 使用系统Python 3.13
```

## 完整安装步骤（修正后）

### 第1步：安装系统依赖
```bash
sudo apt update
sudo apt install -y git zlib1g-dev libncurses-dev libssl-dev libsqlite3-dev libffi-dev make build-essential libtool
```

### 第2步：创建虚拟环境并安装buildozer
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装buildozer（使用--break-system-packages）
pip install --upgrade pip setuptools wheel cython
pip install buildozer
```

### 第3步：打包APK
```bash
# 切换到Android目录
cd /mnt/e/san_guo/Android

# 激活虚拟环境（如果退出了）
source ~/venv/bin/activate

# 清理旧构建（可选）
buildozer android clean

# 开始打包
buildozer android debug
```

---

## 一条命令完成所有步骤（推荐）

```bash
sudo apt update && sudo apt install -y git zlib1g-dev libncurses-dev libssl-dev libsqlite3-dev libffi-dev make build-essential libtool && python3 -m venv ~/venv && source ~/venv/bin/activate && pip install --break-system-packages buildozer && cd /mnt/e/san_guo/Android && buildozer android debug
```

---

## 重要说明

1. **Kali Linux使用Python 3.13**，不需要单独的Python版本
2. **使用虚拟环境**来避免系统包冲突
3. **pip需要加 --break-system-packages** 参数

---

**编译时间**：约10-30分钟
