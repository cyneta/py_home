"""
Network Presence Detection Component

Detects device presence on local network via ping (ICMP).

Primary use: Backup to iOS location automations for home/away detection.
"""

from .presence import is_device_home

__all__ = [
    'is_device_home'
]
