import pygame
import random
import math
import time
from ASSET.game_data import data

class EffectSystem:
    def __init__(self):
        self.effects = []
        self.particles = []
        self.camera_shake = 0
        self.camera_shake_max = 20
        self.screen_shake_offset = [0, 0]
        self.motion_blur_frames = []
        self.max_motion_blur_frames = 3
    
    def add_effect(self, effect_type, x, y, duration=2000, **kwargs):
        """添加特效"""
        effect = None
        
        if effect_type == "lightning":
            effect = LightningEffect(x, y, duration, **kwargs)
        elif effect_type == "fire":
            effect = FireEffect(x, y, duration, **kwargs)
        elif effect_type == "smoke":
            effect = SmokeEffect(x, y, duration, **kwargs)
        elif effect_type == "ice":
            effect = IceEffect(x, y, duration, **kwargs)
        elif effect_type == "rainbow":
            effect = RainbowEffect(x, y, duration, **kwargs)
        elif effect_type == "stars":
            effect = StarsEffect(x, y, duration, **kwargs)
        elif effect_type == "explosion":
            effect = ExplosionEffect(x, y, duration, **kwargs)
        elif effect_type == "heal":
            effect = HealEffect(x, y, duration, **kwargs)
        elif effect_type == "poison":
            effect = PoisonEffect(x, y, duration, **kwargs)
        elif effect_type == "shockwave":
            effect = ShockwaveEffect(x, y, duration, **kwargs)
        elif effect_type == "meteor":
            effect = MeteorEffect(x, y, duration, **kwargs)
        elif effect_type == "aurora":
            effect = AuroraEffect(x, y, duration, **kwargs)
        elif effect_type == "screen_shake":
            self.add_screen_shake(kwargs.get("intensity", 10), kwargs.get("duration", 500))
            return
        elif effect_type == "motion_blur":
            self.add_motion_blur(kwargs.get("surface"))
            return
        
        if effect:
            self.effects.append(effect)
    
    def add_screen_shake(self, intensity, duration):
        """添加屏幕晃动效果"""
        self.camera_shake = intensity
        self.shake_duration = duration
        self.shake_start_time = pygame.time.get_ticks()
    
    def update_screen_shake(self):
        """更新屏幕晃动"""
        if self.camera_shake > 0:
            elapsed = pygame.time.get_ticks() - self.shake_start_time
            progress = elapsed / self.shake_duration
            
            if progress >= 1:
                self.camera_shake = 0
                self.screen_shake_offset = [0, 0]
            else:
                intensity = self.camera_shake * (1 - progress)
                self.screen_shake_offset = [
                    random.randint(-intensity, intensity),
                    random.randint(-intensity, intensity)
                ]
    
    def add_motion_blur(self, surface):
        """添加运动模糊效果"""
        if surface:
            self.motion_blur_frames.append(surface.copy())
            if len(self.motion_blur_frames) > self.max_motion_blur_frames:
                self.motion_blur_frames.pop(0)
    
    def draw_motion_blur(self, surface):
        """绘制运动模糊"""
        if self.motion_blur_frames:
            alpha_step = 255 // (len(self.motion_blur_frames) + 1)
            for i, frame in enumerate(reversed(self.motion_blur_frames)):
                frame.set_alpha(alpha_step * (i + 1))
                surface.blit(frame, (0, 0))
            self.motion_blur_frames = []
    
    def update(self):
        """更新所有特效"""
        for effect in self.effects[:]:
            effect.update()
            if effect.is_finished():
                self.effects.remove(effect)
        
        for particle in self.particles[:]:
            particle.update()
            if particle.life <= 0:
                self.particles.remove(particle)
        
        # 更新屏幕晃动
        self.update_screen_shake()
    
    def draw(self, surface):
        """绘制所有特效"""
        for effect in self.effects:
            effect.draw(surface)
        
        for particle in self.particles:
            particle.draw(surface)
    
    def add_particle(self, x, y, color, speed_x, speed_y, size, life, gravity=0):
        """添加粒子"""
        self.particles.append(Particle(x, y, color, speed_x, speed_y, size, life, gravity))

