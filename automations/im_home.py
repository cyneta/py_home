#!/usr/bin/env python
"""
I'm Home Automation (Stage 2)

Physical arrival routine when WiFi connects (~5 seconds after entering home).

Stage 1 (Pre-Arrival) runs when crossing geofence boundary - see pre_arrival.py

Actions:
1. Turn on indoor lights (living room + bedroom if evening)
2. Send notification only on errors (no routine notifications)

Stage 1 Fallback:
- If pre-arrival didn't run (WiFi-only arrival), run Stage 1 first

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

# Check for dry-run mode (priority: flag > env var > config > default)
from lib.config import get
DRY_RUN = (
    '--dry-run' in sys.argv or
    os.environ.get('DRY_RUN', '').lower() == 'true' or
    get('automations.dry_run', False)
)


def get_presence_state():
    """Check current presence state from state file"""
    from pathlib import Path
    state_file = Path(__file__).parent.parent / '.presence_state'

    try:
        if state_file.exists():
            return state_file.read_text().strip()
        return 'unknown'
    except Exception:
        return 'unknown'


def run():
    """Execute I'm home automation (Stage 2)"""
    start_time = time.time()
    kvlog(logger, logging.NOTICE, automation='im_home', event='start', stage=2, dry_run=DRY_RUN)

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

    # Check if pre-arrival already ran (Stage 1)
    presence_state = get_presence_state()
    if presence_state != 'home':
        # WiFi-only arrival (no geofence trigger)
        # Run Stage 1 first
        kvlog(logger, logging.INFO, automation='im_home', event='fallback',
              reason='pre_arrival_not_run', state=presence_state)

        try:
            from automations.pre_arrival import run as pre_arrival_run
            pre_arrival_result = pre_arrival_run()

            if pre_arrival_result.get('actions'):
                actions.extend(pre_arrival_result['actions'])
            if pre_arrival_result.get('errors'):
                errors.extend(pre_arrival_result['errors'])

            kvlog(logger, logging.INFO, automation='im_home', event='fallback_complete')
        except Exception as e:
            kvlog(logger, logging.ERROR, automation='im_home', event='fallback_failed',
                  error_type=type(e).__name__, error_msg=str(e))
            errors.append(f"Pre-arrival fallback: {e}")

    # 1. Turn on indoor lights
    try:
        from components.tapo import TapoAPI

        tapo = TapoAPI(dry_run=DRY_RUN)
        hour = datetime.now().hour

        api_start = time.time()

        # Always turn on living room (welcome light)
        tapo.turn_on("LivingRoom Lamp")
        lamps_on = ["Living room"]

        # Turn on bedroom lamps only if evening (after 6pm)
        if hour >= 18:
            tapo.turn_on("Master Left Lamp")
            tapo.turn_on("Master Right Lamp")
            lamps_on.extend(["Bedroom left", "Bedroom right"])

        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, automation='im_home', device='tapo',
              action='indoor_lights', count=len(lamps_on), result='ok', duration_ms=duration_ms)

        actions.append(f"Indoor lights on ({', '.join(lamps_on)})")
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='im_home', device='tapo',
              action='indoor_lights', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Lights: {e}")
        actions.append(f"Lights failed: {str(e)[:30]}")

    # 2. Send notification only on errors
    # Design principle: Notifications are for emergencies/errors only (see design/principles/notifications.md)
    if errors and not DRY_RUN:
        try:
            from lib.notifications import send_automation_summary
            send_automation_summary("⚠️ Arrival Error", actions, priority=1)
            kvlog(logger, logging.INFO, automation='im_home', action='notification', result='sent', reason='errors')
        except Exception as e:
            # Don't add to errors - notification failure isn't critical
            kvlog(logger, logging.ERROR, automation='im_home', action='notification',
                  error_type=type(e).__name__, error_msg=str(e))

    # Complete
    total_duration_ms = int((time.time() - start_time) * 1000)
    kvlog(logger, logging.NOTICE, automation='im_home', event='complete', stage=2,
          duration_ms=total_duration_ms, errors=len(errors), actions_count=len(actions))

    return {
        'action': 'im_home',
        'stage': 2,
        'status': 'success' if not errors else 'partial',
        'actions': actions,
        'errors': errors,
        'duration_ms': total_duration_ms
    }


if __name__ == '__main__':
    # Set up logging to unified automations.log
    from lib.logging_config import setup_logging
    log_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'logs', 'automations.log')
    setup_logging(log_level='INFO', log_file=log_file)

    run()
