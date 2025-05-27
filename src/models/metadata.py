"""
Data models for FIT file metadata and device information.

This module contains dataclasses for representing metadata extracted
from FIT files, including activity information and device details.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class DeviceInfo:
    """
    Represents device information from a FIT file.
    
    Attributes:
        manufacturer: Device manufacturer name
        product: Product name or model
        serial_number: Device serial number
        software_version: Software/firmware version
        hardware_version: Hardware version
        device_type: Type of device (e.g., 'watch', 'bike_computer')
        battery_status: Battery status if available
    """
    manufacturer: Optional[str] = None
    product: Optional[str] = None
    serial_number: Optional[str] = None
    software_version: Optional[str] = None
    hardware_version: Optional[str] = None
    device_type: Optional[str] = None
    battery_status: Optional[str] = None
    
    def __post_init__(self):
        """Validate device info after initialization."""
        # Convert None values to proper types and validate non-None values
        if self.manufacturer is not None and not isinstance(self.manufacturer, str):
            raise TypeError("manufacturer must be a string or None")
            
        if self.product is not None and not isinstance(self.product, str):
            raise TypeError("product must be a string or None")
            
        if self.serial_number is not None and not isinstance(self.serial_number, str):
            raise TypeError("serial_number must be a string or None")
            
        if self.software_version is not None and not isinstance(self.software_version, str):
            raise TypeError("software_version must be a string or None")
            
        if self.hardware_version is not None and not isinstance(self.hardware_version, str):
            raise TypeError("hardware_version must be a string or None")
            
        if self.device_type is not None and not isinstance(self.device_type, str):
            raise TypeError("device_type must be a string or None")
            
        if self.battery_status is not None and not isinstance(self.battery_status, str):
            raise TypeError("battery_status must be a string or None")
    
    def is_complete(self) -> bool:
        """
        Check if device info has all essential information.
        
        Returns:
            True if manufacturer and product are available
        """
        return self.manufacturer is not None and self.product is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert device info to dictionary.
        
        Returns:
            Dictionary representation of device info
        """
        return {
            'manufacturer': self.manufacturer,
            'product': self.product,
            'serial_number': self.serial_number,
            'software_version': self.software_version,
            'hardware_version': self.hardware_version,
            'device_type': self.device_type,
            'battery_status': self.battery_status
        }


