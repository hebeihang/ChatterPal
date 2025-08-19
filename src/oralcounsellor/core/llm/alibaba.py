# -*- coding: utf-8 -*-
"""
阿里百炼LLM实现
基于阿里百炼 OpenAI 兼容 API 进行对话
"""

import os
from typing import Optional, Dict, Any, List, Iterator, Union

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from .base import LLMBase, LLMError, Conversation
from ...utils.encoding_fix import create_safe_logger, safe_str


class AlibabaBailianLLM(LLMBase):
    """
    基于阿里百炼的LLM实现
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化阿里百炼 LLM

        Args:
            config: 配置参数，支持以下参数：
                - api_key: API密钥 (也可以使用 DASHSCOPE_API_KEY 环境变量)
                - model: 模型名称 (默认: qwen-plus)
                - base_url: API基础URL (默认使用 OpenAI 兼容接口)
                - max_tokens: 最大输出token数
                - temperature: 温度参数
                - top_p: top_p参数
                - timeout: 请求超时时间
                - enable_search: 是否启用搜索增强
                - stream_options: 流式选项配置
        """
        super().__init__(config)

        if not OpenAI:
            raise ImportError("openai库未安装，请运行: pip install openai")

        # 获取 API 密钥，优先使用配置中的，然后是环境变量
        self.api_key = self.config.get("api_key") or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise LLMError("阿里百炼API密钥未配置，请设置 api_key 参数或 DASHSCOPE_API_KEY 环境变量")

        self.model = self.config.get("model", "qwen-plus")
        self.base_url = self.config.get(
            "base_url",
            "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.max_tokens = self.config.get("max_tokens", 2000)
        self.temperature = self.config.get("temperature", 0.7)
        self.top_p = self.config.get("top_p", 0.8)
        self.timeout = self.config.get("timeout", 60)
        self.enable_search = self.config.get("enable_search", False)
        self.stream_options = self.config.get("stream_options", {"include_usage": True})

        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )

        self.logger.info(f"阿里百炼 LLM初始化完成，模型: {self.model}, 使用 OpenAI 兼容接口")

    def chat(
        self, messages: Union[List[Dict[str, Any]], Conversation, str], **kwargs
    ) -> str:
        """
        单轮对话

        Args:
            messages: 消息列表、对话对象或单个文本
            **kwargs: 其他参数，支持：
                - model: 临时覆盖模型
                - max_tokens: 临时覆盖最大token数
                - temperature: 临时覆盖温度
                - top_p: 临时覆盖top_p
                - enable_search: 是否启用搜索增强

        Returns:
            回复文本

        Raises:
            LLMError: 对话过程中的错误
        """
        try:
            # 标准化消息格式
            normalized_messages = self.normalize_messages(messages)

            if not self.validate_messages(normalized_messages):
                raise LLMError("消息格式验证失败")

            # 获取参数
            model = kwargs.get("model", self.model)
            max_tokens = kwargs.get("max_tokens", self.max_tokens)
            temperature = kwargs.get("temperature", self.temperature)
            top_p = kwargs.get("top_p", self.top_p)
            enable_search = kwargs.get("enable_search", self.enable_search)

            # 构建请求参数
            request_params = {
                "model": model,
                "messages": normalized_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p
            }

            # 如果启用搜索增强，使用 extra_body 参数
            if enable_search:
                request_params["extra_body"] = {"enable_search": True}

            # 调用 OpenAI 兼容接口
            completion = self.client.chat.completions.create(**request_params)

            # 提取回复内容
            if completion.choices and len(completion.choices) > 0:
                content = completion.choices[0].message.content
                
                # 记录使用情况
                if completion.usage:
                    input_tokens = completion.usage.prompt_tokens
                    output_tokens = completion.usage.completion_tokens
                    total_tokens = completion.usage.total_tokens
                    
                    self.logger.info(
                        f"对话成功，回复长度: {len(content)}, "
                        f"Token使用: {input_tokens}(输入) + {output_tokens}(输出) = {total_tokens}(总计)"
                    )
                else:
                    self.logger.info(f"对话成功，回复长度: {len(content)}")
                
                return content
            else:
                raise LLMError("API返回空的回复")

        except Exception as e:
            # 处理 OpenAI 库的异常
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                if e.response.status_code == 401:
                    raise LLMError("API密钥无效或已过期")
                elif e.response.status_code == 429:
                    raise LLMError("API调用频率超限，请稍后重试")
                elif e.response.status_code >= 500:
                    raise LLMError("服务器内部错误，请稍后重试")
            
            error_msg = safe_str(e)
            self.logger.error(f"对话异常: {error_msg}")
            raise LLMError(f"对话异常: {error_msg}")

    def chat_stream(
        self, messages: Union[List[Dict[str, Any]], Conversation, str], **kwargs
    ) -> Iterator[str]:
        """
        流式对话

        Args:
            messages: 消息列表、对话对象或单个文本
            **kwargs: 其他参数，支持：
                - model: 临时覆盖模型
                - max_tokens: 临时覆盖最大token数
                - temperature: 临时覆盖温度
                - top_p: 临时覆盖top_p
                - enable_search: 是否启用搜索增强

        Yields:
            回复文本片段

        Raises:
            LLMError: 对话过程中的错误
        """
        try:
            # 标准化消息格式
            normalized_messages = self.normalize_messages(messages)

            if not self.validate_messages(normalized_messages):
                raise LLMError("消息格式验证失败")

            # 获取参数
            model = kwargs.get("model", self.model)
            max_tokens = kwargs.get("max_tokens", self.max_tokens)
            temperature = kwargs.get("temperature", self.temperature)
            top_p = kwargs.get("top_p", self.top_p)
            enable_search = kwargs.get("enable_search", self.enable_search)

            # 构建流式请求参数
            request_params = {
                "model": model,
                "messages": normalized_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "stream": True,
                "stream_options": self.stream_options
            }

            # 如果启用搜索增强，使用 extra_body 参数
            if enable_search:
                request_params["extra_body"] = {"enable_search": True}

            # 调用 OpenAI 兼容的流式接口
            stream = self.client.chat.completions.create(**request_params)

            # 处理流式响应
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content

        except Exception as e:
            # 处理 OpenAI 库的异常
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                if e.response.status_code == 401:
                    raise LLMError("API密钥无效或已过期")
                elif e.response.status_code == 429:
                    raise LLMError("API调用频率超限，请稍后重试")
                elif e.response.status_code >= 500:
                    raise LLMError("服务器内部错误，请稍后重试")
            
            error_msg = safe_str(e)
            self.logger.error(f"流式对话异常: {error_msg}")
            raise LLMError(f"流式对话异常: {error_msg}")

    def get_supported_models(self) -> List[str]:
        """
        获取支持的模型列表（基于阿里百炼官方文档）

        Returns:
            支持的模型列表
        """
        return [
            # 通义千问主力模型
            "qwen-turbo",
            "qwen-plus", 
            "qwen-max",
            "qwen-max-0428",
            "qwen-max-0403",
            "qwen-max-0107",
            "qwen-max-longcontext",
            
            # 通义千问2.5系列
            "qwen2.5-72b-instruct",
            "qwen2.5-32b-instruct", 
            "qwen2.5-14b-instruct",
            "qwen2.5-7b-instruct",
            "qwen2.5-3b-instruct",
            "qwen2.5-1.5b-instruct",
            "qwen2.5-0.5b-instruct",
            
            # 通义千问2系列
            "qwen2-72b-instruct",
            "qwen2-57b-a14b-instruct",
            "qwen2-7b-instruct",
            "qwen2-1.5b-instruct",
            "qwen2-0.5b-instruct",
            
            # 代码专用模型
            "qwen2.5-coder-32b-instruct",
            "qwen2.5-coder-14b-instruct",
            "qwen2.5-coder-7b-instruct",
            "qwen2.5-coder-1.5b-instruct",
            
            # 数学专用模型
            "qwen2.5-math-72b-instruct",
            "qwen2.5-math-7b-instruct",
            "qwen2.5-math-1.5b-instruct",
            
            # 通义千问3系列（如果可用）
            "qwen-max-latest"
        ]

    def test_connection(self) -> bool:
        """
        测试阿里百炼服务连接

        Returns:
            连接是否正常
        """
        try:
            # 尝试发送一个简单的测试消息
            test_messages = [
                {"role": "user", "content": "Hello, please reply 'Test successful'."}
            ]
            
            # 使用最小的参数进行测试
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=test_messages,
                max_tokens=10,
                temperature=0.1
            )

            # 检查是否有回复
            if completion.choices and len(completion.choices) > 0:
                response = completion.choices[0].message.content
                if response and len(response.strip()) > 0:
                    self.logger.info("阿里百炼连接测试成功")
                    return True
                else:
                    self.logger.error("阿里百炼连接测试失败：无回复内容")
                    return False
            else:
                self.logger.error("阿里百炼连接测试失败：无回复选择")
                return False

        except Exception as e:
            self.logger.error(f"阿里百炼连接测试失败: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            模型信息字典
        """
        return {
            "provider": "Alibaba Bailian (阿里百炼)",
            "api_type": "OpenAI Compatible",
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "enable_search": self.enable_search,
            "base_url": self.base_url,
            "stream_options": self.stream_options,
            "supported_models": self.get_supported_models(),
        }

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> Dict[str, float]:
        """
        估算调用成本（基于阿里百炼定价）

        Args:
            input_tokens: 输入token数
            output_tokens: 输出token数

        Returns:
            成本信息字典
        """
        # 阿里百炼通义千问定价（2024年最新价格，仅供参考）
        pricing = {
            # 主力模型
            "qwen-turbo": {"input": 0.0003, "output": 0.0006},  # 元/千token
            "qwen-plus": {"input": 0.0008, "output": 0.002},
            "qwen-max": {"input": 0.008, "output": 0.024},
            "qwen-max-0428": {"input": 0.008, "output": 0.024},
            "qwen-max-0403": {"input": 0.008, "output": 0.024},
            "qwen-max-0107": {"input": 0.008, "output": 0.024},
            "qwen-max-longcontext": {"input": 0.008, "output": 0.024},
            
            # 通义千问2.5系列
            "qwen2.5-72b-instruct": {"input": 0.0035, "output": 0.007},
            "qwen2.5-32b-instruct": {"input": 0.002, "output": 0.006},
            "qwen2.5-14b-instruct": {"input": 0.0007, "output": 0.002},
            "qwen2.5-7b-instruct": {"input": 0.0003, "output": 0.0006},
            "qwen2.5-3b-instruct": {"input": 0.0002, "output": 0.0006},
            "qwen2.5-1.5b-instruct": {"input": 0.0001, "output": 0.0002},
            "qwen2.5-0.5b-instruct": {"input": 0.0001, "output": 0.0002},
            
            # 代码专用模型
            "qwen2.5-coder-32b-instruct": {"input": 0.002, "output": 0.006},
            "qwen2.5-coder-14b-instruct": {"input": 0.0007, "output": 0.002},
            "qwen2.5-coder-7b-instruct": {"input": 0.0003, "output": 0.0006},
            "qwen2.5-coder-1.5b-instruct": {"input": 0.0001, "output": 0.0002},
            
            # 数学专用模型
            "qwen2.5-math-72b-instruct": {"input": 0.0035, "output": 0.007},
            "qwen2.5-math-7b-instruct": {"input": 0.0003, "output": 0.0006},
            "qwen2.5-math-1.5b-instruct": {"input": 0.0001, "output": 0.0002},
        }

        model_pricing = pricing.get(self.model, pricing["qwen-turbo"])

        input_cost = (input_tokens / 1000) * model_pricing["input"]
        output_cost = (output_tokens / 1000) * model_pricing["output"]
        total_cost = input_cost + output_cost

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost_yuan": input_cost,
            "output_cost_yuan": output_cost,
            "total_cost_yuan": total_cost,
            "model": self.model,
            "pricing_date": "2024-12"
        }
    
    def get_model_capabilities(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取模型能力信息
        
        Args:
            model_name: 模型名称，如果为None则使用当前模型
            
        Returns:
            模型能力信息
        """
        model = model_name or self.model
        
        # 模型能力映射
        capabilities = {
            # 主力模型
            "qwen-turbo": {
                "max_context_length": 8192,
                "max_output_tokens": 2048,
                "supports_search": True,
                "supports_function_calling": False,
                "supports_vision": False,
                "languages": ["中文", "英文", "日文", "韩文", "法文", "西班牙文", "德文"]
            },
            "qwen-plus": {
                "max_context_length": 32768,
                "max_output_tokens": 2048,
                "supports_search": True,
                "supports_function_calling": True,
                "supports_vision": False,
                "languages": ["中文", "英文", "日文", "韩文", "法文", "西班牙文", "德文"]
            },
            "qwen-max": {
                "max_context_length": 8192,
                "max_output_tokens": 2048,
                "supports_search": True,
                "supports_function_calling": True,
                "supports_vision": False,
                "languages": ["中文", "英文", "日文", "韩文", "法文", "西班牙文", "德文"]
            },
            "qwen-max-longcontext": {
                "max_context_length": 1000000,
                "max_output_tokens": 2048,
                "supports_search": True,
                "supports_function_calling": True,
                "supports_vision": False,
                "languages": ["中文", "英文", "日文", "韩文", "法文", "西班牙文", "德文"]
            }
        }
        
        # 通义千问2.5系列的默认能力
        qwen25_default = {
            "max_context_length": 32768,
            "max_output_tokens": 2048,
            "supports_search": False,
            "supports_function_calling": True,
            "supports_vision": False,
            "languages": ["中文", "英文", "日文", "韩文", "法文", "西班牙文", "德文"]
        }
        
        # 为2.5系列模型设置默认能力
        for model_key in self.get_supported_models():
            if model_key.startswith("qwen2.5") and model_key not in capabilities:
                capabilities[model_key] = qwen25_default.copy()
        
        return capabilities.get(model, qwen25_default)


# 便捷函数
def create_alibaba_llm(
    api_key: str, model: str = "qwen-plus", **kwargs
) -> AlibabaBailianLLM:
    """
    创建阿里百炼 LLM实例的便捷函数

    Args:
        api_key: API密钥
        model: 模型名称
        **kwargs: 其他配置参数

    Returns:
        AlibabaBailianLLM实例
    """
    config = {"api_key": api_key, "model": model, **kwargs}
    return AlibabaBailianLLM(config)


def alibaba_chat(input_text: str, api_key: str, model: str = "qwen-plus") -> str:
    """
    阿里百炼对话的便捷函数（兼容旧代码）

    Args:
        input_text: 输入文本
        api_key: API密钥
        model: 模型名称

    Returns:
        回复文本
    """
    llm = create_alibaba_llm(api_key, model)
    return llm.chat(input_text)


# 向后兼容的别名
AlibabaDashScopeLLM = AlibabaBailianLLM
