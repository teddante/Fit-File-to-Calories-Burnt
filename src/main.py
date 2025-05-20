import os
import glob
import json
from fitparse import FitFile
from datetime import datetime, timedelta
import logging
from typing import List, Tuple, Optional, Dict, Any
from src.core.logger import get_logger
from src.core.utils import load_config, calories_burned, calculate_karvonen_zones

# Get logger for this module
logger = get_logger(__name__)

# Determine the project root directory dynamically
# This assumes the script is run from within the project structure
# src/main.py -> src/ -> project_root/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Custom exceptions for specific error scenarios
class FitFileError(Exception):
    """Base exception for FIT file processing errors."""
    pass

class InvalidFitFileError(FitFileError):
    """Exception raised when a FIT file is invalid or corrupted."""
    pass

class MissingDataError(FitFileError):
    """Exception raised when required data is missing from a FIT file."""
    pass

class ConfigError(Exception):
    """Exception raised for configuration-related errors."""
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

def load_user_config() -> Dict[str, Any]:
    """
    Load and validate user configuration from config file.
    
    Returns:
        Dictionary with validated configuration values
        
    Raises:
        ConfigError: If the configuration file is missing, invalid, or contains invalid values
    """
    try:
        config = load_config(os.path.join(project_root, 'config', 'config.json'))
    except FileNotFoundError as e:
        logger.error("Configuration file not found")
        raise ConfigError("Configuration file not found") from e
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {e}")
        raise ConfigError(f"Invalid JSON in configuration file: {e}") from e
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise ConfigError(f"Error loading configuration: {e}") from e
    
    # Extract and validate configuration values
    try:
        weight = config.get('weight_kg', 70)
        if not isinstance(weight, (int, float)) or weight <= 0:
            logger.warning(f"Invalid weight in config: {weight}. Using default 70kg.")
            weight = 70
            
        age = config.get('age_years', 30)
        if not isinstance(age, (int, float)) or age <= 0:
            logger.warning(f"Invalid age in config: {age}. Using default 30 years.")
            age = 30
            
        gender = config.get('gender', 'male')
        if not isinstance(gender, str) or gender.lower() not in ['male', 'female']:
            logger.warning(f"Invalid gender in config: {gender}. Using default 'male'.")
            gender = 'male'
            
        return {
            'weight_kg': weight,
            'age_years': age,
            'gender': gender.lower()
        }
        
    except Exception as e:
        logger.error(f"Error validating configuration: {e}")
        raise ConfigError(f"Error validating configuration: {e}") from e

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

def prompt_int(prompt_message: str) -> Optional[int]:
    """Prompts the user for an integer input."""
    while True:
        try:
            value = input(prompt_message).strip()
            if not value:
                return None
            return int(value)
        except ValueError:
            print("Invalid input. Please enter a whole number.")

def main():
    """
    Main function to provide calculator options to the user.
    """
    try:
        while True:
            print("\nSelect a calculator option:")
            print("1. Calculate Calories from FIT file")
            print("2. Calculate Karvonen Heart Rate Zones")
            print("3. Clean up FIT file names")
            print("4. Exit")

            choice = input("Enter your choice (1, 2, 3, or 4): ").strip()

            if choice == '1':
                process_fit_files_option()
            elif choice == '2':
                calculate_karvonen_zones_option()
            elif choice == '3':
                clean_up_fit_file_names_option()
            elif choice == '4':
                print("Exiting program.")
                break
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")

    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        print(f"Critical error: {e}")

