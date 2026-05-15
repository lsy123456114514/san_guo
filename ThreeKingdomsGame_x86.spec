# -*- mode: python ; coding: utf-8 -*-
# 32位版本打包配置

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('ASSET', 'ASSET'), ('data', 'data')],
    hiddenimports=['pkg_resources', 'pkg_resources.py2_warn', 'jaraco', 'jaraco.functools', 'jaraco.context', 'jaraco.text', 'pkg_resources._vendor.jaraco.functools', 'pkg_resources._vendor.jaraco.context', 'pkg_resources._vendor.jaraco.text'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'PyQt5', 'wx', 'scipy', 'numpy', 'matplotlib', 'pandas', 'tensorflow', 'torch', 'sklearn'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ThreeKingdoms_Game3_x86',  # 32位版本命名
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='x86',  # 32位架构
    codesign_identity=None,
    entitlements_file=None,
)
