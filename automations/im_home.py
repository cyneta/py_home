#!/usr/bin/env python
"""
I'm Home Automation

Welcome home routine when arriving.

Actions:
1. Disable Nest ECO mode and set comfort temp (70°F)
2. Turn on all lamps (welcome lights)
3. Send welcome notification

Usage:
    python automations/im_home.py
    python automations/im_home.py --dry-run  # Test without executing
    DRY_RUN=true python automations/im_home.py  # Test without executing
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
    """Execute I'm home automation"""
    start_time = time.time()
    kvlog(logger, logging.NOTICE, automation='im_home', event='start', dry_run=DRY_RUN)

    # Check if automations are enabled
    from lib.automation_control import are_automations_enabled
    if not are_automations_enabled():
        kvlog(logger, logging.INFO, automation='im_home', event='skipped', reason='automations_disabled')
        return {
            'action': 'im_home',
            'status': 'skipped',
            'reason': 'Automations disabled via master switch'
        }

    actions = []
    errors = []

    # 1. Disable Nest ECO mode and set comfort temperature
    try:
        from components.nest import NestAPI
        from lib.config import config

        comfort_temp = config['nest']['comfort_temp']
        nest = NestAPI(dry_run=DRY_RUN)

        api_start = time.time()
        nest.set_eco_mode(False)
        nest.set_temperature(comfort_temp)
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, automation='im_home', device='nest',
              action='set_comfort', target=comfort_temp, result='ok', duration_ms=duration_ms)

        actions.append(f"Nest set to {comfort_temp}°F")
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='im_home', device='nest',
              action='set_comfort', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Nest: {e}")
        actions.append(f"Nest failed: {str(e)[:30]}")

    # 2. Turn on all lamps
    try:
        from components.tapo import TapoAPI

        tapo = TapoAPI(dry_run=DRY_RUN)

        api_start = time.time()
        # Turn on all outlets except heater
        lamps = ["Livingroom Lamp", "Bedroom Left Lamp", "Bedroom Right Lamp"]
        for lamp in lamps:
            tapo.turn_on(lamp)
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, automation='im_home', device='tapo',
              action='turn_on_lamps', count=len(lamps), result='ok', duration_ms=duration_ms)

        actions.append("Welcome lights on")
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='im_home', device='tapo',
              action='turn_on_lamps', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Lights: {e}")
        actions.append(f"Lights failed: {str(e)[:30]}")

    # 3. Send notification with action summary
    try:
        if not DRY_RUN:
            from lib.notifications import send_automation_summary

            title = "🏡 Arrived Home"
            priority = 1 if errors else 0  # High priority if errors

            send_automation_summary(title, actions, priority=priority)

            kvlog(logger, logging.INFO, automation='im_home', action='notification', result='sent')
        else:
            kvlog(logger, logging.DEBUG, automation='im_home', action='notification', result='skipped_dry_run')
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='im_home', action='notification',
              error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Notification: {e}")

    # Complete
    total_duration_ms = int((time.time() - start_time) * 1000)
    kvlog(logger, logging.NOTICE, automation='im_home', event='complete',
          duration_ms=total_duration_ms, errors=len(errors))

    return {
        'action': 'im_home',
        'status': 'success' if not errors else 'partial',
        'errors': errors,
        'duration_ms': total_duration_ms
    }


if __name__ == '__main__':
    run()