def process_fit_files_option():
    """
    Handles the option to process FIT files and calculate calories burned.
    """
    try:
        # Load configuration from file
        try:
            config = load_user_config()
            weight = config['weight_kg']
            age = config['age_years']
            gender = config['gender']
            
            logger.info(f"Using configuration: weight={weight}kg, age={age}yrs, gender={gender}")
        except ConfigError as e:
            logger.error(f"Configuration error: {e}")
            print(f"Configuration error: {e}")
            print("Using default values: weight=70kg, age=30yrs, gender=male")
            weight = 70
            age = 30
            gender = 'male'
        
        # Define the directory containing the FIT files: <repo_directory>/fitfiles
        try:
            fit_directory = os.path.join(project_root, 'data', 'fitfiles')
            
            if not os.path.exists(fit_directory):
                logger.warning(f"Fitfiles directory not found: {fit_directory}")
                print(f"Fitfiles directory not found: {fit_directory}")
                try:
                    os.makedirs(fit_directory)
                    logger.info(f"Created fitfiles directory: {fit_directory}")
                    print(f"Created fitfiles directory: {fit_directory}")
                except Exception as e:
                    logger.error(f"Failed to create fitfiles directory: {e}")
                    print(f"Failed to create fitfiles directory: {e}")
                    return
            
            # Find all .fit files in the 'fitfiles' folder
            fit_files = glob.glob(os.path.join(fit_directory, '*.fit'))
            
            if not fit_files:
                logger.warning(f"No .fit files found in directory: {fit_directory}")
                print("No .fit files found in directory:", fit_directory)
                return
    
            logger.info(f"Found {len(fit_files)} .fit files to process")
            
            # Process each file and print its estimated calorie burn
            processed_count = 0
            error_count = 0
            
            for file_path in fit_files:
                try:
                    logger.info(f"Processing file: {os.path.basename(file_path)}")
                    total_calories = process_fit_file(file_path, weight, age, gender)
                    print(f"File: {os.path.basename(file_path)} - Total calories burned (estimated): {total_calories:.2f} kcal")
                    logger.info(f"Calories burned: {total_calories:.2f} kcal")
                    processed_count += 1
                except FileNotFoundError as e:
                    error_msg = f"File not found: {os.path.basename(file_path)}"
                    logger.error(error_msg)
                    print(error_msg)
                    error_count += 1
                except PermissionError as e:
                    error_msg = f"Permission denied: {os.path.basename(file_path)}"
                    logger.error(error_msg)
                    print(error_msg)
                    error_count += 1
                except InvalidFitFileError as e:
                    error_msg = f"Invalid FIT file {os.path.basename(file_path)}: {e}"
                    logger.error(error_msg)
                    print(error_msg)
                    error_count += 1
                except MissingDataError as e:
                    error_msg = f"Missing data in {os.path.basename(file_path)}: {e}"
                    logger.error(error_msg)
                    print(error_msg)
                    error_count += 1
                except Exception as e:
                    error_msg = f"Error processing file {os.path.basename(file_path)}: {e}"
                    logger.error(error_msg)
                    print(error_msg)
                    error_count += 1
            
            logger.info(f"Processing complete. Processed {processed_count} files successfully, {error_count} files with errors.")
            if processed_count > 0:
                print(f"\nProcessing complete. Processed {processed_count} files successfully.")
            if error_count > 0:
                print(f"Encountered errors in {error_count} files. Check the log for details.")
                
        except Exception as e:
            logger.error(f"Error finding or processing FIT files: {e}")
            print(f"Error finding or processing FIT files: {e}")
            
    except Exception as e:
        logger.critical(f"Unhandled exception in process_fit_files_option: {e}")
        print(f"An unexpected error occurred: {e}")

