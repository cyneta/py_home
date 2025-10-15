"""
Google Nest Thermostat API client for py_home

Uses Google Smart Device Management (SDM) API to control Nest thermostats.

Setup required:
1. Device Access registration ($5 one-time)
2. Google Cloud project with SDM API enabled
3. OAuth2 credentials
4. Refresh token from initial auth

See docs/NEST_API_SETUP.md for detailed setup instructions.
"""

import requests
import logging
import time
from datetime import datetime, timedelta
from lib.logging_config import kvlog

logger = logging.getLogger(__name__)


class NestAPI:
    """
    Google Nest thermostat API client

    Handles authentication, token refresh, and thermostat control.
    """

    BASE_URL = "https://smartdevicemanagement.googleapis.com/v1"
    TOKEN_URL = "https://oauth2.googleapis.com/token"

    def __init__(self, dry_run=False):
        from lib.config import config

        self.project_id = config['nest']['project_id']
        self.device_id = config['nest']['device_id']
        self.client_id = config['nest']['client_id']
        self.client_secret = config['nest']['client_secret']
        self.refresh_token = config['nest']['refresh_token']
        self.dry_run = dry_run

        self.access_token = None
        self.token_expiry = None

        # Ensure we have valid credentials
        if not all([self.project_id, self.device_id, self.client_id,
                    self.client_secret, self.refresh_token]):
            raise ValueError(
                "Nest API credentials incomplete. "
                "Check config/.env and see docs/NEST_API_SETUP.md"
            )

    def _ensure_token(self):
        """Ensure we have a valid access token, refresh if needed"""
        if self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry:
                return  # Token still valid

        # Get new access token using refresh token
        logger.info("Refreshing Nest API access token")

        api_start = time.time()
        try:
            resp = requests.post(self.TOKEN_URL, data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            })

            resp.raise_for_status()
            data = resp.json()

            self.access_token = data['access_token']
            # Tokens typically expire in 3600 seconds, refresh early
            expires_in = data.get('expires_in', 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)

            duration_ms = int((time.time() - api_start) * 1000)
            kvlog(logger, logging.INFO, api='nest', action='token_refresh', result='ok', duration_ms=duration_ms)
        except Exception as e:
            duration_ms = int((time.time() - api_start) * 1000)
            kvlog(logger, logging.ERROR, api='nest', action='token_refresh',
                  error_type=type(e).__name__, error_msg=str(e), duration_ms=duration_ms)
            raise

    def _get(self, endpoint):
        """GET request to Nest API"""
        self._ensure_token()

        api_start = time.time()
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            resp = requests.get(url, headers={
                "Authorization": f"Bearer {self.access_token}"
            })

            resp.raise_for_status()
            result = resp.json()
            duration_ms = int((time.time() - api_start) * 1000)
            # Shorten endpoint for logging (remove long device ID)
            short_endpoint = 'device_status' if '/devices/' in endpoint else endpoint
            kvlog(logger, logging.DEBUG, api='nest', action='get', endpoint=short_endpoint, result='ok', duration_ms=duration_ms)
            return result
        except Exception as e:
            duration_ms = int((time.time() - api_start) * 1000)
            short_endpoint = 'device_status' if '/devices/' in endpoint else endpoint
            kvlog(logger, logging.ERROR, api='nest', action='get', endpoint=short_endpoint,
                  error_type=type(e).__name__, error_msg=str(e), duration_ms=duration_ms)
            raise

    def _post(self, endpoint, data):
        """POST request to Nest API"""
        self._ensure_token()

        api_start = time.time()
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            resp = requests.post(url,
                headers={"Authorization": f"Bearer {self.access_token}"},
                json=data
            )

            resp.raise_for_status()
            result = resp.json()
            duration_ms = int((time.time() - api_start) * 1000)
            # Shorten endpoint for logging (extract command name)
            if ':executeCommand' in endpoint:
                command = data.get('command', 'unknown').split('.')[-1]
                short_endpoint = f"cmd:{command}"
            else:
                short_endpoint = endpoint
            kvlog(logger, logging.DEBUG, api='nest', action='post', endpoint=short_endpoint, result='ok', duration_ms=duration_ms)
            return result
        except Exception as e:
            duration_ms = int((time.time() - api_start) * 1000)
            if ':executeCommand' in endpoint:
                command = data.get('command', 'unknown').split('.')[-1]
                short_endpoint = f"cmd:{command}"
            else:
                short_endpoint = endpoint
            kvlog(logger, logging.ERROR, api='nest', action='post', endpoint=short_endpoint,
                  error_type=type(e).__name__, error_msg=str(e), duration_ms=duration_ms)
            raise

    def get_status(self):
        """
        Get current thermostat status

        Returns:
            dict: {
                'current_temp_f': float,
                'current_humidity': int (percent),
                'mode': str ('HEAT', 'COOL', 'HEATCOOL', 'OFF'),
                'heat_setpoint_f': float (if in HEAT mode),
                'cool_setpoint_f': float (if in COOL mode),
                'hvac_status': str ('HEATING', 'COOLING', 'OFF'),
                'eco_mode': str ('MANUAL_ECO', 'OFF') - ECO/away mode status,
                'eco_heat_f': float (ECO heating threshold if in ECO mode),
                'eco_cool_f': float (ECO cooling threshold if in ECO mode)
            }
        """
        data = self._get(self.device_id)

        traits = data.get('traits', {})

        # Current temperature (Celsius)
        temp_c = traits.get('sdm.devices.traits.Temperature', {}).get('ambientTemperatureCelsius')
        temp_f = self._c_to_f(temp_c) if temp_c else None

        # Humidity
        humidity = traits.get('sdm.devices.traits.Humidity', {}).get('ambientHumidityPercent')

        # Mode
        mode = traits.get('sdm.devices.traits.ThermostatMode', {}).get('mode')

        # Setpoints
        setpoints = traits.get('sdm.devices.traits.ThermostatTemperatureSetpoint', {})
        heat_c = setpoints.get('heatCelsius')
        cool_c = setpoints.get('coolCelsius')

        heat_f = self._c_to_f(heat_c) if heat_c else None
        cool_f = self._c_to_f(cool_c) if cool_c else None

        # HVAC status
        hvac = traits.get('sdm.devices.traits.ThermostatHvac', {}).get('status', 'OFF')

        # ECO mode status
        eco_trait = traits.get('sdm.devices.traits.ThermostatEco', {})
        eco_mode = eco_trait.get('mode', 'OFF')  # 'MANUAL_ECO' or 'OFF'
        eco_heat_c = eco_trait.get('heatCelsius')
        eco_cool_c = eco_trait.get('coolCelsius')

        eco_heat_f = self._c_to_f(eco_heat_c) if eco_heat_c else None
        eco_cool_f = self._c_to_f(eco_cool_c) if eco_cool_c else None

        # Validate critical fields before returning
        if temp_f is None:
            raise ValueError(
                "Nest API returned no temperature data - "
                "sensor may be offline or device initializing"
            )
        if mode is None:
            raise ValueError(
                "Nest API returned no mode data - "
                "device may be initializing or API error"
            )

        result = {
            'current_temp_f': temp_f,
            'current_humidity': humidity,
            'mode': mode,
            'heat_setpoint_f': heat_f,
            'cool_setpoint_f': cool_f,
            'hvac_status': hvac,
            'eco_mode': eco_mode,
            'eco_heat_f': eco_heat_f,
            'eco_cool_f': eco_cool_f
        }

        # Log status (include ECO if active)
        status_msg = f"Nest status: {temp_f}°F, mode={mode}"
        if eco_mode == 'MANUAL_ECO':
            status_msg += f", ECO({eco_heat_f}-{eco_cool_f}°F)"
        else:
            status_msg += f", setpoint={heat_f or cool_f}°F"
        status_msg += f", HVAC={hvac}"
        logger.info(status_msg)

        return result

    def set_temperature(self, temp_f, mode=None):
        """
        Set target temperature

        Args:
            temp_f: Target temperature in Fahrenheit
            mode: 'HEAT' or 'COOL' (optional, uses current mode if not specified)

        Example:
            >>> nest.set_temperature(72, mode='HEAT')
        """
        temp_c = self._f_to_c(temp_f)

        # If mode not specified, get current mode
        if mode is None:
            if self.dry_run:
                mode = 'HEAT'  # Default for dry-run
            else:
                status = self.get_status()
                mode = status['mode']

                # If currently OFF, default to HEAT
                if mode == 'OFF':
                    mode = 'HEAT'
                    self.set_mode(mode)

        # Set temperature based on mode
        if mode == 'HEAT':
            command = 'sdm.devices.commands.ThermostatTemperatureSetpoint.SetHeat'
            params = {'heatCelsius': temp_c}
        elif mode == 'COOL':
            command = 'sdm.devices.commands.ThermostatTemperatureSetpoint.SetCool'
            params = {'coolCelsius': temp_c}
        elif mode == 'HEATCOOL':
            # For heat-cool mode, set both (use temp_f as cool, temp_f-2 as heat)
            command = 'sdm.devices.commands.ThermostatTemperatureSetpoint.SetRange'
            params = {
                'heatCelsius': self._f_to_c(temp_f - 2),
                'coolCelsius': temp_c
            }
        else:
            raise ValueError(f"Cannot set temperature in mode: {mode}")

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would set Nest temperature to {temp_f}°F ({mode} mode)")
            logger.info(f"[DRY-RUN] Command: {command}, Params: {params}")
            return

        self._post(f"{self.device_id}:executeCommand", {
            'command': command,
            'params': params
        })

        logger.info(f"Set temperature to {temp_f}°F ({mode} mode)")

    def set_mode(self, mode):
        """
        Set thermostat mode

        Args:
            mode: 'HEAT', 'COOL', 'HEATCOOL', or 'OFF'

        Example:
            >>> nest.set_mode('HEAT')
            >>> nest.set_mode('OFF')
        """
        valid_modes = ['HEAT', 'COOL', 'HEATCOOL', 'OFF']
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {valid_modes}")

        self._post(f"{self.device_id}:executeCommand", {
            'command': 'sdm.devices.commands.ThermostatMode.SetMode',
            'params': {'mode': mode}
        })

        logger.info(f"Set mode to {mode}")

    def set_eco_mode(self, enabled=True):
        """
        Enable or disable Eco mode (away mode)

        Args:
            enabled: True to enable Eco mode, False to disable

        Example:
            >>> nest.set_eco_mode(True)  # Away mode
            >>> nest.set_eco_mode(False)  # Normal mode
        """
        mode = 'MANUAL_ECO' if enabled else 'OFF'

        self._post(f"{self.device_id}:executeCommand", {
            'command': 'sdm.devices.commands.ThermostatEco.SetMode',
            'params': {'mode': mode}
        })

        logger.info(f"Eco mode {'enabled' if enabled else 'disabled'}")

    def set_fan(self, duration_seconds=900):
        """
        Turn on fan for specified duration

        Args:
            duration_seconds: How long to run fan (default 15 min)

        Example:
            >>> nest.set_fan(duration_seconds=1800)  # 30 minutes
        """
        self._post(f"{self.device_id}:executeCommand", {
            'command': 'sdm.devices.commands.Fan.SetTimer',
            'params': {
                'timerMode': 'ON',
                'duration': f"{duration_seconds}s"
            }
        })

        logger.info(f"Fan set to run for {duration_seconds} seconds")

    def set_comfort_mode(self, temp_f=None):
        """
        Set to comfort mode (active heating/cooling)

        Intent-based, idempotent method that:
        1. Gets target temp from config if not specified
        2. Checks current state before making changes
        3. Uses smart HVAC mode selection (HEAT/COOL/HEATCOOL based on weather)
        4. Exits ECO mode if currently in away mode
        5. Only changes state if needed (idempotent)

        Args:
            temp_f: Target temperature (uses config 'temperatures.comfort' if not specified)

        Example:
            >>> nest.set_comfort_mode()  # Use config temp (70°F)
            >>> nest.set_comfort_mode(72)  # Override to 72°F
        """
        from lib.config import get
        from lib.hvac_logic import select_hvac_mode

        # Get target temp from config if not specified
        if temp_f is None:
            temp_f = get('temperatures.comfort', 70)

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would set comfort mode: {temp_f}°F")
            return

        # Get current status
        status = self.get_status()
        current_temp = status['current_temp_f']
        current_mode = status['mode']
        eco_mode = status['eco_mode']

        # Check if already at target comfort state
        is_at_target = False
        if eco_mode == 'OFF':  # Not in ECO mode
            current_setpoint = status.get('heat_setpoint_f') or status.get('cool_setpoint_f')
            if current_setpoint and abs(current_setpoint - temp_f) < 0.5:
                is_at_target = True

        if is_at_target:
            kvlog(logger, logging.NOTICE, device='nest', action='set_comfort',
                  target_temp=temp_f, result='already_at_target')
            return

        # Determine smart HVAC mode (HEAT/COOL/HEATCOOL)
        hvac_mode = select_hvac_mode(temp_f, indoor_temp_f=current_temp)

        # Exit ECO mode if needed
        if eco_mode == 'MANUAL_ECO':
            kvlog(logger, logging.NOTICE, device='nest', action='exit_eco',
                  reason='entering_comfort_mode')
            self.set_eco_mode(False)

        # Set mode if different
        if current_mode != hvac_mode:
            kvlog(logger, logging.NOTICE, device='nest', action='set_mode',
                  from_mode=current_mode, to_mode=hvac_mode, reason='comfort_mode')
            self.set_mode(hvac_mode)

        # Set temperature
        kvlog(logger, logging.NOTICE, device='nest', action='set_temp',
              target_temp=temp_f, hvac_mode=hvac_mode, reason='comfort_mode')
        self.set_temperature(temp_f, mode=hvac_mode)

        kvlog(logger, logging.NOTICE, device='nest', action='set_comfort',
              target_temp=temp_f, hvac_mode=hvac_mode, result='ok')

    def set_away_mode(self):
        """
        Set to away mode (ECO mode with energy-saving bounds)

        Intent-based, idempotent method that:
        1. Gets ECO bounds from config (eco_low, eco_high)
        2. Checks if already in ECO mode (idempotent)
        3. Enables ECO mode only if needed
        4. Logs clearly

        ECO mode means:
        - Heat if temp falls below eco_low (62°F by default)
        - Cool if temp rises above eco_high (80°F by default)
        - Between bounds: No HVAC activity (energy saving)

        Example:
            >>> nest.set_away_mode()  # Use config ECO bounds (62-80°F)
        """
        from lib.config import get

        # Get ECO bounds from config
        eco_low_f = get('temperatures.eco_low', 62)
        eco_high_f = get('temperatures.eco_high', 80)

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would set away mode: ECO({eco_low_f}-{eco_high_f}°F)")
            return

        # Get current status
        status = self.get_status()
        eco_mode = status['eco_mode']
        current_eco_heat = status.get('eco_heat_f')
        current_eco_cool = status.get('eco_cool_f')

        # Check if already in ECO mode with correct bounds
        if eco_mode == 'MANUAL_ECO':
            if (current_eco_heat and abs(current_eco_heat - eco_low_f) < 0.5 and
                current_eco_cool and abs(current_eco_cool - eco_high_f) < 0.5):
                kvlog(logger, logging.NOTICE, device='nest', action='set_away',
                      eco_bounds=f"{eco_low_f}-{eco_high_f}", result='already_in_eco')
                return

        # Enable ECO mode with bounds
        kvlog(logger, logging.NOTICE, device='nest', action='set_away',
              eco_low=eco_low_f, eco_high=eco_high_f, reason='entering_away_mode')

        # Note: Nest API ECO mode automatically sets the bounds
        # The bounds are configured in the Nest app or via the SDM API
        # For now, we just enable ECO mode
        self.set_eco_mode(True)

        kvlog(logger, logging.NOTICE, device='nest', action='set_away',
              eco_bounds=f"{eco_low_f}-{eco_high_f}", result='ok')

    def set_sleep_mode(self, temp_f=None):
        """
        Set to sleep mode

        For Nest, sleep mode = away mode (ECO bounds)
        This allows Sensibo to independently control bedroom temp while
        Nest uses energy-saving ECO mode for the rest of the house.

        Args:
            temp_f: Ignored for Nest (uses ECO bounds), included for API consistency

        Example:
            >>> nest.set_sleep_mode()  # Enable ECO mode
        """
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would set sleep mode (ECO mode)")
            return

        kvlog(logger, logging.INFO, device='nest', action='set_sleep',
              reason='sleep_mode_uses_eco')
        self.set_away_mode()

    # Temperature conversion helpers
    @staticmethod
    def _f_to_c(fahrenheit):
        """Convert Fahrenheit to Celsius (rounded to 1 decimal)"""
        return round((fahrenheit - 32) * 5 / 9, 1)

    @staticmethod
    def _c_to_f(celsius):
        """Convert Celsius to Fahrenheit (rounded to 1 decimal)"""
        return round(celsius * 9 / 5 + 32, 1)


