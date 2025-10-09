#!/usr/bin/env python
"""
Temp Stick Demo Script

Quick test/demo for Temp Stick sensor monitoring.

Usage:
    python services/tempstick_demo.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.tempstick import (
    get_tempstick,
    get_temperature,
    get_humidity,
    get_battery_level,
    is_online,
    get_summary,
    get_sensor_data
)
from lib.logging_config import setup_logging
import logging

# Setup logging
setup_logging('INFO')
logger = logging.getLogger(__name__)


def main():
    print("=" * 70)
    print("Temp Stick Demo")
    print("=" * 70)
    print()

    try:
        # Quick summary
        print("Quick Summary:")
        print(get_summary())
        print()

        # Individual readings
        print("=" * 70)
        print("Individual Readings")
        print("=" * 70)
        temp_f = get_temperature('F')
        temp_c = get_temperature('C')
        humidity = get_humidity()
        battery = get_battery_level()
        online = is_online()

        print(f"Temperature: {temp_f:.1f}°F ({temp_c:.1f}°C)")
        print(f"Humidity: {humidity:.1f}%")
        print(f"Battery: {battery}%")
        print(f"Status: {'✓ Online' if online else '✗ Offline'}")
        print()

        # Full sensor data
        print("=" * 70)
        print("Full Sensor Data")
        print("=" * 70)
        data = get_sensor_data()

        print(f"Sensor ID: {data['sensor_id']}")
        print(f"Sensor Name: {data['sensor_name']}")
        print(f"Temperature: {data['temperature_f']:.1f}°F ({data['temperature_c']:.1f}°C)")
        print(f"Humidity: {data['humidity']:.1f}%")
        print(f"Battery: {data['battery_pct']}% ({data['voltage']:.2f}V)")
        print(f"WiFi Network: {data['wifi_network']}")
        print(f"Signal Strength: {data['rssi']} dBm")
        print(f"Last Check-in: {data['last_checkin']}")
        print(f"Online: {'Yes' if data['is_online'] else 'No'}")
        print()

        # Automation examples
        print("=" * 70)
        print("Automation Examples")
        print("=" * 70)

        # Low temperature alert
        if temp_f < 50:
            print(f"⚠️  LOW TEMP ALERT: {temp_f:.1f}°F (potential pipe freeze risk)")
        else:
            print(f"✓ Temperature OK: {temp_f:.1f}°F")

        # High humidity alert
        if humidity > 70:
            print(f"⚠️  HIGH HUMIDITY: {humidity:.1f}% (mold risk)")
        else:
            print(f"✓ Humidity OK: {humidity:.1f}%")

        # Low battery warning
        if battery < 20:
            print(f"⚠️  LOW BATTERY: {battery}% (replace soon)")
        else:
            print(f"✓ Battery OK: {battery}%")

        # Offline warning
        if not online:
            print(f"⚠️  SENSOR OFFLINE: Last check-in at {data['last_checkin']}")
        else:
            print(f"✓ Sensor online")

        print()

        # Interactive mode
        print("=" * 70)
        print("Interactive Mode")
        print("=" * 70)
        print("Commands:")
        print("  temp - Show temperature")
        print("  humidity - Show humidity")
        print("  battery - Show battery level")
        print("  status - Show full status")
        print("  summary - Show summary")
        print("  quit - Exit")
        print()

        while True:
            try:
                cmd = input("tempstick> ").strip().lower()
                if not cmd:
                    continue

                if cmd in ['quit', 'exit', 'q']:
                    break

                elif cmd == 'temp':
                    temp = get_temperature()
                    print(f"Temperature: {temp:.1f}°F")

                elif cmd == 'humidity':
                    hum = get_humidity()
                    print(f"Humidity: {hum:.1f}%")

                elif cmd == 'battery':
                    bat = get_battery_level()
                    print(f"Battery: {bat}%")

                elif cmd == 'status':
                    data = get_sensor_data()
                    for key, value in data.items():
                        print(f"  {key}: {value}")

                elif cmd == 'summary':
                    print(get_summary())

                else:
                    print("Unknown command. Try: temp, humidity, battery, status, summary, quit")

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
