#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 一键推送工具 GUI 版（tkinter，纯 Python 标准库，零第三方依赖）

按标准 git 流程执行: git add . → git commit -m "..." → git push <remote> <branch>
每条命令与输出都实时显示在日志区，跟命令行操作完全一致。

用法: python git_push_gui.py
"""
import os
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

REPO_DIR = os.path.dirname(os.path.abspath(__file__))


def run(args, timeout=None):
    """捕获执行 git 命令，返回 (code, stdout, stderr)"""
    try:
        p = subprocess.run(args, capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           cwd=REPO_DIR, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return -2, "", "连接超时（%s 秒）" % timeout
    except Exception as e:
        return -1, "", str(e)


class PushGUI:
    def __init__(self, root):
        self.root = root
        root.title("GitHub 一键推送")
        root.geometry("660x580")
        root.minsize(560, 460)
        self.msg_queue = queue.Queue()

        # ── 仓库 ─────────────────────────────────
        top = ttk.Frame(root, padding=(10, 8, 10, 4))
        top.pack(fill="x")
        self.repo_lbl = ttk.Label(top, text="仓库: %s" % REPO_DIR, foreground="#555")
        self.repo_lbl.pack(side="left")
        ttk.Button(top, text="选择目录", command=self.choose_dir).pack(side="right", padx=4)
        ttk.Button(top, text="刷新", command=self.refresh).pack(side="right")

        # ── 提交 ─────────────────────────────────
        frm = ttk.LabelFrame(root, text="提交", padding=(8, 6))
        frm.pack(fill="x", padx=10, pady=4)
        row1 = ttk.Frame(frm)
        row1.pack(fill="x")
        ttk.Label(row1, text="提交信息:").pack(side="left")
        self.msg_entry = ttk.Entry(row1)
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=6)

        row2 = ttk.Frame(frm)
        row2.pack(fill="x", pady=(6, 0))
        self.add_var = tk.BooleanVar(value=True)
        self.commit_var = tk.BooleanVar(value=True)
        self.push_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(row2, text="git add .", variable=self.add_var).pack(side="left")
        ttk.Checkbutton(row2, text="git commit", variable=self.commit_var).pack(side="left", padx=10)
        ttk.Checkbutton(row2, text="git push", variable=self.push_var).pack(side="left")

        # ── 推送目标 ─────────────────────────────
        frm2 = ttk.LabelFrame(root, text="推送目标", padding=(8, 6))
        frm2.pack(fill="x", padx=10, pady=4)
        row3 = ttk.Frame(frm2)
        row3.pack(fill="x")
        ttk.Label(row3, text="远程:").pack(side="left")
        self.remote_combo = ttk.Combobox(row3, state="readonly", width=20)
        self.remote_combo.pack(side="left", padx=6)
        ttk.Label(row3, text="目标分支:").pack(side="left", padx=(12, 0))
        self.branch_entry = ttk.Entry(row3, width=24)
        self.branch_entry.pack(side="left", padx=6)
        self.force_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row3, text="--force", variable=self.force_var).pack(side="left", padx=8)

        # ── 按钮 ─────────────────────────────────
        btns = ttk.Frame(root, padding=(10, 4, 10, 4))
        btns.pack(fill="x")
        self.run_btn = ttk.Button(btns, text="一键执行", command=self.on_run)
        self.run_btn.pack(side="left")
        ttk.Button(btns, text="退出", command=root.destroy).pack(side="left", padx=8)

        # ── 日志 ─────────────────────────────────
        logf = ttk.LabelFrame(root, text="执行日志")
        logf.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.log = tk.Text(logf, wrap="none")
        sb = ttk.Scrollbar(logf, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log.pack(fill="both", expand=True, padx=6, pady=6)

        self.refresh()
        self.root.after(100, self._poll)

    # ── 工具方法 ────────────────────────────────
    def log_line(self, s):
        self.log.insert("end", s + "\n")
        self.log.see("end")

    def choose_dir(self):
        global REPO_DIR
        d = filedialog.askdirectory()
        if d:
            REPO_DIR = d
            self.repo_lbl.config(text="仓库: %s" % d)
            self.refresh()

    def refresh(self):
        code, out, err = run(["git", "remote"])
        if code == 0:
            remotes = [r for r in out.splitlines() if r]
            self.remote_combo["values"] = remotes
            if remotes and not self.remote_combo.get():
                self.remote_combo.current(0)
        code, out, err = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        if code == 0:
            self.branch_entry.delete(0, "end")
            self.branch_entry.insert(0, out.strip())
        else:
            self.log_line("警告: 当前目录不是 git 仓库")

    # ── 执行 ────────────────────────────────────
    def on_run(self):
        remote = self.remote_combo.get().strip()
        branch = self.branch_entry.get().strip()
        if not remote:
            messagebox.showwarning("提示", "请选择远程")
            return
        if not branch:
            messagebox.showwarning("提示", "请输入目标分支")
            return
        if self.commit_var.get() and not self.msg_entry.get().strip():
            messagebox.showwarning("提示", "请输入提交信息")
            return
        self.run_btn.config(state="disabled")
        self.log.delete("1.0", "end")
        threading.Thread(target=self._run_worker, args=(remote, branch), daemon=True).start()

    def _run_worker(self, remote, branch):
        msg = self.msg_entry.get().strip() or "update"
        steps = []
        if self.add_var.get():
            steps.append(["git", "add", "."])
        if self.commit_var.get():
            code, out, _ = run(["git", "status", "--porcelain"])
            if code == 0 and out.strip():
                steps.append(["git", "commit", "-m", msg])
            else:
                self.msg_queue.put(("log", "工作区无更改，跳过 commit"))
        if self.push_var.get():
            cmd = ["git", "push"]
            if self.force_var.get():
                cmd.append("--force")
            cmd += [remote, branch]
            steps.append(cmd)
        if not steps:
            self.msg_queue.put(("log", "没有选择任何步骤"))
            self.msg_queue.put(("done",))
            return
        for st in steps:
            self.msg_queue.put(("cmd", " ".join(st)))
            code = self._stream(st)
            if code != 0:
                self.msg_queue.put(("log", "命令失败，退出码 %d" % code))
                break
        else:
            self.msg_queue.put(("log", "全部完成"))
        self.msg_queue.put(("done",))

    def _stream(self, args):
        """实时流式执行命令，返回退出码（300 秒超时自动终止）"""
        try:
            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, encoding="utf-8", errors="replace",
                                 cwd=REPO_DIR, bufsize=1)
        except Exception as e:
            self.msg_queue.put(("log", str(e)))
            return -1
        deadline = time.time() + 300
        while True:
            try:
                line = p.stdout.readline()
            except Exception:
                break
            if line:
                self.msg_queue.put(("log", line.rstrip("\n")))
                continue
            if p.poll() is not None:
                return p.returncode
            if time.time() > deadline:
                p.kill()
                self.msg_queue.put(("log", "执行超时（300 秒），已终止"))
                return -2
            time.sleep(0.2)

    # ── UI 轮询 ─────────────────────────────────
    def _poll(self):
        try:
            while True:
                item = self.msg_queue.get_nowait()
                kind = item[0]
                if kind == "cmd":
                    self.log_line("$ " + item[1])
                elif kind == "log":
                    self.log_line(item[1])
                elif kind == "done":
                    self.run_btn.config(state="normal")
        except queue.Empty:
            pass
        self.root.after(100, self._poll)


def main():
    root = tk.Tk()
    PushGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
