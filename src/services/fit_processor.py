"""
FIT file processing service module.

This module contains functions for processing FIT files and extracting heart rate data
to calculate calories burned during activities.
"""

import logging
from datetime import datetime
from typing import List, Tuple
from fitparse import FitFile
from src.core.logger import get_logger
from src.core.utils import calories_burned

# Get logger for this module
logger = get_logger(__name__)


class FitFileError(Exception):
    """Base exception for FIT file processing errors."""
    pass


class InvalidFitFileError(FitFileError):
    """Exception raised when a FIT file is invalid or corrupted."""
    pass


class MissingDataError(FitFileError):
    """Exception raised when required data is missing from a FIT file."""
    pass


def extract_heart_rate_data(fitfile) -> List[Tuple[datetime, int]]:
    """
    Extract (timestamp, heart_rate) tuples from a FitFile object or a mock.
    
    Args:
        fitfile: A FitFile object or mock containing heart rate data
        
    Returns:
        A list of (timestamp, heart_rate) tuples sorted by timestamp
        
    Raises:
        TypeError: If fitfile is not a valid FitFile object or mock
        AttributeError: If required methods are missing from fitfile
        MissingDataError: If no valid heart rate data is found
        ValueError: If data values are invalid
    """
    if fitfile is None:
        raise TypeError("FitFile object cannot be None")
    
    heart_rate_data = []
    
    try:
        records = fitfile.get_messages('record')
    except AttributeError as e:
        logger.error(f"Invalid FitFile object: {e}")
        raise TypeError(f"Invalid FitFile object: {e}") from e
    except Exception as e:
        logger.error(f"Error accessing FIT file records: {e}")
        raise FitFileError(f"Error accessing FIT file records: {e}") from e
    
    for record in records:
        logger.debug(f"record: {record}")
        timestamp = None
        hr = None
        
        # Always call __iter__ to get fields; handle mocks with instance-level __iter__
        try:
            iter_func = getattr(record, '__iter__')
            fields = list(iter_func(record))
        except (AttributeError, TypeError) as e:
            logger.debug(f"Could not use instance __iter__: {e}")
            try:
                fields = list(iter(record))
            except (TypeError, ValueError) as e:
                logger.debug(f"Could not iterate record: {e}")
                fields = [record]
        
        logger.debug(f"fields: {fields}")
        
        for field in fields:
            try:
                name = getattr(field, 'name', None)
                value = getattr(field, 'value', None)
                logger.debug(f"field: {field}, name: {name}, value: {value}")
                
                if name == 'timestamp':
                    if not isinstance(value, datetime):
                        logger.warning(f"Invalid timestamp format: {value}")
                        continue
                    timestamp = value
                elif name == 'heart_rate':
                    if not isinstance(value, (int, float)) or value <= 0:
                        logger.warning(f"Invalid heart rate value: {value}")
                        continue
                    hr = value
            except Exception as e:
                logger.warning(f"Error processing field {field}: {e}")
                continue
                
        logger.debug(f"extracted timestamp: {timestamp}, hr: {hr}")
        
        if hr is not None and timestamp is not None:
            heart_rate_data.append((timestamp, hr))
    
    logger.debug(f"heart_rate_data: {heart_rate_data}")
    
    if not heart_rate_data:
        logger.error("No valid heart rate data found in FIT file")
        raise MissingDataError("No valid heart rate data found in FIT file")
        
    return sorted(heart_rate_data, key=lambda x: x[0])


