"""
CLI interface functions for the Fit-File-to-Calories-Burnt application.

This module contains the user interface logic for handling different menu options
including FIT file processing, Karvonen zone calculations, and file cleanup.
"""

import os
import glob
import logging
from typing import Optional
from src.core.logger import get_logger
from src.core.utils import calculate_karvonen_zones
from src.services.fit_processor import process_fit_file
from src.services.file_manager import extract_fit_file_metadata, rename_fit_file
from src.config.config_manager import load_user_config
from src.exceptions import FitFileError, InvalidFitFileError, MissingDataError, ConfigError

# Get logger for this module
logger = get_logger(__name__)

# Determine the project root directory dynamically
# This assumes the script is run from within the project structure
# src/cli/interface.py -> src/ -> project_root/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def prompt_int(prompt_message: str) -> Optional[int]:
    """
    Prompts the user for an integer input.
    
    Args:
        prompt_message: The message to display to the user
        
    Returns:
        The integer value entered by the user, or None if no input provided
    """
    while True:
        try:
            value = input(prompt_message).strip()
            if not value:
                return None
            return int(value)
        except ValueError:
            print("Invalid input. Please enter a whole number.")


def process_fit_files_option():
    """
    Handles the option to process FIT files and calculate calories burned.
    
    This function loads user configuration, finds all FIT files in the data directory,
    and processes each file to calculate estimated calories burned.
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
                logger.info(f"Processing file: {os.path.basename(file_path)}")
                result = process_fit_file(file_path, weight, age, gender)
                
                if result.success:
                    total_calories = result.calorie_data.total_calories
                    avg_hr = result.calorie_data.average_heart_rate
                    duration = result.calorie_data.duration_minutes
                    print(f"File: {os.path.basename(file_path)} - Total calories burned (estimated): {total_calories:.2f} kcal")
                    print(f"  Duration: {duration:.1f} min, Avg HR: {avg_hr:.0f} bpm, Intervals: {result.calorie_data.intervals_processed}")
                    logger.info(f"Calories burned: {total_calories:.2f} kcal, Duration: {duration:.1f} min")
                    processed_count += 1
                else:
                    error_msg = f"Error processing {os.path.basename(file_path)}: {result.error_message}"
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


def cleanup_fit_files_option():
    """
    Handles the option to clean up FIT file names based on extracted metadata.
    
    This function finds all FIT files in the data directory, extracts metadata
    from each file, and renames them to a standardized format.
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
        logger.critical(f"Unhandled exception in cleanup_fit_files_option: {e}")
        print(f"An unexpected error occurred: {e}")


def calculate_karvonen_zones_option():
    """
    Handles the option to calculate Karvonen Heart Rate Zones.
    
    This function prompts the user for their age, resting heart rate, and optionally
    their maximum heart rate, then calculates and displays their heart rate zones
    using the Karvonen formula.
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