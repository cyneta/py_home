#!/usr/bin/env python
"""
Leaving Home Automation

Migrated from: siri_n8n/n8n/workflows/leaving-home.json

Actions:
1. Set Nest thermostat to ECO mode (energy-saving)
2. Turn off all Tapo outlets (coffee maker, lamps, heater)
3. Update presence state to 'away'
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

# Check for dry-run mode (priority: CLI flag > config file)
from lib.config import get
DRY_RUN = (
    '--dry-run' in sys.argv or
    get('automations.dry_run', False)
)


def update_presence_state():
    """Update presence state to 'away' when leaving home"""
    from pathlib import Path
    state_file = Path(__file__).parent.parent / '.presence_state'

    try:
        with open(state_file, 'w') as f:
            f.write('away')
        kvlog(logger, logging.DEBUG, automation='leaving_home', action='update_state',
              state='away', result='ok')
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='leaving_home', action='update_state',
              error_type=type(e).__name__, error_msg=str(e))


def run():
    """Execute leaving home automation"""
    start_time = time.time()
    kvlog(logger, logging.NOTICE, automation='leaving_home', event='start', dry_run=DRY_RUN)

    # Call away transition - handles all device control and notifications
    from lib.transitions import transition_to_away
    result = transition_to_away(dry_run=DRY_RUN)

    # Log transition result
    kvlog(logger, logging.NOTICE, automation='leaving_home',
          transition='away', status=result['status'],
          actions_count=len(result['actions']),
          errors_count=len(result['errors']),
          duration_ms=result['duration_ms'])

    # Unique logic for leaving_home: Update presence state to 'away'
    if not DRY_RUN:
        update_presence_state()

    # Complete
    total_duration_ms = int((time.time() - start_time) * 1000)
    kvlog(logger, logging.NOTICE, automation='leaving_home', event='complete',
          duration_ms=total_duration_ms, errors=len(result['errors']))

    return {
        'action': 'leaving_home',
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
