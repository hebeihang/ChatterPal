"""
主题生成错误处理功能测试
测试主题生成的错误处理和备用方案
"""

import pytest
from unittest.mock import Mock, patch

from chatterpal.services.topic_generator import TopicGenerator
from chatterpal.services.chat import ChatService
from chatterpal.core.errors import error_handler, TopicGenerationError


class MockLLMForTopic:
    """用于主题生成测试的模拟LLM"""
    
    def __init__(self):
        self.should_fail = False
        self.fail_count = 0
        self.call_count = 0
        self.return_invalid_topic = False
    
    def chat(self, messages, **kwargs):
        self.call_count += 1
        
        if self.should_fail:
            if self.fail_count > 0:
                self.fail_count -= 1
                raise Exception(f"LLM服务错误 (调用 {self.call_count})")
        
        if self.return_invalid_topic:
            return "Invalid topic without question mark"
        
        return "What's your favorite hobby and why do you enjoy it"


class TestTopicGeneratorErrorHandling:
    """测试主题生成器错误处""
    
    def setup_method(self):
        """设置测试环境"""
        self.llm = MockLLMForTopic()
        self.topic_generator = TopicGenerator(llm=self.llm)
    
    def test_generate_random_topic_success(self):
        """测试成功生成随机主题"""
        topic = self.topic_generator.generate_random_topic("intermediate")
        assert isinstance(topic, str)
        assert len(topic) > 0
        assert "" in topic or any(word in topic.lower() for word in ['tell me', 'describe', 'explain'])
    
    def test_generate_random_topic_invalid_difficulty(self):
        """测试无效难度级别的处""
        # 无效难度应该回退到默认
        topic = self.topic_generator.generate_random_topic("invalid_difficulty")
        assert isinstance(topic, str)
        assert len(topic) > 0
    
    def test_generate_random_topic_with_fallback_success(self):
        """测试带备用方案的随机主题生成"""
        topic = self.topic_generator.generate_random_topic_with_fallback("intermediate")
        assert isinstance(topic, str)
        assert len(topic) > 0
    
    def test_generate_random_topic_with_fallback_error(self):
        """测试备用方案在错误情况下的工""
        # 模拟内部错误
        with patch.object(self.topic_generator, 'generate_random_topic', side_effect=Exception("Internal error")):
            topic = self.topic_generator.generate_random_topic_with_fallback("intermediate")
            assert isinstance(topic, str)
            assert len(topic) > 0
            # 应该是备用主题之一
            fallback_topics = [
                "What's something interesting that happened to you recently",
                "Tell me about your favorite hobby.",
                "What's your favorite season and why",
                "Describe a place you'd love to visit.",
                "What's something you're proud of"
            ]
            assert topic in fallback_topics
    
    def test_generate_contextual_topic_no_llm(self):
        """测试没有LLM时的上下文主题生""
        topic_generator_no_llm = TopicGenerator(llm=None)
        
        chat_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        topic = topic_generator_no_llm.generate_contextual_topic(chat_history)
        assert isinstance(topic, str)
        assert len(topic) > 0
    
    def test_generate_contextual_topic_empty_history(self):
        """测试空对话历史的处理"""
        topic = self.topic_generator.generate_contextual_topic([])
        assert isinstance(topic, str)
        assert len(topic) > 0
    
    def test_generate_contextual_topic_insufficient_history(self):
        """测试对话历史不足的处""
        short_history = [{"role": "user", "content": "Hi"}]
        topic = self.topic_generator.generate_contextual_topic(short_history)
        assert isinstance(topic, str)
        assert len(topic) > 0
    
    def test_generate_contextual_topic_llm_failure(self):
        """测试LLM失败时的处理"""
        self.llm.should_fail = True
        self.llm.fail_count = 10  # 确保所有重试都失败
        
        chat_history = [
            {"role": "user", "content": "I love reading books"},
            {"role": "assistant", "content": "That's great! What genres do you enjoy"}
        ]
        
        topic = self.topic_generator.generate_contextual_topic(chat_history)
        assert isinstance(topic, str)
        assert len(topic) > 0
        # 应该回退到随机主
    
    def test_generate_contextual_topic_retry_mechanism(self):
        """测试重试机制"""
        # 设置前两次失败,第三次成
        self.llm.should_fail = True
        self.llm.fail_count = 2
        
        chat_history = [
            {"role": "user", "content": "I enjoy cooking"},
            {"role": "assistant", "content": "Cooking is wonderful! What's your favorite dish to make"}
        ]
        
        topic = self.topic_generator.generate_contextual_topic(chat_history)
        assert isinstance(topic, str)
        assert len(topic) > 0
        assert self.llm.call_count == 3  # 验证重试
    
    def test_generate_contextual_topic_invalid_response(self):
        """测试LLM返回无效主题的处""
        self.llm.return_invalid_topic = True
        
        chat_history = [
            {"role": "user", "content": "I like sports"},
            {"role": "assistant", "content": "Sports are great for staying healthy!"}
        ]
        
        topic = self.topic_generator.generate_contextual_topic(chat_history)
        assert isinstance(topic, str)
        assert len(topic) > 0
        # 应该回退到随机主题,因为LLM返回的主题无
    
    def test_validate_topic(self):
        """测试主题验证功能"""
        # 有效主题
        assert self.topic_generator._validate_topic("What's your favorite color")
        assert self.topic_generator._validate_topic("Tell me about your hobbies.")
        assert self.topic_generator._validate_topic("Describe your ideal vacation.")
        
        # 无效主题
        assert not self.topic_generator._validate_topic("")  # 空字符串
        assert not self.topic_generator._validate_topic(None)  # None
        assert not self.topic_generator._validate_topic("Hi")  # 太短
        assert not self.topic_generator._validate_topic("a" * 300)  # 太长
        assert not self.topic_generator._validate_topic("This is not a question")  # 不是问题
        assert not self.topic_generator._validate_topic("What do you think about politics")  # 包含敏感
    
    def test_add_custom_topic(self):
        """测试添加自定义主""
        # 添加有效主题
        success = self.topic_generator.add_custom_topic(
            "What's your favorite programming language", 
            "technology", 
            "intermediate"
        )
        assert success is True
        
        # 验证主题被添
        topics = self.topic_generator.get_topics_by_category("technology", "intermediate")
        assert "What's your favorite programming language" in topics
        
        # 添加无效主题
        success = self.topic_generator.add_custom_topic("", "category", "difficulty")
        assert success is False
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        stats = self.topic_generator.get_statistics()
        
        assert isinstance(stats, dict)
        assert "total_topics" in stats
        assert "topics_by_difficulty" in stats
        assert "topics_by_category" in stats
        assert "available_difficulties" in stats
        assert "available_categories" in stats
        
        assert stats["total_topics"] > 0
        assert len(stats["available_difficulties"]) > 0
        assert len(stats["available_categories"]) > 0


class TestChatServiceTopicIntegration:
    """测试ChatService与主题生成的集成"""
    
    def setup_method(self):
        """设置测试环境"""
        self.llm = MockLLMForTopic()
        self.chat_service = ChatService(llm=self.llm)
    
    def test_generate_topic_success(self):
        """测试成功生成主题"""
        topic = self.chat_service.generate_topic(difficulty="intermediate")
        assert isinstance(topic, str)
        assert len(topic) > 0
    
    def test_generate_topic_with_session(self):
        """测试为会话生成主""
        # 创建会话并添加一些对话历
        session_id = self.chat_service.create_session()
        self.chat_service.chat_with_text("I love traveling", session_id)
        
        # 生成上下文相关主
        topic = self.chat_service.generate_topic(session_id, difficulty="intermediate")
        assert isinstance(topic, str)
        assert len(topic) > 0
        
        # 验证主题被保存到会话元数
        session = self.chat_service.get_session(session_id)
        assert session.get_metadata("current_topic") == topic
    
    def test_generate_topic_llm_failure(self):
        """测试LLM失败时的主题生成"""
        self.llm.should_fail = True
        self.llm.fail_count = 10
        
        # 即使LLM失败,也应该返回备用主题
        topic = self.chat_service.generate_topic(difficulty="intermediate")
        assert isinstance(topic, str)
        assert len(topic) > 0
    
    def test_get_topic_suggestions(self):
        """测试获取主题建议"""
        suggestions = self.chat_service.get_topic_suggestions(
            difficulty="intermediate", 
            count=3
        )
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 3
        for suggestion in suggestions:
            assert isinstance(suggestion, str)
            assert len(suggestion) > 0
    
    def test_get_topic_suggestions_by_category(self):
        """测试按分类获取主题建""
        suggestions = self.chat_service.get_topic_suggestions(
            difficulty="intermediate",
            category="daily",
            count=2
        )
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 2
    
    def test_add_custom_topic_integration(self):
        """测试添加自定义主题的集成"""
        success = self.chat_service.add_custom_topic(
            "What's your favorite coding framework",
            "technology",
            "advanced"
        )
        assert success is True
    
    def test_get_topic_statistics_integration(self):
        """测试获取主题统计信息的集""
        stats = self.chat_service.get_topic_statistics()
        assert isinstance(stats, dict)
        assert "total_topics" in stats
    
    def test_set_topic_for_session(self):
        """测试为会话设置主""
        session_id = self.chat_service.create_session()
        
        success = self.chat_service.set_topic_for_session(
            session_id, 
            "Let's talk about your hobbies"
        )
        assert success is True
        
        # 验证主题被设
        current_topic = self.chat_service.get_current_topic(session_id)
        assert current_topic == "Let's talk about your hobbies"
    
    def test_get_current_topic(self):
        """测试获取当前主题"""
        session_id = self.chat_service.create_session()
        
        # 初始时没有主
        topic = self.chat_service.get_current_topic(session_id)
        assert topic is None
        
        # 生成主题后应该有主题
        generated_topic = self.chat_service.generate_topic(session_id)
        current_topic = self.chat_service.get_current_topic(session_id)
        assert current_topic == generated_topic
    
    def test_clear_context_with_topic(self):
        """测试清除上下文时也清除主""
        session_id = self.chat_service.create_session()
        
        # 设置主题
        self.chat_service.generate_topic(session_id)
        assert self.chat_service.get_current_topic(session_id) is not None
        
        # 清除上下
        success = self.chat_service.clear_context(session_id)
        assert success is True
        
        # 主题应该被清
        assert self.chat_service.get_current_topic(session_id) is None


