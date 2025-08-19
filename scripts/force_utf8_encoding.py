#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
强制设置UTF-8编码的脚本
在应用启动前运行，确保所有编码设置正确
"""

import os
import sys
import locale
import io

def force_utf8_encoding():
    """强制设置UTF-8编码"""
    print("🔧 强制设置UTF-8编码...")
    
    # 1. 设置环境变量
    encoding_vars = {
        'PYTHONIOENCODING': 'utf-8',
        'PYTHONLEGACYWINDOWSSTDIO': '1',
        'LANG': 'zh_CN.UTF-8',
        'LC_ALL': 'zh_CN.UTF-8',
        'LC_CTYPE': 'zh_CN.UTF-8'
    }
    
    for key, value in encoding_vars.items():
        os.environ[key] = value
    
    # 2. 重新配置标准输入输出
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            print("✅ 标准输入输出重新配置为UTF-8")
        except Exception as e:
            print(f"⚠️  标准输入输出重新配置失败: {e}")
    
    # 3. 设置默认编码（如果可能）
    if hasattr(sys, '_getframe'):
        try:
            # 这是一个hack，但在某些情况下有效
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
            print("✅ 使用codecs重新包装标准输出")
        except Exception as e:
            print(f"⚠️  codecs重新包装失败: {e}")
    
    # 4. 设置locale
    try:
        if os.name == 'nt':  # Windows
            locale.setlocale(locale.LC_ALL, 'Chinese_China.utf8')
        else:  # Unix/Linux
            locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
        print("✅ locale设置成功")
    except Exception as e:
        print(f"⚠️  locale设置失败: {e}")
    
    # 5. 测试编码
    test_text = "测试中文编码：你好世界！Hello World!"
    try:
        encoded = test_text.encode('utf-8')
        decoded = encoded.decode('utf-8')
        print(f"✅ 编码测试成功: {decoded}")
    except Exception as e:
        print(f"❌ 编码测试失败: {e}")
        return False
    
    print("🎉 UTF-8编码强制设置完成")
    return True

if __name__ == "__main__":
    success = force_utf8_encoding()
    if not success:
        sys.exit(1)