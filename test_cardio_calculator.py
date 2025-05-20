import pytest
from unittest.mock import MagicMock, patch

# Patch logger before importing the modules
@pytest.fixture(autouse=True)
def mock_logger():
    with patch('logger.get_logger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger

from cardio_calculator import (
    calculate_kcal_per_min,
    calculate_heart_rate,
    calculate_weight,
    calculate_age,
)

def test_calculate_kcal_per_min_typical():
    assert pytest.approx(calculate_kcal_per_min(150, 70, 30), 0.01) == 14.22

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