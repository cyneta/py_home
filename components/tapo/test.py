#!/usr/bin/env python
"""
Quick test to verify Tapo plugs are working
"""

import sys
# No longer needed - using relative imports

from .client import TapoAPI

def test():
    print("Testing Tapo connection...\n")

    try:
        tapo = TapoAPI()
        print(f"✓ Config loaded")
        print(f"  Username: {tapo.username}")
        print(f"  Outlets configured: {len(tapo.outlets)}")
        print()

        print("Getting status of all plugs...\n")
        statuses = tapo.list_all_status()

        success = 0
        failed = 0

        for s in statuses:
            if 'error' in s:
                print(f"✗ {s['name']}: {s['error']}")
                failed += 1
            else:
                status = "ON" if s['on'] else "OFF"
                print(f"✓ {s['device_info']['alias']}: {status} ({s['device_info']['rssi']} dBm)")
                success += 1

        print()
        print(f"Results: {success} working, {failed} failed")

        if failed == 0:
            print("\n✓ All plugs working!")
            return True
        else:
            print(f"\n✗ {failed} plug(s) failed")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test()
    sys.exit(0 if success else 1)
