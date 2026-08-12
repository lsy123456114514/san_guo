#!/usr/bin/env python3
"""
三端同步工具

功能：
1. 同步 ASSET 目录中的 .py 文件到 Android / san_guo / PY C++ 三端，
   保持三端游戏代码一致（单向复制，不删除目标端独有文件）。
2. 同步 san_guo 文件夹中独有的语音相关文件到 PY C++ 文件夹。

用法：
    python sync_to_py_cpp.py               # 默认以 Android/ASSET 为源同步到另外两端
    python sync_to_py_cpp.py --source san_guo   # 指定以 san_guo/ASSET 为源
    python sync_to_py_cpp.py --source pycpp     # 指定以 PY C++/ASSET 为源
"""
import argparse
import os
import shutil
from pathlib import Path

# 三个游戏端的目录名（相对项目根目录）
ENDS = {
    "android": "Android",
    "san_guo": "san_guo",
    "pycpp": "PY C++",
}

# 需要同步的 ASSET 关键文件（None 表示同步整个 ASSET 目录）
SYNC_ALL_ASSET = True


def get_root() -> Path:
    """自动识别项目根目录（脚本所在目录），不再硬编码路径"""
    return Path(os.path.dirname(os.path.abspath(__file__)))


def sync_asset(source: str, root: Path):
    """将源端的 ASSET/*.py 同步到其它两端"""
    src_dir = root / ENDS[source] / "ASSET"
    targets = [name for name, _ in ENDS.items() if name != source]

    if not src_dir.exists():
        print(f"❌ 源目录不存在: {src_dir}")
        return

    print("=" * 60)
    print(f"开始同步 ASSET 目录：{ENDS[source]}/ASSET -> {', '.join(ENDS[t] + '/ASSET' for t in targets)}")
    print("=" * 60)

    files = sorted(src_dir.glob("*.py"))
    for file in files:
        for target in targets:
            dst_dir = root / ENDS[target] / "ASSET"
            dst_file = dst_dir / file.name
            # 覆盖同名文件或新增缺失文件（不删除目标端独有文件）
            shutil.copy2(file, dst_file)
            print(f"✅ 已同步: {ENDS[target]}/ASSET/{file.name}")

    print("=" * 60)
    print(f"ASSET 同步完成，共处理 {len(files)} 个文件")
    print("=" * 60)


def sync_voice_files(root: Path):
    """同步 san_guo 文件夹中独有的语音文件到 PY C++ 文件夹（保留原功能）"""
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
    print("开始同步语音文件到 PY C++ 文件夹")
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
    print("语音文件同步完成！")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="三端游戏代码同步工具")
    parser.add_argument("--source", choices=ENDS.keys(), default="android",
                        help="ASSET 同步的源端（默认 android）")
    parser.add_argument("--skip-asset", action="store_true",
                        help="跳过 ASSET 同步，仅同步语音文件")
    args = parser.parse_args()

    root = get_root()
    print(f"项目根目录: {root}")

    if not args.skip_asset:
        sync_asset(args.source, root)
    sync_voice_files(root)


if __name__ == "__main__":
    main()
