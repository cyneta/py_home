#!/usr/bin/env python
"""
Quick test to verify Nest thermostat is working
"""

import sys

from .client import NestAPI, get_status

def test():
    print("Testing Nest connection...\n")

    try:
        nest = NestAPI()
        print(f"✓ Config loaded")
        print(f"  Project ID: {nest.project_id[:30]}...")
        print(f"  Device ID: {nest.device_id[:40]}...")
        print()

        print("Getting thermostat status...\n")
        status = get_status()

        print(f"✓ Nest thermostat responding!")
        print(f"  Current: {status['current_temp_f']:.1f}°F")
        print(f"  Humidity: {status['current_humidity']}%")
        print(f"  Mode: {status['mode']}")

        if status['heat_setpoint_f']:
            print(f"  Heat Target: {status['heat_setpoint_f']:.1f}°F")
        if status['cool_setpoint_f']:
            print(f"  Cool Target: {status['cool_setpoint_f']:.1f}°F")

        print(f"  HVAC: {status['hvac_status']}")

        print("\n✓ Nest thermostat working!")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test()
    sys.exit(0 if success else 1)
