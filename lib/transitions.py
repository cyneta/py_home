"""
State Transitions for py_home

Defines complete state transitions for the automation system.
Each transition controls ALL components involved in that state change.

Transitions are called by:
- automations/scheduler.py (time-based: 05:00 wake, 22:30 sleep)
- automations/goodnight.py (manual trigger)
- automations/good_morning.py (manual trigger)
- automations/leaving_home.py (location-based)
- automations/pre_arrival.py (location-based)

Design principle: System executes scheduled transitions at specific times,
but respects user manual adjustments between transitions.

See: design/scheduler_transitions.md for complete architecture
See: design/principles/user_control.md for design principle
"""

import logging
import time
from datetime import datetime
from lib.logging_config import kvlog
from lib.config import get

logger = logging.getLogger(__name__)


def is_sleep_time():
    """
    Check if current time is within sleep hours

    Sleep hours are between sleep_time and wake_time.
    Example: 22:30 - 05:00 (overnight)

    Returns:
        bool: True if currently sleep hours
    """
    now = datetime.now()
    sleep_time = get('schedule.sleep_time', '22:30')
    wake_time = get('schedule.wake_time', '05:00')

    # Parse times
    sleep_hour, sleep_min = map(int, sleep_time.split(':'))
    wake_hour, wake_min = map(int, wake_time.split(':'))

    # Convert to minutes since midnight
    current_minutes = now.hour * 60 + now.minute
    sleep_minutes = sleep_hour * 60 + sleep_min
    wake_minutes = wake_hour * 60 + wake_min

    # Handle overnight wrap (e.g., 22:30 - 05:00)
    if sleep_minutes > wake_minutes:
        # Sleep time is after wake time (crosses midnight)
        return current_minutes >= sleep_minutes or current_minutes < wake_minutes
    else:
        # Normal case (shouldn't happen with typical schedule)
        return sleep_minutes <= current_minutes < wake_minutes


