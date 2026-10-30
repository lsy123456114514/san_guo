#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
世界聊天 · 配套服务器（UDP 广播）

和 ASSET/world_chat.py 的 ChatClient 配套：
  join/leave/ping    玩家进出与保活
  chat               聊天消息（原样广播给所有在线玩家）
  player_list        周期性下发在线名单
  history            新玩家加入时补发最近历史

用法：
  py ASSET/chat_server.py            # 默认端口 9999
  py ASSET/chat_server.py 8888       # 指定端口

启动后保持窗口开着即可；游戏内世界聊天连 127.0.0.1:9999（或本机局域网 IP）。
"""

import json
import socket
import sys
import time
from datetime import datetime

HOST = "0.0.0.0"
DEFAULT_PORT = 9999
PLAYER_TTL = 15.0        # 超过这么久没 ping 视为掉线
HISTORY_MAX = 60
PLAYER_LIST_INTERVAL = 3.0


def ts() -> float:
    return time.time()


def now_str() -> str:
    return datetime.now().strftime("%H:%M:%S")


def main() -> int:
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"端口无效：{sys.argv[1]}，使用默认 {DEFAULT_PORT}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((HOST, port))
    except OSError as e:
        print(f"[启动失败] 端口 {port} 被占用：{e}")
        return 1
    sock.settimeout(0.5)

    players: dict[str, dict] = {}     # player_id -> {name, addr, last}
    history: list[dict] = []          # 最近聊天记录
    last_list_ts = 0.0
    print(f"[世界聊天服务器] 已启动  UDP {HOST}:{port}   {now_str()}")
    print("关闭此窗口或 Ctrl+C 即可停服。")

    def broadcast(payload: dict, exclude: str | None = None) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        for pid, info in list(players.items()):
            if pid == exclude:
                continue
            try:
                sock.sendto(raw, info["addr"])
            except OSError:
                pass

    def push_player_list() -> None:
        broadcast({"type": "player_list",
                   "players": [{"id": pid, "name": info["name"]}
                               for pid, info in players.items()]})

    try:
        while True:
            # 周期任务：在线名单 + 掉线清理
            now = ts()
            if now - last_list_ts >= PLAYER_LIST_INTERVAL:
                last_list_ts = now
                gone = [pid for pid, info in players.items()
                        if now - info["last"] > PLAYER_TTL]
                for pid in gone:
                    name = players.pop(pid)["name"]
                    line = f"{name} 离开了聊天室"
                    print(f"  [{now_str()}] - {line}")
                    history.append({"type": "system", "text": line,
                                    "timestamp": ts()})
                    if len(history) > HISTORY_MAX * 2:
                        del history[:HISTORY_MAX]
                    broadcast({"type": "system", "text": line, "timestamp": ts()})
                if players:
                    push_player_list()

            try:
                raw, addr = sock.recvfrom(8192)
            except socket.timeout:
                continue
            except OSError:
                continue

            try:
                msg = json.loads(raw.decode("utf-8"))
            except Exception:
                continue

            mtype = msg.get("type", "")
            pid = str(msg.get("player_id", ""))

            if mtype == "join":
                name = str(msg.get("player_name", "无名"))[:16]
                is_back = pid in players
                players[pid] = {"name": name, "addr": addr, "last": ts()}
                print(f"  [{now_str()}] + {name} 加入（{addr[0]}）在线 {len(players)}")
                line = f"{name} 进入了聊天室"
                # 进出事件也进历史：后来的人能看到谁在何时进过房间
                history.append({"type": "system", "text": line,
                                "timestamp": ts()})
                if len(history) > HISTORY_MAX * 2:
                    del history[:HISTORY_MAX]
                broadcast({"type": "system", "text": line, "timestamp": ts()},
                          exclude=pid if not is_back else None)
                # 补发历史 + 名单
                try:
                    sock.sendto(json.dumps(
                        {"type": "history", "messages": history[-HISTORY_MAX:]},
                        ensure_ascii=False).encode("utf-8"), addr)
                    push_player_list()
                except OSError:
                    pass

            elif mtype == "leave":
                info = players.pop(pid, None)
                if info:
                    print(f"  [{now_str()}] - {info['name']} 离开（主动）在线 {len(players)}")
                    line = f"{info['name']} 离开了聊天室"
                    history.append({"type": "system", "text": line,
                                    "timestamp": ts()})
                    if len(history) > HISTORY_MAX * 2:
                        del history[:HISTORY_MAX]
                    broadcast({"type": "system", "text": line,
                               "timestamp": ts()})

            elif mtype == "ping":
                if pid in players:
                    players[pid]["last"] = ts()
                    players[pid]["addr"] = addr

            elif mtype == "chat":
                info = players.get(pid)
                if info is None:
                    # 没报到的玩家也算加入，避免消息被丢
                    info = players.setdefault(pid, {
                        "name": str(msg.get("player_name", "无名"))[:16],
                        "addr": addr, "last": ts()})
                info["last"] = ts()
                text = str(msg.get("text", "")).strip()[:200]
                if not text:
                    continue
                record = {"type": "chat", "player_id": pid,
                          "player_name": info["name"], "text": text,
                          "timestamp": ts()}
                history.append(record)
                if len(history) > HISTORY_MAX * 2:
                    del history[:HISTORY_MAX]
                print(f"  [{now_str()}] {info['name']}: {text}")
                broadcast(record)

            elif mtype == "system":
                # 客户端一般不发 system；原样广播以便扩展
                broadcast(msg)

    except KeyboardInterrupt:
        print(f"\n[世界聊天服务器] 手动停止 {now_str()}")
    finally:
        sock.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
