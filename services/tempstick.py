"""
Temp Stick WiFi Temperature & Humidity Sensor API

Monitors temperature and humidity from Temp Stick sensors via cloud API.

Setup:
1. Get API key from https://tempstick.com/ account dashboard
2. Get sensor ID from web interface (format: TS00XXXXXX)
3. Add to config/.env: TEMPSTICK_API_KEY and TEMPSTICK_SENSOR_ID
4. Configure in config/config.yaml

API Docs: https://tempstickapi.com/docs/
"""

import requests
import logging
import time
from datetime import datetime, timezone
from lib.logging_config import kvlog

logger = logging.getLogger(__name__)


class TempStickAPI:
    """
    Temp Stick API client for temperature and humidity monitoring

    Uses cloud API at tempstickapi.com to retrieve sensor data.
    """

    BASE_URL = "https://tempstickapi.com/api/v1"

    def __init__(self, api_key=None, sensor_id=None):
        from lib.config import config

        tempstick_config = config.get('tempstick', {})
        self.api_key = api_key or tempstick_config.get('api_key', '')
        self.sensor_id = sensor_id or tempstick_config.get('sensor_id', '')

        if not self.api_key:
            raise ValueError(
                "Temp Stick API key not configured. "
                "Add TEMPSTICK_API_KEY to config/.env"
            )

        if not self.sensor_id:
            raise ValueError(
                "Temp Stick sensor ID not configured. "
                "Add TEMPSTICK_SENSOR_ID to config/.env or sensor_id to config.yaml"
            )

    def _get(self, endpoint):
        """Make GET request to Temp Stick API"""
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {"X-API-KEY": self.api_key}

        api_start = time.time()
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()

            result = resp.json()
            duration_ms = int((time.time() - api_start) * 1000)
            kvlog(logger, logging.INFO, api='tempstick', action='get', endpoint=endpoint,
                  result='ok', duration_ms=duration_ms)
            return result
        except Exception as e:
            duration_ms = int((time.time() - api_start) * 1000)
            kvlog(logger, logging.ERROR, api='tempstick', action='get', endpoint=endpoint,
                  error_type=type(e).__name__, error_msg=str(e), duration_ms=duration_ms)
            raise

    def get_sensor_data(self, sensor_id=None):
        """
        Get current sensor data

        Args:
            sensor_id: Optional sensor ID (uses configured if not provided)

        Returns:
            dict: {
                'sensor_id': str,
                'temperature_c': float,
                'temperature_f': float,
                'humidity': float,
                'battery_pct': int,
                'last_checkin': datetime,
                'is_online': bool,
                'rssi': int (WiFi signal strength),
                'voltage': float
            }

        Example:
            >>> tempstick = TempStickAPI()
            >>> data = tempstick.get_sensor_data()
            >>> print(f"{data['temperature_f']}°F, {data['humidity']}%")
        """
        sid = sensor_id or self.sensor_id
        response = self._get(f"sensor/{sid}")

        if response.get('type') != 'success':
            raise ValueError(f"API error: {response.get('message', 'Unknown error')}")

        raw_data = response['data']

        # Parse last check-in timestamp
        last_checkin_str = raw_data['last_checkin']
        try:
            # Format: "2025-10-09 21:34:08-00:00Z"
            # Remove trailing Z, then parse (timezone offset already present)
            cleaned_str = last_checkin_str.rstrip('Z')
            last_checkin = datetime.fromisoformat(cleaned_str)
        except Exception as e:
            logger.warning(f"Failed to parse timestamp '{last_checkin_str}': {e}")
            last_checkin = None

        # Use TempStick API's offline flag (0 = online, 1 = offline)
        # The API knows better than we do when a sensor is truly offline
        # (sensors may check in less frequently than 30 min under normal operation)
        offline_flag = int(raw_data.get('offline', 0))
        is_online = (offline_flag == 0)

        # Calculate time since last check-in for logging/debugging
        time_since_checkin_minutes = None
        if last_checkin:
            time_since_checkin = datetime.now(timezone.utc) - last_checkin
            time_since_checkin_minutes = time_since_checkin.total_seconds() / 60

        # Convert temperature to Fahrenheit
        temp_c = float(raw_data['last_temp'])
        temp_f = (temp_c * 9/5) + 32

        data = {
            'sensor_id': raw_data['sensor_id'],
            'sensor_name': raw_data['sensor_name'],
            'temperature_c': temp_c,
            'temperature_f': round(temp_f, 1),
            'humidity': float(raw_data['last_humidity']),
            'battery_pct': int(raw_data['battery_pct']),
            'voltage': float(raw_data['last_voltage']),
            'last_checkin': last_checkin,
            'is_online': is_online,
            'rssi': int(raw_data['rssi']),
            'wifi_network': raw_data.get('wlanA', 'unknown'),
            'offline_flag': int(raw_data.get('offline', 0))
        }

        # Build log with optional time_since_checkin
        log_data = {
            'api': 'tempstick',
            'action': 'get_sensor_data',
            'sensor_id': data['sensor_id'],
            'temp_f': data['temperature_f'],
            'humidity': data['humidity'],
            'battery_pct': data['battery_pct'],
            'is_online': is_online,
            'offline_flag': offline_flag
        }
        if time_since_checkin_minutes is not None:
            log_data['minutes_since_checkin'] = round(time_since_checkin_minutes, 1)

        kvlog(logger, logging.INFO, **log_data)

        return data

    def get_temperature(self, sensor_id=None, unit='F'):
        """
        Get current temperature

        Args:
            sensor_id: Optional sensor ID
            unit: 'F' for Fahrenheit, 'C' for Celsius

        Returns:
            float: Temperature in specified unit

        Example:
            >>> tempstick = TempStickAPI()
            >>> temp = tempstick.get_temperature()
            >>> print(f"Current temperature: {temp}°F")
        """
        data = self.get_sensor_data(sensor_id)
        if unit.upper() == 'C':
            return data['temperature_c']
        return data['temperature_f']

    def get_humidity(self, sensor_id=None):
        """
        Get current humidity

        Args:
            sensor_id: Optional sensor ID

        Returns:
            float: Relative humidity percentage

        Example:
            >>> tempstick = TempStickAPI()
            >>> humidity = tempstick.get_humidity()
            >>> print(f"Humidity: {humidity}%")
        """
        data = self.get_sensor_data(sensor_id)
        return data['humidity']

    def is_online(self, sensor_id=None):
        """
        Check if sensor is online (checked in within last 30 minutes)

        Args:
            sensor_id: Optional sensor ID

        Returns:
            bool: True if online, False if offline

        Example:
            >>> tempstick = TempStickAPI()
            >>> if not tempstick.is_online():
            ...     print("Warning: Temp Stick sensor offline!")
        """
        data = self.get_sensor_data(sensor_id)
        return data['is_online']

    def get_battery_level(self, sensor_id=None):
        """
        Get battery level

        Args:
            sensor_id: Optional sensor ID

        Returns:
            int: Battery percentage (0-100)

        Example:
            >>> tempstick = TempStickAPI()
            >>> battery = tempstick.get_battery_level()
            >>> if battery < 20:
            ...     print(f"Low battery: {battery}%")
        """
        data = self.get_sensor_data(sensor_id)
        return data['battery_pct']

    def get_summary(self, sensor_id=None):
        """
        Get human-readable summary of sensor status

        Args:
            sensor_id: Optional sensor ID

        Returns:
            str: Formatted summary

        Example:
            >>> tempstick = TempStickAPI()
            >>> print(tempstick.get_summary())
            "Temp Stick: 70.7°F, 50.4% humidity, Battery: 100%, Status: Offline"
        """
        data = self.get_sensor_data(sensor_id)

        status = "Online" if data['is_online'] else "⚠️ Offline"
        summary = (
            f"{data['sensor_name']}: {data['temperature_f']:.1f}°F, "
            f"{data['humidity']:.1f}% humidity, "
            f"Battery: {data['battery_pct']}%, "
            f"Status: {status}"
        )

        return summary


# Singleton instance
_tempstick = None

def get_tempstick():
    """Get or create Temp Stick API instance"""
    global _tempstick
    if _tempstick is None:
        _tempstick = TempStickAPI()
    return _tempstick


# Convenience functions
def get_temperature(unit='F'):
    """Get current temperature"""
    return get_tempstick().get_temperature(unit=unit)


def get_humidity():
    """Get current humidity"""
    return get_tempstick().get_humidity()


def get_sensor_data():
    """Get full sensor data"""
    return get_tempstick().get_sensor_data()


def is_online():
    """Check if sensor is online"""
    return get_tempstick().is_online()


def get_battery_level():
    """Get battery level"""
    return get_tempstick().get_battery_level()


def get_summary():
    """Get human-readable summary"""
    return get_tempstick().get_summary()


__all__ = [
    'TempStickAPI',
    'get_tempstick',
    'get_temperature',
    'get_humidity',
    'get_sensor_data',
    'is_online',
    'get_battery_level',
    'get_summary'
]
