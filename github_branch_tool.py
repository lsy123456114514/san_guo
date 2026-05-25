#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 分支和标签管理工具
支持：C和Python混合版本 / 纯Python版本
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class GitHubBranchTool:
    def __init__(self, master):
        self.master = master
        self.master.title("GitHub 分支标签管理工具")
        self.master.geometry("700x600")
        self.master.configure(bg="#f5f5f5")
        self.master.resizable(True, True)

        # 版本配置
        self.versions = {
            "C和Python混合版本": {
                "branch": "cpp-python",
                "files": []  # 空列表表示全部文件
            },
            "纯Python版本": {
                "branch": "python-only",
                "files": []  # 空列表表示全部文件
            }
        }

        self.selected_version = tk.StringVar(value="C和Python混合版本")
        self.custom_tag = tk.StringVar()
        self.auto_push = tk.BooleanVar(value=True)
        self.branch_list = []
        self.tag_list = []

        self.create_widgets()
        self.refresh_all()

    def create_widgets(self):
        """创建界面组件"""
        # 标题
        title_frame = tk.Frame(self.master, bg="#2c3e50", height=60)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)

        title = tk.Label(title_frame, text="GitHub 分支 & 标签管理工具",
                         font=("Microsoft YaHei", 18, "bold"),
                         fg="white", bg="#2c3e50")
        title.pack(pady=15)

        # 主容器
        main_frame = tk.Frame(self.master, bg="#f5f5f5")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # 左侧面板 - 版本选择和标签设置
        left_frame = tk.LabelFrame(main_frame, text="版本与标签设置",
                                    font=("Microsoft YaHei", 11, "bold"),
                                    bg="#f5f5f5", padx=10, pady=10)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # 版本选择
        tk.Label(left_frame, text="选择目标版本:", font=("Microsoft YaHei", 10),
                 bg="#f5f5f5").pack(anchor="w")

        for version_name in self.versions.keys():
            rb = tk.Radiobutton(left_frame, text=version_name,
                               variable=self.selected_version,
                               value=version_name,
                               font=("Microsoft YaHei", 10),
                               bg="#f5f5f5",
                               command=self.on_version_change)
            rb.pack(anchor="w", pady=2)

        # 分支信息
        self.branch_info_label = tk.Label(left_frame, text="",
                                          font=("Microsoft YaHei", 9),
                                          bg="#f5f5f5", fg="#e74c3c")
        self.branch_info_label.pack(anchor="w", pady=5)

        # 自定义标签
        tk.Label(left_frame, text="自定义标签 (可选):", font=("Microsoft YaHei", 10),
                 bg="#f5f5f5").pack(anchor="w", pady=(15, 0))

        tag_frame = tk.Frame(left_frame, bg="#f5f5f5")
        tag_frame.pack(fill="x", pady=5)

        self.tag_entry = tk.Entry(tag_frame, textvariable=self.custom_tag,
                                   font=("Microsoft YaHei", 10), width=20)
        self.tag_entry.pack(side="left", fill="x", expand=True)

        tk.Button(tag_frame, text="清除", command=lambda: self.custom_tag.set(""),
                  bg="#95a5a6", fg="white", width=6).pack(side="left", padx=(5, 0))

        # 预设标签
        tk.Label(left_frame, text="快速选择:", font=("Microsoft YaHei", 9),
                 bg="#f5f5f5", fg="#7f8c8d").pack(anchor="w", pady=(10, 0))

        preset_frame = tk.Frame(left_frame, bg="#f5f5f5")
        preset_frame.pack(fill="x")

        presets = ["v1.0", "v1.1", "v2.0", "release"]
        for preset in presets:
            tk.Button(preset_frame, text=preset, command=lambda p=preset: self.custom_tag.set(p),
                     bg="#3498db", fg="white", width=6).pack(side="left", padx=2, pady=2)

        # 操作按钮
        btn_frame = tk.Frame(left_frame, bg="#f5f5f5")
        btn_frame.pack(fill="x", pady=20)

        self.push_btn = tk.Button(btn_frame, text="🚀 推送代码",
                                   command=self.push_to_github,
                                   bg="#27ae60", fg="white",
                                   font=("Microsoft YaHei", 12, "bold"),
                                   height=2, cursor="hand2")
        self.push_btn.pack(fill="x", pady=2)

        tk.Button(btn_frame, text="🔄 刷新全部",
                  command=self.refresh_all,
                  bg="#9b59b6", fg="white",
                  font=("Microsoft YaHei", 10)).pack(fill="x", pady=2)

        # 右侧面板 - 分支和标签列表
        right_frame = tk.Frame(main_frame, bg="#f5f5f5")
        right_frame.pack(side="right", fill="both", expand=True)

        # 分支列表
        branch_frame = tk.LabelFrame(right_frame, text="本地分支",
                                      font=("Microsoft YaHei", 11, "bold"),
                                      bg="#f5f5f5", padx=5, pady=5)
        branch_frame.pack(fill="both", expand=True, pady=(0, 10))

        branch_list_frame = tk.Frame(branch_frame, bg="white")
        branch_list_frame.pack(fill="both", expand=True)

        scrollbar_y = tk.Scrollbar(branch_list_frame)
        scrollbar_y.pack(side="right", fill="y")

        scrollbar_x = tk.Scrollbar(branch_list_frame, orient="horizontal")
        scrollbar_x.pack(side="bottom", fill="x")

        self.branch_listbox = tk.Listbox(branch_list_frame, width=35,
                                          font=("Consolas", 10),
                                          yscrollcommand=scrollbar_y.set,
                                          xscrollcommand=scrollbar_x.set,
                                          bg="white")
        self.branch_listbox.pack(side="left", fill="both", expand=True)
        scrollbar_y.config(command=self.branch_listbox.yview)
        scrollbar_x.config(command=self.branch_listbox.xview)

        branch_btn_frame = tk.Frame(branch_frame, bg="#f5f5f5")
        branch_btn_frame.pack(fill="x", pady=5)

        tk.Button(branch_btn_frame, text="创建分支", command=self.create_branch,
                 bg="#2980b9", fg="white", width=10).pack(side="left", padx=2)
        tk.Button(branch_btn_frame, text="切换分支", command=self.checkout_branch,
                 bg="#8e44ad", fg="white", width=10).pack(side="left", padx=2)
        tk.Button(branch_btn_frame, text="删除分支", command=self.delete_branch,
                 bg="#c0392b", fg="white", width=10).pack(side="left", padx=2)

        # 标签列表
        tag_list_frame = tk.LabelFrame(right_frame, text="本地标签",
                                        font=("Microsoft YaHei", 11, "bold"),
                                        bg="#f5f5f5", padx=5, pady=5)
        tag_list_frame.pack(fill="both", expand=True)

        tag_listbox_frame = tk.Frame(tag_list_frame, bg="white")
        tag_listbox_frame.pack(fill="both", expand=True)

        scrollbar_y2 = tk.Scrollbar(tag_listbox_frame)
        scrollbar_y2.pack(side="right", fill="y")

        self.tag_listbox = tk.Listbox(tag_listbox_frame, width=35,
                                       font=("Consolas", 10),
                                       yscrollcommand=scrollbar_y2.set,
                                       bg="white")
        self.tag_listbox.pack(side="left", fill="both", expand=True)
        scrollbar_y2.config(command=self.tag_listbox.yview)

        tag_btn_frame = tk.Frame(tag_list_frame, bg="#f5f5f5")
        tag_btn_frame.pack(fill="x", pady=5)

        tk.Button(tag_btn_frame, text="创建标签", command=self.create_tag,
                 bg="#27ae60", fg="white", width=10).pack(side="left", padx=2)
        tk.Button(tag_btn_frame, text="推送标签", command=self.push_tag,
                 bg="#f39c12", fg="white", width=10).pack(side="left", padx=2)
        tk.Button(tag_btn_frame, text="删除标签", command=self.delete_tag,
                 bg="#c0392b", fg="white", width=10).pack(side="left", padx=2)

        # 状态栏
        self.status_label = tk.Label(self.master, text="就绪",
                                      font=("Microsoft YaHei", 9),
                                      bg="#34495e", fg="#ecf0f1",
                                      anchor="w")
        self.status_label.pack(side="bottom", fill="x")

    def run_git_command(self, *args, capture=True, check=True, timeout=10):
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
            raise Exception("Git命令超时，请检查网络连接")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Git命令执行失败: {e.stderr}")
        except FileNotFoundError:
            raise Exception("Git未安装或不在PATH中")

    def refresh_all(self):
        """刷新所有信息"""
        self.refresh_branches()
        self.refresh_tags()
        self.update_branch_info()

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

                # 判断是本地还是远程分支
                if 'remotes/' in line or line.startswith('*'):
                    # 远程分支
                    if 'remotes/' in line:
                        remote_branches.append(line)
                else:
                    # 本地分支
                    if line.startswith('*'):
                        line = line[1:].strip()
                    local_branches.append(line)

            # 先显示本地分支
            self.branch_listbox.insert(tk.END, "━━━ 本地分支 ━━━")
            for line in local_branches:
                if line == current:
                    display = f"★ {line} (当前)"
                else:
                    display = f"  {line}"

                # 特殊分支标记
                if 'cpp-python' in line:
                    display += " [C+Python]"
                elif 'python' in line.lower():
                    display += " [Python]"

                self.branch_listbox.insert(tk.END, display)

                if line == current:
                    # 选中当前分支
                    for i in range(self.branch_listbox.size()):
                        if current in self.branch_listbox.get(i):
                            self.branch_listbox.selection_set(i)
                            break

            # 再显示远程分支
            if remote_branches:
                self.branch_listbox.insert(tk.END, "")
                self.branch_listbox.insert(tk.END, "━━━ 远程分支 ━━━")

                # 去重远程分支（显示 origin/xxx 格式）
                seen = set()
                for line in remote_branches:
                    # 提取 remote/branch 格式
                    parts = line.split(' -> ')
                    if len(parts) > 1:
                        continue  # 跳过跟踪分支
                    branch = line.replace('remotes/', '')
                    if '/' in branch:
                        remote_name = branch.split('/')[0]
                        branch_name = '/'.join(branch.split('/')[1:])
                        key = f"{remote_name}/{branch_name}"
                        if key not in seen:
                            seen.add(key)
                            self.branch_listbox.insert(tk.END, f"  🌐 {key}")

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
                        self.tag_listbox.insert(tk.END, f"  {tag.strip()}")
        except Exception as e:
            self.tag_listbox.insert(tk.END, f"错误: {str(e)}")

    def update_branch_info(self):
        """更新分支信息"""
        try:
            current = self.run_git_command("rev-parse", "--abbrev-ref", "HEAD")[0]
            _, remote, _ = self.run_git_command("remote", "-v")
            remote_name = remote.split()[0] if remote else "origin"

            info = f"当前分支: {current} | 远程: {remote_name}"
            self.branch_info_label.config(text=info)
        except:
            pass

    def on_version_change(self):
        """版本选择改变"""
        version = self.selected_version.get()
        branch = self.versions[version]["branch"]
        self.status_label.config(text=f"已选择: {version} -> 分支: {branch}")

    def push_to_github(self):
        """推送到GitHub"""
        try:
            version = self.selected_version.get()
            branch = self.versions[version]["branch"]
            custom_tag = self.custom_tag.get().strip()

            # 检查Git状态
            self.status_label.config(text="正在检查Git状态...", fg="yellow")
            self.master.update()

            # 获取远程仓库信息
            remote_output, _, rc = self.run_git_command("remote", "-v")
            if rc != 0 or not remote_output:
                messagebox.showerror("错误", "未配置远程仓库，请先设置: git remote add origin <url>")
                return

            remote_name = remote_output.split()[0]

            # 检查是否有未提交的更改
            status, _, _ = self.run_git_command("status", "--porcelain")
            if status:
                if not messagebox.askyesno("提示", "有未提交的更改，是否先暂存?"):
                    return
                self.run_git_command("add", "-A")

            # 获取当前分支名
            current_branch, _, _ = self.run_git_command("rev-parse", "--abbrev-ref", "HEAD")

            # 询问是否创建新分支
            if not messagebox.askyesno("确认",
                f"即将推送:\n\n版本: {version}\n分支: {branch}\n当前分支: {current_branch}\n\n是否继续?"):
                return

            self.push_btn.config(state="disabled", text="推送中...")
            self.status_label.config(text="正在推送代码...", fg="yellow")
            self.master.update()

            # 推送代码
            self.run_git_command("push", "-u", remote_name, branch, check=True)

            # 如果填写了标签，则创建并推送标签
            if custom_tag:
                self.status_label.config(text=f"正在创建标签 {custom_tag}...", fg="yellow")
                self.master.update()

                # 创建标签
                self.run_git_command("tag", "-a", custom_tag, "-m", f"Release {custom_tag}")

                # 推送标签
                self.run_git_command("push", remote_name, "tag", custom_tag)

            messagebox.showinfo("成功", f"✅ 推送成功!\n\n版本: {version}\n分支: {branch}\n标签: {custom_tag or '无'}")
            self.status_label.config(text="推送完成", fg="green")

        except Exception as e:
            messagebox.showerror("错误", f"推送失败:\n{str(e)}")
            self.status_label.config(text="推送失败", fg="red")
        finally:
            self.push_btn.config(state="normal", text="🚀 推送代码")

    def create_branch(self):
        """创建分支"""
        dialog = tk.Toplevel(self.master)
        dialog.title("创建分支")
        dialog.geometry("400x220")
        dialog.configure(bg="#f5f5f5")
        dialog.transient(self.master)
        dialog.grab_set()

        tk.Label(dialog, text="分支名称:", font=("Microsoft YaHei", 10),
                 bg="#f5f5f5").pack(pady=10)

        branch_entry = tk.Entry(dialog, font=("Microsoft YaHei", 12), width=30)
        branch_entry.pack(pady=5)
        branch_entry.focus()

        # 添加：是否推送到远程的选项
        push_to_remote = tk.BooleanVar(value=True)
        tk.Checkbutton(dialog, text="同时推送到远程仓库 (GitHub)",
                      variable=push_to_remote,
                      font=("Microsoft YaHei", 10),
                      bg="#f5f5f5").pack(pady=5)

        def do_create():
            name = branch_entry.get().strip()
            if not name:
                messagebox.showwarning("提示", "请输入分支名称")
                return

            try:
                # 获取远程仓库名
                remote_output, _, _ = self.run_git_command("remote", "-v")
                remote_name = remote_output.split()[0] if remote_output else "origin"

                # 创建并切换到新分支
                self.run_git_command("checkout", "-b", name)

                # 如果选择推送到远程
                if push_to_remote.get():
                    self.status_label.config(text=f"正在推送 {name} 到远程...", fg="yellow")
                    dialog.update()
                    self.run_git_command("push", "-u", remote_name, name, check=True)

                messagebox.showinfo("成功", f"分支 '{name}' 创建并推送成功!\n\n远程分支: {remote_name}/{name}")
                dialog.destroy()
                self.refresh_all()
            except Exception as e:
                messagebox.showerror("错误", str(e))

        btn_frame = tk.Frame(dialog, bg="#f5f5f5")
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="创建", command=do_create,
                  bg="#27ae60", fg="white", width=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text="取消", command=dialog.destroy,
                  bg="#95a5a6", fg="white", width=10).pack(side="left", padx=5)

        dialog.bind("<Return>", lambda e: do_create())

    def checkout_branch(self):
        """切换分支"""
        selection = self.branch_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个分支")
            return

        content = self.branch_listbox.get(selection[0])
        # 提取分支名（去掉特殊标记）
        branch = content.replace("★", "").replace("(当前)", "").replace("[C+Python]", "").replace("[Python]", "").replace(" ", "").strip()

        # 处理远程分支
        if "/" in branch:
            branch = branch.split("/")[-1]

        try:
            self.run_git_command("checkout", branch)
            messagebox.showinfo("成功", f"已切换到分支: {branch}")
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
        branch = content.replace("★", "").replace("(当前)", "").replace("[C+Python]", "").replace("[Python]", "").replace(" ", "").strip()

        if "/" in branch:
            branch = branch.split("/")[-1]

        if messagebox.askyesno("确认", f"确定要删除分支 '{branch}' 吗?"):
            try:
                self.run_git_command("branch", "-D", branch)
                messagebox.showinfo("成功", f"分支 '{branch}' 已删除")
                self.refresh_all()
            except Exception as e:
                messagebox.showerror("错误", str(e))

    def create_tag(self):
        """创建标签"""
        dialog = tk.Toplevel(self.master)
        dialog.title("创建标签")
        dialog.geometry("400x200")
        dialog.configure(bg="#f5f5f5")
        dialog.transient(self.master)
        dialog.grab_set()

        tk.Label(dialog, text="标签名称:", font=("Microsoft YaHei", 10),
                 bg="#f5f5f5").pack(pady=10)

        tag_entry = tk.Entry(dialog, font=("Microsoft YaHei", 12), width=30)
        tag_entry.pack(pady=5)
        tag_entry.focus()

        tk.Label(dialog, text="标签说明:", font=("Microsoft YaHei", 10),
                 bg="#f5f5f5").pack(pady=(10, 0))

        msg_entry = tk.Entry(dialog, font=("Microsoft YaHei", 10), width=40)
        msg_entry.pack(pady=5)

        def do_create():
            name = tag_entry.get().strip()
            msg = msg_entry.get().strip() or f"Release {name}"

            if not name:
                messagebox.showwarning("提示", "请输入标签名称")
                return

            try:
                self.run_git_command("tag", "-a", name, "-m", msg)
                messagebox.showinfo("成功", f"标签 '{name}' 创建成功!")
                dialog.destroy()
                self.refresh_tags()
            except Exception as e:
                messagebox.showerror("错误", str(e))

        btn_frame = tk.Frame(dialog, bg="#f5f5f5")
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="创建", command=do_create,
                  bg="#27ae60", fg="white", width=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text="取消", command=dialog.destroy,
                  bg="#95a5a6", fg="white", width=10).pack(side="left", padx=5)

    def push_tag(self):
        """推送标签"""
        selection = self.tag_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个标签")
            return

        content = self.tag_listbox.get(selection[0])
        tag = content.strip()

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

        content = self.tag_listbox.get(selection[0])
        tag = content.strip()

        if messagebox.askyesno("确认", f"确定要删除标签 '{tag}' 吗?"):
            try:
                self.run_git_command("tag", "-d", tag)
                messagebox.showinfo("成功", f"标签 '{tag}' 已删除")
                self.refresh_tags()
            except Exception as e:
                messagebox.showerror("错误", str(e))


def main():
    """主函数"""
    root = tk.Tk()
    app = GitHubBranchTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
