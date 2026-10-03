# -*- mode: python ; coding: utf-8 -*-
# 三国群英传 · 自动测试（双模式）：
#   无参数双击     → tkinter 图形界面
#   带参数         → 无界面 CLI（后台隐藏运行，输出走报告文件/父控制台）
# 打包：py -m PyInstaller auto_test.spec --noconfirm

import os
from PyInstaller.utils.hooks import collect_submodules

# 运行时 ASSET.game_main_menu 用 importlib.import_module("ASSET."+name)
# 动态导入各模块，必须整包收集；tkinter 是 GUI 依赖，绝不能排除
hiddenimports = collect_submodules('ASSET') + [
    'pygame',
    'OpenGL',
    'OpenGL.GL',
    'OpenGL.GLU',
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    # 入口脚本自身：gmm 里 `from auto_test import AutoTestDriver`
    # （实际由 run() 的 sys.modules 注册命中，此处兜底）
    'auto_test',
]

a = Analysis(
    ['auto_test.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ASSET', 'ASSET'),
        # C++ 渲染器 DLL（game_map_3d.py 打包后从 _internal/ 查找）
        ('opengl_renderer.dll', '.'),
        ('renderer_bindings.py', '.'),
        # 3D 地图数据（相对 cwd 读写，冻结后 cwd=_internal）
        ('map_data_lsy.json', '.'),
        ('map_data_weqwqewq.json', '.'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['numpy', 'numpy.libs', 'setuptools', 'pip',
              'PyQt5', 'matplotlib', 'scipy', 'pandas', 'PIL'],
    noarchive=False,
    optimize=0,
)

# 排除缓存字节码（运行时用不到）
a.datas = [d for d in a.datas if '__pycache__' not in d[0]]


def _bn(p):
    return os.path.basename(p.replace('/', os.sep)).lower()


def _dirname(p):
    return os.path.dirname(p.replace('/', os.sep))


# 去重：pygame 子目录里的 DLL 与顶层同名 DLL 重复，留顶层即可
_top = {_bn(d[0]) for d in a.binaries if _dirname(d[0]) in ('', '.')}
a.binaries = [d for d in a.binaries
              if _dirname(d[0]) in ('', '.') or _bn(d[0]) not in _top]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='自动测试',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # 无控制台：双击出 GUI；带参时输出走管道/父控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='自动测试',
)
