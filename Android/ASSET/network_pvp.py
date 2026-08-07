#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络对战模块 - 实现真正的P2P UDP通信
支持玩家匹配、对战同步、消息传输
"""

import socket
import threading
import json
import time
import random
from typing import Optional, Dict, Any, Callable
from ASSET.game_data import draw_gradient_bg, cull_dead, get_font


class NetworkPVP:
    """网络对战类"""
    
    def __init__(self, player_name: str = "玩家"):
        self.player_name = player_name
        self.local_port = 4000
        self.remote_port = 4000
        self.remote_ip = None
        self.sock = None
        self.running = False
        self.thread = None
        self.message_handler = None
        self.connected = False
        self.game_state = {}
        self.player_id = str(random.randint(10000, 99999))
        
    def start_server(self, port: int = 4000, message_callback: Optional[Callable] = None):
        """启动UDP服务器"""
        try:
            self.local_port = port
            self.message_handler = message_callback
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind(('0.0.0.0', port))
            self.running = True
            self.thread = threading.Thread(target=self._server_loop, daemon=True)
            self.thread.start()
            print(f"✅ UDP服务器启动成功，端口: {port}")
            return True
        except Exception as e:
            print(f"❌ 服务器启动失败: {e}")
            return False
    
    def _server_loop(self):
        """服务器主循环"""
        while self.running:
            try:
                self.sock.settimeout(1.0)
                data, addr = self.sock.recvfrom(4096)
                self._handle_message(data, addr)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"接收错误: {e}")
    
    def _handle_message(self, data: bytes, addr: tuple):
        """处理接收到的消息"""
        try:
            message = json.loads(data.decode('utf-8'))
            msg_type = message.get('type', '')
            
            if self.message_handler:
                self.message_handler(message, addr)
            else:
                print(f"收到消息: {message} from {addr}")
                
        except Exception as e:
            print(f"解析消息失败: {e}")
    
    def send_message(self, ip: str, port: int, message: Dict[str, Any]):
        """发送UDP消息"""
        try:
            if not self.sock:
                print("❌ 未初始化socket")
                return False
                
            data = json.dumps(message).encode('utf-8')
            self.sock.sendto(data, (ip, port))
            return True
        except Exception as e:
            print(f"❌ 发送失败: {e}")
            return False
    
    def connect_to_player(self, ip: str, port: int):
        """连接到其他玩家"""
        try:
            self.remote_ip = ip
            self.remote_port = port
            self.connected = True
            
            # 发送连接请求
            self.send_message(ip, port, {
                'type': 'connect',
                'player_id': self.player_id,
                'player_name': self.player_name,
                'timestamp': time.time()
            })
            print(f"✅ 已连接到 {ip}:{port}")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def send_battle_action(self, action: Dict[str, Any]):
        """发送战斗动作"""
        if self.connected and self.remote_ip:
            message = {
                'type': 'battle_action',
                'player_id': self.player_id,
                'action': action,
                'timestamp': time.time()
            }
            return self.send_message(self.remote_ip, self.remote_port, message)
        return False
    
    def send_chat(self, text: str):
        """发送聊天消息"""
        if self.connected and self.remote_ip:
            message = {
                'type': 'chat',
                'player_id': self.player_id,
                'player_name': self.player_name,
                'text': text,
                'timestamp': time.time()
            }
            return self.send_message(self.remote_ip, self.remote_port, message)
        return False
    
    def get_local_ip(self) -> str:
        """获取本地IP地址"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as _e:
            return '127.0.0.1'
    
    def stop(self):
        """停止网络通信"""
        self.running = False
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except Exception as _e:
                logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        print("🛑 网络模块已停止")


# 测试代码
if __name__ == "__main__":
    print("=== 网络对战测试 ===")
    
    def test_handler(msg, addr):
        print(f"📨 来自 {addr}: {msg}")
    
    # 创建玩家1（服务器）
    player1 = NetworkPVP("刘备")
    player1.start_server(4000, test_handler)
    
    # 创建玩家2（客户端）
    player2 = NetworkPVP("关羽")
    player2.start_server(4001, test_handler)
    
    print(f"\n玩家1 IP: {player1.get_local_ip()}:4000")
    print(f"玩家2 IP: {player2.get_local_ip()}:4001\n")
    
    # 测试消息发送
    print("玩家2 连接到 玩家1...")
    player2.connect_to_player('127.0.0.1', 4000)
    
    time.sleep(0.5)
    
    print("\n玩家1 发送消息...")
    player1.send_message('127.0.0.1', 4001, {
        'type': 'chat',
        'text': '二弟，我们来切磋一下！'
    })
    
    time.sleep(0.5)
    
    print("\n玩家2 发送战斗动作...")
    player2.send_battle_action({
        'skill': '青龙偃月斩',
        'damage': 100
    })
    
    time.sleep(1)
    
    player1.stop()
    player2.stop()
    print("\n测试完成！")
