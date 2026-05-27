#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三国游戏 - GUI 打包工具
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
        self.root.title("三国游戏 - 打包工具 v1.0")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # 设置样式
        self.setup_styles()
        
        # 创建变量
        self.setup_variables()
        
        # 创建界面
        self.create_widgets()
        
        # 加载默认配置
        self.load_default_config()
    
    def setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置颜色
        style.configure('Title.TLabel', font=('微软雅黑', 14, 'bold'), foreground='#2c3e50')
        style.configure('Header.TLabel', font=('微软雅黑', 10, 'bold'), foreground='#34495e')
        style.configure('Action.TButton', font=('微软雅黑', 10, 'bold'), padding=10)
        style.configure('Info.TLabel', font=('微软雅黑', 9), foreground='#7f8c8d')
    
    def setup_variables(self):
        """初始化变量"""
        self.project_path = tk.StringVar(value=os.path.dirname(os.path.abspath(__file__)))
        self.main_script = tk.StringVar(value="main.py")
        self.output_name = tk.StringVar(value="SangoHeroes")
        self.icon_path = tk.StringVar(value="")
        self.one_file = tk.BooleanVar(value=True)
        self.console = tk.BooleanVar(value=False)
        self.upx = tk.BooleanVar(value=True)
        self.auto_install = tk.BooleanVar(value=True)
        self.clean_build = tk.BooleanVar(value=True)
        
        # 高级选项
        self.hidden_imports = tk.StringVar(value="pkg_resources,pkg_resources.py2_warn,jaraco,jaraco.functools")
        self.exclude_modules = tk.StringVar(value="tkinter,PyQt5,wx,scipy,numpy,matplotlib,pandas,tensorflow,torch,sklearn")
        
        # 打包状态
        self.is_packing = False
    
    def load_default_config(self):
        """加载默认配置"""
        # 自动检测项目路径
        if os.path.exists(os.path.join(self.project_path.get(), "main.py")):
            self.log_message("✓ 检测到 main.py")
        
        # 检测是否有图标
        for icon in ["icon.ico", "icon.png", "data/icon.png"]:
            if os.path.exists(os.path.join(self.project_path.get(), icon)):
                self.icon_path.set(icon)
                self.log_message(f"✓ 检测到图标: {icon}")
                break
    
    def create_widgets(self):
        """创建所有组件"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🎮 三国游戏 - 打包工具", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # 第一列：基本设置
        self.create_basic_settings(main_frame)
        
        # 第二列：打包选项
        self.create_packing_options(main_frame)
        
        # 第三列：高级选项
        self.create_advanced_options(main_frame)
        
        # 预设配置
        self.create_presets(main_frame)
        
        # 控制按钮
        self.create_control_buttons(main_frame)
        
        # 日志输出
        self.create_log_area(main_frame)
        
        # 配置权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(7, weight=1)
    
    def create_basic_settings(self, parent):
        """基本设置"""
        frame = ttk.LabelFrame(parent, text="📁 基本设置", padding="10")
        frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # 项目路径
        ttk.Label(frame, text="项目路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.project_path, width=30).grid(row=0, column=1, pady=5)
        ttk.Button(frame, text="浏览", command=self.browse_project_path).grid(row=0, column=2, padx=5)
        
        # 主脚本
        ttk.Label(frame, text="主脚本:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.main_script, width=30).grid(row=1, column=1, columnspan=2, pady=5)
        
        # 输出名称
        ttk.Label(frame, text="输出名称:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.output_name, width=30).grid(row=2, column=1, columnspan=2, pady=5)
        
        # 图标
        ttk.Label(frame, text="图标文件:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.icon_path, width=30).grid(row=3, column=1, pady=5)
        ttk.Button(frame, text="选择", command=self.browse_icon).grid(row=3, column=2, padx=5)
    
    def create_packing_options(self, parent):
        """打包选项"""
        frame = ttk.LabelFrame(parent, text="⚙️ 打包选项", padding="10")
        frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # 单文件模式
        ttk.Checkbutton(frame, text="单文件模式 (--onefile)", variable=self.one_file).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 控制台窗口
        ttk.Checkbutton(frame, text="显示控制台", variable=self.console).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # UPX 压缩
        ttk.Checkbutton(frame, text="UPX 压缩", variable=self.upx).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 自动安装依赖
        ttk.Checkbutton(frame, text="自动安装依赖", variable=self.auto_install).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 清理构建目录
        ttk.Checkbutton(frame, text="清理旧构建", variable=self.clean_build).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 数据目录信息
        info_frame = ttk.Frame(frame)
        info_frame.grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Label(info_frame, text="需要包含:", style='Info.TLabel').grid(row=0, column=0, sticky=tk.W)
        ttk.Label(info_frame, text="• ASSET/ 目录", style='Info.TLabel').grid(row=1, column=0, sticky=tk.W)
        ttk.Label(info_frame, text="• data/ 目录", style='Info.TLabel').grid(row=2, column=0, sticky=tk.W)
    
    def create_advanced_options(self, parent):
        """高级选项"""
        frame = ttk.LabelFrame(parent, text="🔧 高级选项", padding="10")
        frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # 隐藏导入
        ttk.Label(frame, text="隐藏导入 (逗号分隔):").grid(row=0, column=0, sticky=tk.W, pady=5)
        hidden_entry = ttk.Entry(frame, textvariable=self.hidden_imports, width=35)
        hidden_entry.grid(row=1, column=0, columnspan=2, pady=5)
        
        # 排除模块
        ttk.Label(frame, text="排除模块 (逗号分隔):").grid(row=2, column=0, sticky=tk.W, pady=5)
        exclude_entry = ttk.Entry(frame, textvariable=self.exclude_modules, width=35)
        exclude_entry.grid(row=3, column=0, columnspan=2, pady=5)
        
        # 帮助信息
        help_frame = ttk.Frame(frame)
        help_frame.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Label(help_frame, text="提示:", font=('微软雅黑', 9, 'bold')).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(help_frame, text="• 默认配置已针对游戏优化", style='Info.TLabel').grid(row=1, column=0, sticky=tk.W)
        ttk.Label(help_frame, text="• 不熟悉请保持默认设置", style='Info.TLabel').grid(row=2, column=0, sticky=tk.W)
        ttk.Label(help_frame, text="• 图标需为 .ico 格式", style='Info.TLabel').grid(row=3, column=0, sticky=tk.W)
    
    def create_presets(self, parent):
        """预设配置"""
        frame = ttk.LabelFrame(parent, text="📋 预设配置", padding="10")
        frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # 预设按钮
        presets = [
            ("🎮 游戏模式", self.preset_game),
            ("📦 便携版", self.preset_portable),
            ("🖥️ 控制台模式", self.preset_console),
            ("⚡ 轻量模式", self.preset_lightweight),
        ]
        
        for i, (text, command) in enumerate(presets):
            ttk.Button(frame, text=text, command=command, width=15).grid(row=0, column=i, padx=5)
        
        ttk.Label(frame, text="选择预设快速配置，或手动调整上方选项", style='Info.TLabel').grid(row=1, column=0, columnspan=4, pady=5)
    
    def create_control_buttons(self, parent):
        """控制按钮"""
        frame = ttk.Frame(parent)
        frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        # 主按钮
        self.pack_button = ttk.Button(frame, text="🚀 开始打包", command=self.start_packing, style='Action.TButton')
        self.pack_button.grid(row=0, column=0, padx=10)
        
        # 停止按钮
        self.stop_button = ttk.Button(frame, text="⏹ 停止", command=self.stop_packing, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=10)
        
        # 清理按钮
        ttk.Button(frame, text="🧹 清理", command=self.clean_build_dir).grid(row=0, column=2, padx=10)
        
        # 打开输出目录
        ttk.Button(frame, text="📂 打开输出", command=self.open_output_dir).grid(row=0, column=3, padx=10)
        
        # 进度条
        self.progress = ttk.Progressbar(frame, mode='indeterminate', length=300)
        self.progress.grid(row=1, column=0, columnspan=4, pady=10)
    
    def create_log_area(self, parent):
        """日志区域"""
        frame = ttk.LabelFrame(parent, text="📝 打包日志", padding="10")
        frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(frame, height=15, width=100, font=('Consolas', 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
    
    # 预设配置方法
    def preset_game(self):
        """游戏模式预设"""
        self.one_file.set(True)
        self.console.set(False)
        self.upx.set(True)
        self.output_name.set("SangoHeroes")
        self.exclude_modules.set("tkinter,PyQt5,wx,scipy,numpy,matplotlib,pandas,tensorflow,torch,sklearn")
        self.log_message("✓ 已加载预设: 游戏模式")
    
    def preset_portable(self):
        """便携版预设"""
        self.one_file.set(False)
        self.console.set(False)
        self.upx.set(False)
        self.output_name.set("SangoHeroes_Portable")
        self.exclude_modules.set("tkinter,PyQt5,wx,scipy,numpy,matplotlib,pandas,tensorflow,torch,sklearn")
        self.log_message("✓ 已加载预设: 便携版（目录模式）")
    
    def preset_console(self):
        """控制台模式预设"""
        self.one_file.set(True)
        self.console.set(True)
        self.upx.set(True)
        self.output_name.set("SangoHeroes_Console")
        self.exclude_modules.set("tkinter,PyQt5,wx,scipy,numpy,matplotlib,pandas,tensorflow,torch,sklearn")
        self.log_message("✓ 已加载预设: 控制台模式")
    
    def preset_lightweight(self):
        """轻量模式预设"""
        self.one_file.set(True)
        self.console.set(False)
        self.upx.set(True)
        self.output_name.set("SangoHeroes_Light")
        # 排除更多模块减小体积
        self.exclude_modules.set("tkinter,PyQt5,wx,scipy,numpy,matplotlib,pandas,tensorflow,torch,sklearn,pkg_resources,jaraco")
        self.log_message("✓ 已加载预设: 轻量模式")
    
    # 文件浏览方法
    def browse_project_path(self):
        """浏览项目路径"""
        path = filedialog.askdirectory(title="选择项目目录")
        if path:
            self.project_path.set(path)
    
    def browse_icon(self):
        """浏览图标文件"""
        path = filedialog.askopenfilename(
            title="选择图标文件",
            filetypes=[("图标文件", "*.ico"), ("PNG图片", "*.png"), ("所有文件", "*.*")]
        )
        if path:
            self.icon_path.set(path)
    
    # 日志方法
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
    
    # 控制方法
    def start_packing(self):
        """开始打包"""
        if self.is_packing:
            messagebox.showwarning("警告", "正在打包中，请稍候...")
            return
        
        # 验证设置
        if not self.validate_settings():
            return
        
        # 开始打包线程
        self.is_packing = True
        self.pack_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress.start()
        
        thread = threading.Thread(target=self.pack_thread)
        thread.daemon = True
        thread.start()
    
    def stop_packing(self):
        """停止打包"""
        if messagebox.askyesno("确认", "确定要停止打包吗？"):
            self.is_packing = False
            self.log_message("⚠ 用户取消打包")
    
    def validate_settings(self):
        """验证设置"""
        # 检查项目路径
        if not os.path.exists(self.project_path.get()):
            messagebox.showerror("错误", "项目路径不存在！")
            return False
        
        # 检查主脚本
        main_script_path = os.path.join(self.project_path.get(), self.main_script.get())
        if not os.path.exists(main_script_path):
            messagebox.showerror("错误", f"主脚本不存在: {self.main_script.get()}")
            return False
        
        # 检查图标
        if self.icon_path.get() and not os.path.exists(self.icon_path.get()):
            messagebox.showerror("错误", f"图标文件不存在: {self.icon_path.get()}")
            return False
        
        # 检查输出名称
        if not self.output_name.get().strip():
            messagebox.showerror("错误", "输出名称不能为空！")
            return False
        
        return True
    
    def pack_thread(self):
        """打包线程"""
        try:
            self.log_message("=" * 60)
            self.log_message("🚀 开始打包...")
            self.log_message(f"📁 项目: {self.project_path.get()}")
            self.log_message(f"📄 主脚本: {self.main_script.get()}")
            self.log_message(f"📦 输出: {self.output_name.get()}")
            
            # 切换到项目目录
            original_dir = os.getcwd()
            os.chdir(self.project_path.get())
            
            # 1. 清理旧构建
            if self.clean_build.get():
                self.log_message("🧹 清理旧构建...")
                if os.path.exists("build"):
                    shutil.rmtree("build")
                if os.path.exists("dist"):
                    shutil.rmtree("dist")
            
            # 2. 自动安装依赖
            if self.auto_install.get():
                self.log_message("📦 检查依赖...")
                self.check_and_install_dependencies()
            
            # 3. 构建 PyInstaller 命令
            cmd = self.build_pyinstaller_command()
            self.log_message(f"⚙️ 执行: {' '.join(cmd[:5])}...")
            
            # 4. 执行打包
            self.log_message("⏳ 正在打包，请稍候...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_message("=" * 60)
                self.log_message("✅ 打包成功！")
                
                # 显示输出信息
                output_dir = os.path.join(self.project_path.get(), "dist")
                exe_path = os.path.join(output_dir, self.output_name.get() + (".exe" if self.one_file.get() else ".exe" + os.sep + self.output_name.get() + ".exe"))
                
                if os.path.exists(exe_path):
                    size = os.path.getsize(exe_path) / (1024 * 1024)
                    self.log_message(f"📍 输出位置: {exe_path}")
                    self.log_message(f"📊 文件大小: {size:.2f} MB")
                    self.log_message("🎉 可以分发了！")
                    
                    # 询问是否打开目录
                    if messagebox.askyesno("成功", "打包完成！是否打开输出目录？"):
                        self.open_output_dir()
                else:
                    self.log_message(f"⚠️ 警告: 未找到输出文件")
                    self.log_message(f"📍 请检查 dist 目录")
            else:
                self.log_message("=" * 60)
                self.log_message("❌ 打包失败！")
                self.log_message("错误信息:")
                for line in result.stderr.split('\n')[-20:]:
                    if line.strip():
                        self.log_message(f"  {line}")
                
                messagebox.showerror("打包失败", "查看日志获取详细信息")
            
            # 恢复原始目录
            os.chdir(original_dir)
            
        except Exception as e:
            self.log_message(f"❌ 错误: {str(e)}")
            import traceback
            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    self.log_message(f"  {line}")
        
        finally:
            # 恢复UI状态
            self.root.after(0, self.pack_complete)
    
    def pack_complete(self):
        """打包完成回调"""
        self.is_packing = False
        self.progress.stop()
        self.pack_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def check_and_install_dependencies(self):
        """检查并安装依赖"""
        required = ['pyinstaller']
        missing = []
        
        for package in required:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing.append(package)
        
        if missing:
            self.log_message(f"📦 需要安装: {', '.join(missing)}")
            cmd = [sys.executable, '-m', 'pip', 'install'] + missing
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                self.log_message("✅ 依赖安装成功")
            else:
                self.log_message("⚠️ 依赖安装失败，继续打包...")
    
    def build_pyinstaller_command(self):
        """构建 PyInstaller 命令"""
        cmd = [sys.executable, '-m', 'PyInstaller']
        
        # 基本选项
        if self.one_file.get():
            cmd.append('--onefile')
        
        cmd.extend(['--name', self.output_name.get()])
        
        # 图标
        if self.icon_path.get():
            cmd.extend(['--icon', self.icon_path.get()])
        
        # 控制台
        if not self.console.get():
            cmd.append('--noconsole')
        
        # UPX
        if self.upx.get():
            cmd.append('--upx-dir=upx')
        else:
            cmd.append('--no-upx')
        
        # 清理
        cmd.append('--noconfirm')
        
        # 添加数据文件
        cmd.extend(['--add-data', 'ASSET' + os.pathsep + 'ASSET'])
        cmd.extend(['--add-data', 'data' + os.pathsep + 'data'])
        
        # 隐藏导入
        hidden_list = [h.strip() for h in self.hidden_imports.get().split(',') if h.strip()]
        for h in hidden_list:
            cmd.extend(['--hidden-import', h])
        
        # 排除模块
        exclude_list = [e.strip() for e in self.exclude_modules.get().split(',') if e.strip()]
        for e in exclude_list:
            cmd.extend(['--exclude-module', e])
        
        # 主脚本
        cmd.append(self.main_script.get())
        
        return cmd
    
    def clean_build_dir(self):
        """清理构建目录"""
        if messagebox.askyesno("确认", "确定要清理 build 和 dist 目录吗？"):
            try:
                if os.path.exists("build"):
                    shutil.rmtree("build")
                    self.log_message("✓ 已清理 build 目录")
                if os.path.exists("dist"):
                    shutil.rmtree("dist")
                    self.log_message("✓ 已清理 dist 目录")
                messagebox.showinfo("完成", "清理完成！")
            except Exception as e:
                messagebox.showerror("错误", f"清理失败: {str(e)}")
    
    def open_output_dir(self):
        """打开输出目录"""
        output_dir = os.path.join(self.project_path.get(), "dist")
        if os.path.exists(output_dir):
            # Windows 打开目录
            os.startfile(output_dir) if sys.platform == 'win32' else os.system(f'xdg-open "{output_dir}"')
        else:
            messagebox.showwarning("警告", "输出目录不存在，请先打包！")


def main():
    """主函数"""
    root = tk.Tk()
    app = PackerGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
