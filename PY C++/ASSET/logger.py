#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统 - 将所有日志和错误信息记录到文件
"""
import os
import sys
import traceback
import datetime

# 日志文件路径
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'game.log')
ERROR_LOG_FILE = os.path.join(LOG_DIR, 'error.log')

# 确保日志目录存在
os.makedirs(LOG_DIR, exist_ok=True)

def get_timestamp():
    """获取当前时间戳"""
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def log_info(message):
    """记录普通日志信息"""
    timestamp = get_timestamp()
    log_entry = f"[{timestamp}] [INFO] {message}\n"
    
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
        error_msg += f"[{timestamp}] [ERROR] 异常信息: {str(exc_value)}\n"
        error_msg += f"[{timestamp}] [ERROR] 完整堆栈跟踪:\n"
        
        # 获取详细堆栈信息
        tb_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
        for tb_line in tb_list:
            for line in tb_line.split('\n'):
                if line.strip():
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
