"""武将仓库/背包系统 - 武将管理、分类筛选、一键上阵"""

import os
import pygame
import platform
import random
import math
from ASSET.game_data import data, save, get_system_font_name, load_sound, EQUIP_SKILLS, GUNS, logger, draw_gradient_bg, cull_dead, get_font
from ASSET import safe_exit
from ASSET.anti_decompile import protect_function

# 颜色主题
COLORS = {
    "bg_dark": (15, 15, 25),
    "bg_light": (25, 25, 40),
    "accent_gold": (255, 215, 0),
    "accent_blue": (70, 130, 220),
    "accent_green": (60, 200, 100),
    "accent_purple": (180, 100, 220),
    "text_white": (255, 255, 255),
    "text_gray": (160, 160, 180),
    "panel_bg": (35, 35, 55, 220),
    "btn_green": (50, 160, 80),
    "btn_green_hover": (70, 200, 100),
    "btn_blue": (60, 120, 200),
    "btn_blue_hover": (80, 160, 255)
}

# 武将图标映射
HERO_ICONS = {
    "赵云": "⚔️",
    "关羽": "🔪",
    "张飞": "🪓",
    "诸葛亮": "📜",
    "曹操": "👑",
    "吕布": "🔱",
    "貂蝉": "💃",
    "黄忠": "🏹",
    "马超": "🐎",
    "周瑜": "🔥"
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
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))

class AnimatedButton:
    def __init__(self, x, y, width, height, text, font, 
                 normal_color, hover_color, text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.scale = 1.0
        self.glow_alpha = 0
        self.particles = []
    
    def update(self, mouse_pos):
        was_hovered = self.is_hovered
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        if self.is_hovered:
            self.scale = min(1.05, self.scale + 0.02)
            self.glow_alpha = min(80, self.glow_alpha + 8)
            if not was_hovered:
                for _ in range(3):
                    self.particles.append(Particle(
                        random.randint(self.rect.x, self.rect.x + self.rect.width),
                        self.rect.y + self.rect.height,
                        COLORS["accent_gold"],
                        2, random.randint(2, 4), 20
                    ))
        else:
            self.scale = max(1.0, self.scale - 0.02)
            self.glow_alpha = max(0, self.glow_alpha - 8)
        
        for p in self.particles:
            p.update()
        self.particles[:] = [p for p in self.particles if p.life > 0]

    
    def draw(self, surface):
        # 发光效果
        if self.glow_alpha > 0:
            glow_surf = pygame.Surface((self.rect.width + 16, self.rect.height + 16), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*self.hover_color[:3], self.glow_alpha),
                           (8, 8, self.rect.width, self.rect.height), border_radius=8)
            surface.blit(glow_surf, (self.rect.x - 8, self.rect.y - 8))
        
        # 按钮主体
        scaled_width = int(self.rect.width * self.scale)
        scaled_height = int(self.rect.height * self.scale)
        scaled_x = self.rect.x + (self.rect.width - scaled_width) // 2
        scaled_y = self.rect.y + (self.rect.height - scaled_height) // 2
        scaled_rect = pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)
        
        color = self.hover_color if self.is_hovered else self.normal_color
        
        # 渐变按钮
        for i in range(scaled_height):
            ratio = i / scaled_height
            r = int(color[0] * (1 - ratio * 0.2))
            g = int(color[1] * (1 - ratio * 0.2))
            b = int(color[2] * (1 - ratio * 0.2))
            pygame.draw.line(surface, (r, g, b), 
                           (scaled_x, scaled_y + i), 
                           (scaled_x + scaled_width, scaled_y + i))
        
        pygame.draw.rect(surface, COLORS["text_white"], scaled_rect, 2, border_radius=8)
        
        # 文字
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=scaled_rect.center)
        surface.blit(text_surf, text_rect)
        
        # 粒子
        for p in self.particles:
            p.draw(surface)

def draw_gradient_bg(surface, color1, color2):
    """绘制渐变背景"""
    width, height = surface.get_size()
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))

def draw_star(surface, x, y, size, filled=True):
    """绘制星星"""
    points = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        radius = size if i % 2 == 0 else size // 2
        px = x + math.cos(angle) * radius
        py = y - math.sin(angle) * radius
        points.append((px, py))
    
    color = COLORS["accent_gold"] if filled else COLORS["text_gray"]
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, COLORS["text_white"], points, 1)

