"""交易系统 - 资源买卖与市场交易"""

import os
import pygame
import random
import datetime
from ASSET.game_data import data, save, get_system_font_name, logger, draw_gradient_bg, cull_dead, get_font
from ASSET.languages import get_text
from ASSET import safe_exit

# 颜色主题
COLORS = {
    "bg_dark": (10, 10, 25),
    "bg_light": (20, 20, 45),
    "accent_gold": (255, 215, 0),
    "accent_blue": (70, 130, 180),
    "accent_blue_light": (100, 149, 237),
    "accent_blue_dark": (50, 100, 150),
    "accent_red": (200, 80, 80),
    "accent_green": (80, 180, 80),
    "text_white": (255, 255, 255),
    "text_gray": (180, 180, 200),
    "panel_bg": (30, 30, 55, 200)
}

class Button:
    def __init__(self, text, x, y, width, height, font, 
                 normal_color=COLORS["accent_blue"], 
                 hover_color=COLORS["accent_blue_light"], 
                 text_color=COLORS["text_white"]):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.is_clicked = False
        self.click_timer = 0
    
    def draw(self, surface):
        # 按钮颜色
        color = self.hover_color if self.is_hovered else self.normal_color
        if self.is_clicked:
            color = COLORS["accent_blue_dark"]
        
        # 渐变效果
        for i in range(self.rect.height):
            alpha = 255 - int(50 * (i / self.rect.height))
            gradient_color = tuple(min(255, c + 20) for c in color[:3])
            pygame.draw.line(surface, gradient_color, 
                           (self.rect.x, self.rect.y + i),
                           (self.rect.x + self.rect.width, self.rect.y + i))
        
        # 按钮边框
        pygame.draw.rect(surface, COLORS["text_white"], self.rect, 2, border_radius=10)
        pygame.draw.rect(surface, COLORS["accent_gold"], self.rect, 1, border_radius=10)
        
        # 文字
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        # 文字阴影
        shadow_surf = self.font.render(self.text, True, (0, 0, 0))
        surface.blit(shadow_surf, (text_rect.x + 2, text_rect.y + 2))
        surface.blit(text_surf, text_rect)
    
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

