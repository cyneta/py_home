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
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for dry-run mode
DRY_RUN = os.environ.get('DRY_RUN', 'false').lower() == 'true' or '--dry-run' in sys.argv


def run():
    """Execute goodnight automation"""
    timestamp = datetime.now().isoformat()

    if DRY_RUN:
        logger.info(f"[DRY-RUN] Goodnight automation triggered at {timestamp}")
    else:
        logger.info(f"Goodnight automation triggered at {timestamp}")

    results = {
        'timestamp': timestamp,
        'action': 'goodnight',
        'message': 'Setting house to sleep mode',
        'errors': []
    }

    # 1. Set Nest to sleep temperature
    try:
        from components.nest import NestAPI
        from lib.config import config

        sleep_temp = config['nest']['sleep_temp']
        nest = NestAPI(dry_run=DRY_RUN)
        nest.set_temperature(sleep_temp)
        results['nest'] = f'Set to {sleep_temp}°F (sleep mode)'
        logger.info(f"✓ Nest set to sleep temp: {sleep_temp}°F")
    except Exception as e:
        logger.error(f"✗ Failed to set Nest: {e}")
        results['errors'].append(f"Nest: {e}")

    # 2. Turn off Sensibo AC
    try:
        from components.sensibo import SensiboAPI

        sensibo = SensiboAPI(dry_run=DRY_RUN)
        sensibo.turn_off()
        results['sensibo'] = 'AC turned off'
        logger.info("✓ Sensibo AC turned off")
    except Exception as e:
        logger.error(f"✗ Failed to turn off Sensibo: {e}")
        results['errors'].append(f"Sensibo: {e}")

    # 3. Turn off all Tapo outlets
    try:
        from components.tapo import TapoAPI

        tapo = TapoAPI(dry_run=DRY_RUN)
        tapo.turn_off_all()
        results['tapo'] = 'All outlets turned off'
        logger.info("✓ All Tapo outlets turned off")
    except Exception as e:
        logger.error(f"✗ Failed to turn off outlets: {e}")
        results['errors'].append(f"Tapo: {e}")

    # 4. Future: Start vacuum
    # Will be implemented when Roborock component is ready
    results['vacuum'] = 'Not configured yet'

    # 5. Send notification
    if DRY_RUN:
        logger.info("[DRY-RUN] Would send notification: 'Goodnight - Sleep mode activated'")
        results['notification'] = 'Skipped (dry-run)'
    else:
        try:
            from lib.notifications import send

            if results['errors']:
                message = f"Sleep mode activated (with {len(results['errors'])} errors)"
                send(message, title="😴 Goodnight", priority=1)
            else:
                send("Goodnight - Sleep mode activated", title="😴 Goodnight")

            results['notification'] = 'Sent'
            logger.info("✓ Notification sent")
        except Exception as e:
            logger.error(f"✗ Failed to send notification: {e}")
            results['errors'].append(f"Notification: {e}")

    # Summary
    status = "SUCCESS" if not results['errors'] else "PARTIAL"
    logger.info(f"\n{'='*50}")
    logger.info(f"Goodnight Automation: {status}")
    logger.info(f"  Nest: {results.get('nest', 'FAILED')}")
    logger.info(f"  Sensibo: {results.get('sensibo', 'FAILED')}")
    logger.info(f"  Tapo: {results.get('tapo', 'FAILED')}")
    logger.info(f"  Vacuum: {results.get('vacuum', 'FAILED')}")
    logger.info(f"  Notification: {results.get('notification', 'FAILED')}")

    if results['errors']:
        logger.info(f"\nErrors:")
        for error in results['errors']:
            logger.info(f"  - {error}")

    logger.info(f"{'='*50}\n")

    return results


if __name__ == '__main__':
    run()
