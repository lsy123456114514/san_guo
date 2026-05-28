#!/usr/bin/env python3
"""
强制同步所有文件到 PY C++ 文件夹
处理被程序占用的文件
"""
import os
import shutil
from pathlib import Path
import time

def force_sync_folder(src_dir, dst_dir, folder_name):
    """强制同步一个文件夹"""
    print(f"\n📁 正在同步: {folder_name}/")
    print("-" * 50)
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for root, dirs, files in os.walk(src_dir):
        # 跳过 .git 和 __pycache__ 文件夹
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules']]
        
        rel_path = os.path.relpath(root, src_dir)
        if rel_path == '.':
            dst_root = dst_dir
        else:
            dst_root = os.path.join(dst_dir, rel_path)
        
        # 确保目标目录存在
        if not os.path.exists(dst_root):
            try:
                os.makedirs(dst_root, exist_ok=True)
            except Exception as e:
                print(f"  ❌ 无法创建目录: {dst_root} - {e}")
                continue
        
        # 复制文件
        for file in files:
            if file.startswith('.'):
                continue  # 跳过隐藏文件
            
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dst_root, file)
            
            # 尝试最多3次
            for attempt in range(3):
                try:
                    # 如果目标文件存在，先删除
                    if os.path.exists(dst_file):
                        try:
                            os.remove(dst_file)
                        except:
                            pass
                    
                    shutil.copy2(src_file, dst_file)
                    success_count += 1
                    break
                except PermissionError:
                    # 文件被占用，跳过
                    skip_count += 1
                    break
                except Exception as e:
                    if attempt < 2:
                        time.sleep(0.5)
                    else:
                        error_count += 1
    
    print(f"  ✅ 成功: {success_count} | ⏭️ 跳过: {skip_count} | ❌ 错误: {error_count}")
    return success_count, skip_count, error_count

def main():
    root = Path("e:/san_guo")
    py_cpp = root / "PY C++"
    san_guo = root / "san_guo"
    android = root / "Android"
    
    print("=" * 70)
    print("🚀 强制同步所有文件到 Android 文件夹")
    print("=" * 70)
    
    total_success = 0
    total_skip = 0
    total_error = 0
    
    # 同步 san_guo 文件夹
    if san_guo.exists():
        s, sk, e = force_sync_folder(san_guo, android, "san_guo")
        total_success += s
        total_skip += sk
        total_error += e
    
    # 同步 PY C++ 文件夹
    if py_cpp.exists():
        s, sk, e = force_sync_folder(py_cpp, android, "PY C++")
        total_success += s
        total_skip += sk
        total_error += e
    
    print("\n" + "=" * 70)
    print("📊 同步完成！")
    print(f"   ✅ 成功复制: {total_success} 个文件")
    print(f"   ⏭️ 跳过(被占用): {total_skip} 个文件")
    print(f"   ❌ 错误: {total_error} 个文件")
    print("=" * 70)
    
    if total_skip > 0:
        print("\n💡 提示: 有些文件被其他程序占用，你可以:")
        print("   1. 关闭正在使用这些文件的程序")
        print("   2. 稍后再次运行此脚本")

if __name__ == "__main__":
    main()