class Particle:
    def __init__(self, x, y, color, speed_x, speed_y, size, life, gravity=0):
        self.x = x
        self.y = y
        self.color = color
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.size = size
        self.life = life
        self.max_life = life
        self.gravity = gravity
    
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.speed_y += self.gravity
        self.life -= 1
        self.size = max(0.5, self.size - 0.05)
    
    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        try:
            pygame.draw.circle(surface, (*self.color[:3], alpha), (int(self.x), int(self.y)), int(self.size))
        except:
            pass

class LightningEffect:
    def __init__(self, x, y, duration=1000, forks=3):
        self.x = x
        self.y = y
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.forks = forks
        self.segments = []
        self.pulse = 0
        self.generate_segments()
    
    def generate_segments(self):
        """生成闪电段"""
        self.segments = []
        for fork in range(self.forks):
            segments = [(self.x, self.y)]
            current_x, current_y = self.x, self.y
            length = random.randint(100, 200)
            
            for _ in range(random.randint(5, 10)):
                current_x += random.randint(-30, 30)
                current_y += random.randint(20, 40)
                segments.append((current_x, current_y))
                if current_y > self.y + length:
                    break
            
            self.segments.append(segments)
    
    def update(self):
        self.pulse = (pygame.time.get_ticks() - self.start_time) % 50 < 25
        if random.random() < 0.3:
            self.generate_segments()
    
    def is_finished(self):
        return pygame.time.get_ticks() - self.start_time >= self.duration
    
    def draw(self, surface):
        if not self.pulse:
            return
        
        for segments in self.segments:
            for i in range(len(segments) - 1):
                x1, y1 = segments[i]
                x2, y2 = segments[i + 1]
                
                for j in range(3):
                    offset = j - 1
                    alpha = max(0, 255 - j * 80)
                    color = (255, 255, 255, alpha)
                    pygame.draw.line(surface, color, 
                                   (x1 + offset, y1), (x2 + offset, y2), 3 - j)

class FireEffect:
    def __init__(self, x, y, duration=3000, intensity=1.0):
        self.x = x
        self.y = y
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.intensity = intensity
        self.flames = []
    
    def update(self):
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed < self.duration:
            if random.random() < 0.3 * self.intensity:
                flame_x = self.x + random.randint(-30, 30)
                flame_y = self.y
                speed_y = -random.uniform(2, 5) * self.intensity
                speed_x = random.uniform(-1, 1)
                life = random.randint(30, 60)
                size = random.randint(5, 15) * self.intensity
                self.flames.append({
                    'x': flame_x,
                    'y': flame_y,
                    'speed_x': speed_x,
                    'speed_y': speed_y,
                    'size': size,
                    'life': life,
                    'max_life': life
                })
        
        for flame in self.flames[:]:
            flame['x'] += flame['speed_x'] + math.sin(pygame.time.get_ticks() * 0.01) * 0.5
            flame['y'] += flame['speed_y']
            flame['life'] -= 1
            flame['size'] *= 0.98
            if flame['life'] <= 0 or flame['size'] < 1:
                self.flames.remove(flame)
    
    def is_finished(self):
        return pygame.time.get_ticks() - self.start_time >= self.duration and len(self.flames) == 0
    
    def draw(self, surface):
        for flame in self.flames:
            alpha = int(255 * (flame['life'] / flame['max_life']))
            ratio = flame['life'] / flame['max_life']
            
            if ratio > 0.7:
                color = (255, 255, 200)
            elif ratio > 0.4:
                color = (255, 150, 50)
            else:
                color = (255, 80, 20)
            
            try:
                pygame.draw.circle(surface, (*color[:3], alpha), 
                                   (int(flame['x']), int(flame['y'])), 
                                   int(flame['size']))
            except:
                pass

