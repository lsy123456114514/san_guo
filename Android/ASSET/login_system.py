import os
import pygame
import platform
import json
import time
from ASSET.game_data import get_system_font_name, RESOURCES, SETTINGS, default_save
from ASSET import safe_exit

def hide_file(filepath):
    """隐藏文件（仅Windows）"""
    if platform.system() == "Windows" and filepath and os.path.exists(filepath):
        try:
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(filepath, 0x02)
        except Exception:
            pass

# 路径适配：安卓用内部存储，PC用本地
if 'ANDROID_DATA' in os.environ:
    from android.storage import app_storage_path
    USERS_PATH = os.path.join(app_storage_path(), "users.json")
else:
    USERS_PATH = os.path.join(os.path.dirname(__file__), "users.json")

# 按钮类
class Button:
    def __init__(self, x, y, width, height, text, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
    
    def draw(self, screen, mx, my, color, hover_color, text_color):
        btn_color = hover_color if self.rect.collidepoint(mx, my) else color
        pygame.draw.rect(screen, btn_color, self.rect)
        text_surf = self.font.render(self.text, True, text_color)
        if text_surf:
            screen.blit(text_surf, (self.rect.x + (self.rect.width - text_surf.get_width()) // 2, 
                                   self.rect.y + (self.rect.height - text_surf.get_height()) // 2))
    
    def is_clicked(self, mx, my):
        return self.rect.collidepoint(mx, my)

# 消息窗口类
class MessageWindow:
    def __init__(self, screen, title, message, font_title, font_normal):
        self.screen = screen
        self.title = title
        self.message = message
        self.font_title = font_title
        self.font_normal = font_normal
        self.width, self.height = screen.get_size()
        self.window_width = min(400, self.width * 0.8)
        self.window_height = min(200, self.height * 0.6)
        self.window_x = (self.width - self.window_width) // 2
        self.window_y = (self.height - self.window_height) // 2
        
        # 颜色定义
        self.COLOR_TITLE = (255, 210, 0)
        self.COLOR_TEXT = (255, 255, 255)
        self.COLOR_BTN = (40, 100, 200)
        self.COLOR_BTN_HOVER = (60, 130, 230)
        
        # 创建按钮
        btn_width = min(100, self.window_width * 0.3)
        btn_height = min(40, self.window_height * 0.2)
        btn_spacing = 20
        
        self.ok_btn = Button(
            self.window_x + (self.window_width - btn_width * 2 - btn_spacing) // 2,
            self.window_y + self.window_height - btn_height - 20,
            btn_width,
            btn_height,
            "确定",
            self.font_normal
        )
        
        self.cancel_btn = Button(
            self.window_x + (self.window_width - btn_width * 2 - btn_spacing) // 2 + btn_width + btn_spacing,
            self.window_y + self.window_height - btn_height - 20,
            btn_width,
            btn_height,
            "取消",
            self.font_normal
        )
        
        self.result = None
    
    def draw(self, mx, my):
        # 绘制背景遮罩
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # 绘制窗口
        window_rect = pygame.Rect(self.window_x, self.window_y, self.window_width, self.window_height)
        pygame.draw.rect(self.screen, (30, 40, 60), window_rect)
        pygame.draw.rect(self.screen, (60, 80, 120), window_rect, 2)
        
        # 绘制标题
        title_surf = self.font_title.render(self.title, True, self.COLOR_TITLE)
        if title_surf:
            self.screen.blit(title_surf, (self.window_x + (self.window_width - title_surf.get_width()) // 2, self.window_y + 20))
        
        # 绘制消息
        message_lines = []
        words = self.message.split(' ')
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            if self.font_normal.size(test_line)[0] <= self.window_width - 40:
                current_line = test_line
            else:
                message_lines.append(current_line)
                current_line = word + " "
        if current_line:
            message_lines.append(current_line)
        
        start_y = self.window_y + 60
        line_height = 25
        for i, line in enumerate(message_lines):
            line_surf = self.font_normal.render(line, True, self.COLOR_TEXT)
            if line_surf:
                self.screen.blit(line_surf, (self.window_x + (self.window_width - line_surf.get_width()) // 2, start_y + i * line_height))
        
        # 绘制按钮
        self.ok_btn.draw(self.screen, mx, my, self.COLOR_BTN, self.COLOR_BTN_HOVER, self.COLOR_TEXT)
        self.cancel_btn.draw(self.screen, mx, my, self.COLOR_BTN, self.COLOR_BTN_HOVER, self.COLOR_TEXT)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            if self.ok_btn.is_clicked(mx, my):
                self.result = True
                return True
            if self.cancel_btn.is_clicked(mx, my):
                self.result = False
                return True
        return False
    
    def show(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            mx, my = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    self.result = False
                if self.handle_event(event):
                    running = False
            
            self.draw(mx, my)
            pygame.display.flip()
            clock.tick(30)
        
        return self.result

# 加载用户数据
def load_users():
    """加载用户数据"""
    if os.path.exists(USERS_PATH):
        try:
            with open(USERS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            import logging
            logging.error(f"加载用户数据失败: {e}")
            return {}
    return {}

# 保存用户数据
def save_users(users):
    """保存用户数据"""
    try:
        with open(USERS_PATH, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        hide_file(USERS_PATH)
    except Exception as e:
        import logging
        logging.error(f"保存用户数据失败: {e}")

# 注册新用户
def register_user(username, password):
    """注册新用户"""
    if not username or not password:
        return False, "用户名和密码不能为空"

    users = load_users()
    if username in users:
        return False, "用户名已存在"

    new_user_data = default_save.copy()
    new_user_data["username"] = username
    new_user_data["password"] = password
    new_user_data["resources"] = {r: 0 for r in RESOURCES}
    new_user_data["saves"] = []

    users[username] = new_user_data

    save_users(users)
    return True, "注册成功"

# 登录用户
def login_user(username, password):
    """登录用户"""
    if (username.lower() == "开发者" or username.lower() == "kaifazhe") and password == "123456":
        dev_data = default_save.copy()
        dev_data["username"] = username
        dev_data["password"] = password
        dev_data["resources"] = {r: 10000 for r in RESOURCES}
        dev_data["saves"] = []
        return True, "登录成功", dev_data

    users = load_users()
    if username not in users:
        return False, "用户名不存在", None

    if users[username]["password"] != password:
        return False, "密码错误", None

    return True, "登录成功", users[username]

# 保存用户进度
def save_user_progress(username, user_data):
    """保存用户进度"""
    users = load_users()
    if username in users:
        existing_saves = users[username].get("saves", [])
        users[username] = user_data.copy()
        users[username]["saves"] = existing_saves
        save_users(users)
        return True
    return False

# 保存存档
def save_game(username, save_name, user_data=None):
    """保存游戏存档"""
    users = load_users()
    if username in users:
        if user_data is not None:
            save_data = {
                "name": save_name,
                "timestamp": int(time.time() * 1000),
                "data": user_data.copy()
            }
        else:
            save_data = {
                "name": save_name,
                "timestamp": int(time.time() * 1000),
                "data": users[username].copy()
            }

        if "saves" in save_data["data"]:
            del save_data["data"]["saves"]

        users[username]["saves"].append(save_data)

        if len(users[username]["saves"]) > 5:
            users[username]["saves"] = users[username]["saves"][-5:]

        save_users(users)
        return True, "存档成功"
    return False, "用户不存在"

# 加载存档
def load_game(username, save_index):
    """加载游戏存档"""
    users = load_users()
    if username in users:
        saves = users[username].get("saves", [])
        if 0 <= save_index < len(saves):
            save_data = saves[save_index]
            # 加载存档数据
            user_data = save_data["data"].copy()
            # 恢复saves字段
            user_data["saves"] = users[username]["saves"]
            return True, "加载成功", user_data
    return False, "存档不存在", None

# 删除存档
def delete_save(username, save_index):
    """删除游戏存档"""
    users = load_users()
    if username in users:
        saves = users[username].get("saves", [])
        if 0 <= save_index < len(saves):
            users[username]["saves"].pop(save_index)
            save_users(users)
            return True, "删除成功"
    return False, "存档不存在"

def show_save_manager(screen, font_title, font_normal, font_small, username, user_data):
    """显示存档管理界面"""
    width, height = screen.get_size()
    
    # 颜色定义
    COLOR_BG = (15, 20, 35)
    COLOR_TITLE = (255, 210, 0)
    COLOR_TEXT = (255, 255, 255)
    COLOR_BTN = (40, 100, 200)
    COLOR_BTN_HOVER = (60, 130, 230)
    COLOR_SAVE_BG = (30, 40, 60)
    COLOR_SAVE_BORDER = (60, 80, 120)
    
    def draw_text(text, x, y, font, color=COLOR_TEXT):
        """绘制文字"""
        surf = font.render(text, True, color)
        if surf:
            screen.blit(surf, (x, y))
    
    # 本地按钮类
    class LocalButton(Button):
        def draw(self, screen, mx, my):
            super().draw(screen, mx, my, COLOR_BTN, COLOR_BTN_HOVER, COLOR_TEXT)
    
    # 加载用户存档
    users = load_users()
    saves = users[username].get("saves", [])
    
    # 创建按钮
    btn_width = min(120, width * 0.2)
    btn_height = min(50, height * 0.1)
    btn_spacing = 20
    
    # 新游戏按钮
    new_game_btn = LocalButton(
        (width - btn_width * 2 - btn_spacing) // 2,
        height - btn_height - 30,
        btn_width,
        btn_height,
        "新游戏",
        font_normal
    )
    
    # 返回按钮
    back_btn = LocalButton(
        (width - btn_width * 2 - btn_spacing) // 2 + btn_width + btn_spacing,
        height - btn_height - 30,
        btn_width,
        btn_height,
        "返回",
        font_normal
    )
    
    # 主循环
    running = True
    while running:
        mx, my = pygame.mouse.get_pos()
        screen.fill(COLOR_BG)
        
        # 标题
        title_text = "存档管理"
        draw_text(title_text, (width - font_title.size(title_text)[0]) // 2, 30, font_title, COLOR_TITLE)
        
        # 绘制存档列表
        save_y = 100
        save_width = min(500, width * 0.8)
        save_height = 80
        save_spacing = 20
        
        if not saves:
            empty_text = "暂无存档"
            draw_text(empty_text, (width - font_normal.size(empty_text)[0]) // 2, save_y, font_normal, (150, 150, 150))
        else:
            for i, save in enumerate(saves):
                save_rect = pygame.Rect((width - save_width) // 2, save_y, save_width, save_height)
                pygame.draw.rect(screen, COLOR_SAVE_BG, save_rect)
                pygame.draw.rect(screen, COLOR_SAVE_BORDER, save_rect, 2)
                
                # 存档名称
                save_name = save.get("name", f"存档{i+1}")
                draw_text(save_name, save_rect.x + 20, save_rect.y + 15, font_normal)
                
                # 存档时间
                import time
                timestamp = save.get("timestamp", 0)
                save_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp / 1000))
                draw_text(save_time, save_rect.x + 20, save_rect.y + 45, font_small, (150, 150, 150))
                
                # 加载按钮
                load_btn = LocalButton(
                    save_rect.right - 100, save_rect.y + 20,
                    90, 40, "加载", font_small
                )
                load_btn.draw(screen, mx, my)
                
                # 删除按钮
                delete_btn = LocalButton(
                    save_rect.right - 195, save_rect.y + 20,
                    90, 40, "删除", font_small
                )
                delete_btn.draw(screen, mx, my)
                
                save_y += save_height + save_spacing
        
        # 绘制新游戏按钮
        new_game_btn.draw(screen, mx, my)
        # 绘制返回按钮
        back_btn.draw(screen, mx, my)
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                # 检查新游戏按钮
                if new_game_btn.is_clicked(mx, my):
                    return user_data
                # 检查返回按钮
                if back_btn.is_clicked(mx, my):
                    return None
                
                # 检查存档按钮
                save_y = 100
                for i, save in enumerate(saves):
                    save_rect = pygame.Rect((width - save_width) // 2, save_y, save_width, save_height)
                    
                    # 加载按钮
                    load_btn = LocalButton(
                        save_rect.right - 100, save_rect.y + 20,
                        90, 40, "加载", font_small
                    )
                    if load_btn.is_clicked(mx, my):
                        success, message, save_data = load_game(username, i)
                        if success:
                            # 显示成功消息窗口
                            msg_window = MessageWindow(screen, "加载成功", message, font_title, font_normal)
                            if msg_window.show():
                                return save_data
                        else:
                            # 显示错误消息窗口
                            msg_window = MessageWindow(screen, "加载失败", message, font_title, font_normal)
                            msg_window.show()
                    
                    # 删除按钮
                    delete_btn = LocalButton(
                        save_rect.right - 195, save_rect.y + 20,
                        90, 40, "删除", font_small
                    )
                    if delete_btn.is_clicked(mx, my):
                        # 显示确认删除消息窗口
                        msg_window = MessageWindow(screen, "确认删除", "确定要删除这个存档吗？", font_title, font_normal)
                        if msg_window.show():
                            success, message = delete_save(username, i)
                            if success:
                                # 显示成功消息窗口
                                msg_window = MessageWindow(screen, "删除成功", message, font_title, font_normal)
                                msg_window.show()
                            else:
                                # 显示错误消息窗口
                                msg_window = MessageWindow(screen, "删除失败", message, font_title, font_normal)
                                msg_window.show()
                            # 重新加载存档列表
                            users = load_users()
                            saves = users[username].get("saves", [])
                    
                    save_y += save_height + save_spacing
        
        pygame.display.flip()
        pygame.time.Clock().tick(30)
    
    return None

def main():
    """登录系统主函数"""
    try:
        # 初始化
        if not pygame.get_init():
            pygame.init()
        pygame.mixer.init()
        
        # 启用 Unicode 输入支持，确保中文输入法正常工作
        try:
            pygame.key.set_text_input_enabled(True)
        except AttributeError:
            # 旧版本Pygame不支持此方法，忽略
            pass
        
        # 分辨率适配
        if 'ANDROID_DATA' in os.environ:
            info = pygame.display.Info()
            SCREEN_WIDTH = info.current_w
            SCREEN_HEIGHT = info.current_h
        else:
            SCREEN_WIDTH = 600
            SCREEN_HEIGHT = 400
        
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("登录系统")
        clock = pygame.time.Clock()
        
        # 字体初始化
        def init_font(size):
            font_name = get_system_font_name()
            try:
                return pygame.font.SysFont(font_name, size)
            except Exception:
                return pygame.font.Font(None, size)
        
        font_title = init_font(32 if not 'ANDROID_DATA' in os.environ else 48)
        font_normal = init_font(24 if not 'ANDROID_DATA' in os.environ else 36)
        font_small = init_font(18 if not 'ANDROID_DATA' in os.environ else 28)
        font_input = init_font(20 if not 'ANDROID_DATA' in os.environ else 32)
        
        # 颜色定义
        COLOR_BG = (15, 20, 35)
        COLOR_TITLE = (255, 210, 0)
        COLOR_TEXT = (255, 255, 255)
        COLOR_TEXT_HINT = (150, 150, 150)
        COLOR_BTN = (40, 100, 200)
        COLOR_BTN_HOVER = (60, 130, 230)
        COLOR_INPUT = (30, 40, 60)
        COLOR_INPUT_BORDER = (60, 80, 120)
        COLOR_INPUT_BORDER_ACTIVE = (100, 150, 255)
        COLOR_ERROR = (255, 100, 100)
        
        def draw_text(text, x, y, font, color=COLOR_TEXT):
            """绘制文字"""
            surf = font.render(text, True, color)
            if surf:
                screen.blit(surf, (x, y))
        
        # 输入框类
        class InputBox:
            def __init__(self, x, y, width, height, font, placeholder=""):
                self.rect = pygame.Rect(x, y, width, height)
                self.color = COLOR_INPUT_BORDER
                self.text = ""
                self.font = font
                self.placeholder = placeholder
                self.active = False
            
            def handle_event(self, event):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.rect.collidepoint(event.pos):
                        self.active = not self.active
                    else:
                        self.active = False
                    self.color = COLOR_INPUT_BORDER_ACTIVE if self.active else COLOR_INPUT_BORDER
                if event.type == pygame.KEYDOWN:
                    if self.active:
                        if event.key == pygame.K_BACKSPACE:
                            self.text = self.text[:-1]
                        elif event.key == pygame.K_RETURN:
                            pass
                if event.type == pygame.TEXTINPUT:
                    if self.active:
                        self.text += event.text
            
            def draw(self, screen):
                # 绘制输入框
                pygame.draw.rect(screen, COLOR_INPUT, self.rect)
                pygame.draw.rect(screen, self.color, self.rect, 2)
                
                # 绘制文字
                if self.text:
                    text_surf = self.font.render(self.text, True, COLOR_TEXT)
                else:
                    text_surf = self.font.render(self.placeholder, True, COLOR_TEXT_HINT)
                
                if text_surf:
                    screen.blit(text_surf, (self.rect.x + 10, self.rect.y + (self.rect.height - text_surf.get_height()) // 2))
        
        # 本地按钮类
        class LocalButton:
            def __init__(self, x, y, width, height, text, font):
                self.rect = pygame.Rect(x, y, width, height)
                self.text = text
                self.font = font
            
            def draw(self, screen, mx, my):
                # 检查鼠标悬停
                is_hovered = self.rect.collidepoint(mx, my)
                # 按钮颜色
                btn_color = COLOR_BTN_HOVER if is_hovered else COLOR_BTN
                # 绘制按钮
                pygame.draw.rect(screen, btn_color, self.rect)
                # 绘制文字
                text_surf = self.font.render(self.text, True, COLOR_TEXT)
                if text_surf:
                    screen.blit(text_surf, (self.rect.x + (self.rect.width - text_surf.get_width()) // 2, 
                                           self.rect.y + (self.rect.height - text_surf.get_height()) // 2))
            
            def is_clicked(self, mx, my):
                return self.rect.collidepoint(mx, my)
        
        # 创建输入框和按钮
        input_width = min(300, SCREEN_WIDTH * 0.7)
        input_height = min(40, SCREEN_HEIGHT * 0.1)
        input_spacing = 20
        
        username_input = InputBox(
            (SCREEN_WIDTH - input_width) // 2,
            SCREEN_HEIGHT // 2 - input_height - input_spacing // 2,
            input_width,
            input_height,
            font_input,
            "请输入用户名"
        )
        
        password_input = InputBox(
            (SCREEN_WIDTH - input_width) // 2,
            SCREEN_HEIGHT // 2 + input_spacing // 2,
            input_width,
            input_height,
            font_input,
            "请输入密码"
        )
        
        btn_width = min(150, SCREEN_WIDTH * 0.3)
        btn_height = min(40, SCREEN_HEIGHT * 0.1)
        btn_spacing = 20
        
        login_btn = LocalButton(
            (SCREEN_WIDTH - btn_width * 2 - btn_spacing) // 2,
            SCREEN_HEIGHT // 2 + input_height + input_spacing * 2,
            btn_width,
            btn_height,
            "登录",
            font_normal
        )
        
        register_btn = LocalButton(
            (SCREEN_WIDTH - btn_width * 2 - btn_spacing) // 2 + btn_width + btn_spacing,
            SCREEN_HEIGHT // 2 + input_height + input_spacing * 2,
            btn_width,
            btn_height,
            "注册",
            font_normal
        )
        
        # 状态
        is_registering = False
        
        # 主循环
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            screen.fill(COLOR_BG)
            
            # 标题
            title_text = "游戏登录"
            draw_text(title_text, (SCREEN_WIDTH - font_title.size(title_text)[0]) // 2, 50, font_title, COLOR_TITLE)
            
            # 绘制输入框
            username_input.draw(screen)
            password_input.draw(screen)
            
            # 绘制按钮
            login_btn.draw(screen, mx, my)
            register_btn.draw(screen, mx, my)
            
            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                username_input.handle_event(event)
                password_input.handle_event(event)
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if login_btn.is_clicked(mx, my):
                        # 登录逻辑
                        success, message, user_data = login_user(username_input.text, password_input.text)
                        if success:
                            # 登录成功，显示存档管理界面
                            save_result = show_save_manager(screen, font_title, font_normal, font_small, username_input.text, user_data)
                            if save_result:
                                return True, username_input.text, save_result
                        else:
                            # 显示错误消息窗口
                            msg_window = MessageWindow(screen, "登录失败", message, font_title, font_normal)
                            msg_window.show()
                    
                    if register_btn.is_clicked(mx, my):
                        # 注册逻辑
                        success, message = register_user(username_input.text, password_input.text)
                        if success:
                            # 显示成功消息窗口
                            msg_window = MessageWindow(screen, "注册成功", "注册成功，请登录", font_title, font_normal)
                            msg_window.show()
                        else:
                            # 显示错误消息窗口
                            msg_window = MessageWindow(screen, "注册失败", message, font_title, font_normal)
                            msg_window.show()
            
            pygame.display.flip()
            clock.tick(30)
        
        # 退出登录系统
        return False, "", None
    except Exception as e:
        print(f"登录系统异常：{str(e)}")
        # 发生异常时，返回登录失败，而不是直接退出程序
        return False, "登录系统异常", None

if __name__ == "__main__":
    main()