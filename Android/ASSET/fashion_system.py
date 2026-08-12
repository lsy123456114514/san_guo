"""时装系统 - 时装装备与外观切换"""

import pygame
import json
import os
from ASSET.game_data import data, save, FASHION_ITEMS, get_system_font_name, create_font, load_sound, logger, draw_gradient_bg, cull_dead, get_font
from ASSET import safe_exit

# 颜色定义
COLORS = {
    "bg_dark": (20, 20, 30),
    "bg_light": (30, 30, 50),
    "text_white": (255, 255, 255),
    "accent_gold": (255, 215, 0),
    "accent_green": (50, 205, 50),
    "accent_red": (255, 69, 0),
    "accent_blue": (64, 128, 255),
    "accent_blue_dark": (30, 60, 120),
    "success": (0, 255, 0),
    "error": (255, 0, 0)
}

class Button:
    """按钮类"""
    def __init__(self, text, x, y, width, height, font, normal_color=(50, 150, 200), hover_color=(80, 180, 230)):
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.rect = pygame.Rect(x, y, width, height)
        self.hover = False
    
    def check_hover(self, pos):
        """检查鼠标是否悬停"""
        self.hover = self.rect.collidepoint(pos)
    
    def check_click(self, pos):
        """检查是否点击"""
        return self.rect.collidepoint(pos)
    
    def draw(self, surface):
        """绘制按钮"""
        color = self.hover_color if self.hover else self.normal_color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, COLORS["accent_gold"], self.rect, 2, border_radius=8)
        text_surf = self.font.render(self.text, True, COLORS["text_white"])
        text_rect = text_surf.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        surface.blit(text_surf, text_rect)

