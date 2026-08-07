#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全网络通信模块
支持 TCP/UDP 双协议 + 加密 + 校验 + 防攻击
"""

import socket
import threading
import json
import time
import hashlib
import random
import struct
from typing import Dict, Any, Optional, Callable
from ASSET.game_data import draw_gradient_bg, cull_dead, get_font


class SecureNetwork:
    """安全网络通信类"""
    
    MAX_PACKET_SIZE = 4096  # 最大数据包大小
    ENCRYPT_KEY = b"ThreeKingdomsGame2024"  # 加密密钥
    
    def __init__(self, player_name: str = "玩家", protocol: str = "tcp"):
        self.player_name = player_name
        self.protocol = protocol.lower()
        self.socket = None
        self.connected = False
        self.running = False
        self.thread = None
        self.message_handler = None
        self.remote_addr = None
        self.player_id = self._generate_player_id()
        self.secret_key = None
    
    def _generate_player_id(self) -> str:
        """生成唯一玩家ID"""
        return hashlib.md5(f"{time.time()}{random.random()}".encode()).hexdigest()[:16]
    
    def _encrypt(self, data: bytes) -> bytes:
        """简单异或加密"""
        result = bytearray()
        for i, byte in enumerate(data):
            result.append(byte ^ self.ENCRYPT_KEY[i % len(self.ENCRYPT_KEY)])
        return bytes(result)
    
    def _decrypt(self, data: bytes) -> bytes:
        """解密（异或加密可逆）"""
        return self._encrypt(data)
    
    def _calculate_checksum(self, data: bytes) -> str:
        """计算数据校验和"""
        return hashlib.sha256(data).hexdigest()[:16]
    
    def _create_packet(self, message: Dict[str, Any]) -> bytes:
        """创建安全数据包"""
        try:
            data = json.dumps(message).encode('utf-8')
            
            if len(data) > self.MAX_PACKET_SIZE - 100:
                raise ValueError("数据包过大")
            
            checksum = self._calculate_checksum(data)
            
            packet = {
                'magic': 'SKYNET',
                'checksum': checksum,
                'data': data.decode('utf-8'),
                'timestamp': time.time(),
                'player_id': self.player_id
            }
            
            packet_data = json.dumps(packet).encode('utf-8')
            encrypted = self._encrypt(packet_data)
            
            if self.protocol == 'tcp':
                length = struct.pack('!I', len(encrypted))
                return length + encrypted
            else:
                return encrypted
                
        except Exception as e:
            print(f"创建数据包失败: {e}")
            return b''
    
    def _parse_packet(self, raw_data: bytes) -> Optional[Dict[str, Any]]:
        """解析并验证数据包"""
        try:
            decrypted = self._decrypt(raw_data)
            packet = json.loads(decrypted.decode('utf-8'))
            
            if packet.get('magic') != 'SKYNET':
                raise ValueError("无效的数据包标识")
            
            data = packet.get('data', '')
            if not data:
                raise ValueError("数据为空")
            
            expected_checksum = packet.get('checksum', '')
            actual_checksum = self._calculate_checksum(data.encode('utf-8'))
            
            if expected_checksum != actual_checksum:
                raise ValueError("校验和不匹配")
            
            message = json.loads(data)
            
            if time.time() - packet.get('timestamp', 0) > 30:
                raise ValueError("数据包过期")
            
            return message
            
        except Exception as e:
            print(f"解析数据包失败: {e}")
            return None
    
    def start_server(self, port: int = 4000, callback: Optional[Callable] = None):
        """启动服务器"""
        try:
            if self.protocol == 'tcp':
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.socket.bind(('0.0.0.0', port))
                self.socket.listen(5)
            else:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.socket.bind(('0.0.0.0', port))
            
            self.message_handler = callback
            self.running = True
            
            if self.protocol == 'tcp':
                self.thread = threading.Thread(target=self._tcp_server_loop, daemon=True)
            else:
                self.thread = threading.Thread(target=self._udp_server_loop, daemon=True)
            
            self.thread.start()
            print(f"✅ 安全服务器启动 ({self.protocol.upper()}): 0.0.0.0:{port}")
            return True
            
        except Exception as e:
            print(f"❌ 启动服务器失败: {e}")
            return False
    
    def _tcp_server_loop(self):
        """TCP服务器循环"""
        while self.running:
            try:
                self.socket.settimeout(1.0)
                conn, addr = self.socket.accept()
                conn.settimeout(30)
                print(f"🔗 客户端连接: {addr}")
                
                threading.Thread(target=self._handle_tcp_client, args=(conn, addr), daemon=True).start()
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"TCP服务器错误: {e}")
    
    def _handle_tcp_client(self, conn: socket.socket, addr: tuple):
        """处理TCP客户端"""
        buffer = b''
        while self.running:
            try:
                data = conn.recv(4096)
                if not data:
                    break
                
                buffer += data
                
                while len(buffer) >= 4:
                    length = struct.unpack('!I', buffer[:4])[0]
                    
                    if length > self.MAX_PACKET_SIZE:
                        print(f"⚠️ 数据包过大: {length}")
                        break
                    
                    if len(buffer) >= 4 + length:
                        packet_data = buffer[4:4+length]
                        buffer = buffer[4+length:]
                        
                        message = self._parse_packet(packet_data)
                        if message:
                            if self.message_handler:
                                self.message_handler(message, addr)
                    else:
                        break
                        
            except Exception as e:
                print(f"处理客户端错误: {e}")
                break
        
        conn.close()
        print(f"🔌 客户端断开: {addr}")
    
    def _udp_server_loop(self):
        """UDP服务器循环"""
        while self.running:
            try:
                self.socket.settimeout(1.0)
                data, addr = self.socket.recvfrom(self.MAX_PACKET_SIZE)
                
                if len(data) > self.MAX_PACKET_SIZE:
                    print(f"⚠️ 收到超大UDP数据包: {len(data)}")
                    continue
                
                message = self._parse_packet(data)
                if message:
                    if self.message_handler:
                        self.message_handler(message, addr)
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"UDP服务器错误: {e}")
    
    def connect(self, host: str, port: int) -> bool:
        """连接到服务器"""
        try:
            if self.protocol == 'tcp':
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(5)
                self.socket.connect((host, port))
            else:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            self.remote_addr = (host, port)
            self.connected = True
            
            self.running = True
            if self.protocol == 'tcp':
                self.thread = threading.Thread(target=self._tcp_client_loop, daemon=True)
                self.thread.start()
            
            print(f"✅ 已连接到 {host}:{port} ({self.protocol.upper()})")
            return True
            
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def _tcp_client_loop(self):
        """TCP客户端循环"""
        buffer = b''
        while self.running and self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    self.connected = False
                    break
                
                buffer += data
                
                while len(buffer) >= 4:
                    length = struct.unpack('!I', buffer[:4])[0]
                    
                    if length > self.MAX_PACKET_SIZE:
                        print(f"⚠️ 数据包过大")
                        break
                    
                    if len(buffer) >= 4 + length:
                        packet_data = buffer[4:4+length]
                        buffer = buffer[4+length:]
                        
                        message = self._parse_packet(packet_data)
                        if message:
                            if self.message_handler:
                                self.message_handler(message, ('server', 0))
                    else:
                        break
                        
            except Exception as e:
                if self.running:
                    print(f"TCP客户端错误: {e}")
                    self.connected = False
    
    def send(self, message: Dict[str, Any]) -> bool:
        """发送消息"""
        try:
            if not self.socket:
                print("❌ 未初始化socket")
                return False
            
            packet = self._create_packet(message)
            if not packet:
                return False
            
            if self.protocol == 'tcp':
                if self.connected:
                    self.socket.sendall(packet)
            else:
                if self.remote_addr:
                    self.socket.sendto(packet, self.remote_addr)
                else:
                    print("❌ 未设置目标地址")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ 发送失败: {e}")
            return False
    
    def send_chat(self, text: str):
        """发送聊天消息"""
        return self.send({
            'type': 'chat',
            'player_id': self.player_id,
            'player_name': self.player_name,
            'text': text,
            'timestamp': time.time()
        })
    
    def send_battle_action(self, action: Dict[str, Any]):
        """发送战斗动作"""
        return self.send({
            'type': 'battle_action',
            'player_id': self.player_id,
            'action': action,
            'timestamp': time.time()
        })
    
    def get_local_ip(self) -> str:
        """获取本地IP"""
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
        if self.socket:
            try:
                self.socket.close()
            except Exception as _e:
                logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)
        print("🛑 安全网络模块已停止")


# 测试代码
def test_secure_network():
    print("=== 安全网络模块测试 ===")
    
    def handle_message(msg, addr):
        print(f"\n📨 收到消息: {msg}")
    
    # 创建TCP服务器
    server = SecureNetwork("服务器玩家", protocol="tcp")
    server.start_server(4000, handle_message)
    
    # 创建TCP客户端
    client = SecureNetwork("客户端玩家", protocol="tcp")
    client.connect('127.0.0.1', 4000)
    
    time.sleep(0.5)
    
    # 发送消息
    print("\n发送聊天消息...")
    client.send_chat("Hello, 这是加密消息！")
    
    print("\n发送战斗动作...")
    client.send_battle_action({'skill': '青龙偃月斩', 'damage': 100})
    
    time.sleep(1)
    
    server.stop()
    client.stop()
    print("\n测试完成！")


if __name__ == "__main__":
    test_secure_network()
