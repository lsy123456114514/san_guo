# -*- coding: utf-8 -*-
"""
语音命令模块 - 简化版
跳过Vosk模型下载问题，使用简单的命令匹配
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
        print("✅ 命令管理器初始化成功")
    
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
            "关机": "shutdown /s /t 30",
            "取消关机": "shutdown /a",
            "重启": "shutdown /r /t 30",
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
        print(f"🔍 尝试匹配命令: '{phrase}'")
        
        if phrase in self.commands:
            action = self.commands[phrase]
            print(f"✅ 找到匹配命令: '{phrase}' -> '{action}'")
            try:
                subprocess.Popen(action, shell=True)
                print(f"✅ 命令执行成功")
                return True, f"执行命令: {phrase}"
            except Exception as e:
                print(f"❌ 命令执行失败: {e}")
                return False, f"执行失败: {str(e)}"
        else:
            for cmd_phrase in self.commands:
                if cmd_phrase in phrase or phrase in cmd_phrase:
                    action = self.commands[cmd_phrase]
                    print(f"⚠️ 模糊匹配: '{phrase}' -> '{cmd_phrase}'")
                    try:
                        subprocess.Popen(action, shell=True)
                        return True, f"执行命令: {cmd_phrase} (匹配: {phrase})"
                    except Exception as e:
                        return False, f"执行失败: {str(e)}"
            
            print(f"❌ 未找到匹配的命令")
            print(f"   可用命令: {list(self.commands.keys())}")
            return False, f"未找到命令: {phrase}"
    
    def recognize_speech(self):
        """简化版：手动输入测试"""
        print("\n🎤 语音识别（测试模式）")
        print("请输入命令（如：打开记事本）: ")
        try:
            text = input().strip()
            print(f"✨ 输入内容: '{text}'")
            return text
        except:
            return None
    
    def listen_and_execute(self):
        """监听并执行命令"""
        text = self.recognize_speech()
        if text:
            return self.execute_command(text)
        return False, "未输入命令"
    
    def list_commands(self):
        """获取所有命令列表"""
        return list(self.commands.keys())
