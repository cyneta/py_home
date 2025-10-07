"""
Network Presence Detection

Detects if devices are on the local network using multiple methods:
1. Ping (ICMP) - fast, requires static IP
2. ARP scan - more reliable, uses MAC address
3. Router query - most accurate, router-specific

Setup:
1. Get your iPhone's IP: Settings → WiFi → (i) → IP Address
2. Get your iPhone's MAC: Settings → General → About → WiFi Address
3. Add to config.yaml under 'presence' section

Usage:
    from components.network import is_device_home

    if is_device_home('192.168.1.50'):
        print("Phone is home!")
"""

import subprocess
import platform
import logging
import re

logger = logging.getLogger(__name__)


def is_device_home(identifier, method='ping'):
    """
    Check if device is on network

    Args:
        identifier: IP address (e.g., '192.168.1.50') or MAC (e.g., 'AA:BB:CC:DD:EE:FF')
        method: 'ping', 'arp', or 'auto' (tries ping first, then arp)

    Returns:
        bool: True if device is on network

    Example:
        >>> is_device_home('192.168.1.50')  # By IP
        True
        >>> is_device_home('AA:BB:CC:DD:EE:FF', method='arp')  # By MAC
        True
    """
    # Detect if identifier is IP or MAC
    is_mac = ':' in identifier or '-' in identifier

    if method == 'auto':
        # Try ping first (faster), fall back to arp
        if is_mac:
            return _check_arp(identifier)
        else:
            return _check_ping(identifier) or _check_arp_by_ip(identifier)
    elif method == 'ping':
        if is_mac:
            raise ValueError("Cannot ping MAC address, use method='arp'")
        return _check_ping(identifier)
    elif method == 'arp':
        return _check_arp(identifier)
    else:
        raise ValueError(f"Unknown method: {method}")


def _check_ping(ip_address):
    """
    Check if device responds to ping

    Fast but less reliable (some devices ignore pings)
    """
    try:
        # Determine ping command based on OS
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        timeout = '-w' if platform.system().lower() == 'windows' else '-W'

        # Ping once with 2 second timeout
        command = ['ping', param, '1', timeout, '2', ip_address]

        result = subprocess.run(
            command,
            capture_output=True,
            timeout=3
        )

        is_home = result.returncode == 0

        if is_home:
            logger.debug(f"Ping successful: {ip_address}")
        else:
            logger.debug(f"Ping failed: {ip_address}")

        return is_home

    except subprocess.TimeoutExpired:
        logger.debug(f"Ping timeout: {ip_address}")
        return False
    except Exception as e:
        logger.error(f"Ping error for {ip_address}: {e}")
        return False


def _check_arp(mac_address):
    """
    Check if device is in ARP table by MAC address

    More reliable than ping, works even if device ignores pings
    Requires arp-scan on Linux or arp command on Windows/Mac
    """
    try:
        mac_normalized = mac_address.lower().replace('-', ':')

        # Try arp-scan first (Linux, most reliable)
        if _has_command('arp-scan'):
            result = subprocess.run(
                ['sudo', 'arp-scan', '--localnet', '--quiet'],
                capture_output=True,
                text=True,
                timeout=10
            )

            is_home = mac_normalized in result.stdout.lower()

            if is_home:
                logger.debug(f"ARP scan found: {mac_address}")
            else:
                logger.debug(f"ARP scan not found: {mac_address}")

            return is_home

        # Fall back to arp command (Windows/Mac/Linux)
        else:
            result = subprocess.run(
                ['arp', '-a'],
                capture_output=True,
                text=True,
                timeout=5
            )

            is_home = mac_normalized in result.stdout.lower()

            if is_home:
                logger.debug(f"ARP table found: {mac_address}")
            else:
                logger.debug(f"ARP table not found: {mac_address}")

            return is_home

    except subprocess.TimeoutExpired:
        logger.debug(f"ARP timeout for: {mac_address}")
        return False
    except Exception as e:
        logger.error(f"ARP error for {mac_address}: {e}")
        return False


