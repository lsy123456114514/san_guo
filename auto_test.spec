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
              'PyQt5', 'matplotlib', 'scipy', 'pandas', 'PIL',
              # urllib3.contrib.pyopenssl 的可选链：整包 4MB+，游戏 HTTP
              # 请求走 stdlib ssl，运行时用不到（实测全量测试通过）
              'cryptography', 'OpenSSL', 'cffi', '_cffi_backend',
              'urllib3.contrib.pyopenssl'],
    noarchive=False,
    optimize=0,
)

# 数据文件瘦身：排除运行时用不到的东西（约 4MB）
#   __pycache__   —— 字节码缓存，冻结环境不加载
#   tcl/tk 的 tzdata/msgs/demos/http1.0/opt0.4 —— GUI 只用标准控件 +
#   中文标签，时区数据/多语言错误消息/演示脚本都用不上（encoding 必须保留：
#   Tk 文本控件依赖它做非 ASCII 编码转换）
_DROP_DATA = ('__pycache__',
              '_tcl_data/tzdata/', '_tcl_data/msgs/',
              '_tcl_data/http1.0/', '_tcl_data/opt0.4/',
              '_tk_data/msgs/', '_tk_data/demos/')
a.datas = [d for d in a.datas
           if not any(s in d[0].replace('\\', '/') for s in _DROP_DATA)]


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
    icon='auto_test.ico',
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
