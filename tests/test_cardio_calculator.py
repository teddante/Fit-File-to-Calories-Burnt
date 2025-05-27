import pytest
from unittest.mock import MagicMock, patch

# Patch logger before importing the modules
@pytest.fixture(autouse=True)
def mock_logger():
    with patch('src.core.logger.get_logger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger

# Import directly from utils module
from src.core.utils import (
    calculate_kcal_per_min,
    calculate_heart_rate,
    calculate_weight,
    calculate_age,
)

# Import from cardio_calculator for error handling tests
from src.cardio.calculator import (
    calculate_with_error_handling
)
from src.validators.input_validator import (
    validate_gender,
    validate_calculation_inputs
)
from src.exceptions import (
    InputValidationError,
    CalculationError
)

def test_calculate_kcal_per_min_typical():
    assert pytest.approx(calculate_kcal_per_min(150, 70, 30), 0.01) == 14.22

def test_calculate_kcal_per_min_female():
    # Test with female gender
    female_kcal = calculate_kcal_per_min(150, 70, 30, 'female')
    assert isinstance(female_kcal, float)
    # Female formula should give different result than male formula
    male_kcal = calculate_kcal_per_min(150, 70, 30, 'male')
    assert female_kcal != male_kcal

def test_calculate_kcal_per_min_zero():
    assert pytest.approx(calculate_kcal_per_min(0, 0, 0), 0.01) == -13.17

def test_calculate_heart_rate_inverse():
    kcal = calculate_kcal_per_min(150, 70, 30)
    hr = calculate_heart_rate(kcal, 70, 30)
    assert pytest.approx(hr, 0.01) == 150

def test_calculate_weight_inverse():
    kcal = calculate_kcal_per_min(150, 70, 30)
    wt = calculate_weight(kcal, 150, 30)
    assert pytest.approx(wt, 0.01) == 70

def test_calculate_age_inverse():
    kcal = calculate_kcal_per_min(150, 70, 30)
    age = calculate_age(kcal, 150, 70)
    assert pytest.approx(age, 0.01) == 30

def test_negative_values():
    assert isinstance(calculate_kcal_per_min(-10, -20, -30), float)
    assert isinstance(calculate_heart_rate(-5, -10, -15), float)
    assert isinstance(calculate_weight(-5, -10, -15), float)
    assert isinstance(calculate_age(-5, -10, -15), float)

# New tests for error handling functionality

def test_validate_gender_valid():
    """Test that validate_gender accepts valid inputs."""
    assert validate_gender("male") == "male"
    assert validate_gender("MALE") == "male"
    assert validate_gender(" female ") == "female"

def test_validate_gender_invalid():
    """Test that validate_gender rejects invalid inputs."""
    with pytest.raises(InputValidationError):
        validate_gender("other")
    with pytest.raises(InputValidationError):
        validate_gender("")

def test_validate_calculation_inputs_valid():
    """Test that validate_calculation_inputs accepts valid inputs."""
    # Test with all inputs valid
    result = validate_calculation_inputs(
        heart_rate=100, 
        weight=70, 
        age=30, 
        kcal_per_min=10, 
        gender="male"
    )
    assert result == {
        "heart_rate": 100,
        "weight": 70,
        "age": 30,
        "kcal_per_min": 10,
        "gender": "male"
    }
    
    # Test with some inputs None (which is valid)
    result = validate_calculation_inputs(
        heart_rate=100,
        weight=None,
        age=30
    )
    assert result == {
        "heart_rate": 100,
        "age": 30
    }

def test_validate_calculation_inputs_invalid():
    """Test that validate_calculation_inputs rejects invalid inputs."""
    # Test invalid heart rate
    with pytest.raises(InputValidationError):
        validate_calculation_inputs(heart_rate=0)
    with pytest.raises(InputValidationError):
        validate_calculation_inputs(heart_rate=300)
        
    # Test invalid weight
    with pytest.raises(InputValidationError):
        validate_calculation_inputs(weight=0)
    with pytest.raises(InputValidationError):
        validate_calculation_inputs(weight=600)
        
    # Test invalid age
    with pytest.raises(InputValidationError):
        validate_calculation_inputs(age=0)
    with pytest.raises(InputValidationError):
        validate_calculation_inputs(age=150)
        
    # Test invalid kcal_per_min
    with pytest.raises(InputValidationError):
        validate_calculation_inputs(kcal_per_min=-1)
    with pytest.raises(InputValidationError):
        validate_calculation_inputs(kcal_per_min=150)
        
    # Test invalid gender
    with pytest.raises(InputValidationError):
        validate_calculation_inputs(gender="other")

def test_calculate_with_error_handling_valid():
    """Test that calculate_with_error_handling works with valid inputs."""
    # Test calculating kcal_per_min
    result = calculate_with_error_handling("kcal_per_min", {
        "heart_rate": 150,
        "weight": 70,
        "age": 30,
        "gender": "male"
    })
    assert pytest.approx(result, 0.01) == 14.22
    
    # Test calculating heart_rate
    result = calculate_with_error_handling("heart_rate", {
        "kcal_per_min": 14.22,
        "weight": 70,
        "age": 30,
        "gender": "male"
    })
    assert pytest.approx(result, 0.01) == 150
    
    # Test calculating weight
    result = calculate_with_error_handling("weight", {
        "kcal_per_min": 14.22,
        "heart_rate": 150,
        "age": 30,
        "gender": "male"
    })
    assert pytest.approx(result, 0.01) == 70
    
    # Test calculating age
    result = calculate_with_error_handling("age", {
        "kcal_per_min": 14.22,
        "heart_rate": 150,
        "weight": 70,
        "gender": "male"
    })
    assert pytest.approx(result, 0.01) == 30

def test_calculate_with_error_handling_missing_inputs():
    """Test that calculate_with_error_handling raises errors for missing inputs."""
    # Missing heart_rate for kcal_per_min calculation
    with pytest.raises(CalculationError) as excinfo:
        calculate_with_error_handling("kcal_per_min", {
            "weight": 70,
            "age": 30,
            "gender": "male"
        })
    assert "Missing required inputs" in str(excinfo.value)
    
    # Missing kcal_per_min for heart_rate calculation
    with pytest.raises(CalculationError) as excinfo:
        calculate_with_error_handling("heart_rate", {
            "weight": 70,
            "age": 30,
            "gender": "male"
        })
    assert "Missing required inputs" in str(excinfo.value)
    
    # Missing heart_rate for weight calculation
    with pytest.raises(CalculationError) as excinfo:
        calculate_with_error_handling("weight", {
            "kcal_per_min": 14.22,
            "age": 30,
            "gender": "male"
        })
    assert "Missing required inputs" in str(excinfo.value)
    
    # Missing weight for age calculation
    with pytest.raises(CalculationError) as excinfo:
        calculate_with_error_handling("age", {
            "kcal_per_min": 14.22,
            "heart_rate": 150,
            "gender": "male"
        })
    assert "Missing required inputs" in str(excinfo.value)

def test_calculate_with_error_handling_unknown_variable():
    """Test that calculate_with_error_handling raises error for unknown variable."""
    with pytest.raises(CalculationError) as excinfo:
        calculate_with_error_handling("unknown", {
            "heart_rate": 150,
            "weight": 70,
            "age": 30,
            "gender": "male"
        })
    assert "Unknown variable" in str(excinfo.value)

def test_calculate_with_error_handling_calculation_error():
    """Test that calculate_with_error_handling wraps calculation errors."""
    # Test unknown variable error - this should raise CalculationError
    with pytest.raises(CalculationError, match="Invalid value in calculation"):
        calculate_with_error_handling("unknown_var", {
            "heart_rate": 150,
            "weight": 70,
            "age": 30,
            "gender": "male"
        })