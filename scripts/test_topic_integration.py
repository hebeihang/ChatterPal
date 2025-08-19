#!/usr/bin/env python3
"""
主题生成器集成演示脚本
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from oralcounsellor.services import ChatService, TopicGenerator
from unittest.mock import Mock


def test_topic_integration():
    """测试主题生成器与聊天服务的集成"""
    print("=== 主题生成器集成测试 ===\n")
    
    # 创建模拟的LLM
    mock_llm = Mock()
    mock_llm.chat.return_value = "What's your favorite way to spend time with friends?"
    mock_llm.test_connection.return_value = True
    
    # 创建聊天服务
    config = {
        "topic_generation": {
            "difficulty_levels": ["beginner", "intermediate", "advanced"],
            "categories": ["daily", "hobby", "travel", "work", "tech", "culture"],
            "max_retries": 3
        }
    }
    
    chat_service = ChatService(llm=mock_llm, config=config)
    
    print("1. 测试主题生成器初始化")
    print(f"   主题生成器可用: {chat_service.topic_generator is not None}")
    print(f"   主题生成器类型: {type(chat_service.topic_generator).__name__}")
    
    print("\n2. 测试随机主题生成")
    for difficulty in ["beginner", "intermediate", "advanced"]:
        topic = chat_service.generate_topic(difficulty=difficulty)
        print(f"   {difficulty.capitalize()}: {topic}")
    
    print("\n3. 测试分类主题生成")
    for category in ["daily", "hobby", "travel", "work"]:
        topic = chat_service.generate_topic(category=category)
        print(f"   {category.capitalize()}: {topic}")
    
    print("\n4. 测试会话主题管理")
    session_id = chat_service.create_session()
    print(f"   创建会话: {session_id}")
    
    # 生成主题
    topic = chat_service.generate_topic(session_id=session_id)
    print(f"   生成主题: {topic}")
    
    # 获取当前主题
    current_topic = chat_service.get_current_topic(session_id)
    print(f"   当前主题: {current_topic}")
    
    # 设置自定义主题
    custom_topic = "Let's discuss your favorite books and why you enjoy reading them."
    success = chat_service.set_topic_for_session(session_id, custom_topic)
    print(f"   设置自定义主题: {success}")
    print(f"   新的当前主题: {chat_service.get_current_topic(session_id)}")
    
    print("\n5. 测试上下文相关主题生成")
    # 添加一些对话历史
    chat_service.chat_with_text("I love reading science fiction novels", session_id)
    chat_service.chat_with_text("That's fascinating! Science fiction opens up so many possibilities.", session_id)
    
    # 生成上下文相关主题
    contextual_topic = chat_service.generate_topic(session_id=session_id)
    print(f"   上下文相关主题: {contextual_topic}")
    
    print("\n6. 测试主题建议")
    suggestions = chat_service.get_topic_suggestions(count=3)
    print("   主题建议:")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"     {i}. {suggestion}")
    
    print("\n7. 测试自定义主题添加")
    custom_topic_text = "What's your opinion on the future of renewable energy?"
    success = chat_service.add_custom_topic(custom_topic_text, "tech", "advanced")
    print(f"   添加自定义主题: {success}")
    
    print("\n8. 测试主题统计信息")
    stats = chat_service.get_topic_statistics()
    print(f"   总主题数: {stats.get('total_topics', 0)}")
    print(f"   可用难度级别: {stats.get('available_difficulties', [])}")
    print(f"   可用分类: {stats.get('available_categories', [])}")
    
    print("\n9. 测试服务状态")
    status = chat_service.get_service_status()
    print(f"   主题生成器可用: {status.get('topic_generator_available', False)}")
    print(f"   活跃会话数: {status.get('active_sessions', 0)}")
    
    print("\n10. 测试上下文清除")
    print(f"    清除前主题: {chat_service.get_current_topic(session_id)}")
    chat_service.clear_context(session_id)
    print(f"    清除后主题: {chat_service.get_current_topic(session_id)}")
    
    print("\n=== 集成测试完成 ===")


def test_topic_generator_standalone():
    """测试独立的主题生成器"""
    print("\n=== 独立主题生成器测试 ===\n")
    
    # 创建模拟的LLM
    mock_llm = Mock()
    mock_llm.chat.return_value = "How do you think technology will change education in the future?"
    
    # 创建主题生成器
    config = {
        "difficulty_levels": ["beginner", "intermediate", "advanced"],
        "categories": ["daily", "hobby", "travel", "work", "tech", "culture"],
        "max_retries": 3
    }
    
    topic_generator = TopicGenerator(llm=mock_llm, config=config)
    
    print("1. 测试随机主题生成")
    random_topic = topic_generator.generate_random_topic()
    print(f"   随机主题: {random_topic}")
    
    print("\n2. 测试分类主题获取")
    categories = topic_generator.get_topic_categories("intermediate")
    print(f"   中级分类: {categories}")
    
    for category in categories[:3]:  # 只显示前3个分类
        topics = topic_generator.get_topics_by_category(category, "intermediate")
        print(f"   {category} 主题数量: {len(topics)}")
        if topics:
            print(f"   示例: {topics[0]}")
    
    print("\n3. 测试上下文主题生成")
    chat_history = [
        {"role": "user", "content": "I enjoy playing basketball with my friends"},
        {"role": "assistant", "content": "That sounds like great exercise and fun!"},
        {"role": "user", "content": "Yes, it helps me stay fit and socialize"},
        {"role": "assistant", "content": "Sports are wonderful for both physical and social benefits."}
    ]
    
    contextual_topic = topic_generator.generate_contextual_topic(chat_history)
    print(f"   上下文主题: {contextual_topic}")
    
    print("\n4. 测试统计信息")
    stats = topic_generator.get_statistics()
    print(f"   总主题数: {stats['total_topics']}")
    print("   按难度分布:")
    for difficulty, data in stats['topics_by_difficulty'].items():
        if isinstance(data, dict) and 'total' in data:
            print(f"     {difficulty}: {data['total']} 个主题")
    
    print("\n=== 独立测试完成 ===")


if __name__ == "__main__":
    try:
        test_topic_integration()
        test_topic_generator_standalone()
        print("\n✅ 所有测试通过！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)