def clean_up_fit_file_names_option():
    """
    Handles the option to clean up FIT file names based on extracted metadata.
    """
    print("\n--- Cleaning up FIT file names ---")
    try:
        fit_directory = os.path.join(project_root, 'data', 'fitfiles')
        
        if not os.path.exists(fit_directory):
            logger.warning(f"Fitfiles directory not found: {fit_directory}")
            print(f"Fitfiles directory not found: {fit_directory}")
            return
            
        fit_files = glob.glob(os.path.join(fit_directory, '*.fit'))
        
        if not fit_files:
            logger.warning(f"No .fit files found in directory: {fit_directory}")
            print("No .fit files found in directory:", fit_directory)
            return
            
        logger.info(f"Found {len(fit_files)} .fit files to clean up.")
        
        renamed_count = 0
        error_count = 0
        
        for file_path in fit_files:
            original_filename = os.path.basename(file_path)
            try:
                logger.info(f"Extracting metadata for {original_filename}")
                metadata = extract_fit_file_metadata(file_path)
                
                new_file_path = rename_fit_file(file_path, metadata)
                
                if new_file_path:
                    renamed_count += 1
                else:
                    error_count += 1
            except Exception as e:
                logger.error(f"Error cleaning up file {original_filename}: {e}")
                print(f"Error cleaning up file {original_filename}: {e}")
                error_count += 1
                
        logger.info(f"File cleanup complete. Renamed {renamed_count} files, {error_count} errors.")
        if renamed_count > 0:
            print(f"\nFile cleanup complete. Renamed {renamed_count} files successfully.")
        if error_count > 0:
            print(f"Encountered errors in {error_count} files. Check the log for details.")
            
    except Exception as e:
        logger.critical(f"Unhandled exception in clean_up_fit_file_names_option: {e}")
        print(f"An unexpected error occurred: {e}")

def calculate_karvonen_zones_option():
    """
    Handles the option to calculate Karvonen Heart Rate Zones.
    """

    print("\n--- Karvonen Heart Rate Zone Calculator ---")
    try:
        age = prompt_int("Enter your age in years (e.g., 30): ")
        if age is None:
            print("Age is required. Aborting Karvonen calculation.")
            return

        resting_heart_rate = prompt_int("Enter your resting heart rate in BPM (e.g., 60): ")
        if resting_heart_rate is None:
            print("Resting heart rate is required. Aborting Karvonen calculation.")
            return

        max_heart_rate = prompt_int("Enter your measured maximum heart rate in BPM (optional, press Enter to calculate): ")
        
        # Default intensity percentages as per common Karvonen zones
        intensity_percentages = [0.5, 0.6, 0.7, 0.8, 0.9]

        zones = calculate_karvonen_zones(age, resting_heart_rate, intensity_percentages, max_heart_rate)

        print("\n--- Your Karvonen Heart Rate Zones ---")
        for zone, (lower_hr, upper_hr) in zones.items():
            print(f"{zone}: {lower_hr} - {upper_hr} BPM")
        
    except ValueError as e:
        logger.error(f"Input error for Karvonen calculation: {e}")
        print(f"Error: {e}")
    except Exception as e:
        logger.critical(f"Unhandled exception in calculate_karvonen_zones_option: {e}", exc_info=True)
        print(f"An unexpected error occurred during Karvonen calculation: {e}")

if __name__ == '__main__':
    # Set logging level to INFO by default
    # To enable debug logging, uncomment the following line:
    # logging.getLogger().setLevel(logging.DEBUG)
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        print(f"Critical error: {e}")