class SmokeEffect:
    def __init__(self, x, y, duration=4000, color=(100, 100, 120)):
        self.x = x
        self.y = y
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.color = color
        self.smoke_particles = []
    
    def update(self):
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed < self.duration:
            if random.random() < 0.2:
                self.smoke_particles.append({
                    'x': self.x + random.randint(-20, 20),
                    'y': self.y,
                    'speed_x': random.uniform(-0.5, 0.5),
                    'speed_y': random.uniform(-1, -0.5),
                    'size': random.randint(10, 20),
                    'life': random.randint(100, 150),
                    'max_life': 150
                })
        
        for smoke in self.smoke_particles[:]:
            smoke['x'] += smoke['speed_x']
            smoke['y'] += smoke['speed_y']
            smoke['size'] *= 1.01
            smoke['life'] -= 1
            if smoke['life'] <= 0:
                self.smoke_particles.remove(smoke)
    
    def is_finished(self):
        return pygame.time.get_ticks() - self.start_time >= self.duration and len(self.smoke_particles) == 0
    
    def draw(self, surface):
        for smoke in self.smoke_particles:
            alpha = int(100 * (smoke['life'] / smoke['max_life']))
            try:
                pygame.draw.circle(surface, (*self.color[:3], alpha), 
                                   (int(smoke['x']), int(smoke['y'])), 
                                   int(smoke['size']))
            except:
                pass

class IceEffect:
    def __init__(self, x, y, duration=2000, radius=50):
        self.x = x
        self.y = y
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.radius = radius
        self.current_radius = 0
        self.crystals = []
    
    def update(self):
        elapsed = pygame.time.get_ticks() - self.start_time
        progress = elapsed / self.duration
        
        self.current_radius = self.radius * min(1, progress * 2)
        
        if progress < 0.3:
            for _ in range(2):
                angle = random.uniform(0, math.pi * 2)
                distance = random.uniform(0, self.current_radius)
                self.crystals.append({
                    'x': self.x + math.cos(angle) * distance,
                    'y': self.y + math.sin(angle) * distance,
                    'size': random.randint(3, 8),
                    'rotation': random.uniform(0, math.pi * 2),
                    'life': random.randint(50, 100)
                })
        
        for crystal in self.crystals[:]:
            crystal['rotation'] += 0.02
            crystal['life'] -= 1
            if crystal['life'] <= 0:
                self.crystals.remove(crystal)
    
    def is_finished(self):
        return pygame.time.get_ticks() - self.start_time >= self.duration
    
    def draw(self, surface):
        # 绘制冰霜圆环
        for i in range(3):
            ring_radius = int(self.current_radius - i * 10)
            if ring_radius > 0:
                alpha = max(0, 150 - i * 50)
                pygame.draw.circle(surface, (150, 200, 255, alpha), 
                                   (self.x, self.y), ring_radius, 2)
        
        # 绘制冰晶
        for crystal in self.crystals:
            alpha = int(200 * (crystal['life'] / 100))
            try:
                points = []
                for j in range(6):
                    angle = crystal['rotation'] + j * math.pi / 3
                    length = crystal['size'] * (1 + (j % 2) * 0.5)
                    px = crystal['x'] + math.cos(angle) * length
                    py = crystal['y'] + math.sin(angle) * length
                    points.append((px, py))
                
                pygame.draw.polygon(surface, (150, 200, 255, alpha), points)
            except:
                pass

class RainbowEffect:
    def __init__(self, x, y, duration=3000, height=100):
        self.x = x
        self.y = y
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.height = height
        self.colors = [
            (255, 0, 0),
            (255, 127, 0),
            (255, 255, 0),
            (0, 255, 0),
            (0, 0, 255),
            (75, 0, 130),
            (148, 0, 211)
        ]
    
    def update(self):
        pass
    
    def is_finished(self):
        return pygame.time.get_ticks() - self.start_time >= self.duration
    
    def draw(self, surface):
        elapsed = pygame.time.get_ticks() - self.start_time
        progress = elapsed / self.duration
        
        if progress < 0.5:
            scale = progress * 2
        else:
            scale = 2 - progress
        
        alpha = int(200 * scale)
        
        for i, color in enumerate(self.colors):
            width = 8 - i
            start_angle = math.pi
            end_angle = 0
            
            points = []
            for angle in range(int(start_angle * 100), int(end_angle * 100), -1):
                angle_rad = angle / 100
                radius = self.height + i * 15
                px = self.x + math.cos(angle_rad) * radius * scale
                py = self.y + math.sin(angle_rad) * radius * scale
                points.append((px, py))
            
            if len(points) >= 2:
                pygame.draw.lines(surface, (*color[:3], alpha), False, points, width)

