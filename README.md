# File to Calories Burnt

A tool to estimate calories burned from fitness files.

## Code Structure

- `file_to_calories.py`: Main script for batch processing `.fit` files in the `fitfiles/` directory, using user configuration from `config.json`.
- `cardio_calculator.py`: Command-line calculator for solving the Keytel et al. formula for calories, heart rate, weight, or age.
- `utils.py`: Shared utility functions for calorie calculations and configuration loading.
- `logger.py`: Centralized logging configuration.
- `config.json`: Stores user-specific parameters (`weight_kg`, `age_years`, `gender`).
- `fitfiles/`: Directory for `.fit` files to be analyzed.
- `test_file_to_calories.py`: Unit tests for `file_to_calories.py` (uses pytest and unittest.mock).
- `test_cardio_calculator.py`: Unit tests for `cardio_calculator.py` (uses pytest).

## Architecture

### Modular Design

The codebase has been refactored to eliminate code duplication through a modular architecture:

- **Utils Module**: The `utils.py` module serves as a central repository for shared functionality:
  - Defines constants for both male and female Keytel formula calculations
  - Provides unified calorie calculation functions used by both main scripts
  - Includes configuration loading functionality
  - Contains formula solvers for different variables (calories, heart rate, weight, age)

### Consolidated Calorie Calculations

The calorie calculation formulas have been consolidated in the `utils.py` module:

- **Formula Constants**: Male and female formula constants are defined as dictionaries:

  ```python
  MALE_CONSTANTS = {
      'base': -55.0969,
      'hr_coef': 0.6309,
      'weight_coef': 0.1988,
      'age_coef': 0.2017,
      'conversion': 4.184
  }
  
  FEMALE_CONSTANTS = {
      'base': -20.4022,
      'hr_coef': 0.4472,
      'weight_coef': -0.1263,
      'age_coef': 0.074,
      'conversion': 4.184
  }
  ```

- **Unified Calculation Functions**: A single implementation handles both male and female formulas:

  ```python
  def calculate_kcal_per_min(hr, weight, age, gender='male'):
      constants = FEMALE_CONSTANTS if gender.lower() == 'female' else MALE_CONSTANTS
      return (constants['base'] +
              (constants['hr_coef'] * hr) +
              (constants['weight_coef'] * weight) +
              (constants['age_coef'] * age)) / constants['conversion']
  ```

### Gender Support

The refactored code now provides improved support for both male and female formulas:

- All calculation functions accept a `gender` parameter (defaulting to 'male')
- The appropriate constants are selected based on the gender parameter
- The negative weight coefficient for females is properly handled

## Installation

- Install dependencies:

  ```sh
  pip install fitparse pytest
  ```

## Usage

- To process all `.fit` files in the `fitfiles/` directory:

  ```python
  python file_to_calories.py
  ```

  Results will be printed for each file.

- To use the interactive calculator:

  ```python
  python cardio_calculator.py
  ```

  Enter values for heart rate, weight, age, or kcal/min (leave one blank to solve for it).

## Configuration

Edit `config.json` to set your parameters:

- `weight_kg`: User's weight in kilograms
- `age_years`: User's age in years
- `gender`: User's gender (`male` or `female`)

## Running Tests

- Run all tests from the project root with:

  ```sh
  pytest
  ```

- Tests are located in `test_file_to_calories.py` and `test_cardio_calculator.py`.

## License

See [LICENSE](LICENSE) for details.

## Error Handling

### Exception Hierarchy

The project implements a robust error handling system with custom exception classes:

- **FIT File Processing Exceptions**:
  - `FitFileError`: Base exception for FIT file processing errors
  - `InvalidFitFileError`: Raised when a FIT file is invalid or corrupted
  - `MissingDataError`: Raised when required data is missing from a FIT file
  - `ConfigError`: Raised for configuration-related errors

- **Calculator Exceptions**:
  - `CardioCalculatorError`: Base exception for cardio calculator errors
  - `InputValidationError`: Raised when input validation fails
  - `CalculationError`: Raised when a calculation fails

### Input Validation

The system performs comprehensive input validation:

- **Type Checking**: Ensures inputs are of the correct data type
- **Range Validation**: Validates that values fall within physiologically reasonable ranges:
  - Heart rate: positive and ≤ 250 bpm
  - Weight: positive and ≤ 500 kg
  - Age: positive and ≤ 130 years
  - Calories: non-negative and ≤ 100 kcal/min
- **Format Validation**: Ensures strings like gender are in the expected format ('male' or 'female')
- **File Validation**: Checks file existence, permissions, and format before processing

### Error Handling Approach

The project follows these error handling principles:

1. **Specific Exceptions**: Uses specific exception types for different error scenarios
2. **Detailed Messages**: Provides clear error messages that explain what went wrong
3. **Exception Chaining**: Preserves original exception context using the `from` keyword
4. **Comprehensive Logging**: Logs errors at appropriate levels (warning, error, critical)
5. **Graceful Degradation**: Falls back to default values when configuration is invalid
6. **User-Friendly Feedback**: Displays informative error messages to the user

### Handling Errors as a User

When using the tools, you might encounter these errors:

- **Configuration Errors**: Check that your `config.json` file exists and contains valid values for `weight_kg`, `age_years`, and `gender`
- **File Errors**: Ensure your FIT files exist, are readable, and are valid FIT format
- **Data Errors**: Verify that your FIT files contain heart rate data
- **Input Errors**: When using the calculator, ensure inputs are within reasonable physiological ranges

The system will provide specific error messages to help diagnose and fix these issues. For more detailed information, check the log file generated by the logger.
