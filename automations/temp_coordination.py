#!/usr/bin/env python
"""
Temperature Coordination Automation

Coordinates Nest thermostat (main house) and Sensibo mini-split (bedroom).

Simple 3-state logic:
1. Away: Both in energy-saving mode
2. Sleep: Nest ECO (62-80°F), Sensibo active (66°F bedroom)
3. Awake: Both active at comfort temp (70°F)

Designed to run as a cron job every 15 minutes:
    */15 * * * * cd /home/pi/py_home && python automations/temp_coordination.py

Usage:
    python automations/temp_coordination.py
    python automations/temp_coordination.py --dry-run  # Test without executing
    DRY_RUN=true python automations/temp_coordination.py  # Test without executing
"""

import logging
import os
import sys
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/c/git/cyneta/py_home')

from lib.logging_config import setup_logging, kvlog
from lib.hvac_logic import is_sleep_time
from components.nest import NestAPI
from components.sensibo import SensiboAPI

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Check for dry-run mode (priority: flag > env var > config > default)
from lib.config import get
DRY_RUN = (
    '--dry-run' in sys.argv or
    os.environ.get('DRY_RUN', '').lower() == 'true' or
    get('automations.dry_run', False)
)

# Create API instances with dry_run mode
nest = NestAPI(dry_run=DRY_RUN)
sensibo = SensiboAPI(dry_run=DRY_RUN)


def check_presence():
    """
    Check if anyone is home using centralized presence state.

    Returns:
        bool: True if home, False if away
    """
    try:
        presence_file = os.path.join(os.path.dirname(__file__), '..', '.presence_state')

        if os.path.exists(presence_file):
            with open(presence_file, 'r') as f:
                state = f.read().strip().lower()
                is_home = (state == 'home')
        else:
            # Fallback to ping if state file doesn't exist
            from components.network import is_device_home
            from lib.config import config
            primary_ip = config['presence']['devices']['primary']['ip']
            is_home = is_device_home(primary_ip)

        kvlog(logger, logging.INFO, automation='temp_coordination',
              check='presence', status='home' if is_home else 'away')
        return is_home

    except Exception as e:
        kvlog(logger, logging.ERROR, automation='temp_coordination',
              check='presence', error_type=type(e).__name__, error_msg=str(e))
        # Default to home (safer than turning off heat/AC)
        return True


def run():
    """Execute temperature coordination"""
    start_time = time.time()
    kvlog(logger, logging.NOTICE, automation='temp_coordination', event='start', dry_run=DRY_RUN)

    errors = []

    try:
        # Determine mode based on presence and time
        is_home = check_presence()
        is_sleep = is_sleep_time()

        # State machine: 3 simple states
        if not is_home:
            # State 1: AWAY - Nobody home
            mode = 'away'
            kvlog(logger, logging.NOTICE, automation='temp_coordination',
                  mode=mode, reason='nobody_home')

            try:
                api_start = time.time()
                nest.set_away_mode()
                duration_ms = int((time.time() - api_start) * 1000)
                kvlog(logger, logging.NOTICE, automation='temp_coordination',
                      device='nest', action='set_away', result='ok', duration_ms=duration_ms)
            except Exception as e:
                kvlog(logger, logging.ERROR, automation='temp_coordination',
                      device='nest', action='set_away',
                      error_type=type(e).__name__, error_msg=str(e))
                errors.append(f"Nest: {e}")

            try:
                api_start = time.time()
                sensibo.set_away_mode()
                duration_ms = int((time.time() - api_start) * 1000)
                kvlog(logger, logging.NOTICE, automation='temp_coordination',
                      device='sensibo', action='set_away', result='ok', duration_ms=duration_ms)
            except Exception as e:
                kvlog(logger, logging.ERROR, automation='temp_coordination',
                      device='sensibo', action='set_away',
                      error_type=type(e).__name__, error_msg=str(e))
                errors.append(f"Sensibo: {e}")

        elif is_sleep:
            # State 2: SLEEP - Home but sleeping (22:30-05:00)
            mode = 'sleep'
            kvlog(logger, logging.NOTICE, automation='temp_coordination',
                  mode=mode, reason='sleep_hours')

            try:
                api_start = time.time()
                nest.set_sleep_mode()  # ECO mode (62-80°F)
                duration_ms = int((time.time() - api_start) * 1000)
                kvlog(logger, logging.NOTICE, automation='temp_coordination',
                      device='nest', action='set_sleep', result='ok', duration_ms=duration_ms)
            except Exception as e:
                kvlog(logger, logging.ERROR, automation='temp_coordination',
                      device='nest', action='set_sleep',
                      error_type=type(e).__name__, error_msg=str(e))
                errors.append(f"Nest: {e}")

            try:
                api_start = time.time()
                sensibo.set_sleep_mode()  # Active at 66°F
                duration_ms = int((time.time() - api_start) * 1000)
                kvlog(logger, logging.NOTICE, automation='temp_coordination',
                      device='sensibo', action='set_sleep', result='ok', duration_ms=duration_ms)
            except Exception as e:
                kvlog(logger, logging.ERROR, automation='temp_coordination',
                      device='sensibo', action='set_sleep',
                      error_type=type(e).__name__, error_msg=str(e))
                errors.append(f"Sensibo: {e}")

        else:
            # State 3: COMFORT - Home and awake (05:00-22:30)
            mode = 'comfort'
            kvlog(logger, logging.NOTICE, automation='temp_coordination',
                  mode=mode, reason='awake_hours')

            try:
                api_start = time.time()
                nest.set_comfort_mode()  # Active at 70°F
                duration_ms = int((time.time() - api_start) * 1000)
                kvlog(logger, logging.NOTICE, automation='temp_coordination',
                      device='nest', action='set_comfort', result='ok', duration_ms=duration_ms)
            except Exception as e:
                kvlog(logger, logging.ERROR, automation='temp_coordination',
                      device='nest', action='set_comfort',
                      error_type=type(e).__name__, error_msg=str(e))
                errors.append(f"Nest: {e}")

            try:
                api_start = time.time()
                sensibo.set_comfort_mode()  # Active at 70°F (helps Nest)
                duration_ms = int((time.time() - api_start) * 1000)
                kvlog(logger, logging.NOTICE, automation='temp_coordination',
                      device='sensibo', action='set_comfort', result='ok', duration_ms=duration_ms)
            except Exception as e:
                kvlog(logger, logging.ERROR, automation='temp_coordination',
                      device='sensibo', action='set_comfort',
                      error_type=type(e).__name__, error_msg=str(e))
                errors.append(f"Sensibo: {e}")

    except Exception as e:
        kvlog(logger, logging.ERROR, automation='temp_coordination', event='failed',
              error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Fatal: {e}")
        return 1

    # Complete
    total_duration_ms = int((time.time() - start_time) * 1000)
    kvlog(logger, logging.NOTICE, automation='temp_coordination', event='complete',
          mode=mode, duration_ms=total_duration_ms, errors=len(errors))

    return 0 if not errors else 1


if __name__ == '__main__':
    sys.exit(run())
