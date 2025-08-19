#!/usr/bin/env python3
"""
修复编码问题的脚本
"""

import os
import sys
import locale

def fix_encoding():
    """修复编码问题"""
    print("🔧 修复编码问题...")
    
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['LANG'] = 'zh_CN.UTF-8'
    os.environ['LC_ALL'] = 'zh_CN.UTF-8'
    
    # 设置默认编码
    if hasattr(sys, 'setdefaultencoding'):
        sys.setdefaultencoding('utf-8')
    
    # 检查当前编码设置
    print(f"系统默认编码: {sys.getdefaultencoding()}")
    print(f"文件系统编码: {sys.getfilesystemencoding()}")
    print(f"标准输出编码: {sys.stdout.encoding}")
    print(f"标准错误编码: {sys.stderr.encoding}")
    
    try:
        print(f"本地化设置: {locale.getdefaultlocale()}")
    except:
        print("无法获取本地化设置")
    
    print("✅ 编码设置完成")

if __name__ == "__main__":
    fix_encoding()