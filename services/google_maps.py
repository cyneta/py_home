"""
Google Maps API client for py_home

Provides travel time and traffic information using Google Maps Distance Matrix
and Directions APIs.

Requires:
- Google Maps API key in config (free tier: 40,000 requests/month)
- 'googlemaps' Python package
"""

import logging
import googlemaps
from datetime import datetime

logger = logging.getLogger(__name__)


def get_client():
    """Get Google Maps API client instance"""
    from lib.config import config
    api_key = config['google_maps']['api_key']

    if not api_key:
        raise ValueError("Google Maps API key not configured in config/.env")

    return googlemaps.Client(key=api_key)


def get_travel_time(origin, destination):
    """
    Get travel time between two locations with current traffic

    Args:
        origin: Starting location (address string or "lat,lng")
        destination: Destination location (address string or "lat,lng")

    Returns:
        dict: {
            'distance_miles': float,
            'duration_minutes': int (without traffic),
            'duration_in_traffic_minutes': int (with current traffic),
            'duration_text': str (human-readable, e.g., "1 hour 45 mins"),
            'traffic_level': 'light' | 'moderate' | 'heavy',
            'delay_minutes': int (traffic delay)
        }

    Example:
        >>> result = get_travel_time("Chicago, IL", "Milwaukee, WI")
        >>> print(f"Travel time: {result['duration_in_traffic_minutes']} mins")
        >>> print(f"Traffic: {result['traffic_level']}")
    """
    gmaps = get_client()

    try:
        result = gmaps.distance_matrix(
            origins=origin,
            destinations=destination,
            mode="driving",
            departure_time="now",  # Include traffic
            units="imperial"
        )

        # Extract data from response
        element = result['rows'][0]['elements'][0]

        if element['status'] != 'OK':
            raise Exception(f"Maps API error: {element['status']}")

        # Duration without traffic (seconds)
        duration_seconds = element['duration']['value']
        duration_minutes = duration_seconds // 60

        # Duration with traffic (seconds)
        duration_traffic = element.get('duration_in_traffic', {})
        duration_traffic_seconds = duration_traffic.get('value', duration_seconds)
        duration_traffic_minutes = duration_traffic_seconds // 60

        # Calculate delay
        delay_seconds = duration_traffic_seconds - duration_seconds
        delay_minutes = delay_seconds // 60

        # Determine traffic level
        delay_ratio = duration_traffic_seconds / duration_seconds if duration_seconds > 0 else 1.0

        if delay_ratio < 1.1:
            traffic = 'light'
        elif delay_ratio < 1.3:
            traffic = 'moderate'
        else:
            traffic = 'heavy'

        # Distance
        distance_meters = element['distance']['value']
        distance_miles = distance_meters / 1609.34

        logger.info(
            f"Travel time from {origin} to {destination}: "
            f"{duration_traffic_minutes} mins ({traffic} traffic)"
        )

        return {
            'distance_miles': round(distance_miles, 1),
            'duration_minutes': duration_minutes,
            'duration_in_traffic_minutes': duration_traffic_minutes,
            'duration_text': duration_traffic.get('text', element['duration']['text']),
            'traffic_level': traffic,
            'delay_minutes': delay_minutes
        }

    except Exception as e:
        logger.error(f"Google Maps API error: {e}")
        raise


def check_route_warnings(origin, destination):
    """
    Check for construction, accidents, or other warnings on route

    Args:
        origin: Starting location
        destination: Destination location

    Returns:
        list: Warning messages (e.g., construction alerts)

    Example:
        >>> warnings = check_route_warnings("Chicago, IL", "Milwaukee, WI")
        >>> for warning in warnings:
        ...     print(warning)
    """
    gmaps = get_client()

    try:
        directions = gmaps.directions(
            origin=origin,
            destination=destination,
            departure_time="now"
        )

        warnings = []
        if directions:
            # Extract warnings from first route
            route = directions[0]

            # API warnings
            for warning in route.get('warnings', []):
                warnings.append(warning)

            # Check for traffic alerts in summary
            summary = route.get('summary', '')
            if summary:
                logger.info(f"Route summary: {summary}")

        logger.info(f"Found {len(warnings)} warnings for route")
        return warnings

    except Exception as e:
        logger.error(f"Google Maps API error: {e}")
        raise


def get_route_info(origin, destination):
    """
    Get comprehensive route information (travel time + warnings)

    Args:
        origin: Starting location
        destination: Destination location

    Returns:
        dict: Combined travel time and warning information

    Example:
        >>> info = get_route_info("Chicago, IL", "Milwaukee, WI")
        >>> print(f"{info['duration_text']} with {info['traffic_level']} traffic")
        >>> if info['warnings']:
        ...     print("Warnings:", info['warnings'])
    """
    travel = get_travel_time(origin, destination)
    warnings = check_route_warnings(origin, destination)

    return {
        **travel,
        'warnings': warnings,
        'has_warnings': len(warnings) > 0
    }


__all__ = ['get_travel_time', 'check_route_warnings', 'get_route_info']
