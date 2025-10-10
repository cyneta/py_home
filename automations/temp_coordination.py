#!/usr/bin/env python
"""
Temperature Coordination Automation

Coordinates Nest thermostat and Sensibo AC to avoid conflicts.

Logic:
- If Nest temp > 76°F: Turn on Sensibo AC (cool mode)
- If Nest temp < 74°F: Turn off Sensibo AC
- Prevents heating and cooling running simultaneously

Designed to run as a cron job every 15 minutes:
    */15 * * * * cd /home/pi/py_home && python automations/temp_coordination.py

Usage:
    python automations/temp_coordination.py
    python automations/temp_coordination.py --dry-run  # Test without executing
    DRY_RUN=true python automations/temp_coordination.py  # Test without executing
"""

import logging
import os
import sys
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for dry-run mode
DRY_RUN = os.environ.get('DRY_RUN', 'false').lower() == 'true' or '--dry-run' in sys.argv


def run():
    """Execute temperature coordination"""
    timestamp = datetime.now().isoformat()

    if DRY_RUN:
        logger.info(f"[DRY-RUN] Temperature coordination triggered at {timestamp}")
    else:
        logger.info(f"Temperature coordination triggered at {timestamp}")

    results = {
        'timestamp': timestamp,
        'action': 'temp_coordination',
        'changes_made': [],
        'errors': []
    }

    try:
        # Get current Nest status (read operations don't need dry-run mode)
        from components.nest import NestAPI

        nest = NestAPI(dry_run=False)  # Always read actual status
        nest_status = nest.get_status()
        current_temp = nest_status['current_temp_f']
        hvac_mode = nest_status['mode']
        hvac_status = nest_status['hvac_status']

        results['nest_temp'] = current_temp
        results['nest_mode'] = hvac_mode
        results['hvac_status'] = hvac_status

        logger.info(f"Nest: {current_temp}°F, mode={hvac_mode}, status={hvac_status}")

    except Exception as e:
        logger.error(f"Failed to get Nest status: {e}")
        results['errors'].append(f"Nest: {e}")
        return results

    try:
        # Get current Sensibo status (read operations don't need dry-run mode)
        from components.sensibo import SensiboAPI

        sensibo_read = SensiboAPI(dry_run=False)  # Always read actual status
        sensibo_status = sensibo_read.get_status()
        ac_on = sensibo_status['on']
        ac_mode = sensibo_status['mode']
        ac_temp = sensibo_status['target_temp_f']

        results['ac_on'] = ac_on
        results['ac_mode'] = ac_mode
        results['ac_target'] = ac_temp

        logger.info(f"Sensibo: {'ON' if ac_on else 'OFF'}, mode={ac_mode}, target={ac_temp}°F")

    except Exception as e:
        logger.error(f"Failed to get Sensibo status: {e}")
        results['errors'].append(f"Sensibo: {e}")
        return results

    # Decision logic
    from lib.config import config
    trigger_temp = config['automation']['temp_coordination']['trigger_ac_above_f']
    turn_off_temp = config['automation']['temp_coordination']['turn_off_ac_below_f']

    # If too hot and AC is off, turn it on
    if current_temp > trigger_temp and not ac_on:
        try:
            from components.sensibo import SensiboAPI

            sensibo = SensiboAPI(dry_run=DRY_RUN)
            # Turn on AC in cool mode at 72°F
            sensibo.turn_on(mode='cool', target_temp_f=72, fan_level='auto')
            results['changes_made'].append(f"Turned ON Sensibo AC (Nest at {current_temp}°F > {trigger_temp}°F)")
            logger.info(f"✓ Turned ON Sensibo AC (too hot: {current_temp}°F)")

            # Send notification with action summary
            if not DRY_RUN:
                from lib.notifications import send_automation_summary
                send_automation_summary(
                    "🌡️ Temperature Adjusted",
                    [f"AC turned ON (house at {current_temp}°F)"],
                    priority=0
                )
            else:
                logger.info(f"[DRY-RUN] Would send notification: AC turned ON")

        except Exception as e:
            logger.error(f"Failed to turn on Sensibo: {e}")
            results['errors'].append(f"Turn on Sensibo: {e}")

    # If cool enough and AC is on, turn it off
    elif current_temp < turn_off_temp and ac_on:
        try:
            from components.sensibo import SensiboAPI

            sensibo = SensiboAPI(dry_run=DRY_RUN)
            sensibo.turn_off()
            results['changes_made'].append(f"Turned OFF Sensibo AC (Nest at {current_temp}°F < {turn_off_temp}°F)")
            logger.info(f"✓ Turned OFF Sensibo AC (cool enough: {current_temp}°F)")

            # Send notification with action summary
            if not DRY_RUN:
                from lib.notifications import send_automation_summary
                send_automation_summary(
                    "🌡️ Temperature Adjusted",
                    [f"AC turned OFF (house at {current_temp}°F)"],
                    priority=0
                )
            else:
                logger.info(f"[DRY-RUN] Would send notification: AC turned OFF")

        except Exception as e:
            logger.error(f"Failed to turn off Sensibo: {e}")
            results['errors'].append(f"Turn off Sensibo: {e}")

    else:
        # No action needed
        results['changes_made'].append("No action needed")
        logger.info(f"→ No action needed (temp={current_temp}°F, AC={'ON' if ac_on else 'OFF'})")

    # Summary
    logger.info(f"\n{'='*50}")
    logger.info(f"Temperature Coordination Complete")
    logger.info(f"  Nest: {current_temp}°F ({hvac_mode})")
    logger.info(f"  AC: {'ON' if ac_on else 'OFF'}")
    logger.info(f"  Changes: {len(results['changes_made'])}")

    for change in results['changes_made']:
        logger.info(f"    - {change}")

    if results['errors']:
        logger.info(f"  Errors: {len(results['errors'])}")
        for error in results['errors']:
            logger.info(f"    - {error}")

    logger.info(f"{'='*50}\n")

    return results


if __name__ == '__main__':
    run()
