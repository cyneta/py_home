#!/usr/bin/env python
"""
Network Presence Detection Configuration Utility

Interactive setup for WiFi-based presence detection.

This utility helps you:
1. Discover your iPhone's IP and MAC address
2. Test ping and ARP detection methods
3. Recommend best detection method
4. Generate config.yaml entries

Usage:
    python -m components.network.config
"""

import sys
import subprocess
import platform
import re
import socket


def print_header(text):
    """Print section header"""
    print(f"\n{'='*70}")
    print(f"{text}")
    print(f"{'='*70}\n")


def get_network_info():
    """Get local network information"""
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    parts = local_ip.split('.')
    network = '.'.join(parts[:3])

    print(f"Your computer's IP: {local_ip}")
    print(f"Network range: {network}.x")

    return network, local_ip


def scan_network_devices():
    """Scan network for active devices"""
    print("\nScanning network for active devices...")
    print("(This may take 10-20 seconds)\n")

    try:
        # Run arp -a to see all devices
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=30)
        output = result.stdout

        devices = []

        for line in output.split('\n'):
            # Extract IP addresses
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
            if ip_match:
                ip = ip_match.group(1)

                # Try to get hostname
                try:
                    hostname = socket.gethostbyaddr(ip)[0]
                    devices.append((ip, hostname))
                except:
                    devices.append((ip, 'Unknown'))

        if devices:
            print(f"Found {len(devices)} active device(s):\n")
            for i, (ip, hostname) in enumerate(devices[:20], 1):  # Show first 20
                print(f"  {i}. {ip:15s} - {hostname}")

            if len(devices) > 20:
                print(f"\n  ... and {len(devices) - 20} more")

        return devices

    except Exception as e:
        print(f"❌ Network scan failed: {e}")
        return []


def test_detection_method(identifier, method):
    """Test a specific detection method"""
    try:
        from components.network import is_device_home

        result = is_device_home(identifier, method=method)
        return result

    except Exception as e:
        print(f"  Error: {e}")
        return None


def test_device_detection(ip, mac=None):
    """Test different detection methods for a device"""
    print(f"\nTesting detection methods for {ip}...")

    results = {}

    # Test ping
    print("\n  Testing ping method...")
    ping_result = test_detection_method(ip, 'ping')
    if ping_result is not None:
        results['ping'] = ping_result
        print(f"    Result: {'✓ DETECTED' if ping_result else '✗ Not detected'}")

    # Test ARP (if MAC provided)
    if mac:
        print("\n  Testing ARP method...")
        arp_result = test_detection_method(mac, 'arp')
        if arp_result is not None:
            results['arp'] = arp_result
            print(f"    Result: {'✓ DETECTED' if arp_result else '✗ Not detected'}")

    # Test auto
    print("\n  Testing auto method...")
    auto_result = test_detection_method(ip, 'auto')
    if auto_result is not None:
        results['auto'] = auto_result
        print(f"    Result: {'✓ DETECTED' if auto_result else '✗ Not detected'}")

    return results


def recommend_method(results):
    """Recommend best detection method based on test results"""
    print("\n  Recommendation:")

    if not results:
        print("    ⚠️  Could not test detection methods")
        return 'auto'

    # Count successes
    successes = sum(1 for v in results.values() if v)

    if successes == 0:
        print("    ⚠️  Device not detected by any method")
        print("       Make sure device is on the same network")
        return 'auto'

    # Prefer ping (fastest), then auto
    if results.get('ping'):
        print("    ✓ Use 'ping' method (fastest, most reliable)")
        return 'ping'
    elif results.get('arp'):
        print("    ✓ Use 'arp' method (more reliable than ping)")
        return 'arp'
    elif results.get('auto'):
        print("    ✓ Use 'auto' method (tries ping then ARP)")
        return 'auto'

    return 'auto'


