#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中文输入法（IME）辅助模块

pygame-ce 中中文上屏依赖 SDL 的文本输入状态：
  · 选字框（候选窗）只有在 text input 激活时才会出现；
  · 中文提交文本会挂到最后一个 KEYDOWN 的 event.unicode 上。
主菜单搜索框失焦时会 stop_text_input()，若不按设置重新启用，
后续界面（世界聊天、AI 对话等）的输入法就完全失效。
本模块按 data['settings']['input']['ime']（默认开）统一启停并定位选字框。
"""

import pygame
from ASSET.game_data import data, save, logger

# 本模块记录的文本输入状态（供无 TEXTINPUT 时的 KEYDOWN 兜底判断）
_active = True


def ime_enabled():
    """读取设置里的中文输入法开关（缺省为开）。"""
    return data.get("settings", {}).get("input", {}).get("ime", True)


def set_ime(enabled):
    """写入设置并立即生效。"""
    data.setdefault("settings", {}).setdefault("input", {})["ime"] = bool(enabled)
    save()
    apply_text_input()


def apply_text_input():
    """按设置启停 SDL 文本输入（选字框出现的前提）。"""
    global _active
    try:
        if ime_enabled():
            pygame.key.start_text_input()
            _active = True
        else:
            pygame.key.stop_text_input()
            _active = False
    except Exception as e:
        logger.debug("[IME] 切换文本输入失败: %s", e)


def is_active():
    """文本输入当前是否处于启用状态（由本模块启停记录）。"""
    return bool(_active)


def ensure_started():
    """进入输入类界面时调用：设置为开则确保文本输入已启用。"""
    if ime_enabled():
        apply_text_input()


def focus_rect(rect):
    """把输入法选字框定位到指定输入框位置。"""
    if rect is None:
        return
    try:
        pygame.key.set_text_input_rect(rect)
    except Exception:
        pass
