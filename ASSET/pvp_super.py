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
from ASSET.game_data import data, save, get_system_font_name

# 导入安全网络模块
try:
    from ASSET.secure_network import SecureNetwork
    from ASSET.p2p_ngrok import P2PNgrok
except Exception:
    pass

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
        pygame.draw.circle(surface, (*self.color[:3], alpha), (int(self.x), int(self.y)), int(self.size))


class AnimatedButton:
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
            font_name = get_system_font_name()
            try:
                return pygame.font.SysFont(font_name, size)
            except Exception:
                return pygame.font.Font(None, size)
        
        self.font_title = init_font(42)
        self.font_big = init_font(32)
        self.font_main = init_font(24)
        self.font_small = init_font(18)
    
    def init_ui(self):
        btn_width = 320
        btn_height = 70
        start_y = 180
        spacing = 90
        
        self.main_buttons = [
            AnimatedButton("🌍 世界聊天", (self.width - btn_width) // 2, start_y, btn_width, btn_height, self.font_main, COLORS["accent_green"]),
            AnimatedButton("🌐 公网P2P对战", (self.width - btn_width) // 2, start_y + spacing, btn_width, btn_height, self.font_main, COLORS["accent_purple"]),
            AnimatedButton("🏠 局域网对战", (self.width - btn_width) // 2, start_y + spacing * 2, btn_width, btn_height, self.font_main, COLORS["accent_blue"]),
            AnimatedButton("🤖 模拟对战", (self.width - btn_width) // 2, start_y + spacing * 3, btn_width, btn_height, self.font_main, COLORS["accent_gold"]),
        ]
        
        self.back_btn = AnimatedButton("← 返回", 30, 20, 140, 50, self.font_small, (100, 100, 120))
        
        # P2P UI
        self.ip_input = InputBox(50, 250, 300, 50, self.font_main, '127.0.0.1')
        self.port_input = InputBox(370, 250, 150, 50, self.font_main, '4000')
        self.create_room_btn = AnimatedButton("创建房间", 540, 250, 150, 50, self.font_main, COLORS["accent_green"])
        self.join_room_btn = AnimatedButton("加入房间", 710, 250, 150, 50, self.font_main, COLORS["accent_blue"])
    
    def init_particles(self):
        self.bg_particles = []
        for _ in range(50):
            self.bg_particles.append(Particle(
                random.randint(0, self.width),
                random.randint(0, self.height),
                (80, 130, 200), 0.25, random.uniform(1, 3.5), random.randint(100, 350)
            ))
    
    def draw_background(self):
        for y in range(self.height):
            ratio = y / self.height
            r = int(COLORS["bg_dark"][0] * (1 - ratio) + COLORS["bg_light"][0] * ratio)
            g = int(COLORS["bg_dark"][1] * (1 - ratio) + COLORS["bg_light"][1] * ratio)
            b = int(COLORS["bg_dark"][2] * (1 - ratio) + COLORS["bg_light"][2] * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.width, y))
        
        for p in self.bg_particles:
            p.update()
            if p.life <= 0 or p.x < 0 or p.x > self.width or p.y < 0 or p.y > self.height:
                p.x = random.randint(0, self.width)
                p.y = random.randint(0, self.height)
                p.life = p.max_life
            p.draw(self.screen)
    
    def draw_main_menu(self):
        title = self.font_title.render("⚔️ 三国游戏 - 对战大厅", True, COLORS["accent_gold"])
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 80))
        
        subtitle = self.font_small.render("选择你的对战方式", True, COLORS["text_gray"])
        self.screen.blit(subtitle, (self.width // 2 - subtitle.get_width() // 2, 140))
        
        player_info = f"{data.get('player_name', '主公')} | Lv.{data.get('player_level', 1)} | ⚔️ {data.get('player_power', 1000)}"
        info_text = self.font_main.render(player_info, True, COLORS["text_white"])
        info_rect = pygame.Rect((self.width - 400) // 2, self.height - 100, 400, 60)
        
        pygame.draw.rect(self.screen, (35, 45, 70), info_rect, border_radius=12)
        pygame.draw.rect(self.screen, (70, 90, 120), info_rect, 2, border_radius=12)
        self.screen.blit(info_text, info_text.get_rect(center=info_rect.center))
    
    def draw_p2p_ngrok(self):
        title = self.font_big.render("🌐 公网P2P对战", True, COLORS["accent_purple"])
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 60))
        
        desc = [
            "使用ngrok内网穿透，跨网对战！",
            "像陶瓦联机一样，地球两端也能玩！"
        ]
        for i, line in enumerate(desc):
            text = self.font_small.render(line, True, COLORS["text_gray"])
            self.screen.blit(text, (self.width // 2 - text.get_width() // 2, 110 + i * 25))
        
        ip_label = self.font_main.render("对方IP:", True, COLORS["text_white"])
        port_label = self.font_main.render("端口:", True, COLORS["text_white"])
        self.screen.blit(ip_label, (50, 220))
        self.screen.blit(port_label, (370, 220))
        
        self.ip_input.draw(self.screen)
        self.port_input.draw(self.screen)
        
        if self.tunnel_url:
            tunnel_text = self.font_main.render(f"你的公网地址: {self.tunnel_url}", True, COLORS["accent_green"])
            self.screen.blit(tunnel_text, (50, 350))
        
        hint = self.font_small.render("提示: 需要先安装ngrok: https://ngrok.com/download", True, COLORS["text_gray"])
        self.screen.blit(hint, (50, 450))
    
    def draw_world_chat_info(self):
        title = self.font_big.render("🌍 世界聊天", True, COLORS["accent_green"])
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 80))
        
        info = [
            "先启动聊天服务器: python ASSET/chat_server.py",
            "然后连接服务器IP即可全球聊天！"
        ]
        for i, line in enumerate(info):
            text = self.font_small.render(line, True, COLORS["text_gray"])
            self.screen.blit(text, (self.width // 2 - text.get_width() // 2, 150 + i * 30))
        
        launch_btn = AnimatedButton("启动聊天", (self.width - 200) // 2, 250, 200, 60, self.font_main, COLORS["accent_green"])
        launch_btn.draw(self.screen, pygame.mouse.get_pos())
        
        return launch_btn
    
    def run(self):
        running = True
        clock = pygame.time.Clock()
        
        try:
            while running:
                self.draw_background()
                mouse_pos = pygame.mouse.get_pos()
                
                if self.state == "main":
                    self.draw_main_menu()
                    for btn in self.main_buttons:
                        btn.draw(self.screen, mouse_pos)
                
                elif self.state == "p2p_ngrok":
                    self.draw_p2p_ngrok()
                    self.create_room_btn.draw(self.screen, mouse_pos)
                    self.join_room_btn.draw(self.screen, mouse_pos)
                    self.back_btn.draw(self.screen, mouse_pos)
                
                elif self.state == "world_chat_info":
                    launch_btn = self.draw_world_chat_info()
                    self.back_btn.draw(self.screen, mouse_pos)
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    
                    if self.state == "main":
                        for i, btn in enumerate(self.main_buttons):
                            if btn.check_click(event, mouse_pos):
                                if i == 0:
                                    self.state = "world_chat_info"
                                elif i == 1:
                                    self.state = "p2p_ngrok"
                                elif i == 2:
                                    self._launch_lan_pvp()
                                elif i == 3:
                                    self._launch_mock_pvp()
                    
                    elif self.state == "p2p_ngrok":
                        self.ip_input.handle_event(event)
                        self.port_input.handle_event(event)
                        
                        if self.create_room_btn.check_click(event, mouse_pos):
                            self._create_ngrok_room()
                        if self.join_room_btn.check_click(event, mouse_pos):
                            self._join_ngrok_room()
                        if self.back_btn.check_click(event, mouse_pos):
                            self.state = "main"
                    
                    elif self.state == "world_chat_info":
                        if self.back_btn.check_click(event, mouse_pos):
                            self.state = "main"
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            self._launch_world_chat()
                
                if self.state in ["p2p_ngrok"]:
                    self.ip_input.update()
                    self.port_input.update()
                
                pygame.display.flip()
                clock.tick(60)
        
        finally:
            if self.ngrok_network:
                self.ngrok_network.stop()
        
        return True
    
    def _create_ngrok_room(self):
        try:
            from ASSET.p2p_ngrok import P2PNgrok
            port = int(self.port_input.text) if self.port_input.text else 4000
            
            self.ngrok_network = P2PNgrok(data.get('player_name', '主公'))
            
            def handle_msg(msg, addr):
                self.messages.append(str(msg))
            
            self.tunnel_url = self.ngrok_network.start_host(port, handle_msg)
            self.messages.append(f"房间已创建: {self.tunnel_url}")
        except Exception as e:
            self.messages.append(f"创建失败: {e}")
    
    def _join_ngrok_room(self):
        pass
    
    def _launch_world_chat(self):
        try:
            from ASSET.world_chat import WorldChat
            chat = WorldChat(self.screen)
            chat.run()
        except Exception as e:
            print(f"启动聊天失败: {e}")
    
    def _launch_lan_pvp(self):
        try:
            from ASSET.pvp_online import PVPOnline
            pvp = PVPOnline(self.screen)
            pvp.run()
        except Exception as e:
            print(f"启动局域网失败: {e}")
    
    def _launch_mock_pvp(self):
        try:
            from ASSET.pvp_p2p import main as mock_pvp
            mock_pvp(self.screen)
        except Exception as e:
            print(f"启动模拟失败: {e}")


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
        print(f"超级PVP异常: {e}")
        return False


if __name__ == "__main__":
    main()