class StarsEffect:
    def __init__(self, x, y, duration=2000, count=20):
        self.x = x
        self.y = y
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.count = count
        self.stars = []
        
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            distance = random.uniform(20, 100)
            self.stars.append({
                'angle': angle,
                'distance': distance,
                'speed': random.uniform(0.5, 2),
                'size': random.randint(2, 5),
                'delay': random.uniform(0, 1)
            })
    
    def update(self):
        pass
    
    def is_finished(self):
        return pygame.time.get_ticks() - self.start_time >= self.duration
    
    def draw(self, surface):
        elapsed = pygame.time.get_ticks() - self.start_time
        progress = elapsed / self.duration
        
        for star in self.stars:
            adjusted_progress = max(0, (progress - star['delay']) / (1 - star['delay'])) if star['delay'] < 1 else 0
            
            if adjusted_progress <= 0:
                continue
            
            current_distance = star['distance'] * min(1, adjusted_progress * star['speed'])
            x = self.x + math.cos(star['angle']) * current_distance
            y = self.y + math.sin(star['angle']) * current_distance
            
            alpha = int(255 * (1 - adjusted_progress))
            size = int(star['size'] * (1 + adjusted_progress))
            
            try:
                pygame.draw.circle(surface, (255, 255, 255, alpha), (int(x), int(y)), size)
            except:
                pass

class ExplosionEffect:
    def __init__(self, x, y, duration=1500, power=1.0):
        self.x = x
        self.y = y
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.power = power
        self.particles = []
        
        for _ in range(int(30 * power)):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 6) * power
            self.particles.append({
                'angle': angle,
                'speed': speed,
                'x': x,
                'y': y,
                'size': random.randint(3, 8),
                'life': random.randint(40, 80),
                'max_life': 80,
                'color': random.choice([(255, 100, 50), (255, 200, 100), (255, 255, 200), (100, 150, 255)])
            })
    
    def update(self):
        for particle in self.particles:
            particle['x'] += math.cos(particle['angle']) * particle['speed']
            particle['y'] += math.sin(particle['angle']) * particle['speed']
            particle['speed'] *= 0.98
            particle['life'] -= 1
            particle['size'] *= 0.99
    
    def is_finished(self):
        return pygame.time.get_ticks() - self.start_time >= self.duration
    
    def draw(self, surface):
        for particle in self.particles:
            if particle['life'] > 0:
                alpha = int(255 * (particle['life'] / particle['max_life']))
                try:
                    pygame.draw.circle(surface, (*particle['color'][:3], alpha), 
                                       (int(particle['x']), int(particle['y'])), 
                                       int(particle['size']))
                except:
                    pass

class HealEffect:
    def __init__(self, x, y, duration=2000):
        self.x = x
        self.y = y
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.particles = []
    
    def update(self):
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed < self.duration:
            if random.random() < 0.3:
                self.particles.append({
                    'x': self.x + random.randint(-30, 30),
                    'y': self.y + random.randint(0, 30),
                    'speed_y': -random.uniform(1, 3),
                    'speed_x': random.uniform(-0.5, 0.5),
                    'size': random.randint(4, 10),
                    'life': random.randint(50, 100),
                    'max_life': 100
                })
        
        for particle in self.particles[:]:
            particle['x'] += particle['speed_x'] + math.sin(pygame.time.get_ticks() * 0.005) * 0.5
            particle['y'] += particle['speed_y']
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def is_finished(self):
        return pygame.time.get_ticks() - self.start_time >= self.duration and len(self.particles) == 0
    
    def draw(self, surface):
        for particle in self.particles:
            alpha = int(200 * (particle['life'] / particle['max_life']))
            color = (100, 255, 150)
            try:
                pygame.draw.circle(surface, (*color[:3], alpha), 
                                   (int(particle['x']), int(particle['y'])), 
                                   int(particle['size']))
            except:
                pass

