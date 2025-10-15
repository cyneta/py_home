"""
Sensibo Mini-Split AC Component

Clean API for controlling Sensibo AC controller.
"""

from .client import (
    SensiboAPI,
    get_sensibo,
    turn_on,
    turn_off,
    get_status,
    set_comfort,
    set_away,
    set_sleep
)

__all__ = [
    'SensiboAPI',
    'get_sensibo',
    'turn_on',
    'turn_off',
    'get_status',
    'set_comfort',
    'set_away',
    'set_sleep'
]
