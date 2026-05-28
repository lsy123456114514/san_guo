#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在线PVP对战模块 - 集成网络通信功能
支持局域网对战、IP直连、玩家匹配
"""

import os
import pygame
import platform
import random
import math
from ASSET.game_data import data, save, get_system_font_name
from ASSET.network_pvp import NetworkPVP
from ASSET import safe_exit

# 颜色主题
COLORS = {
    "bg_dark": (15, 15, 35),
    "bg_light": (25, 25, 50),
    "accent_gold": (255, 215, 0),
    "accent_red": (220, 60, 60),
    "accent_green": (60, 220, 60),
    "accent_blue": (70, 130, 180),
    "accent_blue_light": (100, 149, 237),
    "accent_blue_dark": (50, 100, 150),
    "text_white": (255, 255, 255),
    "text_gray": (180, 180, 200),
    "panel_bg": (40, 40, 70, 200)
}


class Particle:
    def __init__(self, x, y, color, speed, size, life, particle_type="normal"):
        self.x = x
        self.y = y
        self.color = color
        self.speed_x = random.uniform(-speed, speed)
        self.speed_y = random.uniform(-speed, speed)
        self.size = size
        self.life = life
        self.max_life = life
        self.type = particle_type
    
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.life -= 1
        if self.type == "sparkle":
            self.size = max(0, self.size - 0.2)
        else:
            self.size = max(1, self.size - 0.1)
    
    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        if self.type == "sparkle":
            points = []
            for i in range(5):
                angle = math.pi * 2 * i / 5 - math.pi / 2
                px = self.x + math.cos(angle) * self.size
                py = self.y + math.sin(angle) * self.size
                points.append((px, py))
                angle = math.pi * 2 * (i + 0.5) / 5 - math.pi / 2
                px = self.x + math.cos(angle) * (self.size * 0.5)
                py = self.y + math.sin(angle) * (self.size * 0.5)
                points.append((px, py))
            pygame.draw.polygon(surface, self.color, points)
        else:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))


class AnimatedButton:
    def __init__(self, text, x, y, width, height, font, 
                 normal_color=COLORS["accent_blue"], 
                 hover_color=COLORS["accent_blue_light"], 
                 text_color=COLORS["text_white"],
                 icon=None):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.is_clicked = False
        self.click_timer = 0
        self.icon = icon
        self.particles = []
        self.glow_alpha = 0
        self.scale = 1.0
        self.target_scale = 1.0
    
    def draw(self, surface):
        if self.is_hovered:
            self.target_scale = 1.05
        else:
            self.target_scale = 1.0
        self.scale += (self.target_scale - self.scale) * 0.1
        
        scaled_width = int(self.rect.width * self.scale)
        scaled_height = int(self.rect.height * self.scale)
        scaled_x = self.rect.x + (self.rect.width - scaled_width) // 2
        scaled_y = self.rect.y + (self.rect.height - scaled_height) // 2
        scaled_rect = pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)
        
        if self.is_hovered:
            self.glow_alpha = min(120, self.glow_alpha + 8)
        else:
            self.glow_alpha = max(0, self.glow_alpha - 8)
        
        if self.glow_alpha > 0:
            for offset in range(3, 0, -1):
                glow_surf = pygame.Surface((scaled_width + offset * 10, scaled_height + offset * 10), pygame.SRCALPHA)
                alpha = self.glow_alpha // offset
                pygame.draw.rect(glow_surf, (*self.hover_color[:3], alpha), 
                               (0, 0, scaled_width + offset * 10, scaled_height + offset * 10), border_radius=15)
                surface.blit(glow_surf, (scaled_x - offset * 5, scaled_y - offset * 5))
        
        color = self.hover_color if self.is_hovered else self.normal_color
        if self.is_clicked:
            color = COLORS["accent_blue_dark"]
        
        for i in range(scaled_height):
            ratio = i / scaled_height
            gradient_color = (
                int(color[0] * (1 - ratio) + min(255, color[0] + 30) * ratio),
                int(color[1] * (1 - ratio) + min(255, color[1] + 30) * ratio),
                int(color[2] * (1 - ratio) + min(255, color[2] + 30) * ratio)
            )
            pygame.draw.line(surface, gradient_color, 
                           (scaled_x, scaled_y + i),
                           (scaled_x + scaled_width, scaled_y + i))
        
        pygame.draw.rect(surface, COLORS["text_white"], scaled_rect, 2, border_radius=10)
        pygame.draw.rect(surface, COLORS["accent_gold"], scaled_rect, 1, border_radius=10)
        
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=scaled_rect.center)
        shadow_surf = self.font.render(self.text, True, (0, 0, 0))
        surface.blit(shadow_surf, (text_rect.x + 2, text_rect.y + 2))
        surface.blit(text_surf, text_rect)
        
        if self.is_hovered and random.random() < 0.4:
            self.particles.append(Particle(
                random.randint(scaled_x, scaled_x + scaled_width),
                random.randint(scaled_y, scaled_y + scaled_height),
                COLORS["accent_gold"], 1.5, random.randint(2, 4), 40, "sparkle"
            ))
        
        for p in self.particles[:]:
            p.update()
            p.draw(surface)
            if p.life <= 0:
                self.particles.remove(p)
    
    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
    
    def check_click(self, mouse_pos):
        if self.is_hovered and pygame.mouse.get_pressed()[0]:
            if not self.is_clicked:
                self.is_clicked = True
                self.click_timer = pygame.time.get_ticks()
                return True
        elif self.is_clicked:
            if pygame.time.get_ticks() - self.click_timer > 200:
                self.is_clicked = False
        return False


class InputBox:
    def __init__(self, x, y, width, height, font, text=''):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = COLORS["text_gray"]
        self.text = text
        self.font = font
        self.txt_surface = font.render(text, True, COLORS["text_white"])
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = COLORS["accent_gold"] if self.active else COLORS["text_gray"]
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    return self.text
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    if len(self.text) < 50:
                        self.text += event.unicode
                self.txt_surface = self.font.render(self.text, True, COLORS["text_white"])
        return None
    
    def update(self):
        self.cursor_timer += 1
        if self.cursor_timer > 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
    
    def draw(self, surface):
        pygame.draw.rect(surface, (50, 50, 80), self.rect, border_radius=8)
        pygame.draw.rect(surface, self.color, self.rect, 2, border_radius=8)
        
        display_text = self.text
        if self.active and self.cursor_visible:
            display_text += "|"
        
        txt_surface = self.font.render(display_text, True, COLORS["text_white"])
        surface.blit(txt_surface, (self.rect.x + 10, self.rect.y + 10))


def draw_gradient_background(surface, color1, color2):
    width, height = surface.get_size()
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))


def draw_title(surface, text, y_pos, screen_width, font, color=COLORS["accent_gold"]):
    for offset in range(5, 0, -1):
        alpha = max(0, 60 - offset * 10)
        glow_surf = font.render(text, True, (*color[:3], alpha))
        glow_rect = glow_surf.get_rect(center=(screen_width // 2, y_pos))
        for dx in [-offset, 0, offset]:
            for dy in [-offset, 0, offset]:
                if dx != 0 or dy != 0:
                    surface.blit(glow_surf, (glow_rect.x + dx, glow_rect.y + dy))
    
    title = font.render(text, True, color)
    title_rect = title.get_rect(center=(screen_width // 2, y_pos))
    
    shadow = font.render(text, True, (0, 0, 0))
    surface.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
    surface.blit(title, title_rect)
    
    line_y = y_pos + font.get_height() // 2 + 15
    pygame.draw.line(surface, color, 
                    (screen_width // 2 - 120, line_y),
                    (screen_width // 2 - 40, line_y), 3)
    pygame.draw.line(surface, color,
                    (screen_width // 2 + 40, line_y),
                    (screen_width // 2 + 120, line_y), 3)
    pygame.draw.circle(surface, color, (screen_width // 2, line_y), 6)
    pygame.draw.circle(surface, COLORS["bg_dark"], (screen_width // 2, line_y), 4)


class PVPOnline:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.state = "main"
        self.network = None
        self.opponent_info = None
        self.messages = []
        self.chat_history = []
        
        self.player_name = data.get('player_name', '主公')
        self.player_level = data.get('player_level', 1)
        self.player_power = data.get('player_power', 1000)
        
        self.init_fonts()
        self.init_buttons()
        self.init_inputs()
        self.init_particles()
    
    def init_fonts(self):
        def init_font(size):
            font_name = get_system_font_name()
            try:
                return pygame.font.SysFont(font_name, size)
            except Exception:
                return pygame.font.Font(None, size)
        
        self.font_main = init_font(28)
        self.font_small = init_font(22)
        self.font_big = init_font(48)
    
    def init_buttons(self):
        self.buttons = []
    
    def init_inputs(self):
        btn_width = 350
        self.ip_input = InputBox((self.width - btn_width) // 2, self.height * 0.35, btn_width, 50, self.font_small, '127.0.0.1')
        self.port_input = InputBox((self.width - btn_width) // 2, self.height * 0.45, btn_width, 50, self.font_small, '4000')
    
    def init_particles(self):
        self.bg_particles = []
        for _ in range(30):
            self.bg_particles.append(Particle(
                random.randint(0, self.width),
                random.randint(0, self.height),
                COLORS["accent_gold"], 0.3, random.randint(1, 3), random.randint(100, 200), "normal"
            ))
    
    def network_message_handler(self, message, addr):
        msg_type = message.get('type', '')
        if msg_type == 'connect':
            self.opponent_info = {
                'name': message.get('player_name', '对手'),
                'id': message.get('player_id', ''),
                'addr': addr
            }
            self.messages.append(f"📨 {self.opponent_info['name']} 请求连接！")
        elif msg_type == 'chat':
            name = message.get('player_name', '对手')
            text = message.get('text', '')
            self.chat_history.append(f"{name}: {text}")
            if len(self.chat_history) > 20:
                self.chat_history.pop(0)
    
    def create_buttons(self):
        self.buttons.clear()
        btn_width = 280
        btn_height = 60
        start_y = self.height * 0.35
        spacing = 80
        
        if self.state == "main":
            self.buttons.append(AnimatedButton("🌐 创建房间", (self.width - btn_width) // 2, start_y, btn_width, btn_height, self.font_small,
                                            normal_color=COLORS["accent_green"]))
            self.buttons.append(AnimatedButton("🔗 加入房间", (self.width - btn_width) // 2, start_y + spacing, btn_width, btn_height, self.font_small))
            self.buttons.append(AnimatedButton("🎮 模拟对战", (self.width - btn_width) // 2, start_y + spacing * 2, btn_width, btn_height, self.font_small))
            self.buttons.append(AnimatedButton("🔙 返回", (self.width - btn_width) // 2, start_y + spacing * 3, btn_width, btn_height, self.font_small,
                                            normal_color=(100, 100, 130)))
        
        elif self.state == "create_room":
            self.buttons.append(AnimatedButton("✅ 等待连接", (self.width - btn_width) // 2, start_y + spacing * 2, btn_width, btn_height, self.font_small,
                                            normal_color=COLORS["accent_blue"]))
            self.buttons.append(AnimatedButton("🔙 返回", (self.width - btn_width) // 2, start_y + spacing * 3, btn_width, btn_height, self.font_small,
                                            normal_color=(100, 100, 130)))
        
        elif self.state == "join_room":
            self.buttons.append(AnimatedButton("🚀 连接", (self.width - btn_width) // 2, start_y + spacing * 2, btn_width, btn_height, self.font_small,
                                            normal_color=COLORS["accent_green"]))
            self.buttons.append(AnimatedButton("🔙 返回", (self.width - btn_width) // 2, start_y + spacing * 3, btn_width, btn_height, self.font_small,
                                            normal_color=(100, 100, 130)))
    
    def start_room(self):
        if self.network:
            self.network.stop()
        
        self.network = NetworkPVP(self.player_name)
        self.network.start_server(int(self.port_input.text) if self.port_input.text else 4000, self.network_message_handler)
        self.state = "create_room"
        self.messages.append(f"✅ 房间已创建！")
        self.messages.append(f"你的IP: {self.network.get_local_ip()}")
        self.messages.append(f"端口: {self.port_input.text}")
        self.create_buttons()
    
    def join_room(self):
        if self.network:
            self.network.stop()
        
        self.network = NetworkPVP(self.player_name)
        self.network.start_server(int(self.port_input.text) + 1 if self.port_input.text else 4001, self.network_message_handler)
        self.network.connect_to_player(self.ip_input.text, int(self.port_input.text) if self.port_input.text else 4000)
        self.state = "create_room"
        self.messages.append(f"🔗 正在连接 {self.ip_input.text}:{self.port_input.text}...")
        self.create_buttons()
    
    def run(self):
        running = True
        clock = pygame.time.Clock()
        self.create_buttons()
        
        try:
            while running:
                draw_gradient_background(self.screen, COLORS["bg_dark"], COLORS["bg_light"])
                
                for p in self.bg_particles:
                    p.update()
                    if p.x < 0 or p.x > self.width or p.y < 0 or p.y > self.height or p.life <= 0:
                        p.x = random.randint(0, self.width)
                        p.y = random.randint(0, self.height)
                        p.life = p.max_life
                    p.draw(self.screen)
                
                mouse_pos = pygame.mouse.get_pos()
                
                if self.state == "main":
                    draw_title(self.screen, "在线PVP对战", self.height * 0.12, self.width, self.font_big)
                    self.draw_player_info()
                
                elif self.state == "create_room":
                    draw_title(self.screen, "等待对手连接", self.height * 0.12, self.width, self.font_big)
                    self.draw_room_info()
                    self.draw_messages()
                
                elif self.state == "join_room":
                    draw_title(self.screen, "输入房间信息", self.height * 0.12, self.width, self.font_big)
                    self.draw_join_room()
                
                for btn in self.buttons:
                    btn.check_hover(mouse_pos)
                    btn.draw(self.screen)
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    
                    if self.state == "join_room":
                        self.ip_input.handle_event(event)
                        self.port_input.handle_event(event)
                    
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        for i, btn in enumerate(self.buttons):
                            if btn.check_click(mouse_pos):
                                if self.state == "main":
                                    if i == 0:
                                        self.start_room()
                                    elif i == 1:
                                        self.state = "join_room"
                                        self.create_buttons()
                                    elif i == 2:
                                        self.run_mock_battle()
                                    elif i == 3:
                                        running = False
                                elif self.state == "create_room":
                                    if i == 0:
                                        pass
                                    elif i == 1:
                                        if self.network:
                                            self.network.stop()
                                        self.state = "main"
                                        self.create_buttons()
                                elif self.state == "join_room":
                                    if i == 0:
                                        self.join_room()
                                    elif i == 1:
                                        if self.network:
                                            self.network.stop()
                                        self.state = "main"
                                        self.create_buttons()
                
                if self.state == "join_room":
                    self.ip_input.update()
                    self.port_input.update()
                
                pygame.display.flip()
                clock.tick(60)
        
        finally:
            if self.network:
                self.network.stop()
        
        return
    
    def draw_player_info(self):
        panel_width = 400
        panel_height = 80
        panel_x = (self.width - panel_width) // 2
        panel_y = self.height * 0.22
        
        panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (40, 40, 70, 180), (0, 0, panel_width, panel_height), border_radius=15)
        self.screen.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(self.screen, COLORS["accent_gold"], (panel_x, panel_y, panel_width, panel_height), 2, border_radius=15)
        
        player_info = f"{self.player_name} | Lv.{self.player_level} | ⚔️ {self.player_power}"
        info_text = self.font_small.render(player_info, True, COLORS["text_white"])
        info_rect = info_text.get_rect(center=(self.width // 2, panel_y + panel_height // 2))
        self.screen.blit(info_text, info_rect)
    
    def draw_room_info(self):
        panel_width = 450
        panel_height = 120
        panel_x = (self.width - panel_width) // 2
        panel_y = self.height * 0.22
        
        panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (40, 40, 70, 180), (0, 0, panel_width, panel_height), border_radius=15)
        self.screen.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(self.screen, COLORS["accent_gold"], (panel_x, panel_y, panel_width, panel_height), 2, border_radius=15)
        
        if self.network:
            ip_text = self.font_small.render(f"IP: {self.network.get_local_ip()}", True, COLORS["text_white"])
            port_text = self.font_small.render(f"端口: {self.local_port if hasattr(self, 'local_port') else self.port_input.text}", True, COLORS["text_white"])
            
            ip_rect = ip_text.get_rect(center=(self.width // 2, panel_y + 35))
            port_rect = port_text.get_rect(center=(self.width // 2, panel_y + 70))
            
            self.screen.blit(ip_text, ip_rect)
            self.screen.blit(port_text, port_rect)
    
    def draw_messages(self):
        panel_width = 450
        panel_height = 200
        panel_x = (self.width - panel_width) // 2
        panel_y = self.height * 0.45
        
        panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (30, 30, 50, 180), (0, 0, panel_width, panel_height), border_radius=10)
        self.screen.blit(panel_surf, (panel_x, panel_y))
        
        y_offset = panel_y + 10
        for msg in self.messages[-8:]:
            text = self.font_small.render(msg, True, COLORS["text_white"])
            self.screen.blit(text, (panel_x + 15, y_offset))
            y_offset += 25
    
    def draw_join_room(self):
        ip_label = self.font_small.render("对方IP地址:", True, COLORS["text_white"])
        port_label = self.font_small.render("端口:", True, COLORS["text_white"])
        
        self.screen.blit(ip_label, ((self.width - 350) // 2, self.height * 0.32))
        self.screen.blit(port_label, ((self.width - 350) // 2, self.height * 0.42))
        
        self.ip_input.draw(self.screen)
        self.port_input.draw(self.screen)
    
    def run_mock_battle(self):
        from ASSET.pvp_p2p import main as mock_pvp
        mock_pvp()


def main(screen=None):
    try:
        if not pygame.get_init():
            pygame.init()
        
        if screen is None:
            screen = pygame.display.set_mode((800, 600))
            pygame.display.set_caption("⚔️ 在线PVP对战")
        
        pvp = PVPOnline(screen)
        pvp.run()
        
        return True
    except Exception as e:
        print(f"在线PVP模块异常：{str(e)}")
        return False


if __name__ == "__main__":
    main()