def _check_arp_by_ip(ip_address):
    """
    Ping first to populate ARP cache, then check ARP table
    """
    # First ping to ensure entry in ARP cache
    _check_ping(ip_address)

    # Then check ARP table
    try:
        result = subprocess.run(
            ['arp', '-a'],
            capture_output=True,
            text=True,
            timeout=5
        )

        return ip_address in result.stdout

    except Exception as e:
        logger.error(f"ARP check error for {ip_address}: {e}")
        return False


def _has_command(command):
    """Check if command exists"""
    try:
        subprocess.run(
            ['which', command] if platform.system() != 'Windows' else ['where', command],
            capture_output=True,
            timeout=2
        )
        return True
    except:
        return False


def scan_network(subnet='192.168.1.0/24'):
    """
    Scan network for all active devices

    Args:
        subnet: Network subnet to scan (CIDR notation)

    Returns:
        list: List of dicts with IP and MAC for each device

    Example:
        >>> devices = scan_network('192.168.1.0/24')
        >>> for device in devices:
        ...     print(f"{device['ip']} - {device['mac']}")
    """
    devices = []

    try:
        if _has_command('arp-scan'):
            # Use arp-scan (Linux)
            result = subprocess.run(
                ['sudo', 'arp-scan', '--localnet'],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Parse arp-scan output
            # Format: IP<tab>MAC<tab>Vendor
            for line in result.stdout.split('\n'):
                parts = line.split('\t')
                if len(parts) >= 2:
                    ip = parts[0].strip()
                    mac = parts[1].strip()

                    # Validate IP format
                    if re.match(r'^\d+\.\d+\.\d+\.\d+$', ip):
                        devices.append({
                            'ip': ip,
                            'mac': mac,
                            'vendor': parts[2].strip() if len(parts) > 2 else ''
                        })
        else:
            # Fall back to arp -a
            result = subprocess.run(
                ['arp', '-a'],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Parse arp output (varies by OS)
            for line in result.stdout.split('\n'):
                # Look for IP and MAC patterns
                ip_match = re.search(r'\d+\.\d+\.\d+\.\d+', line)
                mac_match = re.search(r'[0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}', line)

                if ip_match and mac_match:
                    devices.append({
                        'ip': ip_match.group(),
                        'mac': mac_match.group(),
                        'vendor': ''
                    })

        logger.info(f"Found {len(devices)} devices on network")
        return devices

    except Exception as e:
        logger.error(f"Network scan error: {e}")
        return []


def get_device_info(identifier):
    """
    Get information about a device on the network

    Args:
        identifier: IP address or MAC address

    Returns:
        dict: Device info (ip, mac, vendor, online) or None

    Example:
        >>> info = get_device_info('192.168.1.50')
        >>> print(f"Device: {info['mac']} - Online: {info['online']}")
    """
    devices = scan_network()

    identifier_lower = identifier.lower().replace('-', ':')

    for device in devices:
        if (device['ip'] == identifier or
            device['mac'].lower().replace('-', ':') == identifier_lower):
            device['online'] = True
            return device

    # Device not found
    return {
        'ip': identifier if '.' in identifier else None,
        'mac': identifier if ':' in identifier or '-' in identifier else None,
        'vendor': '',
        'online': False
    }


def get_my_devices():
    """
    Get configured devices from config

    Returns:
        dict: Configured devices from config.yaml
    """
    try:
        from lib.config import config

        if 'presence' in config and 'devices' in config['presence']:
            return config['presence']['devices']
        else:
            logger.warning("No presence.devices configured in config.yaml")
            return {}

    except Exception as e:
        logger.error(f"Error loading device config: {e}")
        return {}


__all__ = [
    'is_device_home',
    'scan_network',
    'get_device_info',
    'get_my_devices'
]