def process_fit_files_option():
    """
    Handles the option to process FIT files and calculate calories burned.
    """
    try:
        # Load configuration from file
        try:
            config = load_user_config()
            weight = config['weight_kg']
            age = config['age_years']
            gender = config['gender']
            
            logger.info(f"Using configuration: weight={weight}kg, age={age}yrs, gender={gender}")
        except ConfigError as e:
            logger.error(f"Configuration error: {e}")
            print(f"Configuration error: {e}")
            print("Using default values: weight=70kg, age=30yrs, gender=male")
            weight = 70
            age = 30
            gender = 'male'
        
        # Define the directory containing the FIT files: <repo_directory>/fitfiles
        try:
            fit_directory = os.path.join(project_root, 'data', 'fitfiles')
            
            if not os.path.exists(fit_directory):
                logger.warning(f"Fitfiles directory not found: {fit_directory}")
                print(f"Fitfiles directory not found: {fit_directory}")
                try:
                    os.makedirs(fit_directory)
                    logger.info(f"Created fitfiles directory: {fit_directory}")
                    print(f"Created fitfiles directory: {fit_directory}")
                except Exception as e:
                    logger.error(f"Failed to create fitfiles directory: {e}")
                    print(f"Failed to create fitfiles directory: {e}")
                    return
            
            # Find all .fit files in the 'fitfiles' folder
            fit_files = glob.glob(os.path.join(fit_directory, '*.fit'))
            
            if not fit_files:
                logger.warning(f"No .fit files found in directory: {fit_directory}")
                print("No .fit files found in directory:", fit_directory)
                return
    
            logger.info(f"Found {len(fit_files)} .fit files to process")
            
            # Process each file and print its estimated calorie burn
            processed_count = 0
            error_count = 0
            
            for file_path in fit_files:
                try:
                    logger.info(f"Processing file: {os.path.basename(file_path)}")
                    total_calories = process_fit_file(file_path, weight, age, gender)
                    print(f"File: {os.path.basename(file_path)} - Total calories burned (estimated): {total_calories:.2f} kcal")
                    logger.info(f"Calories burned: {total_calories:.2f} kcal")
                    processed_count += 1
                except FileNotFoundError as e:
                    error_msg = f"File not found: {os.path.basename(file_path)}"
                    logger.error(error_msg)
                    print(error_msg)
                    error_count += 1
                except PermissionError as e:
                    error_msg = f"Permission denied: {os.path.basename(file_path)}"
                    logger.error(error_msg)
                    print(error_msg)
                    error_count += 1
                except InvalidFitFileError as e:
                    error_msg = f"Invalid FIT file {os.path.basename(file_path)}: {e}"
                    logger.error(error_msg)
                    print(error_msg)
                    error_count += 1
                except MissingDataError as e:
                    error_msg = f"Missing data in {os.path.basename(file_path)}: {e}"
                    logger.error(error_msg)
                    print(error_msg)
                    error_count += 1
                except Exception as e:
                    error_msg = f"Error processing file {os.path.basename(file_path)}: {e}"
                    logger.error(error_msg)
                    print(error_msg)
                    error_count += 1
            
            logger.info(f"Processing complete. Processed {processed_count} files successfully, {error_count} files with errors.")
            if processed_count > 0:
                print(f"\nProcessing complete. Processed {processed_count} files successfully.")
            if error_count > 0:
                print(f"Encountered errors in {error_count} files. Check the log for details.")
                
        except Exception as e:
            logger.error(f"Error finding or processing FIT files: {e}")
            print(f"Error finding or processing FIT files: {e}")
            
    except Exception as e:
        logger.critical(f"Unhandled exception in process_fit_files_option: {e}")
        print(f"An unexpected error occurred: {e}")

def calculate_karvonen_zones_option():
    """
    Handles the option to calculate Karvonen Heart Rate Zones.
    """

    print("\n--- Karvonen Heart Rate Zone Calculator ---")
    try:
        age = prompt_int("Enter your age in years (e.g., 30): ")
        if age is None:
            print("Age is required. Aborting Karvonen calculation.")
            return

        resting_heart_rate = prompt_int("Enter your resting heart rate in BPM (e.g., 60): ")
        if resting_heart_rate is None:
            print("Resting heart rate is required. Aborting Karvonen calculation.")
            return

        max_heart_rate = prompt_int("Enter your measured maximum heart rate in BPM (optional, press Enter to calculate): ")
        
        # Default intensity percentages as per common Karvonen zones
        intensity_percentages = [0.5, 0.6, 0.7, 0.8, 0.9]

        zones = calculate_karvonen_zones(age, resting_heart_rate, intensity_percentages, max_heart_rate)

        print("\n--- Your Karvonen Heart Rate Zones ---")
        for zone, (lower_hr, upper_hr) in zones.items():
            print(f"{zone}: {lower_hr} - {upper_hr} BPM")
        
    except ValueError as e:
        logger.error(f"Input error for Karvonen calculation: {e}")
        print(f"Error: {e}")
    except Exception as e:
        logger.critical(f"Unhandled exception in calculate_karvonen_zones_option: {e}", exc_info=True)
        print(f"An unexpected error occurred during Karvonen calculation: {e}")

if __name__ == '__main__':
    # Set logging level to INFO by default
    # To enable debug logging, uncomment the following line:
    # logging.getLogger().setLevel(logging.DEBUG)
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        print(f"Critical error: {e}")