class PoisonEffect:
    def __init__(self, x, y, duration=3000, radius=60):
        self.x = x
        self.y = y
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.radius = radius
        self.current_radius = 0
        self.bubbles = []
    
    def update(self):
        elapsed = pygame.time.get_ticks() - self.start_time
        progress = elapsed / self.duration
        
        self.current_radius = self.radius * min(1, progress)
        
        if random.random() < 0.15:
            self.bubbles.append({
                'x': self.x + random.randint(-self.current_radius, self.current_radius),
                'y': self.y + random.randint(-self.current_radius, self.current_radius),
                'speed_y': -random.uniform(0.5, 1.5),
                'size': random.randint(3, 6),
                'life': random.randint(40, 80),
                'max_life': 80
            })
        
        for bubble in self.bubbles[:]:
            bubble['y'] += bubble['speed_y']
            bubble['life'] -= 1
            if bubble['life'] <= 0:
                self.bubbles.remove(bubble)
    
    def is_finished(self):
        return pygame.time.get_ticks() - self.start_time >= self.duration
    
    def draw(self, surface):
        # 绘制毒气云
        for i in range(3):
            cloud_radius = int(self.current_radius * (1 - i * 0.2))
            if cloud_radius > 0:
                alpha = max(0, 80 - i * 25)
                pygame.draw.circle(surface, (100, 200, 100, alpha), 
                                   (self.x, self.y), cloud_radius)
        
        # 绘制气泡
        for bubble in self.bubbles:
            alpha = int(150 * (bubble['life'] / bubble['max_life']))
            try:
                pygame.draw.circle(surface, (150, 255, 150, alpha), 
                                   (int(bubble['x']), int(bubble['y'])), 
                                   int(bubble['size']))
            except:
                pass

class ShockwaveEffect:
    def __init__(self, x, y, duration=1500, max_radius=150):
        self.x = x
        self.y = y
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.max_radius = max_radius
        self.current_radius = 0
    
    def update(self):
        elapsed = pygame.time.get_ticks() - self.start_time
        self.current_radius = self.max_radius * (elapsed / self.duration)
    
    def is_finished(self):
        return pygame.time.get_ticks() - self.start_time >= self.duration
    
    def draw(self, surface):
        elapsed = pygame.time.get_ticks() - self.start_time
        progress = elapsed / self.duration
        alpha = int(200 * (1 - progress))
        
        for i in range(3):
            ring_radius = int(self.current_radius - i * 20)
            if ring_radius > 0:
                ring_alpha = max(0, alpha - i * 50)
                pygame.draw.circle(surface, (200, 200, 255, ring_alpha), 
                                   (self.x, self.y), ring_radius, 3)

