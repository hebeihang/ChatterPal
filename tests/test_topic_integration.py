"""
主题生成器与聊天服务集成测试
"""

import pytest
from unittest.mock import Mock, patch
from chatterpal.services.chat import ChatService
from chatterpal.services.topic_generator import TopicGenerator, TopicGenerationError
from chatterpal.core.llm.base import LLMBase


class TestTopicIntegration:
    """测试主题生成器与聊天服务的集成"""

    @pytest.fixture
    def mock_llm(self):
        """创建模拟的LLM实例"""
        llm = Mock(spec=LLMBase)
        llm.chat.return_value = "What's your favorite hobby and why do you enjoy it"
        llm.test_connection.return_value = True
        return llm

    @pytest.fixture
    def chat_service(self, mock_llm):
        """创建聊天服务实例"""
        config = {
            "topic_generation": {
                "difficulty_levels": ["beginner", "intermediate", "advanced"],
                "categories": ["daily", "hobby", "travel", "work"],
                "max_retries": 3
            }
        }
        return ChatService(llm=mock_llm, config=config)

    def test_topic_generator_initialization(self, chat_service):
        """测试主题生成器初始化"""
        assert chat_service.topic_generator is not None
        assert isinstance(chat_service.topic_generator, TopicGenerator)

    def test_generate_random_topic(self, chat_service):
        """测试生成随机主题"""
        topic = chat_service.generate_topic()
        assert isinstance(topic, str)
        assert len(topic) > 0
        assert topic.endswith('') or any(word in topic.lower() for word in ['tell me', 'describe'])

    def test_generate_topic_with_difficulty(self, chat_service):
        """测试指定难度级别生成主题"""
        # 测试初级主题
        beginner_topic = chat_service.generate_topic(difficulty="beginner")
        assert isinstance(beginner_topic, str)
        assert len(beginner_topic) > 0

        # 测试高级主题
        advanced_topic = chat_service.generate_topic(difficulty="advanced")
        assert isinstance(advanced_topic, str)
        assert len(advanced_topic) > 0

    def test_generate_topic_with_category(self, chat_service):
        """测试指定分类生成主题"""
        hobby_topic = chat_service.generate_topic(category="hobby")
        assert isinstance(hobby_topic, str)
        assert len(hobby_topic) > 0

    def test_generate_contextual_topic(self, chat_service, mock_llm):
        """测试基于上下文生成主题"""
        # 创建会话并添加一些对话历
        session_id = chat_service.create_session()
        chat_service.chat_with_text("I love playing guitar", session_id)
        chat_service.chat_with_text("That's great! Music is wonderful.", session_id)

        # 生成上下文相关主
        topic = chat_service.generate_topic(session_id=session_id)
        assert isinstance(topic, str)
        assert len(topic) > 0

        # 验证LLM被调用用于生成上下文相关主题
        assert mock_llm.chat.called

    def test_set_topic_for_session(self, chat_service):
        """测试为会话设置主题"""
        session_id = chat_service.create_session()
        topic = "Let's talk about your favorite movies."
        
        success = chat_service.set_topic_for_session(session_id, topic)
        assert success is True

        # 验证主题被正确设
        current_topic = chat_service.get_current_topic(session_id)
        assert current_topic == topic

    def test_get_current_topic(self, chat_service):
        """测试获取当前主题"""
        session_id = chat_service.create_session()
        
        # 初始状态下没有主题
        topic = chat_service.get_current_topic(session_id)
        assert topic is None

        # 生成主题后应该有主题
        chat_service.generate_topic(session_id=session_id)
        topic = chat_service.get_current_topic(session_id)
        assert topic is not None

    def test_clear_context_removes_topic(self, chat_service):
        """测试清除上下文时移除主题"""
        session_id = chat_service.create_session()
        
        # 设置主题
        chat_service.generate_topic(session_id=session_id)
        assert chat_service.get_current_topic(session_id) is not None

        # 清除上下
        chat_service.clear_context(session_id)
        
        # 主题应该被清
        assert chat_service.get_current_topic(session_id) is None

    def test_get_topic_suggestions(self, chat_service):
        """测试获取主题建议"""
        suggestions = chat_service.get_topic_suggestions(count=3)
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 3
        
        for suggestion in suggestions:
            assert isinstance(suggestion, str)
            assert len(suggestion) > 0

    def test_add_custom_topic(self, chat_service):
        """测试添加自定义主题"""
        custom_topic = "What's your opinion on artificial intelligence"
        success = chat_service.add_custom_topic(custom_topic, "tech")
        assert success is True

        # 验证自定义主题可以被获取
        tech_topics = chat_service.topic_generator.get_topics_by_category("tech")
        assert custom_topic in tech_topics

    def test_get_topic_statistics(self, chat_service):
        """测试获取主题统计信息"""
        stats = chat_service.get_topic_statistics()
        assert isinstance(stats, dict)
        assert "total_topics" in stats
        assert "topics_by_difficulty" in stats
        assert "topics_by_category" in stats

    def test_process_chat_with_topic_context(self, chat_service):
        """测试带主题上下文的聊天处理"""
        session_id = chat_service.create_session()
        topic = "Tell me about your favorite book."
        
        # 使用主题上下文处理聊
        result = chat_service.process_chat(
            text_input="I love reading science fiction novels.",
            session_id=session_id,
            topic_context=topic
        )
        
        # 验证返回格式
        audio_output, chat_history = result
        assert isinstance(audio_output, tuple)
        assert isinstance(chat_history, list)
        
        # 验证主题被设
        current_topic = chat_service.get_current_topic(session_id)
        assert current_topic == topic

    def test_topic_generation_error_handling(self, chat_service, mock_llm):
        """测试主题生成错误处理"""
        # 模拟LLM调用失败
        mock_llm.chat.side_effect = Exception("LLM调用失败")
        
        # 应该回退到默认主
        topic = chat_service.generate_topic()
        assert isinstance(topic, str)
        assert len(topic) > 0

    def test_service_status_includes_topic_generator(self, chat_service):
        """测试服务状态包含主题生成器信息"""
        status = chat_service.get_service_status()
        
        assert "topic_generator_available" in status
        assert status["topic_generator_available"] is True
        assert "topic_statistics" in status
        assert isinstance(status["topic_statistics"], dict)

    def test_topic_context_enhancement(self, chat_service):
        """测试主题上下文增强功能"""
        session_id = chat_service.create_session()
        topic = "What's your favorite way to exercise"
        
        # 设置主题
        chat_service.set_topic_for_session(session_id, topic)
        
        # 进行对话(应该在早期对话中增强回复)
        result = chat_service.process_chat(
            text_input="I like walking in the park.",
            session_id=session_id
        )
        
        audio_output, chat_history = result
        assert len(chat_history) > 0
        
        # 验证回复存在
        if len(chat_history) > 0 and len(chat_history[-1]) > 1:
            response = chat_history[-1][1]
            assert isinstance(response, str)
            assert len(response) > 0

    def test_invalid_session_handling(self, chat_service):
        """测试无效会话处理"""
        # 测试不存在的会话ID
        topic = chat_service.get_current_topic("nonexistent_session")
        assert topic is None
        
        success = chat_service.set_topic_for_session("nonexistent_session", "test topic")
        assert success is False

    def test_topic_generator_fallback_without_llm(self):
        """测试没有LLM时的主题生成器回退机制"""
        # 创建没有LLM的聊天服
        chat_service = ChatService()
        
        # 应该仍然能够生成主题(使用默认主题)
        topic = chat_service.generate_topic()
        assert isinstance(topic, str)
        assert len(topic) > 0

    @pytest.mark.parametrize("difficulty", ["beginner", "intermediate", "advanced"])
    def test_topic_generation_all_difficulties(self, chat_service, difficulty):
        """测试所有难度级别的主题生成"""
        topic = chat_service.generate_topic(difficulty=difficulty)
        assert isinstance(topic, str)
        assert len(topic) > 0

    @pytest.mark.parametrize("category", ["daily", "hobby", "travel", "work"])
    def test_topic_generation_all_categories(self, chat_service, category):
        """测试所有分类的主题生成"""
        topic = chat_service.generate_topic(category=category)
        assert isinstance(topic, str)
        assert len(topic) > 0








