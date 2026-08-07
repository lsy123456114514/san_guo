# 三国霸业 - MC 风格三国游戏

> 一款基于 Python + Pygame 开发的三国题材 MC 风格 3D 游戏，集成武将招募、战斗、PvP 对战、宠物、副本、阵营、阵法、合成、彩蛋等丰富系统，兼容 Windows 与 Android 双平台。

- **当前版本**: v22（参见 [Android/version.txt](Android/version.txt)）
- **Python 兼容性**: Python 3.6+（避免使用海象运算符等高版本语法）
- **核心引擎**: Pygame（可选 OpenGL / C++ 渲染器加速）

---

## 目录

- [项目简介](#项目简介)
- [目录结构](#目录结构)
- [环境要求与安装](#环境要求与安装)
- [运行方式](#运行方式)
- [主要功能模块](#主要功能模块)
- [核心数据与存档](#核心数据与存档)
- [字体与跨平台显示](#字体与跨平台显示)
- [打包与发布](#打包与发布)
- [开发规范](#开发规范)
- [常见问题排查](#常见问题排查)

---

## 项目简介

本项目是一个综合性三国题材游戏，采用「英语词典」伪装界面进入，主程序包含以下特色：

- **MC 风格 3D 主城**：方块世界 + 昼夜循环 + 天气系统 + 100 个彩蛋
- **武将系统**：详尽的武将数据库（基础属性、成长、技能、终极技、被动、羁绊、专属装备）
- **战斗系统**：回合制 + 元素反应 + 暴击/格挡/连击 + PvP 在线对战
- **养成系统**：宠物、阵营、阵法、命格、转生、天赋、科技树
- **社交系统**：登录注册、世界聊天、好友、邮件、排行榜
- **福利系统**：每日奖励（无固定时间签到）、活动、限时事件、新手引导
- **小游戏**：贪吃蛇、俄罗斯方块、2048、五子棋、扫雷、推箱子、打砖块
- **开发者工具**：开发者控制台、配置编辑器、自定义武将编辑器
- **讽刺文案**：在福利、商店等模块讽刺其他游戏厂商的不友好设计

---

## 目录结构

```
san_guo/
├── README.md                    # 本文件
├── ASSET/                       # 根目录版本（基础版本）
│   ├── __init__.py              # safe_exit、EXIT_FLAG 等公共入口
│   ├── game_data.py             # 数据/存档/字体加载核心
│   ├── game_main_menu.py        # 主菜单
│   ├── game_map_3d.py           # MC 风格 3D 地图
│   ├── battle_system.py         # 战斗系统
│   ├── hero_recruitment.py      # 武将招募
│   ├── equipment_system.py      # 装备系统
│   ├── pet_system.py            # 宠物系统
│   ├── dungeon_system.py        # 副本系统
│   ├── shop_system.py           # 商店系统
│   ├── login_system.py          # 登录注册
│   ├── dictionary_system.py     # 词典（伪装界面）
│   ├── whiteboard.py            # 白板（伪装界面）
│   ├── modern_ui_system.py      # 现代 UI 组件
│   ├── network_pvp.py / pvp_online.py / pvp_p2p.py / pvp_super.py  # PvP
│   ├── chat_server.py / world_chat.py                              # 聊天
│   ├── quest_system.py / task_chain_system.py                      # 任务
│   ├── achievement_system.py / ranking_system.py                   # 成就/排行
│   ├── ai_system.py / secure_network.py / p2p_ngrok.py             # 网络
│   ├── auto_update.py                                              # 自动更新
│   ├── (其它小游戏与功能模块)
│   ├── save.json                # 默认存档
│   ├── users.json               # 用户数据
│   └── login_state.json         # 登录状态缓存
│
├── Android/                     # Android 重构版（推荐主开发分支）
│   ├── main.py                  # 入口（启动 MC 风格 3D 游戏）
│   ├── version.txt              # 版本号
│   ├── requirements.txt         # 依赖清单
│   ├── SangoHeroes.spec         # PyInstaller 打包配置
│   ├── ASSET/                   # 与根目录 ASSET 同步，含 fonts/ 字体目录
│   │   ├── fonts/
│   │   │   └── 字魂白鸽天行体(商用需授权).ttf
│   │   └── font_manager.py      # 字体管理器
│   ├── data/                    # 静态资源（icon、splash、map_data）
│   └── venv/                    # 本地虚拟环境（不入库）
│
├── san_guo/                     # PC 稳定分支（与 Android 同步）
│   ├── main.py                  # PC 入口（词典→登录→主菜单）
│   ├── ASSET/                   # 与 Android 同步
│   └── 性能优化建议.md / 性能测试.py
│
├── .github/workflows/           # GitHub Actions 自动构建
├── .gitignore
└── 各种打包脚本（.bat / .spec / build_*.py）
```

> 三套目录（`ASSET/`、`Android/ASSET/`、`san_guo/ASSET/`）应保持同步，所有改动需在三处同步应用。

---

## 环境要求与安装

### 系统要求

- **OS**: Windows 7+ / Android 5.0+ / Linux（需手动安装依赖）
- **Python**: 3.6 及以上（推荐 3.10+）
- **内存**: 最低 2GB，推荐 4GB+

### 安装依赖

```bash
# 进入项目目录
cd san_guo/Android

# 安装核心依赖（必装）
pip install pygame

# 安装可选依赖（推荐全部安装以获得完整体验）
pip install numpy requests pillow pyinstaller
```

或直接使用 [requirements.txt](Android/requirements.txt)：

```bash
pip install -r Android/requirements.txt
```

### 字体文件

游戏依赖 `ASSET/fonts/字魂白鸽天行体(商用需授权).ttf` 显示中文。如果缺失会导致其他设备上文字显示为方框。

---

## 运行方式

### Windows

```bash
# 方式 1：直接运行 PC 稳定版
cd san_guo/san_guo
python main.py

# 方式 2：运行 Android 重构版（PC 上也可运行）
cd san_guo/Android
python main.py

# 方式 3：双击启动脚本
# san_guo/Android/start_game.bat
# san_guo/san_guo/run_game.bat
```

### Android

通过 Buildozer / Kivy Launcher 打包后运行，详见 [APK构建教程.md](APK构建教程.md)。

### 启动流程

1. 显示「英语词典」伪装界面（[dictionary_system.py](Android/ASSET/dictionary_system.py)）
2. 通过特定条件触发后进入白板或游戏
3. 检查 [login_state.json](Android/ASSET/login_state.json) 是否有保存的登录态
4. 有则直接加载用户数据；无则进入登录界面（[login_system.py](Android/ASSET/login_system.py)）
5. 登录成功后运行启动动画 → 主菜单（[game_main_menu.py](Android/ASSET/game_main_menu.py)）

---

## 主要功能模块

| 模块 | 文件 | 说明 |
|------|------|------|
| 主菜单 | [game_main_menu.py](Android/ASSET/game_main_menu.py) | 游戏主入口、菜单导航、启动动画 |
| 3D 世界 | [game_map_3d.py](Android/ASSET/game_map_3d.py) | MC 风格方块世界、昼夜、天气、彩蛋 |
| 战斗系统 | [battle_system.py](Android/ASSET/battle_system.py) | 回合制战斗、元素反应、技能释放 |
| 武将招募 | [hero_recruitment.py](Android/ASSET/hero_recruitment.py) | 抽卡、碎片合成 |
| 武将仓库 | [hero_warehouse.py](Android/ASSET/hero_warehouse.py) | 武将管理、升级、突破 |
| 武将图鉴 | [hero_collection_system.py](Android/ASSET/hero_collection_system.py) | 武将图鉴收集 |
| 武将转生 | [hero_rebirth_system.py](Android/ASSET/hero_rebirth_system.py) | 转生系统（Android 版独有） |
| 装备系统 | [equipment_system.py](Android/ASSET/equipment_system.py) | 装备穿戴、强化 |
| 宠物系统 | [pet_system.py](Android/ASSET/pet_system.py) | 宠物捕捉、培养 |
| 宠物竞技 | [pet_arena.py](Android/ASSET/pet_arena.py) | 宠物对战 |
| 副本系统 | [dungeon_system.py](Android/ASSET/dungeon_system.py) | 多层副本挑战 |
| 商店系统 | [shop_system.py](Android/ASSET/shop_system.py) | 资源、武将、装备购买 |
| 任务系统 | [quest_system.py](Android/ASSET/quest_system.py) | 主线/支线任务 |
| 任务链 | [task_chain_system.py](Android/ASSET/task_chain_system.py) | 连环任务 |
| 成就系统 | [achievement_system.py](Android/ASSET/achievement_system.py) | 成就解锁 |
| 排行榜 | [ranking_system.py](Android/ASSET/ranking_system.py) | 全服排名 |
| 阵法系统 | [strategy_map_system.py](Android/ASSET/strategy_map_system.py) | 阵法搭配 |
| 天赋系统 | [talent_system.py](Android/ASSET/talent_system.py) | 天赋树 |
| 科技树 | [tech_tree.py](Android/ASSET/tech_tree.py) | 科技研究 |
| 炼金系统 | [alchemy_system.py](Android/ASSET/alchemy_system.py) | 物品合成 |
| 时装系统 | [fashion_system.py](Android/ASSET/fashion_system.py) | 武将外观 |
| 钓鱼系统 | [fishing_system.py](Android/ASSET/fishing_system.py) | 休闲钓鱼 |
| 建筑系统 | [building_system.py](Android/ASSET/building_system.py) | 主城建设 |
| 天气系统 | [weather_system.py](Android/ASSET/weather_system.py) | 动态天气 |
| 事件系统 | [event_system.py](Android/ASSET/event_system.py) | 随机事件 |
| 限时事件 | [limited_time_events.py](Android/ASSET/limited_time_events.py) | 节日活动 |
| 活动系统 | [activity_system.py](Android/ASSET/activity_system.py) | 周期活动 |
| 每日奖励 | [daily_reward_system.py](Android/ASSET/daily_reward_system.py) | 累积奖励（非传统签到） |
| 新手引导 | [newbie_guide.py](Android/ASSET/newbie_guide.py) | 新手指引 |
| 背景故事 | [background_story.py](Android/ASSET/background_story.py) | 剧情文本 |
| 现代 UI | [modern_ui_system.py](Android/ASSET/modern_ui_system.py) | UI 组件库 |
| 视觉特效 | [visual_effects.py](Android/ASSET/visual_effects.py) | 粒子、特效 |
| 趣味效果 | [fun_effects.py](Android/ASSET/fun_effects.py) | 鼠标跟随等 |
| 优化渲染 | [optimized_render.py](Android/ASSET/optimized_render.py) | 渲染优化 |
| 登录系统 | [login_system.py](Android/ASSET/login_system.py) | 注册、登录、用户管理 |
| 词典伪装 | [dictionary_system.py](Android/ASSET/dictionary_system.py) | 英语词典界面 |
| 白板伪装 | [whiteboard.py](Android/ASSET/whiteboard.py) | 教学白板界面 |
| 世界聊天 | [world_chat.py](Android/ASSET/world_chat.py) | 全服聊天 |
| 聊天服务器 | [chat_server.py](Android/ASSET/chat_server.py) | 聊天服务端 |
| 网络 PvP | [network_pvp.py](Android/ASSET/network_pvp.py) | 在线对战 |
| P2P 对战 | [pvp_p2p.py](Android/ASSET/pvp_p2p.py) | P2P 对战 |
| 在线对战 | [pvp_online.py](Android/ASSET/pvp_online.py) | 在线匹配 |
| 超级对战 | [pvp_super.py](Android/ASSET/pvp_super.py) | 综合对战 |
| ngrok 穿透 | [p2p_ngrok.py](Android/ASSET/p2p_ngrok.py) | 内网穿透 |
| 安全网络 | [secure_network.py](Android/ASSET/secure_network.py) | 加密通信 |
| AI 系统 | [ai_system.py](Android/ASSET/ai_system.py) | AI 行为 |
| 自动更新 | [auto_update.py](Android/ASSET/auto_update.py) | 版本检测 |
| 多语言 | [languages.py](Android/ASSET/languages.py) | 国际化 |
| 反编译保护 | [anti_decompile.py](Android/ASSET/anti_decompile.py) | 代码保护 |
| 字体管理 | [font_manager.py](Android/ASSET/font_manager.py) | 字体加载 |
| FAQ | [faq_system.py](Android/ASSET/faq_system.py) | 常见问题 |
| 小游戏 | snake_game.py / tetris.py / game_2048.py / gobang.py / minesweeper.py / push_box.py / breakout.py | 休闲小游戏 |

---

## 核心数据与存档

### 存档文件

| 文件 | 位置 | 说明 |
|------|------|------|
| `save.json` | `ASSET/save.json` | 默认游戏存档（玩家数据、武将、资源等） |
| `users.json` | `ASSET/users.json` | 所有注册用户数据 |
| `login_state.json` | `ASSET/login_state.json` | 当前登录状态缓存 |

### 数据核心 [game_data.py](Android/ASSET/game_data.py)

- `data`: 全局游戏数据字典（玩家进度、武将、资源、设置）
- `save()`: 保存数据到 `save.json`
- `load()`: 从 `save.json` 加载（带备份恢复）
- `get_system_font_name()`: 跨平台中文字体适配
- `load_sound()`: 音效加载
- `SETTINGS`: 全局设置（分辨率、全屏等）

### 数据安全约定

- 所有文件写入使用 **「备份 → 临时文件 → 原子重命名」** 模式
- 数据加载失败时自动尝试从备份恢复
- 关键数据访问点必须有 try-except + 日志
- 数据操作需线程安全（lock 保护）
- 加载时验证数据完整性并自动修正缺失键

---

## 字体与跨平台显示

游戏依赖 [game_data.py](Android/ASSET/game_data.py) 中的 `get_system_font_name()` 实现跨平台中文显示：

1. **优先**：使用打包的字体文件（`ASSET/fonts/*.ttf`），确保其他设备也能正常显示
2. **回退 1**：检测系统平台（Windows → 微软雅黑/宋体；macOS → 苹方；Linux → 文泉驿；Android → DroidSansFallback）
3. **回退 2**：使用 Pygame 默认字体（可能显示方框）

### 打包字体

- 字体文件位于 [Android/ASSET/fonts/字魂白鸽天行体(商用需授权).ttf](Android/ASSET/fonts/)
- 打包 EXE 时通过 `sys._MEIPASS` 解包临时目录加载
- 打包 APK 时通过 Buildozer 的 `include` 配置包含

> **注意**：若在其他设备上文字显示为方框，请检查：
> 1. `game_data.py` 是否有 `import sys`
> 2. `fonts/` 目录是否随程序一起分发
> 3. `get_system_font_name()` 是否正确返回字体路径

---

## 打包与发布

### Windows EXE 打包

使用 [SangoHeroes.spec](Android/SangoHeroes.spec)：

```bash
cd san_guo/Android
pyinstaller SangoHeroes.spec
```

或使用打包工具：

```bash
python 打包工具.py
```

打包产物位于 `dist/` 目录。

### Android APK 打包

详见 [APK构建教程.md](APK构建教程.md)，主要使用 Buildozer：

```bash
buildozer -v android debug
```

配置文件为 [buildozer.spec](Android/buildozer.spec)。

### 打包注意事项

1. 确保字体文件随包分发
2. 隐藏导入（hiddenimports）需包含所有动态导入的模块
3. C++ 渲染器（`opengl_renderer.dll`）为可选加速模块，缺失时自动降级为纯 Python 渲染
4. 数据文件（`save.json`、`users.json`）通过 `datas` 配置包含

---

## 开发规范

### 代码风格

- **Python 版本**: 兼容 3.6+，避免使用海象运算符 `:=`、`match` 语句等高版本语法
- **编码**: 所有 `.py` 文件使用 UTF-8（无 BOM）
- **缩进**: 4 空格
- **命名**: 模块文件使用 `snake_case.py`；系统文件统一 `[系统名]_system.py`
- **注释**: 关键逻辑必须有中文注释

### 架构约定

- **菜单集成**: 新功能必须挂载到「游戏系统」或「其他功能」下拉菜单
- **菜单项 ID**: 每个菜单项分配唯一数字标识（如 40=副将系统、41=阵法系统）
- **数据动态获取**: 所有数据映射从中央数据库（`HERO_DATABASE`、`EQUIPMENT_DATABASE`）动态读取，避免硬编码
- **复用函数**: 优先复用 `buy_resource`、`buy_hero_fragments` 等现有函数，避免代码重复
- **错误处理**: 关键操作必须有 try-except + 日志记录
- **资源释放**: 文件句柄、Surface 对象用完即释放，避免内存泄漏
- **字体缓存**: 频繁创建的 Font 对象应使用缓存（参见 `battle_system.py` 的 `_get_cached_font`）
- **静态文本**: 静态标签预渲染到 `cached_labels` 字典，避免每帧重复渲染
- **UI 事件**: 事件处理需包含 `handled` 标志，防止多个控件响应同一事件
- **下拉菜单**: 必须渲染在最顶层，并处理外部点击关闭

### 防御性编程

- **除零保护**: `ratio = current / maximum if maximum > 0 else 0`
- **空列表访问**: `goals[-1]` 前必须检查 `if goals`
- **零尺寸渲染**: `draw_gradient_rect` 等需检查 `width > 0 and height > 0`
- **颜色范围**: RGB 值使用 `max(0, min(255, v))` 钳制
- **Slider 控件**: 检查 `max_val == min_val` 和 `width == 0` 防止除零

### 玩家友好设计

- **反对逼氪**: 不添加任何逼氪或玩家不友好的设定
- **讽刺文案**: 在福利、商店模块讽刺其他游戏厂商的常见套路
- **每日奖励**: 不使用「固定时间签到」机制，改为玩家友好型累积奖励
- **奖励增长**: 使用乘法增长而非加法递增，保证长期进度感
- **玩家自主权**: 遇到不舒适设定时，给予玩家开发者级修改权限（开发者控制台 → 其他功能）

### 同步策略

三套代码库需保持同步：

- `ASSET/`（根目录基础版）
- `Android/ASSET/`（Android 重构版，主开发分支）
- `san_guo/ASSET/`（PC 稳定版）

修改任何文件后，需在三处同步应用。可使用 `force_sync_all.py` 或 `sync_to_py_cpp.py` 辅助同步。

---

## 常见问题排查

### 1. 文字显示为方框

**原因**：字体文件未随程序分发，或 `game_data.py` 缺少 `import sys`

**解决**：
- 确认 `ASSET/fonts/` 目录下有 `.ttf` 字体文件
- 确认 `game_data.py` 顶部有 `import sys`
- 打包时确认 `SangoHeroes.spec` 的 `datas` 包含字体目录

### 2. PvP 对战闪退

**原因**：网络模块异常或战斗系统除零

**解决**：
- 检查 [battle_system.py](Android/ASSET/battle_system.py) 的 `draw_health_bar` 是否有除零保护
- 检查 [network_pvp.py](Android/ASSET/network_pvp.py) 的网络连接是否稳定
- 查看 `game.log` 中的异常堆栈

### 3. 存档加载失败

**原因**：`save.json` 损坏或缺失关键键

**解决**：
- 程序会自动尝试从备份恢复
- 若备份也损坏，可删除 `save.json` 重新开始
- 检查 `game_data.py` 的 `load()` 函数日志

### 4. 启动时 SyntaxError

**原因**：文件包含 BOM 头或编码错误

**解决**：
- 使用 UTF-8（无 BOM）重新保存文件
- 检查文件是否被截断（行数是否完整）

### 5. 性能卡顿

**原因**：字体频繁创建、Surface 未缓存、渲染未优化

**解决**：
- 使用 `_get_cached_font` 缓存字体
- 静态文本预渲染到 `cached_labels`
- 参见 [性能优化建议.md](性能优化建议.md)

### 6. CPU 占用过高的 nested while 循环

**原因**：部分模块（如 `faq_system.py`）使用嵌套 while 循环且无 sleep

**解决**：
- 在内层循环加入 `pygame.time.Clock().tick(30)` 限制帧率
- 或使用事件驱动模型替代轮询

---

## 日志与调试

- **日志文件**: `game.log` / `debug.log`（运行目录下生成）
- **日志级别**: INFO（默认），可调整为 DEBUG 查看详细输出
- **查看异常**: 启动失败时控制台会打印完整堆栈，同时写入日志文件

---

## 致谢

- 字体：字魂白鸽天行体（商用需授权）
- 引擎：Pygame、PyOpenGL
- 灵感：Minecraft、三国群英传

---

## 版本历史

| 版本 | 主要变更 |
|------|---------|
| v22 | 修复跨设备字体显示、PvP 闪退、除零错误；优化 UI 性能；新增 README 文档 |
| ... | （详见 git log） |

---

> 本项目仅用于学习交流，请勿用于商业用途。游戏中所有讽刺文案均为对游戏行业不良现象的批评，并非针对具体厂商。
