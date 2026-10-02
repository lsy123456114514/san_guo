"""科技树系统 - 科技点升级、全局属性加成、前置依赖"""

import os
import pygame
from ASSET.game_data import data, save, TECH_TREE, get_system_font_name, logger, draw_gradient_bg, open_window
from ASSET import safe_exit

# 全局变量（延迟初始化）
screen = None
clock = None
FONT_MAIN = None
FONT_SMALL = None
FONT_TINY = None
FONT_BIG = None

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
    "panel_bg": (30, 30, 55, 200),
    "tech_available": (100, 200, 100),
    "tech_unavailable": (100, 100, 100),
    "tech_active": (255, 215, 0)
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
    
    def draw(self, surface):
        # 按钮颜色
        color = self.hover_color if self.is_hovered else self.normal_color
        if self.is_clicked:
            color = COLORS["accent_blue_dark"]
        
        # 绘制按钮
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, COLORS["text_white"], self.rect, 2, border_radius=10)
        
        # 文字
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
    
    def check_click(self, mouse_pos):
        if self.is_hovered and pygame.mouse.get_pressed()[0]:
            if not self.is_clicked:
                self.is_clicked = True
                return True
        elif self.is_clicked:
            self.is_clicked = False
        return False

class TechNode:
    def __init__(self, tech_id, tech_data, x, y, width, height):
        self.tech_id = tech_id
        self.tech_data = tech_data
        self.rect = pygame.Rect(x, y, width, height)
        self.is_hovered = False
    
    def is_unlocked(self):
        """检查科技是否已解锁"""
        return self.tech_id in data["tech_tree"].get("unlocked", [])
    
    def is_max_level(self):
        """检查是否达到最高等级"""
        return self.tech_data.get("children", []) == []
    
    def can_upgrade(self):
        """检查是否可以升级（解锁下一级）"""
        if not self.is_unlocked():
            return False
        
        # 检查资源是否足够
        if not self.tech_data.get("cost"):
            return False
        
        for resource, amount in self.tech_data["cost"].items():
            if data["resources"].get(resource, 0) < amount:
                return False
        
        # 检查是否有子节点未解锁
        return len(self.tech_data.get("children", [])) > 0
    
    @staticmethod
    def _fit_text(font, text, color, max_width, zoom):
        """渲染文本：超宽截断加省略号，并按缩放系数缩放，保证不溢出节点卡片。"""
        surf = font.render(text, True, color)
        if surf.get_width() > max_width:
            cut = text
            while cut and font.render(cut + "…", True, color).get_width() > max_width:
                cut = cut[:-1]
            surf = font.render((cut + "…") if cut else "", True, color)
        if zoom != 1.0:
            w = max(1, int(surf.get_width() * zoom))
            h = max(1, int(surf.get_height() * zoom))
            surf = pygame.transform.smoothscale(surf, (w, h))
        return surf

    def draw(self, surface, offset_x=0, offset_y=0, zoom=1.0):
        # 应用偏移和缩放
        adjusted_rect = pygame.Rect(
            int(self.rect.x * zoom + offset_x), 
            int(self.rect.y * zoom + offset_y), 
            int(self.rect.width * zoom), 
            int(self.rect.height * zoom)
        )
        
        # 确定节点颜色
        if not self.is_unlocked():
            color = COLORS["tech_unavailable"]
        elif self.can_upgrade():
            color = COLORS["tech_available"]
        else:
            color = COLORS["tech_active"]
        
        # 绘制节点背景
        pygame.draw.rect(surface, color, adjusted_rect, border_radius=15)
        pygame.draw.rect(surface, COLORS["text_white"], adjusted_rect, 2, border_radius=15)
        
        # 绘制科技名称（按缩放缩放字面，按节点宽度截断，防止溢出卡片）
        name_surf = self._fit_text(FONT_SMALL, self.tech_data["name"], COLORS["text_white"], self.rect.width - 12, zoom)
        name_rect = name_surf.get_rect(center=(adjusted_rect.centerx, adjusted_rect.y + int(35 * zoom)))
        surface.blit(name_surf, name_rect)
        
        # 绘制科技描述（逐级降字号直到整句放得下，不用省略号截断）
        desc_text = self.tech_data["description"]
        _sz = max(8, int(15 * zoom))
        _desc_font = get_scaled_font(_sz)
        while _sz > 7 and _desc_font.size(desc_text)[0] > self.rect.width - 12:
            _sz -= 1
            _desc_font = get_scaled_font(_sz)
        desc_surf = _desc_font.render(desc_text, True, COLORS["text_gray"])
        desc_rect = desc_surf.get_rect(center=(adjusted_rect.centerx, adjusted_rect.y + int(65 * zoom)))
        surface.blit(desc_surf, desc_rect)
        
        # 绘制升级按钮（宽高已在 adjusted_rect 里缩放过，不再二次缩放；字号随缩放）
        if self.can_upgrade():
            btn_font = get_scaled_font(int(30 * zoom))
            upgrade_btn = Button("解锁", 
                               int(adjusted_rect.x + 25 * zoom), 
                               int(adjusted_rect.y + 95 * zoom), 
                               int(adjusted_rect.width - 50 * zoom), 
                               int(30 * zoom), 
                               btn_font, 
                               normal_color=COLORS["accent_green"])
            mouse_pos = pygame.mouse.get_pos()
            upgrade_btn.check_hover(mouse_pos)
            upgrade_btn.draw(surface)
            return upgrade_btn
        
        return None
    
    def upgrade(self):
        """升级科技（解锁子节点）"""
        if not self.can_upgrade():
            return False
        
        # 扣除资源
        for resource, amount in self.tech_data["cost"].items():
            data["resources"][resource] -= amount
        
        # 解锁子节点
        for child_id in self.tech_data.get("children", []):
            if child_id not in data["tech_tree"].get("unlocked", []):
                data["tech_tree"]["unlocked"].append(child_id)
        
        save()
        return True

