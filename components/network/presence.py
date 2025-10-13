"""
Network Presence Detection

Detects if devices are on the local network using ping (ICMP).

Setup:
1. Get your iPhone's IP: Settings → WiFi → (i) → IP Address
2. Add to config.yaml under 'presence' section

Usage:
    from components.network import is_device_home

    if is_device_home('192.168.1.50'):
        print("Phone is home!")
"""

import subprocess
import platform
import logging

logger = logging.getLogger(__name__)


def is_device_home(ip_address):
    """
    Check if device is on network by IP address

    Args:
        ip_address: IP address (e.g., '192.168.1.50')

    Returns:
        bool: True if device responds to ping

    Example:
        >>> is_device_home('192.168.1.50')
        True
    """
    if not ip_address:
        logger.error("No IP address provided")
        return False

    # Validate it's an IP address (not MAC)
    if ':' in ip_address or '-' in ip_address:
        raise ValueError(f"Invalid IP address: {ip_address}. MAC addresses are not supported.")

    return _check_ping(ip_address)


def _check_ping(ip_address):
    """
    Check if device responds to ping

    Fast and reliable for devices that respond to ICMP (like iPhones on home WiFi)
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


__all__ = ['is_device_home']
