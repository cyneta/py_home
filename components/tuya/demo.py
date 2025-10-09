#!/usr/bin/env python
"""
Tuya API Demo Script

Quick test/demo for Alen air purifier control via Tuya Cloud API.

Usage:
    python components/tuya/demo.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from components.tuya import get_tuya, get_air_quality, set_power, get_status
from lib.logging_config import setup_logging
import logging

# Setup logging
setup_logging('INFO')
logger = logging.getLogger(__name__)


def main():
    print("=" * 70)
    print("Tuya API Demo - Alen Air Purifiers")
    print("=" * 70)
    print()

    try:
        # Initialize Tuya API
        print("Initializing Tuya API...")
        tuya = get_tuya()
        print(f"✓ Connected to Tuya Cloud (Region: us)")
        print()

        # Get all devices
        print("=" * 70)
        print("All Devices")
        print("=" * 70)
        devices = tuya.get_all_devices()
        for device in devices:
            print(f"- {device.name} (ID: {device.device_id})")
        print()

        # Get status of all devices
        print("=" * 70)
        print("Device Status")
        print("=" * 70)
        all_status = tuya.list_all_status()
        for status in all_status:
            if 'error' in status:
                print(f"✗ {status['name']}: ERROR - {status['error']}")
            else:
                print(f"✓ {status['name']}:")
                print(f"  Power: {'ON' if status['on'] else 'OFF'}")
                print(f"  PM2.5: {status['pm25']} μg/m³")
                print(f"  AQI: {status['aqi']} ({status['quality']})")
                print(f"  Fan Speed: {status['fan_speed']}")
                print(f"  Mode: {status['mode']}")
                print(f"  Filter Life: {status['filter_life']}%")
                print(f"  Online: {'Yes' if status['online'] else 'No'}")
            print()

        # Demo: Get air quality for first device
        if devices:
            device_name = list(tuya.devices_config.keys())[0]
            print("=" * 70)
            print(f"Air Quality - {device_name}")
            print("=" * 70)
            aq = get_air_quality(device_name)
            print(f"PM2.5: {aq['pm25']} μg/m³")
            print(f"AQI: {aq['aqi']}")
            print(f"Quality: {aq['quality']}")
            print()

        # Demo: Interactive control (optional)
        print("=" * 70)
        print("Interactive Control")
        print("=" * 70)
        print("Available commands:")
        print("  status <device_name>  - Get device status")
        print("  on <device_name>      - Turn device on")
        print("  off <device_name>     - Turn device off")
        print("  speed <device_name> <1-5> - Set fan speed")
        print("  air <device_name>     - Get air quality")
        print("  list                  - List all devices")
        print("  quit                  - Exit")
        print()

        while True:
            try:
                cmd = input("tuya> ").strip().lower()
                if not cmd:
                    continue

                parts = cmd.split()
                action = parts[0]

                if action == 'quit' or action == 'exit':
                    break

                elif action == 'list':
                    for dev_name in tuya.devices_config.keys():
                        print(f"- {dev_name}: {tuya.devices_config[dev_name]['name']}")

                elif action == 'status' and len(parts) >= 2:
                    device_name = parts[1]
                    status = get_status(device_name)
                    print(f"Power: {'ON' if status['on'] else 'OFF'}")
                    print(f"PM2.5: {status['pm25']} μg/m³ (AQI: {status['aqi']})")
                    print(f"Fan Speed: {status['fan_speed']}, Mode: {status['mode']}")
                    print(f"Filter Life: {status['filter_life']}%")

                elif action == 'on' and len(parts) >= 2:
                    device_name = parts[1]
                    set_power(device_name, on=True)
                    print(f"✓ Turned on: {device_name}")

                elif action == 'off' and len(parts) >= 2:
                    device_name = parts[1]
                    set_power(device_name, on=False)
                    print(f"✓ Turned off: {device_name}")

                elif action == 'speed' and len(parts) >= 3:
                    device_name = parts[1]
                    speed = int(parts[2])
                    tuya.set_fan_speed(device_name, speed)
                    print(f"✓ Set fan speed to {speed}: {device_name}")

                elif action == 'air' and len(parts) >= 2:
                    device_name = parts[1]
                    aq = get_air_quality(device_name)
                    print(f"PM2.5: {aq['pm25']} μg/m³")
                    print(f"AQI: {aq['aqi']} ({aq['quality']})")

                else:
                    print("Unknown command or missing arguments")

            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")

    except Exception as e:
        print(f"✗ Error: {e}")
        logger.exception("Demo failed")
        return 1

    print()
    print("=" * 70)
    print("Demo completed")
    print("=" * 70)
    return 0


if __name__ == '__main__':
    sys.exit(main())
