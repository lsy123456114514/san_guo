#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 一键推送工具（最标准方式，纯 Python 标准库，零第三方依赖）

按标准 git 流程在仓库目录执行:
    git add .  →  git commit -m "提交信息"  →  git push <remote> <branch>

每条命令都实时显示，输出与手敲命令行完全一致。

用法:
    python git_push_tool.py "提交信息"            # 一步完成 add+commit+push
    python git_push_tool.py                       # 交互式输入提交信息
    python git_push_tool.py --branch 分支名       # 指定推送分支（默认当前分支）
    python git_push_tool.py --remote 远程名       # 指定远程（默认 origin）
    python git_push_tool.py --repo 仓库目录       # 指定仓库目录（默认脚本所在目录）
    python git_push_tool.py --no-add              # 跳过 git add（需自行暂存）
    python git_push_tool.py --push-only           # 只推送，跳过 add/commit
    python git_push_tool.py --force               # 强制推送
"""
import os
import subprocess
import sys

REPO_DIR = os.path.dirname(os.path.abspath(__file__))


def run(args, capture=True):
    """运行 git 命令。capture=True 返回 (code, out, err)；否则实时显示输出。"""
    try:
        if capture:
            p = subprocess.run(args, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", cwd=REPO_DIR)
            return p.returncode, p.stdout.strip(), p.stderr.strip()
        p = subprocess.run(args, cwd=REPO_DIR)
        return p.returncode, "", ""
    except FileNotFoundError:
        print("错误: 未找到 git 命令，请先安装 Git 并加入 PATH")
        sys.exit(1)


def git(cmd):
    """执行 git 命令：先打印命令行，再实时显示输出，返回退出码"""
    print("\n$ git %s" % " ".join(cmd))
    return run(["git"] + cmd, capture=False)[0]


def parse_args(argv):
    opts = {"remote": None, "branch": None, "repo": None, "message": None,
            "no_add": False, "push_only": False, "force": False}
    rest = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--remote" and i + 1 < len(argv):
            opts["remote"] = argv[i + 1]
            i += 2
            continue
        if a == "--branch" and i + 1 < len(argv):
            opts["branch"] = argv[i + 1]
            i += 2
            continue
        if a == "--repo" and i + 1 < len(argv):
            opts["repo"] = argv[i + 1]
            i += 2
            continue
        if a == "--no-add":
            opts["no_add"] = True
        elif a == "--push-only":
            opts["push_only"] = True
        elif a == "--force":
            opts["force"] = True
        else:
            rest.append(a)
        i += 1
    if rest:
        opts["message"] = " ".join(rest)
    return opts


def main():
    global REPO_DIR
    opts = parse_args(sys.argv[1:])
    if opts["repo"]:
        REPO_DIR = os.path.abspath(opts["repo"])

    remote = opts["remote"] or "origin"

    # 获取当前分支（标准方式）
    code, out, err = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture=True)
    if code != 0:
        print("错误: 不是 git 仓库（%s）" % (err or out))
        return 1
    branch = opts["branch"] or out
    print("仓库: %s" % REPO_DIR)
    print("远程: %s   分支: %s" % (remote, branch))

    # 1. git add .（暂存所有更改）
    if not opts["push_only"] and not opts["no_add"]:
        if git(["add", "."]) != 0:
            print("git add 失败，已停止")
            return 1

    # 2. git commit（工作区有更改才提交）
    if not opts["push_only"]:
        code, out, _ = run(["git", "status", "--porcelain"], capture=True)
        if out.strip():
            msg = opts["message"]
            if not msg:
                try:
                    msg = input("提交信息（回车默认 update）: ").strip()
                except (EOFError, KeyboardInterrupt):
                    msg = ""
            if not msg:
                msg = "update"
            git(["commit", "-m", msg])
        else:
            print("工作区无更改，跳过 commit")

    # 3. git push <remote> <branch>（最标准用法）
    push_cmd = ["push"]
    if opts["force"]:
        push_cmd.append("--force")
    push_cmd += [remote, branch]
    code = git(push_cmd)
    if code != 0:
        print("\n推送失败（退出码 %d），请检查网络/认证后重试" % code)
        return code

    print("\n推送完成: %s -> %s/%s" % (branch, remote, branch))
    return 0


if __name__ == "__main__":
    sys.exit(main())
