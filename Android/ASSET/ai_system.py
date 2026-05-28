#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pygame
import os
import json
from ASSET.game_data import data, save, get_system_font_name
from ASSET.game_main_menu import Button, draw_gradient_background, COLORS

# 尝试导入requests模块
try:
    import requests
    requests_available = True
except ImportError:
    requests_available = False

# 字体变量
FONT_MAIN = None
FONT_SMALL = None
FONT_BIG = None

def draw_title(surface, text, y_pos, screen_width):
    """绘制带特效的标题"""
    global FONT_BIG
    # 发光效果
    for offset in range(5, 0, -1):
        alpha = 50 - offset * 8
        glow_surf = FONT_BIG.render(text, True, (*COLORS["accent_gold"][:3], alpha))
        glow_rect = glow_surf.get_rect(center=(screen_width // 2, y_pos))
        surface.blit(glow_surf, (glow_rect.x - offset, glow_rect.y))
        surface.blit(glow_surf, (glow_rect.x + offset, glow_rect.y))
    
    # 主标题
    title = FONT_BIG.render(text, True, COLORS["accent_gold"])
    title_rect = title.get_rect(center=(screen_width // 2, y_pos))
    
    # 阴影
    shadow = FONT_BIG.render(text, True, (0, 0, 0))
    surface.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
    surface.blit(title, title_rect)
    
    # 装饰线
    line_y = y_pos + 40
    pygame.draw.line(surface, COLORS["accent_gold"], 
                    (screen_width // 2 - 150, line_y),
                    (screen_width // 2 - 50, line_y), 3)
    pygame.draw.line(surface, COLORS["accent_gold"],
                    (screen_width // 2 + 50, line_y),
                    (screen_width // 2 + 150, line_y), 3)
    # 中间装饰
    pygame.draw.circle(surface, COLORS["accent_gold"], (screen_width // 2, line_y), 8)
    pygame.draw.circle(surface, COLORS["bg_dark"], (screen_width // 2, line_y), 5)

def draw_resource_panel(surface, x, y, width, height):
    """绘制资源面板"""
    global FONT_SMALL
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
    
    spacing = width // len(resources)
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

def show_message(screen, message, font):
    """显示消息（自动换行和滚动）"""
    # 自动换行处理
    max_width = screen.get_width() - 100  # 屏幕宽度减去边距
    lines = []
    
    # 按换行符分割
    message_lines = message.split('\n')
    
    for line in message_lines:
        if len(line) == 0:
            lines.append("")
            continue
            
        # 处理长行
        if font.render(line, True, COLORS["text_white"]).get_width() > max_width:
            words = line.split(' ')
            current_line = ""
            for word in words:
                test_line = current_line + word + " "
                test_surf = font.render(test_line, True, COLORS["text_white"])
                if test_surf.get_width() > max_width:
                    if current_line:
                        lines.append(current_line)
                    current_line = word + " "
                else:
                    current_line = test_line
            if current_line:
                lines.append(current_line)
        else:
            lines.append(line)
    
    # 计算总高度
    line_height = font.get_height() + 5
    total_height = len(lines) * line_height
    
    # 计算背景框尺寸
    max_line_width = 0
    for line in lines:
        line_surf = font.render(line, True, COLORS["text_white"])
        max_line_width = max(max_line_width, line_surf.get_width())
    
    bg_width = min(max_line_width + 40, screen.get_width() - 50)
    bg_height = min(total_height + 30, screen.get_height() - 50)
    
    # 居中显示
    bg_x = (screen.get_width() - bg_width) // 2
    bg_y = (screen.get_height() - bg_height) // 2
    
    # 消息背景
    bg_rect = pygame.Rect(bg_x, bg_y, bg_width, bg_height)
    pygame.draw.rect(screen, (30, 30, 55, 200), bg_rect, border_radius=10)
    pygame.draw.rect(screen, COLORS["accent_gold"], bg_rect, 2, border_radius=10)
    
    # 绘制文字（支持滚动）
    y_offset = bg_y + 15
    visible_lines = []
    current_y = y_offset
    
    for line in lines:
        line_surf = font.render(line, True, COLORS["text_white"])
        if current_y + line_surf.get_height() <= bg_y + bg_height - 15:
            line_x = bg_x + (bg_width - line_surf.get_width()) // 2
            screen.blit(line_surf, (line_x, current_y))
            current_y += line_height
        else:
            visible_lines.append(line)
    
    # 如果有更多内容，显示滚动提示
    if visible_lines:
        scroll_text = "... 按任意键查看更多 ..."
        scroll_surf = font.render(scroll_text, True, COLORS["accent_gold"])
        scroll_x = bg_x + (bg_width - scroll_surf.get_width()) // 2
        screen.blit(scroll_surf, (scroll_x, bg_y + bg_height - 30))
        
        # 等待用户输入
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
        
        # 显示剩余内容
        current_y = y_offset
        for line in lines:
            line_surf = font.render(line, True, COLORS["text_white"])
            line_x = bg_x + (bg_width - line_surf.get_width()) // 2
            screen.blit(line_surf, (line_x, current_y))
            current_y += line_height
    
    pygame.display.flip()
    pygame.time.wait(2000)

def input_text(screen, font, prompt):
    """输入文本"""
    input_text = ""
    active = True
    clock = pygame.time.Clock()
    
    while active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    active = False
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode
        
        # 绘制
        draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
        draw_title(screen, "游戏内AI", screen.get_height() * 0.1, screen.get_width())
        
        # 提示文字（自动换行）
        prompt_lines = []
        words = prompt.split(' ')
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            test_surf = font.render(test_line, True, COLORS["text_white"])
            if test_surf.get_width() > screen.get_width() - 100:  # 屏幕宽度减去边距
                prompt_lines.append(current_line)
                current_line = word + " "
            else:
                current_line = test_line
        
        if current_line:
            prompt_lines.append(current_line)
        
        # 绘制提示文字
        y_offset = screen.get_height() * 0.3
        for line in prompt_lines:
            line_surf = font.render(line, True, COLORS["text_white"])
            screen.blit(line_surf, (screen.get_width() // 2 - line_surf.get_width() // 2, y_offset))
            y_offset += line_surf.get_height() + 5
        
        # 输入框
        input_rect = pygame.Rect(screen.get_width() // 2 - 200, y_offset + 20, 400, 40)
        pygame.draw.rect(screen, (40, 40, 70), input_rect, border_radius=10)
        pygame.draw.rect(screen, COLORS["accent_gold"], input_rect, 2, border_radius=10)
        
        # 输入文字
        input_surf = font.render(input_text, True, COLORS["text_white"])
        screen.blit(input_surf, (input_rect.x + 10, input_rect.y + 5))
        
        # 确认按钮
        confirm_btn = Button(
            "确认",
            screen.get_width() // 2 - 75,
            input_rect.y + 60,
            150,
            40,
            font,
            normal_color=COLORS["accent_green"]
        )
        confirm_btn.check_hover(pygame.mouse.get_pos())
        confirm_btn.draw(screen)
        
        # 鼠标点击
        if pygame.mouse.get_pressed()[0]:
            if confirm_btn.check_click(pygame.mouse.get_pos()):
                active = False
        
        pygame.display.flip()
        clock.tick(60)
    
    return input_text

def call_ollama(prompt, model, url):
    """调用OLLAMA模型"""
    if not requests_available:
        return "错误: 缺少requests模块，请安装requests库"
    # 三国主题预设 - 即使是本地模型也能使用
    system_prompt = """
你是一个专注于三国历史的AI助手，精通三国时期的人物、事件、地理和文化。你的回答应该基于《三国演义》和正史《三国志》的内容，对玩家的问题提供准确、详细的解答。当玩家询问三国相关问题时，你要以专业的历史知识回答，同时保持友好易懂的语气。

你需要了解的核心内容包括：
- 三国主要人物：刘备、关羽、张飞、诸葛亮、曹操、孙权、周瑜、司马懿等
- 重要事件：桃园结义、三顾茅庐、赤壁之战、空城计、六出祁山等
- 地理知识：荆州、益州、徐州、赤壁、华容道等
- 兵器与战术：青龙偃月刀、丈八蛇矛、木牛流马、八阵图等
- 文化典故：草船借箭、舌战群儒、煮酒论英雄等

请以三国专家的身份回答问题，避免回答与三国无关的内容。
    """
    
    # 构建完整提示
    full_prompt = f"{system_prompt}\n\n玩家问题: {prompt}"
    
    # 确保URL格式正确
    if not url:
        url = "http://localhost:11434"
    
    # 移除末尾的斜杠，避免重复
    url = url.rstrip('/')
    
    # 构建完整的API URL
    api_url = f"{url}/api/generate"
    
    try:
        # 先测试连接
        test_url = f"{url}/api/tags"
        test_response = requests.get(test_url, timeout=5)
        test_response.raise_for_status()
        models = test_response.json().get("models", [])
        model_names = [m.get("name") for m in models]
        
        # 检查模型是否存在
        if model not in model_names:
            return f"错误: 模型'{model}'未找到\n已下载的模型: {', '.join(model_names)}\n请运行: ollama pull {model}"
        
        # 发送生成请求
        response = requests.post(
            api_url,
            json={
                "model": model,
                "prompt": full_prompt,
                "stream": False
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            if "tags" in str(e.request.url):
                return f"错误: 404 - OLLAMA API未找到，请检查URL是否正确\n地址: {url}"
            else:
                return f"错误: 404 - 模型'{model}'未找到，请确保模型已下载\n请运行: ollama pull {model}"
        return f"错误: HTTP错误 {e.response.status_code}\n详情: {e.response.text}"
    except requests.exceptions.ConnectionError:
        return f"错误: 连接失败，请确保OLLAMA服务已启动\n地址: {url}\n请检查: 1. OLLAMA服务是否运行 2. 防火墙是否允许访问 3. 端口是否正确"
    except Exception as e:
        return f"错误: {str(e)}\n请检查: 1. OLLAMA服务是否运行 2. 模型是否已下载 3. URL是否正确"

def main():
    """游戏内AI主函数"""
    global screen, clock, FONT_MAIN, FONT_SMALL, FONT_BIG
    
    # 初始化pygame
    if not pygame.get_init():
        pygame.init()
    
    # 获取屏幕大小
    if 'ANDROID_DATA' in os.environ:
        # Android设备使用全屏
        info = pygame.display.Info()
        screen_width = info.current_w
        screen_height = info.current_h
        screen = pygame.display.set_mode((screen_width, screen_height))
    else:
        # PC设备
        screen_width = 800
        screen_height = 600
        screen = pygame.display.set_mode((screen_width, screen_height))
    
    pygame.display.set_caption("游戏内AI")
    clock = pygame.time.Clock()
    
    # 初始化字体
    font_name = get_system_font_name()
    try:
        if font_name:
            FONT_MAIN = pygame.font.SysFont(font_name, 40)
            FONT_SMALL = pygame.font.SysFont(font_name, 28)
            FONT_BIG = pygame.font.SysFont(font_name, 60)
        else:
            FONT_MAIN = pygame.font.Font(None, 40)
            FONT_SMALL = pygame.font.Font(None, 28)
            FONT_BIG = pygame.font.Font(None, 60)
    except Exception:
        FONT_MAIN = pygame.font.Font(None, 40)
        FONT_SMALL = pygame.font.Font(None, 28)
        FONT_BIG = pygame.font.Font(None, 60)
    
    # 确保AI数据存在
    if "ai" not in data:
        data["ai"] = {
            "enabled": False,
            "model": "",
            "url": "http://localhost:11434"
        }
    
    # 主循环
    running = True
    messages = []
    user_input = ""
    
    while running:
        # 渐变背景
        draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
        
        # 标题
        draw_title(screen, "游戏内AI", screen_height * 0.1, screen_width)
        
        # 资源面板
        panel_width = min(500, screen_width * 0.7)
        draw_resource_panel(screen, (screen_width - panel_width) // 2, 
                          screen_height * 0.18, panel_width, 50)
        
        # AI状态
        ai_enabled = data["ai"]["enabled"]
        status_text = f"AI状态: {'已开启' if ai_enabled else '已关闭'}"
        status_surf = FONT_MAIN.render(status_text, True, COLORS["accent_gold"] if ai_enabled else COLORS["accent_red"])
        screen.blit(status_surf, (screen_width // 2 - status_surf.get_width() // 2, screen_height * 0.28))
        
        # 配置按钮
        config_btn = Button(
            "配置AI",
            screen_width - 200,
            20,
            180,
            50,
            FONT_SMALL,
            normal_color=COLORS["accent_blue"]
        )
        config_btn.check_hover(pygame.mouse.get_pos())
        config_btn.draw(screen)
        
        # 消息区域
        message_area = pygame.Rect(50, screen_height * 0.35, screen_width - 100, screen_height * 0.4)
        pygame.draw.rect(screen, (30, 30, 55, 200), message_area, border_radius=10)
        pygame.draw.rect(screen, COLORS["accent_gold"], message_area, 2, border_radius=10)
        
        # 显示消息
        y_offset = message_area.y + 10
        for msg in messages[-10:]:  # 只显示最近10条消息
            msg_surf = FONT_SMALL.render(msg, True, COLORS["text_white"])
            screen.blit(msg_surf, (message_area.x + 10, y_offset))
            y_offset += msg_surf.get_height() + 5
        
        # 输入区域
        input_rect = pygame.Rect(50, screen_height - 80, screen_width - 200, 40)
        pygame.draw.rect(screen, (40, 40, 70), input_rect, border_radius=10)
        pygame.draw.rect(screen, COLORS["accent_gold"], input_rect, 2, border_radius=10)
        
        # 输入文字
        input_surf = FONT_SMALL.render(user_input, True, COLORS["text_white"])
        screen.blit(input_surf, (input_rect.x + 10, input_rect.y + 5))
        
        # 发送按钮
        send_btn = Button(
            "发送",
            screen_width - 130,
            screen_height - 80,
            80,
            40,
            FONT_SMALL,
            normal_color=COLORS["accent_green"]
        )
        send_btn.check_hover(pygame.mouse.get_pos())
        send_btn.draw(screen)
        
        # 返回按钮
        back_btn = Button(
            "返回主菜单",
            20,
            screen_height - 60,
            180,
            50,
            FONT_SMALL,
            normal_color=COLORS["accent_blue_dark"]
        )
        back_btn.check_hover(pygame.mouse.get_pos())
        back_btn.draw(screen)
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save()
                pygame.quit()
                return
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if user_input and ai_enabled:
                        # 添加用户消息
                        messages.append(f"你: {user_input}")
                        
                        # 调用OLLAMA
                        response = call_ollama(user_input, data["ai"]["model"], data["ai"]["url"])
                        messages.append(f"AI: {response}")
                        
                        user_input = ""
                    elif user_input and not ai_enabled:
                        messages.append("提示: 请先开启AI并配置模型")
                        user_input = ""
                elif event.key == pygame.K_BACKSPACE:
                    user_input = user_input[:-1]
                else:
                    user_input += event.unicode
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                
                # 配置按钮
                if config_btn.check_click(mouse_pos):
                    if not requests_available:
                        show_message(screen, "错误: 缺少requests模块，请安装requests库", FONT_MAIN)
                    else:
                        # 切换AI状态
                        data["ai"]["enabled"] = not data["ai"]["enabled"]
                        
                        if data["ai"]["enabled"]:
                            # 提示需要安装OLLAMA
                            show_message(screen, "请确保本地已安装OLLAMA并运行", FONT_MAIN)
                            
                            # 模型大小提醒
                            show_message(screen, "模型大小提醒:\n\n- gemma:2b: 约1GB\n- llama3:8b: 约4GB\n- 其他模型: 可能更大\n\n请确保有足够的磁盘空间\n\n提示：游戏目录下有 '下载OLLAMA模型.bat' 文件，\n可双击运行来自动下载 gemma:2b 模型。", FONT_MAIN)
                            
                            # 详细免责条款 - 滚动容器
                            def show_disclaimer(screen):
                                """显示详细免责条款"""
                                running = True
                                scroll_y = 0
                                max_scroll = 0
                                
                                # 条款内容
                                terms = """三国小游戏用户服务条款及免责声明

欢迎您使用本三国小游戏（以下简称"本游戏"），本游戏由我方（以下简称"运营方"）独立开发、运营及维护。为规范用户使用行为，明确运营方与用户之间的权利义务，保障双方合法权益，依据《中华人民共和国民法典》《网络安全法》《网络游戏管理暂行规定》等相关法律法规，特制定本用户服务条款及免责声明（以下简称"本条款"）。请您在下载、安装、注册、登录及使用本游戏前，仔细阅读并充分理解本条款全部内容，尤其是免除或限制运营方责任的条款、限制用户权利的条款，您点击"同意"、完成注册或使用本游戏服务，即视为您已阅读、理解并自愿接受本条款的全部约束；若您不同意本条款任何内容，请立即停止下载、安装及使用本游戏。

一、用户基本权利与义务

1.  用户有权在遵守本条款及游戏内相关规则的前提下，正常使用本游戏提供的各项服务，包括但不限于账号注册、角色创建、游戏战斗、道具获取、社交互动等核心功能，运营方将尽力保障用户使用体验的稳定性。

2.  用户应提供真实、合法、准确、有效的个人身份信息及注册资料，不得使用虚假信息、他人信息注册账号，不得冒用、盗用他人账号使用本游戏服务。若用户提供的信息存在虚假、无效或违法情形，运营方有权暂停或终止其账号使用权，由此产生的一切后果由用户自行承担。

3.  用户应妥善保管自己的游戏账号、密码及相关登录凭证，对账号下的所有操作行为（包括但不限于充值、道具交易、角色操作等）承担全部责任。若因用户自身保管不善、泄露账号信息，或因第三方盗取、冒用账号导致的账号损失、道具丢失、权益受损等，运营方不承担任何责任。

4.  用户在使用本游戏过程中，应严格遵守国家法律法规及本条款约定，不得从事任何违法违规、违背公序良俗或损害运营方、其他用户合法权益的行为，包括但不限于：使用外挂、作弊程序、破解工具等破坏游戏公平性；传播不良信息、违法内容、虚假信息；攻击游戏服务器、篡改游戏数据；盗用、交易、转让游戏账号及虚拟道具；骚扰、辱骂、诋毁其他用户等。

5.  用户应自行配备使用本游戏所需的设备（电脑、手机等）及网络环境，承担相关硬件、网络费用，并对自身设备的安全性负责，运营方不承担因用户设备故障、网络异常导致的游戏无法正常使用、数据丢失等责任。

二、游戏服务相关约定

1.  运营方有权根据游戏运营需求、技术升级、法律法规要求等，对本游戏的内容、功能、规则、界面等进行调整、更新或优化，包括但不限于武将技能调整、道具属性变更、地图优化、系统升级等，相关调整将通过游戏内公告、官方通知等方式告知用户，用户继续使用本游戏即视为接受该等调整。

2.  本游戏内的所有虚拟道具（包括但不限于武将、装备、金币、粮草、道具等）均为游戏服务的一部分，所有权归运营方所有，用户仅享有在游戏内的使用权，不得将虚拟道具用于游戏外的交易、转让、变现等行为，否则运营方有权收回相关虚拟道具、暂停或终止账号使用权，由此产生的损失由用户自行承担。

3.  运营方将尽力保障游戏服务器的正常运行，但因不可抗力（包括但不限于地震、洪水、台风等自然灾害，战争、政策调整等社会事件）、技术故障、网络攻击、服务器维护、第三方服务异常等非运营方主观原因导致的游戏中断、卡顿、数据异常、无法登录等情况，运营方不承担违约责任，将尽力及时修复并通知用户。

4.  本游戏为休闲娱乐类小游戏，运营方不保证游戏内容的绝对准确性、完整性，游戏内的三国历史元素、武将设定等均为娱乐化改编，不代表真实历史，仅用于提升游戏趣味性，用户不得将游戏内容作为历史参考依据。

三、免责条款

1.  因不可抗力、第三方因素（包括但不限于网络服务提供商故障、黑客攻击、病毒感染等）导致本游戏无法正常提供服务，或用户账号、数据、虚拟道具出现异常、丢失等，运营方不承担任何赔偿责任，仅在能力范围内尽力协助用户恢复。

2.  因用户自身操作失误、设备故障、网络异常、账号保管不善、使用第三方软件或服务等原因导致的任何损失（包括但不限于账号被盗、道具丢失、数据丢失、无法登录等），均由用户自行承担，运营方不承担任何责任。

3.  用户因违反本条款约定、国家法律法规，或从事违法违规、破坏游戏公平性的行为，导致账号被暂停、终止使用，或虚拟道具被收回、数据被清除等，相关损失由用户自行承担，运营方不承担任何赔偿责任，同时有权追究用户的相关法律责任。

4.  本游戏内的广告、第三方链接等内容，均由第三方提供，运营方仅提供展示服务，不对其真实性、合法性、安全性承担任何责任，用户点击相关广告或链接产生的任何损失（包括但不限于财产损失、信息泄露等），由用户自行承担，与运营方无关。

5.  运营方不对本游戏的使用效果、稳定性、兼容性做任何明示或默示的担保，不保证游戏无任何漏洞、无故障，也不保证用户使用本游戏不会产生任何损失。用户使用本游戏所产生的一切风险，均由用户自行承担。

6.  因游戏版本更新、技术升级等原因，可能导致部分旧版本游戏无法正常使用，运营方将通过公告等方式告知用户更新版本，用户未及时更新导致的游戏无法使用、数据异常等损失，由用户自行承担。

7.  用户在使用本游戏过程中，因自身身体状况（包括但不限于视力下降、颈椎不适等）产生的任何健康问题，均与运营方无关，由用户自行承担相关责任。

8.  任何因用户个人信息泄露导致的损失，若该泄露并非因运营方故意或重大过失造成（包括但不限于用户自行泄露、第三方非法获取等），运营方不承担任何责任。

9.  本游戏仅为娱乐用途，用户因使用本游戏产生的任何间接损失、偶然损失、特殊损失（包括但不限于预期收益、精神损失等），运营方不承担任何赔偿责任。

四、其他条款

1.  本条款的成立、生效、履行、解释及纠纷解决，均适用中华人民共和国法律。若用户与运营方之间因本条款或使用本游戏产生任何纠纷，双方应首先友好协商解决；协商不成的，任何一方均有权向运营方所在地有管辖权的人民法院提起诉讼。

2.  运营方有权根据国家法律法规变化、游戏运营需求等，对本条款进行修改、补充，修改后的条款将通过游戏内公告、官方通知等方式发布，自发布之日起生效，用户继续使用本游戏即视为接受修改后的条款；若用户不同意修改后的条款，应立即停止使用本游戏。

3.  本条款未尽事宜，按照国家相关法律法规及行业惯例执行；若本条款中的任何条款被认定为无效或不可执行，不影响其他条款的效力。

4.  您在使用本游戏过程中，若有任何疑问、建议或投诉，可通过游戏内反馈渠道、官方联系方式与运营方联系，运营方将在合理期限内予以回复和处理。

5.  本条款自您点击"同意"、完成注册或使用本游戏服务之日起生效，有效期至您停止使用本游戏服务之日止。

温馨提示：请您合理安排游戏时间，适度游戏，避免沉迷网络，保护自身身心健康及财产安全。

运营方：XXX

生效日期：XXX"""
                                
                                # 计算最大滚动距离（考虑自动换行）
                                lines = terms.split('\n')
                                line_height = FONT_SMALL.get_height() + 2
                                total_lines = 0
                                
                                # 计算实际行数（包括自动换行）
                                for line in lines:
                                    if len(line) > 80:
                                        # 估算换行后的行数
                                        words = line.split(' ')
                                        current_length = 0
                                        for word in words:
                                            test_surf = FONT_SMALL.render(word + " ", True, COLORS["text_white"])
                                            current_length += test_surf.get_width()
                                            if current_length > (screen.get_width() - 140):  # 容器宽度减去边距
                                                total_lines += 1
                                                current_length = test_surf.get_width()
                                        if current_length > 0:
                                            total_lines += 1
                                    else:
                                        total_lines += 1
                                
                                max_scroll = max(0, total_lines * line_height - 400)
                                
                                while running:
                                    for event in pygame.event.get():
                                        if event.type == pygame.QUIT:
                                            return False
                                        if event.type == pygame.KEYDOWN:
                                            if event.key == pygame.K_DOWN:
                                                scroll_y = min(scroll_y + 30, max_scroll)
                                            elif event.key == pygame.K_UP:
                                                scroll_y = max(scroll_y - 30, 0)
                                            elif event.key == pygame.K_RETURN:
                                                return True
                                            elif event.key == pygame.K_ESCAPE:
                                                return False
                                        if event.type == pygame.MOUSEBUTTONDOWN:
                                            if event.button == 4:  # 鼠标滚轮向上
                                                scroll_y = max(scroll_y - 30, 0)
                                            elif event.button == 5:  # 鼠标滚轮向下
                                                scroll_y = min(scroll_y + 30, max_scroll)
                                    
                                    # 绘制背景
                                    draw_gradient_background(screen, COLORS["bg_dark"], COLORS["bg_light"])
                                    
                                    # 标题
                                    draw_title(screen, "用户服务条款及免责声明", screen.get_height() * 0.1, screen.get_width())
                                    
                                    # 滚动容器
                                    container_rect = pygame.Rect(50, screen.get_height() * 0.2, screen.get_width() - 100, 400)
                                    pygame.draw.rect(screen, (30, 30, 55, 200), container_rect, border_radius=10)
                                    pygame.draw.rect(screen, COLORS["accent_gold"], container_rect, 2, border_radius=10)
                                    
                                    # 绘制条款内容
                                    y_offset = container_rect.y + 10 - scroll_y
                                    for line in lines:
                                        if y_offset > container_rect.y + container_rect.height:
                                            break
                                        
                                        # 处理长行自动换行
                                        if len(line) > 80:  # 限制每行长度
                                            words = line.split(' ')
                                            current_line = ""
                                            for word in words:
                                                test_line = current_line + word + " "
                                                test_surf = FONT_SMALL.render(test_line, True, COLORS["text_white"])
                                                if test_surf.get_width() > container_rect.width - 40:
                                                    # 绘制当前行
                                                    if current_line:
                                                        line_surf = FONT_SMALL.render(current_line, True, COLORS["text_white"])
                                                        if y_offset + line_surf.get_height() > container_rect.y:
                                                            screen.blit(line_surf, (container_rect.x + 20, y_offset))
                                                        y_offset += line_height
                                                    current_line = word + " "
                                                else:
                                                    current_line = test_line
                                            # 绘制最后一行
                                            if current_line:
                                                line_surf = FONT_SMALL.render(current_line, True, COLORS["text_white"])
                                                if y_offset + line_surf.get_height() > container_rect.y:
                                                    screen.blit(line_surf, (container_rect.x + 20, y_offset))
                                                y_offset += line_height
                                        else:
                                            # 普通行直接绘制
                                            line_surf = FONT_SMALL.render(line, True, COLORS["text_white"])
                                            if y_offset + line_surf.get_height() > container_rect.y:
                                                screen.blit(line_surf, (container_rect.x + 20, y_offset))
                                            y_offset += line_height
                                    
                                    # 提示信息
                                    prompt_surf = FONT_MAIN.render("按上下箭头或鼠标滚轮滚动查看，按Enter同意，按Esc拒绝", True, COLORS["accent_gold"])
                                    screen.blit(prompt_surf, (screen.get_width() // 2 - prompt_surf.get_width() // 2, screen.get_height() - 60))
                                    
                                    pygame.display.flip()
                                    clock.tick(60)
                            
                            # 显示免责条款
                            accepted = show_disclaimer(screen)
                            if not accepted:
                                data["ai"]["enabled"] = False
                                show_message(screen, "未接受条款，AI功能已关闭", FONT_MAIN)
                                continue
                            
                            # 教程选项
                            tutorial = input_text(screen, FONT_MAIN, "是否查看使用教程？\n\n1. 查看教程\n2. 直接配置\n\n请输入数字选择:")
                            if tutorial == "1":
                                show_message(screen, "AI系统使用教程:\n\n1. 安装OLLAMA (https://ollama.com/)\n2. 启动OLLAMA服务\n3. 在游戏中开启AI功能\n4. 选择自动配置或手动配置\n5. 输入问题与AI对话\n\n教程结束", FONT_MAIN)
                            
                            # 选择配置方式
                            config_option = input_text(screen, FONT_MAIN, "选择配置方式:\n\n1. 自动配置 (推荐)\n2. 手动配置\n\n请输入数字选择:")
                            
                            if config_option == "1":
                                # 自动配置
                                show_message(screen, "正在自动配置AI...", FONT_MAIN)
                                # 默认使用轻量模型
                                data["ai"]["model"] = "gemma:2b"
                                data["ai"]["url"] = "http://localhost:11434"
                                show_message(screen, "自动配置完成！\n使用模型: gemma:2b\n地址: http://localhost:11434", FONT_MAIN)
                            else:
                                # 手动配置
                                # 输入模型名称
                                model = input_text(screen, FONT_MAIN, "请输入模型完整名称\n\n例如: gemma:2b\n\n请输入:")
                                if model:
                                    data["ai"]["model"] = model
                                
                                # 输入OLLAMA地址
                                url = input_text(screen, FONT_MAIN, "请输入OLLAMA地址\n\n默认: http://localhost:11434\n\n请输入:")
                                if url:
                                    data["ai"]["url"] = url
                                
                                # 地址选择 - 允许用户指定模型存储位置
                                storage_option = input_text(screen, FONT_MAIN, "模型存储选项:\n\n1. 使用默认位置\n2. 自定义存储位置\n3. 使用已下载的模型\n\n请输入数字选择:")
                                if storage_option == "2":
                                    storage_path = input_text(screen, FONT_MAIN, "请输入模型存储路径:\n\n例如: D:\\OLLAMA\\models\n\n请输入:")
                                    if storage_path:
                                        # 这里仅记录路径，实际配置需要用户在OLLAMA中设置
                                        show_message(screen, f"存储路径已记录: {storage_path}\n\n请在OLLAMA中设置此路径", FONT_MAIN)
                                elif storage_option == "3":
                                    existing_model = input_text(screen, FONT_MAIN, "请输入已下载的模型名称:\n\n例如: gemma:2b\n\n请输入:")
                                    if existing_model:
                                        data["ai"]["model"] = existing_model
                                        show_message(screen, f"已设置使用现有模型: {existing_model}", FONT_MAIN)
                            
                            # 保存配置
                            save()
                            show_message(screen, "配置已保存！", FONT_MAIN)
                
                # 发送按钮
                if send_btn.check_click(mouse_pos):
                    if user_input and ai_enabled:
                        # 添加用户消息
                        messages.append(f"你: {user_input}")
                        
                        # 调用OLLAMA
                        response = call_ollama(user_input, data["ai"]["model"], data["ai"]["url"])
                        messages.append(f"AI: {response}")
                        
                        user_input = ""
                    elif user_input and not ai_enabled:
                        messages.append("提示: 请先开启AI并配置模型")
                        user_input = ""
                
                # 返回按钮
                if back_btn.check_click(mouse_pos):
                    save()
                    return
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