def integrate_calories_over_intervals(heart_rate_data: List[Tuple[datetime, int]],
                                     weight: float,
                                     age: float,
                                     gender: str) -> float:
    """
    Integrate calories burned over heart rate intervals.
    
    Args:
        heart_rate_data: List of (timestamp, heart_rate) tuples sorted by timestamp
        weight: User's weight in kg
        age: User's age in years
        gender: User's gender ('male' or 'female')
        
    Returns:
        Total calories burned
        
    Raises:
        ValueError: If input parameters are invalid
        IndexError: If heart_rate_data has fewer than 2 entries
        TypeError: If input data types are incorrect
    """
    # Validate input parameters
    if not heart_rate_data:
        raise ValueError("Heart rate data cannot be empty")
    
    if len(heart_rate_data) < 2:
        raise ValueError("At least two heart rate data points are required")
        
    if not isinstance(weight, (int, float)) or weight <= 0:
        raise ValueError(f"Weight must be a positive number, got {weight}")
        
    if not isinstance(age, (int, float)) or age <= 0:
        raise ValueError(f"Age must be a positive number, got {age}")
        
    if not isinstance(gender, str) or gender.lower() not in ['male', 'female']:
        raise ValueError(f"Gender must be 'male' or 'female', got {gender}")
    
    total_calories = 0.0
    
    try:
        for i in range(1, len(heart_rate_data)):
            prev_ts, prev_hr = heart_rate_data[i - 1]
            curr_ts, curr_hr = heart_rate_data[i]
            
            # Validate timestamps
            if not isinstance(prev_ts, datetime) or not isinstance(curr_ts, datetime):
                raise TypeError("Timestamps must be datetime objects")
                
            # Check for negative time intervals
            if curr_ts <= prev_ts:
                logger.warning(f"Invalid time interval: {prev_ts} to {curr_ts}. Skipping.")
                continue
                
            delta_minutes = (curr_ts - prev_ts).total_seconds() / 60.0
            
            # Skip very short intervals
            if delta_minutes < 0.01:  # Less than 1 second
                logger.debug(f"Skipping very short interval: {delta_minutes} minutes")
                continue
                
            avg_hr = (prev_hr + curr_hr) / 2.0
            
            # Skip unrealistic heart rates
            if avg_hr <= 0 or avg_hr > 250:
                logger.warning(f"Unrealistic heart rate: {avg_hr}. Skipping.")
                continue
                
            interval_calories = calories_burned(avg_hr, delta_minutes, weight, age, gender)
            total_calories += interval_calories
            logger.debug(f"Interval: {delta_minutes:.2f} min, HR: {avg_hr:.1f}, Calories: {interval_calories:.2f}")
            
    except (TypeError, ValueError) as e:
        logger.error(f"Error calculating calories: {e}")
        raise
        
    return total_calories


def process_fit_file(file_path: str, weight: float, age: float, gender: str) -> float:
    """
    Process a single FIT file to compute the total calories burned.
    
    Args:
        file_path: Path to the FIT file
        weight: User's weight in kg
        age: User's age in years
        gender: User's gender ('male' or 'female')
        
    Returns:
        Total calories burned
        
    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If the file cannot be accessed due to permissions
        InvalidFitFileError: If the file is not a valid FIT file
        MissingDataError: If required data is missing from the file
        ValueError: If input parameters are invalid
    """
    import os
    
    # Validate input parameters
    if not isinstance(file_path, str) or not file_path:
        raise ValueError("File path must be a non-empty string")
        
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")
        
    if not os.path.isfile(file_path):
        logger.error(f"Not a file: {file_path}")
        raise ValueError(f"Not a file: {file_path}")
        
    if not os.access(file_path, os.R_OK):
        logger.error(f"Permission denied: {file_path}")
        raise PermissionError(f"Permission denied: {file_path}")
    
    try:
        fitfile = FitFile(file_path)
    except Exception as e:
        logger.error(f"Error opening FIT file {file_path}: {e}")
        raise InvalidFitFileError(f"Error opening FIT file: {e}") from e
    
    try:
        heart_rate_data = extract_heart_rate_data(fitfile)
        return integrate_calories_over_intervals(heart_rate_data, weight, age, gender)
    except MissingDataError:
        logger.error(f"No heart rate data found in {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error processing FIT file {file_path}: {e}")
        raise FitFileError(f"Error processing FIT file: {e}") from e