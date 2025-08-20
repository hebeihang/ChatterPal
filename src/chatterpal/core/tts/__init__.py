# -*- coding: utf-8 -*-
"""
语音合成(TTS)模块
提供统一的语音合成接口，支持多种TTS引擎
"""

from .base import TTSBase, TTSError
from .edge import EdgeTTS

__all__ = ["TTSBase", "TTSError", "EdgeTTS"]