_scaled_font_cache = {}

def get_scaled_font(size):
    """按字号取字体（带缓存），用于缩放后仍保持文字与按钮比例。"""
    size = max(8, int(size))
    font = _scaled_font_cache.get(size)
    if font is None:
        font_name = get_system_font_name()
        try:
            if font_name:
                font = pygame.font.SysFont(font_name, size)
            else:
                font = pygame.font.Font(None, size)
        except Exception:
            font = pygame.font.Font(None, size)
        _scaled_font_cache[size] = font
    return font

def init_fonts():
    """初始化字体"""
    global FONT_MAIN, FONT_SMALL, FONT_BIG, FONT_TINY
    FONT_MAIN = get_scaled_font(36)
    FONT_SMALL = get_scaled_font(24)
    FONT_TINY = get_scaled_font(20)
    FONT_BIG = get_scaled_font(50)

def draw_title(surface, text, y_pos, screen_width):
    """绘制标题"""
    title = FONT_BIG.render(text, True, COLORS["accent_gold"])
    title_rect = title.get_rect(center=(screen_width // 2, y_pos))
    surface.blit(title, title_rect)
    
    # 装饰线
    line_y = y_pos + 40
    pygame.draw.line(surface, COLORS["accent_gold"], 
                    (screen_width // 2 - 150, line_y),
                    (screen_width // 2 + 150, line_y), 3)

def draw_resource_panel(surface, x, y, width, height):
    """绘制资源面板"""
    panel_rect = pygame.Rect(x, y, width, height)
    
    # 面板背景
    panel_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (30, 30, 55, 180), (0, 0, width, height), border_radius=10)
    surface.blit(panel_surf, (x, y))
    
    # 边框
    pygame.draw.rect(surface, COLORS["accent_gold"], panel_rect, 2, border_radius=10)
    
    # 资源图标和文字
    resources = [
        ("金元宝", data['resources']['金元宝'], COLORS["accent_gold"]),
        ("水", data['resources']['水'], COLORS["accent_blue"]),
        ("食物", data['resources']['食物'], (200, 150, 100))
    ]
    
    spacing = width // max(1, len(resources))
    for i, (icon, value, color) in enumerate(resources):
        icon_x = x + i * spacing + spacing // 2
        icon_y = y + height // 2
        
        # 资源名称背景
        pygame.draw.rect(surface, (40, 40, 70), (icon_x - 40, icon_y - 12, 80, 24), border_radius=12)
        pygame.draw.rect(surface, color, (icon_x - 40, icon_y - 12, 80, 24), 2, border_radius=12)
        
        # 文字
        text = FONT_SMALL.render(f"{icon}: {value}", True, COLORS["text_white"])
        text_rect = text.get_rect(center=(icon_x, icon_y))
        surface.blit(text, text_rect)

def draw_tech_info(surface, tech_node):
    """绘制科技详细信息"""
    if not tech_node:
        return
    
    panel_width = 300
    panel_height = 200
    panel_x = screen.get_width() - panel_width - 20
    panel_y = 120
    
    # 面板背景
    panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (30, 30, 55, 200), (0, 0, panel_width, panel_height), border_radius=10)
    surface.blit(panel_surf, (panel_x, panel_y))
    
    # 边框
    pygame.draw.rect(surface, COLORS["accent_gold"], 
                    (panel_x, panel_y, panel_width, panel_height), 2, border_radius=10)
    
    # 科技名称
    name_surf = FONT_MAIN.render(tech_node.tech_data["name"], True, COLORS["accent_gold"])
    name_rect = name_surf.get_rect(center=(panel_x + panel_width // 2, panel_y + 30))
    surface.blit(name_surf, name_rect)
    
    # 科技描述
    desc_text = tech_node.tech_data["description"]
    desc_surf = FONT_SMALL.render(desc_text, True, COLORS["text_white"])
    desc_rect = desc_surf.get_rect(center=(panel_x + panel_width // 2, panel_y + 70))
    surface.blit(desc_surf, desc_rect)
    
    # 解锁状态
    status_text = "已解锁" if tech_node.is_unlocked() else "未解锁"
    status_color = COLORS["accent_green"] if tech_node.is_unlocked() else COLORS["text_gray"]
    status_surf = FONT_SMALL.render(f"状态: {status_text}", True, status_color)
    surface.blit(status_surf, (panel_x + 20, panel_y + 100))
    
    # 计算起始y坐标
    start_y = panel_y + 130
    
    # 升级成本
    if tech_node.tech_data.get("cost"):
        cost_text = "解锁成本:"
        cost_surf = FONT_SMALL.render(cost_text, True, COLORS["text_white"])
        surface.blit(cost_surf, (panel_x + 20, start_y))
        
        y_offset = start_y + 30
        for resource, amount in tech_node.tech_data["cost"].items():
            cost_desc = f"{resource}: {amount}"
            cost_desc_surf = FONT_SMALL.render(cost_desc, True, COLORS["text_white"])
            surface.blit(cost_desc_surf, (panel_x + 30, y_offset))
            y_offset += 25
        start_y = y_offset
    
    # 效果
    if tech_node.tech_data.get("effects"):
        effect_text = "效果:"
        effect_surf = FONT_SMALL.render(effect_text, True, COLORS["text_white"])
        surface.blit(effect_surf, (panel_x + 20, start_y))
        
        y_offset = start_y + 30
        for effect, value in tech_node.tech_data["effects"].items():
            # 转换效果名称为中文
            effect_name = effect
            if effect == "resource_gather_speed":
                effect_name = "资源采集速度"
            elif effect == "resource_capacity":
                effect_name = "资源存储容量"
            elif effect == "resource_transport":
                effect_name = "资源运输效率"
            elif effect == "occupation_speed":
                effect_name = "占领速度"
            elif effect == "occupation_cost":
                effect_name = "占领消耗减少"
            elif effect == "combat_attack":
                effect_name = "攻击力"
            elif effect == "combat_defense":
                effect_name = "防御力"
            elif effect == "combat_speed":
                effect_name = "攻击速度"
            elif effect == "combat_critical":
                effect_name = "暴击率"
            elif effect == "element_resistance":
                effect_name = "元素抗性"
            elif effect == "health_regen":
                effect_name = "生命恢复"
            elif effect == "hero_bonus":
                effect_name = "武将属性"
            elif effect == "equip_bonus":
                effect_name = "装备效果"
            elif effect == "research_speed":
                effect_name = "研究速度"
            
            effect_desc = f"{effect_name}: +{int(value * 100)}%"
            effect_surf = FONT_SMALL.render(effect_desc, True, COLORS["text_white"])
            surface.blit(effect_surf, (panel_x + 30, y_offset))
            y_offset += 25

def build_tech_tree():
    """构建科技树节点（整齐树布局：先量子树宽度，再居中放置，避免互相压盖/出屏）"""
    nodes = {}
    node_width = 200
    node_height = 150
    h_gap = 60   # 兄弟子树之间的水平间距
    v_gap = 70   # 层与层之间的垂直间距

    # 自底向上量每棵子树需要的宽度
    widths = {}

    def measure(tech_id):
        children = TECH_TREE[tech_id].get("children", [])
        if children:
            total = sum(measure(c) for c in children) + h_gap * (len(children) - 1)
            widths[tech_id] = max(node_width, total)
        else:
            widths[tech_id] = node_width
        return widths[tech_id]

    # 自顶向下放置：节点在自己子树宽度内水平居中
    def place(tech_id, left, y):
        w = widths[tech_id]
        x = left + (w - node_width) // 2
        nodes[tech_id] = TechNode(tech_id, TECH_TREE[tech_id], x, y, node_width, node_height)
        children = TECH_TREE[tech_id].get("children", [])
        child_left = left
        for child_id in children:
            place(child_id, child_left, y + node_height + v_gap)
            child_left += widths[child_id] + h_gap

    root_order = ["resource", "occupation", "combat", "defense", "special"]
    roots = [t for t in root_order if t in TECH_TREE]
    roots += [t for t in TECH_TREE if not TECH_TREE[t].get("parent") and t not in roots]

    for tech_id in roots:
        measure(tech_id)

    # 根节点排成一行，从 x=0 开始（main() 里再按视口居中）
    x = 0
    for tech_id in roots:
        place(tech_id, x, 0)
        x += widths[tech_id] + h_gap

    return nodes

def draw_connections(surface, nodes, offset_x=0, offset_y=0, zoom=1.0):
    """绘制科技节点之间的连接"""
    for tech_id, node in nodes.items():
        tech_data = TECH_TREE[tech_id]
        children = tech_data.get("children", [])
        
        for child_id in children:
            if child_id in nodes:
                parent_center = (node.rect.centerx * zoom + offset_x, node.rect.centery * zoom + offset_y)
                child_center = (nodes[child_id].rect.centerx * zoom + offset_x, nodes[child_id].rect.centery * zoom + offset_y)
                
                # 绘制连接线
                pygame.draw.line(surface, COLORS["text_gray"], parent_center, child_center, 3)

def main():
    """科技树主循环"""
    global screen, clock
    
    # 初始化pygame
    if not pygame.get_init():
        pygame.init()
    
    # 分辨率适配
    screen = open_window()
    screen_width, screen_height = screen.get_size()
    pygame.display.set_caption("科技树系统")
    clock = pygame.time.Clock()
    
    # 初始化字体
    init_fonts()
    
    # 构建科技树
    tech_nodes = build_tech_tree()

    # 计算树的包围盒，缩放到可视区域并居中（避免出屏/压在标题栏上）
    min_x = min(n.rect.x for n in tech_nodes.values())
    max_x = max(n.rect.right for n in tech_nodes.values())
    min_y = min(n.rect.y for n in tech_nodes.values())
    max_y = max(n.rect.bottom for n in tech_nodes.values())
    tree_w = max(1, max_x - min_x)
    tree_h = max(1, max_y - min_y)

    view_top = 150          # 标题 + 资源栏 + 返回/缩放按钮
    view_bottom = 60        # 底部操作提示
    fit_w = (screen_width - 40) / tree_w
    fit_h = (screen_height - view_top - view_bottom) / tree_h
    zoom_level = max(0.4, min(1.0, fit_w, fit_h))  # 缩放级别（整树塞进视口）

    # 视口中心对准树中心
    view_center_x = screen_width / 2
    view_center_y = view_top + (screen_height - view_top - view_bottom) / 2
    tree_cx = (min_x + max_x) / 2
    tree_cy = (min_y + max_y) / 2
    view_offset = [int(view_center_x - tree_cx * zoom_level),
                   int(view_center_y - tree_cy * zoom_level)]
    drag_start = None
    
    # 返回按钮
    back_button = Button("返回主菜单", 20, 20, 180, 50, FONT_SMALL, normal_color=COLORS["accent_red"])
    
    # 缩放按钮
    zoom_in_button = Button("放大", 220, 20, 80, 50, FONT_SMALL, normal_color=COLORS["accent_blue"])
    zoom_out_button = Button("缩小", 320, 20, 80, 50, FONT_SMALL, normal_color=COLORS["accent_blue"])
    
    # 当前选中的科技节点
    selected_node = None
    
    running = True
    while running:
        # 渐变背景
        draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])
        
        # 标题
        draw_title(screen, "科技树系统", 60, screen_width)
        
        # 资源面板（宽度要放得下三组"名称: 数值"）
        draw_resource_panel(screen, 20, 80, 520, 50)
        
        # 绘制科技连接
        draw_connections(screen, tech_nodes, view_offset[0], view_offset[1], zoom_level)
        
        # 绘制科技节点
        mouse_pos = pygame.mouse.get_pos()
        mx, my = mouse_pos
        upgrade_buttons = []
        
        for tech_id, node in tech_nodes.items():
            # 计算缩放后的碰撞检测
            scaled_rect = pygame.Rect(
                node.rect.x * zoom_level, 
                node.rect.y * zoom_level, 
                node.rect.width * zoom_level, 
                node.rect.height * zoom_level
            )
            node.is_hovered = scaled_rect.collidepoint((mx - view_offset[0], my - view_offset[1]))
            upgrade_btn = node.draw(screen, view_offset[0], view_offset[1], zoom_level)
            if upgrade_btn:
                upgrade_buttons.append((upgrade_btn, node))
            
            # 检查是否选中
            if node.is_hovered:
                selected_node = node
        
        # 绘制科技信息
        draw_tech_info(screen, selected_node)
        
        # 绘制返回按钮
        back_button.check_hover(mouse_pos)
        back_button.draw(screen)
        
        # 绘制缩放按钮
        zoom_in_button.check_hover(mouse_pos)
        zoom_in_button.draw(screen)
        zoom_out_button.check_hover(mouse_pos)
        zoom_out_button.draw(screen)
        
        # 绘制操作提示
        hint_text = "拖动鼠标可移动科技树，点击节点查看详情，点击解锁按钮升级科技，使用放大/缩小按钮调整视图"
        hint_surf = FONT_SMALL.render(hint_text, True, COLORS["text_gray"])
        screen.blit(hint_surf, (20, screen_height - 40))
        
        # 绘制当前缩放级别
        zoom_text = f"缩放: {int(zoom_level * 100)}%"
        zoom_surf = FONT_SMALL.render(zoom_text, True, COLORS["text_white"])
        screen.blit(zoom_surf, (420, 35))
        
        # 拖动科技树
        if pygame.mouse.get_pressed()[0] and my > 150:  # 不在UI区域拖动
            if drag_start is None:
                drag_start = (mx, my)
            else:
                dx = mx - drag_start[0]
                dy = my - drag_start[1]
                view_offset[0] += dx
                view_offset[1] += dy
                drag_start = (mx, my)
        else:
            drag_start = None
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save()
                safe_exit("科技树系统")
                return
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # 检查返回按钮
                    if back_button.check_click(mouse_pos):
                        save()
                        return
                    
                    # 检查缩放按钮
                    if zoom_in_button.check_click(mouse_pos):
                        if zoom_level < 2.0:
                            zoom_level += 0.2
                    elif zoom_out_button.check_click(mouse_pos):
                        if zoom_level > 0.5:
                            zoom_level -= 0.2
                    
                    # 检查升级按钮（按钮矩形已是屏幕坐标）
                    for btn, node in upgrade_buttons:
                        if btn.check_click((mx, my)):
                            if node.upgrade():
                                # 升级成功
                                logger.info(f"成功解锁 {node.tech_data['name']} 的子科技")
        
        clock.tick(60)

if __name__ == '__main__':
    main()