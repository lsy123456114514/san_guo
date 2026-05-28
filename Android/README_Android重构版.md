# MC风格三国 - Android 重构版

## ⚠️ 重要说明

**所有修改仅在 `e:\san_guo\Android` 文件夹中进行，不修改其他文件夹！**

---

## 📋 重构内容

### 1. 主程序重构 (`main.py`)
- 简化为直接启动MC风格3D游戏
- 支持Android和Windows双平台
- 修复了初始化方法调用

### 2. MC风格功能（从PY C++同步）
- ✅ 100个彩蛋系统
- ✅ 昼夜循环系统（MC时间0-24000）
- ✅ 天气系统（晴天/下雨/下雪）
- ✅ 生物系统（动物/怪物）
- ✅ 创造模式/生存模式
- ✅ 命令系统
- ✅ 合成系统（3x3网格）
- ✅ 背包系统
- ✅ 海浪效果
- ✅ Herobrine彩蛋

---

## 🎮 游戏功能

| 功能 | 描述 |
|------|------|
| 方块系统 | 放置/破坏多种方块 |
| 合成台 | 3x3合成网格 |
| 背包 | 物品管理 |
| 昼夜系统 | MC时间系统 |
| 天气系统 | 雨/雪效果 |
| 生物系统 | 动物/怪物生成 |
| 彩蛋系统 | 100个彩蛋 |
| 命令系统 | /give, /gamemode等 |

---

## 🚀 运行方式

### Windows测试
```bash
cd e:\san_guo\Android
python main.py
```

或双击 `启动MC游戏.bat`

### Android打包

**方式1: 一键打包（需要WSL）**
```bash
双击 "一键打包APK.bat"
```

**方式2: 手动打包**
```bash
# 在WSL或Linux中
cd /mnt/e/san_guo/Android
buildozer android debug
```

**方式3: 命令行**
```bash
# 在WSL中
cd /mnt/e/san_guo/Android
bash build_android.sh
```

---

## 📁 文件结构

```
Android/
├── main.py                    # 主程序
├── buildozer.spec            # 打包配置
├── 启动MC游戏.bat            # Windows启动
├── 一键打包APK.bat          # 一键打包
├── build_android.sh          # Linux打包脚本
├── ASSET/
│   ├── game_map_3d.py       # MC风格3D游戏
│   ├── game_data.py          # 存档系统
│   └── ...                   # 其他游戏模块
└── README_Android重构版.md   # 本文件
```

---

## ⌨️ 操作方式

| 按键 | 功能 |
|------|------|
| WASD | 移动 |
| 空格 | 跳跃 |
| 鼠标 | 视角控制 |
| Tab | 锁定鼠标 |
| E | 背包 |
| C | 合成台 |
| 1-9 | 选择物品 |
| 左键 | 放置方块 |
| 右键 | 破坏方块 |
| F5 | 切换视角 |
| Esc | 暂停菜单 |
| / | 打开命令输入 |

---

## 🔧 构建要求

### Windows
- Python 3.8+
- pygame
- PyOpenGL

### Android打包（WSL/Linux）
- Python 3.8+
- buildozer
- Android SDK
- Android NDK

---

## 📝 打包步骤

1. **安装WSL**（如果还没有）
```powershell
wsl --install
```

2. **在WSL中安装依赖**
```bash
sudo apt update
sudo apt install -y python3.8-venv python3-dev git zlib1g-dev libncurses5-dev libncursesw5-dev libssl-dev libsqlite3-dev
pip install buildozer cython
```

3. **运行打包脚本**
```bash
cd /mnt/e/san_guo/Android
bash build_android.sh
```

4. **等待完成**
- APK文件会生成在 `bin/` 目录
- 文件名类似 `sangoheroes-1.0.0-arm64-v8a_armeabi-v7a-debug.apk`

---

## ⚠️ 注意事项

1. **仅修改Android文件夹**，其他文件夹保持不变
2. 所有MC功能已从 `PY C++` 同步
3. 包含完整的存档系统
4. 兼容Android和Windows双平台
5. C++渲染器需要在Android上重新编译

---

## 🎉 游戏特色

- MC风格的视觉效果
- 100个隐藏彩蛋
- 昼夜交替和天气变化
- 创造模式和生存模式
- 完整的合成系统
- 命令系统

---

**重构时间**: 2026-05-28
**重构范围**: 仅 Android 文件夹
