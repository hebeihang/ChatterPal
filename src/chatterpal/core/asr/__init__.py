# -*- coding: utf-8 -*-
"""
语音识别(ASR)模块
提供统一的语音识别接口，支持多种ASR引擎
"""

from .base import ASRBase, ASRError
from .whisper import WhisperASR
from .aliyun import AliyunASR

__all__ = ["ASRBase", "ASRError", "WhisperASR", "AliyunASR"]