class MeteorEffect:
    def __init__(self, x, y, duration=2000, target_x=400, target_y=300):
        self.x = x
        self.y = y
        self.target_x = target_x
        self.target_y = target_y
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.trail = []
    
    def update(self):
        elapsed = pygame.time.get_ticks() - self.start_time
        progress = min(elapsed / self.duration, 1)
        
        self.x = self.x + (self.target_x - self.x) * progress
        self.y = self.y + (self.target_y - self.y) * progress
        
        if random.random() < 0.5:
            self.trail.append({
                'x': self.x + random.randint(-10, 10),
                'y': self.y + random.randint(-10, 10),
                'size': random.randint(5, 15),
                'life': random.randint(30, 50),
                'max_life': 50
            })
        
        for particle in self.trail[:]:
            particle['life'] -= 1
            particle['size'] *= 0.95
            if particle['life'] <= 0 or particle['size'] < 1:
                self.trail.remove(particle)
    
    def is_finished(self):
        return pygame.time.get_ticks() - self.start_time >= self.duration
    
    def draw(self, surface):
        for particle in self.trail:
            alpha = int(200 * (particle['life'] / particle['max_life']))
            color = (255, 150, 50) if particle['life'] > 25 else (255, 200, 100)
            try:
                pygame.draw.circle(surface, (*color[:3], alpha), 
                                   (int(particle['x']), int(particle['y'])), 
                                   int(particle['size']))
            except:
                pass
        
        elapsed = pygame.time.get_ticks() - self.start_time
        progress = min(elapsed / self.duration, 1)
        
        if progress < 1:
            meteor_size = int(15 + progress * 10)
            try:
                pygame.draw.circle(surface, (255, 100, 50), (int(self.x), int(self.y)), meteor_size)
                pygame.draw.circle(surface, (255, 200, 100), (int(self.x), int(self.y)), meteor_size // 2)
            except:
                pass

class AuroraEffect:
    def __init__(self, x, y, duration=5000, width=300):
        self.x = x
        self.y = y
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.width = width
        self.waves = []
        
        for i in range(5):
            self.waves.append({
                'offset': random.uniform(0, math.pi * 2),
                'speed': random.uniform(0.5, 1.5),
                'color': random.choice([(0, 255, 200), (150, 200, 255), (200, 150, 255), (100, 255, 150)]),
                'amplitude': random.uniform(20, 50),
                'frequency': random.uniform(0.01, 0.02)
            })
    
    def update(self):
        pass
    
    def is_finished(self):
        return pygame.time.get_ticks() - self.start_time >= self.duration
    
    def draw(self, surface):
        elapsed = pygame.time.get_ticks() - self.start_time
        
        for wave in self.waves:
            points = []
            for px in range(-self.width // 2, self.width // 2, 5):
                py = math.sin(px * wave['frequency'] + elapsed * 0.001 * wave['speed'] + wave['offset']) * wave['amplitude']
                points.append((self.x + px, self.y + py))
            
            alpha = int(100 + math.sin(elapsed * 0.001 + wave['offset']) * 50)
            pygame.draw.lines(surface, (*wave['color'][:3], alpha), False, points, 3)

class AfterImage:
    """残影效果"""
    def __init__(self, x, y, surface, duration=300, alpha=200, scale=1.0):
        self.x = x
        self.y = y
        self.surface = surface.copy()
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.alpha = alpha
        self.scale = scale
        self.rotation = 0
        self.rotation_speed = random.uniform(-2, 2)
    
    def update(self):
        self.rotation += self.rotation_speed
        self.scale *= 0.98
    
    def is_finished(self):
        return pygame.time.get_ticks() - self.start_time >= self.duration
    
    def draw(self, surface):
        elapsed = pygame.time.get_ticks() - self.start_time
        progress = elapsed / self.duration
        alpha = int(self.alpha * (1 - progress))
        
        if alpha <= 0:
            return
        
        # 缩放和旋转
        if self.scale != 1.0 or self.rotation != 0:
            size = (int(self.surface.get_width() * self.scale), 
                   int(self.surface.get_height() * self.scale))
            scaled_surf = pygame.transform.scale(self.surface, size)
            if self.rotation != 0:
                scaled_surf = pygame.transform.rotate(scaled_surf, self.rotation)
            scaled_surf.set_alpha(alpha)
            rect = scaled_surf.get_rect(center=(self.x, self.y))
            surface.blit(scaled_surf, rect)
        else:
            self.surface.set_alpha(alpha)
            rect = self.surface.get_rect(center=(self.x, self.y))
            surface.blit(self.surface, rect)

class GlowEffect:
    """发光效果"""
    def __init__(self, x, y, radius=30, color=(255, 215, 0), duration=1000, pulse_speed=0.05):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.pulse_speed = pulse_speed
        self.pulse_offset = random.uniform(0, math.pi * 2)
    
    def update(self):
        pass
    
    def is_finished(self):
        return pygame.time.get_ticks() - self.start_time >= self.duration
    
    def draw(self, surface):
        elapsed = pygame.time.get_ticks() - self.start_time
        progress = elapsed / self.duration
        
        if progress >= 1:
            return
        
        pulse = math.sin(elapsed * self.pulse_speed + self.pulse_offset) * 0.3 + 0.7
        alpha = int(150 * (1 - progress) * pulse)
        
        for i in range(3):
            r = int(self.radius * (1 + i * 0.3))
            a = int(alpha * (1 - i * 0.3))
            glow_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color[:3], a), (r, r), r)
            surface.blit(glow_surf, (self.x - r, self.y - r))

# 更新 EffectSystem 以支持新特效
def add_after_image(self, x, y, surface, duration=300, alpha=200):
    """添加残影效果"""
    effect = AfterImage(x, y, surface, duration, alpha)
    self.effects.append(effect)

def add_glow(self, x, y, radius=30, color=(255, 215, 0), duration=1000):
    """添加发光效果"""
    effect = GlowEffect(x, y, radius, color, duration)
    self.effects.append(effect)

# 添加到 EffectSystem 类
EffectSystem.add_after_image = add_after_image
EffectSystem.add_glow = add_glow

effect_system = EffectSystem()

def init_effect_system():
    """初始化特效系统"""
    global effect_system
    effect_system = EffectSystem()

def get_effect_system():
    """获取特效系统实例"""
    return effect_system