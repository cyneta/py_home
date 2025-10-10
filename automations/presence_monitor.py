#!/usr/bin/env python
"""
Presence Monitor Automation

Monitors network for device presence and triggers automations on arrival/departure.

Backup/complement to iOS location automations.

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

        # Get device identifier (prefer MAC over IP)
        identifier = primary_device.get('mac') or primary_device.get('ip')
        method = primary_device.get('method', 'auto')

        if not identifier:
            kvlog(logger, logging.ERROR, automation='presence_monitor', action='check_presence',
                  error_type='ConfigError', error_msg='Device has no IP or MAC configured')
            return False

        # Check if device is home
        is_home = is_device_home(identifier, method=method)
        duration_ms = int((time.time() - api_start) * 1000)

        device_name = primary_device.get('name', 'Device')
        kvlog(logger, logging.INFO, automation='presence_monitor', action='check_presence',
              device=device_name, identifier=identifier, status='home' if is_home else 'away',
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
    """Execute presence monitoring"""
    start_time = time.time()
    timestamp = datetime.now().isoformat()
    kvlog(logger, logging.NOTICE, automation='presence_monitor', event='start', timestamp=timestamp)

    # Check current presence
    currently_home = check_presence()

    # Get previous state
    was_home = get_previous_state()

    # Log state
    if was_home is None:
        kvlog(logger, logging.INFO, automation='presence_monitor', action='initialize',
              state='home' if currently_home else 'away')
        save_state(currently_home)

        total_duration_ms = int((time.time() - start_time) * 1000)
        kvlog(logger, logging.NOTICE, automation='presence_monitor', event='complete',
              duration_ms=total_duration_ms)

        return {
            'timestamp': timestamp,
            'action': 'initialize',
            'state': 'home' if currently_home else 'away'
        }

    # Detect state CHANGE
    if currently_home and not was_home:
        # ARRIVED HOME
        kvlog(logger, logging.NOTICE, automation='presence_monitor', action='state_change',
              change='arrived', prev_state='away', new_state='home')

        # Trigger im_home automation (it will send notification with actions)
        trigger_automation('im_home.py')

        # Save new state
        save_state(True)

        # Note: No notification here - im_home.py will send one with action summary

        total_duration_ms = int((time.time() - start_time) * 1000)
        kvlog(logger, logging.NOTICE, automation='presence_monitor', event='complete',
              duration_ms=total_duration_ms)

        return {
            'timestamp': timestamp,
            'action': 'arrived',
            'state': 'home',
            'automation': 'im_home.py'
        }

    elif not currently_home and was_home:
        # LEFT HOME
        kvlog(logger, logging.NOTICE, automation='presence_monitor', action='state_change',
              change='departed', prev_state='home', new_state='away')

        # Trigger leaving_home automation (it will send notification with actions)
        trigger_automation('leaving_home.py')

        # Save new state
        save_state(False)

        # Note: No notification here - leaving_home.py will send one with action summary

        total_duration_ms = int((time.time() - start_time) * 1000)
        kvlog(logger, logging.NOTICE, automation='presence_monitor', event='complete',
              duration_ms=total_duration_ms)

        return {
            'timestamp': timestamp,
            'action': 'departed',
            'state': 'away',
            'automation': 'leaving_home.py'
        }

    else:
        # NO CHANGE
        state_name = 'home' if currently_home else 'away'
        kvlog(logger, logging.INFO, automation='presence_monitor', action='no_change',
              state=state_name)

        total_duration_ms = int((time.time() - start_time) * 1000)
        kvlog(logger, logging.NOTICE, automation='presence_monitor', event='complete',
              duration_ms=total_duration_ms)

        return {
            'timestamp': timestamp,
            'action': 'no_change',
            'state': state_name
        }


if __name__ == '__main__':
    result = run()
