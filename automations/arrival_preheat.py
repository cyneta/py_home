#!/usr/bin/env python
"""
Arrival Pre-Heat Automation

Triggered when leaving work (20+ min away from home).
Pre-heats house based on current weather and ETA.
"""

import sys
import logging

# Add project root to path
sys.path.insert(0, '/c/git/cyneta/py_home')

from components.nest import set_temperature, get_status
from components.sensibo import set_ac_state, get_ac_status
from services.openweather import get_current_weather
from lib.config import config
from lib.notifications import send_notification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """
    Pre-heat/cool house before arrival

    Strategy:
    - Check current outdoor temp
    - If cold (<50°F): Set Nest to comfort temp (72°F)
    - If hot (>75°F): Turn on Sensibo AC
    - Send notification with ETA
    """
    logger.info("Running arrival pre-heat automation")

    try:
        # Get ETA from command line arg (if provided)
        eta_minutes = int(sys.argv[1]) if len(sys.argv) > 1 else None

        # Get current weather
        weather = get_current_weather()
        temp = weather['temp']

        logger.info(f"Current temp: {temp}°F, ETA: {eta_minutes} min")

        actions_taken = []

        # Cold weather: Pre-heat with Nest
        if temp < 50:
            comfort_temp = config['nest']['comfort_temp']
            logger.info(f"Cold weather detected. Setting Nest to {comfort_temp}°F")

            result = set_temperature(comfort_temp)
            actions_taken.append(f"Nest → {comfort_temp}°F")

        # Hot weather: Pre-cool with AC
        elif temp > 75:
            logger.info("Hot weather detected. Turning on AC")

            result = set_ac_state(
                power='on',
                mode='cool',
                target_temp=68,
                fan_level='auto'
            )
            actions_taken.append("AC → Cool 68°F")

        # Moderate weather: No action needed
        else:
            logger.info("Moderate weather. No pre-heating needed")
            actions_taken.append("No action (temp OK)")

        # Send notification
        if eta_minutes:
            message = f"Pre-heating house. ETA: {eta_minutes} min. {', '.join(actions_taken)}"
        else:
            message = f"Pre-heating house. {', '.join(actions_taken)}"

        send_notification(
            title="🏡 Arriving Soon",
            message=message,
            priority=0
        )

        logger.info(f"Pre-heat complete: {', '.join(actions_taken)}")
        print(f"✓ {message}")

    except Exception as e:
        logger.error(f"Pre-heat automation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
