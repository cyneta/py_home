"""
Find Tapo devices on your network

This script scans your local network to find Tapo smart plugs and displays their IP addresses.
"""

import socket
import subprocess
import re

def get_local_network():
    """Get the local network IP range"""
    # Get local IP
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    # Extract network prefix (e.g., 192.168.1)
    parts = local_ip.split('.')
    network = '.'.join(parts[:3])

    return network, local_ip

def scan_arp_table():
    """Scan ARP table for Tapo/TP-Link devices"""
    print("Scanning ARP table for Tapo devices...\n")

    try:
        # Run arp -a command
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
        output = result.stdout

        # Look for TP-Link MAC addresses (starts with specific prefixes)
        # TP-Link common MAC prefixes: 50-C7-BF, C0-06-C3, 1C-3B-F3, etc.
        tapo_devices = []

        for line in output.split('\n'):
            # Parse IP addresses from ARP output
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
            if ip_match:
                ip = ip_match.group(1)

                # Try to get hostname
                try:
                    hostname = socket.gethostbyaddr(ip)[0]
                    if 'tapo' in hostname.lower() or 'tplink' in hostname.lower():
                        tapo_devices.append((ip, hostname))
                        print(f"✓ Found Tapo device: {ip} ({hostname})")
                except:
                    pass

        return tapo_devices

    except Exception as e:
        print(f"Error scanning ARP: {e}")
        return []

def manual_scan_range(network):
    """Manual scan of common IPs (faster than full range)"""
    print(f"\nScanning common IP ranges on {network}.x...\n")

    # Common DHCP ranges
    ranges = list(range(1, 20)) + list(range(100, 150)) + list(range(200, 255))

    found = []
    for i in ranges:
        ip = f"{network}.{i}"
        try:
            # Try to resolve hostname
            hostname = socket.gethostbyaddr(ip)[0]
            if 'tapo' in hostname.lower() or 'tplink' in hostname.lower() or 'plug' in hostname.lower():
                found.append((ip, hostname))
                print(f"✓ Found: {ip} ({hostname})")
        except:
            pass

    return found

def main():
    print("="*60)
    print("Tapo Device Finder")
    print("="*60)
    print()

    network, local_ip = get_local_network()
    print(f"Your computer's IP: {local_ip}")
    print(f"Network range: {network}.x")
    print()

    # Method 1: Scan ARP table
    devices = scan_arp_table()

    # Method 2: If nothing found, try manual scan
    if not devices:
        print("\nNo devices found in ARP table. Trying manual scan...")
        devices = manual_scan_range(network)

    print()
    print("="*60)

    if devices:
        print("Found Tapo devices:")
        print()
        for ip, hostname in devices:
            print(f"  IP: {ip}")
            print(f"  Hostname: {hostname}")
            print()
    else:
        print("No Tapo devices found automatically.")
        print()
        print("Manual steps to find your 'Kitchen plug':")
        print()
        print("1. Check your router's admin page")
        print("   - Usually at 192.168.1.1 or 192.168.0.1")
        print("   - Look for 'DHCP Clients' or 'Connected Devices'")
        print("   - Find devices with 'Tapo' or 'TP-Link' in the name")
        print()
        print("2. Or use your router's mobile app")
        print()
        print("3. Or try pinging your plug:")
        print(f"   - Unplug the Kitchen plug from power")
        print(f"   - Run: arp -a > before.txt")
        print(f"   - Plug in the Kitchen plug, wait 30 seconds")
        print(f"   - Run: arp -a > after.txt")
        print(f"   - Compare files to see new IP")

    print("="*60)
    print()
    print("Once you have the IP, add it to config/config.yaml:")
    print()
    print("  tapo:")
    print("    outlets:")
    print("      - name: 'Kitchen plug'")
    print("        ip: '192.168.1.XXX'")
    print()

if __name__ == '__main__':
    main()
