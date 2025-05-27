"""
File management service module.

This module contains functions for managing FIT files, including metadata extraction
and file renaming operations.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fitparse import FitFile
from src.core.logger import get_logger
from src.models.metadata import FitFileMetadata, DeviceInfo, create_metadata_from_dict

# Get logger for this module
logger = get_logger(__name__)


def extract_fit_file_metadata(file_path: str) -> FitFileMetadata:
    """
    Extracts relevant metadata from a FIT file.
    
    Args:
        file_path: Path to the FIT file.
        
    Returns:
        FitFileMetadata object containing extracted metadata
    """
    # Initialize metadata with defaults
    metadata = FitFileMetadata(
        file_path=file_path,
        created_timestamp=datetime.now()
    )
    
    try:
        # Get file size
        if os.path.exists(file_path):
            metadata.file_size_bytes = os.path.getsize(file_path)
        
        fitfile = FitFile(file_path)
        
        # Extract device information
        device_info = DeviceInfo()
        device_messages = list(fitfile.get_messages('device_info'))
        if device_messages:
            device = device_messages[0]  # Use first device
            for field in device:
                if field.name == 'manufacturer':
                    device_info.manufacturer = str(field.value) if field.value else None
                elif field.name == 'product':
                    device_info.product = str(field.value) if field.value else None
                elif field.name == 'serial_number':
                    device_info.serial_number = str(field.value) if field.value else None
                elif field.name == 'software_version':
                    device_info.software_version = str(field.value) if field.value else None
                elif field.name == 'hardware_version':
                    device_info.hardware_version = str(field.value) if field.value else None
                elif field.name == 'device_type':
                    device_info.device_type = str(field.value) if field.value else None
                elif field.name == 'battery_status':
                    device_info.battery_status = str(field.value) if field.value else None
        
        metadata.device_info = device_info
        
        # Try to get data from session messages first
        session_messages = list(fitfile.get_messages('session'))
        if session_messages:
            session = session_messages[0]  # Assuming one session per file for simplicity
            for field in session:
                if field.name == 'start_time':
                    metadata.start_time = field.value
                elif field.name == 'total_elapsed_time':
                    metadata.duration_seconds = float(field.value) if field.value else 0.0
                elif field.name == 'sport':
                    metadata.sport = str(field.value).replace('_', ' ').title() if field.value else 'Unknown'
                elif field.name == 'sub_sport':
                    metadata.sub_sport = str(field.value).replace('_', ' ').title() if field.value else 'Unknown'
                elif field.name == 'total_distance':
                    metadata.total_distance = float(field.value) if field.value else None
                elif field.name == 'total_calories':
                    metadata.total_calories = float(field.value) if field.value else None
                elif field.name == 'avg_heart_rate':
                    metadata.avg_heart_rate = float(field.value) if field.value else None
                elif field.name == 'max_heart_rate':
                    metadata.max_heart_rate = float(field.value) if field.value else None
        
        # Fallback to record messages for start_time and duration if session data is missing
        if metadata.start_time is None or metadata.duration_seconds == 0:
            record_timestamps = []
            for record in fitfile.get_messages('record'):
                for field in record:
                    if field.name == 'timestamp':
                        record_timestamps.append(field.value)
            
            if record_timestamps:
                record_timestamps.sort()
                if metadata.start_time is None:
                    metadata.start_time = record_timestamps[0]
                if metadata.duration_seconds == 0 and len(record_timestamps) > 1:
                    metadata.duration_seconds = (record_timestamps[-1] - record_timestamps[0]).total_seconds()
                    metadata.end_time = record_timestamps[-1]
                    
    except Exception as e:
        logger.error(f"Error extracting metadata from {file_path}: {e}")
        # Keep default metadata values in case of error
        
    return metadata


def rename_fit_file(original_file_path: str, metadata: FitFileMetadata) -> Optional[str]:
    """
    Renames a FIT file based on extracted metadata.
    
    Args:
        original_file_path: The current path of the FIT file.
        metadata: FitFileMetadata object containing metadata.
        
    Returns:
        The new file path if successful, None otherwise.
    """
    directory, original_filename = os.path.split(original_file_path)
    
    if metadata.start_time is None:
        logger.warning(f"Could not determine start time for {original_filename}. Skipping rename.")
        return None
        
    # Format date and time
    date_str = metadata.start_time.strftime('%Y-%m-%d')
    time_str = metadata.start_time.strftime('%H%M')
    
    # Use the formatted activity name from metadata
    activity_type = metadata.get_activity_name()
    
    # Format duration using the metadata method
    duration_str = metadata.get_duration_formatted()
    
    # Construct new filename
    new_filename_base = f"{date_str}_{time_str}_{activity_type}"
    if duration_str and duration_str != "0s":
        new_filename_base += f"_{duration_str}"
        
    new_filename = f"{new_filename_base}.fit"
    new_file_path = os.path.join(directory, new_filename)
    
    # Handle potential naming conflicts
    counter = 1
    while os.path.exists(new_file_path) and new_file_path != original_file_path:
        new_filename = f"{new_filename_base}_{counter}.fit"
        new_file_path = os.path.join(directory, new_filename)
        counter += 1
        
    try:
        if original_file_path != new_file_path:
            os.rename(original_file_path, new_file_path)
            logger.info(f"Renamed '{original_filename}' to '{new_filename}'")
            return new_file_path
        else:
            logger.info(f"File '{original_filename}' already has the desired name. No rename needed.")
            return original_file_path
    except Exception as e:
        logger.error(f"Error renaming file '{original_filename}' to '{new_filename}': {e}")
        return None


def extract_fit_file_metadata_legacy(file_path: str) -> Dict[str, Any]:
    """
    Legacy function that returns metadata as a dictionary for backward compatibility.
    
    Args:
        file_path: Path to the FIT file.
        
    Returns:
        A dictionary containing extracted metadata for backward compatibility.
    """
    metadata_obj = extract_fit_file_metadata(file_path)
    
    # Convert to legacy format
    return {
        'start_time': metadata_obj.start_time,
        'duration_seconds': metadata_obj.duration_seconds,
        'activity_type': metadata_obj.sport,
        'sub_activity_type': metadata_obj.sub_sport
    }