"""
Tests for configuration loading
"""

import pytest
from lib.config import config, get


def test_config_loads():
    """Test that config loads without errors"""
    assert config is not None
    assert isinstance(config, dict)


def test_config_has_expected_sections():
    """Test that all expected top-level sections exist"""
    # Core py_home sections (removed tesla - not used in this project)
    expected_sections = [
        'nest',
        'locations',
        'notifications',
        'tapo',
        'sensibo',
        'automation'
    ]

    for section in expected_sections:
        assert section in config, f"Missing config section: {section}"

    # Optional sections (warn if missing but don't fail)
    optional_sections = ['alen', 'roborock', 'github', 'checkvist', 'google_maps', 'openweather']
    for section in optional_sections:
        if section not in config:
            print(f"Optional section '{section}' not configured")


def test_get_function():
    """Test the get() helper function"""
    # Test existing path (use nest config instead of tesla)
    project_id = get('nest.project_id')
    assert project_id is not None

    # Test nested path
    home_lat = get('locations.home.lat')
    assert isinstance(home_lat, (int, float))

    # Test non-existent path with default
    result = get('non.existent.path', default='default_value')
    assert result == 'default_value'

    # Test non-existent path without default
    result = get('non.existent.path')
    assert result is None


def test_env_var_substitution():
    """Test that environment variables are substituted"""
    # These should not contain ${...} after substitution
    token = get('notifications.pushover.token')

    # If .env is set up, token should be substituted
    # If using .env.example, it will be empty string
    assert not (isinstance(token, str) and token.startswith('${'))


def test_locations_config():
    """Test locations configuration"""
    # Test home location (required)
    home = config['locations']['home']
    assert 'lat' in home
    assert 'lng' in home
    assert 'radius_meters' in home

    # Test work location (if configured)
    if 'work' in config['locations']:
        work = config['locations']['work']
        assert 'lat' in work or 'address' in work  # Either lat/lng or address


def test_automation_settings():
    """Test automation settings"""
    tesla_preheat = config['automation']['tesla_preheat']
    assert 'cold_threshold_f' in tesla_preheat
    assert 'min_battery_percent' in tesla_preheat
    assert 'target_temp_f' in tesla_preheat

    assert isinstance(tesla_preheat['cold_threshold_f'], (int, float))
    assert isinstance(tesla_preheat['min_battery_percent'], (int, float))
