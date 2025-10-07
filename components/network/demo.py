#!/usr/bin/env python
"""
Network Presence Detection Demo

Interactive demo to test network presence detection.

Usage:
    python components/network/demo.py
"""

import sys
import time
from presence import is_device_home, scan_network, get_device_info


def print_header(text):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"{text}")
    print(f"{'='*60}\n")


def demo_scan_network():
    """Demo: Scan entire network"""
    print_header("Network Scan - Find All Devices")

    print("Scanning network for active devices...")
    print("(This may take 10-30 seconds)\n")

    devices = scan_network()

    if not devices:
        print("No devices found (or arp-scan not available)")
        print("\nTo install arp-scan:")
        print("  Linux: sudo apt install arp-scan")
        print("  Mac: brew install arp-scan")
        return

    print(f"Found {len(devices)} devices:\n")
    print(f"{'IP Address':<20} {'MAC Address':<20} {'Vendor':<30}")
    print("-" * 70)

    for device in devices:
        print(f"{device['ip']:<20} {device['mac']:<20} {device.get('vendor', ''):<30}")

    print("\n💡 Tip: Find your iPhone in the list above")
    print("   Settings → WiFi → (i) → to see its IP")
    print("   Settings → General → About → WiFi Address to see MAC")


def demo_ping_detection():
    """Demo: Ping-based detection"""
    print_header("Ping Detection")

    ip = input("Enter device IP address to check (e.g., 192.168.1.50): ").strip()

    if not ip:
        print("Skipped")
        return

    print(f"\nPinging {ip}...")

    is_online = is_device_home(ip, method='ping')

    if is_online:
        print(f"✅ Device {ip} is ONLINE (responds to ping)")
    else:
        print(f"❌ Device {ip} is OFFLINE (no ping response)")
        print("\nNote: Some devices ignore pings to save battery")
        print("      Try ARP detection instead")


def demo_arp_detection():
    """Demo: ARP-based detection"""
    print_header("ARP Detection")

    mac = input("Enter device MAC address (e.g., AA:BB:CC:DD:EE:FF): ").strip()

    if not mac:
        print("Skipped")
        return

    print(f"\nChecking ARP table for {mac}...")

    is_online = is_device_home(mac, method='arp')

    if is_online:
        print(f"✅ Device {mac} is ONLINE (found in ARP table)")
    else:
        print(f"❌ Device {mac} is OFFLINE (not in ARP table)")
        print("\nNote: Make sure device is connected to WiFi")


def demo_device_info():
    """Demo: Get device info"""
    print_header("Device Information Lookup")

    identifier = input("Enter IP or MAC address: ").strip()

    if not identifier:
        print("Skipped")
        return

    print(f"\nLooking up device info for {identifier}...")

    info = get_device_info(identifier)

    if info['online']:
        print(f"\n✅ Device is ONLINE")
        print(f"   IP: {info.get('ip', 'Unknown')}")
        print(f"   MAC: {info.get('mac', 'Unknown')}")
        print(f"   Vendor: {info.get('vendor', 'Unknown')}")
    else:
        print(f"\n❌ Device is OFFLINE")


def demo_continuous_monitoring():
    """Demo: Continuous presence monitoring"""
    print_header("Continuous Monitoring")

    identifier = input("Enter IP or MAC to monitor (blank to skip): ").strip()

    if not identifier:
        print("Skipped")
        return

    print(f"\nMonitoring {identifier} every 10 seconds...")
    print("Press Ctrl+C to stop\n")

    previous_state = None

    try:
        while True:
            is_online = is_device_home(identifier, method='auto')

            timestamp = time.strftime("%H:%M:%S")

            # Detect state change
            if previous_state is None:
                print(f"[{timestamp}] Initial state: {'ONLINE' if is_online else 'OFFLINE'}")
            elif is_online and not previous_state:
                print(f"[{timestamp}] 🟢 Device ARRIVED (went online)")
            elif not is_online and previous_state:
                print(f"[{timestamp}] 🔴 Device DEPARTED (went offline)")
            else:
                print(f"[{timestamp}] {'🟢 Online' if is_online else '⚪ Offline'}")

            previous_state = is_online
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped")


def main():
    """Run all demos"""
    print("\n" + "="*60)
    print(" "*15 + "Network Presence Detection Demo")
    print("="*60)

    while True:
        print("\nWhat would you like to test?")
        print("1. Scan entire network (find all devices)")
        print("2. Ping detection (by IP)")
        print("3. ARP detection (by MAC)")
        print("4. Device info lookup")
        print("5. Continuous monitoring")
        print("6. Exit")

        choice = input("\nChoice (1-6): ").strip()

        if choice == '1':
            demo_scan_network()
        elif choice == '2':
            demo_ping_detection()
        elif choice == '3':
            demo_arp_detection()
        elif choice == '4':
            demo_device_info()
        elif choice == '5':
            demo_continuous_monitoring()
        elif choice == '6':
            print("\nExiting...")
            break
        else:
            print("Invalid choice")

    print("\n" + "="*60)
    print("Demo complete!")
    print("\nNext steps:")
    print("1. Find your iPhone's IP/MAC from network scan")
    print("2. Add to config/config.yaml under 'presence' section")
    print("3. Use in automations: is_device_home('192.168.1.50')")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
