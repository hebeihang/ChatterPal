# -*- coding: utf-8 -*-
"""
LLM基类定义
定义统一的大语言模型接口
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Iterator, Union
import logging

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """大语言模型错误基类"""

    pass


class Message:
    """消息类，用于表示对话中的单条消息"""

    def __init__(self, role: str, content: str, **kwargs):
        """
        初始化消息

        Args:
            role: 消息角色 (user, assistant, system)
            content: 消息内容
            **kwargs: 其他属性
        """
        self.role = role
        self.content = content
        self.metadata = kwargs

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {"role": self.role, "content": self.content}
        result.update(self.metadata)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """从字典创建消息"""
        role = data.get("role", "user")
        content = data.get("content", "")
        metadata = {k: v for k, v in data.items() if k not in ["role", "content"]}
        return cls(role, content, **metadata)

    def __str__(self) -> str:
        return f"{self.role}: {self.content}"


class Conversation:
    """对话类，用于管理多轮对话"""

    def __init__(self, system_prompt: Optional[str] = None):
        """
        初始化对话

        Args:
            system_prompt: 系统提示词
        """
        self.messages: List[Message] = []
        if system_prompt:
            self.add_system_message(system_prompt)

    def add_message(self, role: str, content: str, **kwargs) -> None:
        """添加消息"""
        message = Message(role, content, **kwargs)
        self.messages.append(message)

    def add_user_message(self, content: str, **kwargs) -> None:
        """添加用户消息"""
        self.add_message("user", content, **kwargs)

    def add_assistant_message(self, content: str, **kwargs) -> None:
        """添加助手消息"""
        self.add_message("assistant", content, **kwargs)

    def add_system_message(self, content: str, **kwargs) -> None:
        """添加系统消息"""
        self.add_message("system", content, **kwargs)

    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取消息列表

        Args:
            limit: 限制消息数量，从最新开始

        Returns:
            消息字典列表
        """
        messages = self.messages
        if limit and len(messages) > limit:
            # 保留系统消息和最近的消息
            system_messages = [msg for msg in messages if msg.role == "system"]
            other_messages = [msg for msg in messages if msg.role != "system"]

            if len(other_messages) > limit - len(system_messages):
                other_messages = other_messages[-(limit - len(system_messages)) :]

            messages = system_messages + other_messages

        return [msg.to_dict() for msg in messages]

    def clear(self, keep_system: bool = True) -> None:
        """
        清空对话

        Args:
            keep_system: 是否保留系统消息
        """
        if keep_system:
            self.messages = [msg for msg in self.messages if msg.role == "system"]
        else:
            self.messages = []

    def __len__(self) -> int:
        return len(self.messages)


