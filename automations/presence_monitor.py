#!/usr/bin/env python
"""
Presence Monitor Automation

**STATUS: DEPRECATED as of 2025-10-13**

This script is no longer used in the primary presence detection stack.
Replaced by:
1. WiFi DHCP Monitor (wifi_event_monitor.py) - Instant arrivals
2. iOS Geofencing (home-geofence.js) - Instant arrivals + departures

See docs/PRESENCE_DETECTION_DECISION.md for rationale.

Kept for:
- Manual testing
- Emergency backup
- Historical reference

---

Original Purpose:
Monitors network for device presence and triggers automations on arrival/departure.

Designed to run as cron job every 5 minutes:
    */5 * * * * cd /home/pi/py_home && python automations/presence_monitor.py

Usage:
    python automations/presence_monitor.py
"""

import os
import sys
import logging
import time
import subprocess
from datetime import datetime
from lib.logging_config import kvlog

logger = logging.getLogger(__name__)

# State file to track previous presence
STATE_FILE = os.path.join(os.path.dirname(__file__), '..', '.presence_state')
FAIL_COUNT_FILE = os.path.join(os.path.dirname(__file__), '..', '.presence_fail_count')

# Robustness: Require N consecutive ping failures before declaring "away"
# This prevents false "away" events from temporary network issues
REQUIRED_FAILURES = 3  # 3 failures = 6 minutes of no response


def get_previous_state():
    """
    Load previous presence state from file

    Returns:
        bool or None: True=home, False=away, None=unknown (first run)
    """
    if not os.path.exists(STATE_FILE):
        return None

    try:
        with open(STATE_FILE, 'r') as f:
            state = f.read().strip().lower()
            return state == 'home'
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='presence_monitor', action='read_state',
              error_type=type(e).__name__, error_msg=str(e))
        return None


def save_state(is_home):
    """
    Save current presence state to file

    Args:
        is_home (bool): True if home, False if away
    """
    try:
        with open(STATE_FILE, 'w') as f:
            f.write('home' if is_home else 'away')
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='presence_monitor', action='save_state',
              error_type=type(e).__name__, error_msg=str(e))


def get_fail_count():
    """Get consecutive ping failure count"""
    if not os.path.exists(FAIL_COUNT_FILE):
        return 0
    try:
        with open(FAIL_COUNT_FILE, 'r') as f:
            return int(f.read().strip())
    except:
        return 0


def increment_fail_count():
    """Increment consecutive failure count"""
    count = get_fail_count() + 1
    try:
        with open(FAIL_COUNT_FILE, 'w') as f:
            f.write(str(count))
    except:
        pass
    return count


def reset_fail_count():
    """Reset failure count (device responded)"""
    try:
        if os.path.exists(FAIL_COUNT_FILE):
            os.remove(FAIL_COUNT_FILE)
    except:
        pass


def check_presence():
    """
    Check if primary device is home

    Returns:
        bool: True if home, False if away
    """
    api_start = time.time()
    try:
        from lib.config import config
        from components.network import is_device_home

        # Get device config
        if 'presence' not in config or 'devices' not in config['presence']:
            kvlog(logger, logging.WARNING, automation='presence_monitor', action='check_presence',
                  error_type='ConfigError', error_msg='No presence.devices configured')
            return False

        devices = config['presence']['devices']

        # Check primary device (first in list or named 'primary')
        primary_device = None

        if 'primary' in devices:
            primary_device = devices['primary']
        else:
            # Use first device in list
            device_names = list(devices.keys())
            if device_names:
                primary_device = devices[device_names[0]]

        if not primary_device:
            kvlog(logger, logging.ERROR, automation='presence_monitor', action='check_presence',
                  error_type='ConfigError', error_msg='No primary device configured')
            return False

        # Get device IP address
        ip_address = primary_device.get('ip')

        if not ip_address:
            kvlog(logger, logging.ERROR, automation='presence_monitor', action='check_presence',
                  error_type='ConfigError', error_msg='Device has no IP configured')
            return False

        # Check if device is home
        is_home = is_device_home(ip_address)
        duration_ms = int((time.time() - api_start) * 1000)

        device_name = primary_device.get('name', 'Device')
        kvlog(logger, logging.INFO, automation='presence_monitor', action='check_presence',
              device=device_name, ip=ip_address, status='home' if is_home else 'away',
              result='ok', duration_ms=duration_ms)

        return is_home

    except Exception as e:
        duration_ms = int((time.time() - api_start) * 1000)
        kvlog(logger, logging.ERROR, automation='presence_monitor', action='check_presence',
              error_type=type(e).__name__, error_msg=str(e), duration_ms=duration_ms)
        return False


def trigger_automation(script_name):
    """
    Run an automation script

    Args:
        script_name (str): Name of script (e.g., 'leaving_home.py')
    """
    script_path = os.path.join(os.path.dirname(__file__), script_name)

    if not os.path.exists(script_path):
        kvlog(logger, logging.ERROR, automation='presence_monitor', action='trigger_automation',
              script=script_name, error_type='FileNotFound', error_msg=f'Script not found: {script_path}')
        return False

    api_start = time.time()
    try:
        kvlog(logger, logging.INFO, automation='presence_monitor', action='trigger_automation',
              script=script_name, status='starting')

        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=60
        )

        duration_ms = int((time.time() - api_start) * 1000)

        if result.returncode == 0:
            kvlog(logger, logging.NOTICE, automation='presence_monitor', action='trigger_automation',
                  script=script_name, result='ok', duration_ms=duration_ms)
            return True
        else:
            kvlog(logger, logging.ERROR, automation='presence_monitor', action='trigger_automation',
                  script=script_name, error_type='ScriptFailed', error_msg=result.stderr,
                  duration_ms=duration_ms)
            return False

    except subprocess.TimeoutExpired:
        duration_ms = int((time.time() - api_start) * 1000)
        kvlog(logger, logging.ERROR, automation='presence_monitor', action='trigger_automation',
              script=script_name, error_type='TimeoutExpired', error_msg='Script timed out',
              duration_ms=duration_ms)
        return False
    except Exception as e:
        duration_ms = int((time.time() - api_start) * 1000)
        kvlog(logger, logging.ERROR, automation='presence_monitor', action='trigger_automation',
              script=script_name, error_type=type(e).__name__, error_msg=str(e),
              duration_ms=duration_ms)
        return False


