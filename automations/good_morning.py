#!/usr/bin/env python
"""
Good Morning Automation

Morning routine to start the day.

Actions:
1. Set Nest thermostat to comfort temp (70-72°F)
2. Get weather forecast
3. Send morning summary notification (weather + optional traffic)
4. (Future: Turn on coffee maker outlet)

Usage:
    python automations/good_morning.py
    python automations/good_morning.py --dry-run  # Test without executing
    DRY_RUN=true python automations/good_morning.py  # Test without executing
"""

import logging
import os
import sys
import time
from datetime import datetime
from lib.logging_config import kvlog

logger = logging.getLogger(__name__)

# Check for dry-run mode
DRY_RUN = os.environ.get('DRY_RUN', 'false').lower() == 'true' or '--dry-run' in sys.argv


def run():
    """Execute good morning automation"""
    start_time = time.time()
    kvlog(logger, logging.NOTICE, automation='good_morning', event='start', dry_run=DRY_RUN)

    # Check if automations are enabled
    from lib.automation_control import are_automations_enabled
    if not are_automations_enabled():
        kvlog(logger, logging.INFO, automation='good_morning', event='skipped', reason='automations_disabled')
        return {
            'action': 'good_morning',
            'status': 'skipped',
            'reason': 'Automations disabled via master switch'
        }

    actions = []
    errors = []

    # 1a. Disable night mode flag (for temp_coordination)
    try:
        from lib.night_mode import set_night_mode

        set_night_mode(False)
        kvlog(logger, logging.NOTICE, automation='good_morning', action='night_mode', enabled=False)

        # Don't add to actions (silent operation)
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='good_morning', action='night_mode',
              error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Night mode: {e}")

    # 1b. Disable Nest ECO mode and set comfort temperature
    try:
        from components.nest import NestAPI
        from lib.config import config

        comfort_temp = config['nest']['comfort_temp']
        nest = NestAPI(dry_run=DRY_RUN)

        api_start = time.time()
        nest.set_eco_mode(False)
        nest.set_temperature(comfort_temp)
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, automation='good_morning', device='nest',
              action='set_comfort', target=comfort_temp, result='ok', duration_ms=duration_ms)

        actions.append(f"Nest set to {comfort_temp}°F")
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='good_morning', device='nest',
              action='set_comfort', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Nest: {e}")
        actions.append(f"Nest failed: {str(e)[:30]}")

    # 2. Get weather forecast
    weather_summary = None
    try:
        from services import get_weather_summary

        api_start = time.time()
        weather_summary = get_weather_summary()
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, automation='good_morning', service='weather',
              action='get_summary', result='ok', duration_ms=duration_ms)

        # Add weather as first action (most important for morning)
        actions.insert(0, weather_summary)
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='good_morning', service='weather',
              action='get_summary', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Weather: {e}")
        actions.insert(0, "Weather unavailable")

    # 3. Future: Turn on coffee maker
    # Uncomment when coffee maker outlet is identified
    # try:
    #     from components.tapo import turn_on
    #     api_start = time.time()
    #     turn_on("Heater")  # Replace with actual coffee maker name
    #     duration_ms = int((time.time() - api_start) * 1000)
    #     kvlog(logger, logging.NOTICE, automation='good_morning', device='coffee_maker',
    #           action='turn_on', result='ok', duration_ms=duration_ms)
    #     actions.append("Coffee maker started")
    # except Exception as e:
    #     kvlog(logger, logging.ERROR, automation='good_morning', device='coffee_maker',
    #           action='turn_on', error_type=type(e).__name__, error_msg=str(e))
    #     errors.append(f"Coffee: {e}")
    #     actions.append(f"Coffee maker failed: {str(e)[:30]}")

    # 4. Send morning summary notification
    try:
        if not DRY_RUN:
            from lib.notifications import send_automation_summary

            title = "☀️ Good Morning"
            priority = 1 if errors else 0  # High priority if errors

            send_automation_summary(title, actions, priority=priority)

            kvlog(logger, logging.INFO, automation='good_morning', action='notification', result='sent')
        else:
            kvlog(logger, logging.DEBUG, automation='good_morning', action='notification', result='skipped_dry_run')
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='good_morning', action='notification',
              error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Notification: {e}")

    # Complete
    total_duration_ms = int((time.time() - start_time) * 1000)
    kvlog(logger, logging.NOTICE, automation='good_morning', event='complete',
          duration_ms=total_duration_ms, errors=len(errors))

    return {
        'action': 'good_morning',
        'status': 'success' if not errors else 'partial',
        'errors': errors,
        'duration_ms': total_duration_ms
    }


if __name__ == '__main__':
    run()
