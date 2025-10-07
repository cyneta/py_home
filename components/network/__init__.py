"""
Network Presence Detection Component

Detects device presence on local network via ping or ARP scan.

Primary use: Backup to iOS location automations for home/away detection.
"""

from .presence import is_device_home, scan_network, get_device_info

__all__ = [
    'is_device_home',
    'scan_network',
    'get_device_info'
]
