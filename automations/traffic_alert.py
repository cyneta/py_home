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
import time
from datetime import datetime
from lib.logging_config import kvlog

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
    kvlog(logger, logging.INFO, automation='traffic_alert', event='check_start',
          destination=destination, timestamp=timestamp)

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

        kvlog(logger, logging.INFO, automation='traffic_alert', event='check_complete',
              alert_type=result['alert_type'], severity=result['severity'],
              duration_minutes=result['duration_minutes'])

        return result

    except Exception as e:
        kvlog(logger, logging.ERROR, automation='traffic_alert', action='check_route',
              error_type=type(e).__name__, error_msg=str(e))
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
    start_time = time.time()
    kvlog(logger, logging.NOTICE, automation='traffic_alert', event='start',
          destination=destination)

    conditions = check_route_conditions(destination)

    if 'error' in conditions:
        kvlog(logger, logging.ERROR, automation='traffic_alert', event='error',
              error_msg=conditions['error'])
        return conditions

    # Log summary
    kvlog(logger, logging.INFO, automation='traffic_alert', action='summary_created',
          alert_type=conditions['alert_type'], has_warnings=conditions['has_warnings'])

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
                kvlog(logger, logging.INFO, automation='traffic_alert',
                      action='notification', type='high_priority', result='sent')

            elif alert_type == 'advisory':
                # Medium severity - moderate delays
                title = f"🟡 Traffic Advisory: {destination}"
                message = conditions['summary']
                send(message, title=title)
                kvlog(logger, logging.INFO, automation='traffic_alert',
                      action='notification', type='advisory', result='sent')

            else:
                # All clear - only send if explicitly requested
                # (Don't spam with "all clear" notifications)
                kvlog(logger, logging.INFO, automation='traffic_alert',
                      action='notification', result='skipped_clear')

        except Exception as e:
            kvlog(logger, logging.WARNING, automation='traffic_alert',
                  action='notification', error_type=type(e).__name__, error_msg=str(e))

    total_duration_ms = int((time.time() - start_time) * 1000)
    kvlog(logger, logging.NOTICE, automation='traffic_alert', event='complete',
          duration_ms=total_duration_ms, alert_type=conditions['alert_type'])

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
