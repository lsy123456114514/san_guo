# -*- coding: utf-8 -*-
"""
配置文件管理器 - 负责配置的保存、加载和管理
支持游戏设置（分辨率、音效、语言等）的持久化存储
"""
import os
import json
import platform

try:
    from security_utils import get_user_data_dir
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False

# 默认配置
DEFAULT_CONFIG = {
    "graphics": {
        "resolution": "auto",  # auto, 800x600, 1024x768, 1280x720, 1920x1080
        "fullscreen": False,
        "fps_limit": 60,
        "scaling": 1.0,
        "ui_scale": 1.0
    },
    "sound": {
        "enable": True,
        "volume": 0.7,
        "music_volume": 0.5,
        "effect_volume": 0.8
    },
    "language": {
        "current": "zh",
        "supported": ["zh", "en", "ja"]
    },
    "gameplay": {
        "auto_save": True,
        "auto_save_interval": 300,  # 秒
        "show_tutorial": True,
        "tutorial_completed": False,
        "difficulty": "normal"
    },
    "controls": {
        "sensitivity": 1.0,
        "invert_mouse": False
    },
    "debug": {
        "show_fps": False,
        "show_debug_info": False,
        "log_level": "info"
    }
}

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        # 获取配置文件路径
        if SECURITY_AVAILABLE:
            self.config_dir = get_user_data_dir("三国群英传")
        else:
            self.config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
        
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_file = os.path.join(self.config_dir, 'config.json')
        
        # 加载配置
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并配置（保留默认值作为兜底）
                    return self.merge_config(DEFAULT_CONFIG, loaded_config)
            except Exception as e:
                print(f"加载配置失败，使用默认配置: {e}")
                return DEFAULT_CONFIG.copy()
        else:
            # 如果配置文件不存在，创建默认配置
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
    
    def merge_config(self, default, loaded):
        """合并配置，保留默认值作为兜底"""
        result = default.copy()
        if isinstance(loaded, dict):
            for key, value in loaded.items():
                if key in result:
                    if isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = self.merge_config(result[key], value)
                    else:
                        result[key] = value
        return result
    
    def save_config(self, config=None):
        """保存配置文件"""
        if config is None:
            config = self.config
        
        try:
            if os.path.exists(self.config_file):
                backup_path = self.config_file + ".bak"
                with open(self.config_file, "rb") as f_in:
                    with open(backup_path, "wb") as f_out:
                        f_out.write(f_in.read())
            
            temp_path = self.config_file + ".tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            os.rename(temp_path, self.config_file)
            
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def get(self, key, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key, value):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        for i, k in enumerate(keys[:-1]):
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        
        # 立即保存
        self.save_config()
    
    def get_resolution(self):
        """获取分辨率设置"""
        resolution = self.get('graphics.resolution', 'auto')
        return resolution
    
    def set_resolution(self, width, height):
        """设置分辨率"""
        self.set('graphics.resolution', f"{width}x{height}")
    
    def get_safe_resolution(self, screen_width, screen_height):
        """获取安全的分辨率（考虑小屏幕适配）"""
        resolution = self.get('graphics.resolution', 'auto')
        
        if resolution == 'auto':
            # 自动模式：使用屏幕的80%，但不小于800x600
            safe_width = int(screen_width * 0.8)
            safe_height = int(screen_height * 0.8)
            
            # 确保最小值（适合笔记本屏幕）
            safe_width = max(800, safe_width)
            safe_height = max(600, safe_height)
            
            # 确保不超过屏幕（留边距）
            safe_width = min(safe_width, screen_width - 50)
            safe_height = min(safe_height, screen_height - 50)
            
            # 确保宽高比合理（4:3 ~ 16:10）
            aspect_ratio = safe_width / safe_height
            if aspect_ratio < 4/3:
                safe_width = int(safe_height * 4/3)
            elif aspect_ratio > 16/10:
                safe_height = int(safe_width * 10/16)
            
            return safe_width, safe_height
        else:
            # 手动配置模式
            try:
                width, height = map(int, resolution.split('x'))
                # 验证并修正
                width = max(640, min(width, screen_width - 50))
                height = max(360, min(height, screen_height - 50))
                return width, height
            except ValueError:
                return self.get_safe_resolution(screen_width, screen_height)
    
    def is_tutorial_completed(self):
        """检查新手教程是否完成"""
        return self.get('gameplay.tutorial_completed', False)
    
    def set_tutorial_completed(self, completed=True):
        """设置新手教程完成状态"""
        self.set('gameplay.tutorial_completed', completed)
    
    def reset_to_default(self):
        """重置为默认配置"""
        self.config = DEFAULT_CONFIG.copy()
        self.save_config()
    
    def print_config(self):
        """打印当前配置（用于调试）"""
        print("当前配置:")
        print(json.dumps(self.config, ensure_ascii=False, indent=2))

# 创建全局配置管理器实例
config_manager = ConfigManager()

# 导出接口
__all__ = ['ConfigManager', 'config_manager', 'DEFAULT_CONFIG']