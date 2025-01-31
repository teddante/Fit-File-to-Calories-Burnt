import json

from fitparse import FitFile
from datetime import datetime

def load_config(config_file='config.json'):
    with open(config_file, 'r') as f:
        return json.load(f)


# Function to estimate calories burned during an interval,
# using the Keytel et al. formula for men.
# Adjust the weight (kg) and age (years) as needed.
def calories_burned(hr, duration_minutes, weight, age):
    # Calories per minute (kcal/min)
    cpm = (-55.0969 + (0.6309 * hr) + (0.1988 * weight) + (0.2017 * age)) / 4.184
    return cpm * duration_minutes

# Replace 'your_file.fit' with the path to your .fit file.
fitfile = FitFile('your_file.fit')

# List to store (timestamp, heart_rate) tuples.
heart_rate_data = []

# Extract heart rate and timestamp data from each 'record' message.
for record in fitfile.get_messages('record'):
    timestamp = None
    hr = None

    # Each record may contain several fields.
    for data in record:
        if data.name == 'timestamp':
            timestamp = data.value  # Should be a datetime object.
        elif data.name == 'heart_rate':
            hr = data.value       # Heart rate (in bpm).
    
    # Only keep records that have both timestamp and heart rate.
    if hr is not None and timestamp is not None:
        heart_rate_data.append((timestamp, hr))

# Sort the data by timestamp to ensure proper time ordering.
heart_rate_data.sort(key=lambda x: x[0])

# Personal parameters (change these as appropriate).
config = load_config()
weight = config['weight_kg']
age = config['age_years']
fitfile = FitFile(config['fit_file_path'])

weight = 70  # in kilograms
age = 30     # in years

total_calories = 0.0

# Calculate the total calories burned by integrating over each time interval.
# We assume that between two recorded timestamps, the heart rate changes linearly,
# so we take the average of the two heart rates.
for i in range(1, len(heart_rate_data)):
    prev_ts, prev_hr = heart_rate_data[i-1]
    curr_ts, curr_hr = heart_rate_data[i]
    
    # Calculate duration in minutes between consecutive records.
    delta_minutes = (curr_ts - prev_ts).total_seconds() / 60.0
    
    # Compute the average heart rate for this interval.
    avg_hr = (prev_hr + curr_hr) / 2.0
    
    # Estimate the calories burned during this interval.
    total_calories += calories_burned(avg_hr, delta_minutes, weight, age)

print("Total calories burned (estimated): {:.2f} kcal".format(total_calories))
