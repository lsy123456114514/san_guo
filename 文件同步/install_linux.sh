#!/usr/bin/env bash
# install_linux.sh — 在 Linux 上安装“文件同步客户端”为开机自启
# 用法:
#   sudo ./install_linux.sh /path/to/config.client.json
set -euo pipefail

CFG_SRC="${1:-}"
if [ -z "$CFG_SRC" ] || [ ! -f "$CFG_SRC" ]; then
    echo "用法: sudo $0 /path/to/config.client.json"
    exit 1
fi

APP_DIR=/opt/file-sync
CFG_DIR=/etc/file-sync
HERE="$(cd "$(dirname "$0")" && pwd)"

command -v python3 >/dev/null || { echo "缺少 python3，请先安装"; exit 1; }

echo "[1/4] 部署程序到 $APP_DIR"
install -d "$APP_DIR" "$CFG_DIR"
install -m 0644 "$HERE/sync_client.py" "$APP_DIR/sync_client.py"

echo "[2/4] 部署配置到 $CFG_DIR/config.client.json"
install -m 0644 "$CFG_SRC" "$CFG_DIR/config.client.json"

echo "[3/4] 安装 systemd 单元"
install -m 0644 "$HERE/autosync.service" /etc/systemd/system/autosync.service
install -m 0644 "$HERE/autosync.timer"   /etc/systemd/system/autosync.timer
systemctl daemon-reload

echo "[4/4] 启用开机自启 + 立即跑一次"
systemctl enable --now autosync.timer
systemctl start autosync.service || true

echo ""
echo "完成。查看状态:"
echo "  systemctl status autosync.service"
echo "  journalctl -u autosync.service -n 50"
echo "  或看日志文件（config 里的 log_file）"
