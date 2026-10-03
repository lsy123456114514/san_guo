#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文件同步 - Linux 端客户端

开机（或定时）运行时：
  1. 问 Windows 服务端当前指定文件的 SHA256
  2. 和本地文件比较
  3. 若不同：把本地旧版存成带日期的 zip，回传到 Windows，再下载新文件覆盖本地
  4. 若相同：什么都不做

只依赖 Python 标准库（urllib / zipfile / hashlib）。
"""

import argparse
import datetime
import hashlib
import json
import os
import shutil
import sys
import time
import urllib.request
import zipfile

LOG_PATH = None


def sha256_file(path, buf=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(buf), b""):
            h.update(chunk)
    return h.hexdigest()


def log(msg):
    line = "[%s] %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line)
    if LOG_PATH:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(LOG_PATH)), exist_ok=True)
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass


def http(method, url, token, data=None, timeout=30):
    req = urllib.request.Request(url, method=method, data=data)
    req.add_header("X-Token", token)
    if data is not None:
        req.add_header("Content-Type", "application/octet-stream")
    return urllib.request.urlopen(req, timeout=timeout)


def main():
    global LOG_PATH
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="config.client.json 路径")
    ap.add_argument("--dry-run", action="store_true", help="只检查不写入")
    args = ap.parse_args()

    with open(args.config, encoding="utf-8-sig") as f:
        cfg = json.load(f)["client"]

    base = cfg["server_url"].rstrip("/")
    token = cfg["token"]
    local = cfg["local_file"]
    local_bak = cfg["local_backup_dir"]
    timeout = int(cfg.get("timeout", 120))
    retries = int(cfg.get("retries", 5))
    LOG_PATH = cfg.get("log_file") or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "sync.log")

    # ---- 1. 连接并取远端 hash（带重试，供开机网络未就绪时兜底）----
    remote_sha = None
    for i in range(retries):
        try:
            r = http("HEAD", base + "/file", token, timeout=20)
            remote_sha = r.headers.get("X-SHA256")
            break
        except Exception as e:
            log("连接 Windows 失败（%d/%d）：%s" % (i + 1, retries, e))
            if i + 1 < retries:
                time.sleep(3)
    if remote_sha is None:
        log("放弃：无法读取远端文件（服务端未启动或网络不通）")
        return 1

    local_sha = sha256_file(local) if os.path.isfile(local) else None
    log("远端=%s 本地=%s" % (remote_sha[:12], (local_sha or "无")[:12]))

    if local_sha == remote_sha:
        log("一致，无需同步")
        return 0

    if args.dry_run:
        log("[dry-run] 检测到差异，正式运行会：备份本地旧版 -> 回传 zip -> 下载覆盖")
        return 0

    os.makedirs(os.path.dirname(os.path.abspath(local)), exist_ok=True)
    os.makedirs(local_bak, exist_ok=True)

    # ---- 2. 本地旧版打包为带日期 zip 并回传 Windows ----
    if os.path.isfile(local):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = os.path.splitext(os.path.basename(local))[0]
        zip_name = "%s_%s.zip" % (stem, ts)
        zip_path = os.path.join(local_bak, zip_name)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(local, arcname=os.path.basename(local))
        log("本地旧版已打包：%s" % zip_path)
        with open(zip_path, "rb") as f:
            payload = f.read()
        try:
            http("PUT", base + "/backup/" + zip_name, token, data=payload, timeout=timeout)
            log("备份 zip 已回传 Windows：%s" % zip_name)
        except Exception as e:
            log("回传 zip 失败（保留在本地）：%s" % e)
    else:
        log("本地无文件，直接下载（无需备份）")

    # ---- 3. 下载远端文件（临时文件 + 原子替换）----
    tmp = local + ".synctmp"
    try:
        r = http("GET", base + "/file", token, timeout=timeout)
        with open(tmp, "wb") as f:
            shutil.copyfileobj(r, f)
    except Exception as e:
        log("下载失败：%s" % e)
        if os.path.exists(tmp):
            os.remove(tmp)
        return 2

    got = sha256_file(tmp)
    if got != remote_sha:
        os.remove(tmp)
        log("下载校验失败：期望 %s 实得 %s" % (remote_sha, got))
        return 2

    os.replace(tmp, local)
    log("本地文件已更新：%s" % local)
    return 0


if __name__ == "__main__":
    sys.exit(main())
