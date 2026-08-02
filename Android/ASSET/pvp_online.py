import pygame
import sys
import os
from ASSET.game_data import data, save, get_system_font_name

COLORS = {
    "bg_dark": (10, 15, 28),
    "bg_light": (25, 35, 55),
    "accent_gold": (255, 200, 50),
    "accent_red": (230, 60, 60),
    "accent_green": (70, 200, 80),
    "accent_blue": (80, 150, 230),
    "text_white": (240, 240, 240),
    "text_gray": (160, 170, 190),
}

class Button:
    def __init__(self, text, x, y, width, height, font, color=(100, 100, 150), hover_color=(120, 120, 180), text_color=(255, 255, 255)):
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hovered = False
    
    def draw(self, screen):
        col = self.hover_color if self.hovered else self.color
        pygame.draw.rect(screen, col, (self.x, self.y, self.width, self.height), border_radius=8)
        pygame.draw.rect(screen, COLORS["accent_gold"], (self.x, self.y, self.width, self.height), 2, border_radius=8)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=(self.x + self.width//2, self.y + self.height//2))
        screen.blit(text_surf, text_rect)
    
    def check_click(self, mx, my):
        return self.x <= mx <= self.x + self.width and self.y <= my <= self.y + self.height

class PVPOnline:
    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.clock = pygame.time.Clock()
        self.font_name = get_system_font_name()
        
        try:
            self.font_big = pygame.font.SysFont(self.font_name, 36)
            self.font_main = pygame.font.SysFont(self.font_name, 26)
            self.font_small = pygame.font.SysFont(self.font_name, 20)
        except Exception:
            self.font_big = pygame.font.Font(None, 36)
            self.font_main = pygame.font.Font(None, 26)
            self.font_small = pygame.font.Font(None, 20)
        
        self.rooms = [
            {"id": "ROOM001", "host": "刘备", "players": 1, "max_players": 2, "status": "waiting"},
            {"id": "ROOM002", "host": "曹操", "players": 2, "max_players": 2, "status": "playing"},
            {"id": "ROOM003", "host": "孙权", "players": 1, "max_players": 2, "status": "waiting"},
        ]
        
        self.back_btn = Button("⏎ 返回", 20, self.height - 50, 120, 40, self.font_main)
    
    def draw_gradient(self):
        h = self.height
        for y in range(h):
            r = int(10 + (25-10) * y/h)
            g = int(15 + (35-15) * y/h)
            b = int(28 + (55-28) * y/h)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.width, y))
    
    def run(self):
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            
            self.draw_gradient()
            
            title_surf = self.font_big.render("🔍 局域网对战大厅", True, COLORS["accent_gold"])
            title_rect = title_surf.get_rect(center=(self.width//2, 40))
            self.screen.blit(title_surf, title_rect)
            
            start_y = 80
            for room in self.rooms:
                bg_color = COLORS["accent_green"] if room["status"] == "waiting" else COLORS["accent_red"]
                pygame.draw.rect(self.screen, bg_color, (30, start_y, self.width - 60, 50), border_radius=8)
                
                id_surf = self.font_main.render(f"🏠 {room['id']}", True, COLORS["bg_dark"])
                self.screen.blit(id_surf, (45, start_y + 12))
                
                host_surf = self.font_small.render(f"房主: {room['host']}", True, COLORS["bg_dark"])
                self.screen.blit(host_surf, (150, start_y + 15))
                
                players_surf = self.font_small.render(f"{room['players']}/{room['max_players']}", True, COLORS["bg_dark"])
                players_x = self.width - 200
                self.screen.blit(players_surf, (players_x, start_y + 15))
                
                status_text = "等待中" if room["status"] == "waiting" else "对战中"
                status_surf = self.font_small.render(status_text, True, COLORS["bg_dark"])
                status_x = self.width - 100 - status_surf.get_width()
                self.screen.blit(status_surf, (status_x, start_y + 15))
                
                if room["status"] == "waiting":
                    join_btn = Button("加入", self.width - 110, start_y + 5, 80, 40, self.font_small, COLORS["accent_blue"], (120, 180, 250))
                    join_btn.hovered = join_btn.check_click(mx, my)
                    join_btn.draw(self.screen)
                    if join_btn.check_click(mx, my) and pygame.mouse.get_pressed()[0]:
                        msg_surf = self.font_main.render("正在加入房间...", True, COLORS["accent_gold"])
                        msg_rect = msg_surf.get_rect(center=(self.width//2, self.height//2))
                        self.screen.blit(msg_surf, msg_rect)
                        pygame.display.flip()
                        pygame.time.wait(2000)
                
                start_y += 60
            
            self.back_btn.hovered = self.back_btn.check_click(mx, my)
            self.back_btn.draw(self.screen)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.back_btn.check_click(mx, my):
                        running = False
            
            pygame.display.flip()
            self.clock.tick(30)

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pvp = PVPOnline(screen)
    pvp.run()
    pygame.quit()