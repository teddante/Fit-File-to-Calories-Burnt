"""
Input validation module for the Fit-File-to-Calories-Burnt application.

This module contains validation functions for physiological parameters,
heart rate data, and FIT file data integrity checks.
"""

import logging
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional, Union
from src.core.logger import get_logger
from src.exceptions import InputValidationError

# Get logger for this module
logger = get_logger(__name__)


def validate_gender(gender: str) -> str:
    """
    Validate and normalize the gender input.
    
    Args:
        gender: The gender string to validate ('male' or 'female')
        
    Returns:
        Normalized gender string ('male' or 'female')
        
    Raises:
        InputValidationError: If the gender is not 'male' or 'female'
    """
    if not isinstance(gender, str):
        raise InputValidationError(f"Gender must be a string, got {type(gender).__name__}")
        
    normalized = gender.strip().lower()
    if normalized not in ['male', 'female']:
        raise InputValidationError(f"Gender must be 'male' or 'female', got '{gender}'")
    return normalized


def validate_heart_rate(heart_rate: Union[int, float]) -> float:
    """
    Validate heart rate value for physiological reasonableness.
    
    Args:
        heart_rate: Heart rate in beats per minute
        
    Returns:
        Validated heart rate as float
        
    Raises:
        InputValidationError: If heart rate is outside reasonable physiological ranges
    """
    if not isinstance(heart_rate, (int, float)):
        raise InputValidationError(f"Heart rate must be a number, got {type(heart_rate).__name__}")
        
    if heart_rate <= 0:
        raise InputValidationError(f"Heart rate must be positive, got {heart_rate}")
        
    if heart_rate > 250:  # Physiological maximum
        raise InputValidationError(f"Heart rate {heart_rate} exceeds physiological maximum (250 bpm)")
        
    return float(heart_rate)


def validate_weight(weight: Union[int, float]) -> float:
    """
    Validate weight value for reasonableness.
    
    Args:
        weight: Weight in kg
        
    Returns:
        Validated weight as float
        
    Raises:
        InputValidationError: If weight is outside reasonable ranges
    """
    if not isinstance(weight, (int, float)):
        raise InputValidationError(f"Weight must be a number, got {type(weight).__name__}")
        
    if weight <= 0:
        raise InputValidationError(f"Weight must be positive, got {weight}")
        
    if weight > 500:  # Reasonable maximum in kg
        raise InputValidationError(f"Weight {weight} kg exceeds reasonable maximum (500 kg)")
        
    return float(weight)


def validate_age(age: Union[int, float]) -> float:
    """
    Validate age value for reasonableness.
    
    Args:
        age: Age in years
        
    Returns:
        Validated age as float
        
    Raises:
        InputValidationError: If age is outside reasonable ranges
    """
    if not isinstance(age, (int, float)):
        raise InputValidationError(f"Age must be a number, got {type(age).__name__}")
        
    if age <= 0:
        raise InputValidationError(f"Age must be positive, got {age}")
        
    if age > 130:  # Reasonable maximum age
        raise InputValidationError(f"Age {age} exceeds reasonable maximum (130 years)")
        
    return float(age)


def validate_kcal_per_min(kcal_per_min: Union[int, float]) -> float:
    """
    Validate kilocalories per minute value for reasonableness.
    
    Args:
        kcal_per_min: Kilocalories burned per minute
        
    Returns:
        Validated kcal_per_min as float
        
    Raises:
        InputValidationError: If kcal_per_min is outside reasonable ranges
    """
    if not isinstance(kcal_per_min, (int, float)):
        raise InputValidationError(f"Kcal per minute must be a number, got {type(kcal_per_min).__name__}")
        
    if kcal_per_min < 0:
        raise InputValidationError(f"Kcal per minute cannot be negative, got {kcal_per_min}")
        
    if kcal_per_min > 100:  # Reasonable maximum
        raise InputValidationError(f"Kcal per minute {kcal_per_min} exceeds reasonable maximum (100 kcal/min)")
        
    return float(kcal_per_min)


