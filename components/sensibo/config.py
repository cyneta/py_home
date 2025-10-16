#!/usr/bin/env python
"""
Sensibo Configuration Utility

Interactive setup for Sensibo mini-split AC integration.

This utility helps you:
1. Verify your Sensibo API key
2. Discover devices on your account
3. Test device control
4. Generate config.yaml entries

Usage:
    python -m components.sensibo.config
"""

import os
import sys
from pathlib import Path


def print_header(text):
    """Print section header"""
    print(f"\n{'='*70}")
    print(f"{text}")
    print(f"{'='*70}\n")


def check_api_key():
    """Check if API key is configured"""
    from lib.config import config

    if 'sensibo' not in config:
        print("❌ No 'sensibo' section in config.yaml")
        return None

    api_key = config['sensibo'].get('api_key')

    if not api_key:
        print("❌ No API key configured")
        print("\nTo get your API key:")
        print("1. Go to https://home.sensibo.com/me/api")
        print("2. Generate API key")
        print("3. Add to config/.env: SENSIBO_API_KEY=your_key")
        return None

    # Mask key for display
    masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    print(f"✓ API key configured: {masked}")

    return api_key


def discover_devices():
    """Discover Sensibo devices"""
    print("\nDiscovering Sensibo devices...")

    try:
        from components.sensibo.client import SensiboAPI

        sensibo = SensiboAPI()
        devices = sensibo.get_devices()

        if not devices:
            print("❌ No devices found on this account")
            return []

        print(f"\n✓ Found {len(devices)} device(s):\n")

        for i, device in enumerate(devices, 1):
            print(f"Device {i}:")
            print(f"  ID: {device['id']}")
            print(f"  Room: {device['room']['name']}")

            # Get current status
            status = sensibo.get_device_status(device['id'])
            temp_c = status['measurements']['temperature']
            temp_f = (temp_c * 9/5) + 32
            humidity = status['measurements']['humidity']

            print(f"  Temperature: {temp_f:.1f}°F ({temp_c:.1f}°C)")
            print(f"  Humidity: {humidity:.1f}%")

            ac_state = status['acState']
            print(f"  Power: {'ON' if ac_state['on'] else 'OFF'}")
            print(f"  Mode: {ac_state.get('mode', 'N/A')}")

            if ac_state['on'] and 'targetTemperature' in ac_state:
                target_c = ac_state['targetTemperature']
                target_f = (target_c * 9/5) + 32
                print(f"  Target: {target_f:.0f}°F ({target_c:.0f}°C)")

            print()

        return devices

    except Exception as e:
        print(f"\n❌ Failed to discover devices: {e}")
        print("\nTroubleshooting:")
        print("1. Check that API key is valid")
        print("2. Verify devices are online in Sensibo app")
        print("3. Check internet connection")
        return []


def test_device_control(device_id):
    """Test device control (read-only)"""
    print(f"\nTesting device control for {device_id}...")

    try:
        from components.sensibo.client import SensiboAPI

        sensibo = SensiboAPI()
        status = sensibo.get_device_status(device_id)

        ac_state = status['acState']
        current_power = ac_state['on']

        print(f"✓ Can read device state")
        print(f"  Current power: {'ON' if current_power else 'OFF'}")

        # Don't actually change anything, just verify API access
        print(f"✓ API access confirmed (no changes made)")

        return True

    except Exception as e:
        print(f"❌ Control test failed: {e}")
        return False


def generate_config_template(devices):
    """Generate config.yaml template based on discovered devices"""
    if not devices:
        print("\nNo devices to generate config for.")
        return

    print("\nConfig Template (add to config/config.yaml):")
    print("-" * 70)
    print("\nsensibo:")
    print("  api_key: ${SENSIBO_API_KEY}  # From config/.env")

    # Use first device as default
    device = devices[0]
    print(f"  device_id: \"{device['id']}\"")
    print(f"  room: \"{device['room']['name']}\"")

    if len(devices) > 1:
        print("\n  # Additional devices found:")
        for device in devices[1:]:
            print(f"  # - ID: {device['id']}")
            print(f"  #   Room: {device['room']['name']}")

    print("\n" + "-" * 70)


def check_config():
    """Check current config"""
    print("\nChecking config.yaml settings...")

    try:
        from lib.config import config

        if 'sensibo' not in config:
            print("❌ No 'sensibo' section in config.yaml")
            return False, None

        sensibo_config = config['sensibo']

        # Check required fields
        if 'device_id' not in sensibo_config:
            print("❌ No device_id in config")
            return False, None

        device_id = sensibo_config['device_id']
        room = sensibo_config.get('room', 'Unknown')

        print("✓ Config section exists")
        print(f"  Device ID: {device_id[:20]}...")
        print(f"  Room: {room}")

        return True, device_id

    except Exception as e:
        print(f"❌ Config error: {e}")
        return False, None


def main():
    """Run Sensibo configuration utility"""
    print_header("Sensibo AC Configuration Utility")

    print("This utility will help you set up your Sensibo mini-split AC integration.\n")

    # Step 1: Check API key
    print_header("Step 1: Check API Key")
    api_key = check_api_key()

    if not api_key:
        print("\nSetup instructions:")
        print("1. Get API key from https://home.sensibo.com/me/api")
        print("2. Add to config/.env: SENSIBO_API_KEY=your_key")
        print("3. Run this utility again")
        return 1

    # Step 2: Discover devices
    print_header("Step 2: Discover Devices")
    devices = discover_devices()

    # Step 3: Check config
    print_header("Step 3: Check Configuration")
    has_config, device_id = check_config()

    # Step 4: Test control (if configured)
    if has_config and device_id:
        print_header("Step 4: Test Device Control")
        control_ok = test_device_control(device_id)
    else:
        print_header("Step 4: Test Device Control")
        print("⊘ Skipped (not configured)")
        control_ok = False

    # Summary
    print_header("Summary")

    if control_ok:
        print("✅ Sensibo AC is fully configured and working!")
        print("\nYou can now use:")
        print("  - python -m components.sensibo.demo")
        print("  - python -m components.sensibo.test")
        print("  - Automation scripts (goodnight.py, etc.)")

    elif devices and not has_config:
        print("⚠️  Devices found but not configured in config.yaml")
        generate_config_template(devices)

        print("\nNext steps:")
        print("1. Copy the template above to config/config.yaml")
        print("2. Choose which device to use as primary")
        print("3. Run this utility again to test")

    elif has_config and not control_ok:
        print("⚠️  Configuration exists but control test failed")
        print("\nNext steps:")
        print("1. Verify device_id is correct")
        print("2. Check device is online in Sensibo app")
        print("3. Verify API key is valid")

    else:
        print("❌ Sensibo AC is not configured")
        print("\nNext steps:")
        print("1. Get API key from https://home.sensibo.com/me/api")
        print("2. Add to config/.env: SENSIBO_API_KEY=your_key")
        print("3. Run this utility again")

    print("\n" + "="*70 + "\n")

    return 0 if control_ok else 1


if __name__ == '__main__':
    sys.exit(main())
