#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 分支标签管理工具 - Plus Pro Max 版
支持：GitHub账户绑定、密钥管理、仓库克隆、自定义目录等高级功能
"""

import os
import sys
import subprocess
import threading
import json
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext, filedialog


class GitHubBranchTool:
    def __init__(self, master):
        self.master = master
        self.master.title("GitHub 分支标签管理工具 - Plus Pro Max")
        self.master.geometry("900x750")
        self.master.configure(bg="#1a1a2e")
        self.master.resizable(True, True)

        # 配置文件路径
        self.config_file = os.path.join(os.path.expanduser("~"), ".github_tool_config.json")
        
        # 状态变量
        self.custom_branch = tk.StringVar(value="main")
        self.custom_tag = tk.StringVar()
        self.tag_message = tk.StringVar()
        self.commit_message = tk.StringVar(value="Update")
        self.include_all_files = tk.BooleanVar(value=True)
        self.push_tags = tk.BooleanVar(value=True)
        self.force_push = tk.BooleanVar(value=False)
        self.github_token = tk.StringVar()
        self.github_user = tk.StringVar()
        self.repo_url = tk.StringVar()
        self.local_path = tk.StringVar(value=os.getcwd())

        # 数据列表
        self.branch_list = []
        self.tag_list = []
        self.push_history = []
        self.repo_list = []

        # 加载配置
        self.load_config()

        # 创建界面
        self.create_widgets()
        self.refresh_all()

    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'github_token' in config:
                        self.github_token.set(config['github_token'])
                    if 'github_user' in config:
                        self.github_user.set(config['github_user'])
                    if 'repo_url' in config:
                        self.repo_url.set(config['repo_url'])
        except:
            pass

    def save_config(self):
        """保存配置文件"""
        config = {
            'github_token': self.github_token.get(),
            'github_user': self.github_user.get(),
            'repo_url': self.repo_url.get()
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")

    def create_widgets(self):
        """创建界面组件"""
        # 顶部状态栏
        status_bar = tk.Frame(self.master, bg="#16213e", height=30)
        status_bar.pack(fill="x")
        status_bar.pack_propagate(False)

        self.status_label = tk.Label(status_bar, text="准备就绪", 
                                     font=("Microsoft YaHei", 10),
                                     bg="#16213e", fg="#00ff00")
        self.status_label.pack(side="left", padx=20)

        self.git_status_label = tk.Label(status_bar, text="", 
                                          font=("Microsoft YaHei", 10),
                                          bg="#16213e", fg="#f39c12")
        self.git_status_label.pack(side="right", padx=20)

        # 主容器 - 使用 Notebook 分页
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # ========== 推送代码页面 ==========
        self.create_push_page()

        # ========== 分支管理页面 ==========
        self.create_branch_page()

        # ========== 标签管理页面 ==========
        self.create_tag_page()

        # ========== 仓库管理页面 ==========
        self.create_repo_page()

        # ========== 设置页面 ==========
        self.create_settings_page()

    def create_push_page(self):
        """创建推送代码页面"""
        push_frame = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(push_frame, text="🚀 推送代码")

        # 左侧配置区
        left_frame = tk.Frame(push_frame, bg="#1a1a2e")
        left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # 分支设置
        branch_frame = tk.LabelFrame(left_frame, text="📁 分支设置",
                                     font=("Microsoft YaHei", 11, "bold"),
                                     bg="#16213e", fg="#f39c12", padx=10, pady=10)
        branch_frame.pack(fill="x", pady=5)

        tk.Label(branch_frame, text="目标分支:", font=("Microsoft YaHei", 10),
                 bg="#16213e", fg="#ffffff").pack(anchor="w")

        branch_entry_frame = tk.Frame(branch_frame, bg="#16213e")
        branch_entry_frame.pack(fill="x", pady=5)

        self.branch_entry = tk.Entry(branch_entry_frame, textvariable=self.custom_branch,
                                     font=("Microsoft YaHei", 12), width=25,
                                     bg="#0f3460", fg="#ffffff", insertbackground="white")
        self.branch_entry.pack(side="left", fill="x", expand=True)

        # 快速选择常用分支
        quick_frame = tk.Frame(branch_frame, bg="#16213e")
        quick_frame.pack(fill="x", pady=5)
        for branch in ["main", "master", "develop", "feature", "cpp-python", "python-only"]:
            tk.Button(quick_frame, text=branch,
                      command=lambda b=branch: self.custom_branch.set(b),
                      bg="#3498db", fg="white", width=8, font=("Microsoft YaHei", 9)).pack(side="left", padx=2)

        # 标签设置
        tag_frame = tk.LabelFrame(left_frame, text="🏷️ 标签设置",
                                   font=("Microsoft YaHei", 11, "bold"),
                                   bg="#16213e", fg="#f39c12", padx=10, pady=10)
        tag_frame.pack(fill="x", pady=5)

        tk.Label(tag_frame, text="标签名称:", font=("Microsoft YaHei", 10),
                 bg="#16213e", fg="#ffffff").pack(anchor="w")

        tag_entry_frame = tk.Frame(tag_frame, bg="#16213e")
        tag_entry_frame.pack(fill="x", pady=3)

        self.tag_entry = tk.Entry(tag_entry_frame, textvariable=self.custom_tag,
                                   font=("Microsoft YaHei", 11), width=20,
                                   bg="#0f3460", fg="#ffffff", insertbackground="white")
        self.tag_entry.pack(side="left", fill="x", expand=True)

        tk.Button(tag_entry_frame, text="清除", command=lambda: self.custom_tag.set(""),
                  bg="#95a5a6", fg="white", width=6).pack(side="left", padx=(5, 0))

        tk.Label(tag_frame, text="标签说明:", font=("Microsoft YaHei", 10),
                 bg="#16213e", fg="#ffffff").pack(anchor="w")
        tk.Entry(tag_frame, textvariable=self.tag_message,
                 font=("Microsoft YaHei", 11), width=35,
                 bg="#0f3460", fg="#ffffff", insertbackground="white").pack(fill="x", pady=3)

        # 预设标签
        preset_frame = tk.Frame(tag_frame, bg="#16213e")
        preset_frame.pack(fill="x", pady=5)
        for preset in ["v1.0", "v1.1", "v2.0", "release", "beta", "alpha"]:
            tk.Button(preset_frame, text=preset,
                      command=lambda p=preset: self.custom_tag.set(p),
                      bg="#27ae60", fg="white", width=6).pack(side="left", padx=2)

        # 提交设置
        commit_frame = tk.LabelFrame(left_frame, text="📝 提交设置",
                                      font=("Microsoft YaHei", 11, "bold"),
                                      bg="#16213e", fg="#f39c12", padx=10, pady=10)
        commit_frame.pack(fill="x", pady=5)

        tk.Label(commit_frame, text="提交信息:", font=("Microsoft YaHei", 10),
                 bg="#16213e", fg="#ffffff").pack(anchor="w")
        tk.Entry(commit_frame, textvariable=self.commit_message,
                 font=("Microsoft YaHei", 11), width=35,
                 bg="#0f3460", fg="#ffffff", insertbackground="white").pack(fill="x", pady=3)

        # 推送选项
        options_frame = tk.LabelFrame(left_frame, text="⚙️ 推送选项",
                                       font=("Microsoft YaHei", 11, "bold"),
                                       bg="#16213e", fg="#f39c12", padx=10, pady=10)
        options_frame.pack(fill="x", pady=5)

        tk.Checkbutton(options_frame, text="推送所有文件",
                      variable=self.include_all_files,
                      font=("Microsoft YaHei", 10), bg="#16213e", fg="#ffffff",
                      selectcolor="#0f3460").pack(anchor="w")
        tk.Checkbutton(options_frame, text="推送标签",
                      variable=self.push_tags,
                      font=("Microsoft YaHei", 10), bg="#16213e", fg="#ffffff",
                      selectcolor="#0f3460").pack(anchor="w")
        tk.Checkbutton(options_frame, text="强制推送 (--force)",
                      variable=self.force_push,
                      font=("Microsoft YaHei", 10), bg="#16213e", fg="#e74c3c",
                      selectcolor="#0f3460").pack(anchor="w")

        # 进度条
        progress_frame = tk.LabelFrame(left_frame, text="📊 推送进度",
                                        font=("Microsoft YaHei", 11, "bold"),
                                        bg="#16213e", fg="#f39c12", padx=10, pady=10)
        progress_frame.pack(fill="x", pady=5)

        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal",
                                            length=350, mode="determinate")
        self.progress_bar.pack(fill="x", pady=5)

        self.progress_label = tk.Label(progress_frame, text="准备就绪",
                                       font=("Microsoft YaHei", 10),
                                       bg="#16213e", fg="#27ae60")
        self.progress_label.pack(anchor="w")

        # 操作按钮
        btn_frame = tk.Frame(left_frame, bg="#1a1a2e")
        btn_frame.pack(fill="x", pady=10)

        self.push_btn = tk.Button(btn_frame, text="🚀 推送代码",
                                   command=self.push_to_github,
                                   bg="#27ae60", fg="white",
                                   font=("Microsoft YaHei", 12, "bold"),
                                   height=2, cursor="hand2")
        self.push_btn.pack(fill="x", pady=2)

        # 右侧信息区
        right_frame = tk.Frame(push_frame, bg="#1a1a2e")
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # 当前状态
        status_frame = tk.LabelFrame(right_frame, text="📈 当前状态",
                                      font=("Microsoft YaHei", 11, "bold"),
                                      bg="#16213e", fg="#f39c12", padx=10, pady=10)
        status_frame.pack(fill="x", pady=5)

        self.status_text = scrolledtext.ScrolledText(status_frame, height=8,
                                                     font=("Consolas", 10),
                                                     bg="#0f3460", fg="#00ff00")
        self.status_text.pack(fill="both", expand=True)

        # 推送历史
        history_frame = tk.LabelFrame(right_frame, text="📜 推送历史",
                                       font=("Microsoft YaHei", 11, "bold"),
                                       bg="#16213e", fg="#f39c12", padx=10, pady=10)
        history_frame.pack(fill="both", expand=True, pady=5)

        self.history_listbox = tk.Listbox(history_frame, font=("Microsoft YaHei", 10),
                                          bg="#0f3460", fg="#ffffff", height=8)
        self.history_listbox.pack(fill="both", expand=True)

    def create_branch_page(self):
        """创建分支管理页面"""
        branch_frame = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(branch_frame, text="🌿 分支管理")

        # 分支列表
        list_frame = tk.Frame(branch_frame, bg="#1a1a2e")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.branch_listbox = tk.Listbox(list_frame, font=("Consolas", 11),
                                          bg="#0f3460", fg="#ffffff", width=70)
        self.branch_listbox.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # 操作按钮
        btn_frame = tk.Frame(list_frame, bg="#1a1a2e")
        btn_frame.pack(side="right", fill="y")

        tk.Button(btn_frame, text="📤 创建分支", command=self.create_branch,
                  bg="#27ae60", fg="white", width=14, font=("Microsoft YaHei", 10)).pack(fill="x", pady=5)
        tk.Button(btn_frame, text="🔄 切换分支", command=self.checkout_branch,
                  bg="#3498db", fg="white", width=14, font=("Microsoft YaHei", 10)).pack(fill="x", pady=5)
        tk.Button(btn_frame, text="🗑️ 删除分支", command=self.delete_branch,
                  bg="#e74c3c", fg="white", width=14, font=("Microsoft YaHei", 10)).pack(fill="x", pady=5)
        tk.Button(btn_frame, text="⬇️ 拉取更新", command=self.pull_branch,
                  bg="#9b59b6", fg="white", width=14, font=("Microsoft YaHei", 10)).pack(fill="x", pady=5)
        tk.Button(btn_frame, text="🔃 刷新列表", command=self.refresh_branches,
                  bg="#7f8c8d", fg="white", width=14, font=("Microsoft YaHei", 10)).pack(fill="x", pady=5)

    def create_tag_page(self):
        """创建标签管理页面"""
        tag_frame = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(tag_frame, text="🏷️ 标签管理")

        # 标签列表
        list_frame = tk.Frame(tag_frame, bg="#1a1a2e")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tag_listbox = tk.Listbox(list_frame, font=("Consolas", 11),
                                       bg="#0f3460", fg="#ffffff", width=70)
        self.tag_listbox.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # 操作按钮
        btn_frame = tk.Frame(list_frame, bg="#1a1a2e")
        btn_frame.pack(side="right", fill="y")

        tk.Button(btn_frame, text="📤 创建标签", command=self.create_tag,
                  bg="#27ae60", fg="white", width=14, font=("Microsoft YaHei", 10)).pack(fill="x", pady=5)
        tk.Button(btn_frame, text="⬆️ 推送标签", command=self.push_tag,
                  bg="#f39c12", fg="white", width=14, font=("Microsoft YaHei", 10)).pack(fill="x", pady=5)
        tk.Button(btn_frame, text="🗑️ 删除标签", command=self.delete_tag,
                  bg="#e74c3c", fg="white", width=14, font=("Microsoft YaHei", 10)).pack(fill="x", pady=5)
        tk.Button(btn_frame, text="🔃 刷新列表", command=self.refresh_tags,
                  bg="#7f8c8d", fg="white", width=14, font=("Microsoft YaHei", 10)).pack(fill="x", pady=5)

    def create_repo_page(self):
        """创建仓库管理页面"""
        repo_frame = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(repo_frame, text="📦 仓库管理")

        # 远程仓库URL
        url_frame = tk.LabelFrame(repo_frame, text="🌐 远程仓库",
                                   font=("Microsoft YaHei", 11, "bold"),
                                   bg="#16213e", fg="#f39c12", padx=10, pady=10)
        url_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(url_frame, text="仓库URL:", font=("Microsoft YaHei", 10),
                 bg="#16213e", fg="#ffffff").pack(anchor="w")
        tk.Entry(url_frame, textvariable=self.repo_url,
                 font=("Microsoft YaHei", 11), width=60,
                 bg="#0f3460", fg="#ffffff", insertbackground="white").pack(fill="x", pady=3)

        # 本地路径选择
        path_frame = tk.LabelFrame(repo_frame, text="📂 本地路径",
                                    font=("Microsoft YaHei", 11, "bold"),
                                    bg="#16213e", fg="#f39c12", padx=10, pady=10)
        path_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(path_frame, text="目标路径:", font=("Microsoft YaHei", 10),
                 bg="#16213e", fg="#ffffff").pack(anchor="w")
        
        path_entry_frame = tk.Frame(path_frame, bg="#16213e")
        path_entry_frame.pack(fill="x", pady=3)
        
        tk.Entry(path_entry_frame, textvariable=self.local_path,
                 font=("Microsoft YaHei", 11), width=50,
                 bg="#0f3460", fg="#ffffff", insertbackground="white").pack(side="left", fill="x", expand=True)
        tk.Button(path_entry_frame, text="浏览", command=self.browse_path,
                  bg="#3498db", fg="white", width=8).pack(side="left", padx=(5, 0))

        # 文件夹名称
        name_frame = tk.LabelFrame(repo_frame, text="📁 新建文件夹",
                                    font=("Microsoft YaHei", 11, "bold"),
                                    bg="#16213e", fg="#f39c12", padx=10, pady=10)
        name_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(name_frame, text="文件夹名称:", font=("Microsoft YaHei", 10),
                 bg="#16213e", fg="#ffffff").pack(anchor="w")
        self.folder_name_entry = tk.Entry(name_frame, font=("Microsoft YaHei", 11), width=30,
                                          bg="#0f3460", fg="#ffffff", insertbackground="white")
        self.folder_name_entry.pack(fill="x", pady=3)
        self.folder_name_entry.insert(0, "my_project")

        # 操作按钮
        btn_frame = tk.Frame(repo_frame, bg="#1a1a2e")
        btn_frame.pack(fill="x", padx=10, pady=10)

        tk.Button(btn_frame, text="⬇️ 克隆仓库", command=self.clone_repo,
                  bg="#27ae60", fg="white", font=("Microsoft YaHei", 11, "bold"),
                  height=2).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(btn_frame, text="🆕 初始化仓库", command=self.init_repo,
                  bg="#3498db", fg="white", font=("Microsoft YaHei", 11, "bold"),
                  height=2).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(btn_frame, text="🔗 添加远程", command=self.add_remote,
                  bg="#f39c12", fg="white", font=("Microsoft YaHei", 11, "bold"),
                  height=2).pack(side="left", fill="x", expand=True, padx=5)

        # 克隆历史
        history_frame = tk.LabelFrame(repo_frame, text="📜 操作日志",
                                       font=("Microsoft YaHei", 11, "bold"),
                                       bg="#16213e", fg="#f39c12", padx=10, pady=10)
        history_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.repo_log = scrolledtext.ScrolledText(history_frame, font=("Consolas", 10),
                                                  bg="#0f3460", fg="#00ff00", height=15)
        self.repo_log.pack(fill="both", expand=True)

    def create_settings_page(self):
        """创建设置页面"""
        settings_frame = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(settings_frame, text="⚙️ 设置")

        # GitHub账户设置
        account_frame = tk.LabelFrame(settings_frame, text="👤 GitHub 账户设置",
                                       font=("Microsoft YaHei", 11, "bold"),
                                       bg="#16213e", fg="#f39c12", padx=10, pady=15)
        account_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(account_frame, text="GitHub用户名:", font=("Microsoft YaHei", 10),
                 bg="#16213e", fg="#ffffff").pack(anchor="w")
        tk.Entry(account_frame, textvariable=self.github_user,
                 font=("Microsoft YaHei", 11), width=40,
                 bg="#0f3460", fg="#ffffff", insertbackground="white").pack(fill="x", pady=3)

        tk.Label(account_frame, text="访问令牌 (Token):", font=("Microsoft YaHei", 10),
                 bg="#16213e", fg="#ffffff").pack(anchor="w")
        token_frame = tk.Frame(account_frame, bg="#16213e")
        token_frame.pack(fill="x", pady=3)
        tk.Entry(token_frame, textvariable=self.github_token,
                 font=("Microsoft YaHei", 11), width=40, show="*",
                 bg="#0f3460", fg="#ffffff", insertbackground="white").pack(side="left", fill="x", expand=True)
        tk.Button(token_frame, text="查看", command=self.toggle_token_visibility,
                  bg="#95a5a6", fg="white", width=8).pack(side="left", padx=(5, 0))

        # 提示信息
        hint_frame = tk.LabelFrame(settings_frame, text="💡 使用提示",
                                    font=("Microsoft YaHei", 11, "bold"),
                                    bg="#16213e", fg="#f39c12", padx=10, pady=10)
        hint_frame.pack(fill="x", padx=10, pady=10)

        hints = [
            "🔑 访问令牌获取方式:",
            "  1. 登录 GitHub → Settings → Developer settings",
            "  2. 选择 Personal access tokens",
            "  3. 点击 Generate new token",
            "  4. 勾选 repo, workflow 权限",
            "  5. 复制生成的令牌",
            "",
            "⚠️ 重要提示:",
            "  - 令牌只显示一次，请妥善保存",
            "  - 令牌具有仓库读写权限，请不要泄露",
            "  - 令牌存储在本地配置文件中",
        ]

        for hint in hints:
            tk.Label(hint_frame, text=hint, font=("Microsoft YaHei", 10),
                     bg="#16213e", fg="#ffffff", justify="left").pack(anchor="w")

        # 操作按钮
        btn_frame = tk.Frame(settings_frame, bg="#1a1a2e")
        btn_frame.pack(fill="x", padx=10, pady=20)

        tk.Button(btn_frame, text="💾 保存配置", command=self.save_config,
                  bg="#27ae60", fg="white", font=("Microsoft YaHei", 11, "bold"),
                  height=2).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(btn_frame, text="🔌 测试连接", command=self.test_connection,
                  bg="#3498db", fg="white", font=("Microsoft YaHei", 11, "bold"),
                  height=2).pack(side="left", fill="x", expand=True, padx=5)

    def toggle_token_visibility(self):
        """切换令牌可见性"""
        pass  # 简化实现

    def browse_path(self):
        """浏览选择路径"""
        path = filedialog.askdirectory()
        if path:
            self.local_path.set(path)

    def run_git_command(self, *args, capture=True, check=True, timeout=60):
        """执行git命令"""
        try:
            if capture:
                result = subprocess.run(
                    ["git"] + list(args),
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=timeout
                )
                if check and result.returncode != 0:
                    raise subprocess.CalledProcessError(
                        result.returncode, list(args), result.stdout, result.stderr
                    )
                return result.stdout.strip(), result.stderr.strip(), result.returncode
            else:
                result = subprocess.run(["git"] + list(args), check=True, timeout=timeout)
                return "", "", 0
        except subprocess.TimeoutExpired:
            raise Exception(f"Git命令超时 ({timeout}秒)")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Git命令执行失败: {e.stderr}")
        except FileNotFoundError:
            raise Exception("Git未安装或不在PATH中")

    def update_status(self):
        """更新状态信息"""
        self.status_text.delete(1.0, tk.END)
        try:
            current_branch = self.run_git_command("rev-parse", "--abbrev-ref", "HEAD")[0]
            remote_info = self.run_git_command("remote", "-v")[0]
            status = self.run_git_command("status", "--porcelain")[0]
            commit = self.run_git_command("log", "--oneline", "-1")[0]

            self.status_text.insert(tk.END, f"当前分支: {current_branch}\n")
            self.status_text.insert(tk.END, f"最近提交: {commit}\n")
            self.status_text.insert(tk.END, f"\n远程仓库:\n{remote_info}\n")
            self.status_text.insert(tk.END, f"\n工作区状态:\n")
            if status:
                self.status_text.insert(tk.END, status)
            else:
                self.status_text.insert(tk.END, "  ✅ 工作区干净")
            
            self.git_status_label.config(text=f"当前分支: {current_branch}")
        except Exception as e:
            self.status_text.insert(tk.END, f"获取状态失败: {str(e)}")
            self.git_status_label.config(text="未检测到Git仓库")

    def refresh_all(self):
        """刷新所有信息"""
        self.refresh_branches()
        self.refresh_tags()
        self.update_status()

    def refresh_branches(self):
        """刷新分支列表"""
        self.branch_listbox.delete(0, tk.END)
        try:
            output, _, _ = self.run_git_command("branch", "-a")
            current = self.run_git_command("rev-parse", "--abbrev-ref", "HEAD")[0]

            local_branches = []
            remote_branches = []

            for line in output.split('\n'):
                line = line.strip()
                if not line:
                    continue
                if line.startswith('*'):
                    line = line[1:].strip()
                    local_branches.append(f"★ {line}")
                elif 'remotes/' in line:
                    remote_branches.append(f"🌐 {line.replace('remotes/', '')}")
                else:
                    local_branches.append(f"  {line}")

            self.branch_listbox.insert(tk.END, "━━━ 本地分支 ━━━")
            for branch in local_branches:
                self.branch_listbox.insert(tk.END, branch)

            if remote_branches:
                self.branch_listbox.insert(tk.END, "")
                self.branch_listbox.insert(tk.END, "━━━ 远程分支 ━━━")
                for branch in remote_branches:
                    self.branch_listbox.insert(tk.END, branch)

        except Exception as e:
            self.branch_listbox.insert(tk.END, f"错误: {str(e)}")

    def refresh_tags(self):
        """刷新标签列表"""
        self.tag_listbox.delete(0, tk.END)
        try:
            output, _, _ = self.run_git_command("tag", "-l")
            if output:
                for tag in output.split('\n'):
                    if tag.strip():
                        self.tag_listbox.insert(tk.END, tag.strip())
            else:
                self.tag_listbox.insert(tk.END, "暂无标签")
        except Exception as e:
            self.tag_listbox.insert(tk.END, f"错误: {str(e)}")

    def push_to_github(self):
        """推送到GitHub"""
        branch = self.custom_branch.get().strip()
        tag = self.custom_tag.get().strip()
        tag_msg = self.tag_message.get().strip() or f"Release {tag}"
        commit_msg = self.commit_message.get().strip() or "Update"

        if not branch:
            messagebox.showwarning("提示", "请输入目标分支")
            return

        self.push_btn.config(state="disabled", text="推送中...")
        self.progress_bar.config(value=0)

        def worker():
            try:
                steps = 10
                step = 0

                step += 1
                self.progress_bar.config(value=int(step/steps*100))
                self.progress_label.config(text="正在检查Git状态...", fg="#3498db")
                self.status_label.config(text="正在检查Git状态...")
                self.master.update()

                remote_output, _, rc = self.run_git_command("remote", "-v")
                if rc != 0 or not remote_output:
                    raise Exception("未配置远程仓库")
                remote_name = remote_output.split()[0]

                if self.include_all_files.get():
                    step += 1
                    self.progress_bar.config(value=int(step/steps*100))
                    self.progress_label.config(text="正在添加文件...", fg="#3498db")
                    self.status_label.config(text="正在添加文件...")
                    self.master.update()
                    self.run_git_command("add", "-A")

                step += 1
                self.progress_bar.config(value=int(step/steps*100))
                self.progress_label.config(text="正在提交...", fg="#3498db")
                self.status_label.config(text="正在提交...")
                self.master.update()
                self.run_git_command("commit", "-m", commit_msg)

                step += 1
                self.progress_bar.config(value=int(step/steps*100))
                self.progress_label.config(text="正在检查分支...", fg="#3498db")
                self.status_label.config(text="正在检查分支...")
                self.master.update()

                branches_output, _, _ = self.run_git_command("branch", "-a")
                local_exists = f"\n{branch}\n" in branches_output or f"* {branch}\n" in branches_output

                if not local_exists:
                    self.progress_label.config(text=f"分支 {branch} 不存在，正在创建...", fg="#f39c12")
                    self.status_label.config(text=f"正在创建分支 {branch}...")
                    self.master.update()
                    self.run_git_command("checkout", "-b", branch)
                    step += 1
                    self.progress_bar.config(value=int(step/steps*100))

                step += 1
                self.progress_bar.config(value=int(step/steps*100))
                self.progress_label.config(text="正在推送代码...", fg="#3498db")
                self.status_label.config(text="正在推送代码...")
                self.master.update()

                push_cmd = ["push", "-u", remote_name, branch]
                if self.force_push.get():
                    push_cmd.append("--force")
                self.run_git_command(*push_cmd)

                if tag and self.push_tags.get():
                    step += 1
                    self.progress_bar.config(value=int(step/steps*100))
                    self.progress_label.config(text=f"正在创建标签 {tag}...", fg="#3498db")
                    self.status_label.config(text=f"正在创建标签 {tag}...")
                    self.master.update()

                    tags_output, _, _ = self.run_git_command("tag", "-l")
                    if tag in tags_output:
                        if messagebox.askyesno("确认", f"标签 '{tag}' 已存在，是否覆盖?"):
                            self.run_git_command("tag", "-d", tag)
                        else:
                            raise Exception(f"标签 '{tag}' 已存在")

                    self.run_git_command("tag", "-a", tag, "-m", tag_msg)
                    self.run_git_command("push", remote_name, "tag", tag)

                step += 1
                self.progress_bar.config(value=100)
                self.progress_label.config(text="✅ 推送完成!", fg="#27ae60")
                self.status_label.config(text="推送完成")
                self.master.update()

                history_entry = f"{branch} | {tag if tag else '无标签'} | {commit_msg}"
                self.push_history.insert(0, history_entry)
                if len(self.push_history) > 10:
                    self.push_history.pop()

                self.history_listbox.delete(0, tk.END)
                for entry in self.push_history:
                    self.history_listbox.insert(tk.END, entry)

                messagebox.showinfo("成功", f"✅ 推送成功!\n\n分支: {branch}\n标签: {tag or '无'}\n提交: {commit_msg}")

            except Exception as e:
                self.progress_label.config(text=f"❌ {str(e)}", fg="#e74c3c")
                self.status_label.config(text="推送失败")
                messagebox.showerror("错误", f"推送失败:\n{str(e)}")
            finally:
                self.push_btn.config(state="normal", text="🚀 推送代码")
                self.update_status()
                self.refresh_all()

        threading.Thread(target=worker, daemon=True).start()

    def create_branch(self):
        """创建分支"""
        dialog = tk.Toplevel(self.master)
        dialog.title("创建分支")
        dialog.geometry("450x300")
        dialog.configure(bg="#1a1a2e")
        dialog.transient(self.master)
        dialog.grab_set()

        tk.Label(dialog, text="📁 分支名称:", font=("Microsoft YaHei", 11),
                 bg="#1a1a2e", fg="#ffffff").pack(pady=10)

        branch_entry = tk.Entry(dialog, font=("Microsoft YaHei", 12), width=30,
                                bg="#0f3460", fg="#ffffff", insertbackground="white")
        branch_entry.pack(pady=5)
        branch_entry.focus()

        # 本地路径选择
        tk.Label(dialog, text="📂 本地目录 (可选):", font=("Microsoft YaHei", 11),
                 bg="#1a1a2e", fg="#ffffff").pack(pady=(10, 0))
        
        path_frame = tk.Frame(dialog, bg="#1a1a2e")
        path_frame.pack(fill="x", padx=20, pady=5)
        
        path_var = tk.StringVar(value=os.getcwd())
        tk.Entry(path_frame, textvariable=path_var,
                 font=("Microsoft YaHei", 11), width=35,
                 bg="#0f3460", fg="#ffffff", insertbackground="white").pack(side="left", fill="x", expand=True)
        tk.Button(path_frame, text="浏览", command=lambda: path_var.set(filedialog.askdirectory()),
                  bg="#3498db", fg="white", width=8).pack(side="left", padx=(5, 0))

        push_to_remote = tk.BooleanVar(value=True)
        tk.Checkbutton(dialog, text="☑️ 同时推送到远程",
                      variable=push_to_remote,
                      font=("Microsoft YaHei", 10), bg="#1a1a2e", fg="#ffffff",
                      selectcolor="#0f3460").pack(pady=5)

        def do_create():
            name = branch_entry.get().strip()
            if not name:
                messagebox.showwarning("提示", "请输入分支名称")
                return

            try:
                remote_output, _, _ = self.run_git_command("remote", "-v")
                remote_name = remote_output.split()[0] if remote_output else "origin"

                self.run_git_command("checkout", "-b", name)

                if push_to_remote.get():
                    self.run_git_command("push", "-u", remote_name, name)

                messagebox.showinfo("成功", f"分支 '{name}' 创建成功!")
                dialog.destroy()
                self.custom_branch.set(name)
                self.refresh_branches()
            except Exception as e:
                messagebox.showerror("错误", str(e))

        btn_frame = tk.Frame(dialog, bg="#1a1a2e")
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="创建", command=do_create,
                  bg="#27ae60", fg="white", width=12, font=("Microsoft YaHei", 10)).pack(side="left", padx=5)
        tk.Button(btn_frame, text="取消", command=dialog.destroy,
                  bg="#95a5a6", fg="white", width=12, font=("Microsoft YaHei", 10)).pack(side="left", padx=5)

        dialog.bind("<Return>", lambda e: do_create())

    def checkout_branch(self):
        """切换分支"""
        selection = self.branch_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个分支")
            return

        content = self.branch_listbox.get(selection[0])
        branch = content.replace("★", "").replace("🌐", "").replace(" ", "").strip()

        if "/" in branch:
            branch = branch.split('/')[-1]

        try:
            self.run_git_command("checkout", branch)
            messagebox.showinfo("成功", f"已切换到分支: {branch}")
            
            self.custom_branch.set(branch)
            
            self.refresh_all()
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def delete_branch(self):
        """删除分支"""
        selection = self.branch_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个分支")
            return

        content = self.branch_listbox.get(selection[0])
        branch = content.replace("★", "").replace("🌐", "").replace(" ", "").strip()

        if "/" in branch:
            branch = branch.split('/')[-1]

        if messagebox.askyesno("确认", f"确定要删除分支 '{branch}' 吗?"):
            try:
                self.run_git_command("branch", "-D", branch)
                messagebox.showinfo("成功", f"分支 '{branch}' 已删除")
                self.refresh_branches()
            except Exception as e:
                messagebox.showerror("错误", str(e))

    def pull_branch(self):
        """拉取分支更新"""
        try:
            self.status_label.config(text="正在拉取更新...")
            self.master.update()

            remote_output, _, _ = self.run_git_command("remote", "-v")
            remote_name = remote_output.split()[0] if remote_output else "origin"

            current_branch = self.run_git_command("rev-parse", "--abbrev-ref", "HEAD")[0]
            self.run_git_command("pull", remote_name, current_branch)

            self.status_label.config(text="拉取完成")
            messagebox.showinfo("成功", "拉取更新成功!")
            self.refresh_all()
        except Exception as e:
            self.status_label.config(text="拉取失败")
            messagebox.showerror("错误", str(e))

    def create_tag(self):
        """创建标签"""
        dialog = tk.Toplevel(self.master)
        dialog.title("创建标签")
        dialog.geometry("400x220")
        dialog.configure(bg="#1a1a2e")
        dialog.transient(self.master)
        dialog.grab_set()

        tk.Label(dialog, text="🏷️ 标签名称:", font=("Microsoft YaHei", 11),
                 bg="#1a1a2e", fg="#ffffff").pack(pady=10)

        tag_entry = tk.Entry(dialog, font=("Microsoft YaHei", 12), width=30,
                             bg="#0f3460", fg="#ffffff", insertbackground="white")
        tag_entry.pack(pady=5)
        tag_entry.focus()

        tk.Label(dialog, text="📝 标签说明:", font=("Microsoft YaHei", 11),
                 bg="#1a1a2e", fg="#ffffff").pack(pady=(10, 0))

        msg_entry = tk.Entry(dialog, font=("Microsoft YaHei", 10), width=40,
                             bg="#0f3460", fg="#ffffff", insertbackground="white")
        msg_entry.pack(pady=5)

        def do_create():
            name = tag_entry.get().strip()
            msg = msg_entry.get().strip() or f"Release {name}"

            if not name:
                messagebox.showwarning("提示", "请输入标签名称")
                return

            try:
                tags_output, _, _ = self.run_git_command("tag", "-l")
                if name in tags_output:
                    if messagebox.askyesno("确认", f"标签 '{name}' 已存在，是否覆盖?"):
                        self.run_git_command("tag", "-d", name)
                    else:
                        return

                self.run_git_command("tag", "-a", name, "-m", msg)
                messagebox.showinfo("成功", f"标签 '{name}' 创建成功!")
                dialog.destroy()
                self.refresh_tags()
            except Exception as e:
                messagebox.showerror("错误", str(e))

        btn_frame = tk.Frame(dialog, bg="#1a1a2e")
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="创建", command=do_create,
                  bg="#27ae60", fg="white", width=12, font=("Microsoft YaHei", 10)).pack(side="left", padx=5)
        tk.Button(btn_frame, text="取消", command=dialog.destroy,
                  bg="#95a5a6", fg="white", width=12, font=("Microsoft YaHei", 10)).pack(side="left", padx=5)

    def push_tag(self):
        """推送标签"""
        selection = self.tag_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个标签")
            return

        tag = self.tag_listbox.get(selection[0])

        try:
            remote_output, _, _ = self.run_git_command("remote", "-v")
            remote_name = remote_output.split()[0] if remote_output else "origin"

            self.run_git_command("push", remote_name, "tag", tag)
            messagebox.showinfo("成功", f"标签 '{tag}' 推送成功!")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def delete_tag(self):
        """删除标签"""
        selection = self.tag_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个标签")
            return

        tag = self.tag_listbox.get(selection[0])

        if messagebox.askyesno("确认", f"确定要删除标签 '{tag}' 吗?"):
            try:
                self.run_git_command("tag", "-d", tag)
                messagebox.showinfo("成功", f"标签 '{tag}' 已删除")
                self.refresh_tags()
            except Exception as e:
                messagebox.showerror("错误", str(e))

    def clone_repo(self):
        """克隆仓库"""
        url = self.repo_url.get().strip()
        local_path = self.local_path.get().strip()
        folder_name = self.folder_name_entry.get().strip()

        if not url:
            messagebox.showwarning("提示", "请输入仓库URL")
            return

        if not local_path:
            messagebox.showwarning("提示", "请选择本地路径")
            return

        if not folder_name:
            messagebox.showwarning("提示", "请输入文件夹名称")
            return

        full_path = os.path.join(local_path, folder_name)

        if os.path.exists(full_path):
            if not messagebox.askyesno("确认", f"文件夹 '{full_path}' 已存在，是否覆盖?"):
                return

        def worker():
            try:
                self.status_label.config(text="正在克隆仓库...")
                self.repo_log.insert(tk.END, f"开始克隆仓库: {url}\n")
                self.repo_log.insert(tk.END, f"目标路径: {full_path}\n")
                self.master.update()

                # 使用token构建认证URL
                token = self.github_token.get()
                if token and url.startswith("https://"):
                    auth_url = url.replace("https://", f"https://{token}@")
                else:
                    auth_url = url

                self.run_git_command("clone", auth_url, full_path)

                self.repo_log.insert(tk.END, "✅ 克隆成功!\n\n")
                self.status_label.config(text="克隆完成")
                messagebox.showinfo("成功", f"仓库克隆成功!\n\n路径: {full_path}")
            except Exception as e:
                self.repo_log.insert(tk.END, f"❌ 克隆失败: {str(e)}\n\n")
                self.status_label.config(text="克隆失败")
                messagebox.showerror("错误", f"克隆失败:\n{str(e)}")

        threading.Thread(target=worker, daemon=True).start()

    def init_repo(self):
        """初始化仓库"""
        local_path = self.local_path.get().strip()
        folder_name = self.folder_name_entry.get().strip()

        if not local_path:
            messagebox.showwarning("提示", "请选择本地路径")
            return

        if not folder_name:
            messagebox.showwarning("提示", "请输入文件夹名称")
            return

        full_path = os.path.join(local_path, folder_name)

        if os.path.exists(full_path):
            if not messagebox.askyesno("确认", f"文件夹 '{full_path}' 已存在，是否继续?"):
                return

        def worker():
            try:
                self.status_label.config(text="正在初始化仓库...")
                self.repo_log.insert(tk.END, f"初始化仓库: {full_path}\n")
                self.master.update()

                os.makedirs(full_path, exist_ok=True)
                
                original_cwd = os.getcwd()
                os.chdir(full_path)
                
                self.run_git_command("init")
                self.run_git_command("config", "user.name", self.github_user.get() or "User")
                self.run_git_command("config", "user.email", "user@example.com")
                
                os.chdir(original_cwd)

                self.repo_log.insert(tk.END, "✅ 初始化成功!\n\n")
                self.status_label.config(text="初始化完成")
                messagebox.showinfo("成功", f"仓库初始化成功!\n\n路径: {full_path}")
            except Exception as e:
                self.repo_log.insert(tk.END, f"❌ 初始化失败: {str(e)}\n\n")
                self.status_label.config(text="初始化失败")
                messagebox.showerror("错误", f"初始化失败:\n{str(e)}")

        threading.Thread(target=worker, daemon=True).start()

    def add_remote(self):
        """添加远程仓库"""
        url = self.repo_url.get().strip()
        
        if not url:
            messagebox.showwarning("提示", "请输入仓库URL")
            return

        try:
            self.run_git_command("remote", "add", "origin", url)
            self.repo_log.insert(tk.END, f"✅ 添加远程仓库: {url}\n\n")
            messagebox.showinfo("成功", "远程仓库添加成功!")
            self.refresh_all()
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def test_connection(self):
        """测试GitHub连接"""
        token = self.github_token.get()
        user = self.github_user.get()

        if not token:
            messagebox.showwarning("提示", "请先输入访问令牌")
            return

        self.status_label.config(text="正在测试连接...")
        self.master.update()

        try:
            # 简单测试token是否有效
            result = subprocess.run(
                ["git", "ls-remote", "--heads", "https://github.com"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                messagebox.showinfo("成功", "✅ GitHub连接测试成功!\n\n令牌有效，网络正常")
                self.status_label.config(text="连接测试成功")
            else:
                messagebox.showwarning("警告", "⚠️ 连接可能有问题，请检查网络")
                self.status_label.config(text="连接测试完成")
        except Exception as e:
            messagebox.showerror("错误", f"测试失败: {str(e)}")
            self.status_label.config(text="连接测试失败")


def main():
    """主函数"""
    root = tk.Tk()
    app = GitHubBranchTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
