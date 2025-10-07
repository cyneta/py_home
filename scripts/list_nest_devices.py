"""
List Nest devices and get device IDs

Run this after setting NEST_REFRESH_TOKEN in config/.env
"""

import sys
sys.path.insert(0, '.')

from utils.nest_api import get_nest

def main():
    print("\n=== Listing Nest Devices ===\n")

    try:
        nest = get_nest()

        # Get device list
        devices = nest._get(f"{nest.project_id}/devices")

        print(f"Found {len(devices.get('devices', []))} device(s):\n")

        for device in devices.get('devices', []):
            print("="*60)
            print(f"Name: {device['name']}")
            print(f"Type: {device['type']}")

            # Parse traits
            traits = device.get('traits', {})

            # Device info
            if 'sdm.devices.traits.Info' in traits:
                info = traits['sdm.devices.traits.Info']
                print(f"Custom Name: {info.get('customName', 'N/A')}")

            # Current temperature
            if 'sdm.devices.traits.Temperature' in traits:
                temp_c = traits['sdm.devices.traits.Temperature'].get('ambientTemperatureCelsius')
                temp_f = (temp_c * 9/5) + 32 if temp_c else None
                print(f"Current Temp: {temp_f:.1f}°F ({temp_c}°C)")

            # Mode
            if 'sdm.devices.traits.ThermostatMode' in traits:
                mode = traits['sdm.devices.traits.ThermostatMode'].get('mode')
                print(f"Mode: {mode}")

            print("="*60)
            print()

            # Show device ID to copy
            print("Copy this device ID to config/config.yaml:")
            print(f"  device_id: \"{device['name']}\"")
            print()

    except ValueError as e:
        print(f"✗ Configuration Error: {e}")
        print("\nMake sure config/.env has:")
        print("- NEST_REFRESH_TOKEN=...")
        print("\nRun: python scripts/get_nest_token.py")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
