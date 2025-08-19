# -*- coding: utf-8 -*-
"""
通用工具模块

提供音频处理、文本处理和日志记录等通用功能。
"""

from .audio import (
    AudioProcessor,
    create_temp_audio_file,
    cleanup_temp_file,
    get_audio_duration,
    convert_audio_format,
)

from .text import (
    TextProcessor,
    remove_filler_words,
    format_transcript_with_timestamps,
    extract_pronunciation_targets,
    generate_pronunciation_feedback,
)

from .logger import (
    OralCounsellorLogger,
    get_logger,
    setup_logging,
    LoggerMixin,
    log_function_call,
    log_performance,
    debug,
    info,
    warning,
    error,
    critical,
    exception,
)

__all__ = [
    # Audio utilities
    "AudioProcessor",
    "create_temp_audio_file",
    "cleanup_temp_file",
    "get_audio_duration",
    "convert_audio_format",
    # Text utilities
    "TextProcessor",
    "remove_filler_words",
    "format_transcript_with_timestamps",
    "extract_pronunciation_targets",
    "generate_pronunciation_feedback",
    # Logger utilities
    "OralCounsellorLogger",
    "get_logger",
    "setup_logging",
    "LoggerMixin",
    "log_function_call",
    "log_performance",
    "debug",
    "info",
    "warning",
    "error",
    "critical",
    "exception",
]
