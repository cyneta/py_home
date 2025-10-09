"""
Tuya Cloud API Component for Alen Air Purifiers

Clean API for controlling Alen BreatheSmart 75i air purifiers via Tuya Cloud.
"""

from .client import (
    TuyaAPI,
    get_tuya,
    get_air_quality,
    set_power,
    set_fan_speed,
    get_status,
    list_all_status
)

from .air_purifier import AlenAirPurifier

__all__ = [
    'TuyaAPI',
    'get_tuya',
    'get_air_quality',
    'set_power',
    'set_fan_speed',
    'get_status',
    'list_all_status',
    'AlenAirPurifier'
]
