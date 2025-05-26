import os
import glob
import json
from datetime import datetime, timedelta
import logging
from typing import List, Tuple, Optional, Dict, Any
from src.core.logger import get_logger
from src.core.utils import load_config, calculate_karvonen_zones
from src.services.fit_processor import process_fit_file, FitFileError, InvalidFitFileError, MissingDataError
from src.services.file_manager import extract_fit_file_metadata, rename_fit_file

# Get logger for this module
logger = get_logger(__name__)

# Determine the project root directory dynamically
# This assumes the script is run from within the project structure
# src/main.py -> src/ -> project_root/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class ConfigError(Exception):
    """Exception raised for configuration-related errors."""
    pass


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
    # Initialize logging
    from src.core.logger import initialize_logging
    initialize_logging(logging.INFO)
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
