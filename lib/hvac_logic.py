"""
HVAC logic helpers for smart mode selection and temperature control.

Shared logic used by both Nest and Sensibo components.
"""

import logging
from lib.config import get

logger = logging.getLogger(__name__)


def select_hvac_mode(target_temp_f, indoor_temp_f=None, outdoor_temp_f=None):
    """
    Smart HEAT/COOL/HEATCOOL selection based on temperatures.

    Logic:
    1. Primary: Check outdoor temp against thresholds
       - If outdoor < heat_below (65°F) → HEAT (heating season)
       - If outdoor > cool_above (75°F) → COOL (cooling season)
       - Between 65-75°F → Check indoor temp

    2. Override: If indoor is far from target, force mode
       - Indoor < target-2°F → HEAT (house needs heating now)
       - Indoor > target+2°F → COOL (house needs cooling now)

    3. Default: HEATCOOL (let thermostat auto-decide)

    Args:
        target_temp_f: Desired temperature
        indoor_temp_f: Current indoor temperature (optional)
        outdoor_temp_f: Current outdoor temperature (optional, will fetch if needed)

    Returns:
        str: 'HEAT', 'COOL', or 'HEATCOOL'

    Examples:
        >>> select_hvac_mode(70, 68, 40)  # Cold outside
        'HEAT'
        >>> select_hvac_mode(70, 72, 85)  # Hot outside
        'COOL'
        >>> select_hvac_mode(70, 69, 68)  # Mild outside
        'HEATCOOL'
    """
    # Get thresholds from config
    heat_threshold = get('temperatures.heat_below', 65)
    cool_threshold = get('temperatures.cool_above', 75)

    # Get outdoor temp if not provided
    if outdoor_temp_f is None:
        outdoor_temp_f = get_outdoor_temp()

    # Primary decision: outdoor temp
    if outdoor_temp_f < heat_threshold:
        mode = 'HEAT'  # Definitely heating season
    elif outdoor_temp_f > cool_threshold:
        mode = 'COOL'  # Definitely cooling season
    else:
        mode = 'HEATCOOL'  # Shoulder season - auto mode

    # Override: Check indoor temp if provided
    if indoor_temp_f is not None:
        if indoor_temp_f < target_temp_f - 2:
            logger.debug(f"Indoor {indoor_temp_f}°F < target {target_temp_f}°F, forcing HEAT")
            return 'HEAT'
        elif indoor_temp_f > target_temp_f + 2:
            logger.debug(f"Indoor {indoor_temp_f}°F > target {target_temp_f}°F, forcing COOL")
            return 'COOL'

    logger.debug(f"Mode={mode} (outdoor={outdoor_temp_f}°F, indoor={indoor_temp_f}°F, target={target_temp_f}°F)")
    return mode


def get_outdoor_temp():
    """
    Get current outdoor temperature from weather API.

    Returns:
        float: Outdoor temperature in Fahrenheit
    """
    try:
        from services.openweather import get_current_weather
        weather = get_current_weather()
        temp = weather['temp']
        logger.debug(f"Outdoor temp: {temp}°F")
        return temp
    except Exception as e:
        logger.warning(f"Can't get outdoor temp, assuming 70°F: {e}")
        return 70.0  # Safe default (shoulder season)


def is_sleep_time():
    """
    Check if current time is within sleep schedule.

    Returns:
        bool: True if it's sleep time (22:30 - 05:00)
    """
    from datetime import datetime, time

    now = datetime.now().time()

    # Get schedule from config
    sleep_str = get('schedule.sleep_time', '22:30')
    wake_str = get('schedule.wake_time', '05:00')

    # Parse times
    sleep_hour, sleep_min = map(int, sleep_str.split(':'))
    wake_hour, wake_min = map(int, wake_str.split(':'))

    sleep_time = time(sleep_hour, sleep_min)
    wake_time = time(wake_hour, wake_min)

    # Handle overnight wrap (sleep_time > wake_time)
    if sleep_time > wake_time:
        is_sleep = now >= sleep_time or now < wake_time
    else:
        is_sleep = sleep_time <= now < wake_time

    logger.debug(f"Is sleep time? {is_sleep} (now={now.strftime('%H:%M')}, sleep={sleep_str}, wake={wake_str})")
    return is_sleep


__all__ = ['select_hvac_mode', 'get_outdoor_temp', 'is_sleep_time']
