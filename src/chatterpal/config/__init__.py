# -*- coding: utf-8 -*-
"""
Configuration management module.

This module provides unified configuration management for ChatterPal,
supporting environment variables, configuration files, and type-safe access.
"""

from .settings import (
    Settings,
    get_settings,
    reload_settings,
    get_api_config,
    get_audio_config,
    get_model_config,
    get_web_config,
)

from .loader import (
    ConfigurationError,
    load_config_file,
    validate_api_keys,
    check_required_config,
    get_config_summary,
    create_default_config_file,
    print_config_status,
)

__all__ = [
    # Settings
    "Settings",
    "get_settings",
    "reload_settings",
    "get_api_config",
    "get_audio_config",
    "get_model_config",
    "get_web_config",
    # Loader
    "ConfigurationError",
    "load_config_file",
    "validate_api_keys",
    "check_required_config",
    "get_config_summary",
    "create_default_config_file",
    "print_config_status",
]
