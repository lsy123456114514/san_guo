# 解决pkg_resources依赖问题的完整方案

## 问题描述
在运行打包好的exe文件时出现错误：
```
ModuleNotFoundError: No module named 'jaraco'
```

## 解决方案

### 方案一：直接运行Python脚本（推荐）
最简单的方法是直接使用Python运行游戏，避免打包问题。

**使用方法：**
1. 双击运行 `run_game.bat` 文件
2. 游戏将直接使用Python运行，没有依赖问题

---

### 方案二：修复现有exe运行环境

**使用方法：**
1. 确保您已经运行了 `install_dependencies_full.bat` 安装了所有依赖
2. 创建一个启动脚本，在运行exe之前设置正确的Python路径

创建一个新的启动脚本 `start_game_with_env.bat`：

---

### 方案三：重新打包游戏

**前提条件：**
- 确保PyInstaller已正确安装

**步骤：**
1. 检查Python版本和安装路径
2. 确保所有依赖已正确安装
3. 使用新的spec文件重新打包

---

## 可用文件列表

### 游戏运行相关文件
1. `run_game.bat` - 直接运行Python游戏脚本（推荐）
2. `install_dependencies_full.bat` - 完整安装所有依赖

### 可执行文件
1. `dist/ThreeKingdomsGame.exe` - 原始打包文件
2. `dist/SangoHeroes.exe` - 重命名版本
3. `dist/SangoHeroes_v2.exe` - 最新重命名版本

### 配置文件
1. `SangoHeroes_fixed.spec` - 修复版本的PyInstaller配置
2. `ThreeKingdomsGame.spec` - 原始PyInstaller配置

## 快速开始

### 最快的方法（推荐）
```batch
# 双击运行
run_game.bat
```

### 如果需要重新安装依赖
```batch
# 先安装依赖
install_dependencies_full.bat

# 然后运行游戏
run_game.bat
```

## 常见问题

### Q: 为什么会出现jaraco模块缺失错误？
A: PyInstaller在打包时没有正确处理pkg_resources的嵌套依赖关系。

### Q: 直接运行Python脚本是最好的方案吗？
A: 是的，这样可以避免所有打包问题，而且运行效果完全相同。

### Q: 我如何才能创建一个真正独立的exe文件？
A: 可以尝试使用cx_Freeze或PyOxidizer等替代打包工具。
