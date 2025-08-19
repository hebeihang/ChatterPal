# -*- coding: utf-8 -*-
"""
大语言模型(LLM)模块
提供统一的大语言模型接口，支持多种LLM提供商
"""

from .base import LLMBase, LLMError
from .alibaba import AlibabaDashScopeLLM
from .openai import OpenAILLM

__all__ = ["LLMBase", "LLMError", "AlibabaDashScopeLLM", "OpenAILLM"]
