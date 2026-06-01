# -*- coding: utf-8 -*-
"""
语音命令模块
支持语音控制电脑（简化版，避免额外依赖）
"""

import json
import os
import subprocess
from pathlib import Path


class VoiceCommands:
    """语音命令管理器（简化版）"""
    
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.commands_file = self.data_dir / "commands.json"
        self.commands = self.load_commands()
    
    def load_commands(self):
        """加载命令"""
        if self.commands_file.exists():
            with open(self.commands_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "打开浏览器": "start chrome",
            "打开记事本": "start notepad",
            "关闭窗口": "taskkill /f /im notepad.exe",
            "打开音乐": "start wmplayer",
            "打开设置": "start ms-settings:",
            "打开计算器": "start calc",
            "打开文件管理器": "start explorer",
        }
    
    def save_commands(self):
        """保存命令"""
        with open(self.commands_file, 'w', encoding='utf-8') as f:
            json.dump(self.commands, f, ensure_ascii=False, indent=2)
    
    def add_command(self, phrase, action):
        """添加命令"""
        self.commands[phrase] = action
        self.save_commands()
    
    def remove_command(self, phrase):
        """删除命令"""
        if phrase in self.commands:
            del self.commands[phrase]
            self.save_commands()
    
    def execute_command(self, phrase):
        """执行命令"""
        if phrase in self.commands:
            action = self.commands[phrase]
            try:
                subprocess.Popen(action, shell=True)
                return True, f"执行命令: {phrase}"
            except Exception as e:
                return False, f"执行失败: {str(e)}"
        return False, "未找到命令"
    
    def listen_and_execute(self):
        """简化版：不依赖speech_recognition，直接显示提示"""
        return False, "语音识别需要额外安装 speech_recognition 模块\n请使用输入框测试命令功能"
    
    def list_commands(self):
        """获取所有命令列表"""
        return list(self.commands.keys())
