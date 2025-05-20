import os
import glob
from fitparse import FitFile
from datetime import datetime
import logging
from logger import get_logger
from utils import load_config, calories_burned

# Get logger for this module
logger = get_logger(__name__)

def extract_heart_rate_data(fitfile):
    """
    Extract (timestamp, heart_rate) tuples from a FitFile object or a mock.
    Returns a sorted list by timestamp.
    Handles both real FitFile and MagicMock/dict-based mocks.
    Adds debug logs for diagnosis.
    """
    heart_rate_data = []
    for record in fitfile.get_messages('record'):
        logger.debug(f"record: {record}")
        timestamp = None
        hr = None
        # Always call __iter__ to get fields; handle mocks with instance-level __iter__
        try:
            iter_func = getattr(record, '__iter__')
            fields = list(iter_func(record))
        except Exception:
            try:
                fields = list(iter(record))
            except Exception:
                fields = [record]
        logger.debug(f"fields: {fields}")
        for field in fields:
            name = getattr(field, 'name', None)
            value = getattr(field, 'value', None)
            logger.debug(f"field: {field}, name: {name}, value: {value}")
            if name == 'timestamp':
                timestamp = value
            elif name == 'heart_rate':
                hr = value
        logger.debug(f"extracted timestamp: {timestamp}, hr: {hr}")
        if hr is not None and timestamp is not None:
            heart_rate_data.append((timestamp, hr))
    logger.debug(f"heart_rate_data: {heart_rate_data}")
    return sorted(heart_rate_data, key=lambda x: x[0])

def integrate_calories_over_intervals(heart_rate_data, weight, age, gender):
    """
    Integrate calories burned over heart rate intervals.
    """
    total_calories = 0.0
    for i in range(1, len(heart_rate_data)):
        prev_ts, prev_hr = heart_rate_data[i - 1]
        curr_ts, curr_hr = heart_rate_data[i]
        delta_minutes = (curr_ts - prev_ts).total_seconds() / 60.0
        avg_hr = (prev_hr + curr_hr) / 2.0
        total_calories += calories_burned(avg_hr, delta_minutes, weight, age, gender)
    return total_calories

def process_fit_file(file_path, weight, age, gender):
    """
    Process a single FIT file to compute the total calories burned.
    """
    fitfile = FitFile(file_path)
    heart_rate_data = extract_heart_rate_data(fitfile)
    return integrate_calories_over_intervals(heart_rate_data, weight, age, gender)

def main():
    # Load configuration from file.
    config = load_config()
    weight = config.get('weight_kg', 70)       # Default to 70 kg if not specified.
    age = config.get('age_years', 30)          # Default to 30 years if not specified.
    gender = config.get('gender', 'male')      # Default to 'male' if not specified.
    
    logger.info(f"Using configuration: weight={weight}kg, age={age}yrs, gender={gender}")
    
    # Define the directory containing the FIT files: <repo_directory>/fitfiles
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    fit_directory = os.path.join(repo_dir, 'fitfiles')
    
    # Find all .fit files in the 'fitfiles' folder.
    fit_files = glob.glob(os.path.join(fit_directory, '*.fit'))
    
    if not fit_files:
        logger.warning(f"No .fit files found in directory: {fit_directory}")
        print("No .fit files found in directory:", fit_directory)
        return

    logger.info(f"Found {len(fit_files)} .fit files to process")
    
    # Process each file and print its estimated calorie burn.
    for file_path in fit_files:
        try:
            logger.info(f"Processing file: {os.path.basename(file_path)}")
            total_calories = process_fit_file(file_path, weight, age, gender)
            print(f"File: {os.path.basename(file_path)} - Total calories burned (estimated): {total_calories:.2f} kcal")
            logger.info(f"Calories burned: {total_calories:.2f} kcal")
        except Exception as e:
            error_msg = f"Error processing file {file_path}: {e}"
            logger.error(error_msg)
            print(error_msg)

if __name__ == '__main__':
    # Set logging level to INFO by default
    # To enable debug logging, uncomment the following line:
    # logging.getLogger().setLevel(logging.DEBUG)
    main()
