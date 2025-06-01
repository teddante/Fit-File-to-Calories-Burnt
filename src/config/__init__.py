"""
Configuration package for the Fit-File-to-Calories-Burnt application.

This package contains configuration management functionality including
loading and validating user configuration settings.
"""

from .config_manager import load_user_config, ConfigError, get_current_config, display_config

__all__ = [
    'load_user_config',
    'ConfigError',
    'get_current_config',
    'display_config'
]