import json
import os
import glob
from fitparse import FitFile
from datetime import datetime

def load_config(config_file='config.json'):
    """
    Loads configuration parameters from a JSON file.
    Expected keys:
      - weight_kg: your weight in kilograms (e.g., 70)
      - age_years: your age in years (e.g., 30)
    """
    with open(config_file, 'r') as f:
        return json.load(f)

def calories_burned(hr, duration_minutes, weight, age):
    """
    Estimate the calories burned during an interval using the Keytel et al. formula for men.
    
    Parameters:
      - hr: heart rate in beats per minute.
      - duration_minutes: duration of the interval in minutes.
      - weight: weight in kilograms.
      - age: age in years.
      
    Returns:
      - Estimated calories burned during the interval.
    """
    # Calories per minute (kcal/min) computed from the formula.
    cpm = (-55.0969 + (0.6309 * hr) + (0.1988 * weight) + (0.2017 * age)) / 4.184
    return cpm * duration_minutes

def process_fit_file(file_path, weight, age):
    """
    Process a single FIT file to compute the total calories burned.
    
    Parameters:
      - file_path: path to the FIT file.
      - weight: weight in kilograms.
      - age: age in years.
      
    Returns:
      - Total estimated calories burned.
    """
    fitfile = FitFile(file_path)
    heart_rate_data = []

    # Extract heart rate and timestamp data from each 'record' message.
    for record in fitfile.get_messages('record'):
        timestamp = None
        hr = None

        # Each record may contain several fields.
        for data in record:
            if data.name == 'timestamp':
                timestamp = data.value  # datetime object.
            elif data.name == 'heart_rate':
                hr = data.value       # heart rate (in bpm).

        # Only keep records that have both a timestamp and a heart rate.
        if hr is not None and timestamp is not None:
            heart_rate_data.append((timestamp, hr))

    # Sort the data by timestamp to ensure proper time ordering.
    heart_rate_data.sort(key=lambda x: x[0])

    total_calories = 0.0

    # Calculate total calories burned by integrating over each time interval.
    # We assume that between two recorded timestamps, the heart rate changes linearly,
    # so we take the average of the two heart rates.
    for i in range(1, len(heart_rate_data)):
        prev_ts, prev_hr = heart_rate_data[i - 1]
        curr_ts, curr_hr = heart_rate_data[i]
        
        # Calculate duration in minutes between consecutive records.
        delta_minutes = (curr_ts - prev_ts).total_seconds() / 60.0
        
        # Compute the average heart rate for this interval.
        avg_hr = (prev_hr + curr_hr) / 2.0
        
        # Estimate the calories burned during this interval.
        total_calories += calories_burned(avg_hr, delta_minutes, weight, age)
        
    return total_calories

def main():
    # Load configuration from file.
    config = load_config()
    weight = config.get('weight_kg', 70)       # Default to 70 kg if not specified.
    age = config.get('age_years', 30)            # Default to 30 years if not specified.
    
    # Define the directory containing the FIT files: <repo_directory>/fitfiles
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    fit_directory = os.path.join(repo_dir, 'fitfiles')
    
    # Find all .fit files in the 'fitfiles' folder.
    fit_files = glob.glob(os.path.join(fit_directory, '*.fit'))
    
    if not fit_files:
        print("No .fit files found in directory:", fit_directory)
        return

    # Process each file and print its estimated calorie burn.
    for file_path in fit_files:
        try:
            total_calories = process_fit_file(file_path, weight, age)
            print(f"File: {os.path.basename(file_path)} - Total calories burned (estimated): {total_calories:.2f} kcal")
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

if __name__ == '__main__':
    main()
