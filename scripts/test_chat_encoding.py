#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试聊天编码问题的脚本
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

try:
    from oralcounsellor.config.loader import create_llm
    from oralcounsellor.config.settings import get_settings
    from oralcounsellor.services.chat import ChatService
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)

def test_chinese_chat():
    """测试中文对话"""
    print("🧪 测试中文对话编码...")
    
    try:
        # 获取设置
        settings = get_settings()
        print(f"✅ 配置加载成功，LLM提供商: {settings.llm_provider}")
        
        # 创建LLM实例
        llm = create_llm(settings)
        print(f"✅ LLM实例创建成功: {type(llm).__name__}")
        
        # 创建聊天服务
        chat_service = ChatService(llm=llm)
        print("✅ 聊天服务创建成功")
        
        # 测试中文对话
        test_messages = [
            "你好",
            "请介绍一下自己",
            "What is your name?",
            "你能说中文吗？",
            "Hello, how are you today? 今天天气怎么样？"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n🔤 测试消息 {i}: {message}")
            
            try:
                response, session_id = chat_service.chat_with_text(message)
                print(f"   ✅ 回复成功: {response[:100]}...")
                print(f"   📝 会话ID: {session_id}")
            except Exception as e:
                print(f"   ❌ 对话失败: {e}")
                return False
        
        print("\n🎉 所有中文对话测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🌏 中文对话编码测试")
    print("=" * 50)
    
    success = test_chinese_chat()
    
    if success:
        print("\n✅ 编码问题已修复，聊天功能正常！")
        return 0
    else:
        print("\n❌ 编码问题仍然存在，需要进一步调试。")
        return 1

if __name__ == "__main__":
    sys.exit(main())