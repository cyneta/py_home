#!/usr/bin/env python
"""
Goodnight Automation

Migrated from: siri_n8n/n8n/workflows/goodnight.json

Actions:
1. Set Nest thermostat to sleep temp (68°F)
2. Turn off Sensibo AC
3. Turn off all Tapo outlets (coffee maker, lamps)
4. (Future: Start Roborock vacuum)
5. Send notification

Usage:
    python automations/goodnight.py
    python automations/goodnight.py --dry-run  # Test without executing
    DRY_RUN=true python automations/goodnight.py  # Test without executing
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
    """Execute goodnight automation"""
    start_time = time.time()
    kvlog(logger, logging.NOTICE, automation='goodnight', event='start', dry_run=DRY_RUN)

    errors = []

    # 1. Set Nest to sleep temperature
    try:
        from components.nest import NestAPI
        from lib.config import config

        sleep_temp = config['nest']['sleep_temp']
        nest = NestAPI(dry_run=DRY_RUN)

        api_start = time.time()
        nest.set_temperature(sleep_temp)
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, automation='goodnight', device='nest',
              action='set_temp', target=sleep_temp, result='ok', duration_ms=duration_ms)
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='goodnight', device='nest',
              action='set_temp', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Nest: {e}")

    # 2. Turn off Sensibo AC
    try:
        from components.sensibo import SensiboAPI

        sensibo = SensiboAPI(dry_run=DRY_RUN)

        api_start = time.time()
        sensibo.turn_off()
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, automation='goodnight', device='sensibo',
              action='turn_off', result='ok', duration_ms=duration_ms)
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='goodnight', device='sensibo',
              action='turn_off', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Sensibo: {e}")

    # 3. Turn off all Tapo outlets
    try:
        from components.tapo import TapoAPI

        tapo = TapoAPI(dry_run=DRY_RUN)

        api_start = time.time()
        tapo.turn_off_all()
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, automation='goodnight', device='tapo',
              action='turn_off_all', result='ok', duration_ms=duration_ms)
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='goodnight', device='tapo',
              action='turn_off_all', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Tapo: {e}")

    # 4. Future: Start vacuum
    # Will be implemented when Roborock component is ready

    # 5. Send notification
    try:
        if not DRY_RUN:
            from lib.notifications import send

            if errors:
                message = f"Sleep mode activated (with {len(errors)} errors)"
                send(message, title="Goodnight", priority=1)
            else:
                send("Goodnight - Sleep mode activated", title="Goodnight")

            kvlog(logger, logging.INFO, automation='goodnight', action='notification', result='sent')
        else:
            kvlog(logger, logging.DEBUG, automation='goodnight', action='notification', result='skipped_dry_run')
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='goodnight', action='notification',
              error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Notification: {e}")

    # Complete
    total_duration_ms = int((time.time() - start_time) * 1000)
    kvlog(logger, logging.NOTICE, automation='goodnight', event='complete',
          duration_ms=total_duration_ms, errors=len(errors))

    return {
        'action': 'goodnight',
        'status': 'success' if not errors else 'partial',
        'errors': errors,
        'duration_ms': total_duration_ms
    }


if __name__ == '__main__':
    run()
