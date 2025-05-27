"""
Custom exception classes for the Fit-File-to-Calories-Burnt application.

This module contains all custom exceptions used throughout the application,
organized in a logical hierarchy for better error handling and maintainability.
"""


class FitFileApplicationError(Exception):
    """
    Base exception class for all application-specific errors.
    
    This serves as the root exception for all custom exceptions in the
    Fit-File-to-Calories-Burnt application, allowing for broad exception
    handling when needed.
    """
    pass


# =============================================================================
# FIT File Processing Exceptions
# =============================================================================

class FitFileError(FitFileApplicationError):
    """
    Base exception for FIT file processing errors.
    
    This exception serves as the parent class for all FIT file-related
    errors, including file parsing, data extraction, and processing issues.
    """
    pass


class InvalidFitFileError(FitFileError):
    """
    Exception raised when a FIT file is invalid or corrupted.
    
    This exception is raised when:
    - The file is not a valid FIT file format
    - The file is corrupted or unreadable
    - The file structure is malformed
    """
    pass


class MissingDataError(FitFileError):
    """
    Exception raised when required data is missing from a FIT file.
    
    This exception is raised when:
    - No heart rate data is found in the FIT file
    - Essential metadata is missing
    - Required fields for calculations are not present
    """
    pass


# =============================================================================
# Configuration Exceptions
# =============================================================================

class ConfigError(FitFileApplicationError):
    """
    Exception raised for configuration-related errors.
    
    This exception is raised when:
    - Configuration file is missing or unreadable
    - Configuration file contains invalid JSON
    - Configuration values are invalid or out of range
    - Required configuration parameters are missing
    """
    pass


# =============================================================================
# Input Validation Exceptions
# =============================================================================

class InputValidationError(FitFileApplicationError):
    """
    Exception raised when input validation fails.
    
    This exception is raised when:
    - User input parameters are invalid or out of range
    - Heart rate data fails validation checks
    - File paths are invalid or contain dangerous characters
    - Physiological parameters are unreasonable
    """
    pass


# =============================================================================
# Cardio Calculator Exceptions
# =============================================================================

class CardioCalculatorError(FitFileApplicationError):
    """
    Base exception for cardio calculator errors.
    
    This exception serves as the parent class for all cardio calculation-related
    errors, including mathematical computation failures and invalid input scenarios.
    """
    pass


class CalculationError(CardioCalculatorError):
    """
    Exception raised when a calculation fails.
    
    This exception is raised when:
    - Mathematical calculations result in division by zero
    - Calculation inputs produce invalid results
    - Numerical computation errors occur
    - Algorithm constraints are violated
    """
    pass