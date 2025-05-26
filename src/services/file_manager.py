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

# Get logger for this module
logger = get_logger(__name__)


def extract_fit_file_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extracts relevant metadata from a FIT file.
    
    Args:
        file_path: Path to the FIT file.
        
    Returns:
        A dictionary containing extracted metadata:
        - 'start_time': datetime object of the activity start.
        - 'duration_seconds': Total duration of the activity in seconds.
        - 'activity_type': Sport type (e.g., 'running', 'cycling').
        - 'sub_activity_type': Sub-sport type (e.g., 'treadmill', 'road').
    """
    metadata = {
        'start_time': None,
        'duration_seconds': 0,
        'activity_type': 'Unknown',
        'sub_activity_type': 'Unknown'
    }
    
    try:
        fitfile = FitFile(file_path)
        
        # Try to get data from session messages first
        session_messages = list(fitfile.get_messages('session'))
        if session_messages:
            session = session_messages[0] # Assuming one session per file for simplicity
            for field in session:
                if field.name == 'start_time':
                    metadata['start_time'] = field.value
                elif field.name == 'total_elapsed_time':
                    metadata['duration_seconds'] = field.value
                elif field.name == 'sport':
                    metadata['activity_type'] = str(field.value).replace('_', ' ').title()
                elif field.name == 'sub_sport':
                    metadata['sub_activity_type'] = str(field.value).replace('_', ' ').title()
        
        # Fallback to record messages for start_time and duration if session data is missing
        if metadata['start_time'] is None or metadata['duration_seconds'] == 0:
            record_timestamps = []
            for record in fitfile.get_messages('record'):
                for field in record:
                    if field.name == 'timestamp':
                        record_timestamps.append(field.value)
            
            if record_timestamps:
                record_timestamps.sort()
                if metadata['start_time'] is None:
                    metadata['start_time'] = record_timestamps[0]
                if metadata['duration_seconds'] == 0 and len(record_timestamps) > 1:
                    metadata['duration_seconds'] = (record_timestamps[-1] - record_timestamps[0]).total_seconds()
                    
    except Exception as e:
        logger.error(f"Error extracting metadata from {file_path}: {e}")
        # Keep default metadata values in case of error
        
    return metadata


def rename_fit_file(original_file_path: str, metadata: Dict[str, Any]) -> Optional[str]:
    """
    Renames a FIT file based on extracted metadata.
    
    Args:
        original_file_path: The current path of the FIT file.
        metadata: Dictionary containing 'start_time', 'duration_seconds', 'activity_type'.
        
    Returns:
        The new file path if successful, None otherwise.
    """
    directory, original_filename = os.path.split(original_file_path)
    
    start_time = metadata.get('start_time')
    activity_type = metadata.get('activity_type', 'Unknown')
    duration_seconds = metadata.get('duration_seconds', 0)
    
    if start_time is None:
        logger.warning(f"Could not determine start time for {original_filename}. Skipping rename.")
        return None
        
    # Format date and time
    date_str = start_time.strftime('%Y-%m-%d')
    time_str = start_time.strftime('%H%M')
    
    # Format duration
    hours = int(duration_seconds // 3600)
    minutes = int((duration_seconds % 3600) // 60)
    
    duration_str = ""
    if hours > 0:
        duration_str += f"{hours}h"
    if minutes > 0 or (hours == 0 and duration_seconds > 0): # Show minutes even if 0 if total duration > 0
        duration_str += f"{minutes}m"
    if not duration_str and duration_seconds == 0:
        duration_str = "0m" # For activities with no recorded duration

    # Construct new filename
    new_filename_base = f"{date_str}_{time_str}_{activity_type}"
    if duration_str:
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