#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 推送工具（纯 Python 标准库，零第三方依赖）
- 列出远程仓库、本地分支、远程分支，交互式选择后推送
- 认证复用已配置好的 SSH 密钥/令牌，本工具不做任何认证处理
用法:
    python git_push_tool.py
    python git_push_tool.py --remote origin        # 指定远程，跳过选择
    python git_push_tool.py --force                # 强制推送
    python git_push_tool.py --upstream             # 推送后设置上游跟踪
"""
import os
import subprocess
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

REPO_DIR = os.path.dirname(os.path.abspath(__file__))


def run(args, capture=True, timeout=None):
    """运行 git 命令，capture=True 返回 (code, out, err)，否则实时显示输出"""
    try:
        if capture:
            p = subprocess.run(args, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", cwd=REPO_DIR,
                               timeout=timeout)
            return p.returncode, p.stdout.strip(), p.stderr.strip()
        p = subprocess.run(args, encoding="utf-8", errors="replace", cwd=REPO_DIR)
        return p.returncode, "", ""
    except subprocess.TimeoutExpired:
        return -2, "", "连接超时（超过 %s 秒），请检查网络/代理" % timeout
    except FileNotFoundError:
        print("错误: 未找到 git 命令，请先安装 Git 并加入 PATH")
        sys.exit(1)


def pick(items, prompt, allow_new=False):
    """打印编号列表让用户选择；allow_new=True 时输入非编号视为新输入值"""
    if not items:
        return None
    for i, item in enumerate(items, 1):
        print("[%d] %s" % (i, item))
    while True:
        try:
            v = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if not v:
            return None
        if v.isdigit():
            n = int(v)
            if 1 <= n <= len(items):
                return items[n - 1]
            print("编号超出范围，请重试")
            continue
        if allow_new:
            return v
        print("请输入列表中的编号")


def list_remote_branches(remote):
    """列出远程实际存在的分支名列表（15 秒超时）"""
    code, out, err = run(["git", "ls-remote", "--heads", remote], timeout=15)
    if code != 0:
        print("获取远程分支失败（若是网络/认证问题，请检查已配置的令牌）:")
        print(err or out)
        return None
    return [ln.split("refs/heads/")[-1] for ln in out.splitlines() if "refs/heads/" in ln]


def main():
    args = sys.argv[1:]
    force = "--force" in args
    upstream = "--upstream" in args
    preset_remote = None
    if "--remote" in args:
        preset_remote = args[args.index("--remote") + 1]

    # 1. 选择远程
    if preset_remote:
        remote = preset_remote
        print("使用远程: %s" % remote)
    else:
        code, out, err = run(["git", "remote"])
        if code != 0:
            print("获取远程列表失败: %s" % (err or out))
            return 1
        remotes = [r for r in out.splitlines() if r]
        if not remotes:
            print("错误: 当前仓库没有配置远程仓库")
            return 1
        if len(remotes) == 1:
            remote = remotes[0]
            print("使用远程: %s" % remote)
        else:
            remote = pick(remotes, "请选择远程编号: ")
            if not remote:
                return 0

    # 2. 选择本地分支
    code, out, err = run(["git", "branch", "--no-color", "--list"])
    locals_ = []
    for line in out.splitlines():
        name = line.strip()
        if name.startswith("*"):
            name = name[1:].strip()
        if name:
            locals_.append(name)
    if not locals_:
        print("错误: 没有本地分支")
        return 1
    print("\n本地分支:")
    local_branch = pick(locals_, "请选择要推送的本地分支编号: ")
    if not local_branch:
        return 0

    # 3. 选择远程分支（可直接输入新分支名以新建）
    remote_branches = list_remote_branches(remote)
    if remote_branches is None:
        return 1
    print("\n远程分支:")
    if not remote_branches:
        print("（远程暂无分支，将直接新建）")
    target = pick(remote_branches, "请选择目标远程分支编号（或直接输入新分支名）: ", allow_new=True)
    if not target:
        return 0

    # 4. 确认并推送
    cmd = "git push%s %s %s:%s" % (" --force" if force else "", remote, local_branch, target)
    print("\n将执行: %s" % cmd)
    try:
        confirm = input("确认推送? (y/N): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n已取消")
        return 0
    if confirm not in ("y", "yes"):
        print("已取消")
        return 0

    push_args = ["git", "push"]
    if force:
        push_args.append("--force")
    push_args += [remote, "%s:%s" % (local_branch, target)]
    print("\n推送中...")
    code, out, err = run(push_args, timeout=180)
    if out:
        print(out)
    if err:
        print(err)
    if code != 0:
        print("推送失败，退出码 %d" % code)
        return code

    if upstream:
        run(["git", "branch", "--set-upstream-to=%s/%s" % (remote, target), local_branch])
        print("已设置上游跟踪: %s/%s" % (remote, target))
    print("推送完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
