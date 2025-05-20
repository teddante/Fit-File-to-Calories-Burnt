# File to Calories Burnt

A tool to estimate calories burned from fitness files.

## Code Structure

- `file_to_calories.py`: Main script for batch processing `.fit` files in the `fitfiles/` directory, using user configuration from `config.json`.
- `cardio_calculator.py`: Command-line calculator for solving the Keytel et al. formula for calories, heart rate, weight, or age.
- `config.json`: Stores user-specific parameters (`weight_kg`, `age_years`, `gender`).
- `fitfiles/`: Directory for `.fit` files to be analyzed.
- `test_file_to_calories.py`: Unit tests for `file_to_calories.py` (uses pytest and unittest.mock).
- `test_cardio_calculator.py`: Unit tests for `cardio_calculator.py` (uses pytest).

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
