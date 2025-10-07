#!/usr/bin/env python
"""
Traffic Alert Automation

Check for construction, incidents, or delays on I-80 West to Milwaukee.

Can be run manually or as part of "Leaving for Milwaukee" routine.

Usage:
    python automations/traffic_alert.py
    python automations/traffic_alert.py "Milwaukee, WI"
"""

import sys
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_route_conditions(destination="Milwaukee, WI"):
    """
    Check route for traffic, construction, warnings

    Args:
        destination: Destination address

    Returns:
        dict: Route conditions with warnings, delays, summary
    """
    timestamp = datetime.now().isoformat()
    logger.info(f"Traffic alert triggered at {timestamp}")
    logger.info(f"Checking route to: {destination}")

    try:
        from services import get_travel_time, check_route_warnings
        from lib.config import config

        # Get home location
        home = config['locations']['home']
        origin = f"{home['lat']},{home['lng']}"

        # Get travel time with traffic
        travel = get_travel_time(origin, destination)

        # Get route warnings
        warnings = check_route_warnings(origin, destination)

        # Analyze conditions
        result = {
            'timestamp': timestamp,
            'destination': destination,
            'distance_miles': travel['distance_miles'],
            'duration_minutes': travel['duration_in_traffic_minutes'],
            'traffic_level': travel['traffic_level'],
            'delay_minutes': travel.get('delay_minutes', 0),
            'warnings': warnings,
            'has_warnings': len(warnings) > 0
        }

        # Determine severity
        if len(warnings) > 0 or travel['traffic_level'] == 'heavy':
            result['severity'] = 'high'
            result['alert_type'] = 'warning'
        elif travel['traffic_level'] == 'moderate' or travel['delay_minutes'] > 15:
            result['severity'] = 'medium'
            result['alert_type'] = 'advisory'
        else:
            result['severity'] = 'low'
            result['alert_type'] = 'clear'

        # Create human-readable summary
        result['summary'] = create_summary(result)

        logger.info(f"Route check complete: {result['alert_type']}")

        return result

    except Exception as e:
        logger.error(f"Failed to check route: {e}")
        return {
            'timestamp': timestamp,
            'destination': destination,
            'error': str(e),
            'alert_type': 'error'
        }


def create_summary(conditions):
    """Create human-readable summary"""

    lines = []

    # Traffic status
    traffic = conditions['traffic_level']
    duration = conditions['duration_minutes']
    delay = conditions['delay_minutes']

    if traffic == 'heavy':
        lines.append(f"🔴 Heavy traffic - {duration} minutes")
        if delay > 0:
            lines.append(f"   +{delay} min delay from normal")
    elif traffic == 'moderate':
        lines.append(f"🟡 Moderate traffic - {duration} minutes")
        if delay > 0:
            lines.append(f"   +{delay} min delay from normal")
    else:
        lines.append(f"🟢 Light traffic - {duration} minutes")

    # Distance
    lines.append(f"📍 {conditions['distance_miles']} miles")

    # Warnings
    if conditions['has_warnings']:
        lines.append(f"\n⚠️ Route Warnings:")
        for warning in conditions['warnings']:
            lines.append(f"   • {warning}")
    else:
        lines.append(f"\n✅ No construction or incidents")

    return '\n'.join(lines)


def run(destination="Milwaukee, WI", send_notification=True):
    """
    Execute traffic alert check

    Args:
        destination: Where to check traffic to
        send_notification: Send notification if conditions warrant
    """
    conditions = check_route_conditions(destination)

    if 'error' in conditions:
        logger.error(f"Error checking traffic: {conditions['error']}")
        return conditions

    # Print summary
    print(f"\n{'='*50}")
    print(f"Traffic Alert: {destination}")
    print(f"{'='*50}")
    print(conditions['summary'])
    print(f"{'='*50}\n")

    # Send notification if warranted
    if send_notification:
        try:
            from lib.notifications import send, send_high

            alert_type = conditions['alert_type']

            if alert_type == 'warning':
                # High severity - construction or heavy traffic
                title = f"⚠️ Traffic Alert: {destination}"
                message = conditions['summary']
                send_high(message, title=title)
                logger.info("✓ High-priority alert sent")

            elif alert_type == 'advisory':
                # Medium severity - moderate delays
                title = f"🟡 Traffic Advisory: {destination}"
                message = conditions['summary']
                send(message, title=title)
                logger.info("✓ Advisory notification sent")

            else:
                # All clear - only send if explicitly requested
                # (Don't spam with "all clear" notifications)
                logger.info("✓ Route is clear, no notification needed")

        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")

    return conditions


if __name__ == '__main__':
    # Get destination from command line or use default
    destination = sys.argv[1] if len(sys.argv) > 1 else "Milwaukee, WI"

    result = run(destination)

    # Exit code based on conditions
    if 'error' in result:
        sys.exit(1)
    elif result['alert_type'] == 'warning':
        sys.exit(2)  # High severity
    else:
        sys.exit(0)  # All clear or advisory
