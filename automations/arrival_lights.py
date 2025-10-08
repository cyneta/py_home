#!/usr/bin/env python
"""
Arrival Lights Automation

Triggered when approaching home (5-10 min away).
Turns on key lights for arrival.
"""

import sys
import logging

# Add project root to path
sys.path.insert(0, '/c/git/cyneta/py_home')

from components.tapo import turn_on, get_outlet_by_name
from lib.notifications import send_notification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """
    Turn on lights when approaching home

    Lights to turn on:
    - Living room lamp (main light)
    - Bedroom lamps (if after dark)
    """
    logger.info("Running arrival lights automation")

    try:
        from datetime import datetime

        # Determine if it's after dark (simplified: 5pm - 7am)
        hour = datetime.now().hour
        is_dark = hour >= 17 or hour <= 7

        lights_turned_on = []

        # Always turn on living room lamp
        logger.info("Turning on living room lamp")
        livingroom = get_outlet_by_name("Livingroom Lamp")
        if livingroom:
            turn_on(livingroom['ip'])
            lights_turned_on.append("Living Room")

        # Turn on bedroom lamps if dark
        if is_dark:
            logger.info("After dark - turning on bedroom lamps")

            bedroom_right = get_outlet_by_name("Bedroom Right Lamp")
            if bedroom_right:
                turn_on(bedroom_right['ip'])
                lights_turned_on.append("Bedroom Right")

            bedroom_left = get_outlet_by_name("Bedroom Left Lamp")
            if bedroom_left:
                turn_on(bedroom_left['ip'])
                lights_turned_on.append("Bedroom Left")

        # Send notification
        message = f"Lights on: {', '.join(lights_turned_on)}"
        send_notification(
            title="💡 Welcome Home Soon",
            message=message,
            priority=0
        )

        logger.info(f"Arrival lights complete: {message}")
        print(f"✓ {message}")

    except Exception as e:
        logger.error(f"Arrival lights automation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