def draw_equip_info(surface, x, y, font_small):
    """绘制装备信息"""
    equips = data["equips"]
    equip_types = ["weapon", "armor", "horse", "book"]
    equip_names = {"weapon": "武器", "armor": "防具", "horse": "坐骑", "book": "书籍"}
    
    y_offset = 0
    for equip_type in equip_types:
        level = equips.get(equip_type, 0)
        if equip_type in EQUIP_SKILLS and level in EQUIP_SKILLS[equip_type]:
            skill = EQUIP_SKILLS[equip_type][level]
            if equip_type == "weapon":
                info = f"{equip_names[equip_type]}: {skill['name']} (伤害: {skill['damage']})"
            elif equip_type == "armor":
                info = f"{equip_names[equip_type]}: {skill['name']} (防御: {skill['defense']})"
            elif equip_type == "horse":
                info = f"{equip_names[equip_type]}: {skill['name']} (速度: {skill['speed']})"
            else:  # book
                info = f"{equip_names[equip_type]}: {skill['name']} (暴击: {int(skill['critical'] * 100)}%)"
            
            info_surf = font_small.render(info, True, COLORS["text_white"])
            surface.blit(info_surf, (x, y + y_offset))
            y_offset += 25
    
    # 时间卡信息
    time_cards = ["时间卡", "时间卡+", "时间卡++"]
    has_time_cards = False
    for card in time_cards:
        if data['resources'].get(card, 0) > 0:
            has_time_cards = True
            break
    
    if has_time_cards:
        y_offset += 10
        time_title = font_small.render("⏰ 时间卡", True, COLORS["accent_purple"])
        surface.blit(time_title, (x, y + y_offset))
        y_offset += 25
        
        for card in time_cards:
            amount = data['resources'].get(card, 0)
            if amount > 0:
                card_info = f"{card}: {amount}"
                card_surf = font_small.render(card_info, True, COLORS["text_white"])
                surface.blit(card_surf, (x, y + y_offset))
                y_offset += 20
    
    # 宠物蛋信息
    pet_eggs = ["宠物蛋", "稀有宠物蛋", "史诗宠物蛋", "传说宠物蛋"]
    has_pet_eggs = False
    for egg in pet_eggs:
        if data['resources'].get(egg, 0) > 0:
            has_pet_eggs = True
            break
    
    if has_pet_eggs:
        y_offset += 10
        egg_title = font_small.render("🥚 宠物蛋", True, COLORS["accent_gold"])
        surface.blit(egg_title, (x, y + y_offset))
        y_offset += 25
        
        for egg in pet_eggs:
            amount = data['resources'].get(egg, 0)
            if amount > 0:
                # 根据宠物蛋类型显示不同颜色
                if egg == "宠物蛋":
                    egg_color = COLORS["text_white"]
                elif egg == "稀有宠物蛋":
                    egg_color = (30, 255, 30)  # 绿色
                elif egg == "史诗宠物蛋":
                    egg_color = (0, 100, 255)  # 蓝色
                elif egg == "传说宠物蛋":
                    egg_color = (255, 165, 0)  # 橙色
                else:
                    egg_color = COLORS["text_white"]
                
                egg_info = f"{egg}: {amount}"
                egg_surf = font_small.render(egg_info, True, egg_color)
                surface.blit(egg_surf, (x, y + y_offset))
                y_offset += 20

