#!/usr/bin/env python
"""
Arrival Pre-Heat Automation

Triggered when leaving work (20+ min away from home).
Pre-heats house based on current weather and ETA.
"""

import sys
import logging
import os
import time

# Add project root to path
sys.path.insert(0, '/c/git/cyneta/py_home')

from services.openweather import get_current_weather
from lib.config import config
from lib.notifications import send_notification
from lib.logging_config import kvlog

logger = logging.getLogger(__name__)

# Check for dry-run mode (priority: flag > env var > config > default)
from lib.config import get
DRY_RUN = (
    '--dry-run' in sys.argv or
    os.environ.get('DRY_RUN', '').lower() == 'true' or
    get('automations.dry_run', False)
)


def main():
    """
    Pre-heat/cool house before arrival

    Strategy:
    - Check current outdoor temp
    - If cold (<50°F): Set Nest to comfort temp (72°F)
    - If hot (>75°F): Turn on Sensibo AC
    - Send notification with ETA
    """
    start_time = time.time()
    kvlog(logger, logging.NOTICE, automation='arrival_preheat', event='start', dry_run=DRY_RUN)

    errors = []

    try:
        # Get ETA from command line arg (if provided)
        eta_minutes = int(sys.argv[1]) if len(sys.argv) > 1 else None

        # Get current weather
        try:
            api_start = time.time()
            weather = get_current_weather()
            temp = weather['temp']
            duration_ms = int((time.time() - api_start) * 1000)

            kvlog(logger, logging.NOTICE, automation='arrival_preheat', service='weather',
                  action='get_temp', temp=temp, eta_minutes=eta_minutes, result='ok', duration_ms=duration_ms)
        except Exception as e:
            kvlog(logger, logging.ERROR, automation='arrival_preheat', service='weather',
                  action='get_temp', error_type=type(e).__name__, error_msg=str(e))
            errors.append(f"Weather: {e}")
            raise

        # Pre-condition house for arrival (smart mode selection based on weather)
        try:
            from components.nest import NestAPI

            nest = NestAPI(dry_run=DRY_RUN)

            api_start = time.time()
            nest.set_comfort_mode()  # Automatically selects HEAT/COOL/HEATCOOL based on weather
            duration_ms = int((time.time() - api_start) * 1000)

            action_desc = f"Nest → comfort mode (70°F)"
            kvlog(logger, logging.NOTICE, automation='arrival_preheat', device='nest',
                  action='set_comfort', outdoor_temp=temp, result='ok', duration_ms=duration_ms)
        except Exception as e:
            kvlog(logger, logging.ERROR, automation='arrival_preheat', device='nest',
                  action='set_comfort', error_type=type(e).__name__, error_msg=str(e))
            errors.append(f"Nest: {e}")
            action_desc = f"Nest failed"

        try:
            from components.sensibo import SensiboAPI

            sensibo = SensiboAPI(dry_run=DRY_RUN)

            api_start = time.time()
            sensibo.set_comfort_mode()  # Automatically helps Nest with smart mode selection
            duration_ms = int((time.time() - api_start) * 1000)

            kvlog(logger, logging.NOTICE, automation='arrival_preheat', device='sensibo',
                  action='set_comfort', outdoor_temp=temp, result='ok', duration_ms=duration_ms)
        except Exception as e:
            kvlog(logger, logging.ERROR, automation='arrival_preheat', device='sensibo',
                  action='set_comfort', error_type=type(e).__name__, error_msg=str(e))
            errors.append(f"Sensibo: {e}")

        # Send notification
        try:
            if not DRY_RUN:
                if eta_minutes:
                    message = f"Pre-conditioning house. ETA: {eta_minutes} min. {action_desc}"
                else:
                    message = f"Pre-conditioning house. {action_desc}"

                send_notification(
                    title="Arriving Soon",
                    message=message,
                    priority=0
                )

                kvlog(logger, logging.INFO, automation='arrival_preheat', action='notification', result='sent')
            else:
                kvlog(logger, logging.DEBUG, automation='arrival_preheat', action='notification', result='skipped_dry_run')
        except Exception as e:
            kvlog(logger, logging.ERROR, automation='arrival_preheat', action='notification',
                  error_type=type(e).__name__, error_msg=str(e))
            errors.append(f"Notification: {e}")

    except Exception as e:
        kvlog(logger, logging.ERROR, automation='arrival_preheat', event='failed',
              error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Fatal: {e}")
        sys.exit(1)

    # Complete
    total_duration_ms = int((time.time() - start_time) * 1000)
    kvlog(logger, logging.NOTICE, automation='arrival_preheat', event='complete',
          duration_ms=total_duration_ms, errors=len(errors))


if __name__ == '__main__':
    main()
