#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 推送工具 GUI 版（tkinter，纯 Python 标准库，零第三方依赖）
- 下拉选择远程、列表选择本地/远程分支，可输入新分支名
- 推送输出实时显示在日志区，后台线程执行不卡界面
- 认证复用已配置好的 SSH 密钥/令牌，本工具不做任何认证处理
用法: python git_push_gui.py
"""
import os
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

REPO_DIR = os.path.dirname(os.path.abspath(__file__))

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def run_capture(args, timeout=None):
    """运行 git 命令并捕获输出，返回 (code, stdout, stderr)；timeout 秒超时返回 code=-2"""
    try:
        p = subprocess.run(args, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", cwd=REPO_DIR,
                           timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return -2, "", "连接超时（超过 %s 秒），请检查网络/代理" % timeout
    except FileNotFoundError:
        return -1, "", "未找到 git 命令，请先安装 Git 并加入 PATH"
    except Exception as e:
        return -1, "", str(e)


class PushGUI:
    def __init__(self, root):
        self.root = root
        root.title("GitHub 推送工具")
        root.geometry("700x580")
        root.minsize(600, 480)

        self.msg_queue = queue.Queue()

        # ── 远程选择 ────────────────────────────────
        top = ttk.Frame(root, padding=(10, 8, 10, 4))
        top.pack(fill="x")
        ttk.Label(top, text="远程仓库:").pack(side="left")
        self.remote_combo = ttk.Combobox(top, state="readonly", width=28)
        self.remote_combo.pack(side="left", padx=(6, 6))
        self.remote_combo.bind("<<ComboboxSelected>>", lambda e: self.load_remote_branches())
        ttk.Button(top, text="刷新远程", command=self.load_remotes).pack(side="left")
        ttk.Button(top, text="刷新分支", command=self.load_all).pack(side="left", padx=6)

        # ── 本地 / 远程分支 ──────────────────────────
        mid = ttk.Frame(root, padding=(10, 4, 10, 4))
        mid.pack(fill="both", expand=True)

        left = ttk.LabelFrame(mid, text="本地分支")
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self.local_list = tk.Listbox(left, exportselection=False)
        self.local_list.pack(fill="both", expand=True, padx=6, pady=6)

        right = ttk.LabelFrame(mid, text="远程分支（选中或输入新名新建）")
        right.pack(side="right", fill="both", expand=True, padx=(5, 0))
        self.remote_list = tk.Listbox(right, exportselection=False)
        self.remote_list.pack(fill="both", expand=True, padx=6, pady=(6, 2))
        newrow = ttk.Frame(right)
        newrow.pack(fill="x", padx=6, pady=(2, 6))
        ttk.Label(newrow, text="新分支名:").pack(side="left")
        self.new_entry = ttk.Entry(newrow)
        self.new_entry.pack(side="left", fill="x", expand=True, padx=6)

        # ── 选项与按钮 ──────────────────────────────
        opt = ttk.Frame(root, padding=(10, 2, 10, 2))
        opt.pack(fill="x")
        self.force_var = tk.BooleanVar(value=False)
        self.upstream_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt, text="强制推送 (--force)", variable=self.force_var).pack(side="left")
        ttk.Checkbutton(opt, text="设置上游跟踪 (--upstream)", variable=self.upstream_var).pack(side="left", padx=12)

        btns = ttk.Frame(root, padding=(10, 2, 10, 6))
        btns.pack(fill="x")
        self.push_btn = ttk.Button(btns, text="推送", command=self.on_push)
        self.push_btn.pack(side="left")
        ttk.Button(btns, text="退出", command=root.destroy).pack(side="left", padx=8)

        # ── 日志区 ──────────────────────────────────
        logframe = ttk.LabelFrame(root, text="推送日志")
        logframe.pack(fill="both", expand=True, padx=10, pady=(2, 10))
        self.log = tk.Text(logframe, height=10, state="normal", wrap="none")
        sb = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log.pack(fill="both", expand=True, padx=6, pady=6)

        self.load_all()
        self.root.after(100, self._poll)

    # ── 数据加载 ─────────────────────────────────
    def log_line(self, text):
        self.log.insert("end", text + "\n")
        self.log.see("end")

    def load_all(self):
        self.load_remotes()
        self.load_local_branches()

    def load_remotes(self):
        code, out, err = run_capture(["git", "remote"])
        if code != 0:
            messagebox.showerror("错误", err or out)
            return
        remotes = [r for r in out.splitlines() if r]
        self.remote_combo["values"] = remotes
        if remotes and not self.remote_combo.get():
            self.remote_combo.current(0)
            self.load_remote_branches()

    def load_local_branches(self):
        code, out, err = run_capture(["git", "branch", "--no-color", "--list"])
        self.local_list.delete(0, "end")
        if code != 0:
            self.log_line("读取本地分支失败: %s" % (err or out))
            return
        for line in out.splitlines():
            name = line.strip()
            if name.startswith("*"):
                name = name[1:].strip()
            if name:
                self.local_list.insert("end", name)

    def load_remote_branches(self):
        remote = self.remote_combo.get().strip()
        if not remote:
            return
        self.remote_list.delete(0, "end")
        self.remote_list.insert("end", "加载中...")
        threading.Thread(target=self._load_remote_worker, args=(remote,), daemon=True).start()

    def _load_remote_worker(self, remote):
        code, out, err = run_capture(["git", "ls-remote", "--heads", remote], timeout=15)
        self.msg_queue.put(("remote_branches", (code, out, err)))

    # ── 推送 ─────────────────────────────────────
    def on_push(self):
        remote = self.remote_combo.get().strip()
        sel_local = self.local_list.curselection()
        if not remote:
            messagebox.showwarning("提示", "请选择远程仓库")
            return
        if not sel_local:
            messagebox.showwarning("提示", "请选择要推送的本地分支")
            return
        local = self.local_list.get(sel_local[0])

        target = self.new_entry.get().strip()
        if not target:
            sel_remote = self.remote_list.curselection()
            if sel_remote:
                target = self.remote_list.get(sel_remote[0])
                if target == "加载中...":
                    messagebox.showwarning("提示", "远程分支还在加载，请稍候")
                    return
        if not target:
            messagebox.showwarning("提示", "请选择远程分支或输入新分支名")
            return

        if not messagebox.askyesno("确认推送", "推送 %s 到 %s/%s ?" % (local, remote, target)):
            return

        force = self.force_var.get()
        upstream = self.upstream_var.get()
        self.push_btn.config(state="disabled")
        self.log.delete("1.0", "end")
        self.log_line("> git push %s %s:%s" % ("--force " if force else "", remote, local, target))
        threading.Thread(target=self._push_worker,
                         args=(remote, local, target, force, upstream), daemon=True).start()

    def _push_worker(self, remote, local, target, force, upstream):
        args = ["git", "push"]
        if force:
            args.append("--force")
        args += [remote, "%s:%s" % (local, target)]
        code = -1
        try:
            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, encoding="utf-8", errors="replace",
                                 cwd=REPO_DIR, bufsize=1)
        except Exception as e:
            self.msg_queue.put(("log", str(e)))
            self.msg_queue.put(("done", code))
            return
        deadline = time.time() + 180  # 推送总超时 180 秒
        while True:
            try:
                line = p.stdout.readline()
            except Exception:
                break
            if line:
                self.msg_queue.put(("log", line.rstrip("\n")))
                continue
            if p.poll() is not None:
                code = p.returncode
                break
            if time.time() > deadline:
                p.kill()
                self.msg_queue.put(("log", "推送超时（180 秒），已终止"))
                code = -2
                break
            time.sleep(0.2)
        if upstream and code == 0:
            run_capture(["git", "branch", "--set-upstream-to=%s/%s" % (remote, target), local])
        self.msg_queue.put(("done", code))

    # ── UI 轮询队列 ─────────────────────────────
    def _poll(self):
        try:
            while True:
                kind, payload = self.msg_queue.get_nowait()
                if kind == "log":
                    self.log_line(payload)
                elif kind == "remote_branches":
                    self._apply_remote_branches(*payload)
                elif kind == "done":
                    self.push_btn.config(state="normal")
                    if payload == 0:
                        self.log_line("推送完成")
                    else:
                        self.log_line("推送失败，退出码 %d" % payload)
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def _apply_remote_branches(self, code, out, err):
        self.remote_list.delete(0, "end")
        if code != 0:
            self.remote_list.insert("end", "无法获取远程分支（网络/认证问题）")
            self.log_line("获取远程分支失败: %s" % (err or out))
            return
        branches = [ln.split("refs/heads/")[-1] for ln in out.splitlines() if "refs/heads/" in ln]
        if not branches:
            self.remote_list.insert("end", "（远程暂无分支，可用新分支名创建）")
        for b in branches:
            self.remote_list.insert("end", b)


def main():
    root = tk.Tk()
    PushGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