@dataclass
class FitFileMetadata:
    """
    Represents metadata extracted from a FIT file.
    
    Attributes:
        start_time: Activity start time
        end_time: Activity end time (optional)
        duration_seconds: Total duration in seconds
        sport: Primary sport/activity type
        sub_sport: Sub-sport/activity type
        total_distance: Total distance if available
        total_calories: Total calories from device if available
        avg_heart_rate: Average heart rate from device if available
        max_heart_rate: Maximum heart rate from device if available
        device_info: Device information
        file_path: Path to the FIT file
        file_size_bytes: Size of the FIT file in bytes
        created_timestamp: When the metadata was extracted
    """
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    sport: str = 'Unknown'
    sub_sport: str = 'Unknown'
    total_distance: Optional[float] = None
    total_calories: Optional[float] = None
    avg_heart_rate: Optional[float] = None
    max_heart_rate: Optional[float] = None
    device_info: Optional[DeviceInfo] = None
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    created_timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate metadata after initialization."""
        if self.start_time is not None and not isinstance(self.start_time, datetime):
            raise TypeError("start_time must be a datetime object or None")
            
        if self.end_time is not None and not isinstance(self.end_time, datetime):
            raise TypeError("end_time must be a datetime object or None")
            
        if not isinstance(self.duration_seconds, (int, float)):
            raise TypeError("duration_seconds must be a number")
        if self.duration_seconds < 0:
            raise ValueError("duration_seconds cannot be negative")
            
        if not isinstance(self.sport, str):
            raise TypeError("sport must be a string")
            
        if not isinstance(self.sub_sport, str):
            raise TypeError("sub_sport must be a string")
            
        if self.total_distance is not None:
            if not isinstance(self.total_distance, (int, float)):
                raise TypeError("total_distance must be a number or None")
            if self.total_distance < 0:
                raise ValueError("total_distance cannot be negative")
                
        if self.total_calories is not None:
            if not isinstance(self.total_calories, (int, float)):
                raise TypeError("total_calories must be a number or None")
            if self.total_calories < 0:
                raise ValueError("total_calories cannot be negative")
                
        if self.avg_heart_rate is not None:
            if not isinstance(self.avg_heart_rate, (int, float)):
                raise TypeError("avg_heart_rate must be a number or None")
            if self.avg_heart_rate <= 0:
                raise ValueError("avg_heart_rate must be positive")
                
        if self.max_heart_rate is not None:
            if not isinstance(self.max_heart_rate, (int, float)):
                raise TypeError("max_heart_rate must be a number or None")
            if self.max_heart_rate <= 0:
                raise ValueError("max_heart_rate must be positive")
                
        if self.device_info is not None and not isinstance(self.device_info, DeviceInfo):
            raise TypeError("device_info must be a DeviceInfo instance or None")
            
        if self.file_path is not None and not isinstance(self.file_path, str):
            raise TypeError("file_path must be a string or None")
            
        if self.file_size_bytes is not None:
            if not isinstance(self.file_size_bytes, int):
                raise TypeError("file_size_bytes must be an integer or None")
            if self.file_size_bytes < 0:
                raise ValueError("file_size_bytes cannot be negative")
                
        if self.created_timestamp is not None and not isinstance(self.created_timestamp, datetime):
            raise TypeError("created_timestamp must be a datetime object or None")
            
        # Validate time consistency
        if (self.start_time is not None and self.end_time is not None and 
            self.end_time <= self.start_time):
            raise ValueError("end_time must be after start_time")
    
    def calculate_duration_from_times(self) -> float:
        """
        Calculate duration from start and end times.
        
        Returns:
            Duration in seconds, or 0 if times are not available
        """
        if self.start_time is not None and self.end_time is not None:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def is_complete(self) -> bool:
        """
        Check if metadata has essential information.
        
        Returns:
            True if start_time and duration are available
        """
        return (self.start_time is not None and 
                (self.duration_seconds > 0 or self.end_time is not None))
    
    def get_activity_name(self) -> str:
        """
        Get a formatted activity name.
        
        Returns:
            Formatted activity name combining sport and sub_sport
        """
        if self.sub_sport != 'Unknown' and self.sub_sport != self.sport:
            return f"{self.sport} - {self.sub_sport}"
        return self.sport
    
    def get_duration_formatted(self) -> str:
        """
        Get formatted duration string.
        
        Returns:
            Duration formatted as "Xh Ym" or "Ym" or "Xs"
        """
        if self.duration_seconds == 0:
            return "0s"
            
        hours = int(self.duration_seconds // 3600)
        minutes = int((self.duration_seconds % 3600) // 60)
        seconds = int(self.duration_seconds % 60)
        
        if hours > 0:
            if minutes > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{hours}h"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return f"{seconds}s"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metadata to dictionary.
        
        Returns:
            Dictionary representation of metadata
        """
        return {
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.duration_seconds,
            'sport': self.sport,
            'sub_sport': self.sub_sport,
            'total_distance': self.total_distance,
            'total_calories': self.total_calories,
            'avg_heart_rate': self.avg_heart_rate,
            'max_heart_rate': self.max_heart_rate,
            'device_info': self.device_info.to_dict() if self.device_info else None,
            'file_path': self.file_path,
            'file_size_bytes': self.file_size_bytes,
            'created_timestamp': self.created_timestamp.isoformat() if self.created_timestamp else None,
            'activity_name': self.get_activity_name(),
            'duration_formatted': self.get_duration_formatted(),
            'is_complete': self.is_complete()
        }


def create_metadata_from_dict(metadata_dict: Dict[str, Any]) -> FitFileMetadata:
    """
    Create FitFileMetadata from a dictionary (e.g., from file_manager.extract_fit_file_metadata).
    
    Args:
        metadata_dict: Dictionary containing metadata fields
        
    Returns:
        FitFileMetadata object
        
    Raises:
        TypeError: If metadata_dict is not a dictionary
    """
    if not isinstance(metadata_dict, dict):
        raise TypeError("metadata_dict must be a dictionary")
    
    # Extract and convert values with defaults
    start_time = metadata_dict.get('start_time')
    duration_seconds = metadata_dict.get('duration_seconds', 0)
    sport = metadata_dict.get('activity_type', 'Unknown')
    sub_sport = metadata_dict.get('sub_activity_type', 'Unknown')
    
    # Create metadata object
    metadata = FitFileMetadata(
        start_time=start_time,
        duration_seconds=float(duration_seconds) if duration_seconds else 0.0,
        sport=sport,
        sub_sport=sub_sport,
        created_timestamp=datetime.now()
    )
    
    return metadata


def merge_metadata(base_metadata: FitFileMetadata, additional_data: Dict[str, Any]) -> FitFileMetadata:
    """
    Merge additional data into existing metadata.
    
    Args:
        base_metadata: Base FitFileMetadata object
        additional_data: Dictionary of additional data to merge
        
    Returns:
        New FitFileMetadata object with merged data
        
    Raises:
        TypeError: If inputs are not of correct types
    """
    if not isinstance(base_metadata, FitFileMetadata):
        raise TypeError("base_metadata must be a FitFileMetadata instance")
        
    if not isinstance(additional_data, dict):
        raise TypeError("additional_data must be a dictionary")
    
    # Create a copy of the base metadata as a dict
    merged_dict = base_metadata.to_dict()
    
    # Update with additional data
    for key, value in additional_data.items():
        if key in merged_dict:
            merged_dict[key] = value
    
    # Convert back to FitFileMetadata
    # Note: This is a simplified conversion - in practice you might want more sophisticated merging
    return create_metadata_from_dict(merged_dict)