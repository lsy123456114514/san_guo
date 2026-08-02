# -*- coding: utf-8 -*-
"""
安全工具模块 - 提供加密、路径验证、安全存储等功能
"""
import os
import sys
import hashlib
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

# 获取安全的用户数据目录
def get_user_data_dir(app_name="三国群英传"):
    """获取安全的用户数据目录（避免权限问题）"""
    if sys.platform == 'win32':
        # Windows: C:\Users\<用户名>\AppData\Roaming\<应用名>
        try:
            from win32com.shell import shell, shellcon
            return os.path.join(shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, None, 0), app_name)
        except ImportError:
            # 降级方案
            return os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), app_name)
    elif sys.platform == 'darwin':
        # macOS: ~/Library/Application Support/<应用名>
        return os.path.join(os.path.expanduser('~/Library/Application Support'), app_name)
    else:
        # Linux: ~/.local/share/<应用名>
        return os.path.join(os.path.expanduser('~/.local/share'), app_name)

# 路径白名单验证
def validate_file_path(filepath, allowed_dirs=None):
    """验证文件路径是否在允许的目录内"""
    if not filepath:
        return False, "路径为空"
    
    # 标准化路径
    filepath = os.path.abspath(os.path.normpath(filepath))
    
    # 默认允许的目录
    if allowed_dirs is None:
        allowed_dirs = [
            os.path.abspath('.'),
            get_user_data_dir(),
            os.path.abspath('ASSET'),
            os.path.abspath('data'),
            os.path.abspath('voice_data'),
        ]
    
    # 检查路径遍历攻击
    if '..' in filepath.split(os.sep):
        return False, "检测到路径遍历攻击"
    
    # 检查是否在允许的目录内
    for allowed_dir in allowed_dirs:
        allowed_dir = os.path.abspath(os.path.normpath(allowed_dir))
        if filepath.startswith(allowed_dir):
            return True, "路径验证通过"
    
    return False, f"路径不在允许的目录内: {filepath}"

# 加密相关功能
class SecureStorage:
    """安全存储类 - 提供加密存储功能"""
    
    def __init__(self, password="sanguo2026", salt=b'sanguo_salt_2026'):
        self.password = password.encode()
        self.salt = salt
        self.key = self._generate_key()
    
    def _generate_key(self):
        """生成加密密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password))
        return key
    
    def encrypt_data(self, data):
        """加密数据"""
        try:
            fernet = Fernet(self.key)
            if isinstance(data, dict):
                data_str = json.dumps(data, ensure_ascii=False)
            else:
                data_str = str(data)
            encrypted = fernet.encrypt(data_str.encode('utf-8'))
            return encrypted.decode('utf-8')
        except Exception as e:
            # 如果加密失败，返回原始数据（降级处理）
            if isinstance(data, dict):
                return json.dumps(data, ensure_ascii=False)
            return str(data)
    
    def decrypt_data(self, encrypted_data):
        """解密数据"""
        try:
            fernet = Fernet(self.key)
            decrypted = fernet.decrypt(encrypted_data.encode('utf-8'))
            data_str = decrypted.decode('utf-8')
            try:
                return json.loads(data_str)
            except json.JSONDecodeError:
                return data_str
        except Exception:
            # 如果解密失败，尝试作为原始数据返回
            try:
                return json.loads(encrypted_data)
            except json.JSONDecodeError:
                return encrypted_data

# 安全日志记录
class SecureLogger:
    """安全日志类 - 避免记录敏感信息"""
    
    def __init__(self, log_dir=None):
        if log_dir is None:
            log_dir = os.path.join(get_user_data_dir(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, 'secure_game.log')
        self.error_file = os.path.join(log_dir, 'secure_error.log')
        
        # 需要脱敏的敏感字段
        self.sensitive_fields = [
            'password', 'pwd', 'pass', 'token', 'key', 
            'secret', 'api_key', 'access_token',
            'phone', 'mobile', 'tel', 'email', 'mail',
            'id_card', '身份证', '银行卡', 'bank'
        ]
    
    def _sanitize_data(self, data):
        """脱敏处理 - 移除敏感信息"""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # 检查键名是否敏感
                key_lower = key.lower()
                is_sensitive = any(field in key_lower for field in self.sensitive_fields)
                
                if is_sensitive:
                    result[key] = '***已脱敏***'
                elif isinstance(value, dict):
                    result[key] = self._sanitize_data(value)
                elif isinstance(value, str) and len(value) > 20:
                    result[key] = value[:20] + '...'
                else:
                    result[key] = value
            return result
        return data
    
    def log_info(self, message, data=None):
        """记录信息日志"""
        try:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"[{timestamp}] [INFO] {message}"
            
            if data:
                sanitized_data = self._sanitize_data(data)
                log_entry += f" | 数据: {json.dumps(sanitized_data, ensure_ascii=False, indent=2)}"
            
            log_entry += "\n"
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception:
            pass
    
    def log_error(self, message, exception=None):
        """记录错误日志"""
        try:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"[{timestamp}] [ERROR] {message}"
            
            if exception:
                import traceback
                log_entry += f"\n[{timestamp}] [ERROR] 异常: {str(exception)}"
                log_entry += f"\n[{timestamp}] [ERROR] 堆栈: {traceback.format_exc()}"
            
            log_entry += "\n"
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            
            with open(self.error_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception:
            pass
    
    def log_warning(self, message):
        """记录警告日志"""
        try:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"[{timestamp}] [WARNING] {message}\n"
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception:
            pass

# 导入必要模块
import datetime
import base64

# 创建全局安全存储实例
secure_storage = SecureStorage()
secure_logger = SecureLogger()

# 导出接口
__all__ = [
    'get_user_data_dir',
    'validate_file_path',
    'SecureStorage',
    'SecureLogger',
    'secure_storage',
    'secure_logger'
]