def draw_hero_card(surface, x, y, width, height, hero_name, fragments, unlocked, star, power, font_small, font_icon, gun_info=None):
    """绘制武将卡片"""
    card_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    bg_color = (45, 45, 70, 230) if unlocked else (35, 35, 50, 200)
    pygame.draw.rect(card_surf, bg_color, (0, 0, width, height), border_radius=12)
    surface.blit(card_surf, (x, y))

    border_color = COLORS["accent_gold"] if unlocked else COLORS["text_gray"]
    pygame.draw.rect(surface, border_color, (x, y, width, height), 2, border_radius=12)

    icon = HERO_ICONS.get(hero_name, "👤")
    icon_surf = font_icon.render(icon, True, COLORS["text_white"])
    surface.blit(icon_surf, (x + 15, y + 15))

    name_surf = font_small.render(hero_name, True, COLORS["accent_gold"] if unlocked else COLORS["text_gray"])
    surface.blit(name_surf, (x + 60, y + 18))

    frag_text = f"碎片: {fragments}"
    if not unlocked:
        frag_text += "/10"
    frag_surf = font_small.render(frag_text, True, COLORS["text_white"])
    surface.blit(frag_surf, (x + 15, y + 55))

    if unlocked:
        star_x = x + 15
        for i in range(5):
            draw_star(surface, star_x + i * 22, y + 85, 10, filled=(i < star))

        power_surf = font_small.render(f"战力: {power}", True, COLORS["accent_blue"])
        surface.blit(power_surf, (x + 15, y + 105))

        if gun_info:
            gun_color = COLORS["accent_red"]
            level = gun_info.get("gun_level", 1)
            multiplier = gun_info.get("gun_multiplier", GUNS[gun_info.get("gun_type", "pistol")]["damage_multiplier"])
            gun_surf = font_small.render(f"🔫 {gun_info['gun_name']} Lv.{level} ({multiplier:.1f}x)", True, gun_color)
            surface.blit(gun_surf, (x + 15, y + 125))

    return unlocked

