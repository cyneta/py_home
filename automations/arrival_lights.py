#!/usr/bin/env python
"""
Arrival Lights Automation

Triggered when approaching home (5-10 min away).
Turns on key lights for arrival.
"""

import sys
import logging
import time

# Add project root to path
sys.path.insert(0, '/c/git/cyneta/py_home')

from components.tapo import turn_on, get_outlet_by_name
from lib.notifications import send_notification
from lib.logging_config import kvlog

logger = logging.getLogger(__name__)


def main():
    """
    Turn on lights when approaching home

    Lights to turn on:
    - Living room lamp (main light)
    - Bedroom lamps (if after dark)
    """
    start_time = time.time()
    kvlog(logger, logging.NOTICE, automation='arrival_lights', event='start')

    try:
        from datetime import datetime

        # Determine if it's after dark (simplified: 5pm - 7am)
        hour = datetime.now().hour
        is_dark = hour >= 17 or hour <= 7

        lights_turned_on = []

        # Always turn on living room lamp
        livingroom = get_outlet_by_name("Livingroom Lamp")
        if livingroom:
            api_start = time.time()
            turn_on(livingroom['ip'])
            duration_ms = int((time.time() - api_start) * 1000)
            lights_turned_on.append("Living Room")
            kvlog(logger, logging.NOTICE, automation='arrival_lights', device='livingroom_lamp',
                  action='turn_on', result='ok', duration_ms=duration_ms)

        # Turn on bedroom lamps if dark
        if is_dark:
            kvlog(logger, logging.INFO, automation='arrival_lights', condition='after_dark',
                  hour=hour, bedroom_lights='enabled')

            bedroom_right = get_outlet_by_name("Bedroom Right Lamp")
            if bedroom_right:
                api_start = time.time()
                turn_on(bedroom_right['ip'])
                duration_ms = int((time.time() - api_start) * 1000)
                lights_turned_on.append("Bedroom Right")
                kvlog(logger, logging.NOTICE, automation='arrival_lights', device='bedroom_right_lamp',
                      action='turn_on', result='ok', duration_ms=duration_ms)

            bedroom_left = get_outlet_by_name("Bedroom Left Lamp")
            if bedroom_left:
                api_start = time.time()
                turn_on(bedroom_left['ip'])
                duration_ms = int((time.time() - api_start) * 1000)
                lights_turned_on.append("Bedroom Left")
                kvlog(logger, logging.NOTICE, automation='arrival_lights', device='bedroom_left_lamp',
                      action='turn_on', result='ok', duration_ms=duration_ms)

        # Send notification
        try:
            message = f"Lights on: {', '.join(lights_turned_on)}"
            send_notification(
                title="💡 Welcome Home Soon",
                message=message,
                priority=0
            )
            kvlog(logger, logging.INFO, automation='arrival_lights', action='notification',
                  result='sent', lights_count=len(lights_turned_on))
        except Exception as e:
            kvlog(logger, logging.ERROR, automation='arrival_lights', action='notification',
                  error_type=type(e).__name__, error_msg=str(e))

        # Complete
        total_duration_ms = int((time.time() - start_time) * 1000)
        kvlog(logger, logging.NOTICE, automation='arrival_lights', event='complete',
              duration_ms=total_duration_ms, lights_count=len(lights_turned_on))

    except Exception as e:
        kvlog(logger, logging.ERROR, automation='arrival_lights', event='failed',
              error_type=type(e).__name__, error_msg=str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
