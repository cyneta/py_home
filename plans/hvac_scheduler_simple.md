# HVAC Scheduler - Simple Implementation

**Date:** 2025-10-16
**Status:** Planning
**Replaces:** scheduler_implementation.md (which conflated scheduler + state machine)

## Overview

Restore time-based HVAC scheduling to replace the deleted temp_coordination.py. This is a **simple, focused solution** that only handles:
- Check time every 15 minutes via cron
- At 05:00 → Set HVAC to comfort mode
- At 22:30 → Set HVAC to sleep mode

**NOT included:** Refactoring existing automations, state machine architecture, or transitions abstraction. Those are separate future considerations.

## Architecture

**Single file:** `automations/hvac_scheduler.py`

**Purpose:** Time-based HVAC control only

**Logic:**
```python
#!/usr/bin/env python
"""
HVAC Scheduler - Time-based HVAC mode changes

Runs every 15 minutes via cron.
Checks current time and triggers appropriate HVAC mode:
- 05:00-05:14 → Comfort mode (wake up)
- 22:30-22:44 → Sleep mode (bedtime)

Does NOT handle:
- Location-based changes (leaving_home.py, pre_arrival.py)
- Manual changes (goodnight.py, good_morning.py)
- Other devices (lights, outlets, etc.)

Usage:
    # Via cron (every 15 min)
    */15 * * * * cd /path && python automations/hvac_scheduler.py

    # Manual test
    python automations/hvac_scheduler.py --dry-run
"""

import logging
import time
from datetime import datetime
from lib.config import get
from lib.logging_config import setup_logging, kvlog

logger = logging.getLogger(__name__)

def should_transition_to_wake():
    """Check if it's time for wake transition (05:00-05:14)"""
    now = datetime.now()
    wake_time = get('schedule.wake_time', '05:00')
    hour, minute = map(int, wake_time.split(':'))

    # Within 15 min window of wake time
    return now.hour == hour and now.minute >= minute and now.minute < minute + 15

def should_transition_to_sleep():
    """Check if it's time for sleep transition (22:30-22:44)"""
    now = datetime.now()
    sleep_time = get('schedule.sleep_time', '22:30')
    hour, minute = map(int, sleep_time.split(':'))

    # Within 15 min window of sleep time
    if minute + 15 >= 60:
        # Wraps to next hour
        return (now.hour == hour and now.minute >= minute) or \
               (now.hour == hour + 1 and now.minute < (minute + 15) % 60)
    else:
        return now.hour == hour and now.minute >= minute and now.minute < minute + 15

def check_already_transitioned(transition_type):
    """Check if we already transitioned today (prevent duplicates)"""
    from pathlib import Path
    import json

    state_file = Path(__file__).parent.parent / '.hvac_scheduler_state'
    today = datetime.now().date().isoformat()

    if not state_file.exists():
        return False

    try:
        with open(state_file, 'r') as f:
            state = json.load(f)
            return state.get(transition_type) == today
    except:
        return False

def mark_transitioned(transition_type):
    """Mark that we transitioned today"""
    from pathlib import Path
    import json

    state_file = Path(__file__).parent.parent / '.hvac_scheduler_state'
    today = datetime.now().date().isoformat()

    # Load existing state
    state = {}
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
        except:
            pass

    # Update
    state[transition_type] = today

    # Save
    with open(state_file, 'w') as f:
        json.dump(state, f)

def run():
    """Main scheduler logic"""
    start_time = time.time()
    kvlog(logger, logging.INFO, automation='hvac_scheduler', event='check')

    # Check if it's wake time
    if should_transition_to_wake():
        if not check_already_transitioned('wake'):
            kvlog(logger, logging.NOTICE, automation='hvac_scheduler',
                  event='wake_time', action='setting_comfort_mode')

            # Set Nest to comfort
            try:
                from components.nest import NestAPI
                nest = NestAPI()
                nest.set_comfort_mode()
                kvlog(logger, logging.NOTICE, automation='hvac_scheduler',
                      device='nest', action='set_comfort', result='ok')
            except Exception as e:
                kvlog(logger, logging.ERROR, automation='hvac_scheduler',
                      device='nest', action='set_comfort',
                      error_type=type(e).__name__, error_msg=str(e))

            # Set Sensibo to comfort
            try:
                from components.sensibo import SensiboAPI
                sensibo = SensiboAPI()
                sensibo.set_comfort_mode()
                kvlog(logger, logging.NOTICE, automation='hvac_scheduler',
                      device='sensibo', action='set_comfort', result='ok')
            except Exception as e:
                kvlog(logger, logging.ERROR, automation='hvac_scheduler',
                      device='sensibo', action='set_comfort',
                      error_type=type(e).__name__, error_msg=str(e))

            mark_transitioned('wake')
        else:
            kvlog(logger, logging.DEBUG, automation='hvac_scheduler',
                  event='wake_time', result='already_transitioned_today')

    # Check if it's sleep time
    elif should_transition_to_sleep():
        if not check_already_transitioned('sleep'):
            kvlog(logger, logging.NOTICE, automation='hvac_scheduler',
                  event='sleep_time', action='setting_sleep_mode')

            # Set Nest to sleep
            try:
                from components.nest import NestAPI
                nest = NestAPI()
                nest.set_sleep_mode()
                kvlog(logger, logging.NOTICE, automation='hvac_scheduler',
                      device='nest', action='set_sleep', result='ok')
            except Exception as e:
                kvlog(logger, logging.ERROR, automation='hvac_scheduler',
                      device='nest', action='set_sleep',
                      error_type=type(e).__name__, error_msg=str(e))

            # Set Sensibo to sleep
            try:
                from components.sensibo import SensiboAPI
                sensibo = SensiboAPI()
                sensibo.set_sleep_mode()
                kvlog(logger, logging.NOTICE, automation='hvac_scheduler',
                      device='sensibo', action='set_sleep', result='ok')
            except Exception as e:
                kvlog(logger, logging.ERROR, automation='hvac_scheduler',
                      device='sensibo', action='set_sleep',
                      error_type=type(e).__name__, error_msg=str(e))

            mark_transitioned('sleep')
        else:
            kvlog(logger, logging.DEBUG, automation='hvac_scheduler',
                  event='sleep_time', result='already_transitioned_today')

    duration_ms = int((time.time() - start_time) * 1000)
    kvlog(logger, logging.INFO, automation='hvac_scheduler',
          event='complete', duration_ms=duration_ms)

if __name__ == '__main__':
    setup_logging()
    run()
```

