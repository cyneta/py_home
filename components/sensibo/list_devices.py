"""
List Sensibo devices and get device IDs

Run this after adding SENSIBO_API_KEY to config/.env

Get your API key at: https://home.sensibo.com/me/api
"""

import sys
sys.path.insert(0, '.')

from utils.sensibo_api import SensiboAPI

def main():
    print("\n=== Listing Sensibo Devices ===\n")

    try:
        # Create API client (will use key from config)
        sensibo = SensiboAPI()

        # List all devices
        devices = sensibo.list_devices()

        if not devices:
            print("No Sensibo devices found on your account")
            print("\nMake sure:")
            print("1. Your Sensibo device is set up in the Sensibo app")
            print("2. API key is correct in config/.env")
            return

        print(f"Found {len(devices)} device(s):\n")

        for i, device in enumerate(devices, 1):
            print(f"Device {i}:")
            print(f"  ID: {device['id']}")
            print(f"  Room: {device['room'].get('name', 'Unnamed')}")

            # Get detailed status
            try:
                status = sensibo.get_status(device['id'])
                print(f"  Status: {'ON' if status['on'] else 'OFF'}")
                if status['on']:
                    print(f"  Mode: {status['mode']}")
                    print(f"  Target: {status['target_temp_f']}°F")
                print(f"  Current: {status['current_temp_f']}°F, {status['current_humidity']}%")
            except Exception as e:
                print(f"  (Could not get status: {e})")

            print()
            print(f"Add to config/config.yaml:")
            print(f"  sensibo:")
            print(f"    bedroom_ac_id: \"{device['id']}\"")
            print()
            print("="*60)
            print()

    except ValueError as e:
        print(f"✗ Configuration Error: {e}")
        print("\nGet your API key at: https://home.sensibo.com/me/api")
        print("Then add to config/.env:")
        print("  SENSIBO_API_KEY=your_key_here")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
