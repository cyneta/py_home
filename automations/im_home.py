#!/usr/bin/env python
"""
I'm Home Automation

Welcome home routine when arriving.

Actions:
1. Set Nest thermostat to comfort temp (72°F)
2. Send welcome notification
3. (Future: Turn on entry lights)

Usage:
    python automations/im_home.py
    python automations/im_home.py --dry-run  # Test without executing
    DRY_RUN=true python automations/im_home.py  # Test without executing
"""

import logging
import os
import sys
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for dry-run mode
DRY_RUN = os.environ.get('DRY_RUN', 'false').lower() == 'true' or '--dry-run' in sys.argv


def run():
    """Execute I'm home automation"""
    timestamp = datetime.now().isoformat()

    if DRY_RUN:
        logger.info(f"[DRY-RUN] I'm home automation triggered at {timestamp}")
    else:
        logger.info(f"I'm home automation triggered at {timestamp}")

    results = {
        'timestamp': timestamp,
        'action': 'im_home',
        'message': 'Welcome home routine',
        'errors': []
    }

    # 1. Set Nest to comfort temperature
    try:
        from components.nest import NestAPI
        from lib.config import config

        comfort_temp = config['nest']['comfort_temp']
        nest = NestAPI(dry_run=DRY_RUN)
        nest.set_temperature(comfort_temp)
        results['nest'] = f'Set to {comfort_temp}°F (comfort mode)'
        logger.info(f"✓ Nest set to comfort temp: {comfort_temp}°F")
    except Exception as e:
        logger.error(f"✗ Failed to set Nest: {e}")
        results['errors'].append(f"Nest: {e}")

    # 2. Future: Turn on entry lights
    # Will be implemented when additional Tapo devices are configured
    results['lights'] = 'Not configured yet'

    # 3. Send notification
    if DRY_RUN:
        logger.info("[DRY-RUN] Would send notification: 'Welcome home! House is ready.'")
        results['notification'] = 'Skipped (dry-run)'
    else:
        try:
            from lib.notifications import send_low

            if results['errors']:
                message = f"Welcome home (with {len(results['errors'])} errors)"
                send_low(message, title="🏡 Welcome Home")
            else:
                send_low("Welcome home! House is ready.", title="🏡 Welcome Home")

            results['notification'] = 'Sent'
            logger.info("✓ Notification sent")
        except Exception as e:
            logger.error(f"✗ Failed to send notification: {e}")
            results['errors'].append(f"Notification: {e}")

    # Summary
    status = "SUCCESS" if not results['errors'] else "PARTIAL"
    logger.info(f"\n{'='*50}")
    logger.info(f"I'm Home Automation: {status}")
    logger.info(f"  Nest: {results.get('nest', 'FAILED')}")
    logger.info(f"  Lights: {results.get('lights', 'FAILED')}")
    logger.info(f"  Notification: {results.get('notification', 'FAILED')}")

    if results['errors']:
        logger.info(f"\nErrors:")
        for error in results['errors']:
            logger.info(f"  - {error}")

    logger.info(f"{'='*50}\n")

    return results


if __name__ == '__main__':
    run()
