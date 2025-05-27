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
from src.models.fit_data import HeartRateData, CalorieData, ProcessingResult, create_heart_rate_data_from_tuples, calculate_average_heart_rate, calculate_total_duration
from src.validators.input_validator import validate_heart_rate_data, validate_calculation_inputs
from src.exceptions import FitFileError, InvalidFitFileError, MissingDataError, InputValidationError

# Get logger for this module
logger = get_logger(__name__)


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
                                     gender: str) -> CalorieData:
    """
    Integrate calories burned over heart rate intervals.
    
    Args:
        heart_rate_data: List of (timestamp, heart_rate) tuples sorted by timestamp
        weight: User's weight in kg
        age: User's age in years
        gender: User's gender ('male' or 'female')
        
    Returns:
        CalorieData object containing calculation results
        
    Raises:
        InputValidationError: If input parameters are invalid
        ValueError: If heart_rate_data has fewer than 2 entries
        TypeError: If input data types are incorrect
    """
    # Validate input parameters using validators
    try:
        validated_inputs = validate_calculation_inputs(
            weight=weight,
            age=age,
            gender=gender
        )
        weight = validated_inputs['weight']
        age = validated_inputs['age']
        gender = validated_inputs['gender']
    except InputValidationError as e:
        raise ValueError(f"Input validation failed: {e}") from e
    
    # Validate heart rate data
    try:
        validated_hr_data = validate_heart_rate_data(heart_rate_data)
    except InputValidationError as e:
        raise ValueError(f"Heart rate data validation failed: {e}") from e
    
    if len(validated_hr_data) < 2:
        raise ValueError("At least two heart rate data points are required")
    
    total_calories = 0.0
    intervals_processed = 0
    
    try:
        for i in range(1, len(validated_hr_data)):
            prev_ts, prev_hr = validated_hr_data[i - 1]
            curr_ts, curr_hr = validated_hr_data[i]
            
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
            
            # Skip unrealistic heart rates (additional check beyond validation)
            if avg_hr <= 0 or avg_hr > 250:
                logger.warning(f"Unrealistic heart rate: {avg_hr}. Skipping.")
                continue
                
            interval_calories = calories_burned(avg_hr, delta_minutes, weight, age, gender)
            total_calories += interval_calories
            intervals_processed += 1
            logger.debug(f"Interval: {delta_minutes:.2f} min, HR: {avg_hr:.1f}, Calories: {interval_calories:.2f}")
            
    except (TypeError, ValueError) as e:
        logger.error(f"Error calculating calories: {e}")
        raise
    
    # Calculate statistics
    heart_rates = [hr for _, hr in validated_hr_data]
    average_heart_rate = sum(heart_rates) / len(heart_rates)
    duration_minutes = calculate_total_duration(create_heart_rate_data_from_tuples(validated_hr_data))
    
    # Create and return CalorieData object
    return CalorieData(
        total_calories=total_calories,
        average_heart_rate=average_heart_rate,
        duration_minutes=duration_minutes,
        weight=weight,
        age=age,
        gender=gender,
        intervals_processed=intervals_processed
    )


def process_fit_file(file_path: str, weight: float, age: float, gender: str) -> ProcessingResult:
    """
    Process a single FIT file to compute the total calories burned.
    
    Args:
        file_path: Path to the FIT file
        weight: User's weight in kg
        age: User's age in years
        gender: User's gender ('male' or 'female')
        
    Returns:
        ProcessingResult object containing all processing results
        
    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If the file cannot be accessed due to permissions
        InvalidFitFileError: If the file is not a valid FIT file
        MissingDataError: If required data is missing from the file
        ValueError: If input parameters are invalid
    """
    import os
    import time
    from src.validators.input_validator import validate_file_path
    
    start_time = time.time()
    
    try:
        # Validate input parameters
        validated_file_path = validate_file_path(file_path)
        
        # Validate physiological parameters
        validated_inputs = validate_calculation_inputs(
            weight=weight,
            age=age,
            gender=gender
        )
        
        if not os.path.exists(validated_file_path):
            logger.error(f"File not found: {validated_file_path}")
            raise FileNotFoundError(f"File not found: {validated_file_path}")
            
        if not os.path.isfile(validated_file_path):
            logger.error(f"Not a file: {validated_file_path}")
            raise ValueError(f"Not a file: {validated_file_path}")
            
        if not os.access(validated_file_path, os.R_OK):
            logger.error(f"Permission denied: {validated_file_path}")
            raise PermissionError(f"Permission denied: {validated_file_path}")
        
        try:
            fitfile = FitFile(validated_file_path)
        except Exception as e:
            logger.error(f"Error opening FIT file {validated_file_path}: {e}")
            raise InvalidFitFileError(f"Error opening FIT file: {e}") from e
        
        try:
            heart_rate_data_tuples = extract_heart_rate_data(fitfile)
            heart_rate_data_objects = create_heart_rate_data_from_tuples(heart_rate_data_tuples)
            calorie_data = integrate_calories_over_intervals(
                heart_rate_data_tuples,
                validated_inputs['weight'],
                validated_inputs['age'],
                validated_inputs['gender']
            )
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                file_path=validated_file_path,
                success=True,
                calorie_data=calorie_data,
                heart_rate_data=heart_rate_data_objects,
                processing_time_seconds=processing_time,
                metadata={'file_size_bytes': os.path.getsize(validated_file_path)}
            )
            
        except MissingDataError as e:
            logger.error(f"No heart rate data found in {validated_file_path}")
            processing_time = time.time() - start_time
            return ProcessingResult(
                file_path=validated_file_path,
                success=False,
                error_message=f"No heart rate data found: {e}",
                processing_time_seconds=processing_time
            )
        except Exception as e:
            logger.error(f"Error processing FIT file {validated_file_path}: {e}")
            processing_time = time.time() - start_time
            return ProcessingResult(
                file_path=validated_file_path,
                success=False,
                error_message=f"Error processing FIT file: {e}",
                processing_time_seconds=processing_time
            )
            
    except (InputValidationError, ValueError, FileNotFoundError, PermissionError, InvalidFitFileError) as e:
        processing_time = time.time() - start_time
        return ProcessingResult(
            file_path=file_path,
            success=False,
            error_message=str(e),
            processing_time_seconds=processing_time
        )
    except Exception as e:
        logger.error(f"Unexpected error processing {file_path}: {e}")
        processing_time = time.time() - start_time
        return ProcessingResult(
            file_path=file_path,
            success=False,
            error_message=f"Unexpected error: {e}",
            processing_time_seconds=processing_time
        )