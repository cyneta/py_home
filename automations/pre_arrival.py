#!/usr/bin/env python
"""
Pre-Arrival Automation (Stage 1)

Triggered when crossing geofence boundary (~173m, ~60 seconds before home).
Prepares house with lead-time actions that need time to take effect.

Actions:
1. Set Nest to comfort temperature (5-15 min lead time for HVAC)
2. Enable Sensibo if night mode active (10-20 min for bedroom cooling)
3. Turn on outdoor lights if dark (pathway safety)
4. Update presence state to prevent duplicate triggers

Stage 2 (Physical Arrival) happens when WiFi connects - see im_home.py

Usage:
    python automations/pre_arrival.py
    python automations/pre_arrival.py --dry-run  # Test without executing
    DRY_RUN=true python automations/pre_arrival.py  # Test without executing
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


def is_dark():
    """Check if it's dark outside (after sunset or before sunrise)"""
    hour = datetime.now().hour
    # Dark between 6pm and 6am
    return hour >= 18 or hour < 6


def is_night_mode():
    """Check if night mode is active"""
    from pathlib import Path
    night_mode_file = Path(__file__).parent.parent / '.night_mode'
    return night_mode_file.exists()


def update_presence_state():
    """Update presence state to 'home' to prevent duplicate triggers"""
    from pathlib import Path
    state_file = Path(__file__).parent.parent / '.presence_state'

    try:
        with open(state_file, 'w') as f:
            f.write('home')
        kvlog(logger, logging.DEBUG, automation='pre_arrival', action='update_state',
              state='home', result='ok')
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='pre_arrival', action='update_state',
              error_type=type(e).__name__, error_msg=str(e))


def run():
    """Execute pre-arrival automation (Stage 1)"""
    start_time = time.time()
    kvlog(logger, logging.NOTICE, automation='pre_arrival', event='start', stage=1, dry_run=DRY_RUN)

    # Check if automations are enabled
    from lib.automation_control import are_automations_enabled
    if not are_automations_enabled():
        kvlog(logger, logging.INFO, automation='pre_arrival', event='skipped', reason='automations_disabled')
        return {
            'action': 'pre_arrival',
            'status': 'skipped',
            'reason': 'Automations disabled via master switch'
        }

    actions = []
    errors = []

    # 1. Set Nest to comfort mode (immediate response for arrival)
    try:
        from components.nest import NestAPI

        nest = NestAPI(dry_run=DRY_RUN)

        api_start = time.time()
        nest.set_comfort_mode()  # Intent-based API - idempotent, config-driven
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, automation='pre_arrival', device='nest',
              action='set_comfort', result='ok', duration_ms=duration_ms)

        actions.append("Nest → comfort mode (70°F)")
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='pre_arrival', device='nest',
              action='set_comfort', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Nest: {e}")
        actions.append(f"Nest failed: {str(e)[:30]}")

    # 2. Set Sensibo based on time of day (immediate response for arrival)
    try:
        from components.sensibo import SensiboAPI
        from lib.hvac_logic import is_sleep_time

        sensibo = SensiboAPI(dry_run=DRY_RUN)

        api_start = time.time()
        if is_sleep_time():
            sensibo.set_sleep_mode()  # Active 66°F for bedroom during sleep hours
            actions.append("Bedroom → 66°F (sleep mode)")
        else:
            sensibo.set_comfort_mode()  # Active 70°F to help Nest
            actions.append("Bedroom → 70°F (comfort mode)")
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, automation='pre_arrival', device='sensibo',
              action='set_mode', result='ok', duration_ms=duration_ms)

    except Exception as e:
        kvlog(logger, logging.ERROR, automation='pre_arrival', device='sensibo',
              action='set_mode', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Sensibo: {e}")
        actions.append(f"Sensibo failed: {str(e)[:30]}")

    # 3. Turn on outdoor lights if dark
    if is_dark():
        try:
            from components.tapo import TapoAPI

            tapo = TapoAPI(dry_run=DRY_RUN)

            api_start = time.time()
            # Turn on living room lamp as pathway light
            # (Later we'll add actual outdoor lights when hardware available)
            tapo.turn_on("Livingroom Lamp")
            duration_ms = int((time.time() - api_start) * 1000)

            kvlog(logger, logging.NOTICE, automation='pre_arrival', device='tapo',
                  action='outdoor_lights', result='ok', duration_ms=duration_ms)

            actions.append("Pathway lights on")
        except Exception as e:
            kvlog(logger, logging.ERROR, automation='pre_arrival', device='tapo',
                  action='outdoor_lights', error_type=type(e).__name__, error_msg=str(e))
            errors.append(f"Outdoor lights: {e}")
            actions.append(f"Lights failed: {str(e)[:30]}")

    # 4. Update presence state
    if not DRY_RUN:
        update_presence_state()

    # Note: No notification sent - wait for Stage 2 (im_home.py)

    # Complete
    total_duration_ms = int((time.time() - start_time) * 1000)
    kvlog(logger, logging.NOTICE, automation='pre_arrival', event='complete', stage=1,
          duration_ms=total_duration_ms, errors=len(errors), actions_count=len(actions))

    return {
        'action': 'pre_arrival',
        'stage': 1,
        'status': 'success' if not errors else 'partial',
        'actions': actions,
        'errors': errors,
        'duration_ms': total_duration_ms,
        'note': 'Stage 2 (indoor lights + notification) will trigger on WiFi connect'
    }


if __name__ == '__main__':
    # Set up logging to unified automations.log
    from lib.logging_config import setup_logging
    log_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'logs', 'automations.log')
    setup_logging(log_level='INFO', log_file=log_file)

    result = run()

    # Print result for manual testing
    if DRY_RUN or '--dry-run' in sys.argv:
        import json
        print(json.dumps(result, indent=2))