def draw_title(surface, text, y_pos, screen_width, font_big):
    """绘制带特效的标题"""
    # 发光效果
    for offset in range(5, 0, -1):
        alpha = 50 - offset * 8
        glow_surf = font_big.render(text, True, (*COLORS["accent_gold"][:3], alpha))
        glow_rect = glow_surf.get_rect(center=(screen_width // 2, y_pos))
        surface.blit(glow_surf, (glow_rect.x - offset, glow_rect.y))
        surface.blit(glow_surf, (glow_rect.x + offset, glow_rect.y))
    
    # 主标题
    title = font_big.render(text, True, COLORS["accent_gold"])
    title_rect = title.get_rect(center=(screen_width // 2, y_pos))
    
    # 阴影
    shadow = font_big.render(text, True, (0, 0, 0))
    surface.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
    surface.blit(title, title_rect)

def show_message(surface, message, font_main):
    """显示提示消息"""
    screen_width = surface.get_width()
    screen_height = surface.get_height()
    
    # 半透明遮罩
    overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    surface.blit(overlay, (0, 0))
    
    # 消息面板
    panel_width = 400
    panel_height = 150
    panel_x = (screen_width - panel_width) // 2
    panel_y = (screen_height - panel_height) // 2
    
    panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (40, 40, 70, 200), (0, 0, panel_width, panel_height), border_radius=15)
    surface.blit(panel_surf, (panel_x, panel_y))
    
    # 边框
    pygame.draw.rect(surface, COLORS["accent_gold"], 
                    (panel_x, panel_y, panel_width, panel_height), 3, border_radius=15)
    
    # 文字
    text_surf = font_main.render(message, True, COLORS["text_white"])
    text_rect = text_surf.get_rect(center=(screen_width // 2, panel_y + panel_height // 2))
    surface.blit(text_surf, text_rect)
    
    pygame.display.flip()
    pygame.time.wait(2000)

class TradingSystem:
    """交易系统"""
    def __init__(self):
        # 初始化交易数据
        if "trading" not in data:
            data["trading"] = {
                "offers": []
            }
    
    def create_offer(self, item_type, item_name, price):
        """创建交易 offer"""
        offer = {
            "id": f"offer_{datetime.datetime.now().timestamp()}",
            "seller": data.get("username", "player"),
            "item_type": item_type,
            "item_name": item_name,
            "price": price,
            "created_at": datetime.datetime.now().isoformat(),
            "status": "active"
        }
        data["trading"]["offers"].append(offer)
        save()
        return True, "交易 offer 创建成功！"
    
    def buy_item(self, offer_id):
        """购买物品"""
        for offer in data["trading"]["offers"]:
            if offer["id"] == offer_id and offer["status"] == "active":
                # 检查金币是否足够
                if data["resources"].get("金元宝", 0) >= offer["price"]:
                    # 扣除金币
                    data["resources"]["金元宝"] -= offer["price"]
                    # 标记交易完成
                    offer["status"] = "completed"
                    offer["buyer"] = data.get("username", "player")
                    offer["completed_at"] = datetime.datetime.now().isoformat()
                    save()
                    return True, f"购买成功！"
                else:
                    return False, "金币不足"
        return False, "交易 offer 不存在"
    
    def cancel_offer(self, offer_id):
        """取消交易 offer"""
        for offer in data["trading"]["offers"]:
            if offer["id"] == offer_id and offer["status"] == "active":
                offer["status"] = "cancelled"
                offer["cancelled_at"] = datetime.datetime.now().isoformat()
                save()
                return True, "交易 offer 已取消！"
        return False, "交易 offer 不存在或已完成"

def draw_trading_system(screen, font_big, font_main, font_small):
    """绘制交易系统"""
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # 标题
    draw_title(screen, "交易系统", screen_height * 0.1, screen_width, font_big)
    
    trading_system = TradingSystem()
    
    # 交易 offer 列表
    y_offset = screen_height * 0.2
    
    if not data["trading"]["offers"]:
        empty_surf = font_small.render("暂无交易 offer", True, COLORS["text_gray"])
        screen.blit(empty_surf, (60, y_offset))
    else:
        for offer in data["trading"]["offers"]:
            if offer["status"] == "active":
                offer_rect = pygame.Rect(50, y_offset, screen_width - 100, 80)
                
                # 背景
                pygame.draw.rect(screen, (40, 40, 70, 200), offer_rect, border_radius=10)
                pygame.draw.rect(screen, COLORS["accent_gold"], offer_rect, 2, border_radius=10)
                
                # 交易信息
                item_surf = font_main.render(f"{offer['item_name']}", True, COLORS["accent_gold"])
                seller_surf = font_small.render(f"卖家: {offer['seller']}", True, COLORS["text_white"])
                price_surf = font_small.render(f"价格: {offer['price']} 金元宝", True, COLORS["text_gray"])
                
                screen.blit(item_surf, (60, y_offset + 10))
                screen.blit(seller_surf, (60, y_offset + 35))
                screen.blit(price_surf, (200, y_offset + 35))
                
                # 购买按钮
                buy_btn = Button("购买", screen_width - 150, y_offset + 20, 100, 40, font_small, normal_color=COLORS["accent_green"])
                buy_btn.draw(screen)
                
                y_offset += 90

def draw_create_offer(screen, font_big, font_main, font_small):
    """绘制创建交易 offer 界面"""
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # 标题
    draw_title(screen, "创建交易", screen_height * 0.1, screen_width, font_big)
    
    # 表单
    form_y = screen_height * 0.2
    
    # 物品类型
    type_label = font_main.render("物品类型:", True, COLORS["text_white"])
    screen.blit(type_label, (100, form_y))
    
    type_options = ["装备", "道具", "材料"]
    type_rects = []
    for i, option in enumerate(type_options):
        rect = pygame.Rect(250, form_y, 120, 40)
        type_rects.append(rect)
        pygame.draw.rect(screen, (40, 40, 70, 200), rect, border_radius=5)
        pygame.draw.rect(screen, COLORS["accent_gold"], rect, 2, border_radius=5)
        text_surf = font_small.render(option, True, COLORS["text_white"])
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)
        form_y += 50
    
    # 物品名称
    name_label = font_main.render("物品名称:", True, COLORS["text_white"])
    screen.blit(name_label, (100, form_y))
    name_input = pygame.Rect(250, form_y, 300, 40)
    pygame.draw.rect(screen, (40, 40, 70, 200), name_input, border_radius=5)
    pygame.draw.rect(screen, COLORS["accent_gold"], name_input, 2, border_radius=5)
    form_y += 50
    
    # 价格
    price_label = font_main.render("价格:", True, COLORS["text_white"])
    screen.blit(price_label, (100, form_y))
    price_input = pygame.Rect(250, form_y, 200, 40)
    pygame.draw.rect(screen, (40, 40, 70, 200), price_input, border_radius=5)
    pygame.draw.rect(screen, COLORS["accent_gold"], price_input, 2, border_radius=5)
    form_y += 80
    
    # 按钮
    create_btn = Button("创建交易", screen_width // 2 - 100, form_y, 200, 50, font_main, normal_color=COLORS["accent_green"])
    create_btn.draw(screen)

def main():
    """交易系统主函数"""
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
                SCREEN_WIDTH = 900
                SCREEN_HEIGHT = 700
        
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("交易系统")
        clock = pygame.time.Clock()

        # 字体初始化（根据屏幕大小自适应）
        def init_font(size):
            return get_font(size)

        font_big = init_font(48)
        font_main = init_font(32)
        font_small = init_font(24)

        # 系统初始化
        trading_system = TradingSystem()

        # 当前页面
        current_page = "browse"  # browse, create

        # 主循环
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            
            # 渐变背景
            draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])
            
            # 导航按钮
            nav_buttons = [
                ("浏览交易", "browse", 50, SCREEN_HEIGHT - 70),
                ("创建交易", "create", 200, SCREEN_HEIGHT - 70),
                ("返回", "back", SCREEN_WIDTH - 150, SCREEN_HEIGHT - 70)
            ]
            
            for text, page, x, y in nav_buttons:
                btn = Button(text, x, y, 120, 50, font_small)
                btn.check_hover((mx, my))
                btn.draw(screen)
            
            # 绘制当前页面
            if current_page == "browse":
                draw_trading_system(screen, font_big, font_main, font_small)
            elif current_page == "create":
                draw_create_offer(screen, font_big, font_main, font_small)
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # 处理导航按钮
                    for text, page, x, y in nav_buttons:
                        btn = Button(text, x, y, 120, 50, font_small)
                        if btn.rect.collidepoint(event.pos):
                            if page == "back":
                                running = False
                            else:
                                current_page = page
                            break
                    
                    # 处理页面内按钮
                    if current_page == "browse":
                        # 处理交易购买
                        y_offset = SCREEN_HEIGHT * 0.2
                        for offer in data["trading"]["offers"]:
                            if offer["status"] == "active":
                                buy_btn = Button("购买", SCREEN_WIDTH - 150, y_offset + 20, 100, 40, font_small)
                                if buy_btn.rect.collidepoint(event.pos):
                                    success, message = trading_system.buy_item(offer["id"])
                                    show_message(screen, message, font_main)
                                y_offset += 90
                    
                    elif current_page == "create":
                        # 处理创建交易
                        create_btn = Button("创建交易", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT * 0.2 + 230, 200, 50, font_main)
                        if create_btn.rect.collidepoint(event.pos):
                            # 简化处理，直接创建一个测试交易
                            success, message = trading_system.create_offer("装备", "测试装备", 100)
                            show_message(screen, message, font_main)
            
            clock.tick(60)
        
        safe_exit("交易系统")
    except Exception as e:
        logger.info(f"异常：{str(e)}")
        logger.info("详细错误信息：")
        import traceback
        traceback.print_exc()
        safe_exit("交易系统", str(e))

if __name__ == "__main__":
    main()
