#!/usr/bin/env python
"""
Scheduler - Time-based transition trigger

Runs every minute via cron.
Checks current time against configured schedule times.
Triggers appropriate transitions when time matches.

Cron job:
    * * * * * cd /home/matt.wheeler/py_home && /home/matt.wheeler/py_home/venv/bin/python automations/scheduler.py >> /home/matt.wheeler/py_home/data/logs/automations.log 2>&1

Schedule times configured in config.yaml:
    schedule.wake_time: "05:00"   # Morning wake transition
    schedule.sleep_time: "22:30"  # Evening sleep transition

State tracking:
    - Uses .scheduler_state file to prevent duplicate transitions
    - Tracks last run date per transition type
    - Resets automatically when date changes (new day = can run again)

Design principle:
    System executes scheduled transitions at specific times,
    but respects user manual adjustments between transitions.

See: design/scheduler_transitions.md for complete architecture
See: design/principles/user_control.md for design principle

Usage:
    python automations/scheduler.py
    python automations/scheduler.py --dry-run  # Test without executing
    DRY_RUN=true python automations/scheduler.py  # Test without executing
"""

import logging
import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from lib.logging_config import setup_logging, kvlog
from lib.config import get

logger = logging.getLogger(__name__)

# Check for dry-run mode
DRY_RUN = (
    '--dry-run' in sys.argv or
    os.environ.get('DRY_RUN', '').lower() == 'true' or
    get('automations.dry_run', False)
)

# State file location
PROJECT_ROOT = Path(__file__).parent.parent
STATE_FILE = PROJECT_ROOT / '.scheduler_state'


def already_ran_today(transition_type):
    """
    Check if transition already ran today

    Args:
        transition_type: 'wake' or 'sleep'

    Returns:
        bool: True if transition already ran today
    """
    if not STATE_FILE.exists():
        return False

    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            last_run_date = state.get(f'last_{transition_type}_date')
            today = datetime.now().date().isoformat()
            return last_run_date == today
    except (json.JSONDecodeError, KeyError) as e:
        kvlog(logger, logging.WARNING, automation='scheduler',
              action='check_state', transition=transition_type,
              error_type=type(e).__name__, error_msg=str(e))
        # Assume not run if state file corrupt
        return False


def mark_completed(transition_type):
    """
    Mark transition as completed today

    Args:
        transition_type: 'wake' or 'sleep'
    """
    today = datetime.now().date().isoformat()

    # Load existing state
    state = {}
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
        except json.JSONDecodeError:
            kvlog(logger, logging.WARNING, automation='scheduler',
                  action='load_state', result='corrupt_file', note='creating_new')

    # Update state
    state[f'last_{transition_type}_date'] = today

    # Save state
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        kvlog(logger, logging.DEBUG, automation='scheduler',
              action='mark_completed', transition=transition_type, date=today)
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='scheduler',
              action='mark_completed', transition=transition_type,
              error_type=type(e).__name__, error_msg=str(e))


def should_transition_to_wake():
    """
    Check if should trigger wake transition now

    Checks:
    1. Current time matches wake_time (exact hour:minute)
    2. Haven't already transitioned today

    Returns:
        bool: True if should trigger wake transition
    """
    now = datetime.now()
    wake_time = get('schedule.wake_time', '05:00')
    hour, minute = map(int, wake_time.split(':'))

    # Exact time match (within same minute)
    time_matches = now.hour == hour and now.minute == minute

    if time_matches:
        # Check if already ran today
        already_done = already_ran_today('wake')
        kvlog(logger, logging.DEBUG, automation='scheduler',
              check='should_transition_to_wake', time_matches=True,
              already_done=already_done)
        return not already_done

    return False


def should_transition_to_sleep():
    """
    Check if should trigger sleep transition now

    Checks:
    1. Current time matches sleep_time (exact hour:minute)
    2. Haven't already transitioned today

    Returns:
        bool: True if should trigger sleep transition
    """
    now = datetime.now()
    sleep_time = get('schedule.sleep_time', '22:30')
    hour, minute = map(int, sleep_time.split(':'))

    # Exact time match (within same minute)
    time_matches = now.hour == hour and now.minute == minute

    if time_matches:
        # Check if already ran today
        already_done = already_ran_today('sleep')
        kvlog(logger, logging.DEBUG, automation='scheduler',
              check='should_transition_to_sleep', time_matches=True,
              already_done=already_done)
        return not already_done

    return False


def run():
    """
    Main scheduler logic

    Checks time and triggers transitions if needed.
    Most runs will be no-ops (not matching any transition time).
    """
    start_time = time.time()

    # Check wake transition
    if should_transition_to_wake():
        kvlog(logger, logging.NOTICE, automation='scheduler',
              event='wake_time', action='triggering_wake_transition', dry_run=DRY_RUN)

        from lib.transitions import transition_to_wake
        result = transition_to_wake(dry_run=DRY_RUN)

        kvlog(logger, logging.NOTICE, automation='scheduler',
              transition='wake', status=result['status'],
              actions_count=len(result['actions']),
              errors_count=len(result['errors']),
              duration_ms=result['duration_ms'])

        if not DRY_RUN:
            mark_completed('wake')

        # Log completion
        total_duration_ms = int((time.time() - start_time) * 1000)
        kvlog(logger, logging.INFO, automation='scheduler',
              event='complete', transition='wake', duration_ms=total_duration_ms)
        return

    # Check sleep transition
    if should_transition_to_sleep():
        kvlog(logger, logging.NOTICE, automation='scheduler',
              event='sleep_time', action='triggering_sleep_transition', dry_run=DRY_RUN)

        from lib.transitions import transition_to_sleep
        result = transition_to_sleep(dry_run=DRY_RUN)

        kvlog(logger, logging.NOTICE, automation='scheduler',
              transition='sleep', status=result['status'],
              actions_count=len(result['actions']),
              errors_count=len(result['errors']),
              duration_ms=result['duration_ms'])

        if not DRY_RUN:
            mark_completed('sleep')

        # Log completion
        total_duration_ms = int((time.time() - start_time) * 1000)
        kvlog(logger, logging.INFO, automation='scheduler',
              event='complete', transition='sleep', duration_ms=total_duration_ms)
        return

    # Most runs: No-op (not matching any transition time)
    # Only log if we took significant time (> 100ms indicates we did something)
    duration_ms = int((time.time() - start_time) * 1000)
    if duration_ms > 100:
        kvlog(logger, logging.DEBUG, automation='scheduler',
              event='check', result='no_transition', duration_ms=duration_ms)


if __name__ == '__main__':
    # Set up logging
    log_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'logs', 'automations.log')
    setup_logging(log_level='INFO', log_file=log_file)

    run()
