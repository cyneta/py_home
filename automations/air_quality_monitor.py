#!/usr/bin/env python
"""
Air Quality Monitor

Monitors Alen air purifiers for PM2.5 air quality:
- Unhealthy air (PM2.5 > 100)
- Moderate air quality (PM2.5 > 50)
- Device offline warnings

Usage:
    python automations/air_quality_monitor.py [--dry-run]

Schedule with cron:
    */30 * * * * cd /home/pi/py_home && python automations/air_quality_monitor.py
"""

import sys
import os
import argparse
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.tuya import get_air_quality
from lib.notifications import send, send_high
from lib.logging_config import setup_logging, kvlog
from lib.alert_state import should_send_alert, record_alert_sent

logger = logging.getLogger(__name__)

# Air Quality Thresholds (EPA AQI standards)
# PM2.5 concentration (μg/m³)
GOOD = 12.0  # 0-12: Good
MODERATE = 35.4  # 12.1-35.4: Moderate (sensitive groups)
UNHEALTHY_SENSITIVE = 55.4  # 35.5-55.4: Unhealthy for sensitive groups
UNHEALTHY = 150.4  # 55.5-150.4: Unhealthy
VERY_UNHEALTHY = 250.4  # 150.5-250.4: Very unhealthy

# Alert thresholds (simplified)
MODERATE_THRESHOLD = 50.0  # Alert for sensitive groups
UNHEALTHY_THRESHOLD = 100.0  # Alert for everyone


def check_air_quality(device_name, dry_run=False):
    """
    Check air quality for a specific device

    Args:
        device_name: Device name (bedroom or living_room)
        dry_run: If True, don't send notifications

    Returns:
        bool: True if issues detected
    """
    try:
        aq = get_air_quality(device_name)

        pm25 = aq['pm25']
        aqi = aq['aqi']
        quality = aq['quality']
        location = device_name.replace('_', ' ').title()

        kvlog(logger, logging.INFO, automation='air_quality_monitor',
              device=device_name, pm25=pm25, aqi=aqi, quality=quality)

        # Check for unhealthy air
        if pm25 >= UNHEALTHY_THRESHOLD:
            title = f"🔴 Air Quality ({location})"
            message = f"PM2.5 {pm25:.0f} - Unhealthy"

            kvlog(logger, logging.WARNING, automation='air_quality_monitor',
                  alert='unhealthy_air', device=device_name, pm25=pm25,
                  threshold=UNHEALTHY_THRESHOLD, dry_run=dry_run)

            # Rate limiting: max 1 alert per hour
            if should_send_alert('unhealthy_air', device_name, cooldown_minutes=60):
                if not dry_run:
                    send_high(message, title)
                    record_alert_sent('unhealthy_air', device_name)
                else:
                    logger.info(f"[DRY-RUN] Would send alert: {title}: {message}")
            else:
                logger.info(f"Alert suppressed (cooldown): {title}: {message}")

            return True

        elif pm25 >= MODERATE_THRESHOLD:
            title = f"⚠️ Air Quality ({location})"
            message = f"PM2.5 {pm25:.0f} - Moderate"

            kvlog(logger, logging.NOTICE, automation='air_quality_monitor',
                  alert='moderate_air', device=device_name, pm25=pm25,
                  threshold=MODERATE_THRESHOLD, dry_run=dry_run)

            # Rate limiting: max 1 alert per hour
            if should_send_alert('moderate_air', device_name, cooldown_minutes=60):
                if not dry_run:
                    send(message, title)
                    record_alert_sent('moderate_air', device_name)
                else:
                    logger.info(f"[DRY-RUN] Would send warning: {title}: {message}")
            else:
                logger.info(f"Alert suppressed (cooldown): {title}: {message}")

            return True

        # Air is good
        logger.info(f"✓ {location}: PM2.5 {pm25:.0f} - {quality}")
        return False

    except Exception as e:
        # Device offline or error
        location = device_name.replace('_', ' ').title()
        title = f"⚠️ Air Quality ({location})"
        message = "Device offline"

        kvlog(logger, logging.WARNING, automation='air_quality_monitor',
              alert='device_offline', device=device_name,
              error_type=type(e).__name__, error_msg=str(e), dry_run=dry_run)

        # Rate limiting: max 1 alert per 2 hours for offline devices
        if should_send_alert('device_offline', device_name, cooldown_minutes=120):
            if not dry_run:
                send(message, title)
                record_alert_sent('device_offline', device_name)
            else:
                logger.info(f"[DRY-RUN] Would send alert: {title}: {message}")
        else:
            logger.info(f"Alert suppressed (cooldown): {title}: {message}")

        return True


def main():
    parser = argparse.ArgumentParser(description='Air Quality Monitor')
    parser.add_argument('--dry-run', action='store_true',
                        help='Test mode - no actual notifications sent')
    args = parser.parse_args()

    # Setup logging
    setup_logging('INFO')

    kvlog(logger, logging.NOTICE, automation='air_quality_monitor', event='start',
          dry_run=args.dry_run)

    # Check both devices
    devices = ['bedroom', 'living_room']
    issues_found = False

    for device in devices:
        if check_air_quality(device, args.dry_run):
            issues_found = True

    if not issues_found:
        kvlog(logger, logging.INFO, automation='air_quality_monitor',
              event='complete', status='ok', issues_found=False)
        logger.info("✓ All air quality checks passed - Air is good")
    else:
        kvlog(logger, logging.WARNING, automation='air_quality_monitor',
              event='complete', status='issues_found', issues_found=True)
        logger.warning("⚠️ Air quality issues detected - alerts sent")

    return 0


if __name__ == '__main__':
    sys.exit(main())
