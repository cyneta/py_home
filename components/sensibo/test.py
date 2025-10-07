#!/usr/bin/env python
"""
Quick test to verify Sensibo AC is working
"""

import sys

from .client import SensiboAPI, get_status

def test():
    print("Testing Sensibo connection...\n")

    try:
        sensibo = SensiboAPI()
        print(f"✓ Config loaded")
        print(f"  API Key: {sensibo.api_key[:10]}...")
        print(f"  Device ID: {sensibo.device_id}")
        print()

        print("Getting AC status...\n")
        status = get_status()

        print(f"✓ Sensibo AC responding!")
        print(f"  Room: {status['room']}")
        print(f"  Power: {'ON' if status['on'] else 'OFF'}")
        print(f"  Mode: {status['mode']}")
        print(f"  Target: {status['target_temp_f']}°F")
        print(f"  Current: {status['current_temp_f']}°F")
        print(f"  Humidity: {status['current_humidity']}%")

        print("\n✓ Sensibo AC working!")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test()
    sys.exit(0 if success else 1)
