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
from ASSET.game_data import data, save, get_system_font_name, logger, draw_gradient_bg, cull_dead, get_font

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
        alpha = int(255 * (self.life / self.max_life))
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
            logger.info(f"连接失败: {e}")
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
                    logger.info(f"接收错误: {e}")
    
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
            logger.info(f"解析错误: {e}")
    
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
        except Exception as _e:
            logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)
    
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
            return get_font(size)


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
        logger.info(f"世界聊天异常: {e}")
        return False


if __name__ == "__main__":
    main()
