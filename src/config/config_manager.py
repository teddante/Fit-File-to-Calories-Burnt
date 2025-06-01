"""
Configuration management module for the Fit-File-to-Calories-Burnt application.

This module handles loading and validating user configuration from the config file,
providing default values when necessary and ensuring configuration integrity.
"""

import os
import json
from typing import Dict, Any
from src.core.logger import get_logger
from src.core.utils import load_config
from src.exceptions import ConfigError

# Get logger for this module
logger = get_logger(__name__)

# Determine the project root directory dynamically
# This assumes the script is run from within the project structure
# src/config/config_manager.py -> src/ -> project_root/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def load_user_config() -> Dict[str, Any]:
    """
    Load and validate user configuration from config file.
    
    This function loads the user configuration from the config.json file,
    validates the values, and provides sensible defaults for missing or
    invalid configuration values.
    
    Returns:
        Dictionary with validated configuration values containing:
        - weight_kg: User's weight in kilograms (float)
        - age_years: User's age in years (int)
        - gender: User's gender ('male' or 'female')
        
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

def get_current_config() -> Dict[str, Any]:
    """
    Retrieves the current validated user configuration.

    This function acts as a wrapper around load_user_config, providing a
    convenient way to access the application's configuration.

    Returns:
        Dictionary with validated configuration values.

    Raises:
        ConfigError: If the configuration cannot be loaded or is invalid.
    """
    return load_user_config()

def display_config(config: Dict[str, Any]) -> None:
    """
    Prints the current configuration to the console in a user-friendly format.

    Args:
        config: A dictionary containing the configuration values.
    """
    print("\n--- Current Configuration ---")
    for key, value in config.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    print("---------------------------\n")