# Singleton instance for convenience
_nest = None

def get_nest():
    """Get or create Nest API instance"""
    global _nest
    if _nest is None:
        _nest = NestAPI()
    return _nest


# Convenience functions
def get_status():
    """Get current thermostat status"""
    return get_nest().get_status()


def set_temperature(temp_f, mode=None):
    """Set target temperature"""
    return get_nest().set_temperature(temp_f, mode)


def set_mode(mode):
    """Set thermostat mode"""
    return get_nest().set_mode(mode)


def set_away():
    """
    Set to away mode (ECO mode with energy-saving bounds)

    Uses ECO bounds from config (eco_low, eco_high).
    Idempotent - safe to call multiple times.

    Example:
        >>> set_away()  # Enable ECO mode with config bounds
    """
    return get_nest().set_away_mode()


def set_comfort(temp_f=None):
    """
    Set to comfort mode (active heating/cooling)

    Args:
        temp_f: Target temperature (uses config 'temperatures.comfort' if not specified)

    Idempotent - safe to call multiple times.
    Uses smart HVAC mode selection based on weather.

    Example:
        >>> set_comfort()  # Use config temp (70°F)
        >>> set_comfort(72)  # Override to 72°F
    """
    return get_nest().set_comfort_mode(temp_f)


def set_sleep(temp_f=None):
    """
    Set to sleep mode (ECO mode for Nest)

    For Nest, sleep mode uses ECO bounds to save energy while
    Sensibo independently controls bedroom temperature.

    Example:
        >>> set_sleep()  # Enable ECO mode
    """
    return get_nest().set_sleep_mode(temp_f)


__all__ = [
    'NestAPI', 'get_nest', 'get_status', 'set_temperature',
    'set_mode', 'set_away', 'set_comfort', 'set_sleep'
]