@protect_function
def main():
    """武将仓库主函数"""
    try:
        # 初始化
        if not pygame.get_init():
            pygame.init()
        
        # 分辨率适配
        if 'ANDROID_DATA' in os.environ:
            info = pygame.display.Info()
            SCREEN_WIDTH = info.current_w
            SCREEN_HEIGHT = info.current_h
        else:
            # 使用设置的分辨率
            resolution = data['settings']['graphics']['resolution']
            try:
                width, height = map(int, resolution.split('x'))
                SCREEN_WIDTH = width
                SCREEN_HEIGHT = height
            except ValueError:
                SCREEN_WIDTH = 800
                SCREEN_HEIGHT = 600
        
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("🏛️ 武将仓库")
        clock = pygame.time.Clock()

        # 字体初始化
        def init_font(size):
            return get_font(size)

        font_title = init_font(36 if not 'ANDROID_DATA' in os.environ else 52)
        font_normal = init_font(24 if not 'ANDROID_DATA' in os.environ else 36)
        font_small = init_font(18 if not 'ANDROID_DATA' in os.environ else 28)
        font_icon = init_font(40 if not 'ANDROID_DATA' in os.environ else 56)

        # 加载音效
        click_sound = load_sound("click.wav")
        success_sound = load_sound("win.wav")

        def play_sound(sound):
            if sound and data['settings']['sound']['enable']:
                try:
                    sound.play()
                except Exception as _e:
                    logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

        # 解锁武将（10碎片）
        def unlock_hero(hero_name):
            if data["hero_fragments"].get(hero_name, 0) >= 10:
                data["hero_fragments"][hero_name] -= 10
                data["heroes"][hero_name] = {"star": 1, "power": 100}
                save()
                return True
            return False

        # 升星武将（碎片需求递增）
        def upgrade_hero(hero_name):
            if hero_name in data["heroes"]:
                current_star = data["heroes"][hero_name]["star"]
                need_fragments = 5 * current_star
                if data["hero_fragments"].get(hero_name, 0) >= need_fragments:
                    data["hero_fragments"][hero_name] -= need_fragments
                    data["heroes"][hero_name]["star"] += 1
                    data["heroes"][hero_name]["power"] += 50 * current_star
                    save()
                    return True
            return False

        def equip_gun(hero_name, gun_type):
            if hero_name not in data["hero_guns"]:
                data["hero_guns"][hero_name] = {}
            data["hero_guns"][hero_name]["gun_type"] = gun_type
            data["hero_guns"][hero_name]["gun_name"] = GUNS[gun_type]["name"]
            data["hero_guns"][hero_name]["gun_level"] = 1
            data["hero_guns"][hero_name]["gun_multiplier"] = GUNS[gun_type]["damage_multiplier"]
            save()
            return True

        def unequip_gun(hero_name):
            if hero_name in data["hero_guns"]:
                del data["hero_guns"][hero_name]
                save()
            return True

        def upgrade_gun(hero_name):
            """升级枪械"""
            if hero_name in data["hero_guns"]:
                gun_info = data["hero_guns"][hero_name]
                gun_type = gun_info.get("gun_type")
                current_level = gun_info.get("gun_level", 1)
                if current_level < 5:
                    # 检查是否有足够的资源
                    upgrade_cost = current_level * 10
                    if data["resources"].get("金元宝", 0) >= upgrade_cost:
                        data["resources"]["金元宝"] -= upgrade_cost
                        gun_info["gun_level"] = current_level + 1
                        # 提升伤害倍率
                        base_multiplier = GUNS[gun_type]["damage_multiplier"]
                        gun_info["gun_multiplier"] = base_multiplier + current_level * 0.3
                        save()
                        return True, "升级成功！"
                    else:
                        return False, "金元宝不足"
                else:
                    return False, "已达最高等级"
            return False, "未装备枪械"

        # 特效
        particles = []
        
        # 背景星星
        stars = []
        for _ in range(30):
            stars.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(1, 2),
                'alpha': random.randint(30, 100),
                'twinkle': random.uniform(0.02, 0.05)
            })

        # 主循环
        running = True
        scroll_offset = 0
        selected_hero_for_gun = None
        showing_gun_select = False
        gun_btns = []
        close_btn = None
        while running:
            mx, my = pygame.mouse.get_pos()
            
            # 渐变背景
            draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])
            
            # 绘制星星
            for star in stars:
                star['alpha'] += math.sin(pygame.time.get_ticks() * star['twinkle']) * 2
                star['alpha'] = max(20, min(100, star['alpha']))
                star_surf = pygame.Surface((star['size'] * 2, star['size'] * 2), pygame.SRCALPHA)
                pygame.draw.circle(star_surf, (255, 255, 255, int(star['alpha'])),
                                 (star['size'], star['size']), star['size'])
                screen.blit(star_surf, (star['x'], star['y']))

            if showing_gun_select and selected_hero_for_gun:
                gun_select_width = min(500, SCREEN_WIDTH * 0.8)
                gun_select_height = min(400, SCREEN_HEIGHT * 0.6)
                gun_select_x = (SCREEN_WIDTH - gun_select_width) // 2
                gun_select_y = (SCREEN_HEIGHT - gun_select_height) // 2

                panel_surf = pygame.Surface((gun_select_width, gun_select_height), pygame.SRCALPHA)
                pygame.draw.rect(panel_surf, (40, 40, 70, 240), (0, 0, gun_select_width, gun_select_height), border_radius=15)
                screen.blit(panel_surf, (gun_select_x, gun_select_y))
                pygame.draw.rect(screen, COLORS["accent_gold"], (gun_select_x, gun_select_y, gun_select_width, gun_select_height), 3, border_radius=15)

                title_surf = font_title.render(f"为 {selected_hero_for_gun} 选择枪械", True, COLORS["accent_gold"])
                title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, gun_select_y + 40))
                screen.blit(title_surf, title_rect)

                gun_btns = []
                gun_y = gun_select_y + 100
                for gun_type, gun_data in GUNS.items():
                    bullet_type = gun_data["bullet_type"]
                    bullet_cost = gun_data["bullets_per_round"]
                    info_text = f"{gun_data['name']} - 倍率: {gun_data['damage_multiplier']}x - 消耗: 每回合{bullet_cost}颗{bullet_type}"

                    has_bullets = data["resources"].get(bullet_type, 0) >= bullet_cost

                    btn_color = COLORS["btn_green"] if has_bullets else (80, 80, 100)
                    btn_hover = COLORS["btn_green_hover"] if has_bullets else (100, 100, 120)

                    btn = AnimatedButton(
                        gun_select_x + 50, gun_y,
                        gun_select_width - 100, 50, info_text, font_small,
                        btn_color, btn_hover
                    )
                    btn.update((mx, my))
                    btn.draw(screen)
                    gun_btns.append((btn, gun_type))
                    gun_y += 65

                close_btn = AnimatedButton(
                    gun_select_x + gun_select_width // 2 - 80, gun_select_y + gun_select_height - 70,
                    160, 45, "关闭", font_normal,
                    (120, 80, 80), (160, 100, 100)
                )
                close_btn.update((mx, my))
                close_btn.draw(screen)

            # 标题
            title_surf = font_title.render("🏛️ 武将仓库", True, COLORS["accent_gold"])
            title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 40))
            screen.blit(title_surf, title_rect)
            
            # 副标题
            subtitle = f"已解锁: {len(data['heroes'])} / {len(data['hero_fragments'])}"
            sub_surf = font_small.render(subtitle, True, COLORS["text_gray"])
            sub_rect = sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 75))
            screen.blit(sub_surf, sub_rect)
            
            # 装备信息
            equip_title = font_normal.render("⚔️ 装备信息", True, COLORS["accent_blue"])
            screen.blit(equip_title, (50, 105))
            draw_equip_info(screen, 50, 135, font_small)

            # 卡片区域（自适应）
            card_width = min(280, SCREEN_WIDTH * 0.35)
            card_height = min(140, SCREEN_HEIGHT * 0.2)
            cards_per_row = max(1, (SCREEN_WIDTH - 60) // (card_width + 20))
            
            unlock_btns = []
            upgrade_btns = []
            equip_gun_btns = []
            unequip_gun_btns = []
            upgrade_gun_btns = []
            gun_select_btns = []

            all_heroes = list(data["hero_fragments"].keys())
            
            if not all_heroes:
                empty_surf = font_normal.render("你还没有任何武将碎片", True, COLORS["text_gray"])
                empty_rect = empty_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                screen.blit(empty_surf, empty_rect)
            else:
                start_y = 240  # 向下移动，避免与装备信息重叠
                for idx, hero in enumerate(all_heroes):
                    row = idx // cards_per_row
                    col = idx % cards_per_row
                    
                    x = 30 + col * (card_width + 20)
                    y = start_y + row * (card_height + 15) - scroll_offset
                    
                    if y > -card_height and y < SCREEN_HEIGHT:
                        fragments = data["hero_fragments"].get(hero, 0)
                        unlocked = hero in data["heroes"]
                        star = data["heroes"][hero]["star"] if unlocked else 0
                        power = data["heroes"][hero]["power"] if unlocked else 0
                        gun_info = data["hero_guns"].get(hero, None)

                        draw_hero_card(screen, x, y, card_width, card_height, hero,
                                     fragments, unlocked, star, power, font_small, font_icon, gun_info)
                        
                        # 解锁按钮
                        if not unlocked and fragments >= 10:
                            btn = AnimatedButton(
                                x + card_width - 90, y + card_height - 45,
                                80, 35, "✨ 解锁", font_small,
                                COLORS["btn_green"], COLORS["btn_green_hover"]
                            )
                            btn.update((mx, my))
                            btn.draw(screen)
                            unlock_btns.append((btn, hero))
                        
                        # 升星按钮
                        if unlocked:
                            need_frag = 5 * star
                            can_upgrade = fragments >= need_frag
                            btn_text = f"⭐ 升星({need_frag})" if can_upgrade else "⭐ 碎片不足"
                            btn_color = COLORS["btn_blue"] if can_upgrade else (80, 80, 100)
                            btn_hover = COLORS["btn_blue_hover"] if can_upgrade else (100, 100, 120)

                            btn = AnimatedButton(
                                x + card_width - 110, y + card_height - 45,
                                100, 35, btn_text, font_small,
                                btn_color, btn_hover
                            )
                            btn.update((mx, my))
                            btn.draw(screen)
                            if can_upgrade:
                                upgrade_btns.append((btn, hero))

                            if gun_info:
                                # 枪械升级按钮
                                gun_level = gun_info.get("gun_level", 1)
                                upgrade_cost = gun_level * 10
                                can_upgrade_gun = gun_level < 5 and data["resources"].get("金元宝", 0) >= upgrade_cost
                                gun_upgrade_text = f"🔫升级({upgrade_cost})" if can_upgrade_gun else "🔫已满级"
                                gun_upgrade_btn = AnimatedButton(
                                    x + card_width - 220, y + card_height - 80,
                                    105, 30, gun_upgrade_text, font_small,
                                    COLORS["accent_purple"] if can_upgrade_gun else (80, 80, 100),
                                    (200, 120, 250) if can_upgrade_gun else (100, 100, 120)
                                )
                                gun_upgrade_btn.update((mx, my))
                                gun_upgrade_btn.draw(screen)
                                if can_upgrade_gun:
                                    upgrade_gun_btns.append((gun_upgrade_btn, hero))
                                
                                # 卸下枪械按钮
                                unequip_btn = AnimatedButton(
                                    x + card_width - 110, y + card_height - 80,
                                    100, 30, "卸下枪械", font_small,
                                    (150, 80, 80), (180, 100, 100)
                                )
                                unequip_btn.update((mx, my))
                                unequip_btn.draw(screen)
                                unequip_gun_btns.append((unequip_btn, hero))
                            else:
                                gun_btn = AnimatedButton(
                                    x + card_width - 110, y + card_height - 80,
                                    100, 30, "装备枪械", font_small,
                                    COLORS["btn_green"], COLORS["btn_green_hover"]
                                )
                                gun_btn.update((mx, my))
                                gun_btn.draw(screen)
                                equip_gun_btns.append((gun_btn, hero))

            # 返回按钮（自适应）
            return_btn_width = min(160, SCREEN_WIDTH * 0.25)
            return_btn_height = min(50, SCREEN_HEIGHT * 0.08)
            return_btn_y = SCREEN_HEIGHT - return_btn_height - 30
            return_btn = AnimatedButton(
                (SCREEN_WIDTH - return_btn_width) // 2, return_btn_y,
                return_btn_width, return_btn_height, "↩️ 返回", font_normal,
                (60, 120, 60), (80, 160, 80)
            )
            return_btn.update((mx, my))
            return_btn.draw(screen)

            # 更新和绘制粒子
            for p in particles[:]:
                p.update()
                p.draw(screen)

            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # 解锁武将
                    for btn, hero in unlock_btns:
                        if btn.rect.collidepoint(mx, my):
                            play_sound(click_sound)
                            if unlock_hero(hero):
                                play_sound(success_sound)
                                # 成功特效
                                for _ in range(20):
                                    particles.append(Particle(
                                        mx, my, COLORS["accent_gold"],
                                        4, random.randint(4, 8), 40
                                    ))
                    # 升星武将
                    for btn, hero in upgrade_btns:
                        if btn.rect.collidepoint(mx, my):
                            play_sound(click_sound)
                            if upgrade_hero(hero):
                                play_sound(success_sound)
                                # 升级特效
                                for _ in range(25):
                                    particles.append(Particle(
                                        mx, my, COLORS["accent_blue"],
                                        5, random.randint(5, 10), 50
                                    ))
                    # 装备枪械
                    for btn, hero in equip_gun_btns:
                        if btn.rect.collidepoint(mx, my):
                            selected_hero_for_gun = hero
                            showing_gun_select = True
                    # 卸下枪械
                    for btn, hero in unequip_gun_btns:
                        if btn.rect.collidepoint(mx, my):
                            play_sound(click_sound)
                            unequip_gun(hero)
                    
                    # 升级枪械
                    for btn, hero in upgrade_gun_btns:
                        if btn.rect.collidepoint(mx, my):
                            play_sound(click_sound)
                            success, msg = upgrade_gun(hero)
                            if success:
                                play_sound(success_sound)
                                # 升级特效
                                for _ in range(20):
                                    particles.append(Particle(
                                        mx, my, COLORS["accent_purple"],
                                        4, random.randint(4, 8), 40
                                    ))

                    if showing_gun_select and selected_hero_for_gun:
                        for btn, gun_type in gun_btns:
                            if btn.rect.collidepoint(mx, my):
                                bullet_type = GUNS[gun_type]["bullet_type"]
                                if data["resources"].get(bullet_type, 0) >= GUNS[gun_type]["bullets_per_round"]:
                                    equip_gun(selected_hero_for_gun, gun_type)
                                    showing_gun_select = False
                                    selected_hero_for_gun = None
                        if close_btn.rect.collidepoint(mx, my):
                            showing_gun_select = False
                            selected_hero_for_gun = None
                    # 返回
                    if return_btn.rect.collidepoint(mx, my):
                        running = False
                if event.type == pygame.MOUSEWHEEL:
                    scroll_offset = max(0, scroll_offset - event.y * 30)

            pygame.display.flip()
            clock.tick(60)

        safe_exit("武将仓库")
    except Exception as e:
        safe_exit("武将仓库", str(e))

if __name__ == "__main__":
    main()
