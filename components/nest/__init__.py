"""
Nest Thermostat Component

Clean API for controlling Nest thermostat via Google Smart Device Management.
"""

from .client import (
    NestAPI,
    get_nest,
    set_temperature,
    get_status,
    set_mode,
    set_comfort,
    set_away,
    set_sleep
)

__all__ = [
    'NestAPI',
    'get_nest',
    'set_temperature',
    'get_status',
    'set_mode',
    'set_comfort',
    'set_away',
    'set_sleep'
]
