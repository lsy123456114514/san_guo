# -*- coding: utf-8 -*-
"""
VoicePlay - 主程序入口
超酷的声音检测和互动项目
"""

import tkinter as tk
import os
import sys


def main():
    """主函数"""
    # 设置路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(current_dir, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    root = tk.Tk()
    root.title("🎵 VoicePlay - 声音魔法乐园")
    root.geometry("1000x700")
    root.resizable(True, True)
    
    try:
        from ui.main_window import VoicePlayWindow
        app = VoicePlayWindow(root)
        root.mainloop()
    except Exception as e:
        import traceback
        error_msg = f"程序启动失败：\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        # 尝试简单错误提示
        try:
            import tkinter.messagebox as mb
            mb.showerror("启动错误", error_msg)
        except:
            pass


if __name__ == "__main__":
    main()
