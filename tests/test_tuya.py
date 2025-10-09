#!/usr/bin/env python
"""
Test Tuya integration (Alen air purifiers)

Tests dry-run mode without requiring actual Tuya API credentials.
"""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from components.tuya.air_purifier import AlenAirPurifier


class MockTuyaClient:
    """Mock Tuya client for testing"""

    def __init__(self):
        self.dry_run = True
        self.last_command = None

    def get_device_status(self, device_id):
        """Mock device status"""
        return {
            'success': True,
            'result': {
                'online': True,
                'status': [
                    {'code': 'switch', 'value': True},
                    {'code': 'pm25', 'value': 15},
                    {'code': 'fan_speed_enum', 'value': '3'},
                    {'code': 'mode', 'value': 'auto'},
                    {'code': 'filter_life', 'value': 85}
                ]
            }
        }

    def send_command(self, device_id, commands):
        """Mock send command"""
        self.last_command = commands
        return {'success': True}


class TestAlenAirPurifier(unittest.TestCase):
    """Test Alen air purifier device class"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = MockTuyaClient()
        self.device = AlenAirPurifier(
            device_id='test_device_123',
            name='Test Bedroom',
            tuya_client=self.mock_client,
            dry_run=True
        )

    def test_init(self):
        """Test device initialization"""
        self.assertEqual(self.device.device_id, 'test_device_123')
        self.assertEqual(self.device.name, 'Test Bedroom')
        self.assertTrue(self.device.dry_run)

    def test_turn_on_dry_run(self):
        """Test turn on in dry-run mode"""
        # Should not raise exception
        self.device.turn_on()

    def test_turn_off_dry_run(self):
        """Test turn off in dry-run mode"""
        # Should not raise exception
        self.device.turn_off()

    def test_set_fan_speed(self):
        """Test fan speed setting"""
        # Valid speeds
        for speed in range(1, 6):
            self.device.set_fan_speed(speed)

        # Invalid speeds
        with self.assertRaises(ValueError):
            self.device.set_fan_speed(0)
        with self.assertRaises(ValueError):
            self.device.set_fan_speed(6)

    def test_set_mode(self):
        """Test mode setting"""
        # Valid modes
        for mode in ['auto', 'manual', 'sleep']:
            self.device.set_mode(mode)

        # Invalid mode
        with self.assertRaises(ValueError):
            self.device.set_mode('invalid')

    def test_get_air_quality_dry_run(self):
        """Test air quality reading in dry-run mode"""
        aq = self.device.get_air_quality()
        self.assertIn('pm25', aq)
        self.assertIn('aqi', aq)
        self.assertIn('quality', aq)
        self.assertEqual(aq['pm25'], 15)
        self.assertEqual(aq['quality'], 'good')

    def test_get_status_dry_run(self):
        """Test status reading in dry-run mode"""
        status = self.device.get_status()
        self.assertIn('on', status)
        self.assertIn('pm25', status)
        self.assertIn('aqi', status)
        self.assertIn('quality', status)
        self.assertIn('fan_speed', status)
        self.assertIn('mode', status)
        self.assertIn('filter_life', status)
        self.assertIn('online', status)

    def test_is_on_dry_run(self):
        """Test is_on check in dry-run mode"""
        self.assertTrue(self.device.is_on())

    def test_pm25_to_aqi_conversion(self):
        """Test PM2.5 to AQI conversion"""
        test_cases = [
            (0, 0),      # Good
            (12, 50),    # Good upper
            (35, 99),    # Moderate
            (55, 150),   # Unhealthy for sensitive
            (150, 200),  # Unhealthy
            (250, 300),  # Very unhealthy
            (500, 500)   # Hazardous
        ]

        for pm25, expected_aqi_approx in test_cases:
            aqi = self.device._pm25_to_aqi(pm25)
            # Allow some tolerance for rounding
            self.assertAlmostEqual(aqi, expected_aqi_approx, delta=5,
                                   msg=f"PM2.5 {pm25} should convert to AQI ~{expected_aqi_approx}")

    def test_aqi_to_quality_conversion(self):
        """Test AQI to quality description conversion"""
        test_cases = [
            (0, 'good'),
            (50, 'good'),
            (51, 'moderate'),
            (100, 'moderate'),
            (101, 'unhealthy_sensitive'),
            (150, 'unhealthy_sensitive'),
            (151, 'unhealthy'),
            (200, 'unhealthy'),
            (201, 'very_unhealthy'),
            (300, 'very_unhealthy'),
            (301, 'hazardous'),
            (500, 'hazardous')
        ]

        for aqi, expected_quality in test_cases:
            quality = self.device._aqi_to_quality(aqi)
            self.assertEqual(quality, expected_quality,
                             msg=f"AQI {aqi} should be '{expected_quality}'")

    def test_extract_dp_value(self):
        """Test data point extraction from Tuya status"""
        status = {
            'result': {
                'status': [
                    {'code': 'switch', 'value': True},
                    {'code': 'pm25', 'value': 42},
                ]
            }
        }

        # Test existing DP
        self.assertEqual(self.device._extract_dp_value(status, 'switch'), True)
        self.assertEqual(self.device._extract_dp_value(status, 'pm25'), 42)

        # Test missing DP with default
        self.assertEqual(self.device._extract_dp_value(status, 'missing', default=99), 99)

    def test_get_air_quality_with_mock(self):
        """Test air quality reading with mock client"""
        # Switch to non-dry-run to use mock client
        self.device.dry_run = False

        aq = self.device.get_air_quality()
        self.assertEqual(aq['pm25'], 15)
        self.assertEqual(aq['aqi'], 57)  # PM2.5 of 15 → AQI ~57
        self.assertEqual(aq['quality'], 'moderate')

    def test_get_status_with_mock(self):
        """Test status reading with mock client"""
        # Switch to non-dry-run to use mock client
        self.device.dry_run = False

        status = self.device.get_status()
        self.assertTrue(status['on'])
        self.assertEqual(status['pm25'], 15)
        self.assertEqual(status['fan_speed'], 3)
        self.assertEqual(status['mode'], 'auto')
        self.assertEqual(status['filter_life'], 85)
        self.assertTrue(status['online'])


class TestTuyaAPI(unittest.TestCase):
    """Test TuyaAPI client (requires config or mock)"""

    def test_import(self):
        """Test that TuyaAPI can be imported"""
        from components.tuya import TuyaAPI
        self.assertIsNotNone(TuyaAPI)

    def test_convenience_functions_import(self):
        """Test that convenience functions can be imported"""
        from components.tuya import (
            get_air_quality, set_power, set_fan_speed,
            get_status, list_all_status
        )
        self.assertIsNotNone(get_air_quality)
        self.assertIsNotNone(set_power)
        self.assertIsNotNone(set_fan_speed)
        self.assertIsNotNone(get_status)
        self.assertIsNotNone(list_all_status)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
