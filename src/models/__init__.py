"""
Data models package for the Fit-File-to-Calories-Burnt application.

This package contains data classes and models for representing:
- Heart rate data and calorie calculations
- FIT file metadata and device information
- Processing results and validation structures
"""

from .fit_data import HeartRateData, CalorieData, ProcessingResult
from .metadata import FitFileMetadata, DeviceInfo

__all__ = [
    'HeartRateData',
    'CalorieData', 
    'ProcessingResult',
    'FitFileMetadata',
    'DeviceInfo'
]