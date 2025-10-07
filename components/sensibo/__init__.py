"""
Sensibo Mini-Split AC Component

Clean API for controlling Sensibo AC controller.
"""

from .client import (
    SensiboAPI,
    get_sensibo,
    set_temperature,
    turn_on,
    turn_off,
    get_status
)

__all__ = [
    'SensiboAPI',
    'get_sensibo',
    'set_temperature',
    'turn_on',
    'turn_off',
    'get_status'
]