## Configuration

Uses existing config from `config.yaml`:
- `schedule.wake_time: "05:00"`
- `schedule.sleep_time: "22:30"`
- `temperatures.comfort: 70`
- `temperatures.bedroom_sleep: 66`

No new config needed.

## Implementation Steps

1. **Create automations/hvac_scheduler.py**
   - Copy logic outline above
   - Add dry-run support
   - Add proper error handling
   - Test time window detection logic

2. **Test locally in dry-run**
   - Test at 05:00 (mock time or wait)
   - Test at 22:30 (mock time or wait)
   - Test outside windows (should do nothing)
   - Test duplicate prevention (run twice in same window)

3. **Update DEPLOYMENT.md**
   - Document cron job: `*/15 * * * * hvac_scheduler.py`
   - Explain what it does
   - Note it replaces temp_coordination

4. **Deploy to Pi**
   - Push code
   - Add cron job
   - Monitor logs

5. **Verify over 24 hours**
   - Check 05:00 transition happened
   - Check 22:30 transition happened
   - Check no duplicate transitions
   - Check no errors

## Success Criteria

- [ ] At 05:00, both HVAC units set to comfort mode (70°F)
- [ ] At 22:30, both HVAC units set to sleep mode (Nest ECO, Sensibo 66°F)
- [ ] State tracking prevents duplicate transitions within same day
- [ ] Existing automations (goodnight.py, good_morning.py, etc.) still work unchanged
- [ ] Logs show clear time checks and actions taken
- [ ] Dry-run mode works for testing

## Non-Goals (Future Work)

These are **explicitly NOT part of this implementation**:
- Refactoring existing automations
- Creating transitions abstraction layer
- State machine architecture
- Adding grow light control
- Consolidating duplicate HVAC logic across files

See `plans/state_machine_transitions.md` for future architectural improvements.

## Rollback Plan

If issues arise:
1. Comment out cron job
2. System continues working via manual triggers (iOS Shortcuts)
3. No other automation files were changed, so nothing breaks

## Related Files

**New:**
- automations/hvac_scheduler.py
- .hvac_scheduler_state (runtime state)

**Modified:**
- dev/setup/DEPLOYMENT.md (document cron job)

**Unchanged:**
- All existing automations continue to work as-is
- No refactoring needed

## Estimated Time

~2-3 hours:
- 1 hour: Write hvac_scheduler.py
- 30 min: Test locally
- 30 min: Deploy and verify
- 1 hour: Monitor over time
