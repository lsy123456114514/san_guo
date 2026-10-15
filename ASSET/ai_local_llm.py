#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地小模型接入(llama.cpp) - 启动自动拉起、可开关、AI军师邮件推送

配合桌面 tiny-ai 目录使用（llama-server.exe + *.gguf 模型），
全程离线纯 CPU 运行，不依赖 requests / OLLAMA。
"""

import os
import time
import atexit
import json
import threading
import subprocess
import urllib.request
import urllib.error
from datetime import date

import pygame

from ASSET.game_data import data, save, logger, draw_gradient_bg, get_font
from ASSET.game_main_menu import Button, COLORS

DEFAULTS = {
    "enabled": False,      # 是否启用本地AI军师
    "decided": False,      # 是否已询问过玩家
    "server_exe": "",      # 手动指定 llama-server.exe（留空自动探测）
    "model_path": "",      # 手动指定 .gguf（留空自动探测）
    "port": 8080,
    "host": "127.0.0.1",
    "last_push": "",       # 最近一次军师来信日期 YYYY-MM-DD
}

_proc = None
_atexit_done = False
_GUO_SYSTEM = (
    "你是三国策略游戏中的军师。用古风白话给主公写短信，"
    "不超过60字，只输出正文，不要客套格式。内容结合经营建议或鼓励。"
)


def cfg():
    c = data.setdefault("ai_local", {})
    for k, v in DEFAULTS.items():
        c.setdefault(k, v)
    return c


def _game_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_install():
    """探测 (llama-server.exe, model.gguf)；找不到返回 (None, None)"""
    c = cfg()
    exe, model = c.get("server_exe") or "", c.get("model_path") or ""
    if exe and model and os.path.isfile(exe) and os.path.isfile(model):
        return exe, model

    g = _game_dir()
    llama_dirs = [
        os.path.join(g, "tiny-ai", "llama"),
        os.path.normpath(os.path.join(g, "..", "tiny-ai", "llama")),
        os.path.join(g, "llama"),
        os.path.join(os.path.expanduser("~"), "Desktop", "tiny-ai", "llama"),
        os.path.join(os.path.expanduser("~"), "tiny-ai", "llama"),
    ]
    for d in llama_dirs:
        e = os.path.join(d, "llama-server.exe")
        if not os.path.isfile(e):
            continue
        model_dirs = [
            os.path.normpath(os.path.join(d, "..", "models")),
            os.path.join(d, "models"),
        ]
        for md in model_dirs:
            if not os.path.isdir(md):
                continue
            ggufs = sorted(f for f in os.listdir(md) if f.lower().endswith(".gguf"))
            if not ggufs:
                continue
            pick = next((f for f in ggufs if "qwen" in f.lower()), ggufs[0])
            return e, os.path.join(md, pick)
    return None, None


def base_url():
    c = cfg()
    return "http://%s:%s" % (c["host"], c["port"])


def is_running(timeout=1.5):
    try:
        req = urllib.request.Request(base_url() + "/health")
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except Exception:
        return False


def start_server(wait_secs=20):
    """拉起 llama-server；已在运行则直接返回 True"""
    global _proc, _atexit_done
    if is_running():
        return True
    exe, model = find_install()
    if not exe:
        logger.warning("[AI本地] 未找到 tiny-ai 安装目录")
        return False
    try:
        c = cfg()
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        devnull = open(os.devnull, "w")
        _proc = subprocess.Popen(
            [exe, "-m", model, "--port", str(c["port"]), "-c", "4096", "--no-warmup"],
            stdout=devnull, stderr=devnull, stdin=devnull,
            creationflags=flags,
        )
    except Exception as e:
        logger.error("[AI本地] 启动失败: %s", e)
        return False
    if not _atexit_done:
        atexit.register(stop_server)
        _atexit_done = True
    t0 = time.time()
    while time.time() - t0 < wait_secs:
        if is_running():
            logger.info("[AI本地] 服务就绪 %s model=%s", base_url(), os.path.basename(model))
            return True
        if _proc.poll() is not None:
            logger.error("[AI本地] llama-server 进程提前退出 code=%s", _proc.returncode)
            return False
        time.sleep(0.4)
    logger.error("[AI本地] 等待服务就绪超时(%ss)", wait_secs)
    return False


def stop_server():
    global _proc
    p, _proc = _proc, None
    if p is None or p.poll() is not None:
        return
    try:
        p.terminate()
        p.wait(3)
    except Exception:
        try:
            p.kill()
        except Exception:
            pass
    logger.info("[AI本地] 服务已停止")


def chat(prompt, system=None, max_tokens=160, timeout=90):
    """调用本地 OpenAI 兼容接口；失败返回空串"""
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    body = json.dumps({
        "model": "local", "messages": msgs,
        "max_tokens": max_tokens, "temperature": 0.8, "stream": False,
    }).encode("utf-8")
    req = urllib.request.Request(
        base_url() + "/v1/chat/completions",
        data=body, headers={"Content-Type": "application/json"}, method="POST",
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            j = json.loads(r.read().decode("utf-8"))
        txt = j["choices"][0]["message"]["content"].strip()
        logger.info("[AI本地] 生成完成 耗时%.2fs len=%d", time.perf_counter() - t0, len(txt))
        return txt
    except Exception as e:
        logger.error("[AI本地] chat失败: %s", e)
        return ""


def push_advisor_mail(force=False):
    """AI军师来信推送（每天最多一封）"""
    c = cfg()
    today = date.today().isoformat()
    if not force and c.get("last_push") == today:
        return False
    content = chat("主公，今日可有见教？请写一封军师来信。", system=_GUO_SYSTEM, max_tokens=120, timeout=60)
    if not content:
        content = "主公亲启：今岁风调雨顺，宜积粮筑城、招贤纳士。静待时机，可图中原。——军师敬上"
    try:
        from ASSET.gameplay_systems import MailSystem
        MailSystem().add_mail(sender="AI军师", title="军师来信", content=content, mail_type="ai")
    except Exception as e:
        logger.error("[AI本地] 推送邮件失败: %s", e)
        return False
    c["last_push"] = today
    save()
    logger.info("[AI本地] 已推送军师来信")
    return True


def _wrap(text, font, max_w):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n" or font.size(cur + ch)[0] > max_w:
            lines.append(cur)
            cur = "" if ch == "\n" else ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def _ask(screen, title, lines):
    """启动选择对话框：返回 True=启用"""
    clock = pygame.time.Clock()
    font = get_font(26)
    big = get_font(40)
    W, H = screen.get_size()
    yes = Button("启用AI军师", W // 2 - 220, H // 2 + 90, 200, 52, font, normal_color=COLORS["accent_green"])
    no = Button("暂不使用", W // 2 + 20, H // 2 + 90, 200, 52, font, normal_color=COLORS["accent_blue_dark"])
    wrapped = []
    for para in lines:
        wrapped.extend(_wrap(para, font, W - 160) or [""])
    while True:
        draw_gradient_bg(screen, COLORS["bg_dark"], COLORS["bg_light"])
        t = big.render(title, True, COLORS["accent_gold"])
        screen.blit(t, (W // 2 - t.get_width() // 2, H // 2 - 150))
        y = H // 2 - 70
        for ln in wrapped:
            s = font.render(ln, True, COLORS["text_white"])
            screen.blit(s, (W // 2 - s.get_width() // 2, y))
            y += s.get_height() + 6
        hint = font.render("（也可以随时在“游戏内AI”模块里开关）", True, COLORS["text_gray"])
        screen.blit(hint, (W // 2 - hint.get_width() // 2, H // 2 + 160))
        for b in (yes, no):
            b.check_hover(pygame.mouse.get_pos())
            b.draw(screen)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_y, pygame.K_RETURN):
                    return True
                if e.key in (pygame.K_n, pygame.K_ESCAPE):
                    return False
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if yes.check_click(e.pos):
                    return True
                if no.check_click(e.pos):
                    return False
        pygame.display.flip()
        clock.tick(60)


def ai_startup_gate(screen=None):
    """main_game 启动钩子：首次询问、按需自启、推送军师来信"""
    screen = pygame.display.get_surface() or screen
    c = cfg()
    if not c.get("decided"):
        exe, model = find_install()
        if exe:
            ok = _ask(screen, "AI军师（本地小模型）", [
                "检测到本机安装了 tiny-ai 小模型，可离线启用AI军师：",
                "模型: %s（纯CPU运行，不联网、不上传任何数据）" % os.path.basename(model),
                "启用后每次启动游戏会自动运行小模型，并可能向邮箱推送军师来信。",
            ])
            c["enabled"] = bool(ok and exe)
        else:
            ok = _ask(screen, "AI军师（本地小模型）", [
                "未在本机找到 tiny-ai 小模型目录，暂时无法启用。",
                "如需使用，请先安装 tiny-ai（llama-server + gguf 模型）。",
            ])
            c["enabled"] = False
        c["decided"] = True
        save()

    if not c.get("enabled"):
        return False
    ok = start_server()
    if ok:
        try:
            push_advisor_mail()
        except Exception as e:
            logger.error("[AI本地] 启动推送异常: %s", e)
    else:
        logger.warning("[AI本地] 已启用但服务启动失败，本次跳过")
    return ok
