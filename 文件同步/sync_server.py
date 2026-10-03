#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文件同步 - Windows 端服务

在 Windows 上常驻，对外提供：
  HEAD /file          -> 返回当前指定文件的 SHA256（客户端用来判断是否变化）
  GET  /file          -> 下载当前指定文件
  PUT  /backup/<名字>  -> 接收 Linux 回传的旧版备份 zip

所有请求都要带 HTTP 头 X-Token，值和配置里的 token 一致。
只依赖 Python 标准库。建议配合 Tailscale 使用（私网直连）。
"""

import argparse
import hashlib
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def sha256_file(path, buf=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(buf), b""):
            h.update(chunk)
    return h.hexdigest()


class Handler(BaseHTTPRequestHandler):
    server_version = "FileSync/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("[server] " + (fmt % args) + "\n")

    def _auth(self):
        if self.headers.get("X-Token", "") != self.server.token:
            self.send_response(401)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return False
        return True

    def _end(self, code):
        self.send_response(code)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_HEAD(self):
        if not self._auth():
            return
        if self.path.rstrip("/") != "/file":
            return self._end(404)
        p = self.server.share_file
        if not os.path.isfile(p):
            return self._end(404)
        st = os.stat(p)
        self.send_response(200)
        self.send_header("X-SHA256", sha256_file(p))
        self.send_header("X-Size", str(st.st_size))
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        if not self._auth():
            return
        if self.path.rstrip("/") != "/file":
            return self._end(404)
        p = self.server.share_file
        if not os.path.isfile(p):
            return self._end(404)
        data = open(p, "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("X-SHA256", hashlib.sha256(data).hexdigest())
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_PUT(self):
        if not self._auth():
            return
        if not self.path.startswith("/backup/"):
            return self._end(404)
        name = os.path.basename(self.path[len("/backup/"):])
        if not name or name in (".", ".."):
            return self._end(400)
        length = int(self.headers.get("Content-Length", "0"))
        os.makedirs(self.server.backup_dir, exist_ok=True)
        dst = os.path.join(self.server.backup_dir, name)
        remaining = length
        with open(dst, "wb") as f:
            while remaining > 0:
                chunk = self.rfile.read(min(1 << 20, remaining))
                if not chunk:
                    break
                f.write(chunk)
                remaining -= len(chunk)
        sys.stderr.write("[server] 收到备份: %s (%d bytes)\n" % (dst, length))
        self._end(200)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="config.server.json 路径")
    args = ap.parse_args()

    with open(args.config, encoding="utf-8-sig") as f:
        cfg = json.load(f)["server"]

    bind = cfg.get("bind", "0.0.0.0")
    port = int(cfg["port"])
    httpd = ThreadingHTTPServer((bind, port), Handler)
    httpd.token = cfg["token"]
    httpd.share_file = cfg["share_file"]
    httpd.backup_dir = cfg["backup_dir"]

    print("[server] 共享文件: %s" % httpd.share_file)
    print("[server] 备份目录: %s" % httpd.backup_dir)
    print("[server] 监听 %s:%d" % (bind, port))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
