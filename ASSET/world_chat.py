#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
世界聊天客户端
精美PyGame界面，支持全球聊天
"""

import os
import pygame
import random
import math
import time
import socket
import json
import threading
from typing import List, Dict, Optional
from ASSET.game_data import data, save, get_system_font_name

# 颜色主题
COLORS = {
    "bg_dark": (12, 18, 30),
    "bg_panel": (25, 35, 55),
    "bg_input": (35, 45, 70),
    "accent_gold": (255, 191, 0),
    "accent_red": (230, 70, 70),
    "accent_green": (70, 200, 70),
    "accent_blue": (80, 150, 220),
    "text_white": (240, 240, 240),
    "text_gray": (150, 160, 180),
    "system": (150, 200, 255),
    "player_other": (120, 200, 150),
    "player_self": (255, 210, 100),
}


class Particle:
    def __init__(self, x, y, color, speed, size, life):
        self.x = x
        self.y = y
        self.color = color
        self.speed_x = random.uniform(-speed, speed)
        self.speed_y = random.uniform(-speed, speed)
        self.size = size
        self.life = life
        self.max_life = life
    
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.life -= 1
        self.size = max(0.5, self.size - 0.05)
    
    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life)) if self.max_life > 0 else 0
        temp_surface = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(temp_surface, (*self.color, alpha), (int(self.size), int(self.size)), int(self.size))
        surface.blit(temp_surface, (int(self.x - self.size), int(self.y - self.size)))


class ChatMessage:
    def __init__(self, text: str, sender: str = "系统", msg_type: str = "system", timestamp: float = 0):
        self.text = text
        self.sender = sender
        self.type = msg_type
        self.timestamp = timestamp if timestamp else time.time()
        self.y_offset = 0
        self.opacity = 255
    
    def get_color(self):
        if self.type == "system":
            return COLORS["system"]
        elif self.type == "self":
            return COLORS["player_self"]
        else:
            return COLORS["player_other"]


class InputBox:
    def __init__(self, x, y, width, height, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = COLORS["accent_blue"]
        self.text = ""
        self.font = font
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = COLORS["accent_gold"] if self.active else COLORS["accent_blue"]
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return self.text
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if len(self.text) < 100 and event.unicode:
                    self.text += event.unicode
        return None
    
    def update(self):
        self.cursor_timer += 1
        if self.cursor_timer > 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
    
    def draw(self, surface):
        pygame.draw.rect(surface, COLORS["bg_input"], self.rect, border_radius=12)
        pygame.draw.rect(surface, self.color, self.rect, 2, border_radius=12)
        
        display_text = self.text
        if self.active and self.cursor_visible:
            display_text += "|"
        
        text_surface = self.font.render(display_text, True, COLORS["text_white"])
        surface.blit(text_surface, (self.rect.x + 15, self.rect.y + 12))


class Button:
    def __init__(self, text, x, y, width, height, font, color=COLORS["accent_blue"]):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.font = font
        self.hovered = False
        self.clicked = False
    
    def draw(self, surface, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        color = tuple(min(c + 30, 255) for c in self.color) if self.hovered else self.color
        
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, COLORS["text_white"], self.rect, 2, border_radius=10)
        
        text_surface = self.font.render(self.text, True, COLORS["text_white"])
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
    
    def check_click(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and self.hovered:
            return True
        return False


class ChatClient:
    """聊天网络客户端"""
    
    def __init__(self):
        self.sock = None
        self.server_addr = None
        self.running = False
        self.thread = None
        self.player_id = str(int(time.time()))
        self.connected = False
        self.messages: List[ChatMessage] = []
        self.players: List[Dict] = []
        self.on_message = None
    
    def connect(self, host: str, port: int, player_name: str):
        """连接到聊天服务器"""
        try:
            self.server_addr = (host, port)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(2)
            
            self.running = True
            self.thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.thread.start()
            
            self._send({
                'type': 'join',
                'player_id': self.player_id,
                'player_name': player_name
            })
            
            self.connected = True
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False
    
    def _receive_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                self._handle_message(data)
            except socket.timeout:
                if self.connected:
                    self._send({'type': 'ping', 'player_id': self.player_id})
            except Exception as e:
                if self.running:
                    print(f"接收错误: {e}")
    
    def _handle_message(self, data: bytes):
        try:
            message = json.loads(data.decode('utf-8'))
            msg_type = message.get('type', '')
            
            if msg_type == 'chat':
                is_self = message.get('player_id', '') == self.player_id
                self.messages.append(ChatMessage(
                    message.get('text', ''),
                    message.get('player_name', ''),
                    'self' if is_self else 'other',
                    message.get('timestamp', 0)
                ))
                if len(self.messages) > 100:
                    self.messages.pop(0)
            
            elif msg_type == 'system':
                self.messages.append(ChatMessage(
                    message.get('text', ''),
                    '系统',
                    'system',
                    message.get('timestamp', 0)
                ))
                if len(self.messages) > 100:
                    self.messages.pop(0)
            
            elif msg_type == 'player_list':
                self.players = message.get('players', [])
            
            elif msg_type == 'history':
                for msg in message.get('messages', []):
                    if msg.get('type') == 'chat':
                        is_self = msg.get('player_id', '') == self.player_id
                        self.messages.append(ChatMessage(
                            msg.get('text', ''),
                            msg.get('player_name', ''),
                            'self' if is_self else 'other',
                            msg.get('timestamp', 0)
                        ))
                    elif msg.get('type') == 'system':
                        self.messages.append(ChatMessage(
                            msg.get('text', ''),
                            '系统',
                            'system',
                            msg.get('timestamp', 0)
                        ))
            
            if self.on_message:
                self.on_message()
                
        except Exception as e:
            print(f"解析错误: {e}")
    
    def send_chat(self, text: str):
        """发送聊天消息"""
        if not self.connected:
            return False
        
        self._send({
            'type': 'chat',
            'player_id': self.player_id,
            'player_name': data.get('player_name', '主公'),
            'text': text
        })
        return True
    
    def _send(self, data: Dict):
        """发送数据"""
        try:
            self.sock.sendto(json.dumps(data).encode('utf-8'), self.server_addr)
        except Exception:
            pass
    
    def disconnect(self):
        """断开连接"""
        if self.connected:
            self._send({'type': 'leave', 'player_id': self.player_id})
        
        self.running = False
        self.connected = False
        
        if self.sock:
            self.sock.close()
        
        if self.thread:
            self.thread.join(timeout=1)


class WorldChat:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.client = ChatClient()
        self.client.on_message = self._on_new_message
        
        self.init_fonts()
        self.init_ui()
        self.init_particles()
        
        self.state = "connect"  # connect, chatting
        self.chat_scroll = 0
        self.new_message_effects: List[Particle] = []
    
    def init_fonts(self):
        def init_font(size):
            font_name = get_system_font_name()
            try:
                return pygame.font.SysFont(font_name, size)
            except Exception:
                return pygame.font.Font(None, size)
        
        self.font_title = init_font(36)
        self.font_main = init_font(24)
        self.font_small = init_font(18)
    
    def init_ui(self):
        btn_width = 150
        btn_height = 45
        
        self.input_box = InputBox(50, self.height - 70, self.width - 220, 50, self.font_main)
        self.send_btn = Button("发送", self.width - 160, self.height - 70, btn_width, btn_height, self.font_main, COLORS["accent_green"])
        
        self.server_input = InputBox(50, self.height * 0.35, 300, 50, self.font_main, '127.0.0.1')
        self.port_input = InputBox(370, self.height * 0.35, 150, 50, self.font_main, '5000')
        self.connect_btn = Button("连接", 540, self.height * 0.35, 120, 50, self.font_main, COLORS["accent_green"])
        self.back_btn = Button("返回", self.width - 200, 20, 140, 45, self.font_small, (100, 100, 120))
    
    def init_particles(self):
        self.bg_particles = []
        for _ in range(40):
            self.bg_particles.append(Particle(
                random.randint(0, self.width),
                random.randint(0, self.height),
                (60, 100, 160), 0.3, random.uniform(1, 3), random.randint(100, 300)
            ))
    
    def _on_new_message(self):
        for _ in range(5):
            self.new_message_effects.append(Particle(
                self.width // 2, self.height - 100,
                COLORS["accent_gold"], 2, random.uniform(3, 6), 30
            ))
    
    def draw_background(self):
        for y in range(self.height):
            ratio = y / self.height
            r = int(COLORS["bg_dark"][0] * (1 - ratio) + COLORS["bg_panel"][0] * ratio)
            g = int(COLORS["bg_dark"][1] * (1 - ratio) + COLORS["bg_panel"][1] * ratio)
            b = int(COLORS["bg_dark"][2] * (1 - ratio) + COLORS["bg_panel"][2] * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.width, y))
        
        for p in self.bg_particles:
            p.update()
            if p.life <= 0 or p.x < 0 or p.x > self.width or p.y < 0 or p.y > self.height:
                p.x = random.randint(0, self.width)
                p.y = random.randint(0, self.height)
                p.life = p.max_life
            p.draw(self.screen)
    
    def draw_connect_screen(self):
        title = self.font_title.render("🌍 世界聊天", True, COLORS["accent_gold"])
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 80))
        
        info = self.font_small.render("输入服务器地址连接到世界聊天", True, COLORS["text_gray"])
        self.screen.blit(info, (self.width // 2 - info.get_width() // 2, 150))
        
        server_label = self.font_main.render("服务器IP:", True, COLORS["text_white"])
        port_label = self.font_main.render("端口:", True, COLORS["text_white"])
        self.screen.blit(server_label, (50, self.height * 0.32))
        self.screen.blit(port_label, (370, self.height * 0.32))
        
        self.server_input.draw(self.screen)
        self.port_input.draw(self.screen)
        
        hint = self.font_small.render("提示: 你可以在本地启动 chat_server.py 作为服务器", True, COLORS["text_gray"])
        self.screen.blit(hint, (50, self.height * 0.5))
    
    def draw_chat_screen(self):
        title = self.font_title.render("🌍 世界聊天", True, COLORS["accent_gold"])
        self.screen.blit(title, (30, 25))
        
        status = self.font_small.render(f"在线: {len(self.client.players)} 人", True, COLORS["text_gray"])
        self.screen.blit(status, (self.width - 150, 35))
        
        panel_rect = pygame.Rect(30, 80, self.width - 60, self.height - 170)
        pygame.draw.rect(self.screen, COLORS["bg_panel"], panel_rect, border_radius=15)
        pygame.draw.rect(self.screen, (60, 80, 110), panel_rect, 2, border_radius=15)
        
        y = self.height - 180
        for msg in reversed(self.client.messages):
            if y < 90:
                break
            
            time_str = time.strftime("%H:%M", time.localtime(msg.timestamp))
            
            if msg.type == "system":
                text = f"[{time_str}] {msg.text}"
                text_surface = self.font_small.render(text, True, msg.get_color())
                x = (self.width - text_surface.get_width()) // 2
            else:
                prefix = f"[{time_str}] {msg.sender}: "
                prefix_surface = self.font_small.render(prefix, True, msg.get_color())
                text_surface = self.font_small.render(msg.text, True, COLORS["text_white"])
                
                total_width = prefix_surface.get_width() + text_surface.get_width()
                x = 50 if msg.type == "other" else self.width - 50 - total_width
                
                self.screen.blit(prefix_surface, (x, y))
                x += prefix_surface.get_width()
                self.screen.blit(text_surface, (x, y))
            
            y -= 30
        
        self.input_box.draw(self.screen)
        self.send_btn.draw(self.screen, pygame.mouse.get_pos())
        
        for p in self.new_message_effects[:]:
            p.update()
            p.draw(self.screen)
            if p.life <= 0:
                self.new_message_effects.remove(p)
    
    def run(self):
        running = True
        clock = pygame.time.Clock()
        
        try:
            while running:
                self.draw_background()
                
                mouse_pos = pygame.mouse.get_pos()
                
                if self.state == "connect":
                    self.draw_connect_screen()
                    self.connect_btn.draw(self.screen, mouse_pos)
                    self.back_btn.draw(self.screen, mouse_pos)
                elif self.state == "chatting":
                    self.draw_chat_screen()
                    self.back_btn.draw(self.screen, mouse_pos)
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    
                    if self.state == "connect":
                        self.server_input.handle_event(event)
                        self.port_input.handle_event(event)
                        
                        if self.connect_btn.check_click(event, mouse_pos):
                            host = self.server_input.text
                            port = int(self.port_input.text) if self.port_input.text else 5000
                            name = data.get('player_name', '主公')
                            
                            if self.client.connect(host, port, name):
                                self.state = "chatting"
                        
                        if self.back_btn.check_click(event, mouse_pos):
                            running = False
                    
                    elif self.state == "chatting":
                        result = self.input_box.handle_event(event)
                        if result:
                            self.client.send_chat(result)
                            self.input_box.text = ""
                        
                        if self.send_btn.check_click(event, mouse_pos):
                            if self.input_box.text:
                                self.client.send_chat(self.input_box.text)
                                self.input_box.text = ""
                        
                        if self.back_btn.check_click(event, mouse_pos):
                            self.client.disconnect()
                            running = False
                
                self.input_box.update()
                self.server_input.update()
                self.port_input.update()
                
                pygame.display.flip()
                clock.tick(60)
        
        finally:
            self.client.disconnect()
        
        return True


def main(screen=None):
    try:
        if not pygame.get_init():
            pygame.init()
        
        if screen is None:
            screen = pygame.display.set_mode((900, 650))
            pygame.display.set_caption("🌍 三国游戏 - 世界聊天")
        
        chat = WorldChat(screen)
        chat.run()
        
        return True
    except Exception as e:
        print(f"世界聊天异常: {e}")
        return False


if __name__ == "__main__":
    main()
