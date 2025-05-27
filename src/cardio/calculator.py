import logging
from typing import Optional, Dict, Any, Union
from src.core.logger import get_logger
from src.core.utils import (
    calculate_kcal_per_min,
    calculate_heart_rate,
    calculate_weight,
    calculate_age
)
from src.validators.input_validator import (
    validate_gender,
    validate_calculation_inputs
)
from src.exceptions import CardioCalculatorError, CalculationError, InputValidationError

# Get logger for this module
logger = get_logger(__name__)

def prompt_float(prompt: str) -> Optional[float]:
    """
    Prompt the user for a float value. Returns None if input is blank.
    
    Args:
        prompt: The prompt text to display to the user
        
    Returns:
        A float value or None if the input is blank
        
    Raises:
        KeyboardInterrupt: If the user interrupts the input (Ctrl+C)
    """
    while True:
        try:
            value = input(prompt)
            if value.strip() == "":
                return None
            try:
                return float(value)
            except ValueError:
                print("Please enter a valid number or leave blank.")
        except KeyboardInterrupt:
            logger.info("Input interrupted by user")
            raise


def calculate_with_error_handling(missing_var: str, values: Dict[str, Any]) -> float:
    """
    Calculate the missing variable with comprehensive error handling.
    
    Args:
        missing_var: The name of the variable to calculate
        values: Dictionary of input values
        
    Returns:
        The calculated value
        
    Raises:
        CalculationError: If the calculation fails
        InputValidationError: If inputs are invalid
    """
    try:
        if missing_var == "kcal_per_min":
            # Validate required inputs
            if any(values.get(key) is None for key in ['heart_rate', 'weight', 'age']):
                raise InputValidationError("Missing required inputs for kcal_per_min calculation")
                
            return calculate_kcal_per_min(values['heart_rate'], values['weight'], values['age'], values['gender'])
            
        elif missing_var == "heart_rate":
            # Validate required inputs
            if any(values.get(key) is None for key in ['kcal_per_min', 'weight', 'age']):
                raise InputValidationError("Missing required inputs for heart_rate calculation")
                
            return calculate_heart_rate(values['kcal_per_min'], values['weight'], values['age'], values['gender'])
            
        elif missing_var == "weight":
            # Validate required inputs
            if any(values.get(key) is None for key in ['kcal_per_min', 'heart_rate', 'age']):
                raise InputValidationError("Missing required inputs for weight calculation")
                
            return calculate_weight(values['kcal_per_min'], values['heart_rate'], values['age'], values['gender'])
            
        elif missing_var == "age":
            # Validate required inputs
            if any(values.get(key) is None for key in ['kcal_per_min', 'heart_rate', 'weight']):
                raise InputValidationError("Missing required inputs for age calculation")
                
            return calculate_age(values['kcal_per_min'], values['heart_rate'], values['weight'], values['gender'])
            
        else:
            raise ValueError(f"Unknown variable: {missing_var}")
            
    except ZeroDivisionError as e:
        logger.error(f"Division by zero in calculation: {e}")
        raise CalculationError(f"Division by zero error: {e}") from e
    except ValueError as e:
        logger.error(f"Value error in calculation: {e}")
        raise CalculationError(f"Invalid value in calculation: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error in calculation: {e}")
        raise CalculationError(f"Calculation error: {e}") from e

def main():
    """
    Main function for the cardio calculator.
    
    Prompts the user for input values, validates them, and calculates the missing variable.
    Handles errors gracefully and provides informative error messages.
    """
    try:
        logger.info("Starting cardio calculator")
        print("Enter values for the following variables. Leave one blank (press Enter) if unknown.")
        
        try:
            heart_rate = prompt_float("Heart rate: ")
            weight = prompt_float("Weight (in kg): ")
            age = prompt_float("Age (in years): ")
            kcal_per_min = prompt_float("Kcal per minute: ")
            
            gender_input = input("Gender (male/female, default: male): ").strip().lower() or "male"
            try:
                gender = validate_gender(gender_input)
            except InputValidationError as e:
                logger.warning(f"Invalid gender input: {e}")
                print(f"Warning: {e}. Using default 'male'.")
                gender = "male"
            
            # Create values dictionary
            values = {
                "heart_rate": heart_rate,
                "weight": weight,
                "age": age,
                "kcal_per_min": kcal_per_min,
                "gender": gender,
            }
            logger.debug(f"Input values: {values}")
            
            # Validate inputs where provided
            try:
                validate_calculation_inputs(**{k: v for k, v in values.items() if v is not None})
            except InputValidationError as e:
                logger.warning(f"Input validation warning: {e}")
                print(f"Warning: {e}")
            
            # Check for exactly one missing value
            missing = [k for k, v in values.items() if v is None and k != 'gender']
            if len(missing) != 1:
                error_msg = "Error: Exactly one value must be missing."
                logger.error(error_msg)
                print(error_msg)
                return
            
            missing_var = missing[0]
            logger.info(f"Calculating missing variable: {missing_var}")
            
            # Calculate the missing variable with error handling
            try:
                result_value = calculate_with_error_handling(missing_var, values)
                
                # Format and display the result
                if missing_var == "kcal_per_min":
                    result = f"Calculated kcal per minute: {result_value:.4f}"
                elif missing_var == "heart_rate":
                    result = f"Calculated heart rate: {result_value:.4f}"
                elif missing_var == "weight":
                    result = f"Calculated weight (kg): {result_value:.4f}"
                elif missing_var == "age":
                    result = f"Calculated age (years): {result_value:.4f}"
                
                logger.info(result)
                print(result)
                
            except (InputValidationError, CalculationError) as e:
                logger.error(f"Calculation failed: {e}")
                print(f"Error: {e}")
                
        except KeyboardInterrupt:
            print("\nInput interrupted. Exiting.")
            logger.info("Input interrupted by user")
            return
            
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {e}", exc_info=True)
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
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
