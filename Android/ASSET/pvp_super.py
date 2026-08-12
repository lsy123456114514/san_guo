#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超级PVP对战大厅
集成世界聊天 + 公网P2P + 局域网对战
"""

import os
import pygame
import random
import math
import time
from typing import Dict, Any, Optional
from ASSET.game_data import data, save, get_system_font_name, logger, draw_gradient_bg, cull_dead, get_font

# 导入安全网络模块
try:
    from ASSET.secure_network import SecureNetwork
    from ASSET.p2p_ngrok import P2PNgrok
except Exception as _e:
    logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

# 颜色主题
COLORS = {
    "bg_dark": (10, 15, 28),
    "bg_light": (25, 35, 55),
    "accent_gold": (255, 200, 50),
    "accent_red": (230, 60, 60),
    "accent_green": (70, 200, 80),
    "accent_blue": (80, 150, 230),
    "accent_purple": (160, 80, 220),
    "text_white": (240, 240, 240),
    "text_gray": (160, 170, 190),
}


class Particle:
    """粒子效果 - 带透明度渐变的圆形粒子"""
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
        pygame.draw.circle(surface, (*self.color[:3], alpha), (int(self.x), int(self.y)), int(self.size))


class AnimatedButton:
    """动画按钮 - 悬停缩放与发光效果"""
    def __init__(self, text, x, y, width, height, font, color=COLORS["accent_blue"], icon=None):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.font = font
        self.icon = icon
        self.hovered = False
        self.glow_alpha = 0
        self.scale = 1.0
    
    def draw(self, surface, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        self.target_scale = 1.05 if self.hovered else 1.0
        self.scale += (self.target_scale - self.scale) * 0.1
        
        self.glow_alpha = min(150, self.glow_alpha + 10) if self.hovered else max(0, self.glow_alpha - 10)
        
        scaled_w = int(self.rect.width * self.scale)
        scaled_h = int(self.rect.height * self.scale)
        scaled_x = self.rect.x + (self.rect.width - scaled_w) // 2
        scaled_y = self.rect.y + (self.rect.height - scaled_h) // 2
        scaled_rect = pygame.Rect(scaled_x, scaled_y, scaled_w, scaled_h)
        
        if self.glow_alpha > 0:
            glow_rect = scaled_rect.inflate(20, 20)
            glow_surface = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*self.color[:3], self.glow_alpha // 3), 
                         (0, 0, glow_rect.width, glow_rect.height), border_radius=15)
            surface.blit(glow_surface, glow_rect)
        
        pygame.draw.rect(surface, self.color, scaled_rect, border_radius=12)
        pygame.draw.rect(surface, COLORS["text_white"], scaled_rect, 2, border_radius=12)
        
        text_surface = self.font.render(self.text, True, COLORS["text_white"])
        text_rect = text_surface.get_rect(center=scaled_rect.center)
        surface.blit(text_surface, text_rect)
    
    def check_click(self, event, mouse_pos):
        return event.type == pygame.MOUSEBUTTONDOWN and self.hovered


class InputBox:
    """输入框 - 支持点击激活、光标闪烁与文字输入"""
    def __init__(self, x, y, width, height, font, text=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = COLORS["accent_blue"]
        self.text = text
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
            elif event.unicode and len(self.text) < 80:
                self.text += event.unicode
        return None
    
    def update(self):
        self.cursor_timer += 1
        if self.cursor_timer > 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
    
    def draw(self, surface):
        pygame.draw.rect(surface, (40, 50, 75), self.rect, border_radius=10)
        pygame.draw.rect(surface, self.color, self.rect, 2, border_radius=10)
        
        display_text = self.text
        if self.active and self.cursor_visible:
            display_text += "|"
        
        text_surface = self.font.render(display_text, True, COLORS["text_white"])
        surface.blit(text_surface, (self.rect.x + 12, self.rect.y + 12))


class SuperPVP:
    """超级对战大厅 - 整合世界聊天、局域网与P2P对战"""
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.state = "main"  # main, world_chat, lan_pvp, p2p_ngrok, mock_pvp
        
        self.init_fonts()
        self.init_ui()
        self.init_particles()
        
        self.p2p_network = None
        self.ngrok_network = None
        self.messages = []
        self.player_list = []
        self.tunnel_url = None
    
    def init_fonts(self):
        def init_font(size):
            return get_font(size)


def main(screen=None):
    try:
        if not pygame.get_init():
            pygame.init()
        
        if screen is None:
            screen = pygame.display.set_mode((950, 700))
            pygame.display.set_caption("⚔️ 三国游戏 - 超级对战大厅")
        
        pvp = SuperPVP(screen)
        pvp.run()
        
        return True
    except Exception as e:
        logger.info(f"超级PVP异常: {e}")
        return False


if __name__ == "__main__":
    main()
