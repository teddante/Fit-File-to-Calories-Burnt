"""
Centralized exception handling package for the Fit-File-to-Calories-Burnt application.

This package contains all custom exceptions used throughout the application,
organized in a logical hierarchy for better error handling and maintainability.
"""

from .custom_exceptions import (
    # Base exceptions
    FitFileApplicationError,
    
    # FIT file processing exceptions
    FitFileError,
    InvalidFitFileError,
    MissingDataError,
    
    # Configuration exceptions
    ConfigError,
    
    # Input validation exceptions
    InputValidationError,
    
    # Cardio calculator exceptions
    CardioCalculatorError,
    CalculationError,
)

__all__ = [
    # Base exceptions
    'FitFileApplicationError',
    
    # FIT file processing exceptions
    'FitFileError',
    'InvalidFitFileError',
    'MissingDataError',
    
    # Configuration exceptions
    'ConfigError',
    
    # Input validation exceptions
    'InputValidationError',
    
    # Cardio calculator exceptions
    'CardioCalculatorError',
    'CalculationError',
]