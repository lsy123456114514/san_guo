#!/usr/bin/env python3
"""
同步 san_guo 文件夹中独有的文件到 PY C++ 文件夹
"""
import os
import shutil
from pathlib import Path

def sync_files():
    root = Path("e:/san_guo")
    san_guo = root / "san_guo"
    py_cpp = root / "PY C++"

    files_to_sync = [
        "build_all.py",
        "voice_recognition.py",
        "voice_recognition_example.py",
        "voice_recognition_gui.py",
        "voice_recognition_gui_enhanced.py",
        "voice_recognition_ultimate.py",
    ]

    dirs_to_sync = [
        "voice_data_gui",
        "voice_data_ultimate",
    ]

    print("=" * 60)
    print("开始同步文件到 PY C++ 文件夹")
    print("=" * 60)

    for file in files_to_sync:
        src = san_guo / file
        dst = py_cpp / file

        if src.exists():
            shutil.copy2(src, dst)
            print(f"✅ 已复制文件: {file}")
        else:
            print(f"❌ 源文件不存在: {file}")

    for dir_name in dirs_to_sync:
        src = san_guo / dir_name
        dst = py_cpp / dir_name

        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"✅ 已复制文件夹: {dir_name}/")
        else:
            print(f"❌ 源文件夹不存在: {dir_name}/")

    print("=" * 60)
    print("同步完成！")
    print("=" * 60)

if __name__ == "__main__":
    sync_files()
