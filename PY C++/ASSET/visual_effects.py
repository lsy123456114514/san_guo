import pygame
import random
import time
import math

class VisualEffects:
    """视觉特效系统 - 借鉴成功游戏的视觉风格"""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.particles = []
        self.stars = []
        self.floating_elements = []
        self.animating_elements = {}
        
        self.colors = {
            "gold": (255, 215, 0),
            "cyan": (0, 212, 255),
            "purple": (138, 43, 226),
            "red": (255, 69, 0),
            "green": (50, 205, 50),
            "dark_bg": (15, 20, 30),
            "panel_bg": (25, 35, 50),
            "text_primary": (255, 255, 255),
            "text_secondary": (180, 180, 200)
        }
        
        self._init_background_elements()
    
    def _init_background_elements(self):
        for _ in range(50):
            self.stars.append({
                "x": random.randint(0, self.screen_width),
                "y": random.randint(0, self.screen_height),
                "size": random.randint(1, 3),
                "speed": random.uniform(0.1, 0.5),
                "brightness": random.uniform(0.3, 1.0),
                "twinkle_speed": random.uniform(0.02, 0.05)
            })
        
        for _ in range(10):
            self.floating_elements.append({
                "type": random.choice(["cloud", "particle", "glow"]),
                "x": random.randint(0, self.screen_width),
                "y": random.randint(0, self.screen_height),
                "speed_x": random.uniform(-0.3, 0.3),
                "speed_y": random.uniform(-0.2, 0.2),
                "size": random.randint(20, 50),
                "alpha": random.uniform(0.1, 0.3)
            })
    
    def update(self):
        self._update_stars()
        self._update_floating_elements()
        self._update_particles()
        self._update_animations()
    
    def _update_stars(self):
        for star in self.stars:
            star["brightness"] += star["twinkle_speed"]
            if star["brightness"] >= 1.0 or star["brightness"] <= 0.3:
                star["twinkle_speed"] *= -1
            
            star["y"] -= star["speed"]
            if star["y"] < 0:
                star["y"] = self.screen_height
                star["x"] = random.randint(0, self.screen_width)
    
    def _update_floating_elements(self):
        for elem in self.floating_elements:
            elem["x"] += elem["speed_x"]
            elem["y"] += elem["speed_y"]
            
            if elem["x"] < -elem["size"]:
                elem["x"] = self.screen_width + elem["size"]
            elif elem["x"] > self.screen_width + elem["size"]:
                elem["x"] = -elem["size"]
            
            if elem["y"] < -elem["size"]:
                elem["y"] = self.screen_height + elem["size"]
            elif elem["y"] > self.screen_height + elem["size"]:
                elem["y"] = -elem["size"]
    
    def _update_particles(self):
        self.particles = [p for p in self.particles if p["life"] > 0]
        
        for particle in self.particles:
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            particle["vy"] += particle["gravity"]
            particle["life"] -= particle["decay"]
            particle["alpha"] = particle["life"] / particle["max_life"]
            
            if particle["type"] == "spark":
                particle["size"] *= 0.98
            elif particle["type"] == "smoke":
                particle["size"] *= 1.02
    
    def _update_animations(self):
        to_remove = []
        for key, anim in self.animating_elements.items():
            anim["progress"] += anim["speed"]
            if anim["progress"] >= 1.0:
                if anim["loop"]:
                    anim["progress"] = 0
                else:
                    to_remove.append(key)
        
        for key in to_remove:
            del self.animating_elements[key]
    
    def draw(self, surface):
        self._draw_stars(surface)
        self._draw_floating_elements(surface)
        self._draw_particles(surface)
    
    def _draw_stars(self, surface):
        for star in self.stars:
            alpha = int(255 * star["brightness"])
            color = (255, 255, 255, alpha)
            pygame.draw.circle(surface, color, (star["x"], star["y"]), star["size"])
    
    def _draw_floating_elements(self, surface):
        for elem in self.floating_elements:
            if elem["type"] == "cloud":
                self._draw_cloud(surface, elem)
            elif elem["type"] == "particle":
                self._draw_glow_particle(surface, elem)
    
    def _draw_cloud(self, surface, elem):
        color = (255, 255, 255, int(255 * elem["alpha"]))
        pygame.draw.circle(surface, color, (elem["x"], elem["y"]), elem["size"])
        pygame.draw.circle(surface, color, (elem["x"] + elem["size"] * 0.6, elem["y"] - elem["size"] * 0.3), elem["size"] * 0.8)
        pygame.draw.circle(surface, color, (elem["x"] - elem["size"] * 0.6, elem["y"] - elem["size"] * 0.3), elem["size"] * 0.7)
    
    def _draw_glow_particle(self, surface, elem):
        color = self.colors["cyan"]
        alpha = int(255 * elem["alpha"])
        
        for i in range(3):
            radius = elem["size"] * (3 - i) / 3
            glow_alpha = int(alpha * (1 - i * 0.4))
            pygame.draw.circle(surface, (*color, glow_alpha), (elem["x"], elem["y"]), radius)
    
    def _draw_particles(self, surface):
        for particle in self.particles:
            if particle["life"] <= 0:
                continue
            
            color = particle["color"]
            alpha = int(255 * particle["alpha"])
            
            if particle["type"] == "spark":
                pygame.draw.circle(surface, (*color, alpha), (int(particle["x"]), int(particle["y"])), int(particle["size"]))
            elif particle["type"] == "smoke":
                pygame.draw.circle(surface, (100, 100, 120, alpha), (int(particle["x"]), int(particle["y"])), int(particle["size"]))
            elif particle["type"] == "explosion":
                pygame.draw.circle(surface, (*color, alpha), (int(particle["x"]), int(particle["y"])), int(particle["size"]))
            elif particle["type"] == "magic":
                for i in range(3):
                    radius = particle["size"] * (3 - i) / 3
                    pygame.draw.circle(surface, (*color, int(alpha * (1 - i * 0.3))), (int(particle["x"]), int(particle["y"])), int(radius))
    
    def create_explosion(self, x, y, color=(255, 215, 0), count=20):
        for _ in range(count):
            angle = random.uniform(0, 360)
            speed = random.uniform(3, 8)
            self.particles.append({
                "x": x,
                "y": y,
                "vx": speed * math.cos(math.radians(angle)),
                "vy": speed * math.sin(math.radians(angle)),
                "size": random.uniform(2, 6),
                "color": color,
                "life": 1.0,
                "max_life": 1.0,
                "decay": random.uniform(0.03, 0.06),
                "gravity": 0.1,
                "type": "explosion"
            })
    
    def create_sparkle(self, x, y, count=15):
        for _ in range(count):
            angle = random.uniform(0, 360)
            speed = random.uniform(2, 5)
            self.particles.append({
                "x": x,
                "y": y,
                "vx": speed * math.cos(math.radians(angle)),
                "vy": speed * math.sin(math.radians(angle)),
                "size": random.uniform(1, 3),
                "color": (255, 255, 200),
                "life": 0.8,
                "max_life": 0.8,
                "decay": random.uniform(0.04, 0.08),
                "gravity": 0,
                "type": "spark"
            })
    
    def create_magic_circle(self, x, y):
        for i in range(20):
            angle = (i / 20) * 360
            speed = 3
            self.particles.append({
                "x": x + math.cos(math.radians(angle)) * 30,
                "y": y + math.sin(math.radians(angle)) * 30,
                "vx": -speed * math.cos(math.radians(angle)),
                "vy": -speed * math.sin(math.radians(angle)),
                "size": random.uniform(2, 4),
                "color": (138, 43, 226),
                "life": 1.0,
                "max_life": 1.0,
                "decay": 0.02,
                "gravity": 0,
                "type": "magic"
            })
    
    def create_smoke(self, x, y, count=10):
        for _ in range(count):
            self.particles.append({
                "x": x + random.uniform(-10, 10),
                "y": y,
                "vx": random.uniform(-1, 1),
                "vy": random.uniform(-2, -1),
                "size": random.uniform(5, 15),
                "color": (100, 100, 120),
                "life": 1.0,
                "max_life": 1.0,
                "decay": random.uniform(0.01, 0.03),
                "gravity": 0,
                "type": "smoke"
            })


