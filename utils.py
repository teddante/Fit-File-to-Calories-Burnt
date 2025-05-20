import json
import logging
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

def load_config(config_file='config.json') -> Dict[str, Any]:
    """
    Loads configuration parameters from a JSON file.
    Expected keys:
      - weight_kg: your weight in kilograms (e.g., 70)
      - age_years: your age in years (e.g., 30)
      - gender: 'male' or 'female' (defaults to 'male' if not specified)
    """
    with open(config_file, 'r') as f:
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