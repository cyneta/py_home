#!/usr/bin/env python
"""
Sensibo Mini-Split AC Demo - All Features

This demo shows everything you can do with Sensibo-controlled AC units.
"""

import sys
import time

from .client import (
    get_status, turn_on, turn_off,
    set_temperature, SensiboAPI
)

def demo_1_status():
    """Demo 1: Get current AC status"""
    print("\n" + "="*60)
    print("DEMO 1: Get AC Status")
    print("="*60)

    status = get_status()

    print(f"\nCurrent Status:")
    print(f"  Room: {status['room']}")
    print(f"  Power: {'ON' if status['on'] else 'OFF'}")
    print(f"  Mode: {status['mode']}")
    print(f"  Target: {status['target_temp_f']}°F ({status['target_temp_c']}°C)")
    print(f"  Current: {status['current_temp_f']}°F")
    print(f"  Humidity: {status['current_humidity']}%")
    print(f"  Fan: {status['fan_level']}")
    print(f"  Swing: {status['swing']}")


def demo_2_turn_on():
    """Demo 2: Turn on AC"""
    print("\n" + "="*60)
    print("DEMO 2: Turn On AC")
    print("="*60)

    print("\nTurning ON in COOL mode at 72°F...")
    turn_on(mode='cool', temp_f=72)

    time.sleep(2)

    status = get_status()
    print(f"  ✓ Power: {'ON' if status['on'] else 'OFF'}")
    print(f"  ✓ Mode: {status['mode']}")
    print(f"  ✓ Target: {status['target_temp_f']}°F")


def demo_3_temperature():
    """Demo 3: Adjust temperature"""
    print("\n" + "="*60)
    print("DEMO 3: Adjust Temperature")
    print("="*60)

    print("\nSetting temperature to 70°F...")
    set_temperature(70)

    time.sleep(2)

    status = get_status()
    print(f"  ✓ Target: {status['target_temp_f']}°F")
    print(f"  ✓ Current: {status['current_temp_f']}°F")


def demo_4_modes():
    """Demo 4: Different AC modes"""
    print("\n" + "="*60)
    print("DEMO 4: AC Modes")
    print("="*60)

    print("\nAvailable modes: cool, heat, fan, dry, auto")

    print("\nSwitching to HEAT mode at 68°F...")
    turn_on(mode='heat', temp_f=68)
    time.sleep(2)

    status = get_status()
    print(f"  ✓ Mode: {status['mode']}")
    print(f"  ✓ Target: {status['target_temp_f']}°F")

    print("\nSwitching to FAN mode...")
    turn_on(mode='fan', temp_f=72)
    time.sleep(2)

    status = get_status()
    print(f"  ✓ Mode: {status['mode']}")


def demo_5_advanced():
    """Demo 5: Advanced control (fan, swing)"""
    print("\n" + "="*60)
    print("DEMO 5: Advanced Control")
    print("="*60)

    sensibo = SensiboAPI()

    print("\nSetting fan to HIGH...")
    sensibo.set_ac_state(fan_level='high')
    time.sleep(2)

    status = sensibo.get_status()
    print(f"  ✓ Fan level: {status['fan_level']}")

    print("\nTurning AC OFF...")
    turn_off()
    time.sleep(2)

    status = get_status()
    print(f"  ✓ Power: {'ON' if status['on'] else 'OFF'}")


def main():
    print("\n" + "="*60)
    print("SENSIBO MINI-SPLIT AC DEMO")
    print("="*60)
    print("\nThis demo shows all Sensibo AC capabilities.")
    print("\nAvailable demos:")
    print("  1. Get current AC status")
    print("  2. Turn on AC (cool mode)")
    print("  3. Adjust temperature")
    print("  4. Different AC modes (heat, fan, etc.)")
    print("  5. Advanced control (fan level, swing)")
    print("  all. Run all demos")
    print()

    choice = input("Enter demo number (1-5) or 'all': ").strip()

    if choice == '1':
        demo_1_status()
    elif choice == '2':
        demo_2_turn_on()
    elif choice == '3':
        demo_3_temperature()
    elif choice == '4':
        demo_4_modes()
    elif choice == '5':
        demo_5_advanced()
    elif choice.lower() == 'all':
        demo_1_status()
        input("\nPress ENTER to continue to next demo...")
        demo_2_turn_on()
        input("\nPress ENTER to continue to next demo...")
        demo_3_temperature()
        input("\nPress ENTER to continue to next demo...")
        demo_4_modes()
        input("\nPress ENTER to continue to next demo...")
        demo_5_advanced()
    else:
        print("Invalid choice")
        return

    print("\n" + "="*60)
    print("Demo complete!")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