class LLMBase(ABC):
    """
    大语言模型基类
    定义统一的LLM接口，所有LLM实现都应继承此类
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化LLM实例

        Args:
            config: 配置参数字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def chat(
        self, messages: Union[List[Dict[str, Any]], Conversation, str], **kwargs
    ) -> str:
        """
        单轮对话

        Args:
            messages: 消息列表、对话对象或单个文本
            **kwargs: 其他参数

        Returns:
            回复文本

        Raises:
            LLMError: 对话过程中的错误
        """
        pass

    def chat_stream(
        self, messages: Union[List[Dict[str, Any]], Conversation, str], **kwargs
    ) -> Iterator[str]:
        """
        流式对话

        Args:
            messages: 消息列表、对话对象或单个文本
            **kwargs: 其他参数

        Yields:
            回复文本片段

        Raises:
            LLMError: 对话过程中的错误
        """
        # 默认实现：将完整回复作为单个片段返回
        try:
            response = self.chat(messages, **kwargs)
            yield response
        except Exception as e:
            raise LLMError(f"流式对话失败: {e}")

    def normalize_messages(
        self, messages: Union[List[Dict[str, Any]], Conversation, str]
    ) -> List[Dict[str, Any]]:
        """
        标准化消息格式

        Args:
            messages: 输入消息

        Returns:
            标准化的消息列表
        """
        if isinstance(messages, str):
            # 单个文本转换为用户消息
            return [{"role": "user", "content": messages}]
        elif isinstance(messages, Conversation):
            # 对话对象转换为消息列表
            return messages.get_messages()
        elif isinstance(messages, list):
            # 验证消息列表格式
            normalized = []
            for msg in messages:
                if isinstance(msg, dict):
                    if "role" in msg and "content" in msg:
                        normalized.append(msg)
                    else:
                        self.logger.warning(f"消息格式不完整: {msg}")
                elif isinstance(msg, Message):
                    normalized.append(msg.to_dict())
                else:
                    self.logger.warning(f"不支持的消息类型: {type(msg)}")
            return normalized
        else:
            raise LLMError(f"不支持的消息格式: {type(messages)}")

    def validate_messages(self, messages: List[Dict[str, Any]]) -> bool:
        """
        验证消息格式

        Args:
            messages: 消息列表

        Returns:
            是否有效
        """
        if not messages:
            self.logger.error("消息列表为空")
            return False

        for i, msg in enumerate(messages):
            if not isinstance(msg, dict):
                self.logger.error(f"消息 {i} 不是字典格式")
                return False

            if "role" not in msg or "content" not in msg:
                self.logger.error(f"消息 {i} 缺少必要字段")
                return False

            if msg["role"] not in ["user", "assistant", "system"]:
                self.logger.warning(f"消息 {i} 角色不标准: {msg['role']}")

            if not isinstance(msg["content"], str):
                self.logger.error(f"消息 {i} 内容不是字符串")
                return False

        return True

    def create_conversation(self, system_prompt: Optional[str] = None) -> Conversation:
        """
        创建新对话

        Args:
            system_prompt: 系统提示词

        Returns:
            对话对象
        """
        return Conversation(system_prompt)

    def test_connection(self) -> bool:
        """
        测试LLM服务连接

        Returns:
            连接是否正常
        """
        try:
            # 尝试发送一个简单的测试消息
            test_message = "Hello, this is a test message. Please reply with 'OK'."
            response = self.chat(test_message)

            # 检查是否有回复
            if response and len(response.strip()) > 0:
                self.logger.info("LLM连接测试成功")
                return True
            else:
                self.logger.error("LLM连接测试失败：无回复")
                return False

        except Exception as e:
            self.logger.error(f"LLM连接测试失败: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            模型信息字典
        """
        return {
            "provider": self.__class__.__name__,
            "model": self.config.get("model", "unknown"),
            "max_tokens": self.config.get("max_tokens", 0),
            "temperature": self.config.get("temperature", 0.0),
            "config": self.config,
        }

    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的token数量

        Args:
            text: 输入文本

        Returns:
            估算的token数量
        """
        # 简单估算：中文按字符数，英文按单词数的1.3倍
        if not text:
            return 0

        # 统计中文字符
        chinese_chars = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")

        # 统计英文单词
        english_words = len([word for word in text.split() if word.isalpha()])

        # 估算token数
        estimated_tokens = chinese_chars + int(english_words * 1.3)

        return max(estimated_tokens, len(text) // 4)  # 最少按1/4字符数计算

    def truncate_messages(
        self, messages: List[Dict[str, Any]], max_tokens: int
    ) -> List[Dict[str, Any]]:
        """
        截断消息以适应token限制

        Args:
            messages: 消息列表
            max_tokens: 最大token数

        Returns:
            截断后的消息列表
        """
        if not messages:
            return messages

        # 保留系统消息
        system_messages = [msg for msg in messages if msg.get("role") == "system"]
        other_messages = [msg for msg in messages if msg.get("role") != "system"]

        # 计算系统消息的token数
        system_tokens = sum(
            self.estimate_tokens(msg.get("content", "")) for msg in system_messages
        )

        # 剩余可用token数
        remaining_tokens = max_tokens - system_tokens

        if remaining_tokens <= 0:
            self.logger.warning("系统消息已超过token限制")
            return system_messages

        # 从最新消息开始保留
        truncated_messages = []
        current_tokens = 0

        for msg in reversed(other_messages):
            msg_tokens = self.estimate_tokens(msg.get("content", ""))
            if current_tokens + msg_tokens <= remaining_tokens:
                truncated_messages.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break

        return system_messages + truncated_messages
