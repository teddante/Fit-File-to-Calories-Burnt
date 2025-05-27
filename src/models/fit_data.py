"""
Data models for FIT file processing and calorie calculations.

This module contains dataclasses for representing heart rate data,
calorie calculation results, and processing outcomes.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple, Optional, Any


@dataclass
class HeartRateData:
    """
    Represents heart rate data from a FIT file.
    
    Attributes:
        timestamp: The datetime when the heart rate was recorded
        heart_rate: Heart rate in beats per minute
        interval_minutes: Duration of this data point in minutes (optional)
    """
    timestamp: datetime
    heart_rate: int
    interval_minutes: Optional[float] = None
    
    def __post_init__(self):
        """Validate heart rate data after initialization."""
        if not isinstance(self.timestamp, datetime):
            raise TypeError("timestamp must be a datetime object")
        
        if not isinstance(self.heart_rate, (int, float)):
            raise TypeError("heart_rate must be a number")
            
        if self.heart_rate <= 0:
            raise ValueError("heart_rate must be positive")
            
        if self.heart_rate > 250:
            raise ValueError("heart_rate exceeds physiological maximum (250 bpm)")
            
        if self.interval_minutes is not None:
            if not isinstance(self.interval_minutes, (int, float)):
                raise TypeError("interval_minutes must be a number")
            if self.interval_minutes < 0:
                raise ValueError("interval_minutes cannot be negative")


@dataclass
class CalorieData:
    """
    Represents calorie calculation results.
    
    Attributes:
        total_calories: Total calories burned
        average_heart_rate: Average heart rate during the activity
        duration_minutes: Total duration of the activity in minutes
        weight: User's weight in kg used for calculation
        age: User's age in years used for calculation
        gender: User's gender used for calculation
        intervals_processed: Number of heart rate intervals processed
    """
    total_calories: float
    average_heart_rate: float
    duration_minutes: float
    weight: float
    age: float
    gender: str
    intervals_processed: int
    
    def __post_init__(self):
        """Validate calorie data after initialization."""
        if not isinstance(self.total_calories, (int, float)):
            raise TypeError("total_calories must be a number")
        if self.total_calories < 0:
            raise ValueError("total_calories cannot be negative")
            
        if not isinstance(self.average_heart_rate, (int, float)):
            raise TypeError("average_heart_rate must be a number")
        if self.average_heart_rate <= 0:
            raise ValueError("average_heart_rate must be positive")
            
        if not isinstance(self.duration_minutes, (int, float)):
            raise TypeError("duration_minutes must be a number")
        if self.duration_minutes < 0:
            raise ValueError("duration_minutes cannot be negative")
            
        if not isinstance(self.weight, (int, float)):
            raise TypeError("weight must be a number")
        if self.weight <= 0:
            raise ValueError("weight must be positive")
            
        if not isinstance(self.age, (int, float)):
            raise TypeError("age must be a number")
        if self.age <= 0:
            raise ValueError("age must be positive")
            
        if not isinstance(self.gender, str):
            raise TypeError("gender must be a string")
        if self.gender.lower() not in ['male', 'female']:
            raise ValueError("gender must be 'male' or 'female'")
            
        if not isinstance(self.intervals_processed, int):
            raise TypeError("intervals_processed must be an integer")
        if self.intervals_processed < 0:
            raise ValueError("intervals_processed cannot be negative")


@dataclass
class ProcessingResult:
    """
    Represents the complete result of FIT file processing.
    
    Attributes:
        file_path: Path to the processed FIT file
        success: Whether processing was successful
        calorie_data: CalorieData object if successful, None otherwise
        heart_rate_data: List of HeartRateData objects
        error_message: Error message if processing failed
        processing_time_seconds: Time taken to process the file
        metadata: Additional metadata from processing
    """
    file_path: str
    success: bool
    calorie_data: Optional[CalorieData] = None
    heart_rate_data: Optional[List[HeartRateData]] = None
    error_message: Optional[str] = None
    processing_time_seconds: Optional[float] = None
    metadata: Optional[dict] = None
    
    def __post_init__(self):
        """Validate processing result after initialization."""
        if not isinstance(self.file_path, str):
            raise TypeError("file_path must be a string")
        if not self.file_path:
            raise ValueError("file_path cannot be empty")
            
        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean")
            
        if self.success and self.calorie_data is None:
            raise ValueError("calorie_data must be provided when success is True")
            
        if not self.success and self.error_message is None:
            raise ValueError("error_message must be provided when success is False")
            
        if self.calorie_data is not None and not isinstance(self.calorie_data, CalorieData):
            raise TypeError("calorie_data must be a CalorieData instance")
            
        if self.heart_rate_data is not None:
            if not isinstance(self.heart_rate_data, list):
                raise TypeError("heart_rate_data must be a list")
            for item in self.heart_rate_data:
                if not isinstance(item, HeartRateData):
                    raise TypeError("All items in heart_rate_data must be HeartRateData instances")
                    
        if self.processing_time_seconds is not None:
            if not isinstance(self.processing_time_seconds, (int, float)):
                raise TypeError("processing_time_seconds must be a number")
            if self.processing_time_seconds < 0:
                raise ValueError("processing_time_seconds cannot be negative")


def create_heart_rate_data_from_tuples(data_tuples: List[Tuple[datetime, int]]) -> List[HeartRateData]:
    """
    Convert a list of (timestamp, heart_rate) tuples to HeartRateData objects.
    
    Args:
        data_tuples: List of (timestamp, heart_rate) tuples
        
    Returns:
        List of HeartRateData objects
        
    Raises:
        TypeError: If input is not a list or contains invalid tuples
        ValueError: If heart rate values are invalid
    """
    if not isinstance(data_tuples, list):
        raise TypeError("data_tuples must be a list")
        
    heart_rate_data = []
    for i, item in enumerate(data_tuples):
        if not isinstance(item, tuple) or len(item) != 2:
            raise TypeError(f"Item {i} must be a tuple of length 2")
            
        timestamp, heart_rate = item
        heart_rate_data.append(HeartRateData(timestamp=timestamp, heart_rate=heart_rate))
        
    return heart_rate_data


def calculate_average_heart_rate(heart_rate_data: List[HeartRateData]) -> float:
    """
    Calculate the average heart rate from a list of HeartRateData objects.
    
    Args:
        heart_rate_data: List of HeartRateData objects
        
    Returns:
        Average heart rate
        
    Raises:
        ValueError: If the list is empty
        TypeError: If input is not a list of HeartRateData objects
    """
    if not isinstance(heart_rate_data, list):
        raise TypeError("heart_rate_data must be a list")
        
    if not heart_rate_data:
        raise ValueError("heart_rate_data cannot be empty")
        
    for item in heart_rate_data:
        if not isinstance(item, HeartRateData):
            raise TypeError("All items must be HeartRateData instances")
            
    total_hr = sum(data.heart_rate for data in heart_rate_data)
    return total_hr / len(heart_rate_data)


def calculate_total_duration(heart_rate_data: List[HeartRateData]) -> float:
    """
    Calculate the total duration from a list of HeartRateData objects.
    
    Args:
        heart_rate_data: List of HeartRateData objects sorted by timestamp
        
    Returns:
        Total duration in minutes
        
    Raises:
        ValueError: If the list has fewer than 2 items
        TypeError: If input is not a list of HeartRateData objects
    """
    if not isinstance(heart_rate_data, list):
        raise TypeError("heart_rate_data must be a list")
        
    if len(heart_rate_data) < 2:
        raise ValueError("At least 2 heart rate data points are required")
        
    for item in heart_rate_data:
        if not isinstance(item, HeartRateData):
            raise TypeError("All items must be HeartRateData instances")
            
    # Sort by timestamp to ensure correct calculation
    sorted_data = sorted(heart_rate_data, key=lambda x: x.timestamp)
    start_time = sorted_data[0].timestamp
    end_time = sorted_data[-1].timestamp
    
    return (end_time - start_time).total_seconds() / 60.0