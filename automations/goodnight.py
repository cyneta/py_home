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

    # Check if automations are enabled
    from lib.automation_control import are_automations_enabled
    if not are_automations_enabled():
        kvlog(logger, logging.INFO, automation='goodnight', event='skipped', reason='automations_disabled')
        return {
            'action': 'goodnight',
            'status': 'skipped',
            'reason': 'Automations disabled via master switch'
        }

    actions = []
    errors = []

    # 1. Set Nest to ECO mode (night mode - minimal whole-house conditioning)
    try:
        from components.nest import NestAPI

        nest = NestAPI(dry_run=DRY_RUN)

        api_start = time.time()
        nest.set_eco_mode(True)
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, automation='goodnight', device='nest',
              action='set_eco_mode', enabled=True, result='ok', duration_ms=duration_ms)

        actions.append("Nest ECO mode enabled")
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='goodnight', device='nest',
              action='set_eco_mode', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Nest: {e}")
        actions.append(f"Nest ECO failed: {str(e)[:30]}")

    # 1b. Enable night mode flag (for temp_coordination)
    try:
        from lib.night_mode import set_night_mode

        set_night_mode(True)
        kvlog(logger, logging.NOTICE, automation='goodnight', action='night_mode', enabled=True)

        actions.append("Night mode: Master Suite only (66°F)")
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='goodnight', action='night_mode',
              error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Night mode: {e}")
        actions.append(f"Night mode failed: {str(e)[:30]}")

    # 2. Sensibo (mini-split) will be handled by temp_coordination
    # Night mode sets Sensibo to 66°F automatically

    # 3. Turn off all Tapo outlets
    try:
        from components.tapo import TapoAPI

        tapo = TapoAPI(dry_run=DRY_RUN)

        api_start = time.time()
        tapo.turn_off_all()
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, automation='goodnight', device='tapo',
              action='turn_off_all', result='ok', duration_ms=duration_ms)

        actions.append("All outlets turned off")
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='goodnight', device='tapo',
              action='turn_off_all', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Tapo: {e}")
        actions.append(f"Outlets failed: {str(e)[:30]}")

    # 4. Future: Start vacuum
    # Will be implemented when Roborock component is ready

    # 5. Send notification with action summary
    try:
        if not DRY_RUN:
            from lib.notifications import send_automation_summary

            title = "🌙 Goodnight"
            priority = 1 if errors else 0  # High priority if errors

            send_automation_summary(title, actions, priority=priority)

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
