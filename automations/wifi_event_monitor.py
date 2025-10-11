#!/usr/bin/env python
"""
WiFi Event Monitor - Instant Home Detection

Monitors system logs for WiFi connection events to trigger instant home arrival.
Much faster than cron-based polling (sub-5 second vs 2-minute response time).

How it works:
1. Monitors system journal for DHCP lease events
2. When configured device IP appears, triggers im_home automation
3. Tracks state to avoid duplicate triggers

Usage:
    python automations/wifi_event_monitor.py

Systemd Service:
    sudo systemctl start py_home_wifi_monitor
    sudo systemctl enable py_home_wifi_monitor
"""

import subprocess
import logging
import time
import os
from pathlib import Path
from lib.logging_config import kvlog

logger = logging.getLogger(__name__)

# State file to track previous presence (same as presence_monitor)
STATE_FILE = Path(__file__).parent.parent / '.presence_state'


def get_previous_state():
    """Read previous presence state from file"""
    if not STATE_FILE.exists():
        return None

    try:
        with open(STATE_FILE, 'r') as f:
            state = f.read().strip().lower()
            return state == 'home'
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='wifi_event_monitor', action='read_state',
              error_type=type(e).__name__, error_msg=str(e))
        return None


def save_state(is_home):
    """Save current presence state to file"""
    try:
        with open(STATE_FILE, 'w') as f:
            f.write('home' if is_home else 'away')
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='wifi_event_monitor', action='save_state',
              error_type=type(e).__name__, error_msg=str(e))


def trigger_im_home():
    """Trigger im_home automation"""
    import sys
    script_path = Path(__file__).parent / 'im_home.py'

    try:
        kvlog(logger, logging.NOTICE, automation='wifi_event_monitor', action='trigger',
              script='im_home.py', status='starting')

        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            kvlog(logger, logging.NOTICE, automation='wifi_event_monitor', action='trigger',
                  script='im_home.py', result='ok')
            return True
        else:
            kvlog(logger, logging.ERROR, automation='wifi_event_monitor', action='trigger',
                  script='im_home.py', error_type='ScriptFailed', error_msg=result.stderr)
            return False

    except subprocess.TimeoutExpired:
        kvlog(logger, logging.ERROR, automation='wifi_event_monitor', action='trigger',
              script='im_home.py', error_type='TimeoutExpired', error_msg='Script timed out')
        return False
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='wifi_event_monitor', action='trigger',
              script='im_home.py', error_type=type(e).__name__, error_msg=str(e))
        return False


def monitor_wifi_events():
    """
    Monitor system journal for WiFi connection events

    Watches for DHCP lease assignments to configured device IP.
    Triggers im_home automation when device connects.
    """
    from lib.config import config

    # Get configured device IP
    if 'presence' not in config or 'devices' not in config['presence']:
        kvlog(logger, logging.ERROR, automation='wifi_event_monitor', action='start',
              error_type='ConfigError', error_msg='No presence.devices configured')
        return

    primary_device = config['presence']['devices'].get('primary')
    if not primary_device:
        kvlog(logger, logging.ERROR, automation='wifi_event_monitor', action='start',
              error_type='ConfigError', error_msg='No primary device configured')
        return

    device_ip = primary_device.get('ip')
    if not device_ip:
        kvlog(logger, logging.ERROR, automation='wifi_event_monitor', action='start',
              error_type='ConfigError', error_msg='Primary device has no IP configured')
        return

    device_name = primary_device.get('name', 'Device')

    kvlog(logger, logging.NOTICE, automation='wifi_event_monitor', event='start',
          device=device_name, ip=device_ip)

    # Monitor journalctl for DHCP events
    # Using journalctl -f (follow) to get real-time log stream
    cmd = [
        'journalctl',
        '-f',  # Follow mode
        '-u', 'dnsmasq',  # DHCP service (dnsmasq on most routers/Pi)
        '--since', 'now',  # Only new events
        '--no-pager'
    ]

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )

        kvlog(logger, logging.INFO, automation='wifi_event_monitor', action='monitoring',
              device=device_name, ip=device_ip, status='started')

        # Read log lines in real-time
        for line in process.stdout:
            # Look for DHCP lease lines containing our device IP
            # Example: "DHCPACK(br0) 192.168.50.189 aa:bb:cc:dd:ee:ff Matt's-iPhone"
            if device_ip in line and ('DHCPACK' in line or 'DHCPOFFER' in line):
                kvlog(logger, logging.INFO, automation='wifi_event_monitor', event='dhcp_detected',
                      device=device_name, ip=device_ip, log_line=line.strip())

                # Check if this is a new arrival (state changed from away to home)
                was_home = get_previous_state()

                if was_home is False or was_home is None:
                    # Device just arrived home!
                    kvlog(logger, logging.NOTICE, automation='wifi_event_monitor', event='arrival_detected',
                          device=device_name, ip=device_ip, prev_state='away' if was_home is False else 'unknown')

                    # Update state BEFORE triggering automation (prevent duplicates)
                    save_state(True)

                    # Trigger im_home automation
                    trigger_im_home()

                    # Add cooldown to prevent rapid re-triggers
                    time.sleep(30)

                else:
                    # Already home, just a DHCP renewal
                    kvlog(logger, logging.DEBUG, automation='wifi_event_monitor', event='dhcp_renewal',
                          device=device_name, ip=device_ip, status='already_home')

    except KeyboardInterrupt:
        kvlog(logger, logging.NOTICE, automation='wifi_event_monitor', event='stop',
              reason='KeyboardInterrupt')
        if process:
            process.terminate()

    except Exception as e:
        kvlog(logger, logging.ERROR, automation='wifi_event_monitor', action='monitor',
              error_type=type(e).__name__, error_msg=str(e))
        if process:
            process.terminate()


if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',  # kvlog handles formatting
        handlers=[
            logging.FileHandler('/home/matt.wheeler/py_home/data/logs/wifi_event_monitor.log'),
            logging.StreamHandler()
        ]
    )

    kvlog(logger, logging.NOTICE, automation='wifi_event_monitor', event='startup')

    try:
        monitor_wifi_events()
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='wifi_event_monitor', event='fatal_error',
              error_type=type(e).__name__, error_msg=str(e))
        raise
