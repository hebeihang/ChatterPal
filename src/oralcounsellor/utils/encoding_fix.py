# -*- coding: utf-8 -*-
"""
编码修复工具模块
用于解决中文字符编码问题
"""

import os
import sys
import logging
from typing import Any

def setup_utf8_environment():
    """设置UTF-8编码环境"""
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if os.name == 'nt':  # Windows
        os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '1'
    
    # 重新配置标准输入输出
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except:
            pass

def safe_str(obj: Any) -> str:
    """安全的字符串转换，处理编码问题"""
    if obj is None:
        return ""
    
    if isinstance(obj, bytes):
        try:
            return obj.decode('utf-8', errors='replace')
        except:
            return str(obj, errors='replace')
    
    try:
        return str(obj)
    except UnicodeEncodeError:
        # 如果转换失败，尝试编码后再解码
        try:
            return str(obj).encode('utf-8', errors='replace').decode('utf-8')
        except:
            return repr(obj)

def safe_log(logger: logging.Logger, level: str, message: str, *args, **kwargs):
    """安全的日志记录，避免编码错误"""
    try:
        # 确保消息是安全的字符串
        safe_message = safe_str(message)
        safe_args = [safe_str(arg) for arg in args]
        
        # 调用相应的日志方法
        log_method = getattr(logger, level.lower())
        log_method(safe_message, *safe_args, **kwargs)
    except Exception as e:
        # 如果日志记录失败，至少打印到控制台
        try:
            print(f"日志记录失败: {safe_str(e)}")
            print(f"原始消息: {safe_str(message)}")
        except:
            print("日志记录和错误处理都失败了")

class SafeLogger:
    """安全的日志记录器包装器"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def debug(self, message: str, *args, **kwargs):
        safe_log(self.logger, 'debug', message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        safe_log(self.logger, 'info', message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        safe_log(self.logger, 'warning', message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        safe_log(self.logger, 'error', message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        safe_log(self.logger, 'critical', message, *args, **kwargs)

def create_safe_logger(name: str) -> SafeLogger:
    """创建安全的日志记录器"""
    logger = logging.getLogger(name)
    return SafeLogger(logger)

# 在模块导入时自动设置UTF-8环境
setup_utf8_environment()