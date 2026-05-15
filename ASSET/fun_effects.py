import pygame
import random
import math

class PetSprite:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.target_x = 0
        self.target_y = 0
        self.speed = 0.15
        self.size = 40
        self.animation_frame = 0
        self.animation_speed = 0.15
        self.direction = 1
        self.emotions = ['happy', 'curious', 'sleepy']
        self.current_emotion = 'happy'
        self.emotion_timer = 0
        
    def update(self, mouse_pos):
        self.target_x, self.target_y = mouse_pos
        
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > 10:
            self.x += dx * self.speed
            self.y += dy * self.speed
            
        if dx > 0:
            self.direction = 1
        elif dx < 0:
            self.direction = -1
            
        self.animation_frame += self.animation_speed
        self.emotion_timer += 1
        
        if self.emotion_timer > 300:
            self.current_emotion = random.choice(self.emotions)
            self.emotion_timer = 0
        
    def draw(self, surface):
        body_color = (255, 180, 100)
        eye_color = (30, 30, 50)
        blush_color = (255, 150, 180)
        
        x, y = int(self.x), int(self.y)
        scale = 1 if self.direction == 1 else -1
        
        if self.current_emotion == 'sleepy':
            eye_width = 2
            eye_height = 8
        else:
            eye_width = 8
            eye_height = 10
        
        pygame.draw.ellipse(surface, body_color, (x - 15, y - 12, 30, 24))
        
        pygame.draw.circle(surface, body_color, (x - 10, y - 8), 8)
        pygame.draw.circle(surface, body_color, (x + 10, y - 8), 8)
        
        eye_offset_y = 0 if self.current_emotion == 'happy' else 3
        
        pygame.draw.ellipse(surface, eye_color, 
            (x - 8 + eye_offset_y, y - 5, eye_width * scale, eye_height))
        pygame.draw.ellipse(surface, eye_color, 
            (x + 8 - eye_offset_y - eye_width, y - 5, eye_width * scale, eye_height))
        
        pygame.draw.circle(surface, blush_color, (x - 18, y + 2), 5)
        pygame.draw.circle(surface, blush_color, (x + 18, y + 2), 5)
        
        if self.current_emotion == 'happy':
            pygame.draw.arc(surface, (100, 50, 50), (x - 6, y + 2, 12, 8), 0.2, math.pi - 0.2, 2)
        else:
            pygame.draw.line(surface, (100, 50, 50), (x - 4, y + 4), (x + 4, y + 4), 2)
        
        tail_wag = math.sin(self.animation_frame * 3) * 5
        pygame.draw.circle(surface, body_color, (x + 22 + tail_wag, y + 5), 6)

class FloatingParticles:
    def __init__(self, screen_width, screen_height):
        self.particles = []
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.types = ['star', 'heart', 'sparkle', 'circle']
        
        for _ in range(30):
            self.add_particle()
            
    def add_particle(self):
        particle = {
            'x': random.randint(0, self.screen_width),
            'y': random.randint(-100, self.screen_height),
            'type': random.choice(self.types),
            'size': random.randint(4, 12),
            'speed': random.uniform(0.2, 0.8),
            'rotation': random.uniform(0, math.pi * 2),
            'rotation_speed': random.uniform(-0.02, 0.02),
            'alpha': random.randint(100, 255),
            'color': random.choice([
                (255, 215, 0), (255, 180, 220), (150, 200, 255),
                (200, 255, 200), (255, 200, 150), (220, 150, 255)
            ])
        }
        self.particles.append(particle)
        
    def update(self):
        for particle in self.particles[:]:
            particle['y'] -= particle['speed']
            particle['rotation'] += particle['rotation_speed']
            particle['x'] += math.sin(particle['rotation'] * 2) * 0.5
            
            if particle['y'] < -50:
                self.particles.remove(particle)
                self.add_particle()
                
    def draw(self, surface):
        for particle in self.particles:
            x, y = int(particle['x']), int(particle['y'])
            size = particle['size']
            color = (*particle['color'], particle['alpha'])
            
            if particle['type'] == 'star':
                self.draw_star(surface, x, y, size, color)
            elif particle['type'] == 'heart':
                self.draw_heart(surface, x, y, size, color)
            elif particle['type'] == 'sparkle':
                self.draw_sparkle(surface, x, y, size, color)
            else:
                pygame.draw.circle(surface, color, (x, y), size, 2)
                
    def draw_star(self, surface, x, y, size, color):
        points = []
        for i in range(5):
            angle = i * 4 * math.pi / 5 - math.pi / 2
            px = x + math.cos(angle) * size
            py = y + math.sin(angle) * size
            points.append((px, py))
        pygame.draw.polygon(surface, color, points)
        
    def draw_heart(self, surface, x, y, size, color):
        scale = size / 10
        points = []
        for t in range(100):
            angle = t / 100 * math.pi * 2
            px = 16 * math.sin(angle) ** 3
            py = 13 * math.cos(angle) - 5 * math.cos(2*angle) - 2 * math.cos(3*angle) - math.cos(4*angle)
            points.append((x + px * scale, y - py * scale))
        pygame.draw.polygon(surface, color, points)
        
    def draw_sparkle(self, surface, x, y, size, color):
        for i in range(4):
            angle = i * math.pi / 2
            end_x = x + math.cos(angle) * size
            end_y = y + math.sin(angle) * size
            pygame.draw.line(surface, color, (x, y), (end_x, end_y), 2)

class DynamicBackground:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.layers = []
        
        for i in range(3):
            layer = {
                'stars': [],
                'scroll_speed': 0.1 + i * 0.05,
                'star_size': 1 + i * 0.5
            }
            for _ in range(50):
                layer['stars'].append({
                    'x': random.randint(0, screen_width),
                    'y': random.randint(0, screen_height),
                    'brightness': random.uniform(0.3, 1)
                })
            self.layers.append(layer)
            
    def update(self):
        for layer in self.layers:
            for star in layer['stars']:
                star['y'] -= layer['scroll_speed']
                if star['y'] < 0:
                    star['y'] = self.screen_height
                    star['x'] = random.randint(0, self.screen_width)
                
    def draw(self, surface):
        gradient = pygame.Surface((self.screen_width, self.screen_height))
        for y in range(self.screen_height):
            ratio = y / self.screen_height
            r = int(10 + ratio * 30)
            g = int(15 + ratio * 40)
            b = int(35 + ratio * 60)
            gradient.fill((r, g, b), (0, y, self.screen_width, 1))
        surface.blit(gradient, (0, 0))
        
        for layer in self.layers:
            for star in layer['stars']:
                alpha = int(100 + star['brightness'] * 155)
                pygame.draw.circle(
                    surface, 
                    (255, 255, 255, alpha),
                    (int(star['x']), int(star['y'])),
                    int(layer['star_size'])
                )
