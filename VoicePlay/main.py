# -*- coding: utf-8 -*-
"""
VoicePlay - 主程序入口
超酷的声音检测和互动项目
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.main_window import VoicePlayWindow


def main():
    """主函数"""
    root = tk.Tk()
    root.title("🎵 VoicePlay - 声音魔法乐园")
    root.geometry("1000x700")
    root.resizable(True, True)
    
    try:
        root.iconbitmap(default="assets/icons/voiceplay.ico")
    except:
        pass
    
    app = VoicePlayWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
