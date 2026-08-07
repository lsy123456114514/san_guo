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
from ASSET.game_data import data, save, get_system_font_name, logger, draw_gradient_bg, cull_dead, get_font
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
        
        for p in self.particles:
            p.update()
            p.draw(surface)
        self.particles[:] = [p for p in self.particles if p.life > 0]

    
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


def draw_gradient_bg(surface, color1, color2):
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
            return get_font(size)


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
        logger.info(f"在线PVP模块异常：{str(e)}")
        return False


if __name__ == "__main__":
    main()
