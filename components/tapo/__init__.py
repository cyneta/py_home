"""
Tapo P125M Smart Plug Component

Clean API for controlling Tapo smart plugs.
"""

from .client import (
    TapoAPI,
    get_tapo,
    turn_on,
    turn_off,
    turn_on_all,
    turn_off_all,
    get_status
)

__all__ = [
    'TapoAPI',
    'get_tapo',
    'turn_on',
    'turn_off',
    'turn_on_all',
    'turn_off_all',
    'get_status'
]
