"""
CLI package for the Fit-File-to-Calories-Burnt application.

This package contains the command-line interface components including
menu handling and user interaction logic.
"""

from .menu import main
from .interface import (
    process_fit_files_option,
    calculate_karvonen_zones_option,
    cleanup_fit_files_option,
    prompt_int
)

__all__ = [
    'main',
    'process_fit_files_option',
    'calculate_karvonen_zones_option',
    'cleanup_fit_files_option',
    'prompt_int'
]