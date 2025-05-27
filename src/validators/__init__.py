"""
Validation package for the Fit-File-to-Calories-Burnt application.

This package contains validation functions for:
- Input validation for physiological parameters
- FIT file data integrity validation
- Data model validation
"""

from .input_validator import (
    validate_gender,
    validate_heart_rate,
    validate_weight,
    validate_age,
    validate_kcal_per_min,
    validate_calculation_inputs,
    validate_heart_rate_data,
    validate_fit_file_data_integrity,
    InputValidationError
)

__all__ = [
    'validate_gender',
    'validate_heart_rate',
    'validate_weight',
    'validate_age',
    'validate_kcal_per_min',
    'validate_calculation_inputs',
    'validate_heart_rate_data',
    'validate_fit_file_data_integrity',
    'InputValidationError'
]