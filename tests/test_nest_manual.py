"""
Manual test for Nest API

Run this after setting up credentials in config/.env
See docs/NEST_API_SETUP.md for setup instructions

Usage:
    python tests/test_nest_manual.py
"""

import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_nest_connection():
    """Test basic Nest API connection"""
    print("\n=== Testing Nest API Connection ===\n")

    try:
        from utils.nest_api import get_nest

        print("1. Creating Nest API client...")
        nest = get_nest()
        print("   ✓ Client created")

        print("\n2. Getting thermostat status...")
        status = nest.get_status()

        print(f"\n   Current Status:")
        print(f"   - Temperature: {status['current_temp_f']}°F")
        print(f"   - Humidity: {status['current_humidity']}%")
        print(f"   - Mode: {status['mode']}")
        print(f"   - Heat Setpoint: {status['heat_setpoint_f']}°F")
        print(f"   - Cool Setpoint: {status['cool_setpoint_f']}°F")
        print(f"   - HVAC Status: {status['hvac_status']}")

        print("\n✓ Nest API working!\n")
        return True

    except ValueError as e:
        print(f"\n✗ Configuration Error: {e}")
        print("\nPlease:")
        print("1. Check config/.env has Nest credentials")
        print("2. See docs/NEST_API_SETUP.md for setup instructions")
        return False

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_nest_control():
    """Test Nest control (optional - will change thermostat!)"""
    print("\n=== Testing Nest Control (OPTIONAL) ===\n")

    response = input("This will change your thermostat settings. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Skipped control test")
        return

    try:
        from utils.nest_api import get_nest

        nest = get_nest()

        # Get current status
        original = nest.get_status()
        print(f"\nOriginal temperature: {original['heat_setpoint_f']}°F")

        # Test: Set temperature to 71°F
        print("\nSetting temperature to 71°F...")
        nest.set_temperature(71, mode='HEAT')
        print("   ✓ Command sent")

        # Wait a moment and verify
        import time
        time.sleep(3)

        new_status = nest.get_status()
        print(f"\nNew setpoint: {new_status['heat_setpoint_f']}°F")

        # Restore original
        print(f"\nRestoring original temperature ({original['heat_setpoint_f']}°F)...")
        nest.set_temperature(original['heat_setpoint_f'], mode='HEAT')
        print("   ✓ Restored")

        print("\n✓ Nest control working!\n")
        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Test connection first
    if test_nest_connection():
        # Optionally test control
        test_nest_control()
