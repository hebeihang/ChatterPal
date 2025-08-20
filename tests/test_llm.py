"""
Tests for LLM (Large Language Model) modules.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from chatterpal.core.llm.base import (
    LLMBase, LLMError, Message, Conversation
)
from chatterpal.core.llm.alibaba import AlibabaDashScopeLLM
from chatterpal.core.llm.openai import OpenAILLM


class MockLLM(LLMBase):
    """Mock LLM implementation for testing base class functionality."""
    
    def __init__(self, config=None, should_fail=False):
        super().__init__(config)
        self.should_fail = should_fail
        self.chat_calls = []
        
    def chat(self, messages, **kwargs):
        self.chat_calls.append((messages, kwargs))
        if self.should_fail:
            raise LLMError("Mock LLM failure")
        return "Mock response"


class TestMessage:
    """Test the Message class."""
    
    def test_initialization(self):
        """Test Message initialization."""
        msg = Message("user", "Hello world")
        assert msg.role == "user"
        assert msg.content == "Hello world"
        assert msg.metadata == {}
        
        msg_with_metadata = Message("assistant", "Hi there", timestamp=123456)
        assert msg_with_metadata.metadata == {"timestamp": 123456}
    
    def test_to_dict(self):
        """Test Message to_dict conversion."""
        msg = Message("user", "Hello", timestamp=123456)
        result = msg.to_dict()
        
        expected = {
            "role": "user",
            "content": "Hello",
            "timestamp": 123456
        }
        assert result == expected
    
    def test_from_dict(self):
        """Test Message from_dict creation."""
        data = {
            "role": "assistant",
            "content": "Hi there",
            "timestamp": 123456
        }
        msg = Message.from_dict(data)
        
        assert msg.role == "assistant"
        assert msg.content == "Hi there"
        assert msg.metadata == {"timestamp": 123456}
    
    def test_from_dict_minimal(self):
        """Test Message from_dict with minimal data."""
        data = {"role": "user", "content": "Hello"}
        msg = Message.from_dict(data)
        
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.metadata == {}
    
    def test_from_dict_missing_fields(self):
        """Test Message from_dict with missing fields."""
        data = {"content": "Hello"}
        msg = Message.from_dict(data)
        
        assert msg.role == "user"  # Default role
        assert msg.content == "Hello"
    
    def test_str_representation(self):
        """Test Message string representation."""
        msg = Message("user", "Hello world")
        assert str(msg) == "user: Hello world"


class TestConversation:
    """Test the Conversation class."""
    
    def test_initialization_empty(self):
        """Test Conversation initialization without system prompt."""
        conv = Conversation()
        assert len(conv) == 0
        assert conv.messages == []
    
    def test_initialization_with_system_prompt(self):
        """Test Conversation initialization with system prompt."""
        conv = Conversation("You are a helpful assistant.")
        assert len(conv) == 1
        assert conv.messages[0].role == "system"
        assert conv.messages[0].content == "You are a helpful assistant."
    
    def test_add_message(self):
        """Test adding messages to conversation."""
        conv = Conversation()
        
        conv.add_message("user", "Hello")
        assert len(conv) == 1
        assert conv.messages[0].role == "user"
        assert conv.messages[0].content == "Hello"
    
    def test_add_user_message(self):
        """Test adding user message."""
        conv = Conversation()
        conv.add_user_message("Hello world")
        
        assert len(conv) == 1
        assert conv.messages[0].role == "user"
        assert conv.messages[0].content == "Hello world"
    
    def test_add_assistant_message(self):
        """Test adding assistant message."""
        conv = Conversation()
        conv.add_assistant_message("Hi there!")
        
        assert len(conv) == 1
        assert conv.messages[0].role == "assistant"
        assert conv.messages[0].content == "Hi there!"
    
    def test_add_system_message(self):
        """Test adding system message."""
        conv = Conversation()
        conv.add_system_message("You are helpful.")
        
        assert len(conv) == 1
        assert conv.messages[0].role == "system"
        assert conv.messages[0].content == "You are helpful."
    
    def test_get_messages_no_limit(self):
        """Test getting all messages without limit."""
        conv = Conversation()
        conv.add_user_message("Hello")
        conv.add_assistant_message("Hi")
        conv.add_user_message("How are you")
        
        messages = conv.get_messages()
        assert len(messages) == 3
        assert all(isinstance(msg, dict) for msg in messages)
    
    def test_get_messages_with_limit(self):
        """Test getting messages with limit."""
        conv = Conversation("System prompt")
        conv.add_user_message("Hello")
        conv.add_assistant_message("Hi")
        conv.add_user_message("How are you")
        conv.add_assistant_message("I'm good")
        
        # Should keep system message + 2 most recent messages
        messages = conv.get_messages(limit=3)
        assert len(messages) == 3
        
        # Check that system message is preserved
        system_messages = [msg for msg in messages if msg["role"] == "system"]
        assert len(system_messages) == 1
    
    def test_clear_keep_system(self):
        """Test clearing conversation while keeping system messages."""
        conv = Conversation("System prompt")
        conv.add_user_message("Hello")
        conv.add_assistant_message("Hi")
        
        conv.clear(keep_system=True)
        assert len(conv) == 1
        assert conv.messages[0].role == "system"
    
    def test_clear_all(self):
        """Test clearing all messages."""
        conv = Conversation("System prompt")
        conv.add_user_message("Hello")
        conv.add_assistant_message("Hi")
        
        conv.clear(keep_system=False)
        assert len(conv) == 0


class TestLLMBase:
    """Test the LLM base class functionality."""
    
    def test_initialization(self):
        """Test LLM base class initialization."""
        llm = MockLLM()
        assert llm.config == {}
        assert llm.logger is not None
        
        config = {"model": "test", "temperature": 0.7}
        llm_with_config = MockLLM(config)
        assert llm_with_config.config == config
    
    def test_normalize_messages_string(self):
        """Test normalizing string input to messages."""
        llm = MockLLM()
        
        result = llm.normalize_messages("Hello world")
        expected = [{"role": "user", "content": "Hello world"}]
        assert result == expected
    
    def test_normalize_messages_conversation(self):
        """Test normalizing Conversation object to messages."""
        llm = MockLLM()
        
        conv = Conversation()
        conv.add_user_message("Hello")
        conv.add_assistant_message("Hi")
        
        result = llm.normalize_messages(conv)
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"
    
    def test_normalize_messages_list(self):
        """Test normalizing message list."""
        llm = MockLLM()
        
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"}
        ]
        
        result = llm.normalize_messages(messages)
        assert result == messages
    
    def test_normalize_messages_invalid(self):
        """Test normalizing invalid input."""
        llm = MockLLM()
        
        with pytest.raises(LLMError):
            llm.normalize_messages(123)
    
    def test_validate_messages_valid(self):
        """Test validating valid messages."""
        llm = MockLLM()
        
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"}
        ]
        
        assert llm.validate_messages(messages) is True
    
    def test_validate_messages_empty(self):
        """Test validating empty messages."""
        llm = MockLLM()
        assert llm.validate_messages([]) is False
    
    def test_validate_messages_invalid_format(self):
        """Test validating messages with invalid format."""
        llm = MockLLM()
        
        # Non-dict message
        assert llm.validate_messages(["invalid"]) is False
        
        # Missing required fields
        assert llm.validate_messages([{"role": "user"}]) is False
        assert llm.validate_messages([{"content": "Hello"}]) is False
        
        # Non-string content
        assert llm.validate_messages([{"role": "user", "content": 123}]) is False
    
    def test_create_conversation(self):
        """Test creating conversation."""
        llm = MockLLM()
        
        conv = llm.create_conversation()
        assert isinstance(conv, Conversation)
        assert len(conv) == 0
        
        conv_with_system = llm.create_conversation("System prompt")
        assert len(conv_with_system) == 1
        assert conv_with_system.messages[0].role == "system"
    
    def test_test_connection_success(self):
        """Test successful connection test."""
        llm = MockLLM()
        assert llm.test_connection() is True
    
    def test_test_connection_failure(self):
        """Test failed connection test."""
        llm = MockLLM(should_fail=True)
        assert llm.test_connection() is False
    
    def test_get_model_info(self):
        """Test getting model information."""
        config = {"model": "test-model", "temperature": 0.7}
        llm = MockLLM(config)
        
        info = llm.get_model_info()
        assert info["provider"] == "MockLLM"
        assert info["model"] == "test-model"
        assert info["temperature"] == 0.7
        assert info["config"] == config
    
    def test_estimate_tokens(self):
        """Test token estimation."""
        llm = MockLLM()
        
        # Test empty text
        assert llm.estimate_tokens("") == 0
        
        # Test English text
        tokens = llm.estimate_tokens("Hello world")
        assert tokens > 0
        
        # Test Chinese text
        tokens = llm.estimate_tokens("你好世界")
        assert tokens > 0
        
        # Test mixed text
        tokens = llm.estimate_tokens("Hello 世界")
        assert tokens > 0
    
    def test_truncate_messages(self):
        """Test message truncation."""
        llm = MockLLM()
        
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "How are you"},
            {"role": "assistant", "content": "Good"}
        ]
        
        # Test with reasonable limit
        truncated = llm.truncate_messages(messages, max_tokens=100)
        assert len(truncated) >= 1  # At least system message
        
        # Test with very low limit
        truncated = llm.truncate_messages(messages, max_tokens=1)
        system_msgs = [msg for msg in truncated if msg["role"] == "system"]
        assert len(system_msgs) == 1
    
    def test_chat_stream_default(self):
        """Test default chat_stream implementation."""
        llm = MockLLM()
        
        result = list(llm.chat_stream("Hello"))
        assert result == ["Mock response"]
    
    def test_chat_stream_failure(self):
        """Test chat_stream failure."""
        llm = MockLLM(should_fail=True)
        
        with pytest.raises(LLMError):
            list(llm.chat_stream("Hello"))


class TestAlibabaDashScopeLLM:
    """测试阿里云DashScope LLM实现"""
    
    def test_initialization(self):
        """测试阿里云LLM初始""
        config = {
            "api_key": "test_key",
            "model": "qwen-turbo"
        }
        llm = AlibabaDashScopeLLM(config)
        assert llm.config == config
        assert llm.api_key == "test_key"
        assert llm.model == "qwen-turbo"
    
    def test_initialization_missing_api_key(self):
        """测试缺少API密钥时的初始""
        with pytest.raises(LLMError, match="阿里云API密钥未配):
            AlibabaDashScopeLLM({})
    
    @patch('requests.post')
    def test_chat_success(self, mock_post):
        """测试成功的对""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {
                "text": "你好!我可以帮助你什么?"
            }
        }
        mock_post.return_value = mock_response
        
        config = {"api_key": "test_key"}
        llm = AlibabaDashScopeLLM(config)
        
        result = llm.chat("你好")
        assert result == "你好!我可以帮助你什么?"
    
    @patch('requests.post')
    def test_chat_failure(self, mock_post):
        """测试对话失败"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "message": "API错误"
        }
        mock_post.return_value = mock_response
        
        config = {"api_key": "test_key"}
        llm = AlibabaDashScopeLLM(config)
        
        with pytest.raises(LLMError):
            llm.chat("你好")
    
    @patch('requests.post')
    def test_chat_with_conversation(self, mock_post):
        """测试使用对话对象进行对话"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {
                "text": "回复内容"
            }
        }
        mock_post.return_value = mock_response
        
        config = {"api_key": "test_key"}
        llm = AlibabaDashScopeLLM(config)
        
        conv = Conversation("你是一个有用的助手")
        conv.add_user_message("你好")
        
        result = llm.chat(conv)
        assert result == "回复内容"


