#!/usr/bin/env python3
"""
聊天服务测试脚本
测试集成的聊天服务功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / ".env")
except ImportError:
    pass

try:
    from oralcounsellor.services.chat import ChatService
    from oralcounsellor.core.llm.alibaba import AlibabaBailianLLM
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已正确安装项目依赖")
    sys.exit(1)


def test_chat_service():
    """测试聊天服务"""
    print("🧪 测试聊天服务...")
    
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("ALIBABA_API_KEY")
    if not api_key:
        print("   ⚠️  未设置 API 密钥，跳过测试")
        return False
    
    try:
        # 创建 LLM 实例
        llm = AlibabaBailianLLM({
            "api_key": api_key,
            "model": "qwen-plus"
        })
        
        # 创建聊天服务
        chat_service = ChatService(llm=llm)
        print("   ✅ 聊天服务创建成功")
        
        # 创建会话
        session_id = chat_service.create_session()
        print(f"   ✅ 会话创建成功: {session_id[:8]}...")
        
        # 测试文本对话
        print("   📤 发送文本消息...")
        response, _ = chat_service.chat_with_text(
            "Hello! I'm learning English. Can you help me practice?",
            session_id=session_id
        )
        print(f"   📥 收到回复: {response[:100]}...")
        print("   ✅ 文本对话测试成功")
        
        # 测试主题生成
        print("   🎯 测试主题生成...")
        topic = chat_service.generate_topic(session_id, difficulty="intermediate")
        print(f"   📝 生成的主题: {topic}")
        print("   ✅ 主题生成测试成功")
        
        # 测试对话历史
        history = chat_service.get_conversation_history(session_id)
        print(f"   📚 对话历史: {len(history)} 条消息")
        print("   ✅ 对话历史测试成功")
        
        # 测试服务状态
        status = chat_service.get_service_status()
        print(f"   📊 服务状态: LLM可用={status['llm_available']}, 活跃会话={status['active_sessions']}")
        print("   ✅ 服务状态测试成功")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 聊天服务测试失败: {e}")
        return False


def test_interactive_chat():
    """测试交互式聊天"""
    print("\n💬 测试交互式聊天...")
    
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("ALIBABA_API_KEY")
    if not api_key:
        print("   ⚠️  未设置 API 密钥，跳过测试")
        return False
    
    try:
        # 创建 LLM 实例
        llm = AlibabaBailianLLM({
            "api_key": api_key,
            "model": "qwen-plus"
        })
        
        # 创建聊天服务
        chat_service = ChatService(llm=llm)
        session_id = chat_service.create_session()
        
        # 模拟多轮对话
        conversations = [
            "Hi, I want to practice English conversation.",
            "What's your favorite hobby?",
            "I like reading books. What about you?",
            "Can you recommend some good English books for beginners?"
        ]
        
        print("   🗣️  开始多轮对话...")
        for i, message in enumerate(conversations, 1):
            print(f"\n   👤 用户 {i}: {message}")
            
            response, _ = chat_service.chat_with_text(message, session_id)
            print(f"   🤖 AI {i}: {response[:150]}...")
        
        print("\n   ✅ 交互式聊天测试成功")
        return True
        
    except Exception as e:
        print(f"   ❌ 交互式聊天测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🔧 聊天服务集成测试")
    print("=" * 50)
    
    # 检查环境变量
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("ALIBABA_API_KEY")
    if not api_key:
        print("⚠️  未设置 DASHSCOPE_API_KEY 或 ALIBABA_API_KEY 环境变量")
        return 1
    
    # 运行测试
    tests = [
        ("聊天服务", test_chat_service),
        ("交互式聊天", test_interactive_chat),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！聊天服务工作正常。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查配置。")
        return 1


if __name__ == "__main__":
    sys.exit(main())