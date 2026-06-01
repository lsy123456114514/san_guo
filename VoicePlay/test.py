# -*- coding: utf-8 -*-
"""
VoicePlay 快速测试脚本
"""

import sys
import os

print("=" * 50)
print("   VoicePlay - 快速环境测试")
print("=" * 50)
print()

# 测试1: 检查Python
print("[1/5] 检查Python版本...")
print(f"    Python 版本: {sys.version}")
if sys.version_info < (3, 8):
    print("    ⚠️ 警告: 建议使用Python 3.8或更高版本")
else:
    print("    ✅ Python版本符合要求")
print()

# 测试2: 检查核心依赖
print("[2/5] 检查核心依赖...")
modules = [
    ("numpy", "NumPy - 数学计算库"),
    ("librosa", "Librosa - 音频处理库"),
    ("sounddevice", "SoundDevice - 音频IO库"),
    ("pygame", "Pygame - 音频播放库"),
    ("scipy", "SciPy - 科学计算库"),
]

all_ok = True
for module, desc in modules:
    try:
        __import__(module)
        print(f"    ✅ {desc}: OK")
    except ImportError:
        print(f"    ❌ {desc}: 未安装")
        all_ok = False
print()

# 测试3: 检查目录结构
print("[3/5] 检查目录结构...")
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
data_path = os.path.join(current_dir, 'data')

print(f"    根目录: {current_dir}")
if os.path.exists(src_path):
    print(f"    ✅ src目录: 存在")
else:
    print(f"    ❌ src目录: 不存在")
    all_ok = False

if not os.path.exists(data_path):
    os.makedirs(data_path, exist_ok=True)
    print(f"    ✅ data目录: 已创建")
else:
    print(f"    ✅ data目录: 存在")
print()

# 测试4: 检查主程序
print("[4/5] 检查主程序文件...")
main_py = os.path.join(current_dir, 'main.py')
if os.path.exists(main_py):
    print(f"    ✅ main.py: 存在")
else:
    print(f"    ❌ main.py: 不存在")
    all_ok = False

voice_module = os.path.join(src_path, 'voice_recognition.py')
if os.path.exists(voice_module):
    print(f"    ✅ voice_recognition.py: 存在")
else:
    print(f"    ⚠️ voice_recognition.py: 不存在")

ui_module = os.path.join(src_path, 'ui', 'main_window.py')
if os.path.exists(ui_module):
    print(f"    ✅ ui/main_window.py: 存在")
else:
    print(f"    ⚠️ ui/main_window.py: 不存在")
print()

# 测试5: 测试声音设备
print("[5/5] 测试音频设备...")
try:
    import sounddevice as sd
    devices = sd.query_devices()
    print(f"    ✅ 发现 {len(devices)} 个音频设备")
    if len(devices) > 0:
        print(f"    默认输入: {sd.default.device[0]}")
        print(f"    默认输出: {sd.default.device[1]}")
except Exception as e:
    print(f"    ⚠️ 音频设备测试失败: {e}")
print()

print("=" * 50)
if all_ok:
    print("   ✅ 所有检查通过！准备就绪。")
else:
    print("   ⚠️ 部分检查未通过，请解决后再运行。")
print("=" * 50)
print()
print("安装依赖命令:")
print("    py -m pip install -r requirements.txt")
print()
print("启动程序:")
print("    py main.py")
print("    或双击 启动VoicePlay.bat")
print()

try:
    input("按Enter键退出...")
except:
    pass
