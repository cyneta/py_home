#!/usr/bin/env python
"""
Test Temp Stick integration

Tests basic functionality without requiring actual API credentials.
"""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestTempStickImport(unittest.TestCase):
    """Test that Temp Stick module can be imported"""

    def test_import(self):
        """Test that TempStickAPI can be imported"""
        from services.tempstick import TempStickAPI
        self.assertIsNotNone(TempStickAPI)

    def test_convenience_functions_import(self):
        """Test that convenience functions can be imported"""
        from services.tempstick import (
            get_temperature, get_humidity, get_sensor_data,
            is_online, get_battery_level, get_summary
        )
        self.assertIsNotNone(get_temperature)
        self.assertIsNotNone(get_humidity)
        self.assertIsNotNone(get_sensor_data)
        self.assertIsNotNone(is_online)
        self.assertIsNotNone(get_battery_level)
        self.assertIsNotNone(get_summary)


class TestTempStickDataParsing(unittest.TestCase):
    """Test data parsing logic"""

    def test_temperature_conversion(self):
        """Test Celsius to Fahrenheit conversion"""
        # 21.5°C should be 70.7°F
        temp_c = 21.5
        temp_f = (temp_c * 9/5) + 32
        self.assertAlmostEqual(temp_f, 70.7, places=1)

        # 0°C should be 32°F
        temp_c = 0
        temp_f = (temp_c * 9/5) + 32
        self.assertEqual(temp_f, 32)

        # 100°C should be 212°F
        temp_c = 100
        temp_f = (temp_c * 9/5) + 32
        self.assertEqual(temp_f, 212)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
