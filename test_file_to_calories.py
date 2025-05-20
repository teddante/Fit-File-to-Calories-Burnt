import pytest
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime, timedelta
from file_to_calories import (
    calories_burned,
    extract_heart_rate_data,
    integrate_calories_over_intervals,
    process_fit_file,
    load_config,
)

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

@patch('file_to_calories.FitFile')
def test_process_fit_file(mock_fitfile_cls):
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