def transition_to_wake(dry_run=False):
    """
    Morning wake transition (05:00)

    Actions:
    1. Fetch current weather
    2. Calculate target temp based on weather (configurable thresholds):
       - < cold_threshold → cold_target (extra warmth, default 40°F → 72°F)
       - > hot_threshold → hot_target (lighter, default 75°F → 68°F)
       - Between thresholds → comfort temp (normal, default 70°F)
    3. Set Nest to comfort mode with calculated temp
    4. Set Sensibo to comfort mode with calculated temp
    5. Turn ON grow light (placeholder for now)
    6. Send ONE macro notification with weather + all actions

    Config:
        temperatures.weather_aware.cold_threshold (default: 40)
        temperatures.weather_aware.cold_target (default: 72)
        temperatures.weather_aware.hot_threshold (default: 75)
        temperatures.weather_aware.hot_target (default: 68)
        temperatures.comfort (default: 70)

    Args:
        dry_run: If True, log actions but don't execute

    Returns:
        dict: {
            'transition': 'wake',
            'status': 'success' | 'partial' | 'failed',
            'actions': list of action descriptions,
            'errors': list of error descriptions,
            'weather': weather summary string,
            'duration_ms': int
        }
    """
    start_time = time.time()
    kvlog(logger, logging.NOTICE, transition='wake', event='start', dry_run=dry_run)

    actions = []
    errors = []
    weather_info = None
    target_temp = None

    # 1. Fetch weather and calculate target temp
    try:
        from services.openweather import get_current_weather

        api_start = time.time()
        weather = get_current_weather()
        temp = weather['temp']
        condition = weather['conditions']
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.INFO, transition='wake', action='get_weather',
              temp=temp, condition=condition, duration_ms=duration_ms)

        # Calculate target based on outdoor temp (weather-aware)
        cold_threshold = get('temperatures.weather_aware.cold_threshold', 40)
        hot_threshold = get('temperatures.weather_aware.hot_threshold', 75)
        cold_target = get('temperatures.weather_aware.cold_target', 72)
        hot_target = get('temperatures.weather_aware.hot_target', 68)

        if temp < cold_threshold:
            target_temp = cold_target
            mode_note = f"Extra warmth mode ({temp:.0f}°F outside)"
        elif temp > hot_threshold:
            target_temp = hot_target
            mode_note = f"Light mode ({temp:.0f}°F outside)"
        else:
            target_temp = get('temperatures.comfort', 70)
            mode_note = f"Normal mode ({temp:.0f}°F outside)"

        weather_info = f"{temp:.0f}°F, {condition}"

    except Exception as e:
        kvlog(logger, logging.WARNING, transition='wake', action='get_weather',
              error_type=type(e).__name__, error_msg=str(e))
        # Fallback to config default
        target_temp = get('temperatures.comfort', 70)
        weather_info = "Weather unavailable"
        mode_note = f"Normal mode (weather unavailable)"

    # 2. Set Nest to comfort mode
    try:
        from components.nest import NestAPI

        nest = NestAPI(dry_run=dry_run)

        api_start = time.time()
        nest.set_comfort_mode(temp_f=target_temp)
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, transition='wake', device='nest',
              action='set_comfort', target_temp=target_temp, result='ok', duration_ms=duration_ms)

        actions.append(f"Nest → {target_temp}°F HEAT")
    except Exception as e:
        kvlog(logger, logging.ERROR, transition='wake', device='nest',
              action='set_comfort', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Nest: {type(e).__name__}")
        actions.append(f"✗ Nest failed")

    # 3. Set Sensibo to comfort mode
    try:
        from components.sensibo import SensiboAPI

        sensibo = SensiboAPI(dry_run=dry_run)

        api_start = time.time()
        sensibo.set_comfort_mode(temp_f=target_temp)
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, transition='wake', device='sensibo',
              action='set_comfort', target_temp=target_temp, result='ok', duration_ms=duration_ms)

        actions.append(f"Sensibo → {target_temp}°F HEAT")
    except Exception as e:
        kvlog(logger, logging.ERROR, transition='wake', device='sensibo',
              action='set_comfort', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Sensibo: {type(e).__name__}")
        actions.append(f"✗ Sensibo failed")

    # 4. Turn ON grow light (placeholder - will implement when grow light component ready)
    try:
        # Future: from components.grow_light import GrowLightAPI
        # grow_light = GrowLightAPI(dry_run=dry_run)
        # grow_light.turn_on()

        kvlog(logger, logging.INFO, transition='wake', device='grow_light',
              action='turn_on', result='placeholder')

        # Don't add to actions list yet - placeholder only
        # actions.append("Grow light → ON")
    except Exception as e:
        kvlog(logger, logging.ERROR, transition='wake', device='grow_light',
              action='turn_on', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Grow light: {type(e).__name__}")

    # 5. Send ONE macro notification
    try:
        if not dry_run:
            from lib.notifications import send_automation_summary

            title = "☀️ Wake Transition"
            if errors:
                title += " (Partial)"

            # Build notification body: weather + mode + actions + errors
            notification_body = [mode_note] + actions

            if errors:
                notification_body.extend([f"✗ {e}" for e in errors])

            priority = 1 if errors else 0

            send_automation_summary(title, notification_body, priority=priority)

            kvlog(logger, logging.INFO, transition='wake', action='notification', result='sent')
        else:
            kvlog(logger, logging.DEBUG, transition='wake', action='notification', result='skipped_dry_run')
    except Exception as e:
        kvlog(logger, logging.ERROR, transition='wake', action='notification',
              error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Notification: {type(e).__name__}")

    # Determine final status
    if not actions:
        status = 'failed'
    elif errors:
        status = 'partial'
    else:
        status = 'success'

    duration_ms = int((time.time() - start_time) * 1000)
    kvlog(logger, logging.NOTICE, transition='wake', event='complete',
          status=status, actions_count=len(actions), errors_count=len(errors), duration_ms=duration_ms)

    return {
        'transition': 'wake',
        'status': status,
        'actions': actions,
        'errors': errors,
        'weather': weather_info,
        'duration_ms': duration_ms
    }


def transition_to_sleep(dry_run=False):
    """
    Bedtime sleep transition (22:30)

    Actions:
    1. Set Nest to ECO mode (energy saving)
    2. Set Sensibo to sleep mode (66°F)
    3. Turn OFF grow light (placeholder)
    4. Turn OFF all Tapo outlets
    5. Send ONE macro notification with all actions

    Args:
        dry_run: If True, log actions but don't execute

    Returns:
        dict: {
            'transition': 'sleep',
            'status': 'success' | 'partial' | 'failed',
            'actions': list of action descriptions,
            'errors': list of error descriptions,
            'duration_ms': int
        }
    """
    start_time = time.time()
    kvlog(logger, logging.NOTICE, transition='sleep', event='start', dry_run=dry_run)

    actions = []
    errors = []

    # 1. Set Nest to ECO mode
    try:
        from components.nest import NestAPI

        nest = NestAPI(dry_run=dry_run)

        api_start = time.time()
        nest.set_sleep_mode()  # ECO mode
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, transition='sleep', device='nest',
              action='set_sleep', result='ok', duration_ms=duration_ms)

        actions.append("Nest → ECO mode")
    except Exception as e:
        kvlog(logger, logging.ERROR, transition='sleep', device='nest',
              action='set_sleep', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Nest: {type(e).__name__}")
        actions.append(f"✗ Nest failed")

    # 2. Set Sensibo to sleep mode (66°F)
    try:
        from components.sensibo import SensiboAPI

        sensibo = SensiboAPI(dry_run=dry_run)

        api_start = time.time()
        sensibo.set_sleep_mode()  # 66°F
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, transition='sleep', device='sensibo',
              action='set_sleep', result='ok', duration_ms=duration_ms)

        actions.append("Sensibo → 66°F")
    except Exception as e:
        kvlog(logger, logging.ERROR, transition='sleep', device='sensibo',
              action='set_sleep', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Sensibo: {type(e).__name__}")
        actions.append(f"✗ Sensibo failed")

    # 3. Turn OFF grow light (placeholder)
    try:
        # Future: from components.grow_light import GrowLightAPI
        # grow_light = GrowLightAPI(dry_run=dry_run)
        # grow_light.turn_off()

        kvlog(logger, logging.INFO, transition='sleep', device='grow_light',
              action='turn_off', result='placeholder')

        # Don't add to actions list yet - placeholder only
        # actions.append("Grow light → OFF")
    except Exception as e:
        kvlog(logger, logging.ERROR, transition='sleep', device='grow_light',
              action='turn_off', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Grow light: {type(e).__name__}")

    # 4. Turn OFF all Tapo outlets
    try:
        from components.tapo import TapoAPI

        tapo = TapoAPI(dry_run=dry_run)

        api_start = time.time()
        tapo.turn_off_all()
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, transition='sleep', device='tapo',
              action='turn_off_all', result='ok', duration_ms=duration_ms)

        actions.append("All outlets → OFF")
    except Exception as e:
        kvlog(logger, logging.ERROR, transition='sleep', device='tapo',
              action='turn_off_all', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Tapo: {type(e).__name__}")
        actions.append(f"✗ Outlets failed")

    # 5. Send ONE macro notification
    try:
        if not dry_run:
            from lib.notifications import send_automation_summary

            title = "💤 Sleep Transition"
            if errors:
                title += " (Partial)"

            notification_body = actions
            if errors:
                notification_body.extend([f"✗ {e}" for e in errors])

            priority = 1 if errors else 0

            send_automation_summary(title, notification_body, priority=priority)

            kvlog(logger, logging.INFO, transition='sleep', action='notification', result='sent')
        else:
            kvlog(logger, logging.DEBUG, transition='sleep', action='notification', result='skipped_dry_run')
    except Exception as e:
        kvlog(logger, logging.ERROR, transition='sleep', action='notification',
              error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Notification: {type(e).__name__}")

    # Determine final status
    if not actions:
        status = 'failed'
    elif errors:
        status = 'partial'
    else:
        status = 'success'

    duration_ms = int((time.time() - start_time) * 1000)
    kvlog(logger, logging.NOTICE, transition='sleep', event='complete',
          status=status, actions_count=len(actions), errors_count=len(errors), duration_ms=duration_ms)

    return {
        'transition': 'sleep',
        'status': status,
        'actions': actions,
        'errors': errors,
        'duration_ms': duration_ms
    }


def transition_to_away(dry_run=False):
    """
    Leaving home transition

    Actions:
    1. Set Nest to ECO/away mode
    2. Set Sensibo to away mode (OFF)
    3. Turn OFF all Tapo outlets
    4. Grow light: NO CHANGE (plants need consistent schedule)
    5. Send ONE macro notification

    Note: Presence state update handled by caller (leaving_home.py), not transition.

    Args:
        dry_run: If True, log actions but don't execute

    Returns:
        dict: {
            'transition': 'away',
            'status': 'success' | 'partial' | 'failed',
            'actions': list of action descriptions,
            'errors': list of error descriptions,
            'duration_ms': int
        }
    """
    start_time = time.time()
    kvlog(logger, logging.NOTICE, transition='away', event='start', dry_run=dry_run)

    actions = []
    errors = []

    # 1. Set Nest to ECO/away mode
    try:
        from components.nest import NestAPI

        nest = NestAPI(dry_run=dry_run)

        api_start = time.time()
        nest.set_away_mode()
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, transition='away', device='nest',
              action='set_away', result='ok', duration_ms=duration_ms)

        actions.append("Nest → ECO mode")
    except Exception as e:
        kvlog(logger, logging.ERROR, transition='away', device='nest',
              action='set_away', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Nest: {type(e).__name__}")
        actions.append(f"✗ Nest failed")

    # 2. Set Sensibo to away mode (OFF)
    try:
        from components.sensibo import SensiboAPI

        sensibo = SensiboAPI(dry_run=dry_run)

        api_start = time.time()
        sensibo.set_away_mode()
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, transition='away', device='sensibo',
              action='set_away', result='ok', duration_ms=duration_ms)

        actions.append("Sensibo → OFF")
    except Exception as e:
        kvlog(logger, logging.ERROR, transition='away', device='sensibo',
              action='set_away', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Sensibo: {type(e).__name__}")
        actions.append(f"✗ Sensibo failed")

    # 3. Turn OFF all Tapo outlets
    try:
        from components.tapo import TapoAPI

        tapo = TapoAPI(dry_run=dry_run)

        api_start = time.time()
        tapo.turn_off_all()
        duration_ms = int((time.time() - api_start) * 1000)

        kvlog(logger, logging.NOTICE, transition='away', device='tapo',
              action='turn_off_all', result='ok', duration_ms=duration_ms)

        actions.append("All outlets → OFF")
    except Exception as e:
        kvlog(logger, logging.ERROR, transition='away', device='tapo',
              action='turn_off_all', error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Tapo: {type(e).__name__}")
        actions.append(f"✗ Outlets failed")

    # 4. Grow light: NO CHANGE (note this in logging but don't control it)
    kvlog(logger, logging.INFO, transition='away', device='grow_light',
          action='no_change', reason='plants_need_consistent_schedule')

    # 5. Send ONE macro notification
    try:
        if not dry_run:
            from lib.notifications import send_automation_summary

            title = "🚗 Away Transition"
            if errors:
                title += " (Partial)"

            notification_body = actions
            # Add note about grow light being unchanged
            notification_body.append("ℹ️ Grow light unchanged (plant schedule)")

            if errors:
                notification_body.extend([f"✗ {e}" for e in errors])

            priority = 1 if errors else 0

            send_automation_summary(title, notification_body, priority=priority)

            kvlog(logger, logging.INFO, transition='away', action='notification', result='sent')
        else:
            kvlog(logger, logging.DEBUG, transition='away', action='notification', result='skipped_dry_run')
    except Exception as e:
        kvlog(logger, logging.ERROR, transition='away', action='notification',
              error_type=type(e).__name__, error_msg=str(e))
        errors.append(f"Notification: {type(e).__name__}")

    # Determine final status
    if not actions:
        status = 'failed'
    elif errors:
        status = 'partial'
    else:
        status = 'success'

    duration_ms = int((time.time() - start_time) * 1000)
    kvlog(logger, logging.NOTICE, transition='away', event='complete',
          status=status, actions_count=len(actions), errors_count=len(errors), duration_ms=duration_ms)

    return {
        'transition': 'away',
        'status': status,
        'actions': actions,
        'errors': errors,
        'duration_ms': duration_ms
    }


def transition_to_home(dry_run=False, send_notification=True):
    """
    Arriving home transition

    Actions:
    1. Check current time (is_sleep_time)
    2. If sleep hours (22:30-05:00):
       - Set Nest to ECO
       - Set Sensibo to sleep mode (66°F)
    3. If awake hours:
       - Set Nest to comfort mode (70°F)
       - Set Sensibo to comfort mode (70°F)
    4. Send ONE macro notification (optional, controlled by send_notification param)

    Note: Outdoor lights and presence state handled by caller (pre_arrival.py), not transition.

    Args:
        dry_run: If True, log actions but don't execute
        send_notification: If True, send notification. Set False for 2-stage arrival (pre_arrival.py)

    Returns:
        dict: {
            'transition': 'home',
            'status': 'success' | 'partial' | 'failed',
            'actions': list of action descriptions,
            'errors': list of error descriptions,
            'duration_ms': int
        }
    """
    start_time = time.time()
    kvlog(logger, logging.NOTICE, transition='home', event='start', dry_run=dry_run)

    actions = []
    errors = []

    # 1. Check if sleep time
    sleep_hours = is_sleep_time()
    kvlog(logger, logging.INFO, transition='home', check='is_sleep_time', result=sleep_hours)

    if sleep_hours:
        # Arriving home during sleep hours (night)

        # Set Nest to ECO
        try:
            from components.nest import NestAPI

            nest = NestAPI(dry_run=dry_run)

            api_start = time.time()
            nest.set_sleep_mode()  # ECO mode at night
            duration_ms = int((time.time() - api_start) * 1000)

            kvlog(logger, logging.NOTICE, transition='home', device='nest',
                  action='set_sleep', mode='night', result='ok', duration_ms=duration_ms)

            actions.append("Nest → ECO mode (night)")
        except Exception as e:
            kvlog(logger, logging.ERROR, transition='home', device='nest',
                  action='set_sleep', error_type=type(e).__name__, error_msg=str(e))
            errors.append(f"Nest: {type(e).__name__}")
            actions.append(f"✗ Nest failed")

        # Set Sensibo to sleep mode (66°F)
        try:
            from components.sensibo import SensiboAPI

            sensibo = SensiboAPI(dry_run=dry_run)

            api_start = time.time()
            sensibo.set_sleep_mode()
            duration_ms = int((time.time() - api_start) * 1000)

            kvlog(logger, logging.NOTICE, transition='home', device='sensibo',
                  action='set_sleep', mode='night', result='ok', duration_ms=duration_ms)

            actions.append("Sensibo → 66°F (night)")
        except Exception as e:
            kvlog(logger, logging.ERROR, transition='home', device='sensibo',
                  action='set_sleep', error_type=type(e).__name__, error_msg=str(e))
            errors.append(f"Sensibo: {type(e).__name__}")
            actions.append(f"✗ Sensibo failed")

    else:
        # Arriving home during awake hours (day)
        comfort_temp = get('temperatures.comfort', 70)

        # Set Nest to comfort mode
        try:
            from components.nest import NestAPI

            nest = NestAPI(dry_run=dry_run)

            api_start = time.time()
            nest.set_comfort_mode()
            duration_ms = int((time.time() - api_start) * 1000)

            kvlog(logger, logging.NOTICE, transition='home', device='nest',
                  action='set_comfort', mode='day', result='ok', duration_ms=duration_ms)

            actions.append(f"Nest → {comfort_temp}°F HEAT")
        except Exception as e:
            kvlog(logger, logging.ERROR, transition='home', device='nest',
                  action='set_comfort', error_type=type(e).__name__, error_msg=str(e))
            errors.append(f"Nest: {type(e).__name__}")
            actions.append(f"✗ Nest failed")

        # Set Sensibo to comfort mode
        try:
            from components.sensibo import SensiboAPI

            sensibo = SensiboAPI(dry_run=dry_run)

            api_start = time.time()
            sensibo.set_comfort_mode()
            duration_ms = int((time.time() - api_start) * 1000)

            kvlog(logger, logging.NOTICE, transition='home', device='sensibo',
                  action='set_comfort', mode='day', result='ok', duration_ms=duration_ms)

            actions.append(f"Sensibo → {comfort_temp}°F HEAT")
        except Exception as e:
            kvlog(logger, logging.ERROR, transition='home', device='sensibo',
                  action='set_comfort', error_type=type(e).__name__, error_msg=str(e))
            errors.append(f"Sensibo: {type(e).__name__}")
            actions.append(f"✗ Sensibo failed")

    # 2. Send ONE macro notification (if requested)
    if send_notification:
        try:
            if not dry_run:
                from lib.notifications import send_automation_summary

                if sleep_hours:
                    title = "🏠 Home Transition (Night)"
                else:
                    title = "🏠 Home Transition"

                if errors:
                    title += " (Partial)"

                notification_body = actions
                if errors:
                    notification_body.extend([f"✗ {e}" for e in errors])

                priority = 1 if errors else 0

                send_automation_summary(title, notification_body, priority=priority)

                kvlog(logger, logging.INFO, transition='home', action='notification', result='sent')
            else:
                kvlog(logger, logging.DEBUG, transition='home', action='notification', result='skipped_dry_run')
        except Exception as e:
            kvlog(logger, logging.ERROR, transition='home', action='notification',
                  error_type=type(e).__name__, error_msg=str(e))
            errors.append(f"Notification: {type(e).__name__}")
    else:
        kvlog(logger, logging.DEBUG, transition='home', action='notification', result='skipped_by_caller')

    # Determine final status
    if not actions:
        status = 'failed'
    elif errors:
        status = 'partial'
    else:
        status = 'success'

    duration_ms = int((time.time() - start_time) * 1000)
    kvlog(logger, logging.NOTICE, transition='home', event='complete',
          status=status, actions_count=len(actions), errors_count=len(errors), duration_ms=duration_ms)

    return {
        'transition': 'home',
        'status': status,
        'actions': actions,
        'errors': errors,
        'duration_ms': duration_ms
    }


__all__ = [
    'is_sleep_time',
    'transition_to_wake',
    'transition_to_sleep',
    'transition_to_away',
    'transition_to_home'
]
