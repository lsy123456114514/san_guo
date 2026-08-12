# -*- coding: utf-8 -*-
"""临时打包脚本：用 subprocess 列表传参，避免 shell 引号问题"""
import os
import subprocess
import sys

BASE = r'c:\Users\a\Desktop\san_guo\Android'
os.chdir(BASE)

# 清理上次失败残留
for p in [os.path.join('build', 'SangoHeroes_32'),
          os.path.join('dist', 'SangoHeroes_32.exe')]:
    if os.path.isdir(p):
        import shutil
        shutil.rmtree(p, ignore_errors=True)
    elif os.path.isfile(p):
        os.remove(p)

cmd = [
    sys.executable, '-m', 'PyInstaller',
    '--onefile',
    '--name', 'SangoHeroes_32',
    '--noconsole',
    '--noconfirm',
    '--add-data', 'ASSET' + os.pathsep + 'ASSET',
    '--add-data', 'data' + os.pathsep + 'data',
    '--collect-submodules', 'ASSET',
    '--hidden-import', 'pkg_resources',
    '--hidden-import', 'jaraco.functools',
    '--hidden-import', 'OpenGL.GL',
    '--hidden-import', 'OpenGL.GLU',
    '--hidden-import', 'OpenGL.arrays.ctypesarrays',
    '--hidden-import', 'OpenGL.platform.win32',
    '--collect-submodules', 'OpenGL',
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
    'main.py',
]

print('开始打包 SangoHeroes_32 ...')
with open('_build_26.log', 'w', encoding='utf-8', errors='replace') as f:
    result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
print('打包结束，退出码:', result.returncode)
if result.returncode != 0:
    with open('_build_26.log', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    print(''.join(lines[-20:]))
