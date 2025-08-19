# -*- coding: utf-8 -*-
"""
Configuration management system for OralCounsellor.

This module provides a unified configuration management system that supports
environment variables, configuration files, and type-safe configuration access.
"""

import os
from pathlib import Path
from typing import Optional, Union
from pydantic import BaseModel, Field, field_validator, computed_field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


class Settings(BaseSettings):
    """
    Application settings with support for environment variables and .env files.

    Configuration is loaded in the following order (later sources override earlier ones):
    1. Default values
    2. .env file
    3. Environment variables
    """

    # API Configuration
    alibaba_api_key: str = Field(
        default="", description="Alibaba Cloud API key for speech services"
    )
    alibaba_api_secret: str = Field(
        default="", description="Alibaba Cloud API secret for speech services"
    )
    openai_api_key: Optional[str] = Field(
        default=None, description="OpenAI API key (optional)"
    )
    openai_base_url: Optional[str] = Field(
        default=None, description="OpenAI API base URL (optional)"
    )
    openai_model: str = Field(default="gpt-3.5-turbo", description="OpenAI model name")
    alibaba_model: str = Field(default="qwen-turbo", description="Alibaba model name")
    
    # Additional Alibaba Configuration
    dashscope_api_key: Optional[str] = Field(
        default=None, description="DashScope API key (alias for alibaba_api_key)"
    )
    alibaba_base_url: Optional[str] = Field(
        default=None, description="Alibaba API base URL"
    )
    alibaba_max_tokens: Optional[int] = Field(
        default=None, description="Alibaba max tokens"
    )
    alibaba_temperature: Optional[float] = Field(
        default=None, description="Alibaba temperature"
    )
    alibaba_top_p: Optional[float] = Field(
        default=None, description="Alibaba top_p"
    )
    alibaba_enable_search: Optional[bool] = Field(
        default=None, description="Alibaba enable search"
    )

    # Audio Configuration
    audio_sample_rate: int = Field(default=16000, description="Audio sample rate in Hz")
    audio_temp_dir: str = Field(
        default="temp_audio", description="Directory for temporary audio files"
    )
    audio_max_duration: int = Field(
        default=300, description="Maximum audio duration in seconds"
    )

    # Model Configuration
    whisper_model: str = Field(
        default="base",
        description="Whisper model size (tiny, base, small, medium, large)",
    )
    whisper_device: str = Field(
        default="auto", description="Whisper device (auto, cpu, cuda)"
    )
    asr_provider: str = Field(
        default="whisper", description="ASR provider (whisper, alibaba)"
    )
    tts_provider: str = Field(default="edge", description="TTS provider (edge, alibaba)")
    llm_provider: str = Field(
        default="alibaba", description="LLM provider (alibaba, openai)"
    )
    
    # Chat Configuration
    system_prompt: Optional[str] = Field(
        default=None, 
        description="Custom system prompt for the AI conversation coach. If not set, uses default professional coach prompt."
    )
    max_history_length: int = Field(
        default=20, 
        description="Maximum number of conversation messages to keep in history"
    )
    session_timeout: int = Field(
        default=3600, 
        description="Chat session timeout in seconds (default: 1 hour)"
    )

    # TTS Configuration
    edge_tts_voice: str = Field(
        default="en-US-JennyNeural", description="Edge TTS voice"
    )
    edge_tts_rate: str = Field(default="+0%", description="Edge TTS speech rate")
    edge_tts_volume: str = Field(default="+0%", description="Edge TTS volume")
    
    # Alibaba TTS Configuration
    alibaba_tts_voice: str = Field(
        default="longxiaochun", description="Alibaba TTS voice (longxiaochun for cosyvoice-v1)"
    )
    alibaba_tts_volume: int = Field(
        default=50, description="Alibaba TTS volume (0-100)"
    )
    alibaba_tts_speech_rate: int = Field(
        default=0, description="Alibaba TTS speech rate (-500 to 500)"
    )
    alibaba_tts_pitch_rate: int = Field(
        default=0, description="Alibaba TTS pitch rate (-500 to 500)"
    )

    # Web Interface Configuration
    gradio_share: bool = Field(
        default=False, description="Enable Gradio public sharing"
    )
    gradio_port: int = Field(default=7860, description="Gradio server port")
    gradio_server_name: str = Field(
        default="127.0.0.1", description="Gradio server host"
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_file: Optional[str] = Field(
        default=None, description="Log file path (optional)"
    )

    # Development Configuration
    debug: bool = Field(default=False, description="Enable debug mode")
    environment: str = Field(
        default="production", description="Environment (development, production)"
    )

    # Cache Configuration
    cache_dir: str = Field(default=".cache", description="Cache directory")
    model_cache_dir: str = Field(
        default="data/models", description="Model cache directory"
    )

    # Security Configuration
    secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key for security features",
    )
    allowed_hosts: str = Field(
        default="localhost,127.0.0.1",
        description="Comma-separated list of allowed hosts",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @field_validator("whisper_model")
    @classmethod
    def validate_whisper_model(cls, v):
        """Validate Whisper model size."""
        valid_models = [
            "tiny",
            "base",
            "small",
            "medium",
            "large",
            "large-v2",
            "large-v3",
        ]
        if v not in valid_models:
            raise ValueError(
                f"Invalid Whisper model: {v}. Must be one of {valid_models}"
            )
        return v

    @field_validator("asr_provider")
    @classmethod
    def validate_asr_provider(cls, v):
        """Validate ASR provider."""
        valid_providers = ["whisper", "alibaba"]
        if v not in valid_providers:
            raise ValueError(
                f"Invalid ASR provider: {v}. Must be one of {valid_providers}"
            )
        return v

    @field_validator("tts_provider")
    @classmethod
    def validate_tts_provider(cls, v):
        """Validate TTS provider."""
        valid_providers = ["edge", "alibaba"]
        if v not in valid_providers:
            raise ValueError(
                f"Invalid TTS provider: {v}. Must be one of {valid_providers}"
            )
        return v

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v):
        """Validate LLM provider."""
        valid_providers = ["alibaba", "openai"]
        if v not in valid_providers:
            raise ValueError(
                f"Invalid LLM provider: {v}. Must be one of {valid_providers}"
            )
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment."""
        valid_environments = ["development", "production"]
        if v not in valid_environments:
            raise ValueError(
                f"Invalid environment: {v}. Must be one of {valid_environments}"
            )
        return v

    @field_validator("gradio_port")
    @classmethod
    def validate_gradio_port(cls, v):
        """Validate Gradio port."""
        if not (1024 <= v <= 65535):
            raise ValueError(f"Invalid port: {v}. Must be between 1024 and 65535")
        return v

    @field_validator("audio_sample_rate")
    @classmethod
    def validate_audio_sample_rate(cls, v):
        """Validate audio sample rate."""
        valid_rates = [8000, 16000, 22050, 44100, 48000]
        if v not in valid_rates:
            raise ValueError(f"Invalid sample rate: {v}. Must be one of {valid_rates}")
        return v

    @field_validator("audio_max_duration")
    @classmethod
    def validate_audio_max_duration(cls, v):
        """Validate audio max duration."""
        if v <= 0 or v > 3600:  # Max 1 hour
            raise ValueError(
                f"Invalid max duration: {v}. Must be between 1 and 3600 seconds"
            )
        return v

    def get_allowed_hosts_list(self) -> list[str]:
        """Get allowed hosts as a list."""
        return [host.strip() for host in self.allowed_hosts.split(",")]

    def get_audio_temp_path(self) -> Path:
        """Get audio temp directory as Path object."""
        return Path(self.audio_temp_dir)

    def get_cache_path(self) -> Path:
        """Get cache directory as Path object."""
        return Path(self.cache_dir)

    def get_model_cache_path(self) -> Path:
        """Get model cache directory as Path object."""
        return Path(self.model_cache_dir)

    def get_log_file_path(self) -> Optional[Path]:
        """Get log file path as Path object."""
        return Path(self.log_file) if self.log_file else None

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.get_audio_temp_path(),
            self.get_cache_path(),
            self.get_model_cache_path(),
        ]

        # Add log directory if log file is specified
        if self.log_file:
            log_path = self.get_log_file_path()
            if log_path:
                directories.append(log_path.parent)

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def validate_config(self) -> bool:
        """
        Validate configuration settings.

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Check required API keys based on providers
            if self.asr_provider == "alibaba":
                if not self.alibaba_api_key or not self.alibaba_api_secret:
                    print(
                        "❌ Alibaba API credentials are required when using Alibaba ASR"
                    )
                    return False

            if self.llm_provider == "alibaba":
                if not self.alibaba_api_key or not self.alibaba_api_secret:
                    print(
                        "❌ Alibaba API credentials are required when using Alibaba LLM"
                    )
                    return False

            if self.llm_provider == "openai":
                if not self.openai_api_key:
                    print("❌ OpenAI API key is required when using OpenAI LLM")
                    return False

            # Ensure directories exist
            self.ensure_directories()

            return True

        except Exception as e:
            print(f"❌ Configuration validation failed: {e}")
            return False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings(reload: bool = False) -> Settings:
    """
    Get the global settings instance.

    Args:
        reload: If True, reload settings from environment/files

    Returns:
        Settings instance
    """
    global _settings

    if _settings is None or reload:
        # Always try to load from project root first
        project_root = Path(__file__).parent.parent.parent.parent
        env_file = project_root / ".env"
        
        if env_file.exists():
            load_dotenv(env_file, override=True)
        else:
            # Fallback to current directory
            env_file = Path(".env")
            if env_file.exists():
                load_dotenv(env_file, override=True)

        _settings = Settings()
        _settings.ensure_directories()

    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment variables and files.

    Returns:
        Reloaded Settings instance
    """
    return get_settings(reload=True)


# Convenience function for common use cases
def get_api_config() -> dict[str, str]:
    """Get API configuration as a dictionary."""
    settings = get_settings()
    return {
        "alibaba_api_key": settings.alibaba_api_key,
        "alibaba_api_secret": settings.alibaba_api_secret,
        "openai_api_key": settings.openai_api_key or "",
    }


def get_audio_config() -> dict[str, Union[int, str, Path]]:
    """Get audio configuration as a dictionary."""
    settings = get_settings()
    return {
        "sample_rate": settings.audio_sample_rate,
        "temp_dir": settings.get_audio_temp_path(),
        "max_duration": settings.audio_max_duration,
    }


def get_model_config() -> dict[str, str]:
    """Get model configuration as a dictionary."""
    settings = get_settings()
    return {
        "whisper_model": settings.whisper_model,
        "asr_provider": settings.asr_provider,
        "tts_provider": settings.tts_provider,
        "llm_provider": settings.llm_provider,
        "cache_dir": str(settings.get_model_cache_path()),
    }


def get_web_config() -> dict[str, Union[bool, int, str]]:
    """Get web interface configuration as a dictionary."""
    settings = get_settings()
    return {
        "share": settings.gradio_share,
        "port": settings.gradio_port,
        "server_name": settings.gradio_server_name,
        "debug": settings.debug,
    }
