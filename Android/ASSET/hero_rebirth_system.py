import os
import pygame
import random
from ASSET.game_data import data, save, get_system_font_name
from ASSET import safe_exit

COLORS = {
    "bg_dark": (15, 20, 35),
    "bg_light": (25, 30, 50),
    "accent_gold": (255, 215, 0),
    "accent_blue": (70, 130, 220),
    "accent_green": (60, 200, 100),
    "accent_purple": (180, 100, 220),
    "accent_red": (220, 80, 80),
    "accent_orange": (255, 140, 50),
    "text_white": (255, 255, 255),
    "text_gray": (160, 170, 190),
    "panel_bg": (35, 40, 60, 230),
    "btn_green": (50, 160, 80),
    "btn_green_hover": (70, 200, 100),
    "btn_blue": (60, 120, 200),
    "btn_blue_hover": (80, 160, 255),
    "btn_gold": (200, 160, 50),
    "btn_gold_hover": (255, 200, 80),
    "rebirth_purple": (128, 0, 128),
    "rebirth_gold": (255, 215, 0),
    "rebirth_red": (255, 0, 0)
}

REBIRTH_STAGES = {
    1: {
        "name": "一转·凡",
        "description": "脱胎换骨，初窥天道",
        "icon": "🔮",
        "min_level": 50,
        "min_star": 5,
        "cost": {"将魂": 1000, "金元宝": 500},
        "attribute_multiplier": 1.2,
        "new_skill_chance": 0.3
    },
    2: {
        "name": "二转·灵",
        "description": "灵气贯通，超凡脱俗",
        "icon": "✨",
        "min_level": 80,
        "min_star": 7,
        "cost": {"将魂": 3000, "金元宝": 1500},
        "attribute_multiplier": 1.5,
        "new_skill_chance": 0.5
    },
    3: {
        "name": "三转·仙",
        "description": "羽化登仙，法力无边",
        "icon": "👑",
        "min_level": 100,
        "min_star": 9,
        "cost": {"将魂": 8000, "金元宝": 4000},
        "attribute_multiplier": 2.0,
        "new_skill_chance": 0.8
    },
    4: {
        "name": "四转·圣",
        "description": "超凡入圣，主宰一方",
        "icon": "🏆",
        "min_level": 120,
        "min_star": 10,
        "cost": {"将魂": 20000, "金元宝": 10000},
        "attribute_multiplier": 2.8,
        "new_skill_chance": 1.0
    },
    5: {
        "name": "九转·神",
        "description": "九转成神，傲视天下",
        "icon": "⭐",
        "min_level": 150,
        "min_star": 10,
        "cost": {"将魂": 50000, "金元宝": 30000},
        "attribute_multiplier": 4.0,
        "new_skill_chance": 1.0
    }
}

REBIRTH_SKILLS = {
    "divine_strike": {"name": "神圣一击", "description": "攻击时有15%概率造成3倍伤害", "effect": {"divine_strike": 0.15}, "icon": "⚔️"},
    "immortal_body": {"name": "不灭金身", "description": "受到致命伤害时有20%概率保留1点生命", "effect": {"immortal_body": 0.2}, "icon": "🛡️"},
    "life_drain": {"name": "生命汲取", "description": "攻击时恢复造成伤害的10%生命", "effect": {"life_drain": 0.1}, "icon": "💚"},
    "rage_surge": {"name": "狂暴之力", "description": "生命值低于30%时攻击力提升50%", "effect": {"rage_surge": 0.5}, "icon": "🔥"},
    "element_mastery": {"name": "元素精通", "description": "元素伤害提升30%", "effect": {"element_mastery": 0.3}, "icon": "💎"},
    "critical_master": {"name": "暴击大师", "description": "暴击率提升20%，暴击伤害提升50%", "effect": {"critical_master": {"rate": 0.2, "damage": 0.5}}, "icon": "💥"},
    "speed_blur": {"name": "极速残影", "description": "速度提升30%，有10%概率闪避攻击", "effect": {"speed_blur": {"speed": 0.3, "dodge": 0.1}}, "icon": "⚡"},
    "armor_pierce": {"name": "破甲穿透", "description": "无视目标30%防御力", "effect": {"armor_pierce": 0.3}, "icon": "🔪"},
    "heal_aura": {"name": "治愈光环", "description": "每回合恢复自身5%生命，并为周围友军恢复2%", "effect": {"heal_aura": {"self": 0.05, "ally": 0.02}}, "icon": "🌟"},
    "fear_aura": {"name": "恐惧光环", "description": "降低周围敌人15%攻击力", "effect": {"fear_aura": 0.15}, "icon": "😈"},
    "time_stop": {"name": "时间停滞", "description": "攻击时有5%概率使敌人眩晕1回合", "effect": {"time_stop": 0.05}, "icon": "⏱️"},
    "reincarnation": {"name": "轮回重生", "description": "死亡后有10%概率复活并恢复50%生命", "effect": {"reincarnation": 0.1}, "icon": "♻️"}
}