def draw_title(surface, text, y, width):
    """绘制标题"""
    font = create_font(get_system_font_name(), 48)
    text_surf = font.render(text, True, COLORS["accent_gold"])
    text_rect = text_surf.get_rect(center=(width // 2, y))
    surface.blit(text_surf, text_rect)
    
    # 标题阴影
    shadow_surf = font.render(text, True, (0, 0, 0, 50))
    surface.blit(shadow_surf, (text_rect.x + 2, text_rect.y + 2))

def show_message(screen, message, font):
    """显示消息"""
    text_surf = font.render(message, True, COLORS["text_white"])
    text_rect = text_surf.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
    
    # 消息背景
    bg_rect = pygame.Rect(text_rect.x - 20, text_rect.y - 10, text_rect.width + 40, text_rect.height + 20)
    pygame.draw.rect(screen, (30, 30, 55, 200), bg_rect, border_radius=10)
    pygame.draw.rect(screen, COLORS["accent_gold"], bg_rect, 2, border_radius=10)
    
    screen.blit(text_surf, text_rect)
    pygame.display.flip()
    pygame.time.wait(2000)

def initialize_fashion_data():
    """初始化时装数据"""
    if "fashion" not in data:
        data["fashion"] = {
            "equipped": {
                "hero_skin": "normal",
                "weapon_skin": "normal",
                "mount_skin": "normal"
            },
            "unlocked": {
                "hero_skins": ["normal"],
                "weapon_skins": ["normal"],
                "mount_skins": ["normal"]
            }
        }
        save()

def check_resource_cost(cost):
    """检查资源是否足够"""
    for resource, amount in cost.items():
        if data.get("resources", {}).get(resource, 0) < amount:
            return False
    return True

def deduct_resources(cost):
    """扣除资源"""
    for resource, amount in cost.items():
        if resource in data.get("resources", {}):
            data["resources"][resource] -= amount
    save()

def unlock_fashion(category, fashion_id):
    """解锁时装"""
    if fashion_id not in data["fashion"]["unlocked"][f"{category}_skins"]:
        data["fashion"]["unlocked"][f"{category}_skins"].append(fashion_id)
        save()

def equip_fashion(category, fashion_id):
    """穿戴时装"""
    data["fashion"]["equipped"][f"{category}_skin"] = fashion_id
    save()

def get_fashion_effects():
    """获取时装效果"""
    effects = {}
    
    # 英雄皮肤效果
    hero_skin = data["fashion"]["equipped"]["hero_skin"]
    if hero_skin in FASHION_ITEMS["hero_skins"]:
        for key, value in FASHION_ITEMS["hero_skins"][hero_skin]["effects"].items():
            effects[key] = effects.get(key, 0) + value
    
    # 武器皮肤效果
    weapon_skin = data["fashion"]["equipped"]["weapon_skin"]
    if weapon_skin in FASHION_ITEMS["weapon_skins"]:
        for key, value in FASHION_ITEMS["weapon_skins"][weapon_skin]["effects"].items():
            effects[key] = effects.get(key, 0) + value
    
    # 坐骑皮肤效果
    mount_skin = data["fashion"]["equipped"]["mount_skin"]
    if mount_skin in FASHION_ITEMS["mount_skins"]:
        for key, value in FASHION_ITEMS["mount_skins"][mount_skin]["effects"].items():
            effects[key] = effects.get(key, 0) + value
    
    return effects

def draw_skin_avatar(surface, category, skin_id, cx, cy, scale=1.0):
    """绘制时装外观小人示意图，颜色随时装变化"""
    # 根据时装id生成主题色
    seed = sum(ord(c) for c in str(skin_id))
    r = (seed * 37 + 60) % 180 + 50
    g = (seed * 73 + 90) % 180 + 50
    b = (seed * 101 + 120) % 180 + 50
    main_color = (r, g, b)
    dark_color = (r // 2 + 20, g // 2 + 20, b // 2 + 20)
    s = scale
    if category == "hero":
        # 武将小人：头 + 头饰 + 身体 + 腰带
        pygame.draw.circle(surface, (245, 220, 180), (int(cx), int(cy - 34 * s)), int(15 * s))
        pygame.draw.circle(surface, main_color, (int(cx), int(cy - 42 * s)), int(6 * s))
        pygame.draw.rect(surface, main_color, (int(cx - 16 * s), int(cy - 16 * s), int(32 * s), int(40 * s)), border_radius=6)
        pygame.draw.rect(surface, dark_color, (int(cx - 16 * s), int(cy + 8 * s), int(32 * s), int(6 * s)))
    elif category == "weapon":
        # 武器：斜向长柄 + 刃
        pygame.draw.line(surface, main_color, (int(cx - 10 * s), int(cy + 34 * s)), (int(cx + 10 * s), int(cy - 34 * s)), max(3, int(5 * s)))
        pygame.draw.circle(surface, main_color, (int(cx + 10 * s), int(cy - 34 * s)), int(6 * s))
        pygame.draw.rect(surface, dark_color, (int(cx - 14 * s), int(cy + 30 * s), int(28 * s), int(6 * s)))
    elif category == "mount":
        # 坐骑：马形（椭圆身体 + 四条腿 + 头）
        pygame.draw.ellipse(surface, main_color, (int(cx - 30 * s), int(cy - 14 * s), int(60 * s), int(28 * s)))
        pygame.draw.rect(surface, dark_color, (int(cx - 24 * s), int(cy + 12 * s), int(8 * s), int(14 * s)))
        pygame.draw.rect(surface, dark_color, (int(cx - 6 * s), int(cy + 12 * s), int(8 * s), int(14 * s)))
        pygame.draw.rect(surface, dark_color, (int(cx + 12 * s), int(cy + 12 * s), int(8 * s), int(14 * s)))
        pygame.draw.rect(surface, dark_color, (int(cx + 26 * s), int(cy + 12 * s), int(8 * s), int(14 * s)))
        pygame.draw.circle(surface, (245, 220, 180), (int(cx - 26 * s), int(cy - 12 * s)), int(7 * s))
    else:
        # 其他：通用旗帜/徽章
        pygame.draw.rect(surface, main_color, (int(cx - 18 * s), int(cy - 20 * s), int(36 * s), int(40 * s)), border_radius=8)
        pygame.draw.circle(surface, dark_color, (int(cx), int(cy)), int(8 * s))

def draw_fashion_preview(screen, category, fashion_id, x, y, width, height):
    """绘制时装预览"""
    # 预览背景
    pygame.draw.rect(screen, (30, 30, 55, 200), (x, y, width, height), border_radius=10)
    pygame.draw.rect(screen, COLORS["accent_gold"], (x, y, width, height), 2, border_radius=10)
    
    # 时装名称
    fashion_name = FASHION_ITEMS[f"{category}_skins"][fashion_id]["name"]
    font = create_font(get_system_font_name(), 24)
    name_surf = font.render(fashion_name, True, COLORS["accent_gold"])
    screen.blit(name_surf, (x + 20, y + 20))
    
    # 时装描述（超长截断，避免顶出卡片）
    description = FASHION_ITEMS[f"{category}_skins"][fashion_id]["description"]
    if len(description) > 16:
        description = description[:16] + "..."
    desc_font = create_font(get_system_font_name(), 16)
    desc_surf = desc_font.render(description, True, COLORS["text_white"])
    screen.blit(desc_surf, (x + 20, y + 50))
    
    # 时装效果
    effects = FASHION_ITEMS[f"{category}_skins"][fashion_id]["effects"]
    if effects:
        effect_y = y + 80
        for effect, value in effects.items():
            effect_text = f"{effect}: +{value}"
            effect_surf = desc_font.render(effect_text, True, COLORS["success"])
            screen.blit(effect_surf, (x + 20, effect_y))
            effect_y += 20
    
    # 外观示意图（人物/武器/坐骑，颜色随时装变化）
    draw_skin_avatar(screen, category, fashion_id, x + width - 70, y + height // 2, 1.0)
    
    # 时装状态
    is_unlocked = fashion_id in data["fashion"]["unlocked"][f"{category}_skins"]
    is_equipped = data["fashion"]["equipped"][f"{category}_skin"] == fashion_id
    
    if is_equipped:
        status_text = "已穿戴"
        status_color = COLORS["accent_green"]
    elif is_unlocked:
        status_text = "已解锁"
        status_color = COLORS["accent_blue"]
    else:
        status_text = "未解锁"
        status_color = COLORS["accent_red"]
    
    status_surf = font.render(status_text, True, status_color)
    screen.blit(status_surf, (x + 20, y + height - 50))
    
    # 穿戴提示
    tip_surf = desc_font.render("穿戴后战斗自动生效", True, COLORS["text_gray"])
    screen.blit(tip_surf, (x + 130, y + height - 50))
    
    # 价格
    cost = FASHION_ITEMS[f"{category}_skins"][fashion_id]["cost"]
    if cost and not is_unlocked:
        cost_text = "价格: "
        for resource, amount in cost.items():
            cost_text += f"{resource} {amount} "
        cost_surf = desc_font.render(cost_text, True, COLORS["accent_gold"])
        screen.blit(cost_surf, (x + 20, y + height - 25))

def fashion_shop(screen, font_main, font_small, clock):
    """时装商店"""
    categories = ["hero", "weapon", "mount"]
    category_names = {"hero": "英雄皮肤", "weapon": "武器皮肤", "mount": "坐骑皮肤"}
    current_category = 0
    scroll_offset = 0
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                elif event.key == pygame.K_LEFT:
                    current_category = (current_category - 1) % len(categories)
                elif event.key == pygame.K_RIGHT:
                    current_category = (current_category + 1) % len(categories)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                
                # 类别按钮
                for i, category in enumerate(categories):
                    cat_x = 100 + i * 200
                    cat_btn = Button(category_names[category], cat_x, 100, 180, 50, font_small)
                    if cat_btn.check_click(mouse_pos):
                        current_category = i
                        scroll_offset = 0  # 切换类别时重置滚动位置
                
                # 时装按钮
                category = categories[current_category]
                fashion_items = list(FASHION_ITEMS[f"{category}_skins"].items())
                for i, (fashion_id, fashion_data) in enumerate(fashion_items):
                    btn_x = 100
                    btn_y = 200 + i * 200 - scroll_offset
                    btn_width = screen.get_width() - 200
                    btn_height = 180
                    
                    btn_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
                    if btn_rect.collidepoint(mouse_pos):
                        is_unlocked = fashion_id in data["fashion"]["unlocked"][f"{category}_skins"]
                        is_equipped = data["fashion"]["equipped"][f"{category}_skin"] == fashion_id
                        
                        if not is_unlocked:
                            cost = fashion_data["cost"]
                            if check_resource_cost(cost):
                                deduct_resources(cost)
                                unlock_fashion(category, fashion_id)
                                show_message(screen, f"成功解锁 {fashion_data['name']}！", font_small)
                            else:
                                show_message(screen, "资源不足！", font_small)
                        elif not is_equipped:
                            equip_fashion(category, fashion_id)
                            show_message(screen, f"成功穿戴 {fashion_data['name']}！", font_small)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 4:  # 鼠标滚轮向上
                scroll_offset = max(0, scroll_offset - 50)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 5:  # 鼠标滚轮向下
                category = categories[current_category]
                fashion_items = list(FASHION_ITEMS[f"{category}_skins"].items())
                max_scroll = max(0, (len(fashion_items) * 200) - (screen.get_height() - 300))
                scroll_offset = min(max_scroll, scroll_offset + 50)
        
        # 绘制背景
        draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])
        
        # 绘制标题
        draw_title(screen, "时装商店", 50, screen.get_width())
        
        # 绘制类别按钮
        category = categories[current_category]
        for i, cat in enumerate(categories):
            cat_x = 100 + i * 200
            cat_btn = Button(category_names[cat], cat_x, 100, 180, 50, font_small)
            cat_btn.check_hover(pygame.mouse.get_pos())
            if cat == category:
                cat_btn.normal_color = COLORS["accent_gold"]
                cat_btn.hover_color = (255, 230, 50)
            cat_btn.draw(screen)
        
        # 绘制时装列表
        fashion_items = list(FASHION_ITEMS[f"{category}_skins"].items())
        for i, (fashion_id, fashion_data) in enumerate(fashion_items):
            x = 100
            y = 200 + i * 200 - scroll_offset
            width = screen.get_width() - 200
            height = 180
            draw_fashion_preview(screen, category, fashion_id, x, y, width, height)
        
        # 绘制滚动条
        total_items = len(fashion_items)
        if total_items > 0:
            total_height = total_items * 200
            visible_height = screen.get_height() - 300
            if total_height > visible_height:
                scrollbar_height = (visible_height / total_height) * visible_height
                scrollbar_y = 200 + (scroll_offset / total_height) * visible_height
                # 滚动条背景
                pygame.draw.rect(screen, (40, 40, 60), (screen.get_width() - 30, 200, 20, visible_height), border_radius=10)
                # 滚动条
                pygame.draw.rect(screen, COLORS["accent_gold"], (screen.get_width() - 28, scrollbar_y, 16, scrollbar_height), border_radius=8)
        
        # 绘制当前效果
        effects = get_fashion_effects()
        if effects:
            effect_y = screen.get_height() - 150
            font = create_font(get_system_font_name(), 20)
            effect_title = font.render("当前时装效果:", True, COLORS["accent_gold"])
            screen.blit(effect_title, (100, effect_y))
            effect_y += 30
            for effect, value in effects.items():
                effect_text = f"{effect}: +{value}"
                effect_surf = font.render(effect_text, True, COLORS["success"])
                screen.blit(effect_surf, (120, effect_y))
                effect_y += 25
        
        # 绘制返回按钮
        back_btn = Button("返回主菜单", 20, screen.get_height() - 60, 180, 50, font_small, normal_color=COLORS["accent_blue_dark"])
        back_btn.check_hover(pygame.mouse.get_pos())
        back_btn.draw(screen)
        
        if back_btn.check_click(pygame.mouse.get_pos()):
            return
        
        pygame.display.flip()
        clock.tick(60)

def main():
    """时装系统主函数"""
    global screen, clock, FONT_MAIN, FONT_SMALL
    
    # 初始化pygame
    pygame.init()
    
    # 设置屏幕：优先复用当前显示表面，避免返回主菜单错位
    cur_surface = pygame.display.get_surface()
    if cur_surface is not None:
        screen = cur_surface
    else:
        screen_width = 1024
        screen_height = 768
        screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("时装系统")
    clock = pygame.time.Clock()
    
    # 加载字体
    font_name = get_system_font_name()
    try:
        if font_name:
            FONT_MAIN = create_font(font_name, 40)
            FONT_SMALL = create_font(font_name, 24)
        else:
            FONT_MAIN = pygame.font.Font(None, 40)
            FONT_SMALL = pygame.font.Font(None, 24)
    except Exception as _e:
        FONT_MAIN = pygame.font.Font(None, 40)
        FONT_SMALL = pygame.font.Font(None, 24)
    
    # 初始化时装数据
    initialize_fashion_data()
    
    # 运行时装商店
    fashion_shop(screen, FONT_MAIN, FONT_SMALL, clock)

if __name__ == "__main__":
    main()