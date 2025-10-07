#!/usr/bin/env python
"""
Leaving Home Automation

Migrated from: siri_n8n/n8n/workflows/leaving-home.json

Actions:
1. Set Nest thermostat to away temp (62°F)
2. Turn off all Tapo outlets (coffee maker, lamps, heater)
3. (Future: Start Roborock vacuum)
4. Send notification

Usage:
    python automations/leaving_home.py
    python automations/leaving_home.py --dry-run  # Safe testing mode
"""

import os
import sys
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for dry-run mode
DRY_RUN = os.environ.get('DRY_RUN', 'false').lower() == 'true' or '--dry-run' in sys.argv


def run():
    """Execute leaving home automation"""
    timestamp = datetime.now().isoformat()

    if DRY_RUN:
        logger.info(f"[DRY-RUN] Leaving home automation triggered at {timestamp}")
    else:
        logger.info(f"Leaving home automation triggered at {timestamp}")

    results = {
        'timestamp': timestamp,
        'action': 'leaving_home',
        'message': 'Setting house to away mode',
        'errors': []
    }

    # 1. Set Nest to away temperature
    try:
        from components.nest import NestAPI
        from lib.config import config

        away_temp = config['nest']['away_temp']
        nest = NestAPI(dry_run=DRY_RUN)
        nest.set_temperature(away_temp)
        results['nest'] = f'Set to {away_temp}°F (away mode)'
        logger.info(f"✓ Nest set to away temp: {away_temp}°F")
    except Exception as e:
        logger.error(f"✗ Failed to set Nest: {e}")
        results['errors'].append(f"Nest: {e}")

    # 2. Turn off all Tapo outlets
    try:
        from components.tapo import TapoAPI

        tapo = TapoAPI(dry_run=DRY_RUN)
        tapo.turn_off_all()
        results['tapo'] = 'All outlets turned off'
        logger.info("✓ All Tapo outlets turned off")
    except Exception as e:
        logger.error(f"✗ Failed to turn off outlets: {e}")
        results['errors'].append(f"Tapo: {e}")

    # 3. Future: Start vacuum
    # Will be implemented when Roborock component is ready
    results['vacuum'] = 'Not configured yet'

    # 4. Send notification
    try:
        if DRY_RUN:
            logger.info("[DRY-RUN] Would send notification")
            results['notification'] = 'Skipped (dry-run)'
        else:
            from lib.notifications import send

            if results['errors']:
                message = f"House set to away mode (with {len(results['errors'])} errors)"
                send(message, title="🏠 Leaving Home", priority=1)
            else:
                send("House secured - Away mode activated", title="🏠 Leaving Home")

            results['notification'] = 'Sent'
        logger.info("✓ Notification handled")
    except Exception as e:
        logger.error(f"✗ Failed to send notification: {e}")
        results['errors'].append(f"Notification: {e}")

    # Summary
    status = "SUCCESS" if not results['errors'] else "PARTIAL"
    logger.info(f"\n{'='*50}")
    logger.info(f"Leaving Home Automation: {status}")
    logger.info(f"  Nest: {results.get('nest', 'FAILED')}")
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
