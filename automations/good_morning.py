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
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for dry-run mode
DRY_RUN = os.environ.get('DRY_RUN', 'false').lower() == 'true' or '--dry-run' in sys.argv


def run():
    """Execute good morning automation"""
    timestamp = datetime.now().isoformat()

    if DRY_RUN:
        logger.info(f"[DRY-RUN] Good morning automation triggered at {timestamp}")
    else:
        logger.info(f"Good morning automation triggered at {timestamp}")

    results = {
        'timestamp': timestamp,
        'action': 'good_morning',
        'message': 'Morning routine',
        'errors': []
    }

    # 1. Set Nest to comfort temperature
    try:
        from components.nest import NestAPI

        comfort_temp = 70
        nest = NestAPI(dry_run=DRY_RUN)
        nest.set_temperature(comfort_temp)
        results['nest'] = f'Set to {comfort_temp}°F'
        logger.info(f"✓ Nest set to {comfort_temp}°F")
    except Exception as e:
        logger.error(f"✗ Failed to set Nest: {e}")
        results['errors'].append(f"Nest: {e}")

    # 2. Get weather forecast
    try:
        from services import get_weather_summary

        weather_summary = get_weather_summary()
        results['weather'] = weather_summary
        logger.info(f"✓ Weather: {weather_summary}")
    except Exception as e:
        logger.error(f"✗ Failed to get weather: {e}")
        results['errors'].append(f"Weather: {e}")
        weather_summary = "Weather unavailable"

    # 3. Future: Turn on coffee maker
    # Uncomment when coffee maker outlet is identified
    # try:
    #     from components.tapo import turn_on
    #     turn_on("Heater")  # Replace with actual coffee maker name
    #     results['coffee'] = 'Coffee maker started'
    #     logger.info("✓ Coffee maker turned on")
    # except Exception as e:
    #     logger.error(f"✗ Failed to turn on coffee maker: {e}")
    #     results['errors'].append(f"Coffee: {e}")

    results['coffee'] = 'Not configured yet'

    # 4. Send morning summary notification
    if DRY_RUN:
        logger.info(f"[DRY-RUN] Would send notification: 'Good morning! {weather_summary}'")
        results['notification'] = 'Skipped (dry-run)'
    else:
        try:
            from lib.notifications import send

            notification_msg = f"Good morning! {weather_summary}"

            send(notification_msg, title="☀️ Good Morning")
            results['notification'] = 'Sent'
            logger.info("✓ Notification sent")
        except Exception as e:
            logger.error(f"✗ Failed to send notification: {e}")
            results['errors'].append(f"Notification: {e}")

    # Summary
    status = "SUCCESS" if not results['errors'] else "PARTIAL"
    logger.info(f"\n{'='*50}")
    logger.info(f"Good Morning Automation: {status}")
    logger.info(f"  Nest: {results.get('nest', 'FAILED')}")
    logger.info(f"  Weather: {results.get('weather', 'FAILED')}")
    logger.info(f"  Coffee: {results.get('coffee', 'FAILED')}")
    logger.info(f"  Notification: {results.get('notification', 'FAILED')}")

    if results['errors']:
        logger.info(f"\nErrors:")
        for error in results['errors']:
            logger.info(f"  - {error}")

    logger.info(f"{'='*50}\n")

    return results


if __name__ == '__main__':
    run()
