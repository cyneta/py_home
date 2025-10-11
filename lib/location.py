"""
Location tracking and geofencing for py_home

Stores user's current location and calculates ETAs for smart arrival automations.
Used by iOS Shortcuts geofencing to update location on boundary crossings.
"""

import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
from lib.logging_config import kvlog

logger = logging.getLogger(__name__)

# Location data file (stores last known location)
LOCATION_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'location.json')


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two GPS coordinates using Haversine formula

    Args:
        lat1, lon1: First coordinate
        lat2, lon2: Second coordinate

    Returns:
        Distance in meters
    """
    from math import radians, sin, cos, sqrt, atan2

    # Earth radius in meters
    R = 6371000

    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c


def update_location(lat: float, lng: float, trigger: str = "manual") -> Dict:
    """
    Update user's current location

    Args:
        lat: Latitude
        lng: Longitude
        trigger: What triggered the update (e.g., "leaving_work", "near_home")

    Returns:
        dict: {
            'status': 'updated',
            'location': {'lat', 'lng'},
            'trigger': str,
            'timestamp': ISO timestamp,
            'distance_from_home_meters': float,
            'is_home': bool
        }
    """
    from lib.config import config

    # Ensure data directory exists
    data_dir = os.path.dirname(LOCATION_FILE)
    os.makedirs(data_dir, exist_ok=True)

    # Calculate distance from home
    home = config['locations']['home']
    distance = haversine_distance(lat, lng, home['lat'], home['lng'])
    is_home = distance <= home.get('radius_meters', 150)

    # Store location data
    location_data = {
        'lat': lat,
        'lng': lng,
        'trigger': trigger,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'distance_from_home_meters': round(distance, 1),
        'is_home': is_home
    }

    with open(LOCATION_FILE, 'w') as f:
        json.dump(location_data, f, indent=2)

    kvlog(logger, logging.INFO, module='location', action='update_location',
          lat=round(lat, 4), lng=round(lng, 4), distance_m=round(distance, 0),
          trigger=trigger, is_home=is_home)

    return {
        'status': 'updated',
        'location': {'lat': lat, 'lng': lng},
        'trigger': trigger,
        'timestamp': location_data['timestamp'],
        'distance_from_home_meters': distance,
        'is_home': is_home
    }


def get_location() -> Optional[Dict]:
    """
    Get user's last known location

    Returns:
        dict or None: Location data if available:
        {
            'lat': float,
            'lng': float,
            'trigger': str,
            'timestamp': str (ISO format),
            'distance_from_home_meters': float,
            'is_home': bool,
            'age_seconds': float (how old the data is)
        }
    """
    if not os.path.exists(LOCATION_FILE):
        return None

    try:
        with open(LOCATION_FILE, 'r') as f:
            data = json.load(f)

        # Calculate age
        timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        age = (datetime.utcnow() - timestamp.replace(tzinfo=None)).total_seconds()
        data['age_seconds'] = round(age, 1)

        return data

    except Exception as e:
        kvlog(logger, logging.ERROR, module='location', action='get_location',
              error_type=type(e).__name__, error_msg=str(e))
        return None


def get_eta_home() -> Optional[Dict]:
    """
    Calculate ETA to home using Google Maps API

    Returns:
        dict or None: ETA information:
        {
            'duration_minutes': int,
            'duration_in_traffic_minutes': int,
            'distance_miles': float,
            'traffic_level': str,
            'eta_timestamp': str (ISO format),
            'origin': {'lat', 'lng'},
            'destination': {'lat', 'lng'}
        }
    """
    start_time = time.time()
    location = get_location()
    if not location:
        kvlog(logger, logging.WARNING, module='location', action='get_eta_home',
              result='no_location_data')
        return None

    from lib.config import config
    from services.google_maps import get_travel_time

    home = config['locations']['home']

    try:
        # Get travel time with traffic
        origin = f"{location['lat']},{location['lng']}"
        destination = f"{home['lat']},{home['lng']}"

        travel = get_travel_time(origin, destination)

        # Calculate ETA timestamp
        eta_time = datetime.utcnow()
        from datetime import timedelta
        eta_time += timedelta(minutes=travel['duration_in_traffic_minutes'])

        result = {
            **travel,
            'eta_timestamp': eta_time.isoformat() + 'Z',
            'origin': {'lat': location['lat'], 'lng': location['lng']},
            'destination': {'lat': home['lat'], 'lng': home['lng']}
        }

        duration_ms = int((time.time() - start_time) * 1000)
        kvlog(logger, logging.INFO, module='location', action='get_eta_home',
              result='ok', eta_minutes=travel['duration_in_traffic_minutes'],
              distance_miles=round(travel['distance_miles'], 1),
              traffic_level=travel['traffic_level'], duration_ms=duration_ms)

        return result

    except Exception as e:
        kvlog(logger, logging.ERROR, module='location', action='get_eta_home',
              error_type=type(e).__name__, error_msg=str(e))
        return None


def should_trigger_arrival(trigger: str) -> Tuple[bool, Optional[str]]:
    """
    Determine if location update should trigger arrival automations

    Args:
        trigger: Geofence trigger name (e.g., "near_home", "arriving_home")

    Returns:
        (should_trigger, automation_type):
            - should_trigger: bool
            - automation_type: 'preheat' | 'lights' | 'full_arrival' | None
    """
    location = get_location()
    if not location:
        return False, None

    distance = location['distance_from_home_meters']

    # Trigger matrix based on distance and geofence
    if trigger == "leaving_work":
        # Pre-heat house when leaving work (if far enough away)
        if distance > 5000:  # > 5km away
            return True, 'preheat'

    elif trigger == "near_home":
        # Turn on lights when crossing 1km geofence (inside 1km radius)
        if distance <= 1000:
            return True, 'lights'

    elif trigger == "arriving_home":
        # Full arrival automation when crossing home geofence
        if distance <= 200:  # Within home radius
            return True, 'full_arrival'

    return False, None


__all__ = [
    'update_location',
    'get_location',
    'get_eta_home',
    'should_trigger_arrival',
    'haversine_distance'
]
