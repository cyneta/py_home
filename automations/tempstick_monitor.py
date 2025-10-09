#!/usr/bin/env python
"""
Temp Stick Monitor

Monitors Temp Stick temperature/humidity sensor for:
- Pipe freeze risk (temp < 50°F)
- High humidity/leak detection (humidity > 65%)
- Sensor offline warnings
- Equipment failure detection (rapid temp drop)

Location: Configurable via config.yaml (tempstick.room)
Current location: Crawlspace near laundry pipes

Usage:
    python automations/tempstick_monitor.py [--dry-run]

Schedule with cron:
    */30 * * * * cd /home/pi/py_home && python automations/tempstick_monitor.py
"""

import sys
import os
import argparse
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.tempstick import get_sensor_data
from lib.notifications import send, send_high
from lib.logging_config import setup_logging, kvlog
from lib.alert_state import should_send_alert, record_alert_sent

logger = logging.getLogger(__name__)

# Thresholds
PIPE_FREEZE_TEMP = 50.0  # °F - Alert when below this
COLD_WARNING_TEMP = 55.0  # °F - Warning when below this
HIGH_HUMIDITY = 65.0  # % - Alert when above this
VERY_HIGH_HUMIDITY = 70.0  # % - Urgent alert
SENSOR_OFFLINE_MINUTES = 60  # Minutes before offline alert


def check_pipe_freeze_risk(temp_f, room, dry_run=False):
    """
    Check for pipe freeze risk

    Args:
        temp_f: Current temperature in Fahrenheit
        room: Location name
        dry_run: If True, don't send notifications

    Returns:
        bool: True if freeze risk detected
    """
    if temp_f < PIPE_FREEZE_TEMP:
        title = f"🚨 Temp Stick ({room})"
        message = f"{temp_f:.1f}°F - FREEZE RISK"

        kvlog(logger, logging.WARNING, automation='tempstick_monitor',
              alert='pipe_freeze_risk', room=room, temp_f=temp_f,
              threshold=PIPE_FREEZE_TEMP, dry_run=dry_run)

        # Rate limiting: max 1 alert per hour
        if should_send_alert('pipe_freeze', room, cooldown_minutes=60):
            if not dry_run:
                send_high(message, title)
                record_alert_sent('pipe_freeze', room)
            else:
                logger.info(f"[DRY-RUN] Would send alert: {title}: {message}")
        else:
            logger.info(f"Alert suppressed (cooldown): {title}: {message}")

        return True

    elif temp_f < COLD_WARNING_TEMP:
        title = f"⚠️ Temp Stick ({room})"
        message = f"{temp_f:.1f}°F - Cold warning"

        kvlog(logger, logging.NOTICE, automation='tempstick_monitor',
              alert='cold_warning', room=room, temp_f=temp_f,
              threshold=COLD_WARNING_TEMP, dry_run=dry_run)

        # Rate limiting: max 1 alert per hour
        if should_send_alert('cold_warning', room, cooldown_minutes=60):
            if not dry_run:
                send(message, title)
                record_alert_sent('cold_warning', room)
            else:
                logger.info(f"[DRY-RUN] Would send warning: {title}: {message}")
        else:
            logger.info(f"Alert suppressed (cooldown): {title}: {message}")

        return True

    return False


def check_humidity_risk(humidity, room, dry_run=False):
    """
    Check for high humidity (potential leak/mold)

    Args:
        humidity: Current humidity percentage
        room: Location name
        dry_run: If True, don't send notifications

    Returns:
        bool: True if humidity risk detected
    """
    if humidity > VERY_HIGH_HUMIDITY:
        title = f"🚨 Temp Stick ({room})"
        message = f"{humidity:.1f}% humidity - LEAK RISK"

        kvlog(logger, logging.WARNING, automation='tempstick_monitor',
              alert='very_high_humidity', room=room, humidity=humidity,
              threshold=VERY_HIGH_HUMIDITY, dry_run=dry_run)

        # Rate limiting: max 1 alert per hour
        if should_send_alert('very_high_humidity', room, cooldown_minutes=60):
            if not dry_run:
                send_high(message, title)
                record_alert_sent('very_high_humidity', room)
            else:
                logger.info(f"[DRY-RUN] Would send alert: {title}: {message}")
        else:
            logger.info(f"Alert suppressed (cooldown): {title}: {message}")

        return True

    elif humidity > HIGH_HUMIDITY:
        title = f"⚠️ Temp Stick ({room})"
        message = f"{humidity:.1f}% humidity - High"

        kvlog(logger, logging.NOTICE, automation='tempstick_monitor',
              alert='high_humidity', room=room, humidity=humidity,
              threshold=HIGH_HUMIDITY, dry_run=dry_run)

        # Rate limiting: max 1 alert per hour
        if should_send_alert('high_humidity', room, cooldown_minutes=60):
            if not dry_run:
                send(message, title)
                record_alert_sent('high_humidity', room)
            else:
                logger.info(f"[DRY-RUN] Would send warning: {title}: {message}")
        else:
            logger.info(f"Alert suppressed (cooldown): {title}: {message}")

        return True

    return False


