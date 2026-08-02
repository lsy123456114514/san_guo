#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统 - 将所有日志和错误信息记录到文件（安全版）
"""
import os
import sys
import traceback
import datetime
import json

# 导入安全工具
try:
    from security_utils import get_user_data_dir
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False

# 日志文件路径（使用安全的用户数据目录）
if SECURITY_AVAILABLE:
    LOG_DIR = os.path.join(get_user_data_dir("三国群英传"), 'logs')
else:
    LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')

LOG_FILE = os.path.join(LOG_DIR, 'game.log')
ERROR_LOG_FILE = os.path.join(LOG_DIR, 'error.log')

# 确保日志目录存在
os.makedirs(LOG_DIR, exist_ok=True)

# 需要脱敏的敏感字段
SENSITIVE_FIELDS = [
    'password', 'pwd', 'pass', 'token', 'key', 
    'secret', 'api_key', 'access_token',
    'phone', 'mobile', 'tel', 'email', 'mail',
    'id_card', '身份证', '银行卡', 'bank'
]

def get_timestamp():
    """获取当前时间戳"""
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def sanitize_data(data):
    """脱敏处理 - 移除敏感信息"""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # 检查键名是否敏感
            key_lower = key.lower()
            is_sensitive = any(field in key_lower for field in SENSITIVE_FIELDS)
            
            if is_sensitive:
                result[key] = '***已脱敏***'
            elif isinstance(value, dict):
                result[key] = sanitize_data(value)
            elif isinstance(value, str) and len(value) > 50:
                result[key] = value[:50] + '...'
            else:
                result[key] = value
        return result
    elif isinstance(data, str):
        # 检查字符串内容是否包含敏感信息
        for field in SENSITIVE_FIELDS:
            if field.lower() in data.lower():
                return '***包含敏感信息***'
        if len(data) > 100:
            return data[:100] + '...'
    return data

def log_info(message, data=None):
    """记录普通日志信息"""
    timestamp = get_timestamp()
    log_entry = f"[{timestamp}] [INFO] {message}"
    
    if data:
        sanitized_data = sanitize_data(data)
        try:
            log_entry += f" | 数据: {json.dumps(sanitized_data, ensure_ascii=False)}"
        except Exception:
            log_entry += f" | 数据: {str(sanitized_data)[:100]}..."
    
    log_entry += "\n"
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception:
        pass

def log_warning(message):
    """记录警告信息"""
    timestamp = get_timestamp()
    log_entry = f"[{timestamp}] [WARNING] {message}\n"
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception:
        pass

def log_error(message):
    """记录错误信息（包含完整堆栈跟踪）"""
    timestamp = get_timestamp()
    
    # 获取完整的错误堆栈
    exc_type, exc_value, exc_traceback = sys.exc_info()
    
    error_msg = f"[{timestamp}] [ERROR] {message}\n"
    
    if exc_type is not None:
        error_msg += f"[{timestamp}] [ERROR] 异常类型: {exc_type.__name__}\n"
        # 脱敏异常信息
        exc_str = str(exc_value)
        sanitized_exc = sanitize_data(exc_str)
        error_msg += f"[{timestamp}] [ERROR] 异常信息: {sanitized_exc}\n"
        error_msg += f"[{timestamp}] [ERROR] 完整堆栈跟踪:\n"
        
        # 获取详细堆栈信息
        tb_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
        for tb_line in tb_list:
            for line in tb_line.split('\n'):
                if line.strip():
                    # 脱敏堆栈中的路径信息
                    if 'File "' in line:
                        # 只保留文件名，去掉完整路径
                        parts = line.split('File "')
                        if len(parts) > 1:
                            file_part = parts[1].split('",')[0]
                            filename = os.path.basename(file_part)
                            line = line.replace(file_part, filename)
                    error_msg += f"  {line}\n"
    
    try:
        # 写入主日志文件
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(error_msg)
        
        # 同时写入错误专用日志文件
        with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(error_msg)
    except Exception:
        pass

def log_debug(message):
    """记录调试信息"""
    timestamp = get_timestamp()
    log_entry = f"[{timestamp}] [DEBUG] {message}\n"
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception:
        pass

def log_exception(message):
    """记录异常信息（自动捕获堆栈跟踪）"""
    log_error(message)

def setup_logger():
    """初始化日志系统"""
    log_info("=" * 60)
    log_info("日志系统初始化")
    log_info(f"日志文件: {LOG_FILE}")
    log_info(f"错误日志: {ERROR_LOG_FILE}")
    log_info("=" * 60)

def get_recent_logs(lines=50):
    """获取最近的日志内容"""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return ''.join(all_lines[-lines:])
    except Exception:
        pass
    return ""

def get_recent_errors(lines=30):
    """获取最近的错误日志"""
    try:
        if os.path.exists(ERROR_LOG_FILE):
            with open(ERROR_LOG_FILE, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return ''.join(all_lines[-lines:])
    except Exception:
        pass
    return ""

# 初始化日志系统
setup_logger()