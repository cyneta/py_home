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

# Check for dry-run mode (priority: CLI flag > config file)
from lib.config import get
DRY_RUN = (
    '--dry-run' in sys.argv or
    get('automations.dry_run', False)
)


def run():
    """Execute good morning automation"""
    start_time = time.time()
    kvlog(logger, logging.NOTICE, automation='good_morning', event='start', dry_run=DRY_RUN)

    # Call wake transition - handles all device control and notifications
    from lib.transitions import transition_to_wake
    result = transition_to_wake(dry_run=DRY_RUN)

    # Log transition result
    kvlog(logger, logging.NOTICE, automation='good_morning',
          transition='wake', status=result['status'],
          actions_count=len(result['actions']),
          errors_count=len(result['errors']),
          duration_ms=result['duration_ms'])

    # Note: Weather brief is now included in the transition notification
    # The transition already fetches weather and includes it in the notification
    # with weather-aware temperature adjustments

    # Complete
    total_duration_ms = int((time.time() - start_time) * 1000)
    kvlog(logger, logging.NOTICE, automation='good_morning', event='complete',
          duration_ms=total_duration_ms, errors=len(result['errors']))

    return {
        'action': 'good_morning',
        'status': result['status'],
        'errors': result['errors'],
        'duration_ms': total_duration_ms
    }


if __name__ == '__main__':
    # Set up logging to unified automations.log
    from lib.logging_config import setup_logging
    log_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'logs', 'automations.log')
    setup_logging(log_level='INFO', log_file=log_file)

    run()
