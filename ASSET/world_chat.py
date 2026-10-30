#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
世界聊天客户端
精美PyGame界面，支持全球聊天
"""

import os
import sys
import subprocess
import tempfile
import pygame
import random
import time
import socket
import json
import threading
from typing import List, Dict
from ASSET.game_data import data, logger, get_font, open_window

# 颜色主题
COLORS = {
    "bg_dark": (12, 18, 30),
    "bg_panel": (25, 35, 55),
    "bg_input": (35, 45, 70),
    "accent_gold": (255, 191, 0),
    "accent_red": (230, 70, 70),
    "accent_green": (70, 200, 70),
    "accent_blue": (80, 150, 220),
    "text_white": (240, 240, 240),
    "text_gray": (150, 160, 180),
    "system": (150, 200, 255),
    "player_other": (120, 200, 150),
    "player_self": (255, 210, 100),
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
        alpha = max(0, min(255, int(255 * (self.life / self.max_life))))
        temp_surface = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(temp_surface, (*self.color, alpha), (int(self.size), int(self.size)), int(self.size))
        surface.blit(temp_surface, (int(self.x - self.size), int(self.y - self.size)))

class ChatMessage:
    def __init__(self, text: str, sender: str = "系统", msg_type: str = "system", timestamp: float = 0):
        self.text = text
        self.sender = sender
        self.type = msg_type
        self.timestamp = timestamp if timestamp else time.time()
        self.y_offset = 0
        self.opacity = 255
    
    def get_color(self):
        if self.type == "system":
            return COLORS["system"]
        elif self.type == "self":
            return COLORS["player_self"]
        else:
            return COLORS["player_other"]

class InputBox:
    def __init__(self, x, y, width, height, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = COLORS["accent_blue"]
        self.text = ""
        self.font = font
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = COLORS["accent_gold"] if self.active else COLORS["accent_blue"]
            if self.active:
                try:
                    from ASSET.ime_helper import apply_text_input
                    apply_text_input()
                except Exception:
                    pass
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return self.text
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if len(self.text) < 100 and event.unicode:
                    self.text += event.unicode
        return None
    
    def update(self):
        self.cursor_timer += 1
        if self.cursor_timer > 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
    
    def draw(self, surface):
        pygame.draw.rect(surface, COLORS["bg_input"], self.rect, border_radius=12)
        pygame.draw.rect(surface, self.color, self.rect, 2, border_radius=12)
        
        if self.active:
            try:
                from ASSET.ime_helper import focus_rect
                focus_rect(self.rect)
            except Exception:
                pass
        
        display_text = self.text
        if self.active and self.cursor_visible:
            display_text += "|"
        
        text_surface = self.font.render(display_text, True, COLORS["text_white"])
        surface.blit(text_surface, (self.rect.x + 15, self.rect.y + 12))

class Button:
    def __init__(self, text, x, y, width, height, font, color=COLORS["accent_blue"]):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.font = font
        self.hovered = False
        self.clicked = False
    
    def draw(self, surface, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        color = tuple(min(c + 30, 255) for c in self.color) if self.hovered else self.color
        
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, COLORS["text_white"], self.rect, 2, border_radius=10)
        
        text_surface = self.font.render(self.text, True, COLORS["text_white"])
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
    
    def check_click(self, event, mouse_pos):
        # 用事件自带坐标判定（比依赖上一帧 hover 标记更可靠，
        # 鼠标快速移动/无窗口焦点时也不会漏判）；合成事件可能缺 button，
        # 缺省按左键处理
        if (event.type == pygame.MOUSEBUTTONDOWN
                and getattr(event, 'button', 1) == 1
                and self.rect.collidepoint(event.pos)):
            return True
        return False

class ChatClient:
    """聊天网络客户端"""
    
    def __init__(self):
        self.sock = None
        self.server_addr = None
        self.running = False
        self.thread = None
        self.player_id = str(int(time.time()))
        self.connected = False
        self.messages: List[ChatMessage] = []
        self.players: List[Dict] = []
        self.on_message = None
    
    def connect(self, host: str, port: int, player_name: str):
        """连接到聊天服务器"""
        try:
            self.server_addr = (host, port)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(2)
            
            self.running = True
            self.thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.thread.start()
            
            self._send({
                'type': 'join',
                'player_id': self.player_id,
                'player_name': player_name
            })
            
            self.connected = True
            return True
        except Exception as e:
            logger.info(f"连接失败: {e}")
            return False
    
    def _receive_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                self._handle_message(data)
            except socket.timeout:
                if self.connected:
                    self._send({'type': 'ping', 'player_id': self.player_id})
            except (ConnectionResetError, OSError) as e:
                # UDP 发往无人监听的端口会收到 ICMP 端口不可达，
                # 在 Windows 上表现为 WinError 10054——这是常态不是故障，
                # 静默处理（每秒最多提示一次，避免刷日志）
                now = time.time()
                if now - getattr(self, '_last_reset_log', 0) > 1.0:
                    self._last_reset_log = now
                    logger.debug("[世界聊天] 服务器暂不可达（%s），继续等待",
                                 type(e).__name__)
            except Exception as e:
                if self.running:
                    logger.info(f"接收错误: {e}")
    
    def _handle_message(self, data: bytes):
        try:
            message = json.loads(data.decode('utf-8'))
            msg_type = message.get('type', '')
            
            if msg_type == 'chat':
                is_self = message.get('player_id', '') == self.player_id
                self.messages.append(ChatMessage(
                    message.get('text', ''),
                    message.get('player_name', ''),
                    'self' if is_self else 'other',
                    message.get('timestamp', 0)
                ))
                if len(self.messages) > 100:
                    self.messages.pop(0)
            
            elif msg_type == 'system':
                self.messages.append(ChatMessage(
                    message.get('text', ''),
                    '系统',
                    'system',
                    message.get('timestamp', 0)
                ))
                if len(self.messages) > 100:
                    self.messages.pop(0)
            
            elif msg_type == 'player_list':
                self.players = message.get('players', [])
            
            elif msg_type == 'history':
                for msg in message.get('messages', []):
                    if msg.get('type') == 'chat':
                        is_self = msg.get('player_id', '') == self.player_id
                        self.messages.append(ChatMessage(
                            msg.get('text', ''),
                            msg.get('player_name', ''),
                            'self' if is_self else 'other',
                            msg.get('timestamp', 0)
                        ))
                    elif msg.get('type') == 'system':
                        self.messages.append(ChatMessage(
                            msg.get('text', ''),
                            '系统',
                            'system',
                            msg.get('timestamp', 0)
                        ))
                    elif msg.get('type') == 'system':
                        self.messages.append(ChatMessage(
                            msg.get('text', ''),
                            '系统',
                            'system',
                            msg.get('timestamp', 0)
                        ))
            
            if self.on_message:
                self.on_message()
                
        except Exception as e:
            logger.info(f"解析错误: {e}")
    
    def send_chat(self, text: str):
        """发送聊天消息"""
        if not self.connected:
            return False
        
        self._send({
            'type': 'chat',
            'player_id': self.player_id,
            'player_name': data.get('player_name', '主公'),
            'text': text
        })
        return True
    
    def _send(self, data: Dict):
        """发送数据"""
        try:
            self.sock.sendto(json.dumps(data).encode('utf-8'), self.server_addr)
        except Exception as _e:
            logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)
    
    def disconnect(self):
        """断开连接"""
        if self.connected:
            self._send({'type': 'leave', 'player_id': self.player_id})
        
        self.running = False
        self.connected = False
        
        if self.sock:
            self.sock.close()
        
        if self.thread:
            self.thread.join(timeout=1)

class WorldChat:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.client = ChatClient()
        self.client.on_message = self._on_new_message
        
        self.init_fonts()
        self.init_ui()
        self.init_particles()
        
        self.state = "connect"  # connect, chatting
        self.chat_scroll = 0
        self.new_message_effects: List[Particle] = []
    
    def init_fonts(self):
        def init_font(size):
            return get_font(size)

        self.font_title = init_font(40)
        self.font_msg = init_font(22)
        self.font_ui = init_font(20)
        self.font_small = init_font(16)

    def init_ui(self):
        """连接页 + 聊天页的全部控件"""
        w, h = self.width, self.height
        # ── 聊天页 ──
        self.input_box = InputBox(30, h - 90, w - 200, 54, self.font_msg)
        self.send_btn = Button("发送", w - 150, h - 90, 120, 54,
                               self.font_ui, COLORS["accent_green"])
        # ── 连接页 ──
        self.name_box = InputBox(w // 2 - 170, h // 2 - 20, 340, 52, self.font_msg)
        self.name_box.text = data.get('player_name', '主公')
        self.addr_box = InputBox(w // 2 - 170, h // 2 + 60, 340, 52, self.font_msg)
        self.addr_box.text = "127.0.0.1:9999"
        self.connect_btn = Button("连接服务器", w // 2 - 240, h // 2 + 145, 220, 56,
                                  self.font_ui, COLORS["accent_green"])
        self.host_btn = Button("一键起服并连接", w // 2 + 20, h // 2 + 145, 220, 56,
                               self.font_ui, COLORS["accent_blue"])
        self.back_btn = Button("返回", 30, 30, 96, 44,
                               self.font_ui, COLORS["accent_red"])
        self.connect_error = ""

    def init_particles(self):
        self.new_message_effects: List[Particle] = []

    # ── 新消息回调（ChatClient 收到消息后触发）──
    def _on_new_message(self):
        # 底部冒金色粒子庆祝 + 自动滚到最新
        for _ in range(14):
            self.new_message_effects.append(Particle(
                random.uniform(self.width * 0.15, self.width * 0.85),
                self.height - random.uniform(80, 200),
                random.choice([COLORS["player_self"], COLORS["accent_gold"],
                               COLORS["player_other"]]),
                2.2, random.uniform(2, 5), random.randint(24, 48)))
        self.chat_scroll = 0

    # ── 工具：中文按像素宽度折行 ──
    def _wrap(self, text: str, font, max_w: int):
        lines, cur = [], ""
        for ch in text:
            if cur and font.size(cur + ch)[0] > max_w:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
        if cur:
            lines.append(cur)
        return lines or [""]

    def _parse_addr(self, text: str):
        text = (text or "").strip()
        if ":" in text:
            host, _, port = text.rpartition(":")
            try:
                return host or "127.0.0.1", int(port)
            except ValueError:
                return None
        return (text or "127.0.0.1", 9999) if text else None

    # ── 一键起服：拉起本地 chat_server.py 并连接 ──
    def _localhost(self, host: str) -> bool:
        return host in ("127.0.0.1", "localhost", "0.0.0.0", "::1")

    def _spawn_server(self, port: int):
        """后台拉起本地聊天服务器，返回 Popen；打包版/脚本缺失返回 None。

        输出重定向到临时目录日志，Windows 下 CREATE_NO_WINDOW 不弹黑框。
        进程句柄记录在 self._server_proc，退出时统一回收，不留孤儿。
        """
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "chat_server.py")
        if not os.path.isfile(script):
            return None
        if getattr(sys, "frozen", False):
            return None          # 打包环境没有独立 Python，起不了脚本
        try:
            kwargs = {}
            if os.name == "nt":
                kwargs["creationflags"] = 0x08000000     # CREATE_NO_WINDOW
            log = open(os.path.join(tempfile.gettempdir(),
                                    "san_guo_chat_server.log"), "ab")
            return subprocess.Popen([sys.executable, script, str(port)],
                                    stdout=log, stderr=subprocess.STDOUT,
                                    **kwargs)
        except Exception as e:
            logger.info("一键起服失败: %s", e)
            return None

    def _stop_local_server(self):
        """回收自己拉起的服务器进程（外部已存在的服务器不受影响）"""
        proc = getattr(self, "_server_proc", None)
        if proc is not None:
            try:
                proc.terminate()
            except Exception:
                pass
            self._server_proc = None

    def _start_local_and_connect(self):
        addr = self._parse_addr(self.addr_box.text)
        if not addr:
            self.connect_error = "服务器地址格式应为 IP:端口"
            return
        host, port = addr
        name = (self.name_box.text or "主公").strip()[:16]
        # 目标是本机且还没起过服务器 → 先起服（端口被占也没关系，
        # 新进程绑定失败会自行退出，已有服务器照常服务）
        if self._localhost(host) and getattr(self, "_server_proc", None) is None:
            proc = self._spawn_server(port)
            if proc is None:
                self.connect_error = ("一键起服需要 Python 环境；"
                                      "打包版请手动运行 ASSET/chat_server.py")
                return
            self._server_proc = proc
            time.sleep(0.8)          # 给服务器一点绑定端口的时间
        if self.client.connect(host, port, name):
            self.state = "chatting"
            self.client.messages.append(
                ChatMessage(f"欢迎，{name}！已连接 {host}:{port}",
                            "系统", "system"))
        else:
            self.connect_error = "连接失败，请检查地址与网络"

    # ── 事件 ──
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return False
        if self.state == "connect":
            self.name_box.handle_event(event)
            self.addr_box.handle_event(event)
            if self.back_btn.check_click(event, pygame.mouse.get_pos()):
                return False
            if self.connect_btn.check_click(event, pygame.mouse.get_pos()):
                addr = self._parse_addr(self.addr_box.text)
                name = (self.name_box.text or "主公").strip()[:16]
                if not addr:
                    self.connect_error = "服务器地址格式应为 IP:端口"
                elif self.client.connect(addr[0], addr[1], name):
                    self.state = "chatting"
                    self.client.messages.append(
                        ChatMessage(f"欢迎，{name}！已连接 {addr[0]}:{addr[1]}",
                                    "系统", "system"))
                else:
                    self.connect_error = "连接失败，请检查地址与网络"
                return True
            if self.host_btn.check_click(event, pygame.mouse.get_pos()):
                self._start_local_and_connect()
                return True
            return True
        # 聊天页
        if event.type == pygame.MOUSEWHEEL:
            max_scroll = max(0, self._total_lines() - self._visible_lines())
            self.chat_scroll = max(0, min(max_scroll,
                                          self.chat_scroll - event.y * 3))
            return True
        if self.back_btn.check_click(event, pygame.mouse.get_pos()):
            return False
        if self.send_btn.check_click(event, pygame.mouse.get_pos()):
            self._send_current()
            return True
        sent = self.input_box.handle_event(event)
        if sent:   # 输入框里按了回车
            self._send_current()
        return True

    def _send_current(self):
        text = self.input_box.text.strip()
        if not text:
            return
        if not self.client.send_chat(text):
            self.client.messages.append(
                ChatMessage("未连接服务器，消息没有发出去", "系统", "system"))
        self.input_box.text = ""
        self.chat_scroll = 0

    def _total_lines(self):
        """消息折行后的总行数（滚动上限用）"""
        max_w = self.width - 90
        return sum(len(self._wrap(m.text, self.font_msg, max_w))
                   for m in self.client.messages)

    def _visible_lines(self):
        return max(1, (self.height - 230) // 30)

    # ── 主循环 ──
    def run(self):
        clock = pygame.time.Clock()
        running = True
        try:
            while running:
                clock.tick(60)
                for ev in pygame.event.get():
                    if self.handle_event(ev) is False:
                        running = False
                self.input_box.update()
                for p in self.new_message_effects:
                    p.update()
                self.new_message_effects = [p for p in self.new_message_effects
                                            if p.life > 0]
                self.draw()
            self.client.disconnect()
        finally:
            # 无论正常退出还是异常退出，都回收自己拉起的服务器进程
            self._stop_local_server()

    # ── 绘制 ──
    def draw(self):
        mouse = pygame.mouse.get_pos()
        if self.state == "connect":
            self._draw_connect(mouse)
        else:
            self._draw_chat(mouse)
        # 新消息粒子（最上层）
        for p in self.new_message_effects:
            p.draw(self.screen)
        pygame.display.flip()

    def _draw_bg(self):
        """深色底 + 顶部金色氛围光（静态渐变，逐行画一次即可）"""
        self.screen.fill(COLORS["bg_dark"])
        glow = pygame.Surface((self.width, 220), pygame.SRCALPHA)
        for y in range(220):
            a = int(46 * (1 - y / 220))
            pygame.draw.line(glow, (255, 191, 0, a), (0, y), (self.width, y))
        self.screen.blit(glow, (0, 0))

    def _draw_connect(self, mouse):
        self._draw_bg()
        self.back_btn.draw(self.screen, mouse)
        cx = self.width // 2
        t = self.font_title.render("🌍 世界聊天", True, COLORS["accent_gold"])
        self.screen.blit(t, t.get_rect(center=(cx, self.height // 2 - 150)))

        lb = self.font_ui.render("你的名字", True, COLORS["text_gray"])
        self.screen.blit(lb, (self.name_box.rect.x, self.name_box.rect.y - 30))
        self.name_box.draw(self.screen)
        la = self.font_ui.render("服务器地址 (IP:端口)", True, COLORS["text_gray"])
        self.screen.blit(la, (self.addr_box.rect.x, self.addr_box.rect.y - 30))
        self.addr_box.draw(self.screen)
        self.connect_btn.draw(self.screen, mouse)
        self.host_btn.draw(self.screen, mouse)
        if self.connect_error:
            err = self.font_small.render(self.connect_error, True,
                                         COLORS["accent_red"])
            self.screen.blit(err, err.get_rect(
                center=(cx, self.height // 2 + 230)))
        tip = self.font_small.render(
            "需要配套聊天服务器；没有服务器也能进入界面查看", True, COLORS["text_gray"])
        self.screen.blit(tip, tip.get_rect(center=(cx, self.height - 60)))

    def _draw_chat(self, mouse):
        self._draw_bg()
        # 顶栏
        pygame.draw.rect(self.screen, COLORS["bg_panel"],
                         (0, 0, self.width, 76))
        pygame.draw.line(self.screen, COLORS["accent_gold"],
                         (0, 76), (self.width, 76), 2)
        title = self.font_title.render("🌍 世界聊天", True, COLORS["accent_gold"])
        self.screen.blit(title, (150, 12))
        online = self.font_small.render(
            f"在线 {max(1, len(self.client.players))} 人  ·  消息 {len(self.client.messages)}",
            True, COLORS["text_gray"])
        self.screen.blit(online, online.get_rect(
            center=(self.width - 160, 38)))
        self.back_btn.draw(self.screen, mouse)

        # 消息区（底部对齐 + 滚轮上翻）
        max_w = self.width - 90
        line_h = 30
        vis = self._visible_lines()
        lines = []                       # (颜色, 文本行)
        for m in self.client.messages[-80:]:
            col = m.get_color()
            name = m.sender if m.type != "system" else ""
            body = self._wrap(m.text, self.font_msg, max_w - 10)
            for i, ln in enumerate(body):
                prefix = f"{name}：" if (i == 0 and name) else ""
                lines.append((col, prefix + ln))
        total = len(lines)
        max_scroll = max(0, total - vis)
        self.chat_scroll = min(self.chat_scroll, max_scroll)
        show = lines[max(0, total - vis - self.chat_scroll):
                     max(0, total - self.chat_scroll)]
        # 半透明消息底板
        panel = pygame.Surface((self.width - 40, vis * line_h + 20),
                               pygame.SRCALPHA)
        panel.fill((*COLORS["bg_panel"], 120))
        self.screen.blit(panel, (20, 96))
        # 消息贴着底板底部往上排（少消息时也靠下，像真实聊天室）
        y = 106 + max(0, vis - len(show)) * line_h
        for col, ln in show:
            self.screen.blit(self.font_msg.render(ln, True, col), (36, y))
            y += line_h

        # 输入行
        self.input_box.draw(self.screen)
        self.send_btn.draw(self.screen, mouse)

def main(screen=None):
    try:
        if not pygame.get_init():
            pygame.init()
        
        if screen is None:
            screen = open_window()
            pygame.display.set_caption("🌍 三国游戏 - 世界聊天")
        
        chat = WorldChat(screen)
        chat.run()
        
        return True
    except Exception as e:
        logger.info(f"世界聊天异常: {e}")
        return False

if __name__ == "__main__":
    main()
