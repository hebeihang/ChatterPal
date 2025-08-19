#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试编码问题的脚本
"""

import os
import sys
from pathlib import Path

# 设置编码环境
os.environ['PYTHONIOENCODING'] = 'utf-8'
if os.name == 'nt':
    os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '1'

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def debug_api_key():
    """调试API密钥"""
    print("🔍 调试API密钥...")
    
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if api_key:
        print(f"   API密钥长度: {len(api_key)}")
        print(f"   API密钥前10位: {api_key[:10]}")
        print(f"   API密钥类型: {type(api_key)}")
        
        # 检查是否包含非ASCII字符
        try:
            api_key.encode('ascii')
            print("   ✅ API密钥只包含ASCII字符")
        except UnicodeEncodeError as e:
            print(f"   ❌ API密钥包含非ASCII字符: {e}")
            print(f"   问题位置: {e.start}-{e.end}")
            print(f"   问题字符: {repr(api_key[e.start:e.end])}")
    else:
        print("   ❌ 未找到API密钥")

def debug_openai_client():
    """调试OpenAI客户端初始化"""
    print("\n🔍 调试OpenAI客户端初始化...")
    
    try:
        from openai import OpenAI
        
        api_key = os.getenv("DASHSCOPE_API_KEY")
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        print(f"   API密钥: {api_key[:10] if api_key else 'None'}...")
        print(f"   Base URL: {base_url}")
        
        # 尝试创建客户端
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=60
        )
        print("   ✅ OpenAI客户端创建成功")
        
        # 尝试简单的API调用
        print("   🧪 测试API调用...")
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"}
        ]
        
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=messages,
            max_tokens=100
        )
        
        if response.choices:
            content = response.choices[0].message.content
            print(f"   ✅ API调用成功: {content[:50]}...")
        else:
            print("   ❌ API调用返回空结果")
            
    except Exception as e:
        print(f"   ❌ OpenAI客户端测试失败: {e}")
        print(f"   错误类型: {type(e)}")
        
        # 检查是否是编码错误
        error_str = str(e)
        try:
            error_str.encode('ascii')
            print("   错误信息只包含ASCII字符")
        except UnicodeEncodeError as enc_e:
            print(f"   ❌ 错误信息包含非ASCII字符: {enc_e}")
            print(f"   问题位置: {enc_e.start}-{enc_e.end}")
            print(f"   问题字符: {repr(error_str[enc_e.start:enc_e.end])}")

def debug_system_prompt():
    """调试系统提示词"""
    print("\n🔍 调试系统提示词...")
    
    try:
        from oralcounsellor.config.settings import get_settings
        settings = get_settings()
        
        system_prompt = settings.system_prompt
        if system_prompt:
            print(f"   系统提示词长度: {len(system_prompt)}")
            print(f"   系统提示词前100字符: {system_prompt[:100]}")
            
            # 检查第46-50个字符
            if len(system_prompt) > 50:
                problem_chars = system_prompt[45:51]  # 第46-50个字符（0索引）
                print(f"   第46-50个字符: {repr(problem_chars)}")
                
                try:
                    problem_chars.encode('ascii')
                    print("   ✅ 问题字符区域只包含ASCII字符")
                except UnicodeEncodeError as e:
                    print(f"   ❌ 问题字符区域包含非ASCII字符: {e}")
                    print(f"   具体字符: {repr(problem_chars[e.start:e.end])}")
        else:
            print("   ℹ️  未设置自定义系统提示词")
            
    except Exception as e:
        print(f"   ❌ 系统提示词检查失败: {e}")

def debug_default_prompt():
    """调试默认提示词"""
    print("\n🔍 调试默认提示词...")
    
    try:
        from oralcounsellor.core.llm.base import LLMBase
        
        # 检查基类中的默认提示词
        if hasattr(LLMBase, 'DEFAULT_SYSTEM_PROMPT'):
            prompt = LLMBase.DEFAULT_SYSTEM_PROMPT
            print(f"   默认提示词长度: {len(prompt)}")
            
            # 检查第46-50个字符
            if len(prompt) > 50:
                problem_chars = prompt[45:51]
                print(f"   第46-50个字符: {repr(problem_chars)}")
                
                try:
                    problem_chars.encode('ascii')
                    print("   ✅ 默认提示词问题区域只包含ASCII字符")
                except UnicodeEncodeError as e:
                    print(f"   ❌ 默认提示词包含非ASCII字符: {e}")
                    print(f"   具体字符: {repr(problem_chars[e.start:e.end])}")
        else:
            print("   ℹ️  未找到默认系统提示词")
            
    except Exception as e:
        print(f"   ❌ 默认提示词检查失败: {e}")

def main():
    """主函数"""
    print("🐛 编码问题深度调试")
    print("=" * 50)
    
    debug_api_key()
    debug_openai_client()
    debug_system_prompt()
    debug_default_prompt()
    
    print("\n" + "=" * 50)
    print("🔍 调试完成")
    print("💡 请检查上述输出，找出包含非ASCII字符的具体位置")

if __name__ == "__main__":
    main()