class TestOpenAILLM:
    """Test the OpenAI LLM implementation."""
    
    def test_initialization(self):
        """Test OpenAI LLM initialization."""
        config = {
            "api_key": "test_key",
            "model": "gpt-3.5-turbo"
        }
        llm = OpenAILLM(config)
        assert llm.config == config
    
    def test_initialization_missing_api_key(self):
        """Test OpenAI LLM initialization with missing API key."""
        with pytest.raises(LLMError, match="缺少必要的API密钥"):
            OpenAILLM({})
    
    @patch('openai.OpenAI')
    def test_chat_success(self, mock_openai_class):
        """Test successful chat with OpenAI LLM."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Hello! How can I help"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        config = {"api_key": "test_key"}
        llm = OpenAILLM(config)
        
        result = llm.chat("Hello")
        assert result == "Hello! How can I help"
    
    @patch('openai.OpenAI')
    def test_chat_failure(self, mock_openai_class):
        """Test chat failure with OpenAI LLM."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        config = {"api_key": "test_key"}
        llm = OpenAILLM(config)
        
        with pytest.raises(LLMError):
            llm.chat("Hello")
    
    @patch('openai.OpenAI')
    def test_chat_stream_success(self, mock_openai_class):
        """Test successful streaming chat with OpenAI LLM."""
        mock_client = MagicMock()
        
        # Mock streaming response
        mock_chunk1 = MagicMock()
        mock_chunk1.choices[0].delta.content = "Hello"
        mock_chunk2 = MagicMock()
        mock_chunk2.choices[0].delta.content = " world"
        mock_chunk3 = MagicMock()
        mock_chunk3.choices[0].delta.content = None  # End of stream
        
        mock_client.chat.completions.create.return_value = [
            mock_chunk1, mock_chunk2, mock_chunk3
        ]
        mock_openai_class.return_value = mock_client
        
        config = {"api_key": "test_key"}
        llm = OpenAILLM(config)
        
        result = list(llm.chat_stream("Hello"))
        assert result == ["Hello", " world"]


if __name__ == "__main__":
    pytest.main([__file__])








