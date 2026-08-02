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

def draw_gradient(screen):
    h = screen.get_height()
    for y in range(h):
        r = int(10 + (25-10) * y/h)
        g = int(15 + (35-15) * y/h)
        b = int(28 + (55-28) * y/h)
        pygame.draw.line(screen, (r, g, b), (0, y), (screen.get_width(), y))

def main(screen=None):
    try:
        if not pygame.get_init():
            pygame.init()
        
        if screen is None:
            resolution = data['settings']['graphics']['resolution']
            try:
                width, height = map(int, resolution.split('x'))
            except ValueError:
                width, height = 800, 600
            screen = pygame.display.set_mode((width, height))
        
        pygame.display.set_caption("🎮 P2P联机对战")
        clock = pygame.time.Clock()
        
        font_name = get_system_font_name()
        try:
            FONT_BIG = pygame.font.SysFont(font_name, 42)
            FONT_MAIN = pygame.font.SysFont(font_name, 28)
            FONT_SMALL = pygame.font.SysFont(font_name, 22)
        except Exception:
            FONT_BIG = pygame.font.Font(None, 42)
            FONT_MAIN = pygame.font.Font(None, 28)
            FONT_SMALL = pygame.font.Font(None, 22)
        
        player_name = data.get('player_name', '主公')
        
        buttons = [
            Button("🎮 创建房间", width//2 - 150, height//2 - 80, 300, 55, FONT_MAIN, COLORS["accent_green"], (90, 220, 100)),
            Button("🔍 加入房间", width//2 - 150, height//2, 300, 55, FONT_MAIN, COLORS["accent_blue"], (100, 170, 250)),
            Button("📡 局域网搜索", width//2 - 150, height//2 + 80, 300, 55, FONT_MAIN, COLORS["accent_purple"], (180, 100, 240)),
            Button("⏎ 返回", width//2 - 100, height - 60, 200, 45, FONT_MAIN),
        ]
        
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            
            draw_gradient(screen)
            
            title_surf = FONT_BIG.render("🎮 P2P联机对战", True, COLORS["accent_gold"])
            title_rect = title_surf.get_rect(center=(width//2, 60))
            screen.blit(title_surf, title_rect)
            
            info_surf = FONT_SMALL.render(f"玩家: {player_name}", True, COLORS["text_gray"])
            screen.blit(info_surf, (20, 20))
            
            for btn in buttons:
                btn.hovered = btn.check_click(mx, my)
                btn.draw(screen)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for btn in buttons:
                        if btn.check_click(mx, my):
                            if btn.text == "⏎ 返回":
                                running = False
                            else:
                                msg_surf = FONT_MAIN.render(f"{btn.text}功能开发中...", True, COLORS["accent_gold"])
                                msg_rect = msg_surf.get_rect(center=(width//2, height//2 - 150))
                                screen.blit(msg_surf, msg_rect)
                                pygame.display.flip()
                                pygame.time.wait(2000)
            
            pygame.display.flip()
            clock.tick(30)
        
        return True
    except Exception as e:
        print(f"P2P对战异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()