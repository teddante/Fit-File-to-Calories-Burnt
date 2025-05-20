import json
import logging
import os
from typing import Dict, Any, Union

# Constants for Keytel formula
MALE_CONSTANTS = {
    'base': -55.0969,
    'hr_coef': 0.6309,
    'weight_coef': 0.1988,
    'age_coef': 0.2017,
    'conversion': 4.184  # Convert to kcal
}

FEMALE_CONSTANTS = {
    'base': -20.4022,
    'hr_coef': 0.4472,
    'weight_coef': -0.1263,
    'age_coef': 0.074,
    'conversion': 4.184  # Convert to kcal
}

def load_config(config_file_path=None) -> Dict[str, Any]:
    """
    Loads configuration parameters from a JSON file.
    Expected keys:
      - weight_kg: your weight in kilograms (e.g., 70)
      - age_years: your age in years (e.g., 30)
      - gender: 'male' or 'female' (defaults to 'male' if not specified)
    """
    if config_file_path is None:
        # Construct the path relative to the project root
        current_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        config_file_path = os.path.join(project_root, 'config', 'config.json')

    with open(config_file_path, 'r') as f:
        return json.load(f)

def calculate_kcal_per_min(hr: float, weight: float, age: float, gender: str = 'male') -> float:
    """
    Calculate kcal per minute using the Keytel et al. formula.
    
    Parameters:
      - hr: heart rate in beats per minute.
      - weight: weight in kilograms.
      - age: age in years.
      - gender: 'male' or 'female'.
      
    Returns:
      - Estimated kcal burned per minute.
      
    Formulas:
      For men:
        kcal/min = (-55.0969 + (0.6309 * hr) + (0.1988 * weight) + (0.2017 * age)) / 4.184
      For women:
        kcal/min = (-20.4022 + (0.4472 * hr) - (0.1263 * weight) + (0.074 * age)) / 4.184
    """
    constants = FEMALE_CONSTANTS if gender.lower() == 'female' else MALE_CONSTANTS
    
    return (constants['base'] + 
            (constants['hr_coef'] * hr) + 
            (constants['weight_coef'] * weight) + 
            (constants['age_coef'] * age)) / constants['conversion']

def calories_burned(hr: float, duration_minutes: float, weight: float, age: float, gender: str = 'male') -> float:
    """
    Estimate the calories burned during an interval using the Keytel et al. formulas.
    
    Parameters:
      - hr: heart rate in beats per minute.
      - duration_minutes: duration of the interval in minutes.
      - weight: weight in kilograms.
      - age: age in years.
      - gender: 'male' or 'female'.
      
    Returns:
      - Estimated calories burned during the interval.
    """
    kcal_per_min = calculate_kcal_per_min(hr, weight, age, gender)
    return kcal_per_min * duration_minutes

def calculate_heart_rate(kcal_per_min: float, weight: float, age: float, gender: str = 'male') -> float:
    """
    Solve for heart rate given kcal_per_min, weight, and age.
    """
    constants = FEMALE_CONSTANTS if gender.lower() == 'female' else MALE_CONSTANTS
    
    return (constants['conversion'] * kcal_per_min - constants['base'] - 
            constants['weight_coef'] * weight - constants['age_coef'] * age) / constants['hr_coef']

def calculate_weight(kcal_per_min: float, heart_rate: float, age: float, gender: str = 'male') -> float:
    """
    Solve for weight given kcal_per_min, heart_rate, and age.
    """
    constants = FEMALE_CONSTANTS if gender.lower() == 'female' else MALE_CONSTANTS
    
    return (constants['conversion'] * kcal_per_min - constants['base'] - 
            constants['hr_coef'] * heart_rate - constants['age_coef'] * age) / constants['weight_coef']

def calculate_age(kcal_per_min: float, heart_rate: float, weight: float, gender: str = 'male') -> float:
    """
    Solve for age given kcal_per_min, heart_rate, and weight.
    """
    constants = FEMALE_CONSTANTS if gender.lower() == 'female' else MALE_CONSTANTS
    
    return (constants['conversion'] * kcal_per_min - constants['base'] - 
            constants['hr_coef'] * heart_rate - constants['weight_coef'] * weight) / constants['age_coef']

def calculate_karvonen_zones(age: int, resting_heart_rate: int, intensity_percentages: list, max_heart_rate: Union[int, None] = None) -> Dict[str, tuple]:
    """
    Calculates target heart rate zones using the Karvonen Formula.

    Parameters:
      - age: Age in years (positive integer).
      - resting_heart_rate: Resting heart rate in BPM (positive integer).
      - intensity_percentages: A list of floats representing intensity percentages (e.g., [0.5, 0.6, 0.7, 0.85]).
                               Each float must be between 0 and 1. These are treated as lower bounds of zones.
      - max_heart_rate: Optional. Measured maximum heart rate in BPM (positive integer).
                        If not provided, MHR is calculated using Tanaka, Monahan, & Seals formula: 208 - (0.7 * age).

    Returns:
      - A dictionary where keys are strings representing the intensity range (e.g., "50%-60%")
        and values are tuples (lower_hr, upper_hr) representing the target heart rate zone.
    """
    # Input validation
    if not isinstance(age, int) or age <= 0:
        raise ValueError("Age must be a positive integer.")
    if not isinstance(resting_heart_rate, int) or resting_heart_rate <= 0:
        raise ValueError("Resting heart rate must be a positive integer.")
    if not isinstance(intensity_percentages, list) or not intensity_percentages:
        raise ValueError("Intensity percentages must be a non-empty list of floats.")
    for intensity in intensity_percentages:
        if not isinstance(intensity, (float, int)) or not (0 <= intensity <= 1):
            raise ValueError("Each intensity percentage must be a float between 0 and 1.")
    if max_heart_rate is not None and (not isinstance(max_heart_rate, int) or max_heart_rate <= 0):
        raise ValueError("Max heart rate, if provided, must be a positive integer.")

    # Calculate MHR
    if max_heart_rate is None:
        mhr = 208 - (0.7 * age)
    else:
        mhr = float(max_heart_rate) # Ensure float for consistent calculations

    # Calculate Heart Rate Reserve (HRR)
    hrr = mhr - resting_heart_rate
    if hrr < 0:
        raise ValueError("Calculated Max Heart Rate cannot be less than Resting Heart Rate. Check age/RHR or provide a valid Max Heart Rate.")

    # Sort intensity percentages to ensure correct zone calculation
    sorted_intensities = sorted(list(set(intensity_percentages))) # Use set to remove duplicates

    karvonen_zones = {}
    num_intensities = len(sorted_intensities)

    for i, current_intensity in enumerate(sorted_intensities):
        # Determine the upper bound for the current zone
        if i < num_intensities - 1:
            next_intensity = sorted_intensities[i+1]
        else:
            # For the last intensity, assume the zone goes up to 100%
            next_intensity = 1.0

        # Calculate lower and upper HR for the zone
        lower_hr = round((hrr * current_intensity) + resting_heart_rate)
        upper_hr = round((hrr * next_intensity) + resting_heart_rate)
        
        # Ensure lower_hr is not greater than upper_hr due to rounding or edge cases
        if lower_hr > upper_hr:
            lower_hr, upper_hr = upper_hr, lower_hr

        zone_key = f"{int(current_intensity*100)}%-{int(next_intensity*100)}%"
        karvonen_zones[zone_key] = (lower_hr, upper_hr)

    return karvonen_zones