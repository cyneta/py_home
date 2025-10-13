#!/usr/bin/env python
"""
Leaving Home Automation

Migrated from: siri_n8n/n8n/workflows/leaving-home.json

Actions:
1. Set Nest thermostat to ECO mode (energy-saving)
2. Turn off all Tapo outlets (coffee maker, lamps, heater)
3. (Future: Start Roborock vacuum)
4. Send notification

Usage:
    python automations/leaving_home.py
    python automations/leaving_home.py --dry-run  # Safe testing mode
"""

import os
import sys
import logging
import time
from datetime import datetime
from lib.logging_config import kvlog

logger = logging.getLogger(__name__)

# Check for dry-run mode
DRY_RUN = os.environ.get('DRY_RUN', 'false').lower() == 'true' or '--dry-run' in sys.argv


def run():
    """Execute leaving home automation"""
    start_time = time.time()
    kvlog(logger, logging.NOTICE, automation='leaving_home', event='start', dry_run=DRY_RUN)

    # Check if automations are enabled
    from lib.automation_control import are_automations_enabled
    if not are_automations_enabled():
        kvlog(logger, logging.INFO, automation='leaving_home', event='skipped', reason='automations_disabled')
        return {
            'action': 'leaving_home',
            'status': 'skipped',
            'reason': 'Automations disabled via master switch'
        }

    errors = []
    actions = []

    # 1. Set Nest to ECO mode (energy-saving away mode)
    try:
        from components.nest import NestAPI

        nest = NestAPI(dry_run=DRY_RUN)

        api_start = time.time()
        nest.set_eco_mode(True)
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, automation='leaving_home', device='nest',
              action='set_eco_mode', enabled=True, result='ok', duration_ms=duration_ms)
        actions.append("Nest ECO mode enabled")
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='leaving_home', device='nest',
              action='set_eco_mode', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Nest: {e}")
        actions.append(f"Nest ECO failed: {str(e)[:30]}")

    # 2. Turn off all Tapo outlets
    try:
        from components.tapo import TapoAPI

        tapo = TapoAPI(dry_run=DRY_RUN)

        api_start = time.time()
        tapo.turn_off_all()
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, automation='leaving_home', device='tapo',
              action='turn_off_all', result='ok', duration_ms=duration_ms)
        actions.append("All outlets turned off")
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='leaving_home', device='tapo',
              action='turn_off_all', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Tapo: {e}")
        actions.append(f"Outlets failed: {str(e)[:30]}")

    # 3. Send notification with action summary
    try:
        if not DRY_RUN:
            from lib.notifications import send_automation_summary

            title = "🚗 Left Home"
            priority = 1 if errors else 0  # High priority if errors

            send_automation_summary(title, actions, priority=priority)

            kvlog(logger, logging.INFO, automation='leaving_home', action='notification', result='sent')
        else:
            kvlog(logger, logging.DEBUG, automation='leaving_home', action='notification', result='skipped_dry_run')
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='leaving_home', action='notification',
              error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Notification: {e}")

    # Complete
    total_duration_ms = int((time.time() - start_time) * 1000)
    kvlog(logger, logging.NOTICE, automation='leaving_home', event='complete',
          duration_ms=total_duration_ms, errors=len(errors))

    return {
        'action': 'leaving_home',
        'status': 'success' if not errors else 'partial',
        'errors': errors,
        'duration_ms': total_duration_ms
    }


if __name__ == '__main__':
    run()
