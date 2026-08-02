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
        except:
            return '127.0.0.1'
    
    def stop(self):
        """停止网络通信"""
        self.running = False
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
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


def main():
    """网络对战模块主界面"""
    try:
        import pygame
        from ASSET.game_data import data, get_system_font_name
        
        if not pygame.get_init():
            pygame.init()
        
        resolution = data.get('settings', {}).get('graphics', {}).get('resolution', '800x600')
        try:
            width, height = map(int, resolution.split('x'))
        except ValueError:
            width, height = 800, 600
        
        screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("🌐 网络对战")
        clock = pygame.time.Clock()
        
        font_name = get_system_font_name()
        try:
            font_big = pygame.font.SysFont(font_name, 36)
            font_main = pygame.font.SysFont(font_name, 26)
            font_small = pygame.font.SysFont(font_name, 20)
        except Exception:
            font_big = pygame.font.Font(None, 36)
            font_main = pygame.font.Font(None, 26)
            font_small = pygame.font.Font(None, 20)
        
        player_name = data.get('player_name', '主公')
        
        class Button:
            def __init__(self, text, x, y, w, h, font, color=(100,100,150), hover_color=(120,120,180)):
                self.text, self.x, self.y, self.w, self.h = text, x, y, w, h
                self.font, self.color, self.hover_color = font, color, hover_color
                self.hovered = False
            
            def draw(self, screen):
                col = self.hover_color if self.hovered else self.color
                pygame.draw.rect(screen, col, (self.x, self.y, self.w, self.h), border_radius=8)
                pygame.draw.rect(screen, (255, 215, 0), (self.x, self.y, self.w, self.h), 2, border_radius=8)
                text = self.font.render(self.text, True, (255,255,255))
                screen.blit(text, (self.x + self.w//2 - text.get_width()//2, self.y + self.h//2 - text.get_height()//2))
            
            def check(self, mx, my):
                return self.x <= mx <= self.x + self.w and self.y <= my <= self.y + self.h
        
        buttons = [
            Button("🎮 创建房间", width//2 - 150, height//2 - 80, 300, 50, font_main, (70,200,80), (90,220,100)),
            Button("🔍 搜索对手", width//2 - 150, height//2, 300, 50, font_main, (80,150,230), (100,170,250)),
            Button("📡 局域网对战", width//2 - 150, height//2 + 80, 300, 50, font_main, (160,80,220), (180,100,240)),
            Button("⏎ 返回", width//2 - 100, height - 50, 200, 40, font_main),
        ]
        
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            
            for y in range(height):
                ratio = y / height
                r = int(10 + (25-10) * ratio)
                g = int(15 + (35-15) * ratio)
                b = int(30 + (55-30) * ratio)
                pygame.draw.line(screen, (r, g, b), (0, y), (width, y))
            
            title = font_big.render("🌐 网络对战大厅", True, (255,215,0))
            screen.blit(title, (width//2 - title.get_width()//2, 40))
            
            info = font_small.render(f"玩家: {player_name}", True, (200,200,200))
            screen.blit(info, (20, 20))
            
            for btn in buttons:
                btn.hovered = btn.check(mx, my)
                btn.draw(screen)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for btn in buttons:
                        if btn.check(mx, my):
                            if btn.text == "⏎ 返回":
                                running = False
                            else:
                                msg = font_main.render(f"{btn.text}功能开发中...", True, (255,215,0))
                                screen.blit(msg, (width//2 - msg.get_width()//2, height//2 - 150))
                                pygame.display.flip()
                                pygame.time.wait(2000)
            
            pygame.display.flip()
            clock.tick(30)
        
        pygame.display.quit()
        pygame.mixer.quit()
    
    except Exception as e:
        print(f"网络对战错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