class AnimatedButton:
    """动画按钮 - 现代化交互效果"""
    
    def __init__(self, x, y, width, height, text, callback=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.callback = callback
        self.is_hovered = False
        self.is_pressed = False
        self.scale = 1.0
        self.target_scale = 1.0
        self.animation_progress = 0
        self.animation_type = None
        
        self.colors = {
            "normal": (0, 212, 255),
            "hover": (50, 230, 255),
            "pressed": (0, 180, 220),
            "text": (255, 255, 255)
        }
    
    def update(self, mouse_pos):
        self.is_hovered = (self.x <= mouse_pos[0] <= self.x + self.width and
                          self.y <= mouse_pos[1] <= self.y + self.height)
        
        if self.is_hovered:
            self.target_scale = 1.05
        else:
            self.target_scale = 1.0
        
        self.scale += (self.target_scale - self.scale) * 0.2
        
        if pygame.mouse.get_pressed()[0] and self.is_hovered:
            self.is_pressed = True
        else:
            self.is_pressed = False
    
    def draw(self, surface, font):
        actual_width = self.width * self.scale
        actual_height = self.height * self.scale
        actual_x = self.x - (actual_width - self.width) / 2
        actual_y = self.y - (actual_height - self.height) / 2
        
        if self.is_pressed:
            color = self.colors["pressed"]
        elif self.is_hovered:
            color = self.colors["hover"]
        else:
            color = self.colors["normal"]
        
        pygame.draw.rect(surface, color, (actual_x, actual_y, actual_width, actual_height), border_radius=actual_height//2)
        
        if self.is_hovered:
            glow_surface = pygame.Surface((actual_width + 10, actual_height + 10), pygame.SRCALPHA)
            glow_color = (*color, 50)
            pygame.draw.rect(glow_surface, glow_color, (5, 5, actual_width, actual_height), border_radius=actual_height//2)
            surface.blit(glow_surface, (actual_x - 5, actual_y - 5))
        
        text_surface = font.render(self.text, True, self.colors["text"])
        text_rect = text_surface.get_rect(center=(actual_x + actual_width//2, actual_y + actual_height//2))
        surface.blit(text_surface, text_rect)
    
    def handle_click(self, mouse_pos):
        if self.is_hovered and self.callback:
            self.callback()
            return True
        return False


class ProgressRing:
    """圆形进度条 - 现代化UI组件"""
    
    def __init__(self, x, y, radius, progress=0, color=(0, 212, 255)):
        self.x = x
        self.y = y
        self.radius = radius
        self.progress = progress
        self.target_progress = progress
        self.color = color
        self.thickness = 6
    
    def update(self, target_progress=None):
        if target_progress is not None:
            self.target_progress = max(0, min(1, target_progress))
        
        self.progress += (self.target_progress - self.progress) * 0.1
    
    def draw(self, surface):
        pygame.draw.circle(surface, (40, 50, 65), (self.x, self.y), self.radius, self.thickness)
        
        if self.progress > 0:
            start_angle = -90
            end_angle = start_angle + self.progress * 360
            
            for i in range(3):
                glow_radius = self.radius + i * 2
                glow_thickness = self.thickness - i * 1
                if glow_thickness > 0:
                    glow_color = (*self.color, int(255 * (1 - i * 0.3)))
                    pygame.draw.arc(surface, glow_color, (self.x - glow_radius, self.y - glow_radius, glow_radius * 2, glow_radius * 2), math.radians(start_angle), math.radians(end_angle), glow_thickness)


class IconBadge:
    """图标徽章 - 显示未读数量"""
    
    def __init__(self, x, y, icon, count=0, color=(255, 69, 0)):
        self.x = x
        self.y = y
        self.icon = icon
        self.count = count
        self.color = color
        self.bounce_animation = 0
    
    def update(self, count):
        if count != self.count:
            self.bounce_animation = 1.0
        self.count = count
        
        if self.bounce_animation > 0:
            self.bounce_animation -= 0.1
    
    def draw(self, surface, font_large, font_small):
        icon_surface = font_large.render(self.icon, True, (255, 255, 255))
        surface.blit(icon_surface, (self.x, self.y))
        
        if self.count > 0:
            badge_size = 20
            badge_x = self.x + 25
            badge_y = self.y - 5
            
            bounce_offset = math.sin(self.bounce_animation * 3.14) * 3
            
            pygame.draw.circle(surface, self.color, (badge_x, badge_y + bounce_offset), badge_size//2)
            
            count_text = str(self.count) if self.count <= 99 else "99+"
            count_surface = font_small.render(count_text, True, (255, 255, 255))
            count_rect = count_surface.get_rect(center=(badge_x, badge_y + bounce_offset))
            surface.blit(count_surface, count_rect)


class FadeTransition:
    """淡入淡出过渡效果"""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.alpha = 0
        self.target_alpha = 0
        self.is_active = False
    
    def start_transition(self, direction="fade_out"):
        self.is_active = True
        self.target_alpha = 255 if direction == "fade_out" else 0
        
        if direction == "fade_in":
            self.alpha = 255
    
    def update(self):
        if not self.is_active:
            return
        
        if self.target_alpha > self.alpha:
            self.alpha += 10
            if self.alpha >= self.target_alpha:
                self.alpha = self.target_alpha
        else:
            self.alpha -= 10
            if self.alpha <= self.target_alpha:
                self.alpha = self.target_alpha
        
        if self.alpha == self.target_alpha:
            self.is_active = False
    
    def draw(self, surface):
        if self.alpha > 0:
            overlay = pygame.Surface((self.screen_width, self.screen_height))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(self.alpha)
            surface.blit(overlay, (0, 0))


class TextPopup:
    """文字弹出效果"""
    
    def __init__(self, x, y, text, color=(255, 215, 0), duration=2):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.duration = duration
        self.start_time = time.time()
        self.is_active = True
        self.offset_y = 0
        self.alpha = 255
    
    def update(self):
        if not self.is_active:
            return
        
        elapsed = time.time() - self.start_time
        
        if elapsed >= self.duration:
            self.is_active = False
            return
        
        self.offset_y = -elapsed * 50
        
        if elapsed > self.duration - 0.5:
            self.alpha = int(255 * (1 - (elapsed - (self.duration - 0.5)) / 0.5))
    
    def draw(self, surface, font):
        if not self.is_active:
            return
        
        text_surface = font.render(self.text, True, self.color)
        text_surface.set_alpha(self.alpha)
        
        text_rect = text_surface.get_rect(center=(self.x, self.y + self.offset_y))
        surface.blit(text_surface, text_rect)


class DamageNumber:
    """伤害数字显示"""
    
    def __init__(self, x, y, damage, is_critical=False):
        self.x = x
        self.y = y
        self.damage = damage
        self.is_critical = is_critical
        self.start_time = time.time()
        self.is_active = True
        self.offset_y = 0
        self.alpha = 255
        
        if is_critical:
            self.color = (255, 69, 0)
            self.font_size = 32
        else:
            self.color = (255, 255, 255)
            self.font_size = 24
    
    def update(self):
        if not self.is_active:
            return
        
        elapsed = time.time() - self.start_time
        
        if elapsed >= 1.5:
            self.is_active = False
            return
        
        self.offset_y = -elapsed * 80
        
        if elapsed > 1.0:
            self.alpha = int(255 * (1 - (elapsed - 1.0) / 0.5))
    
    def draw(self, surface):
        if not self.is_active:
            return
        
        font = pygame.font.Font(None, self.font_size)
        text = f"-{self.damage}" if not self.is_critical else f"暴击! -{self.damage}"
        text_surface = font.render(text, True, self.color)
        text_surface.set_alpha(self.alpha)
        
        if self.is_critical:
            for i in range(3):
                glow_surface = font.render(text, True, (255, 255, 255, int(50 / (i + 1))))
                surface.blit(glow_surface, (self.x - text_surface.get_width()//2 - i, self.y + self.offset_y - i))
        
        text_rect = text_surface.get_rect(center=(self.x, self.y + self.offset_y))
        surface.blit(text_surface, text_rect)