def validate_calculation_inputs(heart_rate: Optional[float] = None,
                               weight: Optional[float] = None,
                               age: Optional[float] = None,
                               kcal_per_min: Optional[float] = None,
                               gender: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate calculation inputs for physiological reasonableness.
    
    Args:
        heart_rate: Heart rate in beats per minute
        weight: Weight in kg
        age: Age in years
        kcal_per_min: Kilocalories burned per minute
        gender: 'male' or 'female'
        
    Returns:
        Dictionary of validated inputs
        
    Raises:
        InputValidationError: If any input is outside reasonable physiological ranges
    """
    validated = {}
    
    # Validate heart rate if provided
    if heart_rate is not None:
        validated['heart_rate'] = validate_heart_rate(heart_rate)
    
    # Validate weight if provided
    if weight is not None:
        validated['weight'] = validate_weight(weight)
    
    # Validate age if provided
    if age is not None:
        validated['age'] = validate_age(age)
    
    # Validate kcal_per_min if provided
    if kcal_per_min is not None:
        validated['kcal_per_min'] = validate_kcal_per_min(kcal_per_min)
    
    # Validate gender if provided
    if gender is not None:
        validated['gender'] = validate_gender(gender)
    
    return validated


def validate_heart_rate_data(heart_rate_data: List[Tuple[datetime, Union[int, float]]]) -> List[Tuple[datetime, float]]:
    """
    Validate a list of heart rate data tuples.
    
    Args:
        heart_rate_data: List of (timestamp, heart_rate) tuples
        
    Returns:
        List of validated (timestamp, heart_rate) tuples with heart_rate as float
        
    Raises:
        InputValidationError: If data is invalid or contains unreasonable values
    """
    if not isinstance(heart_rate_data, list):
        raise InputValidationError(f"Heart rate data must be a list, got {type(heart_rate_data).__name__}")
        
    if not heart_rate_data:
        raise InputValidationError("Heart rate data cannot be empty")
        
    validated_data = []
    
    for i, item in enumerate(heart_rate_data):
        if not isinstance(item, tuple) or len(item) != 2:
            raise InputValidationError(f"Item {i} must be a tuple of length 2, got {item}")
            
        timestamp, heart_rate = item
        
        # Validate timestamp
        if not isinstance(timestamp, datetime):
            raise InputValidationError(f"Timestamp at index {i} must be a datetime object, got {type(timestamp).__name__}")
            
        # Validate heart rate
        try:
            validated_hr = validate_heart_rate(heart_rate)
        except InputValidationError as e:
            raise InputValidationError(f"Heart rate at index {i}: {e}")
            
        validated_data.append((timestamp, validated_hr))
    
    # Check for chronological order
    timestamps = [item[0] for item in validated_data]
    if timestamps != sorted(timestamps):
        logger.warning("Heart rate data is not in chronological order")
    
    # Check for duplicate timestamps
    unique_timestamps = set(timestamps)
    if len(unique_timestamps) != len(timestamps):
        logger.warning("Heart rate data contains duplicate timestamps")
    
    return validated_data


def validate_fit_file_data_integrity(heart_rate_data: List[Tuple[datetime, Union[int, float]]],
                                    min_data_points: int = 2,
                                    max_gap_minutes: float = 60.0) -> Dict[str, Any]:
    """
    Validate FIT file data integrity and provide quality metrics.
    
    Args:
        heart_rate_data: List of (timestamp, heart_rate) tuples
        min_data_points: Minimum number of data points required
        max_gap_minutes: Maximum allowed gap between data points in minutes
        
    Returns:
        Dictionary containing validation results and quality metrics
        
    Raises:
        InputValidationError: If data fails basic integrity checks
    """
    if not isinstance(heart_rate_data, list):
        raise InputValidationError(f"Heart rate data must be a list, got {type(heart_rate_data).__name__}")
        
    if len(heart_rate_data) < min_data_points:
        raise InputValidationError(f"At least {min_data_points} heart rate data points are required, got {len(heart_rate_data)}")
    
    # Validate individual data points
    validated_data = validate_heart_rate_data(heart_rate_data)
    
    # Sort by timestamp for analysis
    sorted_data = sorted(validated_data, key=lambda x: x[0])
    
    # Calculate quality metrics
    total_duration = (sorted_data[-1][0] - sorted_data[0][0]).total_seconds() / 60.0  # minutes
    data_points = len(sorted_data)
    avg_interval = total_duration / (data_points - 1) if data_points > 1 else 0
    
    # Check for large gaps
    large_gaps = []
    for i in range(1, len(sorted_data)):
        gap_minutes = (sorted_data[i][0] - sorted_data[i-1][0]).total_seconds() / 60.0
        if gap_minutes > max_gap_minutes:
            large_gaps.append({
                'start_time': sorted_data[i-1][0],
                'end_time': sorted_data[i][0],
                'gap_minutes': gap_minutes
            })
    
    # Calculate heart rate statistics
    heart_rates = [hr for _, hr in sorted_data]
    min_hr = min(heart_rates)
    max_hr = max(heart_rates)
    avg_hr = sum(heart_rates) / len(heart_rates)
    
    # Check for unrealistic heart rate patterns
    warnings = []
    
    if min_hr < 40:
        warnings.append(f"Very low minimum heart rate: {min_hr} bpm")
        
    if max_hr > 220:
        warnings.append(f"Very high maximum heart rate: {max_hr} bpm")
        
    if max_hr - min_hr > 150:
        warnings.append(f"Very large heart rate range: {max_hr - min_hr} bpm")
        
    if large_gaps:
        warnings.append(f"Found {len(large_gaps)} large gaps (>{max_gap_minutes} min) in data")
    
    # Check for flat-line periods (same HR for extended time)
    flat_periods = []
    current_hr = None
    flat_start = None
    flat_count = 0
    
    for timestamp, hr in sorted_data:
        if hr == current_hr:
            if flat_start is None:
                flat_start = timestamp
            flat_count += 1
        else:
            if flat_count >= 10:  # 10 or more consecutive identical readings
                flat_periods.append({
                    'heart_rate': current_hr,
                    'start_time': flat_start,
                    'end_time': timestamp,
                    'count': flat_count
                })
            current_hr = hr
            flat_start = None
            flat_count = 1
    
    if flat_periods:
        warnings.append(f"Found {len(flat_periods)} potential flat-line periods")
    
    return {
        'is_valid': True,
        'data_points': data_points,
        'total_duration_minutes': total_duration,
        'average_interval_minutes': avg_interval,
        'heart_rate_stats': {
            'min': min_hr,
            'max': max_hr,
            'average': avg_hr,
            'range': max_hr - min_hr
        },
        'large_gaps': large_gaps,
        'flat_periods': flat_periods,
        'warnings': warnings,
        'quality_score': calculate_data_quality_score(data_points, total_duration, large_gaps, warnings)
    }


def calculate_data_quality_score(data_points: int, 
                                duration_minutes: float, 
                                large_gaps: List[Dict], 
                                warnings: List[str]) -> float:
    """
    Calculate a data quality score from 0.0 to 1.0.
    
    Args:
        data_points: Number of data points
        duration_minutes: Total duration in minutes
        large_gaps: List of large gaps in data
        warnings: List of warning messages
        
    Returns:
        Quality score from 0.0 (poor) to 1.0 (excellent)
    """
    score = 1.0
    
    # Penalize for insufficient data density
    if duration_minutes > 0:
        data_density = data_points / duration_minutes  # points per minute
        if data_density < 0.5:  # Less than 1 point per 2 minutes
            score -= 0.2
        elif data_density < 1.0:  # Less than 1 point per minute
            score -= 0.1
    
    # Penalize for large gaps
    gap_penalty = min(0.3, len(large_gaps) * 0.1)
    score -= gap_penalty
    
    # Penalize for warnings
    warning_penalty = min(0.3, len(warnings) * 0.05)
    score -= warning_penalty
    
    # Ensure score is between 0 and 1
    return max(0.0, min(1.0, score))


def validate_file_path(file_path: str) -> str:
    """
    Validate file path for basic requirements.
    
    Args:
        file_path: Path to validate
        
    Returns:
        Validated file path
        
    Raises:
        InputValidationError: If file path is invalid
    """
    if not isinstance(file_path, str):
        raise InputValidationError(f"File path must be a string, got {type(file_path).__name__}")
        
    if not file_path.strip():
        raise InputValidationError("File path cannot be empty")
        
    # Check for potentially dangerous characters (basic check)
    dangerous_chars = ['<', '>', '|', '*', '?']
    for char in dangerous_chars:
        if char in file_path:
            raise InputValidationError(f"File path contains invalid character: '{char}'")
    
    return file_path.strip()


def validate_duration(duration_seconds: Union[int, float]) -> float:
    """
    Validate duration value.
    
    Args:
        duration_seconds: Duration in seconds
        
    Returns:
        Validated duration as float
        
    Raises:
        InputValidationError: If duration is invalid
    """
    if not isinstance(duration_seconds, (int, float)):
        raise InputValidationError(f"Duration must be a number, got {type(duration_seconds).__name__}")
        
    if duration_seconds < 0:
        raise InputValidationError(f"Duration cannot be negative, got {duration_seconds}")
        
    if duration_seconds > 86400 * 7:  # More than a week
        raise InputValidationError(f"Duration {duration_seconds} seconds exceeds reasonable maximum (1 week)")
        
    return float(duration_seconds)