def generate_config_template(device_name, ip, mac, method):
    """Generate config.yaml template"""
    print("\nConfig Template (add to config/config.yaml):")
    print("-" * 70)
    print("\npresence:")
    print("  devices:")
    print("    primary:")
    print(f"      name: \"{device_name}\"")
    print(f"      ip: \"{ip}\"")
    if mac:
        print(f"      mac: \"{mac}\"")
    print(f"      method: \"{method}\"  # ping, arp, or auto")
    print("\n    # Additional devices (optional):")
    print("    # secondary:")
    print("#       name: \"Another Device\"")
    print("#       ip: \"192.168.1.51\"")
    print("#       mac: \"AA:BB:CC:DD:EE:FF\"")
    print("#       method: \"auto\"")
    print("\n" + "-" * 70)


def check_config():
    """Check current presence configuration"""
    print("\nChecking config.yaml presence settings...")

    try:
        from lib.config import config

        if 'presence' not in config:
            print("❌ No 'presence' section in config.yaml")
            return False

        presence_config = config['presence']

        if 'devices' not in presence_config:
            print("❌ No 'devices' in presence config")
            return False

        devices = presence_config['devices']
        print(f"✓ Found {len(devices)} configured device(s):\n")

        for device_name, device_config in devices.items():
            print(f"  {device_config.get('name', device_name)}:")
            if 'ip' in device_config:
                print(f"    IP: {device_config['ip']}")
            if 'mac' in device_config:
                print(f"    MAC: {device_config['mac']}")
            print(f"    Method: {device_config.get('method', 'auto')}")

        return True

    except Exception as e:
        print(f"❌ Config error: {e}")
        return False


def main():
    """Run network presence configuration utility"""
    print_header("Network Presence Detection Configuration Utility")

    print("This utility will help you set up WiFi-based presence detection.")
    print("Used for automated home/away detection.\n")

    # Step 1: Get network info
    print_header("Step 1: Network Information")
    network, local_ip = get_network_info()

    # Step 2: Scan network
    print_header("Step 2: Scan Network")
    devices = scan_network_devices()

    # Step 3: Manual device entry
    print_header("Step 3: Device Configuration")

    print("To configure presence detection, you need your device's network info.")
    print("\nFor iPhone:")
    print("  - IP Address: Settings → WiFi → (i) → IP Address")
    print("  - MAC Address: Settings → General → About → WiFi Address")
    print("\nFor Android:")
    print("  - IP Address: Settings → WiFi → Current Network → Details")
    print("  - MAC Address: Settings → About Phone → Status")

    print("\n" + "-" * 70)

    # Interactive input
    device_name = input("\nDevice name (e.g., \"Matt's iPhone\"): ").strip()
    if not device_name:
        device_name = "Primary Device"

    ip = input("IP address (e.g., 192.168.1.50): ").strip()
    if not ip:
        print("❌ IP address is required")
        return 1

    mac = input("MAC address (optional, e.g., AA:BB:CC:DD:EE:FF): ").strip()

    # Step 4: Test detection
    print_header("Step 4: Test Detection Methods")
    results = test_device_detection(ip, mac if mac else None)
    recommended_method = recommend_method(results)

    # Step 5: Check existing config
    print_header("Step 5: Check Existing Configuration")
    has_config = check_config()

    # Summary
    print_header("Summary")

    if any(results.values()):
        print("✅ Device detected successfully!")
        generate_config_template(device_name, ip, mac, recommended_method)

        print("\nNext steps:")
        print("1. Copy the template above to config/config.yaml")
        print("2. Test with: python -m components.network.test")
        print("3. Use in automation: python automations/presence_monitor.py")

    else:
        print("⚠️  Device not detected on network")
        print("\nTroubleshooting:")
        print("1. Verify device is connected to same WiFi network")
        print("2. Check IP address is correct (may change if using DHCP)")
        print("3. Try setting a static IP for your device in router settings")
        print("4. Make sure no VPN is active on device")

        if not results:
            print("\n❌ Could not run detection tests")
            print("   Make sure components.network module is installed")

    print("\n" + "="*70 + "\n")

    return 0 if any(results.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
