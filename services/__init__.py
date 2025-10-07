"""
External Services

APIs for external services (not physical devices).
"""

from .google_maps import get_travel_time, check_route_warnings, get_route_info
from .openweather import get_current_weather, get_forecast, get_weather_summary
from .github import add_task, get_repo_info

__all__ = [
    'get_travel_time',
    'check_route_warnings',
    'get_route_info',
    'get_current_weather',
    'get_forecast',
    'get_weather_summary',
    'add_task',
    'get_repo_info'
]
