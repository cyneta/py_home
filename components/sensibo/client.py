"""
Sensibo API client for py_home

Controls mini-split AC units via Sensibo Sky/Air devices.

Setup:
1. Get API key from https://home.sensibo.com/me/api
2. Add to config/.env: SENSIBO_API_KEY=your_key
3. Get device ID by running: python scripts/list_sensibo_devices.py
"""

import requests
import logging
import time
from lib.logging_config import kvlog

logger = logging.getLogger(__name__)


class SensiboAPI:
    """
    Sensibo API client for controlling mini-split AC units

    Official API docs: https://sensibo.github.io
    """

    BASE_URL = "https://home.sensibo.com/api/v2"

    def __init__(self, api_key=None, device_id=None, dry_run=False):
        from lib.config import config

        self.api_key = api_key or config['sensibo']['api_key']
        self.device_id = device_id or config['sensibo'].get('bedroom_ac_id')
        self.dry_run = dry_run

        if not self.api_key:
            raise ValueError(
                "Sensibo API key not configured. "
                "Get one at https://home.sensibo.com/me/api and add to config/.env"
            )

    def _get(self, endpoint, params=None):
        """GET request to Sensibo API"""
        if params is None:
            params = {}
        params['apiKey'] = self.api_key

        api_start = time.time()
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            resp = requests.get(url, params=params)
            resp.raise_for_status()

            data = resp.json()
            if data.get('status') != 'success':
                raise Exception(f"Sensibo API error: {data}")

            result = data.get('result')
            duration_ms = int((time.time() - api_start) * 1000)
            kvlog(logger, logging.INFO, api='sensibo', action='get', endpoint=endpoint, result='ok', duration_ms=duration_ms)
            return result
        except Exception as e:
            duration_ms = int((time.time() - api_start) * 1000)
            kvlog(logger, logging.ERROR, api='sensibo', action='get', endpoint=endpoint,
                  error_type=type(e).__name__, error_msg=str(e), duration_ms=duration_ms)
            raise

    def _patch(self, endpoint, data):
        """PATCH request to Sensibo API"""
        api_start = time.time()
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            params = {'apiKey': self.api_key}

            resp = requests.patch(url, params=params, json=data)
            resp.raise_for_status()

            result = resp.json()
            if result.get('status') != 'success':
                raise Exception(f"Sensibo API error: {result}")

            res = result.get('result')
            duration_ms = int((time.time() - api_start) * 1000)
            kvlog(logger, logging.INFO, api='sensibo', action='patch', endpoint=endpoint, result='ok', duration_ms=duration_ms)
            return res
        except Exception as e:
            duration_ms = int((time.time() - api_start) * 1000)
            kvlog(logger, logging.ERROR, api='sensibo', action='patch', endpoint=endpoint,
                  error_type=type(e).__name__, error_msg=str(e), duration_ms=duration_ms)
            raise

    def _post(self, endpoint, data):
        """POST request to Sensibo API"""
        api_start = time.time()
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            params = {'apiKey': self.api_key}

            resp = requests.post(url, params=params, json=data)
            resp.raise_for_status()

            result = resp.json()
            if result.get('status') != 'success':
                raise Exception(f"Sensibo API error: {result}")

            res = result.get('result')
            duration_ms = int((time.time() - api_start) * 1000)
            kvlog(logger, logging.INFO, api='sensibo', action='post', endpoint=endpoint, result='ok', duration_ms=duration_ms)
            return res
        except Exception as e:
            duration_ms = int((time.time() - api_start) * 1000)
            kvlog(logger, logging.ERROR, api='sensibo', action='post', endpoint=endpoint,
                  error_type=type(e).__name__, error_msg=str(e), duration_ms=duration_ms)
            raise

    def list_devices(self):
        """
        List all Sensibo devices on account

        Returns:
            list: Device info dicts with id, room name, etc.
        """
        pods = self._get("users/me/pods", params={'fields': 'id,room'})
        logger.info(f"Found {len(pods)} Sensibo device(s)")
        return pods

    def get_status(self, device_id=None):
        """
        Get current AC status

        Args:
            device_id: Device ID (uses default if not specified)

        Returns:
            dict: {
                'on': bool,
                'mode': str ('cool', 'heat', 'fan', 'dry', 'auto'),
                'target_temp_f': float,
                'target_temp_c': float,
                'fan_level': str ('low', 'medium', 'high', 'auto'),
                'swing': str ('stopped', 'rangeFull', etc.),
                'current_temp_f': float,
                'current_temp_c': float,
                'current_humidity': int
            }
        """
        device_id = device_id or self.device_id
        if not device_id:
            raise ValueError("No device_id specified")

        # Get AC state
        data = self._get(f"pods/{device_id}", params={
            'fields': 'acState,measurements,room'
        })

        ac_state = data['acState']
        measurements = data.get('measurements', {})

        # Current temperature/humidity
        current_temp_c = measurements.get('temperature')
        current_temp_f = self._c_to_f(current_temp_c) if current_temp_c else None
        current_humidity = measurements.get('humidity')

        # Target temperature (already in the unit specified by temperatureUnit)
        target_temp = ac_state.get('targetTemperature')
        temp_unit = ac_state.get('temperatureUnit', 'C')

        if temp_unit == 'F':
            target_temp_f = target_temp
            target_temp_c = self._f_to_c(target_temp) if target_temp else None
        else:
            target_temp_c = target_temp
            target_temp_f = self._c_to_f(target_temp) if target_temp else None

        result = {
            'on': ac_state.get('on', False),
            'mode': ac_state.get('mode'),
            'target_temp_f': target_temp_f,
            'target_temp_c': target_temp_c,
            'fan_level': ac_state.get('fanLevel'),
            'swing': ac_state.get('swing'),
            'current_temp_f': current_temp_f,
            'current_temp_c': current_temp_c,
            'current_humidity': current_humidity,
            'room': data.get('room', {}).get('name', 'Unknown')
        }

        logger.info(
            f"Sensibo ({result['room']}): {'ON' if result['on'] else 'OFF'}, "
            f"mode={result['mode']}, target={result['target_temp_f']}°F, "
            f"current={result['current_temp_f']}°F"
        )

        return result

    def set_ac_state(self, device_id=None, **kwargs):
        """
        Set AC state

        Args:
            device_id: Device ID (uses default if not specified)
            on: bool - Turn on/off
            mode: str - 'cool', 'heat', 'fan', 'dry', 'auto'
            target_temp_f: float - Target temperature in Fahrenheit
            target_temp_c: float - Target temperature in Celsius (alternative)
            fan_level: str - 'low', 'medium', 'high', 'auto'
            swing: str - 'stopped', 'rangeFull', etc.

        Example:
            >>> sensibo.set_ac_state(on=True, mode='cool', target_temp_f=72)
        """
        device_id = device_id or self.device_id
        if not device_id:
            raise ValueError("No device_id specified")

        # Build AC state update
        ac_state = {}

        if 'on' in kwargs:
            ac_state['on'] = kwargs['on']

        if 'mode' in kwargs:
            ac_state['mode'] = kwargs['mode']

        # Note: Sensibo API uses the unit set on the device (F or C)
        # We need to check current temperatureUnit or just send the value as-is
        if 'target_temp_f' in kwargs:
            # Send as integer, Sensibo will interpret based on device's temperatureUnit setting
            ac_state['targetTemperature'] = int(kwargs['target_temp_f'])
        elif 'target_temp_c' in kwargs:
            ac_state['targetTemperature'] = int(kwargs['target_temp_c'])

        if 'fan_level' in kwargs:
            ac_state['fanLevel'] = kwargs['fan_level']

        if 'swing' in kwargs:
            ac_state['swing'] = kwargs['swing']

        if not ac_state:
            raise ValueError("No AC state changes specified")

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would update Sensibo AC state: {ac_state}")
            logger.info(f"[DRY-RUN] Device: {device_id}")
            return

        # Send update
        self._post(f"pods/{device_id}/acStates", {
            'acState': ac_state
        })

        logger.info(f"Sensibo AC state updated: {ac_state}")

    def turn_on(self, mode='cool', temp_f=72, device_id=None):
        """
        Turn on AC with specified settings

        Args:
            mode: 'cool', 'heat', 'fan', 'dry', 'auto'
            temp_f: Target temperature in Fahrenheit
            device_id: Device ID (optional)

        Example:
            >>> sensibo.turn_on(mode='cool', temp_f=72)
        """
        self.set_ac_state(
            device_id=device_id,
            on=True,
            mode=mode,
            target_temp_f=temp_f
        )
        logger.info(f"Sensibo turned ON: {mode} mode, {temp_f}°F")

    def turn_off(self, device_id=None):
        """
        Turn off AC

        Args:
            device_id: Device ID (optional)

        Example:
            >>> sensibo.turn_off()
        """
        self.set_ac_state(device_id=device_id, on=False)
        logger.info("Sensibo turned OFF")

    def set_temperature(self, temp_f, device_id=None):
        """
        Set target temperature (AC must already be on)

        Args:
            temp_f: Target temperature in Fahrenheit
            device_id: Device ID (optional)

        Example:
            >>> sensibo.set_temperature(72)
        """
        self.set_ac_state(device_id=device_id, target_temp_f=temp_f)
        logger.info(f"Sensibo temperature set to {temp_f}°F")

    # Temperature conversion helpers
    @staticmethod
    def _f_to_c(fahrenheit):
        """Convert Fahrenheit to Celsius (rounded to 1 decimal)"""
        return round((fahrenheit - 32) * 5 / 9, 1)

    @staticmethod
    def _c_to_f(celsius):
        """Convert Celsius to Fahrenheit (rounded to 1 decimal)"""
        return round(celsius * 9 / 5 + 32, 1)


# Singleton instance
_sensibo = None

def get_sensibo():
    """Get or create Sensibo API instance"""
    global _sensibo
    if _sensibo is None:
        _sensibo = SensiboAPI()
    return _sensibo


# Convenience functions
def get_status(device_id=None):
    """Get current AC status"""
    return get_sensibo().get_status(device_id)


def turn_on(mode='cool', temp_f=72, device_id=None):
    """Turn on AC"""
    return get_sensibo().turn_on(mode, temp_f, device_id)


def turn_off(device_id=None):
    """Turn off AC"""
    return get_sensibo().turn_off(device_id)


def set_temperature(temp_f, device_id=None):
    """Set target temperature"""
    return get_sensibo().set_temperature(temp_f, device_id)


__all__ = [
    'SensiboAPI', 'get_sensibo', 'get_status',
    'turn_on', 'turn_off', 'set_temperature'
]
