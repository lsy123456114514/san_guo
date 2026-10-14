# 三国霸业（San Guo）

三国题材的单机 + 局域网对战游戏。Python/pygame 编写，主菜单是三栏"伪系统"启动器：左栏功能台、中栏总览/模块磁贴 + 全局搜索、右栏特色大卡。

## 快速开始

```bash
pip install -r requirements.txt   # 核心只需 pygame（pygame-ce 兼容）
py main.py                        # 启动游戏
```

Python 3.10+，Windows / macOS / Linux 均可运行（纯 Python，无编译依赖）。

## 玩法概览

主菜单五大类、38 个模块，按 `FIVE_CATEGORIES`（`ASSET/game_main_menu.py`）组织：

| 分类 | 代表模块 |
|------|----------|
| 对战竞技 | PVP联机、超级对战大厅、3D地图、副本挑战、小游戏中心、游戏地图、竞速模式 |
| 武将养成 | 武将仓库、武将招募、英雄图鉴、装备、天赋、科技树、时装、宠物 |
| 建设经营 | 建筑、领土争霸、任务、镖局押运、炼金、钓鱼、游戏内AI |
| 社交排行 | 成就、排行榜、签到、邮件中心、社交、世界聊天、白板涂鸦、交易、商城 |
| 系统周边 | 天气、新手引导、背景故事、词典百科、限时活动、幸运转盘 |

**找不到功能？** 主菜单右上角搜索框（或按 `/`）——试试「枪」「子弹」「排行」「钓鱼」。

## 目录结构

```
san_guo/
├── main.py              # 入口
├── ASSET/               # 全部游戏代码与资源
│   ├── game_main_menu.py  # 主菜单（三栏启动器 + 搜索）
│   ├── game_data.py       # 存档/字体/窗口/资源 公共层
│   └── *.py               # 各功能模块（每个都有 main()）
├── data/                # 地图等数据文件
├── auto_test.py         # 自动化测试驱动（点开每个模块验证进出）
├── build.ps1            # Windows 一键：全量测试 + PyInstaller 打包
├── 打包配置/            # 各版本 .spec 归档
├── 启动脚本/            # bat 启动器（含 OLLAMA 模型下载）
└── 文档/                # 设计与使用文档
```

## 测试

```bash
py auto_test.py --list        # 列出将被点击的模块
py auto_test.py --all --fast  # 全量冒烟（约 2 分钟）
py auto_test.py --only 44 --fast  # 只测某个菜单码
```

驱动会逐个点开菜单模块、投递按键验证能正常退出，报告写入 `auto_test_report.txt`。

## 打包发布

```powershell
.\build.ps1              # 全量测试 + 打包（默认）
.\build.ps1 -SkipTest    # 跳过测试直接打包
.\build.ps1 -TestOnly    # 只跑测试
```

### 多平台安装包（GitHub Actions）

推送 `v*` 标签或在 Actions 页手动触发 `Build Release`，自动构建 **18 个桌面安装包 + 源码包**：

| 平台 | Runner | 产物 |
|------|--------|------|
| Windows x64 | windows-latest | onefile / onedir `.zip` |
| Windows x86 (32位) | windows-latest | onefile / onedir `.zip` |
| Windows ARM64 | windows-11-arm（实验） | onefile / onedir `.zip` |
| Linux x64 (新 glibc) | ubuntu-latest | onefile / onedir `.tar.gz` |
| Linux x64 (旧 glibc, 兼容 Ubuntu 22.04 及更早) | ubuntu-22.04 | onefile / onedir `.tar.gz` |
| **Linux ARM64 (aarch64 开发板/服务器)** | **ubuntu-24.04-arm** | **onefile / onedir `.tar.gz`** |
| macOS Intel | macos-13 | onefile / onedir `.tar.gz` |
| macOS Apple Silicon | macos-14 / macos-15 | onefile / onedir `.tar.gz` |
| 源码包 | ubuntu-latest | `.tar.gz` / `.zip` |

Linux ARM64 包可直接在 Ubuntu/Debian ARM64 板子上运行（如树莓派 4/5、RK3588 等），无需本地编译。

安卓构建见 `.github/workflows/build-apk.yml` 与 `文档/APK构建教程.md`。

## 可选：本地 AI 军师

游戏内「游戏内AI」模块为本地问答；配合 `启动脚本/下载OLLAMA模型.bat` 拉取模型后可离线使用。

## License

MIT，见 [LICENSE](LICENSE)。
