#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三国游戏 - GUI 打包工具 (简化版)
功能：创建 Windows 可执行文件 (EXE)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import sys
import shutil
from datetime import datetime


class PackerGUI:
    """打包工具主类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("三国游戏 - 打包工具")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # 设置样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 创建变量
        self.project_path = tk.StringVar(value=os.path.dirname(os.path.abspath(__file__)))
        self.main_script = tk.StringVar(value="main.py")
        self.output_name = tk.StringVar(value="SangoHeroes")
        self.one_file = tk.BooleanVar(value=True)
        self.console = tk.BooleanVar(value=False)
        self.upx = tk.BooleanVar(value=True)
        self.clean_build = tk.BooleanVar(value=True)
        
        # 打包状态
        self.is_packing = False
        
        # 创建界面
        self.create_widgets()
    
    def create_widgets(self):
        """创建所有组件"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🎮 三国游戏打包工具", font=('微软雅黑', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # 基本设置
        basic_frame = ttk.LabelFrame(main_frame, text="基本设置", padding="10")
        basic_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(basic_frame, text="项目路径:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(basic_frame, textvariable=self.project_path, width=50).grid(row=0, column=1)
        ttk.Button(basic_frame, text="浏览", command=self.browse_project_path).grid(row=0, column=2)
        
        ttk.Label(basic_frame, text="主脚本:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(basic_frame, textvariable=self.main_script, width=50).grid(row=1, column=1)
        
        ttk.Label(basic_frame, text="输出名称:").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(basic_frame, textvariable=self.output_name, width=50).grid(row=2, column=1)
        
        # 打包选项
        option_frame = ttk.LabelFrame(main_frame, text="打包选项", padding="10")
        option_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Checkbutton(option_frame, text="单文件模式", variable=self.one_file).grid(row=0, column=0)
        ttk.Checkbutton(option_frame, text="显示控制台", variable=self.console).grid(row=0, column=1)
        ttk.Checkbutton(option_frame, text="UPX 压缩", variable=self.upx).grid(row=0, column=2)
        ttk.Checkbutton(option_frame, text="清理旧构建", variable=self.clean_build).grid(row=0, column=3)
        
        # 预设按钮
        preset_frame = ttk.Frame(main_frame)
        preset_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(preset_frame, text="🎮 游戏模式", command=self.preset_game, width=15).grid(row=0, column=0, padx=5)
        ttk.Button(preset_frame, text="📦 便携版", command=self.preset_portable, width=15).grid(row=0, column=1, padx=5)
        ttk.Button(preset_frame, text="🖥️ 控制台", command=self.preset_console, width=15).grid(row=0, column=2, padx=5)
        ttk.Button(preset_frame, text="⚡ 轻量版", command=self.preset_lightweight, width=15).grid(row=0, column=3, padx=5)
        
        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        self.pack_button = ttk.Button(button_frame, text="🚀 开始打包", command=self.start_packing, width=20)
        self.pack_button.grid(row=0, column=0, padx=10)
        
        ttk.Button(button_frame, text="🧹 清理", command=self.clean_build_dir, width=15).grid(row=0, column=1)
        ttk.Button(button_frame, text="📂 打开输出", command=self.open_output_dir, width=15).grid(row=0, column=2)
        
        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', length=500)
        self.progress.grid(row=5, column=0, columnspan=2, pady=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="打包日志", padding="10")
        log_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, font=('Consolas', 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置主框架权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
    
    # 预设配置
    def preset_game(self):
        """游戏模式"""
        self.one_file.set(True)
        self.console.set(False)
        self.upx.set(True)
        self.output_name.set("SangoHeroes")
        self.log_message("✓ 游戏模式：单文件 + 无控制台 + UPX")
    
    def preset_portable(self):
        """便携版"""
        self.one_file.set(False)
        self.console.set(False)
        self.upx.set(False)
        self.output_name.set("SangoHeroes_Portable")
        self.log_message("✓ 便携版：目录模式 + 无控制台")
    
    def preset_console(self):
        """控制台模式"""
        self.one_file.set(True)
        self.console.set(True)
        self.upx.set(True)
        self.output_name.set("SangoHeroes_Console")
        self.log_message("✓ 控制台模式：单文件 + 显示控制台")
    
    def preset_lightweight(self):
        """轻量模式"""
        self.one_file.set(True)
        self.console.set(False)
        self.upx.set(True)
        self.output_name.set("SangoHeroes_Light")
        self.log_message("✓ 轻量模式：单文件 + 最小体积")
    
    # 文件浏览
    def browse_project_path(self):
        path = filedialog.askdirectory(title="选择项目目录")
        if path:
            self.project_path.set(path)
    
    # 日志
    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    # 打包控制
    def start_packing(self):
        if self.is_packing:
            messagebox.showwarning("警告", "正在打包中...")
            return
        
        # 验证
        if not os.path.exists(self.project_path.get()):
            messagebox.showerror("错误", "项目路径不存在！")
            return
        
        main_script_path = os.path.join(self.project_path.get(), self.main_script.get())
        if not os.path.exists(main_script_path):
            messagebox.showerror("错误", f"主脚本不存在: {self.main_script.get()}")
            return
        
        # 开始打包
        self.is_packing = True
        self.pack_button.config(state=tk.DISABLED)
        self.progress.start()
        
        thread = threading.Thread(target=self.pack_thread)
        thread.daemon = True
        thread.start()
    
    def pack_thread(self):
        try:
            self.log_message("=" * 50)
            self.log_message("🚀 开始打包...")
            self.log_message(f"项目: {self.project_path.get()}")
            self.log_message(f"脚本: {self.main_script.get()}")
            self.log_message(f"输出: {self.output_name.get()}")
            
            # 切换目录
            original_dir = os.getcwd()
            os.chdir(self.project_path.get())
            
            # 清理
            if self.clean_build.get():
                self.log_message("🧹 清理旧构建...")
                if os.path.exists("build"):
                    shutil.rmtree("build")
                if os.path.exists("dist"):
                    shutil.rmtree("dist")
            
            # 构建命令
            cmd = self.build_command()
            self.log_message(f"命令: {' '.join(cmd[:6])}...")
            
            # 执行
            self.log_message("⏳ 正在打包，请稍候...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_message("=" * 50)
                self.log_message("✅ 打包成功！")
                
                exe_path = os.path.join("dist", self.output_name.get() + ".exe")
                if os.path.exists(exe_path):
                    size = os.path.getsize(exe_path) / (1024 * 1024)
                    self.log_message(f"📍 输出: {exe_path}")
                    self.log_message(f"📊 大小: {size:.2f} MB")
                    self.log_message("🎉 可以分发了！")
                    
                    if messagebox.askyesno("成功", "打包完成！打开输出目录？"):
                        self.open_output_dir()
                else:
                    self.log_message("⚠️ 未找到输出文件，请检查 dist 目录")
            else:
                self.log_message("=" * 50)
                self.log_message("❌ 打包失败！")
                self.log_message("错误:")
                for line in result.stderr.split('\n')[-15:]:
                    if line.strip():
                        self.log_message(f"  {line}")
                
                messagebox.showerror("失败", "查看日志获取详细信息")
            
            os.chdir(original_dir)
            
        except Exception as e:
            self.log_message(f"❌ 错误: {str(e)}")
            
        finally:
            self.is_packing = False
            self.progress.stop()
            self.pack_button.config(state=tk.NORMAL)
    
    def build_command(self):
        """构建 PyInstaller 命令"""
        cmd = [sys.executable, '-m', 'PyInstaller']
        
        # 单文件
        if self.one_file.get():
            cmd.append('--onefile')
        
        # 名称
        cmd.extend(['--name', self.output_name.get()])
        
        # 控制台
        if not self.console.get():
            cmd.append('--noconsole')
        
        # UPX - 修复！不再要求 upx 目录
        if self.upx.get():
            cmd.append('--upx')
        else:
            cmd.append('--no-upx')
        
        # 清理
        cmd.append('--noconfirm')
        
        # 添加数据
        cmd.extend(['--add-data', 'ASSET' + os.pathsep + 'ASSET'])
        cmd.extend(['--add-data', 'data' + os.pathsep + 'data'])
        
        # 隐藏导入（针对游戏优化）
        cmd.extend(['--hidden-import', 'pkg_resources'])
        cmd.extend(['--hidden-import', 'jaraco.functools'])
        
        # 排除不必要的模块
        excludes = ['tkinter', 'PyQt5', 'wx', 'scipy', 'numpy', 'matplotlib', 'pandas', 'tensorflow', 'torch', 'sklearn']
        for e in excludes:
            cmd.extend(['--exclude-module', e])
        
        # 轻量模式额外排除
        if self.output_name.get().endswith('_Light'):
            cmd.extend(['--exclude-module', 'pkg_resources'])
            cmd.extend(['--exclude-module', 'jaraco'])
        
        # 主脚本
        cmd.append(self.main_script.get())
        
        return cmd
    
    def clean_build_dir(self):
        if messagebox.askyesno("确认", "确定清理 build 和 dist 目录？"):
            if os.path.exists("build"):
                shutil.rmtree("build")
            if os.path.exists("dist"):
                shutil.rmtree("dist")
            messagebox.showinfo("完成", "清理完成！")
    
    def open_output_dir(self):
        output_dir = os.path.join(self.project_path.get(), "dist")
        if os.path.exists(output_dir):
            os.startfile(output_dir)
        else:
            messagebox.showwarning("警告", "输出目录不存在！")


def main():
    root = tk.Tk()
    app = PackerGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
