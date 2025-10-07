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
import subprocess
from datetime import datetime

logging.basicConfig(level=logging.INFO)
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
        logger.error(f"Failed to read state file: {e}")
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
        logger.error(f"Failed to save state: {e}")


def check_presence():
    """
    Check if primary device is home

    Returns:
        bool: True if home, False if away
    """
    try:
        from lib.config import config
        from components.network import is_device_home

        # Get device config
        if 'presence' not in config or 'devices' not in config['presence']:
            logger.warning("No presence.devices configured in config.yaml")
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
            logger.error("No primary device configured")
            return False

        # Get device identifier (prefer MAC over IP)
        identifier = primary_device.get('mac') or primary_device.get('ip')
        method = primary_device.get('method', 'auto')

        if not identifier:
            logger.error("Device has no IP or MAC configured")
            return False

        # Check if device is home
        is_home = is_device_home(identifier, method=method)

        device_name = primary_device.get('name', 'Device')
        logger.info(f"{device_name} ({identifier}): {'HOME' if is_home else 'AWAY'}")

        return is_home

    except Exception as e:
        logger.error(f"Failed to check presence: {e}")
        return False


def trigger_automation(script_name):
    """
    Run an automation script

    Args:
        script_name (str): Name of script (e.g., 'leaving_home.py')
    """
    script_path = os.path.join(os.path.dirname(__file__), script_name)

    if not os.path.exists(script_path):
        logger.error(f"Script not found: {script_path}")
        return False

    try:
        logger.info(f"Triggering automation: {script_name}")

        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            logger.info(f"✓ {script_name} completed successfully")
            return True
        else:
            logger.error(f"✗ {script_name} failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error(f"✗ {script_name} timed out")
        return False
    except Exception as e:
        logger.error(f"✗ Failed to run {script_name}: {e}")
        return False


def run():
    """Execute presence monitoring"""
    timestamp = datetime.now().isoformat()
    logger.info(f"Presence monitor triggered at {timestamp}")

    # Check current presence
    currently_home = check_presence()

    # Get previous state
    was_home = get_previous_state()

    # Log state
    if was_home is None:
        logger.info("First run - initializing state")
        save_state(currently_home)
        return {
            'timestamp': timestamp,
            'action': 'initialize',
            'state': 'home' if currently_home else 'away'
        }

    # Detect state CHANGE
    if currently_home and not was_home:
        # ARRIVED HOME
        logger.info("🟢 DETECTED: Arrived home")

        # Trigger im_home automation
        trigger_automation('im_home.py')

        # Save new state
        save_state(True)

        # Send notification
        try:
            from lib.notifications import send_low
            send_low("Welcome home! (detected via WiFi)", title="🏡 Arrived Home")
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")

        return {
            'timestamp': timestamp,
            'action': 'arrived',
            'state': 'home',
            'automation': 'im_home.py'
        }

    elif not currently_home and was_home:
        # LEFT HOME
        logger.info("🔴 DETECTED: Left home")

        # Trigger leaving_home automation
        trigger_automation('leaving_home.py')

        # Save new state
        save_state(False)

        # Send notification
        try:
            from lib.notifications import send_low
            send_low("House set to away mode (detected via WiFi)", title="🚗 Left Home")
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")

        return {
            'timestamp': timestamp,
            'action': 'departed',
            'state': 'away',
            'automation': 'leaving_home.py'
        }

    else:
        # NO CHANGE
        state_name = 'home' if currently_home else 'away'
        logger.info(f"No change - still {state_name}")

        return {
            'timestamp': timestamp,
            'action': 'no_change',
            'state': state_name
        }


if __name__ == '__main__':
    result = run()

    # Print summary
    print(f"\nPresence Monitor Results:")
    print(f"  Action: {result['action']}")
    print(f"  State: {result['state']}")

    if 'automation' in result:
        print(f"  Automation: {result['automation']}")
