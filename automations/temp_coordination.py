#!/usr/bin/env python
"""
Temperature Coordination Automation

Coordinates Nest thermostat (upstairs/main house) and Sensibo mini-split (Master Suite).

Strategy:
- Day Mode: Sensibo target = Nest target (both zones same temp)
- Night Mode: Nest in ECO, Sensibo maintains Master Suite at 66°F
- Nobody Home: Turn off Sensibo (Nest has own away mode)

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
        'mode': None,  # 'day', 'night', or 'away'
        'changes_made': [],
        'errors': []
    }

    # Check presence from centralized state file
    try:
        import os
        presence_file = os.path.join(os.path.dirname(__file__), '..', '.presence_state')

        if os.path.exists(presence_file):
            with open(presence_file, 'r') as f:
                state = f.read().strip().lower()
                is_home = (state == 'home')
        else:
            # Fallback to ping if state file doesn't exist
            from components.network import is_device_home
            is_home = is_device_home('192.168.50.189')

        results['is_home'] = is_home
        logger.info(f"Presence: {'HOME' if is_home else 'AWAY'}")
    except Exception as e:
        logger.error(f"Failed to check presence: {e}")
        results['errors'].append(f"Presence: {e}")
        return results

    # Priority 1: Turn off mini-split if nobody home
    if not is_home:
        results['mode'] = 'away'
        logger.info("Mode: AWAY (nobody home)")

        try:
            from components.sensibo import SensiboAPI

            sensibo = SensiboAPI(dry_run=False)  # Always read actual status
            sensibo_status = sensibo.get_status()

            if sensibo_status['on']:
                # Turn off Sensibo
                if not DRY_RUN:
                    sensibo_write = SensiboAPI(dry_run=False)
                    sensibo_write.turn_off()

                    # Send notification
                    from lib.notifications import send_automation_summary
                    send_automation_summary(
                        "🌡️ Temperature Adjusted",
                        ["Mini-split OFF (nobody home)"],
                        priority=0
                    )

                results['changes_made'].append("Turned OFF Sensibo (nobody home)")
                logger.info("✓ Turned OFF Sensibo (nobody home)")
            else:
                results['changes_made'].append("Sensibo already off")
                logger.info("→ Sensibo already off (no action needed)")

        except Exception as e:
            logger.error(f"Failed to turn off Sensibo: {e}")
            results['errors'].append(f"Sensibo: {e}")

        return results

    # Check night mode
    try:
        from lib.night_mode import is_night_mode

        night_mode = is_night_mode()
        results['night_mode'] = night_mode

        if night_mode:
            results['mode'] = 'night'
            logger.info("Mode: NIGHT")
        else:
            results['mode'] = 'day'
            logger.info("Mode: DAY")
    except Exception as e:
        logger.error(f"Failed to check night mode: {e}")
        results['errors'].append(f"Night mode: {e}")
        results['mode'] = 'day'  # Default to day mode
        night_mode = False

    # Priority 2: Night Mode
    if night_mode:
        try:
            from components.sensibo import SensiboAPI
            from components.nest import NestAPI
            from lib.config import config

            target_temp = config['automation']['temp_coordination']['night_mode_temp_f']

            # Read Nest mode to ensure we don't fight it
            nest = NestAPI(dry_run=False)
            nest_status = nest.get_status()
            nest_mode = nest_status['mode']

            logger.info(f"Night mode - Nest mode: {nest_mode}")

            # Read Sensibo status
            sensibo_read = SensiboAPI(dry_run=False)
            sensibo_status = sensibo_read.get_status()
            sensibo_target = sensibo_status['target_temp_f']
            sensibo_mode = sensibo_status['mode']
            master_suite_temp = sensibo_status['current_temp_f']

            results['sensibo_target'] = sensibo_target
            results['sensibo_mode'] = sensibo_mode
            results['master_suite_temp'] = master_suite_temp
            results['night_target'] = target_temp
            results['nest_mode'] = nest_mode

            logger.info(f"Master Suite: {master_suite_temp}°F, Sensibo: {sensibo_mode} {sensibo_target}°F")
            logger.info(f"Night mode target: {target_temp}°F")

            # CRITICAL SAFETY: Sensibo mode MUST match Nest mode
            if nest_mode == 'HEAT':
                required_mode = 'heat'
            elif nest_mode == 'COOL':
                required_mode = 'cool'
            elif nest_mode == 'HEATCOOL':
                # Auto mode - choose based on current temp vs target
                required_mode = 'cool' if master_suite_temp > target_temp else 'heat'
            elif nest_mode == 'OFF':
                # Nest is off - turn off Sensibo too
                if sensibo_status['on']:
                    if not DRY_RUN:
                        sensibo_write = SensiboAPI(dry_run=False)
                        sensibo_write.turn_off()
                    results['changes_made'].append("Turned OFF Sensibo (Nest is OFF)")
                    logger.info("✓ Turned OFF Sensibo (Nest is OFF)")
                else:
                    results['changes_made'].append("Sensibo already off")
                    logger.info("→ Sensibo already off")
                return results
            else:
                logger.error(f"Unknown Nest mode: {nest_mode}")
                results['errors'].append(f"Unknown Nest mode: {nest_mode}")
                return results

            # Check if we need to update
            needs_update = False
            if sensibo_target != target_temp:
                logger.info(f"Temperature mismatch: Sensibo={sensibo_target}°F, Night target={target_temp}°F")
                needs_update = True
            if sensibo_mode != required_mode:
                logger.error(f"MODE MISMATCH! Sensibo={sensibo_mode}, Nest={nest_mode} (required={required_mode})")
                needs_update = True
            if not sensibo_status['on']:
                logger.info("Sensibo is OFF, turning on")
                needs_update = True

            if needs_update:
                if not DRY_RUN:
                    sensibo_write = SensiboAPI(dry_run=False)
                    sensibo_write.turn_on(mode=required_mode, temp_f=target_temp)

                    # Send notification
                    from lib.notifications import send_automation_summary
                    send_automation_summary(
                        "🌡️ Night Mode",
                        [f"Master Suite → {target_temp}°F ({required_mode})"],
                        priority=0
                    )

                results['changes_made'].append(f"Set Sensibo to {target_temp}°F ({required_mode} mode)")
                logger.info(f"✓ Set Sensibo to {target_temp}°F ({required_mode} mode)")
            else:
                results['changes_made'].append("Sensibo already at night target")
                logger.info("→ Sensibo already at night target (no action needed)")

        except Exception as e:
            logger.error(f"Failed to handle night mode: {e}")
            results['errors'].append(f"Night mode: {e}")

        return results

    # Priority 3: Day Mode - Sync Sensibo to Nest
    try:
        # Read Nest status
        from components.nest import NestAPI

        nest = NestAPI(dry_run=False)  # Always read actual status
        nest_status = nest.get_status()
        nest_target = nest_status['heat_setpoint_f'] or nest_status['cool_setpoint_f']
        nest_mode = nest_status['mode']

        results['nest_target'] = nest_target
        results['nest_mode'] = nest_mode

        logger.info(f"Nest: mode={nest_mode}, target={nest_target}°F")

        # Handle Nest in OFF mode
        if nest_mode == 'OFF':
            logger.info("Nest is OFF - keeping Sensibo off")
            results['changes_made'].append("Nest OFF - no coordination")

            # Turn off Sensibo if it's on
            try:
                from components.sensibo import SensiboAPI

                sensibo_read = SensiboAPI(dry_run=False)
                sensibo_status = sensibo_read.get_status()

                if sensibo_status['on']:
                    if not DRY_RUN:
                        sensibo_write = SensiboAPI(dry_run=False)
                        sensibo_write.turn_off()

                    results['changes_made'].append("Turned OFF Sensibo (Nest is OFF)")
                    logger.info("✓ Turned OFF Sensibo (Nest is OFF)")

            except Exception as e:
                logger.error(f"Failed to turn off Sensibo: {e}")
                results['errors'].append(f"Sensibo: {e}")

            return results

    except Exception as e:
        logger.error(f"Failed to get Nest status: {e}")
        results['errors'].append(f"Nest: {e}")
        return results

    try:
        # Handle case where Nest has no setpoint (ECO mode or OFF)
        if nest_target is None:
            logger.info("Nest has no setpoint (likely in ECO mode) - turning off Sensibo")
            results['changes_made'].append("Nest in ECO - turning off Sensibo")

            # Turn off Sensibo when Nest is in ECO
            try:
                from components.sensibo import SensiboAPI

                sensibo_read = SensiboAPI(dry_run=False)
                sensibo_status = sensibo_read.get_status()

                if sensibo_status['on']:
                    if not DRY_RUN:
                        sensibo_write = SensiboAPI(dry_run=False)
                        sensibo_write.turn_off()

                    results['changes_made'].append("Turned OFF Sensibo (Nest in ECO)")
                    logger.info("✓ Turned OFF Sensibo (Nest in ECO)")

            except Exception as e:
                logger.error(f"Failed to turn off Sensibo: {e}")
                results['errors'].append(f"Sensibo: {e}")

            return results

        # Read Sensibo status
        from components.sensibo import SensiboAPI

        sensibo_read = SensiboAPI(dry_run=False)
        sensibo_status = sensibo_read.get_status()
        sensibo_target = sensibo_status['target_temp_f']
        sensibo_mode = sensibo_status['mode']
        master_suite_temp = sensibo_status['current_temp_f']

        results['sensibo_target'] = sensibo_target
        results['sensibo_mode'] = sensibo_mode
        results['master_suite_temp'] = master_suite_temp

        logger.info(f"Master Suite: {master_suite_temp}°F, Sensibo: {sensibo_mode} {sensibo_target}°F")

        # CRITICAL SAFETY: Sensibo mode MUST match Nest mode
        # Map Nest mode to Sensibo mode
        if nest_mode == 'HEAT':
            required_mode = 'heat'
        elif nest_mode == 'COOL':
            required_mode = 'cool'
        elif nest_mode == 'HEATCOOL':
            # Auto mode - choose based on current temp vs target
            required_mode = 'cool' if master_suite_temp > nest_target else 'heat'
        else:
            logger.error(f"Unknown Nest mode: {nest_mode}")
            results['errors'].append(f"Unknown Nest mode: {nest_mode}")
            return results

        # Check if we need to update Sensibo
        needs_update = False
        if sensibo_target != nest_target:
            logger.info(f"Temperature mismatch: Sensibo={sensibo_target}°F, Nest={nest_target}°F")
            needs_update = True
        if sensibo_mode != required_mode:
            logger.error(f"MODE MISMATCH! Sensibo={sensibo_mode}, Nest={nest_mode} (required={required_mode})")
            needs_update = True
        if not sensibo_status['on']:
            logger.info("Sensibo is OFF, turning on")
            needs_update = True

        if needs_update:
            if not DRY_RUN:
                sensibo_write = SensiboAPI(dry_run=False)
                sensibo_write.turn_on(mode=required_mode, temp_f=nest_target)

                # Send notification
                from lib.notifications import send_automation_summary
                send_automation_summary(
                    "🌡️ Temperature Adjusted",
                    [f"Master Suite → {nest_target}°F ({required_mode} mode)"],
                    priority=0
                )

            results['changes_made'].append(f"Set Sensibo to {nest_target}°F ({required_mode} mode)")
            logger.info(f"✓ Set Sensibo to {nest_target}°F ({required_mode} mode)")
        else:
            results['changes_made'].append("Sensibo already synced to Nest")
            logger.info("→ Sensibo already synced to Nest (no action needed)")

    except Exception as e:
        logger.error(f"Failed to sync Sensibo: {e}")
        results['errors'].append(f"Sensibo: {e}")

    # Summary
    logger.info(f"\n{'='*50}")
    logger.info(f"Temperature Coordination Complete")
    logger.info(f"  Mode: {results['mode'].upper()}")
    if results.get('nest_target'):
        logger.info(f"  Nest: {nest_target}°F ({nest_mode})")
    if results.get('sensibo_target'):
        logger.info(f"  Sensibo: {sensibo_target}°F")
    if results.get('master_suite_temp'):
        logger.info(f"  Master Suite: {master_suite_temp}°F")
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