class TestTopicErrorRecovery:
    """测试主题生成的错误恢复机""
    
    def setup_method(self):
        """设置测试环境"""
        self.llm = MockLLMForTopic()
        self.chat_service = ChatService(llm=self.llm)
    
    def test_topic_generation_graceful_degradation(self):
        """测试主题生成的优雅降""
        # 模拟各种错误情况
        error_scenarios = [
            {"should_fail": True, "fail_count": 10},  # 完全失败
            {"return_invalid_topic": True},  # 返回无效主题
        ]
        
        for scenario in error_scenarios:
            # 重置LLM状
            self.llm.should_fail = scenario.get("should_fail", False)
            self.llm.fail_count = scenario.get("fail_count", 0)
            self.llm.return_invalid_topic = scenario.get("return_invalid_topic", False)
            self.llm.call_count = 0
            
            # 生成主题应该总是成功(通过备用方案
            topic = self.chat_service.generate_topic()
            assert isinstance(topic, str)
            assert len(topic) > 0
    
    def test_contextual_topic_fallback_chain(self):
        """测试上下文主题的备用""
        session_id = self.chat_service.create_session()
        
        # 添加对话历史
        self.chat_service.chat_with_text("I enjoy reading science fiction books", session_id)
        
        # 模拟LLM完全失败
        self.llm.should_fail = True
        self.llm.fail_count = 10
        
        # 应该回退到随机主
        topic = self.chat_service.generate_topic(session_id)
        assert isinstance(topic, str)
        assert len(topic) > 0
    
    @patch('chatterpal.core.errors.error_handler.log_error')
    def test_error_logging_in_topic_generation(self, mock_log_error):
        """测试主题生成中的错误日志记录"""
        # 模拟错误
        self.llm.should_fail = True
        self.llm.fail_count = 5
        
        chat_history = [
            {"role": "user", "content": "I like music"},
            {"role": "assistant", "content": "Music is wonderful!"}
        ]
        
        # 生成主题(应该会记录错误但仍然返回结果)
        topic = self.chat_service.topic_generator.generate_contextual_topic(chat_history)
        assert isinstance(topic, str)
        assert len(topic) > 0
        
        # 验证错误被记
        assert mock_log_error.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])








