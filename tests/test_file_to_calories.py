import pytest
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime, timedelta
import logging

# Patch logger before importing the modules
@pytest.fixture(autouse=True)
def mock_logger():
    with patch('src.core.logger.get_logger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger

# Import from utils module
from src.core.utils import calories_burned, load_config

from src.services.fit_processor import (
    extract_heart_rate_data,
    integrate_calories_over_intervals,
    process_fit_file,
    MissingDataError,
    InvalidFitFileError,
    FitFileError
)
from src.main import ConfigError

def test_calories_burned_male_typical():
    kcal = calories_burned(150, 30, 70, 30, gender='male')
    assert kcal > 0

def test_calories_burned_female_typical():
    kcal = calories_burned(150, 30, 70, 30, gender='female')
    assert kcal > 0

def test_calories_burned_zero_duration():
    assert calories_burned(150, 0, 70, 30) == 0

def test_calories_burned_negative_values():
    assert isinstance(calories_burned(-10, -5, -70, -30), float)

def test_extract_heart_rate_data():
    from types import SimpleNamespace
    mock_fitfile = MagicMock()
    record1 = [SimpleNamespace(name='timestamp', value=datetime(2024,1,1,12,0,0)), SimpleNamespace(name='heart_rate', value=100)]
    record2 = [SimpleNamespace(name='timestamp', value=datetime(2024,1,1,12,1,0)), SimpleNamespace(name='heart_rate', value=110)]
    mock_fitfile.get_messages.return_value = [
        SimpleNamespace(__iter__=lambda self: iter(record1)),
        SimpleNamespace(__iter__=lambda self: iter(record2)),
    ]
    data = extract_heart_rate_data(mock_fitfile)
    assert data == [
        (datetime(2024,1,1,12,0,0), 100),
        (datetime(2024,1,1,12,1,0), 110),
    ]

def test_integrate_calories_over_intervals():
    t0 = datetime(2024,1,1,12,0,0)
    t1 = t0 + timedelta(minutes=1)
    t2 = t1 + timedelta(minutes=1)
    hr_data = [(t0, 100), (t1, 110), (t2, 120)]
    total = integrate_calories_over_intervals(hr_data, 70, 30, 'male')
    assert total > 0

@patch('src.services.fit_processor.FitFile')
@patch('os.path.exists')
@patch('os.path.isfile')
@patch('os.access')
def test_process_fit_file(mock_access, mock_isfile, mock_exists, mock_fitfile_cls):
    # Setup file existence mocks
    mock_exists.return_value = True
    mock_isfile.return_value = True
    mock_access.return_value = True
    
    mock_fitfile = MagicMock()
    t0 = datetime(2024,1,1,12,0,0)
    t1 = t0 + timedelta(minutes=1)
    from types import SimpleNamespace
    mock_fitfile.get_messages.return_value = [
        SimpleNamespace(__iter__=lambda self: iter([
            SimpleNamespace(name='timestamp', value=t0),
            SimpleNamespace(name='heart_rate', value=100)
        ])),
        SimpleNamespace(__iter__=lambda self: iter([
            SimpleNamespace(name='timestamp', value=t1),
            SimpleNamespace(name='heart_rate', value=110)
        ])),
    ]
    mock_fitfile_cls.return_value = mock_fitfile
    total = process_fit_file('fake.fit', 70, 30, 'male')
    assert total > 0

def test_load_config_reads_json():
    mock_json = '{"weight_kg": 80, "age_years": 40, "gender": "female"}'
    with patch("builtins.open", mock_open(read_data=mock_json)):
        config = load_config("dummy.json")
        assert config["weight_kg"] == 80
        assert config["age_years"] == 40
        assert config["gender"] == "female"

# Tests for error handling scenarios

def test_extract_heart_rate_data_none_fitfile():
    """Test that extract_heart_rate_data raises TypeError when fitfile is None."""
    with pytest.raises(TypeError, match="FitFile object cannot be None"):
        extract_heart_rate_data(None)

def test_extract_heart_rate_data_invalid_fitfile():
    """Test that extract_heart_rate_data raises TypeError for invalid fitfile."""
    invalid_fitfile = MagicMock()
    invalid_fitfile.get_messages.side_effect = AttributeError("No get_messages method")
    
    with pytest.raises(TypeError, match="Invalid FitFile object"):
        extract_heart_rate_data(invalid_fitfile)

def test_extract_heart_rate_data_no_data():
    """Test that extract_heart_rate_data raises MissingDataError when no heart rate data is found."""
    mock_fitfile = MagicMock()
    mock_fitfile.get_messages.return_value = []
    
    with pytest.raises(MissingDataError, match="No valid heart rate data found"):
        extract_heart_rate_data(mock_fitfile)

def test_integrate_calories_empty_data():
    """Test that integrate_calories_over_intervals raises ValueError for empty data."""
    with pytest.raises(ValueError, match="Heart rate data cannot be empty"):
        integrate_calories_over_intervals([], 70, 30, 'male')

def test_integrate_calories_single_data_point():
    """Test that integrate_calories_over_intervals raises ValueError for single data point."""
    t0 = datetime(2024,1,1,12,0,0)
    with pytest.raises(ValueError, match="At least two heart rate data points are required"):
        integrate_calories_over_intervals([(t0, 100)], 70, 30, 'male')

def test_integrate_calories_invalid_weight():
    """Test that integrate_calories_over_intervals raises ValueError for invalid weight."""
    t0 = datetime(2024,1,1,12,0,0)
    t1 = t0 + timedelta(minutes=1)
    hr_data = [(t0, 100), (t1, 110)]
    
    with pytest.raises(ValueError, match="Weight must be a positive number"):
        integrate_calories_over_intervals(hr_data, -10, 30, 'male')

def test_integrate_calories_invalid_age():
    """Test that integrate_calories_over_intervals raises ValueError for invalid age."""
    t0 = datetime(2024,1,1,12,0,0)
    t1 = t0 + timedelta(minutes=1)
    hr_data = [(t0, 100), (t1, 110)]
    
    with pytest.raises(ValueError, match="Age must be a positive number"):
        integrate_calories_over_intervals(hr_data, 70, -5, 'male')

def test_integrate_calories_invalid_gender():
    """Test that integrate_calories_over_intervals raises ValueError for invalid gender."""
    t0 = datetime(2024,1,1,12,0,0)
    t1 = t0 + timedelta(minutes=1)
    hr_data = [(t0, 100), (t1, 110)]
    
    with pytest.raises(ValueError, match="Gender must be 'male' or 'female'"):
        integrate_calories_over_intervals(hr_data, 70, 30, 'invalid')

@patch('os.path.exists')
def test_process_fit_file_nonexistent(mock_exists):
    """Test that process_fit_file raises FileNotFoundError for nonexistent file."""
    mock_exists.return_value = False
    
    with pytest.raises(FileNotFoundError, match="File not found"):
        process_fit_file('nonexistent.fit', 70, 30, 'male')

@patch('os.path.exists')
@patch('os.path.isfile')
def test_process_fit_file_not_a_file(mock_isfile, mock_exists):
    """Test that process_fit_file raises ValueError if path is not a file."""
    mock_exists.return_value = True
    mock_isfile.return_value = False
    
    with pytest.raises(ValueError, match="Not a file"):
        process_fit_file('directory.fit', 70, 30, 'male')

@patch('os.path.exists')
@patch('os.path.isfile')
@patch('os.access')
def test_process_fit_file_permission_denied(mock_access, mock_isfile, mock_exists):
    """Test that process_fit_file raises PermissionError for inaccessible file."""
    mock_exists.return_value = True
    mock_isfile.return_value = True
    mock_access.return_value = False
    
    with pytest.raises(PermissionError, match="Permission denied"):
        process_fit_file('noaccess.fit', 70, 30, 'male')

@patch('os.path.exists')
@patch('os.path.isfile')
@patch('os.access')
@patch('src.services.fit_processor.FitFile')
def test_process_fit_file_invalid_fit_file(mock_fitfile_cls, mock_access, mock_isfile, mock_exists):
    """Test that process_fit_file raises InvalidFitFileError for invalid FIT file."""
    mock_exists.return_value = True
    mock_isfile.return_value = True
    mock_access.return_value = True
    mock_fitfile_cls.side_effect = Exception("Invalid FIT file format")
    
    with pytest.raises(InvalidFitFileError, match="Error opening FIT file"):
        process_fit_file('invalid.fit', 70, 30, 'male')