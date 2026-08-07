#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 推送工具 - GUI 版
功能：配置仓库、填写 commit 记录、一键推送到 GitHub
安全：Token 以掩码输入，可选保存到本地配置文件（base64 编码，非加密）
"""

import os
import sys
import json
import base64
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog


# ─── 配置文件路径 ───
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".sanguo_git_tool.json")


class GitPushTool:
    """GitHub 推送 GUI 工具"""

    def __init__(self, master):
        self.master = master
        self.master.title("GitHub 推送工具")
        self.master.geometry("780x720")
        self.master.configure(bg="#1e1e2e")
        self.master.minsize(680, 640)

        # ── 变量 ──
        self.project_dir = tk.StringVar(value=os.getcwd())
        self.repo_url = tk.StringVar()
        self.github_user = tk.StringVar()
        self.github_token = tk.StringVar()
        self.branch_name = tk.StringVar(value="main")
        self.commit_msg = tk.StringVar()
        self.commit_detail = tk.StringVar()
        self.save_token = tk.BooleanVar(value=False)
        self.is_pushing = False
        self.current_branch = tk.StringVar(value="")
        self.new_branch_name = tk.StringVar()

        self.load_config()
        self.build_ui()
        self.auto_detect_repo()

    # ────────────────────── UI 构建 ──────────────────────

    def build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#1e1e2e")
        style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4",
                         font=("Microsoft YaHei", 10))
        style.configure("TEntry", fieldbackground="#313244", foreground="#cdd6f4")
        style.configure("TButton", background="#45475a", foreground="#cdd6f4",
                         font=("Microsoft YaHei", 10), padding=6)
        style.map("TButton",
                  background=[("active", "#585b70")],
                  foreground=[("active", "#cdd6f4")])
        style.configure("Gold.TButton", background="#a3992f", foreground="#1e1e2e",
                         font=("Microsoft YaHei", 11, "bold"), padding=10)
        style.map("Gold.TButton",
                  background=[("active", "#d4af37")])
        style.configure("TLabelframe", background="#1e1e2e", foreground="#89b4fa",
                         bordercolor="#45475a")
        style.configure("TLabelframe.Label", background="#1e1e2e",
                         foreground="#89b4fa", font=("Microsoft YaHei", 11, "bold"))

        # 主滚动容器
        canvas = tk.Canvas(self.master, bg="#1e1e2e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.master, orient="vertical", command=canvas.yview)
        self.main_frame = ttk.Frame(canvas)
        self.main_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 鼠标滚轮支持
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self._section_project()
        self._section_repo()
        self._section_branches()
        self._section_commit()
        self._section_actions()
        self._section_log()

    def _section_project(self):
        frame = ttk.LabelFrame(self.main_frame, text="  项目目录  ", padding=12)
        frame.pack(fill="x", padx=16, pady=(16, 8))

        row = ttk.Frame(frame)
        row.pack(fill="x")
        ttk.Entry(row, textvariable=self.project_dir).pack(
            side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(row, text="浏览…", command=self.browse_dir).pack(side="left")
        ttk.Button(row, text="检测Git", command=self.auto_detect_repo).pack(
            side="left", padx=(4, 0))

    def _section_repo(self):
        frame = ttk.LabelFrame(self.main_frame, text="  GitHub 仓库配置  ", padding=12)
        frame.pack(fill="x", padx=16, pady=8)

        # 仓库地址
        ttk.Label(frame, text="仓库地址:").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.repo_url, width=52).grid(
            row=0, column=1, columnspan=2, sticky="we", pady=4, padx=8)
        ttk.Label(frame, text="(如: https://github.com/user/repo.git)",
                  foreground="#6c7086").grid(row=1, column=1, sticky="w", padx=8)

        # 用户名
        ttk.Label(frame, text="GitHub 用户名:").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.github_user, width=30).grid(
            row=2, column=1, sticky="w", pady=4, padx=8)

        # Token
        ttk.Label(frame, text="Personal Token:").grid(row=3, column=0, sticky="w", pady=4)
        self.token_entry = tk.Entry(frame, textvariable=self.github_token, width=52,
                                     show="*", bg="#313244", fg="#cdd6f4",
                                     insertbackground="#cdd6f4", relief="solid", bd=1)
        self.token_entry.grid(row=3, column=1, columnspan=2,
                               sticky="we", pady=4, padx=8)

        # Token 可见切换 + 保存选项
        btn_row = ttk.Frame(frame)
        btn_row.grid(row=4, column=1, columnspan=2, sticky="w", padx=8, pady=(2, 0))
        self.token_visible = False
        self.btn_toggle_vis = ttk.Button(btn_row, text="显示", width=6,
                                          command=self.toggle_token_vis)
        self.btn_toggle_vis.pack(side="left")
        ttk.Checkbutton(btn_row, text="保存到本地配置（base64 编码，非加密）",
                        variable=self.save_token).pack(side="left", padx=12)

        ttk.Label(frame, text="⚠ Token 仅在本机保存，请勿提交到仓库",
                  foreground="#f38ba8").grid(row=5, column=1, sticky="w", padx=8, pady=(2, 0))

        # 分支
        ttk.Label(frame, text="推送分支:").grid(row=6, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.branch_name, width=20).grid(
            row=6, column=1, sticky="w", pady=4, padx=8)

        frame.columnconfigure(1, weight=1)

    def _section_branches(self):
        frame = ttk.LabelFrame(self.main_frame, text="  分支管理  ", padding=12)
        frame.pack(fill="x", padx=16, pady=8)

        # 当前分支显示
        top_row = ttk.Frame(frame)
        top_row.pack(fill="x", pady=(0, 6))
        ttk.Label(top_row, text="当前分支:").pack(side="left")
        self.lbl_current_branch = ttk.Label(top_row, text="(未知)",
                                             foreground="#f9e2af",
                                             font=("Microsoft YaHei", 10, "bold"))
        self.lbl_current_branch.pack(side="left", padx=8)
        ttk.Button(top_row, text="🔄 刷新分支", command=self.refresh_branches).pack(side="right")

        # 分支列表
        list_row = ttk.Frame(frame)
        list_row.pack(fill="x")
        ttk.Label(list_row, text="本地分支:").pack(anchor="w")

        tree_frame = ttk.Frame(list_row)
        tree_frame.pack(fill="x")

        self.branch_tree = ttk.Treeview(tree_frame, columns=("info",), height=5,
                                         show="tree headings")
        self.branch_tree.heading("#0", text="分支名")
        self.branch_tree.heading("info", text="最后提交信息")
        self.branch_tree.column("#0", width=180)
        self.branch_tree.column("info", width=400)
        self.branch_tree.pack(side="left", fill="x", expand=True)

        tree_sb = ttk.Scrollbar(tree_frame, orient="vertical",
                                 command=self.branch_tree.yview)
        tree_sb.pack(side="right", fill="y")
        self.branch_tree.configure(yscrollcommand=tree_sb.set)

        # 双击切换分支
        self.branch_tree.bind("<Double-1>", lambda e: self.switch_branch())

        # 分支操作按钮
        btn_row = ttk.Frame(frame)
        btn_row.pack(fill="x", pady=(6, 0))

        ttk.Label(btn_row, text="新分支名:").pack(side="left")
        ttk.Entry(btn_row, textvariable=self.new_branch_name, width=18).pack(
            side="left", padx=4)
        ttk.Button(btn_row, text="➕ 新建分支", command=self.create_branch).pack(
            side="left", padx=4)
        ttk.Button(btn_row, text="🔄 切换到此分支", command=self.switch_branch).pack(
            side="left", padx=4)
        ttk.Button(btn_row, text="🗑 删除分支", command=self.delete_branch).pack(
            side="left", padx=4)
        ttk.Button(btn_row, text="📋 查看远程分支", command=self.refresh_remote_branches).pack(
            side="left", padx=4)

    def _section_commit(self):
        frame = ttk.LabelFrame(self.main_frame, text="  提交记录 (Commit Message)  ", padding=12)
        frame.pack(fill="x", padx=16, pady=8)

        ttk.Label(frame, text="标题:").pack(anchor="w")
        ttk.Entry(frame, textvariable=self.commit_msg, width=70).pack(
            fill="x", pady=(0, 8))

        ttk.Label(frame, text="详细描述 (可选):").pack(anchor="w")
        self.detail_text = scrolledtext.ScrolledText(
            frame, height=4, width=70, bg="#313244", fg="#cdd6f4",
            insertbackground="#cdd6f4", relief="solid", bd=1,
            font=("Microsoft YaHei", 10))
        self.detail_text.pack(fill="x", pady=(0, 8))

        # 快捷模板
        tmpl_row = ttk.Frame(frame)
        tmpl_row.pack(fill="x")
        ttk.Label(tmpl_row, text="快捷模板:").pack(side="left")
        for tag, text in [("✨新功能", "feat: 添加"),
                          ("🐛修复", "fix: 修复"),
                          ("📝文档", "docs: 更新"),
                          ("♻重构", "refactor: 重构"),
                          ("🎨样式", "style: 调整")]:
            ttk.Button(tmpl_row, text=tag, width=8,
                       command=lambda t=text: self.use_template(t)).pack(
                side="left", padx=2)

    def _section_actions(self):
        frame = ttk.LabelFrame(self.main_frame, text="  操作  ", padding=12)
        frame.pack(fill="x", padx=16, pady=8)

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill="x")

        self.btn_push = ttk.Button(btn_row, text="🚀 一键推送", style="Gold.TButton",
                                    command=self.do_push)
        self.btn_push.pack(side="left", padx=(0, 8))

        ttk.Button(btn_row, text="仅提交 (commit)",
                   command=self.do_commit_only).pack(side="left", padx=4)
        ttk.Button(btn_row, text="查看状态",
                   command=self.do_status).pack(side="left", padx=4)
        ttk.Button(btn_row, text="⬇ 拉取更新",
                   command=self.do_pull).pack(side="left", padx=4)
        ttk.Button(btn_row, text="📋 提交历史",
                   command=self.do_log).pack(side="left", padx=4)
        ttk.Button(btn_row, text="🔍 查看差异",
                   command=self.do_diff).pack(side="left", padx=4)
        ttk.Button(btn_row, text="保存配置",
                   command=self.save_config).pack(side="left", padx=4)
        ttk.Button(btn_row, text="检查 .gitignore",
                   command=self.check_gitignore).pack(side="left", padx=4)

    def _section_log(self):
        frame = ttk.LabelFrame(self.main_frame, text="  执行日志  ", padding=8)
        frame.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        self.log_text = scrolledtext.ScrolledText(
            frame, height=12, bg="#11111b", fg="#a6e3a1",
            insertbackground="#cdd6f4", relief="solid", bd=1,
            font=("Consolas", 10), wrap="word")
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")

    # ────────────────────── 功能方法 ──────────────────────

    def log(self, msg, level="INFO"):
        """写入日志"""
        self.log_text.configure(state="normal")
        colors = {
            "INFO": "#a6e3a1",
            "WARN": "#f9e2af",
            "ERROR": "#f38ba8",
            "CMD": "#89b4fa",
        }
        self.log_text.insert("end", f"[{level}] {msg}\n", level)
        self.log_text.tag_config(level, foreground=colors.get(level, "#cdd6f4"))
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.master.update_idletasks()

    def browse_dir(self):
        d = filedialog.askdirectory(initialdir=self.project_dir.get())
        if d:
            self.project_dir.set(d)
            self.auto_detect_repo()

    def toggle_token_vis(self):
        self.token_visible = not self.token_visible
        self.token_entry.configure(show="" if self.token_visible else "*")
        self.btn_toggle_vis.configure(text="隐藏" if self.token_visible else "显示")

    def use_template(self, prefix):
        self.commit_msg.set(prefix)

    # ────────────────────── 分支管理 ──────────────────────

    def refresh_branches(self):
        """刷新本地分支列表"""
        proj = self.project_dir.get()
        if not os.path.isdir(os.path.join(proj, ".git")):
            self.log("不是 git 仓库，无法刷新分支", "WARN")
            return

        # 清空列表
        for item in self.branch_tree.get_children():
            self.branch_tree.delete(item)

        # 获取当前分支
        current = self._git(proj, ["rev-parse", "--abbrev-ref", "HEAD"]).strip()
        self.current_branch.set(current)
        self.lbl_current_branch.configure(text=current if current else "(未知)")
        if current:
            self.branch_name.set(current)

        # 获取本地分支列表 + 每个分支最后提交信息
        branches_out = self._git(proj, ["for-each-ref", "--format=%(refname:short)|||%(objectname:short)|||%(subject)", "refs/heads/"])
        if branches_out:
            for line in branches_out.strip().split("\n"):
                parts = line.split("|||", 2)
                if len(parts) >= 3:
                    name, short_hash, subject = parts[0], parts[1], parts[2]
                elif len(parts) == 2:
                    name, short_hash, subject = parts[0], parts[1], ""
                else:
                    name, short_hash, subject = line, "", ""
                display = name
                if name == current:
                    display = f"★ {name}"
                info_text = f"{short_hash} {subject}" if short_hash else ""
                self.branch_tree.insert("", "end", text=display, values=(info_text,))

        self.log(f"已加载本地分支（当前: {current}）")

    def refresh_remote_branches(self):
        """查看远程分支"""
        proj = self.project_dir.get()
        self.log("── 远程分支列表 ──")
        ok, out = self._git_live(proj, ["branch", "-r"])
        if ok:
            self.log("远程分支查询完成")

    def create_branch(self):
        """新建分支"""
        proj = self.project_dir.get()
        name = self.new_branch_name.get().strip()
        if not name:
            messagebox.showwarning("提示", "请输入新分支名")
            return

        self.log(f"── 创建分支: {name} ──")
        ok, _ = self._git_live(proj, ["checkout", "-b", name])
        if ok:
            self.log(f"分支 {name} 创建成功并已切换")
            self.new_branch_name.set("")
            self.refresh_branches()
        else:
            self.log(f"创建分支 {name} 失败", "ERROR")

    def switch_branch(self):
        """切换到选中的分支"""
        proj = self.project_dir.get()
        sel = self.branch_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先在列表中选择一个分支")
            return

        item = sel[0]
        branch_text = self.branch_tree.item(item, "text")
        # 去掉 ★ 标记
        branch_name = branch_text.replace("★ ", "").strip()

        if branch_name == self.current_branch.get():
            self.log(f"已经在分支 {branch_name} 上了")
            return

        self.log(f"── 切换到分支: {branch_name} ──")
        ok, _ = self._git_live(proj, ["checkout", branch_name])
        if ok:
            self.log(f"已切换到 {branch_name}")
            self.refresh_branches()
        else:
            self.log(f"切换分支失败，可能有未提交的变更", "ERROR")

    def delete_branch(self):
        """删除选中的分支"""
        proj = self.project_dir.get()
        sel = self.branch_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先在列表中选择一个分支")
            return

        item = sel[0]
        branch_text = self.branch_tree.item(item, "text")
        branch_name = branch_text.replace("★ ", "").strip()

        if branch_name == self.current_branch.get():
            messagebox.showerror("错误", "不能删除当前所在分支！请先切换到其他分支")
            return

        if not messagebox.askyesno("确认", f"确定删除分支 '{branch_name}' 吗？\n此操作不可撤销！"):
            return

        self.log(f"── 删除分支: {branch_name} ──")
        ok, _ = self._git_live(proj, ["branch", "-d", branch_name])
        if ok:
            self.log(f"分支 {branch_name} 已删除")
            self.refresh_branches()
        else:
            self.log(f"删除分支失败，可能需要 -D 强制删除", "ERROR")

    # ────────────────────── 更多操作 ──────────────────────

    def do_pull(self):
        """拉取远程更新"""
        proj = self.project_dir.get()
        branch = self.branch_name.get().strip()
        self.log(f"── 拉取远程更新 ({branch}) ──")
        ok, _ = self._git_live(proj, ["pull", "origin", branch])
        if ok:
            self.log("拉取完成")
            self.refresh_branches()

    def do_log(self):
        """查看提交历史"""
        proj = self.project_dir.get()
        self.log("── 提交历史 (最近20条) ──")
        ok, _ = self._git_live(proj, ["log", "--oneline", "--graph", "-20"])
        if ok:
            self.log("── 历史查询完成 ──")

    def do_diff(self):
        """查看未提交的差异"""
        proj = self.project_dir.get()
        self.log("── 未暂存的差异 ──")
        ok, _ = self._git_live(proj, ["diff"])
        self.log("── 未暂存差异结束 ──")
        self.log("── 已暂存未提交的差异 ──")
        ok2, _ = self._git_live(proj, ["diff", "--cached"])
        self.log("── 差异查看完成 ──")

    def auto_detect_repo(self):
        """自动检测 git 仓库信息"""
        proj = self.project_dir.get()
        if not os.path.isdir(proj):
            return
        git_dir = os.path.join(proj, ".git")
        if not os.path.isdir(git_dir):
            self.log("当前目录不是 git 仓库（无 .git 文件夹）", "WARN")
            return

        # 获取远程地址
        url = self._git(proj, ["config", "--get", "remote.origin.url"])
        if url:
            self.repo_url.set(url.strip())
            # 从 URL 提取用户名
            # https://github.com/user/repo.git  或  git@github.com:user/repo.git
            if "github.com" in url:
                parts = url.strip().replace(":", "/").split("/")
                if len(parts) >= 2:
                    self.github_user.set(parts[-2])
            self.log(f"检测到远程仓库: {url.strip()}")

        # 获取当前分支
        branch = self._git(proj, ["rev-parse", "--abbrev-ref", "HEAD"])
        if branch:
            self.branch_name.set(branch.strip())
            self.log(f"当前分支: {branch.strip()}")

        # 获取状态摘要
        status = self._git(proj, ["status", "--short"])
        if status:
            lines = [l for l in status.strip().split("\n") if l]
            self.log(f"工作区有 {len(lines)} 个变更")
        else:
            self.log("工作区干净，无变更")

        # 刷新分支列表
        self.refresh_branches()

    def _git(self, cwd, args):
        """执行 git 命令并返回输出字符串，失败返回空字符串"""
        try:
            r = subprocess.run(
                ["git"] + args,
                cwd=cwd, capture_output=True, text=True, timeout=30,
                encoding="utf-8", errors="replace"
            )
            if r.returncode == 0:
                return r.stdout
            return ""
        except Exception:
            return ""

    def _git_live(self, cwd, args, env=None):
        """执行 git 命令并实时输出到日志，返回 (成功?, 输出)"""
        cmd_str = "git " + " ".join(args)
        # 对包含 token 的 URL 做脱敏显示
        safe_cmd = cmd_str.replace(self.github_token.get(), "***") if self.github_token.get() else cmd_str
        self.log(f"$ {safe_cmd}", "CMD")
        try:
            r = subprocess.run(
                ["git"] + args,
                cwd=cwd, capture_output=True, text=True, timeout=120,
                encoding="utf-8", errors="replace",
                env=env
            )
            if r.stdout:
                for line in r.stdout.strip().split("\n"):
                    if line:
                        self.log(line)
            if r.stderr:
                for line in r.stderr.strip().split("\n"):
                    if line:
                        # git 常把正常信息输出到 stderr
                        self.log(line, "WARN")
            if r.returncode != 0:
                self.log(f"命令失败，退出码: {r.returncode}", "ERROR")
                return False, r.stdout + r.stderr
            return True, r.stdout
        except subprocess.TimeoutExpired:
            self.log("命令超时（120秒）", "ERROR")
            return False, ""
        except FileNotFoundError:
            self.log("未找到 git 命令，请确认已安装 Git", "ERROR")
            return False, ""

    def do_status(self):
        proj = self.project_dir.get()
        if not os.path.isdir(proj):
            messagebox.showerror("错误", "项目目录不存在")
            return
        self.log("── Git Status ──")
        ok, out = self._git_live(proj, ["status"])
        if ok:
            self.log("状态查询完成")

    def do_commit_only(self):
        if self.is_pushing:
            return
        threading.Thread(target=self._commit_flow, args=(False,), daemon=True).start()

    def do_push(self):
        if self.is_pushing:
            return
        threading.Thread(target=self._commit_flow, args=(True,), daemon=True).start()

    def _commit_flow(self, push):
        """提交+推送流程"""
        self.is_pushing = True
        self.btn_push.configure(state="disabled")
        try:
            proj = self.project_dir.get()
            if not os.path.isdir(proj):
                self.log("项目目录不存在", "ERROR")
                return

            msg = self.commit_msg.get().strip()
            if not msg:
                self.log("请填写 commit 标题", "ERROR")
                messagebox.showwarning("提示", "请填写 commit 标题")
                return

            detail = self.detail_text.get("1.0", "end").strip()
            full_msg = msg
            if detail:
                full_msg = f"{msg}\n\n{detail}"

            # 1. git add -A
            self.log("── 添加文件 ──")
            ok, _ = self._git_live(proj, ["add", "-A"])
            if not ok:
                return

            # 2. git commit
            self.log("── 提交 ──")
            ok, _ = self._git_live(proj, ["commit", "-m", full_msg])
            if not ok:
                # 可能没有变更
                self.log("可能没有需要提交的变更", "WARN")

            if not push:
                self.log("提交完成（未推送）")
                return

            # 3. 推送
            self.log("── 推送到远程 ──")
            token = self.github_token.get().strip()
            user = self.github_user.get().strip()
            repo = self.repo_url.get().strip()
            branch = self.branch_name.get().strip()

            if not repo:
                self.log("未配置仓库地址", "ERROR")
                return

            # 构建带 token 的 URL: https://user:token@github.com/user/repo.git
            push_url = repo
            env = os.environ.copy()
            if token and user:
                # 从 repo URL 提取 github.com/user/repo.git 部分
                if repo.startswith("https://"):
                    push_url = repo.replace(
                        "https://",
                        f"https://{user}:{token}@"
                    )
                elif repo.startswith("http://"):
                    push_url = repo.replace(
                        "http://",
                        f"http://{user}:{token}@"
                    )
                else:
                    # SSH 或其他格式，用环境变量方式
                    env["GIT_ASKPASS"] = ""
                    push_url = repo
            else:
                self.log("未配置 token/用户名，将使用系统已存的凭证", "WARN")

            ok, _ = self._git_live(proj, ["push", push_url, branch], env=env)
            if ok:
                self.log("══ 推送成功！══")
                messagebox.showinfo("成功", "推送完成！")
            else:
                self.log("推送失败，请检查日志", "ERROR")

        except Exception as e:
            self.log(f"异常: {e}", "ERROR")
        finally:
            self.is_pushing = False
            self.btn_push.configure(state="normal")

    def check_gitignore(self):
        proj = self.project_dir.get()
        gi = os.path.join(proj, ".gitignore")
        dangerous = [".env", "*.token", "*secret*", "credentials*",
                      ".github_tool_config", ".sanguo_git_tool"]
        existing = ""
        if os.path.isfile(gi):
            with open(gi, "r", encoding="utf-8", errors="replace") as f:
                existing = f.read()

        missing = [p for p in dangerous if p not in existing]
        if not missing:
            self.log(".gitignore 已包含敏感文件规则")
            return

        self.log(f".gitignore 缺少规则: {', '.join(missing)}", "WARN")
        add = messagebox.askyesno(
            ".gitignore 检查",
            f".gitignore 缺少以下规则:\n{chr(10).join(missing)}\n\n是否追加？"
        )
        if add:
            with open(gi, "a", encoding="utf-8") as f:
                f.write("\n# ── 敏感文件保护 ──\n")
                for p in missing:
                    f.write(p + "\n")
            self.log(f"已追加 {len(missing)} 条规则到 .gitignore")

    # ────────────────────── 配置持久化 ──────────────────────

    def load_config(self):
        try:
            if os.path.isfile(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self.repo_url.set(cfg.get("repo_url", ""))
                self.github_user.set(cfg.get("github_user", ""))
                if cfg.get("github_token_b64"):
                    # base64 解码（仅简单编码，非加密）
                    self.github_token.set(
                        base64.b64decode(cfg["github_token_b64"]).decode("utf-8")
                    )
                    self.save_token.set(True)
                if cfg.get("branch"):
                    self.branch_name.set(cfg["branch"])
        except Exception:
            pass

    def save_config(self):
        cfg = {
            "repo_url": self.repo_url.get(),
            "github_user": self.github_user.get(),
            "branch": self.branch_name.get(),
        }
        if self.save_token.get() and self.github_token.get():
            cfg["github_token_b64"] = base64.b64encode(
                self.github_token.get().encode("utf-8")
            ).decode("utf-8")
            self.log("Token 将以 base64 编码保存到本地配置", "WARN")
        else:
            self.log("Token 不保存（仅本次会话使用）")

        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
            self.log(f"配置已保存到: {CONFIG_FILE}")
            messagebox.showinfo("成功", "配置已保存！")
        except Exception as e:
            self.log(f"保存配置失败: {e}", "ERROR")
            messagebox.showerror("错误", f"保存失败: {e}")


def main():
    root = tk.Tk()
    app = GitPushTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
