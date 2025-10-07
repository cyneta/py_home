"""
Nest Thermostat Component

Clean API for controlling Nest thermostat via Google Smart Device Management.
"""

from .client import (
    NestAPI,
    get_nest,
    set_temperature,
    get_status,
    set_mode
)

__all__ = [
    'NestAPI',
    'get_nest',
    'set_temperature',
    'get_status',
    'set_mode'
]
