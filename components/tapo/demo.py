#!/usr/bin/env python
"""
Tapo Smart Plug Demo - All Features

This demo shows everything you can do with Tapo P125M plugs.
"""

import sys
import time
# No longer needed - using relative imports

from .client import turn_on, turn_off, get_status, turn_on_all, turn_off_all, TapoAPI

def demo_1_status():
    """Demo 1: Get status of all plugs"""
    print("\n" + "="*60)
    print("DEMO 1: Get Status of All Plugs")
    print("="*60)

    tapo = TapoAPI()
    statuses = tapo.list_all_status()

    print(f"\nFound {len(statuses)} plugs:\n")

    for s in statuses:
        if 'error' not in s:
            status_icon = "✓ ON" if s['on'] else "○ OFF"
            print(f"{status_icon}  {s['device_info']['alias']}")
            print(f"        IP: {tapo.get_outlet_by_name(s['name'])['ip']}")
            print(f"        Signal: {s['device_info']['rssi']} dBm")
            print(f"        Firmware: {s['device_info']['firmware_version']}")
            print()

def demo_2_individual():
    """Demo 2: Control individual plug"""
    print("\n" + "="*60)
    print("DEMO 2: Control Individual Plug")
    print("="*60)

    plug_name = "Livingroom Lamp"

    print(f"\nControlling: {plug_name}")
    print(f"  Turning OFF...")
    turn_off(plug_name)
    time.sleep(1)

    print(f"  Turning ON...")
    turn_on(plug_name)

    status = get_status(plug_name)
    print(f"  ✓ Status: {'ON' if status['on'] else 'OFF'}")

def demo_3_bulk():
    """Demo 3: Control all plugs"""
    print("\n" + "="*60)
    print("DEMO 3: Bulk Control")
    print("="*60)

    print("\nTurning OFF all plugs...")
    turn_off_all()
    print("  ✓ All OFF")

    time.sleep(2)

    print("\nTurning ON all plugs...")
    turn_on_all()
    print("  ✓ All ON")

def demo_4_by_ip():
    """Demo 4: Control by IP"""
    print("\n" + "="*60)
    print("DEMO 4: Control by IP Address")
    print("="*60)

    tapo = TapoAPI()
    from lib.config import config
    ip = config['tapo']['outlets'][0]['ip']  # Use first outlet as example

    print(f"\nControlling plug at {ip}...")
    status = tapo.get_status(ip=ip)
    print(f"  Current: {'ON' if status['on'] else 'OFF'}")

    if status['on']:
        tapo.turn_off(ip=ip)
        print(f"  ✓ Turned OFF")
    else:
        tapo.turn_on(ip=ip)
        print(f"  ✓ Turned ON")

def demo_5_details():
    """Demo 5: Get detailed device info"""
    print("\n" + "="*60)
    print("DEMO 5: Detailed Device Information")
    print("="*60)

    plug_name = "Heater"
    print(f"\nGetting detailed info for: {plug_name}\n")

    status = get_status(plug_name)

    print(f"Status:")
    print(f"  Power: {'ON' if status['on'] else 'OFF'}")
    print(f"\nDevice Info:")
    print(f"  Model: {status['device_info']['model']}")
    print(f"  Alias: {status['device_info']['alias']}")
    print(f"  Hardware: {status['device_info']['hardware_version']}")
    print(f"  Firmware: {status['device_info']['firmware_version']}")
    print(f"  MAC: {status['device_info']['mac']}")
    print(f"\nNetwork:")
    print(f"  RSSI: {status['device_info']['rssi']} dBm")

    if status['energy']:
        print(f"\nEnergy (if supported):")
        print(f"  Current Power: {status['energy']['current_power_w']}W")
        print(f"  Total: {status['energy']['total_wh']}Wh")

def main():
    print("\n" + "="*60)
    print("TAPO P125M SMART PLUG DEMO")
    print("="*60)
    print("\nThis demo shows all Tapo plug capabilities.")
    print("\nAvailable demos:")
    print("  1. Get status of all plugs")
    print("  2. Control individual plug by name")
    print("  3. Bulk control (all on/off)")
    print("  4. Control by IP address")
    print("  5. Get detailed device information")
    print("  all. Run all demos")
    print()

    choice = input("Enter demo number (1-5) or 'all': ").strip()

    if choice == '1':
        demo_1_status()
    elif choice == '2':
        demo_2_individual()
    elif choice == '3':
        demo_3_bulk()
    elif choice == '4':
        demo_4_by_ip()
    elif choice == '5':
        demo_5_details()
    elif choice.lower() == 'all':
        demo_1_status()
        input("\nPress ENTER to continue to next demo...")
        demo_2_individual()
        input("\nPress ENTER to continue to next demo...")
        demo_3_bulk()
        input("\nPress ENTER to continue to next demo...")
        demo_4_by_ip()
        input("\nPress ENTER to continue to next demo...")
        demo_5_details()
    else:
        print("Invalid choice")
        return

    print("\n" + "="*60)
    print("Demo complete!")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