REBIRTH_EFFECTS = {
    1: {"particle_color": (180, 100, 220), "glow_color": (128, 0, 128), "name_color": (180, 100, 220)},
    2: {"particle_color": (70, 180, 220), "glow_color": (0, 100, 200), "name_color": (100, 200, 255)},
    3: {"particle_color": (255, 215, 0), "glow_color": (255, 165, 0), "name_color": (255, 255, 100)},
    4: {"particle_color": (255, 100, 100), "glow_color": (255, 0, 0), "name_color": (255, 150, 150)},
    5: {"particle_color": (255, 200, 100), "glow_color": (255, 215, 0), "name_color": (255, 255, 200)}
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
        if alpha <= 0:
            return
        # 在带 alpha 通道的临时 Surface 上绘制再 blit，确保透明度生效
        r = max(1, int(self.size))
        size = r * 2 + 2
        tmp = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(tmp, (*self.color[:3], alpha), (size // 2, size // 2), r)
        surface.blit(tmp, (int(self.x) - size // 2, int(self.y) - size // 2))

class Button:
    def __init__(self, text, x, y, width, height, font, normal_color=COLORS["btn_blue"], hover_color=COLORS["btn_blue_hover"]):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.is_hovered = False
    
    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
    
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.normal_color

        if self.rect.height > 0:
            for i in range(self.rect.height):
                ratio = i / self.rect.height
                r = int(color[0] * (1 - ratio * 0.3))
                g = int(color[1] * (1 - ratio * 0.3))
                b = int(color[2] * (1 - ratio * 0.3))
                pygame.draw.line(surface, (r, g, b),
                               (self.rect.x, self.rect.y + i),
                               (self.rect.x + self.rect.width, self.rect.y + i))
        else:
            pygame.draw.rect(surface, color, self.rect)
        
        pygame.draw.rect(surface, COLORS["text_white"], self.rect, 2, border_radius=8)
        
        text_surf = self.font.render(self.text, True, COLORS["text_white"])
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

class HeroRebirthSystem:
    def __init__(self):
        self._init_data()
    
    def _init_data(self):
        if "hero_rebirth" not in data:
            data["hero_rebirth"] = {}
        save()
    
    def get_rebirth_stage(self, hero_name):
        return data.get("hero_rebirth", {}).get(hero_name, 0)
    
    def can_rebirth(self, hero_name):
        hero_mgmt = data.get("hero_management")
        if not isinstance(hero_mgmt, dict):
            return False, "武将数据不存在"
        heroes = hero_mgmt.get("heroes")
        if not isinstance(heroes, dict):
            return False, "武将数据不存在"

        hero = heroes.get(hero_name)
        if not hero:
            return False, "武将不存在"
        
        current_stage = self.get_rebirth_stage(hero_name)
        if current_stage >= len(REBIRTH_STAGES):
            return False, "已达到最高转生境界"
        
        next_stage = REBIRTH_STAGES[current_stage + 1]
        
        hero_level = hero.get("level", 1)
        hero_star = hero.get("star", 1)
        
        if hero_level < next_stage["min_level"]:
            return False, f"等级不足！需要{next_stage['min_level']}级"
        
        if hero_star < next_stage["min_star"]:
            return False, f"星级不足！需要{next_stage['min_star']}星"
        
        for resource, amount in next_stage["cost"].items():
            if data.get("resources", {}).get(resource, 0) < amount:
                return False, f"资源不足：{resource}"
        
        return True, "可以转生"
    
    def rebirth(self, hero_name):
        can_do, msg = self.can_rebirth(hero_name)
        if not can_do:
            return False, msg, None
        
        current_stage = self.get_rebirth_stage(hero_name)
        next_stage_data = REBIRTH_STAGES[current_stage + 1]
        
        for resource, amount in next_stage_data["cost"].items():
            if "resources" not in data:
                data["resources"] = {}
            data["resources"][resource] = data["resources"].get(resource, 0) - amount

        if "hero_rebirth" not in data:
            data["hero_rebirth"] = {}
        data["hero_rebirth"][hero_name] = current_stage + 1

        hero = data.get("hero_management", {}).get("heroes", {}).get(hero_name)
        if not hero:
            return False, "武将不存在", None
        prev_stage = REBIRTH_STAGES.get(current_stage, {"attribute_multiplier": 1.0})
        prev_mult = prev_stage["attribute_multiplier"]
        new_mult = next_stage_data["attribute_multiplier"]
        # 倍率比：从上一阶到下一阶的实际增幅
        mult_ratio = new_mult / prev_mult if prev_mult > 0 else new_mult

        base_stats = hero.get("base_stats", {})
        if base_stats:
            # 有原始基础属性时，从原始值重新计算（new_mult 是相对于初始值的总倍率）
            for stat, value in base_stats.items():
                if stat in ["attack", "defense", "health", "speed"]:
                    hero[stat] = int(value * new_mult)
        else:
            # 无 base_stats 时，对当前属性应用倍率比
            for stat in ["attack", "defense", "health", "speed"]:
                if stat in hero and isinstance(hero[stat], (int, float)):
                    hero[stat] = int(hero[stat] * mult_ratio)
        
        hero["max_health"] = hero.get("health", 100)
        hero["current_health"] = hero["max_health"]
        
        new_skill = None
        if random.random() < next_stage_data["new_skill_chance"]:
            available_skills = [k for k in REBIRTH_SKILLS.keys() 
                              if k not in hero.get("rebirth_skills", [])]
            if available_skills:
                new_skill_key = random.choice(available_skills)
                new_skill = REBIRTH_SKILLS[new_skill_key]
                if "rebirth_skills" not in hero:
                    hero["rebirth_skills"] = []
                hero["rebirth_skills"].append(new_skill_key)
        
        save()
        
        return True, f"转生成功！{hero_name} 达到{next_stage_data['name']}境界", new_skill
    
    def get_rebirth_bonus(self, hero_name):
        stage = self.get_rebirth_stage(hero_name)
        if stage == 0:
            return {}

        stage_data = REBIRTH_STAGES.get(stage)
        if not stage_data:
            return {}
        bonus = {"attribute_multiplier": stage_data["attribute_multiplier"]}
        
        if "hero_management" in data and hero_name in data.get("hero_management", {}).get("heroes", {}):
            hero = data["hero_management"]["heroes"][hero_name]
            for skill_key in hero.get("rebirth_skills", []):
                skill = REBIRTH_SKILLS.get(skill_key)
                if skill:
                    bonus[skill_key] = skill
        
        return bonus

_bg_cache = {}
_bg_cache_key = None

def draw_gradient_background(surface, color1, color2):
    global _bg_cache_key
    width, height = surface.get_size()
    cache_key = (width, height, color1, color2)
    if cache_key != _bg_cache_key:
        bg = pygame.Surface((width, height))
        for y in range(height):
            ratio = y / height if height > 0 else 0
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            pygame.draw.line(bg, (r, g, b), (0, y), (width, y))
        _bg_cache[cache_key] = bg
        _bg_cache_key = cache_key
    surface.blit(_bg_cache.get(cache_key), (0, 0))

def draw_title(surface, text, y, screen_width, font):
    for offset in range(5, 0, -1):
        alpha = max(0, 50 - offset * 8)
        glow_surf = font.render(text, True, COLORS["accent_gold"][:3])
        glow_surf.set_alpha(alpha)
        glow_rect = glow_surf.get_rect(center=(screen_width // 2, y))
        surface.blit(glow_surf, (glow_rect.x - offset, glow_rect.y))
        surface.blit(glow_surf, (glow_rect.x + offset, glow_rect.y))
    
    title = font.render(text, True, COLORS["accent_gold"])
    title_rect = title.get_rect(center=(screen_width // 2, y))
    
    shadow = font.render(text, True, (0, 0, 0))
    surface.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
    surface.blit(title, title_rect)

def draw_hero_card(surface, hero_name, hero_data, rebirth_stage, x, y, width, height, font_main, font_small):
    stage = rebirth_stage
    if stage > 0:
        effect = REBIRTH_EFFECTS.get(stage, REBIRTH_EFFECTS[1])
        name_color = effect["name_color"]
        border_color = effect["glow_color"]
    else:
        name_color = COLORS["text_white"]
        border_color = COLORS["text_gray"]
    
    card_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(card_surf, COLORS["panel_bg"], (0, 0, width, height), border_radius=12)
    surface.blit(card_surf, (x, y))
    pygame.draw.rect(surface, border_color, (x, y, width, height), 2, border_radius=12)
    
    if stage > 0:
        stage_data = REBIRTH_STAGES.get(stage)
        if stage_data:
            stage_icon_font = pygame.font.Font(None, 35)
            icon_surf = stage_icon_font.render(stage_data["icon"], True, border_color)
            surface.blit(icon_surf, (x + 10, y + 10))

            stage_text = stage_data["name"]
            stage_surf = font_small.render(stage_text, True, border_color)
            surface.blit(stage_surf, (x + 50, y + 12))
    
    name_surf = font_main.render(hero_name, True, name_color)
    name_rect = name_surf.get_rect(center=(x + width // 2, y + 45))
    surface.blit(name_surf, name_rect)
    
    level_text = f"Lv.{hero_data.get('level', 1)}"
    level_surf = font_small.render(level_text, True, COLORS["accent_green"])
    surface.blit(level_surf, (x + 10, y + 70))
    
    star_text = f"⭐ x{hero_data.get('star', 1)}"
    star_surf = font_small.render(star_text, True, COLORS["accent_gold"])
    surface.blit(star_surf, (x + width - 10 - star_surf.get_width(), y + 70))
    
    attack_text = f"⚔️ {hero_data.get('attack', 0)}"
    attack_surf = font_small.render(attack_text, True, COLORS["accent_red"])
    surface.blit(attack_surf, (x + 10, y + 95))
    
    defense_text = f"🛡️ {hero_data.get('defense', 0)}"
    defense_surf = font_small.render(defense_text, True, COLORS["accent_blue"])
    surface.blit(defense_surf, (x + width // 2 - 30, y + 95))
    
    health_text = f"❤️ {hero_data.get('health', 0)}"
    health_surf = font_small.render(health_text, True, COLORS["accent_green"])
    surface.blit(health_surf, (x + width - 10 - health_surf.get_width(), y + 95))
    
    if stage > 0 and "rebirth_skills" in hero_data:
        skills = hero_data["rebirth_skills"]
        skill_y = y + 120
        for skill_key in skills[:2]:
            skill_data = REBIRTH_SKILLS.get(skill_key, {})
            skill_text = f"{skill_data.get('icon', '✨')} {skill_data.get('name', '未知')}"
            skill_surf = font_small.render(skill_text, True, COLORS["accent_purple"])
            surface.blit(skill_surf, (x + 10, skill_y))
            skill_y += 20
    
    return stage

def main(screen=None):
    try:
        if not pygame.get_init():
            pygame.init()

        if screen is not None:
            # 使用主菜单传入的共享窗口
            SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
        else:
            if 'ANDROID_DATA' in os.environ:
                info = pygame.display.Info()
                SCREEN_WIDTH = info.current_w
                SCREEN_HEIGHT = info.current_h
            else:
                resolution = (data.get('settings', {}) or {}).get('graphics', {}).get('resolution', '900x700')
                try:
                    width, height = map(int, resolution.split('x'))
                    SCREEN_WIDTH = width
                    SCREEN_HEIGHT = height
                except (ValueError, AttributeError):
                    SCREEN_WIDTH = 900
                    SCREEN_HEIGHT = 700
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        pygame.display.set_caption("武将转生系统")
        clock = pygame.time.Clock()
        
        scale = min(SCREEN_WIDTH / 900, SCREEN_HEIGHT / 700)
        
        def init_font(size):
            font_name = get_system_font_name()
            adjusted_size = int(size * scale)
            try:
                return pygame.font.SysFont(font_name, adjusted_size)
            except Exception:
                return pygame.font.Font(None, adjusted_size)
        
        font_title = init_font(48)
        font_main = init_font(28)
        font_small = init_font(22)
        
        rebirth_system = HeroRebirthSystem()
        
        particles = []
        
        message = ""
        show_message = False
        message_timer = 0
        
        selected_hero = None
        
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            
            draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
            
            if random.random() < 0.05:
                particles.append(Particle(
                    random.randint(0, SCREEN_WIDTH),
                    random.randint(0, SCREEN_HEIGHT),
                    COLORS["accent_purple"], 0.5, 2, 100
                ))
            
            for p in particles[:]:
                p.update()
                p.draw(screen)
                if p.life <= 0:
                    particles.remove(p)
            
            draw_title(screen, "武将转生系统", SCREEN_HEIGHT * 0.08, SCREEN_WIDTH, font_title)
            
            heroes = data.get("hero_management", {}).get("heroes", {}) if isinstance(data.get("hero_management"), dict) else {}

            hero_buttons = []  # 预初始化，避免无武将时事件处理 NameError

            if heroes:
                card_width = min(200, SCREEN_WIDTH * 0.22)
                card_height = min(170, SCREEN_HEIGHT * 0.24)
                cols = max(1, min(4, int(SCREEN_WIDTH // (card_width + 15))))
                start_x = (SCREEN_WIDTH - (cols * card_width + (cols - 1) * 15)) // 2

                for i, (hero_name, hero_data) in enumerate(heroes.items()):
                    row = i // cols
                    col = i % cols
                    x = start_x + col * (card_width + 15)
                    y = SCREEN_HEIGHT * 0.18 + row * (card_height + 15)
                    
                    if y > SCREEN_HEIGHT - 200:
                        continue
                    
                    stage = draw_hero_card(screen, hero_name, hero_data, 
                                         rebirth_system.get_rebirth_stage(hero_name),
                                         x, y, card_width, card_height, font_main, font_small)
                    
                    card_rect = pygame.Rect(x, y, card_width, card_height)
                    is_selected = selected_hero == hero_name
                    if is_selected:
                        pygame.draw.rect(screen, COLORS["accent_gold"], card_rect, 4, border_radius=12)
                    
                    hero_buttons.append((card_rect, hero_name))
                
                if selected_hero and selected_hero in heroes:
                    hero = heroes[selected_hero]
                    current_stage = rebirth_system.get_rebirth_stage(selected_hero)
                    
                    info_panel_x = SCREEN_WIDTH * 0.05
                    info_panel_y = SCREEN_HEIGHT * 0.75
                    info_panel_width = SCREEN_WIDTH * 0.9
                    info_panel_height = SCREEN_HEIGHT * 0.18
                    
                    info_surf = pygame.Surface((info_panel_width, info_panel_height), pygame.SRCALPHA)
                    pygame.draw.rect(info_surf, COLORS["panel_bg"], (0, 0, info_panel_width, info_panel_height), border_radius=12)
                    screen.blit(info_surf, (info_panel_x, info_panel_y))
                    
                    if current_stage > 0:
                        stage_data = REBIRTH_STAGES.get(current_stage)
                        if stage_data:
                            effect_data = REBIRTH_EFFECTS.get(current_stage, REBIRTH_EFFECTS[1])
                            stage_text = font_main.render(f"当前境界: {stage_data['name']} - {stage_data['description']}", True, effect_data["name_color"])
                            screen.blit(stage_text, (info_panel_x + 20, info_panel_y + 10))

                            bonus_text = f"属性倍率: {stage_data['attribute_multiplier']}x"
                            bonus_surf = font_small.render(bonus_text, True, COLORS["accent_gold"])
                            screen.blit(bonus_surf, (info_panel_x + 20, info_panel_y + 45))
                    else:
                        no_stage_text = font_main.render("当前境界: 未转生", True, COLORS["text_gray"])
                        screen.blit(no_stage_text, (info_panel_x + 20, info_panel_y + 10))
                    
                    if current_stage < len(REBIRTH_STAGES):
                        next_stage_data = REBIRTH_STAGES[current_stage + 1]
                        can_rebirth, msg = rebirth_system.can_rebirth(selected_hero)
                        
                        if can_rebirth:
                            rebirth_btn = Button(f"🎯 {next_stage_data['icon']} 转生到{next_stage_data['name']}",
                                               info_panel_x + info_panel_width - 300, info_panel_y + 10,
                                               280, 50, font_small, COLORS["btn_gold"], COLORS["btn_gold_hover"])
                            rebirth_btn.update((mx, my))
                            rebirth_btn.draw(screen)
                        else:
                            condition_text = font_small.render(f"转生条件: Lv.{next_stage_data['min_level']}+, {next_stage_data['min_star']}星+, {next_stage_data['cost']['将魂']}将魂, {next_stage_data['cost']['金元宝']}金元宝", 
                                                              True, COLORS["text_gray"])
                            screen.blit(condition_text, (info_panel_x + info_panel_width - 550, info_panel_y + 10))
                            
                            reason_surf = font_small.render(f"未满足: {msg}", True, COLORS["accent_red"])
                            screen.blit(reason_surf, (info_panel_x + info_panel_width - 300, info_panel_y + 45))
                    else:
                        max_stage_text = font_main.render("🎉 已达到最高转生境界！", True, COLORS["accent_gold"])
                        screen.blit(max_stage_text, (info_panel_x + info_panel_width - 350, info_panel_y + 25))
            else:
                empty_text = font_main.render("暂无武将，请先招募", True, COLORS["text_gray"])
                screen.blit(empty_text, (SCREEN_WIDTH // 2 - empty_text.get_width() // 2, SCREEN_HEIGHT // 2))
            
            return_btn = Button("返回", SCREEN_WIDTH - 150, SCREEN_HEIGHT - 70, 120, 50, font_main)
            return_btn.update((mx, my))
            return_btn.draw(screen)
            
            if show_message:
                message_surf = font_main.render(message, True, COLORS["accent_green"])
                message_rect = message_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.9))
                # 在 SRCALPHA Surface 上绘制半透明背景，确保 alpha 生效
                panel_w = message_rect.width + 40
                panel_h = message_rect.height + 20
                msg_panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
                pygame.draw.rect(msg_panel, (35, 40, 60, 230), (0, 0, panel_w, panel_h), border_radius=8)
                screen.blit(msg_panel, (message_rect.x - 20, message_rect.y - 10))
                screen.blit(message_surf, message_rect)
                message_timer += 1
                if message_timer > 60:
                    show_message = False
                    message_timer = 0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    click_x, click_y = event.pos  # 使用点击瞬间的坐标，避免鼠标快速移动时判定错位
                    for rect, hero_name in hero_buttons:
                        if rect.collidepoint(click_x, click_y):
                            selected_hero = hero_name
                            break

                    if selected_hero and selected_hero in heroes:
                        current_stage = rebirth_system.get_rebirth_stage(selected_hero)
                        if current_stage < len(REBIRTH_STAGES):
                            can_rebirth, msg = rebirth_system.can_rebirth(selected_hero)
                            if can_rebirth:
                                rebirth_btn_rect = pygame.Rect(SCREEN_WIDTH * 0.05 + SCREEN_WIDTH * 0.9 - 300,
                                                              SCREEN_HEIGHT * 0.75 + 10, 280, 50)
                                if rebirth_btn_rect.collidepoint(click_x, click_y):
                                    success, msg, new_skill = rebirth_system.rebirth(selected_hero)
                                    message = msg
                                    if new_skill:
                                        message += f"！领悟新技能: {new_skill['name']}"
                                    show_message = True
                                    message_timer = 0

                    if return_btn.rect.collidepoint(click_x, click_y):
                        running = False
            
            pygame.display.flip()
            clock.tick(60)
        
        safe_exit("武将转生系统")
    except Exception as e:
        print(f"异常：{str(e)}")
        safe_exit("武将转生系统", str(e))

if __name__ == "__main__":
    main()