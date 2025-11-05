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

# Check for dry-run mode (priority: CLI flag > config file)
from lib.config import get
DRY_RUN = (
    '--dry-run' in sys.argv or
    get('automations.dry_run', False)
)


def run():
    """Execute goodnight automation"""
    start_time = time.time()
    kvlog(logger, logging.NOTICE, automation='goodnight', event='start', dry_run=DRY_RUN)

    # Call sleep transition - handles all device control and notifications
    from lib.transitions import transition_to_sleep
    result = transition_to_sleep(dry_run=DRY_RUN)

    # Log transition result
    kvlog(logger, logging.NOTICE, automation='goodnight',
          transition='sleep', status=result['status'],
          actions_count=len(result['actions']),
          errors_count=len(result['errors']),
          duration_ms=result['duration_ms'])

    # Complete
    total_duration_ms = int((time.time() - start_time) * 1000)
    kvlog(logger, logging.NOTICE, automation='goodnight', event='complete',
          duration_ms=total_duration_ms, errors=len(result['errors']))

    return {
        'action': 'goodnight',
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
