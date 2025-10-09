"""
Tuya Cloud API client for py_home (Alen Air Purifiers)

Controls Alen BreatheSmart 75i air purifiers using Tuya Cloud API via tinytuya library.

Setup:
1. Install: pip install tinytuya
2. Pair devices with Tuya Smart Life app (not Alen Air app)
3. Create Tuya IoT Cloud project at https://iot.tuya.com/
4. Add API credentials to config/.env
5. Configure device IDs in config/config.yaml

Requires Python 3.9+
"""

import logging
import time
from typing import Optional, Dict, List
import tinytuya

from lib.logging_config import kvlog
from .air_purifier import AlenAirPurifier

logger = logging.getLogger(__name__)


class TuyaAPI:
    """
    Tuya Cloud API client for Alen air purifiers

    Uses tinytuya library to communicate with Tuya Cloud API.
    """

    def __init__(self, dry_run=False):
        from lib.config import config

        # Get config from 'alen' section (Alen-branded Tuya devices)
        alen_config = config.get('alen', {})

        self.api_key = alen_config.get('api_key', '')
        self.api_secret = alen_config.get('api_secret', '')
        self.devices_config = alen_config.get('devices', {})
        self.thresholds = alen_config.get('thresholds', {
            'pm25_good': 25,
            'pm25_moderate': 50,
            'pm25_unhealthy': 100
        })
        self.dry_run = dry_run

        if not self.api_key or not self.api_secret:
            raise ValueError(
                "Tuya API credentials not configured. "
                "Add TUYA_API_KEY and TUYA_API_SECRET to config/.env"
            )

        if not self.devices_config:
            raise ValueError(
                "No Tuya devices configured in config/config.yaml under 'alen.devices'"
            )

        # Initialize Tuya Cloud client
        self.cloud = None
        if not dry_run:
            try:
                self.cloud = tinytuya.Cloud(
                    apiRegion="us",  # Change if using different region
                    apiKey=self.api_key,
                    apiSecret=self.api_secret
                )
                kvlog(logger, logging.INFO, api='tuya', action='init', result='ok')
            except Exception as e:
                kvlog(logger, logging.ERROR, api='tuya', action='init',
                      error_type=type(e).__name__, error_msg=str(e))
                raise

    def get_device(self, device_name: str) -> AlenAirPurifier:
        """
        Get air purifier device by name

        Args:
            device_name: Device name from config (e.g., 'bedroom', 'living_room')

        Returns:
            AlenAirPurifier instance

        Example:
            >>> tuya = TuyaAPI()
            >>> bedroom = tuya.get_device('bedroom')
            >>> bedroom.get_air_quality()
        """
        if device_name not in self.devices_config:
            raise ValueError(f"Device not found in config: {device_name}")

        device_config = self.devices_config[device_name]
        device_id = device_config.get('device_id', '')
        friendly_name = device_config.get('name', device_name)

        if not device_id:
            raise ValueError(f"Device ID not configured for: {device_name}")

        return AlenAirPurifier(
            device_id=device_id,
            name=friendly_name,
            tuya_client=self,
            dry_run=self.dry_run
        )

    def get_all_devices(self) -> List[AlenAirPurifier]:
        """
        Get all configured air purifier devices

        Returns:
            List of AlenAirPurifier instances

        Example:
            >>> tuya = TuyaAPI()
            >>> for device in tuya.get_all_devices():
            ...     print(f"{device.name}: {device.get_air_quality()}")
        """
        return [self.get_device(name) for name in self.devices_config.keys()]

    def get_device_status(self, device_id: str) -> Dict:
        """
        Get raw device status from Tuya Cloud API

        Args:
            device_id: Tuya device ID

        Returns:
            dict: Raw device status with data points (DPs)
        """
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would get status for device: {device_id}")
            return {
                'success': True,
                'result': {
                    'online': True,
                    'status': [
                        {'code': 'switch', 'value': True},
                        {'code': 'pm25', 'value': 15},
                        {'code': 'fan_speed', 'value': 3},
                        {'code': 'mode', 'value': 'auto'}
                    ]
                }
            }

        api_start = time.time()
        try:
            status = self.cloud.getstatus(device_id)
            duration_ms = int((time.time() - api_start) * 1000)
            kvlog(logger, logging.INFO, api='tuya', action='get_status',
                  device_id=device_id, result='ok', duration_ms=duration_ms)
            return status
        except Exception as e:
            duration_ms = int((time.time() - api_start) * 1000)
            kvlog(logger, logging.ERROR, api='tuya', action='get_status',
                  device_id=device_id, error_type=type(e).__name__,
                  error_msg=str(e), duration_ms=duration_ms)
            raise

    def send_command(self, device_id: str, commands: Dict) -> Dict:
        """
        Send command to Tuya device

        Args:
            device_id: Tuya device ID
            commands: Command dictionary (e.g., {'switch': True})

        Returns:
            dict: API response
        """
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would send command to {device_id}: {commands}")
            return {'success': True}

        api_start = time.time()
        try:
            response = self.cloud.sendcommand(device_id, commands)
            duration_ms = int((time.time() - api_start) * 1000)
            kvlog(logger, logging.INFO, api='tuya', action='send_command',
                  device_id=device_id, commands=str(commands), result='ok',
                  duration_ms=duration_ms)
            return response
        except Exception as e:
            duration_ms = int((time.time() - api_start) * 1000)
            kvlog(logger, logging.ERROR, api='tuya', action='send_command',
                  device_id=device_id, commands=str(commands),
                  error_type=type(e).__name__, error_msg=str(e),
                  duration_ms=duration_ms)
            raise

    def get_air_quality(self, device_name: str) -> Dict:
        """
        Get air quality reading from device

        Args:
            device_name: Device name from config

        Returns:
            dict: {
                'pm25': int,
                'aqi': int,
                'quality': str (good/moderate/unhealthy/very_unhealthy/hazardous)
            }

        Example:
            >>> tuya = TuyaAPI()
            >>> aq = tuya.get_air_quality('bedroom')
            >>> print(f"PM2.5: {aq['pm25']}, Quality: {aq['quality']}")
        """
        device = self.get_device(device_name)
        return device.get_air_quality()

    def set_power(self, device_name: str, on: bool):
        """
        Turn device on or off

        Args:
            device_name: Device name from config
            on: True to turn on, False to turn off

        Example:
            >>> tuya = TuyaAPI()
            >>> tuya.set_power('bedroom', on=True)
        """
        device = self.get_device(device_name)
        if on:
            device.turn_on()
        else:
            device.turn_off()

    def set_fan_speed(self, device_name: str, speed: int):
        """
        Set fan speed (1-5)

        Args:
            device_name: Device name from config
            speed: Fan speed (1=low, 5=high)

        Example:
            >>> tuya = TuyaAPI()
            >>> tuya.set_fan_speed('bedroom', 3)  # Medium
        """
        device = self.get_device(device_name)
        device.set_fan_speed(speed)

    def get_status(self, device_name: str) -> Dict:
        """
        Get full device status

        Args:
            device_name: Device name from config

        Returns:
            dict: {
                'on': bool,
                'pm25': int,
                'aqi': int,
                'quality': str,
                'fan_speed': int,
                'mode': str,
                'online': bool
            }

        Example:
            >>> tuya = TuyaAPI()
            >>> status = tuya.get_status('bedroom')
            >>> print(f"Power: {status['on']}, PM2.5: {status['pm25']}")
        """
        device = self.get_device(device_name)
        return device.get_status()

    def list_all_status(self) -> List[Dict]:
        """
        Get status of all configured devices

        Returns:
            List of status dicts with 'name' field added

        Example:
            >>> tuya = TuyaAPI()
            >>> for status in tuya.list_all_status():
            ...     print(f"{status['name']}: PM2.5={status['pm25']}")
        """
        results = []
        for device_name in self.devices_config.keys():
            try:
                status = self.get_status(device_name)
                status['name'] = self.devices_config[device_name]['name']
                status['device_key'] = device_name
                results.append(status)
            except Exception as e:
                logger.error(f"Failed to get status for {device_name}: {e}")
                results.append({
                    'name': self.devices_config[device_name]['name'],
                    'device_key': device_name,
                    'error': str(e)
                })
        return results


# Singleton instance
_tuya = None

def get_tuya(dry_run=False) -> TuyaAPI:
    """Get or create Tuya API instance (singleton)"""
    global _tuya
    if _tuya is None:
        _tuya = TuyaAPI(dry_run=dry_run)
    return _tuya


# Convenience functions
def get_air_quality(device_name: str) -> Dict:
    """Get air quality reading from device"""
    return get_tuya().get_air_quality(device_name)


def set_power(device_name: str, on: bool):
    """Turn device on or off"""
    return get_tuya().set_power(device_name, on)


def set_fan_speed(device_name: str, speed: int):
    """Set fan speed (1-5)"""
    return get_tuya().set_fan_speed(device_name, speed)


def get_status(device_name: str) -> Dict:
    """Get full device status"""
    return get_tuya().get_status(device_name)


def list_all_status() -> List[Dict]:
    """Get status of all devices"""
    return get_tuya().list_all_status()


__all__ = [
    'TuyaAPI', 'get_tuya',
    'get_air_quality', 'set_power', 'set_fan_speed',
    'get_status', 'list_all_status'
]
