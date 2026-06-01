# 🎵 VoicePlay - 声音魔法乐园

一个超酷的声音检测和互动项目，包含声纹识别、声音可视化、语音命令等有趣功能！

## ✨ 功能特点

| 功能模块 | 描述 |
|---------|------|
| 🎯 **声纹识别** | 录入声纹，识别说话人，关联专属音频 |
| 🎨 **声音可视化** | 炫酷的实时音频波形显示 |
| 🗣️ **语音命令** | 自定义语音指令（依赖SpeechRecognition） |
| 🎭 **趣味功能** | 多种变声效果，录音保存 |

## 🚀 快速开始

### 1️⃣ 环境要求

- **Python 3.8+**
- 麦克风和扬声器

### 2️⃣ 安装依赖

**Windows用户**（推荐）:
```bash
cd VoicePlay
py -m pip install -r requirements.txt
```

**其他平台**:
```bash
cd VoicePlay
pip install -r requirements.txt
```

### 3️⃣ 运行程序

**Windows用户**（推荐）:
```bash
# 双击运行
启动VoicePlay.bat
```

或命令行:
```bash
py main.py
```

**其他平台**:
```bash
python main.py
```

### 4️⃣ 测试环境

在运行程序前，可以先测试一下环境：

**Windows用户**:
```bash
py test.py
```

**其他平台**:
```bash
python test.py
```

## 📖 详细功能说明

### 🎯 声纹识别

1. 在"姓名"输入框输入名字
2. 点击"🎤 录入声纹"，对着麦克风说话
3. 可选：点击"🔊 设置音频"为用户设置专属音频
4. 点击"🔄 持续监听"开始识别

### 🎨 声音可视化

1. 切换到"声音可视化"标签页
2. 点击"▶️ 开始"
3. 对着麦克风说话，观察炫酷的波形动画

### 🎭 趣味功能

1. 切换到"趣味功能"标签页
2. 选择变声效果
3. 点击"🎤 录音并播放"
4. 喜欢的话点击"💾 保存录音"

## 📁 项目结构

```
VoicePlay/
├── main.py                  # 主程序入口
├── test.py                  # 环境测试脚本
├── 启动VoicePlay.bat       # Windows快速启动
├── requirements.txt         # 依赖列表
├── README.md               # 项目文档
├── src/                    # 源代码目录
│   ├── __init__.py
│   ├── voice_recognition.py  # 声纹识别核心
│   ├── audio_visualizer.py   # 声音可视化
│   ├── voice_commands.py     # 语音命令
│   ├── audio_effects.py      # 音频特效
│   └── ui/                   # UI界面
│       ├── __init__.py
│       └── main_window.py    # 主窗口
├── data/                   # 数据存储
│   ├── voices.json         # 声纹数据
│   └── commands.json       # 命令数据
└── assets/                 # 资源文件
    ├── icons/
    └── sounds/
```

## 🔧 依赖说明

| 库 | 用途 | 是否必需 |
|----|------|---------|
| numpy | 数学计算 | ✅ 必需 |
| librosa | 音频处理 | ✅ 必需 |
| sounddevice | 音频输入输出 | ✅ 必需 |
| pygame | 音频播放 | ✅ 必需 |
| scipy | 科学计算 | ✅ 必需 |
| SpeechRecognition | 语音识别 | ⚠️ 可选 |
| matplotlib | 图形显示 | ⚠️ 可选 |

## 💡 使用技巧

1. **声纹录入**: 安静环境下清晰说话2-3秒效果最好
2. **持续监听**: 最好先关闭扬声器，避免回声干扰
3. **变声效果**: 萝莉/大叔音效果明显，机器人和回声也很有趣

## 📝 开发计划

- [ ] 支持多语言
- [ ] 更多特效
- [ ] 在线演示
- [ ] 移动端适配

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

⭐ 如果喜欢这个项目，请给个 Star！
