#!/usr/bin/env python
"""
Tests for Weather-Aware Temperature Logic

Verifies that transition_to_wake() adjusts wake temperature based on outdoor conditions:
- Cold weather (< 40°F): Target 72°F for extra warmth
- Hot weather (> 75°F): Target 68°F to avoid overheating
- Normal weather (40-75°F): Target 70°F (config default)
"""

import pytest
from unittest.mock import patch


class TestWeatherAwareTemperatures:
    """Test weather-aware wake temperature adjustments"""

    def test_cold_weather_targets_warmer_temp(self):
        """Test cold weather (< 40°F) targets 72°F"""
        from lib.transitions import transition_to_wake

        with patch('services.openweather.get_current_weather') as mock_weather:
            mock_weather.return_value = {'temp': 35, 'conditions': 'clear sky'}

            result = transition_to_wake(dry_run=True)

            # Verify weather was fetched
            assert result['weather'] == '35°F, clear sky'

            # Verify warmer target for cold weather
            assert '72°F' in result['actions'][0], \
                   f"Expected 72°F for cold weather, got {result['actions'][0]}"

    def test_hot_weather_targets_cooler_temp(self):
        """Test hot weather (> 75°F) targets 68°F"""
        from lib.transitions import transition_to_wake

        with patch('services.openweather.get_current_weather') as mock_weather:
            mock_weather.return_value = {'temp': 80, 'conditions': 'sunny'}

            result = transition_to_wake(dry_run=True)

            # Verify weather was fetched
            assert result['weather'] == '80°F, sunny'

            # Verify cooler target for hot weather
            assert '68°F' in result['actions'][0], \
                   f"Expected 68°F for hot weather, got {result['actions'][0]}"

    def test_normal_weather_targets_default_temp(self):
        """Test normal weather (40-75°F) targets 70°F (config default)"""
        from lib.transitions import transition_to_wake

        with patch('services.openweather.get_current_weather') as mock_weather:
            mock_weather.return_value = {'temp': 60, 'conditions': 'partly cloudy'}

            result = transition_to_wake(dry_run=True)

            # Verify weather was fetched
            assert result['weather'] == '60°F, partly cloudy'

            # Verify default target for normal weather
            assert '70°F' in result['actions'][0], \
                   f"Expected 70°F for normal weather, got {result['actions'][0]}"

    def test_boundary_cold_weather_39_degrees(self):
        """Test boundary: 39°F should trigger cold weather logic (72°F)"""
        from lib.transitions import transition_to_wake

        with patch('services.openweather.get_current_weather') as mock_weather:
            mock_weather.return_value = {'temp': 39, 'conditions': 'cold'}

            result = transition_to_wake(dry_run=True)

            assert '72°F' in result['actions'][0], \
                   "39°F should trigger cold weather target (72°F)"

    def test_boundary_hot_weather_76_degrees(self):
        """Test boundary: 76°F should trigger hot weather logic (68°F)"""
        from lib.transitions import transition_to_wake

        with patch('services.openweather.get_current_weather') as mock_weather:
            mock_weather.return_value = {'temp': 76, 'conditions': 'hot'}

            result = transition_to_wake(dry_run=True)

            assert '68°F' in result['actions'][0], \
                   "76°F should trigger hot weather target (68°F)"

    def test_weather_api_failure_uses_fallback(self):
        """Test graceful fallback when weather API fails"""
        from lib.transitions import transition_to_wake

        with patch('services.openweather.get_current_weather') as mock_weather:
            mock_weather.side_effect = Exception("API unavailable")

            result = transition_to_wake(dry_run=True)

            # Should still work with fallback temperature
            assert 'actions' in result
            assert len(result['actions']) > 0


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
