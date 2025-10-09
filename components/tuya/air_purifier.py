"""
Alen BreatheSmart 75i Air Purifier Device Class

Wraps Tuya device API for air purifier-specific operations.
"""

import logging
from typing import Dict, Optional

from lib.logging_config import kvlog

logger = logging.getLogger(__name__)


class AlenAirPurifier:
    """
    Alen BreatheSmart 75i air purifier device

    Provides air purifier-specific methods for controlling and monitoring
    Alen devices via Tuya Cloud API.

    Common Tuya Data Points (DPs) for air purifiers:
    - switch: Power on/off
    - pm25: PM2.5 reading (μg/m³)
    - fan_speed_enum: Fan speed (1-5 or auto)
    - mode: Operating mode (auto/manual/sleep)
    - filter_life: Filter remaining life (%)
    - child_lock: Child lock on/off

    Note: Actual DP codes may vary. Use demo.py to discover device-specific DPs.
    """

    def __init__(self, device_id: str, name: str, tuya_client, dry_run=False):
        """
        Initialize air purifier device

        Args:
            device_id: Tuya device ID
            name: Friendly device name
            tuya_client: TuyaAPI instance
            dry_run: If True, simulate operations without API calls
        """
        self.device_id = device_id
        self.name = name
        self.tuya_client = tuya_client
        self.dry_run = dry_run

    def turn_on(self):
        """
        Turn air purifier on

        Example:
            >>> device = tuya.get_device('bedroom')
            >>> device.turn_on()
        """
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would turn ON: {self.name}")
            return

        try:
            self.tuya_client.send_command(self.device_id, {'switch': True})
            kvlog(logger, logging.INFO, api='tuya', device=self.name,
                  action='turn_on', result='ok')
        except Exception as e:
            kvlog(logger, logging.ERROR, api='tuya', device=self.name,
                  action='turn_on', error_type=type(e).__name__, error_msg=str(e))
            raise

    def turn_off(self):
        """
        Turn air purifier off

        Example:
            >>> device = tuya.get_device('bedroom')
            >>> device.turn_off()
        """
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would turn OFF: {self.name}")
            return

        try:
            self.tuya_client.send_command(self.device_id, {'switch': False})
            kvlog(logger, logging.INFO, api='tuya', device=self.name,
                  action='turn_off', result='ok')
        except Exception as e:
            kvlog(logger, logging.ERROR, api='tuya', device=self.name,
                  action='turn_off', error_type=type(e).__name__, error_msg=str(e))
            raise

    def set_fan_speed(self, speed: int):
        """
        Set fan speed

        Args:
            speed: Fan speed (1-5 where 1=low, 5=turbo)

        Example:
            >>> device = tuya.get_device('bedroom')
            >>> device.set_fan_speed(3)  # Medium
        """
        if not 1 <= speed <= 5:
            raise ValueError(f"Fan speed must be 1-5, got: {speed}")

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would set fan speed to {speed}: {self.name}")
            return

        try:
            # Note: DP code may vary - common codes: 'fan_speed_enum', 'speed', 'fan_speed'
            # User will need to verify correct DP code for their device
            self.tuya_client.send_command(self.device_id, {'fan_speed_enum': str(speed)})
            kvlog(logger, logging.INFO, api='tuya', device=self.name,
                  action='set_fan_speed', speed=speed, result='ok')
        except Exception as e:
            kvlog(logger, logging.ERROR, api='tuya', device=self.name,
                  action='set_fan_speed', speed=speed,
                  error_type=type(e).__name__, error_msg=str(e))
            raise

    def set_mode(self, mode: str):
        """
        Set operating mode

        Args:
            mode: Operating mode ('auto', 'manual', 'sleep')

        Example:
            >>> device = tuya.get_device('bedroom')
            >>> device.set_mode('auto')
        """
        valid_modes = ['auto', 'manual', 'sleep']
        if mode not in valid_modes:
            raise ValueError(f"Mode must be one of {valid_modes}, got: {mode}")

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would set mode to {mode}: {self.name}")
            return

        try:
            self.tuya_client.send_command(self.device_id, {'mode': mode})
            kvlog(logger, logging.INFO, api='tuya', device=self.name,
                  action='set_mode', mode=mode, result='ok')
        except Exception as e:
            kvlog(logger, logging.ERROR, api='tuya', device=self.name,
                  action='set_mode', mode=mode,
                  error_type=type(e).__name__, error_msg=str(e))
            raise

    def get_air_quality(self) -> Dict:
        """
        Get air quality reading

        Returns:
            dict: {
                'pm25': int (μg/m³),
                'aqi': int (US AQI),
                'quality': str (good/moderate/unhealthy/very_unhealthy/hazardous)
            }

        Example:
            >>> device = tuya.get_device('bedroom')
            >>> aq = device.get_air_quality()
            >>> print(f"PM2.5: {aq['pm25']}, Quality: {aq['quality']}")
        """
        if self.dry_run:
            return {
                'pm25': 15,
                'aqi': 55,
                'quality': 'good'
            }

        try:
            status = self.tuya_client.get_device_status(self.device_id)
            pm25 = self._extract_dp_value(status, 'pm25', default=0)

            # Calculate AQI from PM2.5 (US EPA formula)
            aqi = self._pm25_to_aqi(pm25)

            # Determine quality level
            quality = self._aqi_to_quality(aqi)

            kvlog(logger, logging.INFO, api='tuya', device=self.name,
                  action='get_air_quality', pm25=pm25, aqi=aqi, quality=quality,
                  result='ok')

            return {
                'pm25': pm25,
                'aqi': aqi,
                'quality': quality
            }
        except Exception as e:
            kvlog(logger, logging.ERROR, api='tuya', device=self.name,
                  action='get_air_quality', error_type=type(e).__name__,
                  error_msg=str(e))
            raise

    def get_status(self) -> Dict:
        """
        Get full device status

        Returns:
            dict: {
                'on': bool,
                'pm25': int,
                'aqi': int,
                'quality': str,
                'fan_speed': int,
                'mode': str,
                'filter_life': int (percentage),
                'online': bool
            }

        Example:
            >>> device = tuya.get_device('bedroom')
            >>> status = device.get_status()
            >>> print(f"Power: {status['on']}, PM2.5: {status['pm25']}")
        """
        if self.dry_run:
            return {
                'on': True,
                'pm25': 15,
                'aqi': 55,
                'quality': 'good',
                'fan_speed': 3,
                'mode': 'auto',
                'filter_life': 85,
                'online': True
            }

        try:
            raw_status = self.tuya_client.get_device_status(self.device_id)

            # Extract common fields
            on = self._extract_dp_value(raw_status, 'switch', default=False)
            pm25 = self._extract_dp_value(raw_status, 'pm25', default=0)
            aqi = self._pm25_to_aqi(pm25)
            quality = self._aqi_to_quality(aqi)
            fan_speed = self._extract_dp_value(raw_status, 'fan_speed_enum', default=0)
            mode = self._extract_dp_value(raw_status, 'mode', default='unknown')
            filter_life = self._extract_dp_value(raw_status, 'filter_life', default=100)
            online = raw_status.get('result', {}).get('online', False)

            # Convert fan_speed string to int if needed
            if isinstance(fan_speed, str):
                try:
                    fan_speed = int(fan_speed)
                except ValueError:
                    fan_speed = 0

            status = {
                'on': on,
                'pm25': pm25,
                'aqi': aqi,
                'quality': quality,
                'fan_speed': fan_speed,
                'mode': mode,
                'filter_life': filter_life,
                'online': online
            }

            kvlog(logger, logging.INFO, api='tuya', device=self.name,
                  action='get_status', on=on, pm25=pm25, aqi=aqi, quality=quality,
                  result='ok')

            return status
        except Exception as e:
            kvlog(logger, logging.ERROR, api='tuya', device=self.name,
                  action='get_status', error_type=type(e).__name__, error_msg=str(e))
            raise

    def is_on(self) -> bool:
        """
        Check if device is powered on

        Returns:
            bool: True if on, False if off

        Example:
            >>> device = tuya.get_device('bedroom')
            >>> if device.is_on():
            ...     print("Purifier is running")
        """
        status = self.get_status()
        return status.get('on', False)

    def _extract_dp_value(self, status: Dict, dp_code: str, default=None):
        """
        Extract data point value from Tuya status response

        Args:
            status: Raw status dict from Tuya API
            dp_code: Data point code (e.g., 'pm25', 'switch')
            default: Default value if DP not found

        Returns:
            Data point value or default
        """
        result = status.get('result', {})
        status_list = result.get('status', [])

        for dp in status_list:
            if dp.get('code') == dp_code:
                return dp.get('value', default)

        return default

    def _pm25_to_aqi(self, pm25: float) -> int:
        """
        Convert PM2.5 to US EPA AQI

        Args:
            pm25: PM2.5 concentration (μg/m³)

        Returns:
            int: AQI value

        AQI Breakpoints (PM2.5):
        0-12.0   → 0-50   (Good)
        12.1-35.4 → 51-100 (Moderate)
        35.5-55.4 → 101-150 (Unhealthy for Sensitive)
        55.5-150.4 → 151-200 (Unhealthy)
        150.5-250.4 → 201-300 (Very Unhealthy)
        250.5+ → 301-500 (Hazardous)
        """
        breakpoints = [
            (0, 12.0, 0, 50),
            (12.1, 35.4, 51, 100),
            (35.5, 55.4, 101, 150),
            (55.5, 150.4, 151, 200),
            (150.5, 250.4, 201, 300),
            (250.5, 500.4, 301, 500)
        ]

        for pm_low, pm_high, aqi_low, aqi_high in breakpoints:
            if pm_low <= pm25 <= pm_high:
                # Linear interpolation
                aqi = ((aqi_high - aqi_low) / (pm_high - pm_low)) * (pm25 - pm_low) + aqi_low
                return int(round(aqi))

        # If above all breakpoints, return max
        return 500

    def _aqi_to_quality(self, aqi: int) -> str:
        """
        Convert AQI to quality description

        Args:
            aqi: AQI value

        Returns:
            str: Quality description
        """
        if aqi <= 50:
            return 'good'
        elif aqi <= 100:
            return 'moderate'
        elif aqi <= 150:
            return 'unhealthy_sensitive'
        elif aqi <= 200:
            return 'unhealthy'
        elif aqi <= 300:
            return 'very_unhealthy'
        else:
            return 'hazardous'


__all__ = ['AlenAirPurifier']
