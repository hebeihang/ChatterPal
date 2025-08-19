#!/usr/bin/env python3
"""
测试新的AI教练提示词效果
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from oralcounsellor.config.settings import get_settings
from oralcounsellor.services.chat import ChatService
from oralcounsellor.core.llm.alibaba import AlibabaDashScopeLLM


def test_conversation():
    """测试对话效果"""
    print("🎯 OralCounsellor AI教练提示词测试")
    print("=" * 50)
    
    # 初始化
    settings = get_settings()
    llm = AlibabaDashScopeLLM({
        'api_key': settings.alibaba_api_key,
        'model': settings.alibaba_model
    })
    
    chat_service = ChatService(llm=llm)
    
    # 测试对话场景
    test_messages = [
        "Hello! I want to practice English.",
        "I'm learning English for my job. Can you help me?",
        "I sometimes make mistake when I speak. How can I improve?",
        "What topics should we talk about today?"
    ]
    
    session_id = None
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n👤 用户 {i}: {message}")
        
        try:
            response, session_id = chat_service.chat_with_text(message, session_id)
            print(f"🤖 Alex教练: {response}")
            
        except Exception as e:
            print(f"❌ 错误: {e}")
            break
        
        print("-" * 50)
    
    print("\n✅ 测试完成！")
    print("💡 提示：现在启动Web应用体验完整的Alex教练对话功能")


if __name__ == "__main__":
    test_conversation()