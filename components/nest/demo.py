#!/usr/bin/env python
"""
Google Nest Thermostat Demo - All Features

This demo shows everything you can do with the Nest thermostat.
"""

import sys
import time

from .client import (
    get_status, set_temperature, set_mode,
    set_away, set_comfort, NestAPI
)

def demo_1_status():
    """Demo 1: Get current thermostat status"""
    print("\n" + "="*60)
    print("DEMO 1: Get Thermostat Status")
    print("="*60)

    status = get_status()

    print(f"\nCurrent Status:")
    print(f"  Temperature: {status['current_temp_f']:.1f}°F")
    print(f"  Humidity: {status['current_humidity']}%")
    print(f"  Mode: {status['mode']}")

    if status['heat_setpoint_f']:
        print(f"  Heat Setpoint: {status['heat_setpoint_f']:.1f}°F")
    if status['cool_setpoint_f']:
        print(f"  Cool Setpoint: {status['cool_setpoint_f']:.1f}°F")

    print(f"  HVAC Status: {status['hvac_status']}")


def demo_2_heat_mode():
    """Demo 2: Set temperature in HEAT mode"""
    print("\n" + "="*60)
    print("DEMO 2: Set Temperature (HEAT Mode)")
    print("="*60)

    print("\nSetting to HEAT mode at 72°F...")
    set_temperature(72, mode='HEAT')

    time.sleep(2)

    status = get_status()
    print(f"  ✓ Mode: {status['mode']}")
    print(f"  ✓ Target: {status['heat_setpoint_f']:.1f}°F")
    print(f"  ✓ Current: {status['current_temp_f']:.1f}°F")


def demo_3_cool_mode():
    """Demo 3: Set temperature in COOL mode"""
    print("\n" + "="*60)
    print("DEMO 3: Set Temperature (COOL Mode)")
    print("="*60)

    print("\nSetting to COOL mode at 74°F...")
    set_temperature(74, mode='COOL')

    time.sleep(2)

    status = get_status()
    print(f"  ✓ Mode: {status['mode']}")
    print(f"  ✓ Target: {status['cool_setpoint_f']:.1f}°F")
    print(f"  ✓ Current: {status['current_temp_f']:.1f}°F")


def demo_4_mode_control():
    """Demo 4: Change thermostat mode"""
    print("\n" + "="*60)
    print("DEMO 4: Mode Control")
    print("="*60)

    print("\nAvailable modes: HEAT, COOL, HEATCOOL, OFF")

    print("\nSetting to OFF...")
    set_mode('OFF')
    time.sleep(1)

    status = get_status()
    print(f"  ✓ Mode: {status['mode']}")

    print("\nSetting back to HEAT...")
    set_mode('HEAT')
    time.sleep(1)

    status = get_status()
    print(f"  ✓ Mode: {status['mode']}")


def demo_5_presets():
    """Demo 5: Away and Comfort presets"""
    print("\n" + "="*60)
    print("DEMO 5: Temperature Presets")
    print("="*60)

    print("\nSetting AWAY mode (62°F)...")
    set_away(62)

    time.sleep(2)

    status = get_status()
    print(f"  ✓ Temperature: {status['heat_setpoint_f']:.1f}°F")
    print(f"  ✓ Mode: {status['mode']}")

    print("\nSetting COMFORT mode (72°F)...")
    set_comfort(72)

    time.sleep(2)

    status = get_status()
    print(f"  ✓ Temperature: {status['heat_setpoint_f']:.1f}°F")
    print(f"  ✓ Mode: {status['mode']}")


def main():
    print("\n" + "="*60)
    print("GOOGLE NEST THERMOSTAT DEMO")
    print("="*60)
    print("\nThis demo shows all Nest thermostat capabilities.")
    print("\nAvailable demos:")
    print("  1. Get current status")
    print("  2. Set temperature (HEAT mode)")
    print("  3. Set temperature (COOL mode)")
    print("  4. Change thermostat mode")
    print("  5. Away/Comfort presets")
    print("  all. Run all demos")
    print()

    choice = input("Enter demo number (1-5) or 'all': ").strip()

    if choice == '1':
        demo_1_status()
    elif choice == '2':
        demo_2_heat_mode()
    elif choice == '3':
        demo_3_cool_mode()
    elif choice == '4':
        demo_4_mode_control()
    elif choice == '5':
        demo_5_presets()
    elif choice.lower() == 'all':
        demo_1_status()
        input("\nPress ENTER to continue to next demo...")
        demo_2_heat_mode()
        input("\nPress ENTER to continue to next demo...")
        demo_3_cool_mode()
        input("\nPress ENTER to continue to next demo...")
        demo_4_mode_control()
        input("\nPress ENTER to continue to next demo...")
        demo_5_presets()
    else:
        print("Invalid choice")
        return

    print("\n" + "="*60)
    print("Demo complete!")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
