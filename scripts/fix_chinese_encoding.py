#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复中文编码问题的脚本
"""

import os
import sys
import locale
from pathlib import Path

def setup_chinese_encoding():
    """设置中文编码环境"""
    print("🔧 设置中文编码环境...")
    
    # 设置环境变量
    encoding_vars = {
        'PYTHONIOENCODING': 'utf-8',
        'PYTHONLEGACYWINDOWSSTDIO': '1',  # Windows 特有
        'LANG': 'zh_CN.UTF-8',
        'LC_ALL': 'zh_CN.UTF-8',
        'LC_CTYPE': 'zh_CN.UTF-8'
    }
    
    for key, value in encoding_vars.items():
        os.environ[key] = value
        print(f"   设置 {key}={value}")
    
    # 检查当前编码设置
    print("\n📊 当前编码设置:")
    print(f"   系统默认编码: {sys.getdefaultencoding()}")
    print(f"   文件系统编码: {sys.getfilesystemencoding()}")
    print(f"   标准输出编码: {sys.stdout.encoding}")
    print(f"   标准错误编码: {sys.stderr.encoding}")
    
    try:
        default_locale = locale.getdefaultlocale()
        print(f"   默认本地化: {default_locale}")
    except Exception as e:
        print(f"   本地化设置获取失败: {e}")
    
    # 测试中文字符处理
    print("\n🧪 测试中文字符处理:")
    test_text = "你好，这是一个中文测试。Hello, this is an English test."
    try:
        encoded = test_text.encode('utf-8')
        decoded = encoded.decode('utf-8')
        print(f"   ✅ 中文编码测试成功: {decoded}")
    except Exception as e:
        print(f"   ❌ 中文编码测试失败: {e}")
    
    print("✅ 编码环境设置完成")

def add_encoding_headers():
    """为 Python 文件添加编码头"""
    print("\n📝 为 Python 文件添加编码头...")
    
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    
    python_files = list(src_dir.rglob("*.py"))
    updated_files = []
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否已有编码声明
            lines = content.split('\n')
            has_encoding = False
            
            for i, line in enumerate(lines[:3]):  # 只检查前3行
                if 'coding' in line and 'utf-8' in line:
                    has_encoding = True
                    break
            
            if not has_encoding:
                # 添加编码声明
                if lines[0].startswith('#!'):
                    # 如果有 shebang，在第二行添加
                    lines.insert(1, '# -*- coding: utf-8 -*-')
                else:
                    # 否则在第一行添加
                    lines.insert(0, '# -*- coding: utf-8 -*-')
                
                new_content = '\n'.join(lines)
                
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                updated_files.append(py_file.relative_to(project_root))
        
        except Exception as e:
            print(f"   ⚠️  处理文件 {py_file} 失败: {e}")
    
    if updated_files:
        print(f"   ✅ 已更新 {len(updated_files)} 个文件:")
        for file in updated_files[:10]:  # 只显示前10个
            print(f"      • {file}")
        if len(updated_files) > 10:
            print(f"      ... 还有 {len(updated_files) - 10} 个文件")
    else:
        print("   ℹ️  所有文件都已有编码声明")

def main():
    """主函数"""
    print("🌏 中文编码问题修复工具")
    print("=" * 50)
    
    setup_chinese_encoding()
    add_encoding_headers()
    
    print("\n" + "=" * 50)
    print("🎉 编码问题修复完成！")
    print("\n💡 建议:")
    print("   1. 重新启动应用")
    print("   2. 如果问题仍然存在，请检查系统区域设置")
    print("   3. 确保终端支持 UTF-8 编码")

if __name__ == "__main__":
    main()