def run():
    """Execute presence monitoring with robustness (if in doubt, don't change state)"""
    start_time = time.time()
    timestamp = datetime.now().isoformat()
    kvlog(logger, logging.NOTICE, automation='presence_monitor', event='start', timestamp=timestamp)

    # Check current presence
    ping_success = check_presence()

    # Get previous state
    was_home = get_previous_state()
    fail_count = get_fail_count()

    # Log state
    if was_home is None:
        # First run - initialize
        kvlog(logger, logging.INFO, automation='presence_monitor', action='initialize',
              state='home' if ping_success else 'away')
        save_state(ping_success)
        if not ping_success:
            reset_fail_count()  # Start fresh

        total_duration_ms = int((time.time() - start_time) * 1000)
        kvlog(logger, logging.NOTICE, automation='presence_monitor', event='complete',
              duration_ms=total_duration_ms)

        return {
            'timestamp': timestamp,
            'action': 'initialize',
            'state': 'home' if ping_success else 'away'
        }

    # ROBUSTNESS LOGIC: Only declare "away" after multiple consecutive failures
    if ping_success:
        # Device responded - definitely home
        reset_fail_count()

        if not was_home:
            # ARRIVED HOME (transitioning from away → home)
            kvlog(logger, logging.NOTICE, automation='presence_monitor', action='state_change',
                  change='arrived', prev_state='away', new_state='home')

            # Trigger im_home automation (it will send notification with actions)
            trigger_automation('im_home.py')

            # Save new state
            save_state(True)

            total_duration_ms = int((time.time() - start_time) * 1000)
            kvlog(logger, logging.NOTICE, automation='presence_monitor', event='complete',
                  duration_ms=total_duration_ms)

            return {
                'timestamp': timestamp,
                'action': 'arrived',
                'state': 'home',
                'automation': 'im_home.py'
            }
        else:
            # Still home, no change
            kvlog(logger, logging.INFO, automation='presence_monitor', action='no_change',
                  state='home')

            # Update file timestamp to show we're still monitoring
            save_state(True)

            total_duration_ms = int((time.time() - start_time) * 1000)
            kvlog(logger, logging.NOTICE, automation='presence_monitor', event='complete',
                  duration_ms=total_duration_ms)

            return {
                'timestamp': timestamp,
                'action': 'no_change',
                'state': 'home'
            }

    else:
        # Ping failed - might be away, or might be temporary network issue
        new_fail_count = increment_fail_count()

        if was_home:
            # Currently marked as home, but ping failing
            if new_fail_count >= REQUIRED_FAILURES:
                # Multiple consecutive failures - now confident device left
                kvlog(logger, logging.NOTICE, automation='presence_monitor', action='state_change',
                      change='departed', prev_state='home', new_state='away',
                      fail_count=new_fail_count, required=REQUIRED_FAILURES)

                # Trigger leaving_home automation
                trigger_automation('leaving_home.py')

                # Save new state
                save_state(False)

                total_duration_ms = int((time.time() - start_time) * 1000)
                kvlog(logger, logging.NOTICE, automation='presence_monitor', event='complete',
                      duration_ms=total_duration_ms)

                return {
                    'timestamp': timestamp,
                    'action': 'departed',
                    'state': 'away',
                    'automation': 'leaving_home.py',
                    'fail_count': new_fail_count
                }
            else:
                # Not enough failures yet - assume still home (if in doubt, don't change)
                kvlog(logger, logging.WARNING, automation='presence_monitor', action='ping_failed',
                      state='home', fail_count=new_fail_count, required=REQUIRED_FAILURES,
                      message='Assuming still home until more failures')

                total_duration_ms = int((time.time() - start_time) * 1000)
                kvlog(logger, logging.NOTICE, automation='presence_monitor', event='complete',
                      duration_ms=total_duration_ms)

                return {
                    'timestamp': timestamp,
                    'action': 'no_change',
                    'state': 'home',
                    'fail_count': new_fail_count,
                    'message': 'Ping failed but assuming still home'
                }
        else:
            # Already marked as away, ping still failing
            kvlog(logger, logging.INFO, automation='presence_monitor', action='no_change',
                  state='away', fail_count=new_fail_count)

            # Update file timestamp to show we're still monitoring
            save_state(False)

            total_duration_ms = int((time.time() - start_time) * 1000)
            kvlog(logger, logging.NOTICE, automation='presence_monitor', event='complete',
                  duration_ms=total_duration_ms)

            return {
                'timestamp': timestamp,
                'action': 'no_change',
                'state': 'away',
                'fail_count': new_fail_count
            }


if __name__ == '__main__':
    # Set up logging
    from lib.logging_config import setup_logging
    import os
    log_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'logs', 'presence_monitor.log')
    setup_logging(log_level='INFO', log_file=log_file)

    result = run()
