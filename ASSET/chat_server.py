#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
世界聊天中央服务器
用于转发玩家消息，实现全球聊天功能
支持多房间、消息广播、玩家列表
"""

import socket
import sys
import threading
import json
import time
from typing import Dict, List, Any, Set


class ChatServer:
    """世界聊天服务器"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 5000):
        self.host = host
        self.port = port
        self.sock = None
        self.running = False
        self.thread = None
        
        self.players: Dict[str, Dict] = {}  # {player_id: {name, addr, last_seen}}
        self.rooms: Dict[str, Set[str]] = {'world': set()}  # {room_name: {player_id}}
        self.message_history: List[Dict] = []
        self.max_history = 100
    
    def start(self):
        """启动服务器"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((self.host, self.port))
            self.running = True
            self.thread = threading.Thread(target=self._server_loop, daemon=True)
            self.thread.start()
            
            print("="*60)
            print("🌍 三国游戏 - 世界聊天服务器")
            print("="*60)
            print(f"✅ 服务器已启动: {self.host}:{self.port}")
            print("等待玩家连接...\n")
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
                self._cleanup_players()
            except Exception as e:
                if self.running:
                    print(f"服务器错误: {e}")
    
    def _handle_message(self, data: bytes, addr: tuple):
        """处理客户端消息"""
        try:
            message = json.loads(data.decode('utf-8'))
            msg_type = message.get('type', '')
            player_id = message.get('player_id', '')
            
            if msg_type == 'join':
                self._player_join(message, addr)
            elif msg_type == 'leave':
                self._player_leave(player_id)
            elif msg_type == 'chat':
                self._broadcast_chat(message)
            elif msg_type == 'get_players':
                self._send_player_list(player_id, addr)
            elif msg_type == 'ping':
                self._update_player_seen(player_id)
            
        except Exception as e:
            print(f"解析消息失败: {e}")
    
    def _player_join(self, message: Dict, addr: tuple):
        """玩家加入"""
        player_id = message.get('player_id', '')
        player_name = message.get('player_name', '匿名玩家')
        
        self.players[player_id] = {
            'name': player_name,
            'addr': addr,
            'last_seen': time.time()
        }
        
        self.rooms['world'].add(player_id)
        
        print(f"👋 {player_name} ({player_id}) 加入世界聊天")
        
        self._broadcast_system(f"{player_name} 进入了世界聊天")
        self._send_history(player_id, addr)
        self._broadcast_player_list()
    
    def _player_leave(self, player_id: str):
        """玩家离开"""
        if player_id in self.players:
            player_name = self.players[player_id]['name']
            print(f"👋 {player_name} ({player_id}) 离开")
            
            self._broadcast_system(f"{player_name} 离开了")
            
            del self.players[player_id]
            for room in self.rooms:
                if player_id in self.rooms[room]:
                    self.rooms[room].remove(player_id)
            
            self._broadcast_player_list()
    
    def _broadcast_chat(self, message: Dict):
        """广播聊天消息"""
        player_id = message.get('player_id', '')
        if player_id not in self.players:
            return
        
        message['timestamp'] = time.time()
        self.message_history.append(message)
        
        if len(self.message_history) > self.max_history:
            self.message_history.pop(0)
        
        for pid, pdata in self.players.items():
            self._send_to(pdata['addr'], message)
    
    def _broadcast_system(self, text: str):
        """广播系统消息"""
        message = {
            'type': 'system',
            'text': text,
            'timestamp': time.time()
        }
        self.message_history.append(message)
        
        if len(self.message_history) > self.max_history:
            self.message_history.pop(0)
        
        for pid, pdata in self.players.items():
            self._send_to(pdata['addr'], message)
    
    def _broadcast_player_list(self):
        """广播玩家列表"""
        player_list = [
            {'id': pid, 'name': pdata['name']}
            for pid, pdata in self.players.items()
        ]
        
        message = {
            'type': 'player_list',
            'players': player_list
        }
        
        for pid, pdata in self.players.items():
            self._send_to(pdata['addr'], message)
    
    def _send_history(self, player_id: str, addr: tuple):
        """发送历史消息给新玩家"""
        message = {
            'type': 'history',
            'messages': self.message_history[-50:]
        }
        self._send_to(addr, message)
    
    def _send_player_list(self, player_id: str, addr: tuple):
        """发送玩家列表"""
        player_list = [
            {'id': pid, 'name': pdata['name']}
            for pid, pdata in self.players.items()
        ]
        
        message = {
            'type': 'player_list',
            'players': player_list
        }
        self._send_to(addr, message)
    
    def _update_player_seen(self, player_id: str):
        """更新玩家最后在线时间"""
        if player_id in self.players:
            self.players[player_id]['last_seen'] = time.time()
    
    def _cleanup_players(self):
        """清理超时玩家"""
        timeout = 30
        current_time = time.time()
        
        to_remove = []
        for pid, pdata in self.players.items():
            if current_time - pdata['last_seen'] > timeout:
                to_remove.append(pid)
        
        for pid in to_remove:
            self._player_leave(pid)
    
    def _send_to(self, addr: tuple, message: Dict):
        """发送消息到指定地址"""
        try:
            data = json.dumps(message).encode('utf-8')
            self.sock.sendto(data, addr)
        except Exception as e:
            print(f"发送失败: {e}")
    
    def stop(self):
        """停止服务器"""
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        print("\n🛑 服务器已停止")


def main():
    import sys
    
    host = '0.0.0.0'
    port = 5000
    
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    server = ChatServer(host, port)
    
    if server.start():
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            server.stop()


if __name__ == "__main__":
    main()
