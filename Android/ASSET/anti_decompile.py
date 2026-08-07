"""反混淆/反破解运行期检测（发布版启用）"""

import os
import sys
import hashlib
import time
import random
import traceback
from ASSET.game_data import draw_gradient_bg, cull_dead, get_font

# 反反编译保护模块
class AntiDecompile:
    def __init__(self):
        self.protected = False
        self.start_time = time.time()
        self.random_key = self.generate_random_key()
        self.file_hashes = {}
        self.init_protection()
    
    def generate_random_key(self):
        """生成随机密钥"""
        return ''.join([chr(random.randint(32, 126)) for _ in range(32)])
    
    def get_file_hash(self, file_path):
        """计算文件哈希值"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.sha256(content).hexdigest()
        except Exception as _e:
            return None
    
    def init_protection(self):
        """初始化保护机制"""
        # 记录关键文件的哈希值
        self.record_file_hashes()
        # 启动保护线程
        self.start_protection()
    
    def record_file_hashes(self):
        """记录关键文件的哈希值"""
        # 记录主要Python文件的哈希值
        key_files = [
            'game_data.py',
            'hero_warehouse.py',
            'game_main_menu.py',
            'login_system.py'
        ]
        
        for file_name in key_files:
            file_path = os.path.join(os.path.dirname(__file__), file_name)
            if os.path.exists(file_path):
                self.file_hashes[file_name] = self.get_file_hash(file_path)
    
    def start_protection(self):
        """启动保护机制"""
        self.protected = True
        # 检查运行环境
        self.check_environment()
        # 检查文件完整性
        self.check_file_integrity()
    
    def check_environment(self):
        """检查运行环境"""
        # 检查是否在被调试
        self.check_debugger()
        # 检查是否在虚拟机中运行
        self.check_virtual_machine()
    
    def check_debugger(self):
        """检查是否在被调试"""
        try:
            # 简单的反调试检测
            import ctypes
            kernel32 = ctypes.WinDLL('kernel32')
            is_debugger_present = kernel32.IsDebuggerPresent()
            if is_debugger_present:
                self.trigger_protection()
        except Exception as _e:
            logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)
    
    def check_virtual_machine(self):
        """检查是否在虚拟机中运行"""
        try:
            # 检查常见的虚拟机特征
            vm_signatures = [
                'VBOX', 'VMware', 'QEMU', 'VirtualBox', 'Hyper-V'
            ]
            
            # 检查系统信息
            import platform
            system_info = platform.platform() + platform.machine()
            for signature in vm_signatures:
                if signature.lower() in system_info.lower():
                    self.trigger_protection()
        except Exception as _e:
            logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)
    
    def check_file_integrity(self):
        """检查文件完整性"""
        for file_name, original_hash in self.file_hashes.items():
            file_path = os.path.join(os.path.dirname(__file__), file_name)
            if os.path.exists(file_path):
                current_hash = self.get_file_hash(file_path)
                if current_hash != original_hash:
                    self.trigger_protection()
    
    def trigger_protection(self):
        """触发保护机制"""
        # 可以根据需要调整保护措施
        # 这里采用简单的退出策略
        print("检测到异常操作，程序将退出")
        sys.exit(1)
    
    def encrypt_string(self, text):
        """简单的字符串加密"""
        encrypted = []
        for i, char in enumerate(text):
            key_char = self.random_key[i % len(self.random_key)]
            encrypted_char = chr(ord(char) ^ ord(key_char))
            encrypted.append(encrypted_char)
        return ''.join(encrypted)
    
    def decrypt_string(self, encrypted_text):
        """解密字符串"""
        decrypted = []
        for i, char in enumerate(encrypted_text):
            key_char = self.random_key[i % len(self.random_key)]
            decrypted_char = chr(ord(char) ^ ord(key_char))
            decrypted.append(decrypted_char)
        return ''.join(decrypted)
    
    def obfuscate_code(self, code):
        """简单的代码混淆"""
        # 这里只是一个简单的示例，实际混淆可以更复杂
        obfuscated = code
        # 替换一些常见的关键字
        replacements = {
            'def ': 'define_',
            'class ': 'create_class_',
            'import ': 'load_module_',
            'from ': 'from_module_'
        }
        for old, new in replacements.items():
            obfuscated = obfuscated.replace(old, new)
        return obfuscated

# 创建全局反反编译实例
anti_decompile = AntiDecompile()

# 导出保护函数
def protect_function(func):
    """保护函数不被反编译"""
    def wrapper(*args, **kwargs):
        try:
            # 执行原始函数
            result = func(*args, **kwargs)
            # 检查运行时间，防止单步调试
            if time.time() - anti_decompile.start_time > 300:  # 5分钟
                anti_decompile.start_time = time.time()
                anti_decompile.check_file_integrity()
            return result
        except Exception as e:
            # 捕获异常，防止调试器捕获，但显示详细错误
            import traceback
            print(f"函数 {func.__name__} 执行异常: {str(e)}")
            print("详细错误信息:")
            traceback.print_exc()
            # 不要返回 None，重新抛出异常以便调试
            raise
    return wrapper

def protect_variable(var_name, value):
    """保护变量不被轻易访问"""
    encrypted_value = anti_decompile.encrypt_string(str(value))
    return encrypted_value

def get_protected_variable(encrypted_value):
    """获取受保护的变量"""
    return anti_decompile.decrypt_string(encrypted_value)
