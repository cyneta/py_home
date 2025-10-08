#!/usr/bin/env python
"""
Travel Time Query Automation

Get travel time with current traffic to common destinations.

Returns JSON for use by iOS Shortcuts or voice assistants.

Actions:
1. Query Google Maps Distance Matrix API
2. Calculate traffic delay
3. Return human-readable result

Usage:
    python automations/travel_time.py <destination>
    python automations/travel_time.py Milwaukee
    python automations/travel_time.py "1060 W Addison St, Chicago"

Returns:
    JSON: {
        "destination": str,
        "distance_miles": float,
        "duration_minutes": int,
        "duration_text": str,
        "traffic_level": "light" | "moderate" | "heavy",
        "delay_minutes": int,
        "message": str (human-readable summary)
    }
"""

import sys
import json
import logging
import time
from datetime import datetime
from lib.logging_config import kvlog

logger = logging.getLogger(__name__)


def run(destination="Milwaukee, WI"):
    """
    Get travel time to destination

    Args:
        destination: Where to get travel time to (default: Milwaukee, WI)

    Returns:
        dict: Travel time information
    """
    start_time = time.time()
    timestamp = datetime.now().isoformat()
    kvlog(logger, logging.NOTICE, automation='travel_time', event='start',
          destination=destination)

    try:
        from services import get_travel_time
        from lib.config import config

        # Get home location from config
        home = config['locations']['home']
        origin = f"{home['lat']},{home['lng']}"

        # Query Google Maps
        result = get_travel_time(origin, destination)

        # Create human-readable message
        duration = result['duration_in_traffic_minutes']
        traffic = result['traffic_level']
        delay = result['delay_minutes']

        if delay > 0:
            message = (
                f"Travel time to {destination}: {duration} minutes "
                f"({traffic} traffic, {delay} min delay)"
            )
        else:
            message = f"Travel time to {destination}: {duration} minutes ({traffic} traffic)"

        result['destination'] = destination
        result['message'] = message
        result['timestamp'] = timestamp

        total_duration_ms = int((time.time() - start_time) * 1000)
        kvlog(logger, logging.NOTICE, automation='travel_time', event='complete',
              duration_ms=total_duration_ms, travel_minutes=duration, traffic_level=traffic)

        return result

    except Exception as e:
        kvlog(logger, logging.ERROR, automation='travel_time', action='get_travel_time',
              error_type=type(e).__name__, error_msg=str(e))
        return {
            'error': str(e),
            'destination': destination,
            'timestamp': timestamp
        }


if __name__ == '__main__':
    # Get destination from command line args
    if len(sys.argv) > 1:
        destination = ' '.join(sys.argv[1:])
    else:
        destination = "Milwaukee, WI"

    result = run(destination)

    # Print JSON for iOS Shortcuts / voice assistants
    print(json.dumps(result, indent=2))
