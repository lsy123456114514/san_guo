#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import platform

def build_windows():
    """构建 Windows 版本"""
    print("="*60)
    print("构建 Windows 版本...")
    print("="*60)
    
    cmd = [
        "pyinstaller",
        "main.py",
        "--name=三国霸业_Win",
        "--onefile",
        "--windowed",
        "--add-data=ASSET;ASSET",
        "--add-data=data;data",
        "--hidden-import=pygame",
        "--hidden-import=numpy",
        "--hidden-import=requests",
        "--icon=data/icon.png",
        "--upx-dir=.",
        "--distpath=dist/windows",
        "--workpath=build/windows",
        "--specpath=spec"
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("构建成功！")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e.stderr}")
        return False

def build_macos():
    """构建 macOS 版本（需要在 macOS 上运行）"""
    print("="*60)
    print("构建 macOS 版本...")
    print("="*60)
    
    cmd = [
        "pyinstaller",
        "main.py",
        "--name=三国霸业_Mac",
        "--onefile",
        "--windowed",
        "--add-data=ASSET:ASSET",
        "--add-data=data:data",
        "--hidden-import=pygame",
        "--hidden-import=numpy",
        "--hidden-import=requests",
        "--icon=data/icon.png",
        "--distpath=dist/macos",
        "--workpath=build/macos",
        "--specpath=spec"
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("构建成功！")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e.stderr}")
        return False

def build_linux():
    """构建 Linux 版本（需要在 Linux 上运行）"""
    print("="*60)
    print("构建 Linux 版本...")
    print("="*60)
    
    cmd = [
        "pyinstaller",
        "main.py",
        "--name=三国霸业_Linux",
        "--onefile",
        "--windowed",
        "--add-data=ASSET:ASSET",
        "--add-data=data:data",
        "--hidden-import=pygame",
        "--hidden-import=numpy",
        "--hidden-import=requests",
        "--icon=data/icon.png",
        "--distpath=dist/linux",
        "--workpath=build/linux",
        "--specpath=spec"
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("构建成功！")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e.stderr}")
        return False

def create_build_scripts():
    """创建各平台的构建脚本"""
    print("="*60)
    print("创建平台构建脚本...")
    print("="*60)
    
    # 创建 macOS 构建脚本
    mac_script = """#!/bin/bash
echo "构建 macOS 版本..."
cd "$(dirname "$0")"
pyinstaller main.py \\
    --name=三国霸业_Mac \\
    --onefile \\
    --windowed \\
    --add-data=ASSET:ASSET \\
    --add-data=data:data \\
    --hidden-import=pygame \\
    --hidden-import=numpy \\
    --hidden-import=requests \\
    --icon=data/icon.png \\
    --distpath=dist/macos \\
    --workpath=build/macos \\
    --specpath=spec
echo "构建完成！"
"""
    with open("build_macos.sh", "w") as f:
        f.write(mac_script)
    os.chmod("build_macos.sh", 0o755)
    print("已创建: build_macos.sh")
    
    # 创建 Linux 构建脚本
    linux_script = """#!/bin/bash
echo "构建 Linux 版本..."
cd "$(dirname "$0")"
pyinstaller main.py \\
    --name=三国霸业_Linux \\
    --onefile \\
    --windowed \\
    --add-data=ASSET:ASSET \\
    --add-data=data:data \\
    --hidden-import=pygame \\
    --hidden-import=numpy \\
    --hidden-import=requests \\
    --icon=data/icon.png \\
    --distpath=dist/linux \\
    --workpath=build/linux \\
    --specpath=spec
echo "构建完成！"
"""
    with open("build_linux.sh", "w") as f:
        f.write(linux_script)
    os.chmod("build_linux.sh", 0o755)
    print("已创建: build_linux.sh")
    
    # 创建 Windows 构建脚本
    win_script = """@echo off
echo 构建 Windows 版本...
cd /d "%~dp0"
pyinstaller main.py ^
    --name=三国霸业_Win ^
    --onefile ^
    --windowed ^
    --add-data=ASSET;ASSET ^
    --add-data=data;data ^
    --hidden-import=pygame ^
    --hidden-import=numpy ^
    --hidden-import=requests ^
    --icon=data/icon.png ^
    --distpath=dist/windows ^
    --workpath=build/windows ^
    --specpath=spec
echo 构建完成！
pause
"""
    with open("build_windows.bat", "w") as f:
        f.write(win_script)
    print("已创建: build_windows.bat")

def main():
    """主函数"""
    os.makedirs("dist", exist_ok=True)
    os.makedirs("build", exist_ok=True)
    os.makedirs("spec", exist_ok=True)
    
    current_platform = platform.system()
    
    print(f"当前平台: {current_platform}")
    print("