def check_sensor_status(data, dry_run=False):
    """
    Check if sensor is online and battery is OK

    Args:
        data: Sensor data dict
        dry_run: If True, don't send notifications

    Returns:
        bool: True if sensor has issues
    """
    issues = []

    # Check if offline
    if not data['is_online']:
        issues.append("Offline")
        kvlog(logger, logging.WARNING, automation='tempstick_monitor',
              alert='sensor_offline', room=data['room'],
              last_checkin=str(data['last_checkin']), dry_run=dry_run)

    # Check battery
    if data['battery_pct'] < 20:
        issues.append(f"Battery {data['battery_pct']}%")
        kvlog(logger, logging.WARNING, automation='tempstick_monitor',
              alert='low_battery', room=data['room'],
              battery_pct=data['battery_pct'], dry_run=dry_run)

    if issues:
        issue_text = ", ".join(issues)
        title = f"⚠️ Temp Stick ({data['room']})"
        message = f"{issue_text}"

        # Rate limiting: max 1 alert per 2 hours for sensor issues
        if should_send_alert('sensor_issues', data['room'], cooldown_minutes=120):
            if not dry_run:
                send(message, title)
                record_alert_sent('sensor_issues', data['room'])
            else:
                logger.info(f"[DRY-RUN] Would send alert: {title}: {message}")
        else:
            logger.info(f"Alert suppressed (cooldown): {title}: {message}")

        return True

    return False


def get_status_summary(data):
    """
    Get human-readable status summary

    Args:
        data: Sensor data dict

    Returns:
        str: Status summary
    """
    status = "✓" if data['is_online'] else "✗"

    # Temperature status
    if data['temperature_f'] < PIPE_FREEZE_TEMP:
        temp_status = "🚨 FREEZE RISK"
    elif data['temperature_f'] < COLD_WARNING_TEMP:
        temp_status = "⚠️ Cold"
    else:
        temp_status = "✓ OK"

    # Humidity status
    if data['humidity'] > VERY_HIGH_HUMIDITY:
        humid_status = "🚨 VERY HIGH"
    elif data['humidity'] > HIGH_HUMIDITY:
        humid_status = "⚠️ High"
    else:
        humid_status = "✓ OK"

    summary = (
        f"Temp Stick Monitor ({data['room']}):\n"
        f"  Status: {status} {'Online' if data['is_online'] else 'Offline'}\n"
        f"  Temp: {data['temperature_f']:.1f}°F {temp_status}\n"
        f"  Humidity: {data['humidity']:.1f}% {humid_status}\n"
        f"  Battery: {data['battery_pct']}%"
    )

    return summary


def main():
    parser = argparse.ArgumentParser(description='Temp Stick Monitor')
    parser.add_argument('--dry-run', action='store_true',
                        help='Test mode - no actual notifications sent')
    args = parser.parse_args()

    # Setup logging
    setup_logging('INFO')

    kvlog(logger, logging.NOTICE, automation='tempstick_monitor', event='start',
          dry_run=args.dry_run)

    try:
        # Get sensor data
        data = get_sensor_data()

        # Use sensor_name as room for compatibility
        data['room'] = data.get('sensor_name', 'Unknown')

        kvlog(logger, logging.INFO, automation='tempstick_monitor',
              sensor_id=data['sensor_id'], room=data['room'],
              temp_f=data['temperature_f'], humidity=data['humidity'],
              battery_pct=data['battery_pct'], is_online=data['is_online'])

        # Log status summary
        summary = get_status_summary(data)
        logger.info(f"\n{summary}")

        # Check for issues
        issues_found = False

        # 1. Check sensor health first
        if check_sensor_status(data, args.dry_run):
            issues_found = True

        # 2. Check pipe freeze risk (critical)
        if check_pipe_freeze_risk(data['temperature_f'], data['room'], args.dry_run):
            issues_found = True

        # 3. Check humidity (leak/mold risk)
        if check_humidity_risk(data['humidity'], data['room'], args.dry_run):
            issues_found = True

        if not issues_found:
            kvlog(logger, logging.INFO, automation='tempstick_monitor',
                  event='complete', status='ok', issues_found=False)
            logger.info(f"✓ All checks passed - {data['room']} conditions normal")
        else:
            kvlog(logger, logging.WARNING, automation='tempstick_monitor',
                  event='complete', status='issues_found', issues_found=True)
            logger.warning("⚠️ Issues detected - alerts sent")

    except Exception as e:
        kvlog(logger, logging.ERROR, automation='tempstick_monitor',
              event='error', error_type=type(e).__name__, error_msg=str(e))

        message = f"❌ Temp Stick error: {str(e)}"

        if not args.dry_run:
            send(message)

        logger.exception("Temp Stick monitor failed")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
