#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏项目打包配置文件
使用PyInstaller将Python项目打包为exe可执行文件
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 要打包的主文件
MAIN_SCRIPT = os.path.join(PROJECT_ROOT, 'main.py')

# 收集所有需要的文件和模块
excluded_modules = [
    'tkinter',
    'PyQt5',
    'wx',
    'scipy',
    'numpy',
    'matplotlib',
    'pandas',
    'tensorflow',
    'torch',
    'sklearn'
]

# 数据文件
data_files = [
    # 主目录下的文件
    (PROJECT_ROOT, '.'),
    # ASSET目录
    (os.path.join(PROJECT_ROOT, 'ASSET'), 'ASSET'),
    # data目录
    (os.path.join(PROJECT_ROOT, 'data'), 'data'),
]

# 生成PyInstaller命令
pyinstaller_command = [
    'pyinstaller',
    '--name', 'ThreeKingdomsGame',
    '--onefile',
    '--windowed',
    '--add-data', 'ASSET;ASSET',
    '--add-data', 'data;data',
    '--hidden-import', 'pkg_resources',
    '--hidden-import', 'pkg_resources.py2_warn',
    '--hidden-import', 'pkg_resources._vendor.jaraco.functools',
    '--hidden-import', 'pkg_resources._vendor.jaraco.context',
    '--hidden-import', 'pkg_resources._vendor.jaraco.text',
    '--exclude-module', 'tkinter',
    '--exclude-module', 'PyQt5',
    '--exclude-module', 'wx',
    '--exclude-module', 'scipy',
    '--exclude-module', 'numpy',
    '--exclude-module', 'matplotlib',
    '--exclude-module', 'pandas',
    '--exclude-module', 'tensorflow',
    '--exclude-module', 'torch',
    '--exclude-module', 'sklearn',
    MAIN_SCRIPT
]

if __name__ == '__main__':
    print("开始打包游戏项目...")
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"主脚本: {MAIN_SCRIPT}")
    print("打包命令:")
    print(' '.join(pyinstaller_command))
    
    # 执行打包命令
    import subprocess
    subprocess.run(pyinstaller_command, cwd=PROJECT_ROOT)
