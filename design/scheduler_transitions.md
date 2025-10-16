# Scheduler & Transitions Architecture

**Date:** 2025-10-16
**Status:** Design Approved, Not Implemented
**Purpose:** Replace temp_coordination.py with cleaner time-based automation

## Overview

This design introduces two interconnected modules:
1. **lib/transitions.py** - Defines what happens during state changes
2. **automations/scheduler.py** - Triggers time-based state changes

### Key Principle
ONE scheduler handles ALL component actions for time-based events.
The system respects user manual adjustments between scheduled transitions.

## Architecture

### Component Responsibilities

**lib/transitions.py (Smart Orchestrator)**
- Defines complete state transitions
- Controls ALL components (HVAC, lights, outlets, etc.)
- Fetches and uses external data (weather)
- Makes conditional decisions based on context
- Sends ONE macro notification per transition
- Returns structured results

**automations/scheduler.py (Time Trigger)**
- ONLY handles time-based events
- Runs every minute via cron
- Checks if current time matches configured transition times
- Calls appropriate transition
- Tracks state to prevent duplicates (once per day per transition)
- Does NOT handle location or manual triggers

**Automation Scripts (Thin Orchestrators)**
- goodnight.py, good_morning.py, leaving_home.py, pre_arrival.py
- Call appropriate transition
- Add unique per-automation logic (weather brief, presence state updates)
- Send additional notifications if needed

**Component APIs (Dumb Executors)**
- nest.py, sensibo.py, tapo.py, etc.
- Execute commands as told
- Log actions at DEBUG/INFO level
- Do NOT send user notifications

## The Four Transitions

### 1. transition_to_wake()

**Triggered by:**
- Scheduler at 05:00
- Manual: good_morning.py (iOS Shortcut "Good Morning")

**Actions:**
1. Fetch current weather
2. Determine target temperature:
   - < 40°F outside → 72°F (extra warmth)
   - > 75°F outside → 68°F (lighter)
   - 40-75°F → 70°F (normal)
3. Set Nest to comfort mode (calculated temp)
4. Set Sensibo to comfort mode (calculated temp)
5. Turn ON grow light
6. Send notification with weather + actions

**Notification Example:**
```
☀️ Wake Transition
47°F outside - Extra warmth mode
✓ Nest → 72°F HEAT
✓ Sensibo → 72°F HEAT
✓ Grow light → ON
```

**Returns:**
```python
{
    'transition': 'wake',
    'status': 'success' | 'partial' | 'failed',
    'actions': ['Nest → 72°F', 'Sensibo → 72°F', 'Grow light ON'],
    'errors': [],
    'duration_ms': 2341,
    'weather': {'temp': 47, 'condition': 'clear'}
}
```

### 2. transition_to_sleep()

**Triggered by:**
- Scheduler at 22:30
- Manual: goodnight.py (iOS Shortcut "Goodnight")

**Actions:**
1. Set Nest to ECO mode (energy saving)
2. Set Sensibo to sleep mode (66°F)
3. Turn OFF grow light
4. Turn OFF all Tapo outlets
5. Send notification with actions

**Design Decision:** Scheduled 22:30 DOES turn off outlets. If user is still awake, they manually turn outlets back on. System doesn't second-guess user.

**Notification Example:**
```
💤 Sleep Transition
✓ Nest → ECO mode
✓ Sensibo → 66°F
✓ Grow light → OFF
✓ All outlets → OFF
```

**Returns:**
```python
{
    'transition': 'sleep',
    'status': 'success' | 'partial' | 'failed',
    'actions': ['Nest ECO', 'Sensibo 66°F', 'Grow OFF', 'Outlets OFF'],
    'errors': [],
    'duration_ms': 3120
}
```

### 3. transition_to_away()

**Triggered by:**
- Manual: leaving_home.py (iOS Shortcut "Leaving Home")
- NOT triggered by scheduler (location event, not time event)

**Actions:**
1. Set Nest to away/ECO mode
2. Set Sensibo to away mode (OFF)
3. Turn OFF all Tapo outlets
4. Grow light: NO CHANGE (plants need consistent schedule)
5. Send notification

**Note:** Presence state update handled by leaving_home.py caller, not transition.

**Notification Example:**
```
🚗 Away Transition
✓ Nest → ECO mode
✓ Sensibo → OFF
✓ All outlets → OFF
ℹ️ Grow light unchanged (plant schedule)
```

### 4. transition_to_home()

**Triggered by:**
- Manual: pre_arrival.py (iOS Shortcut/geofence)
- NOT triggered by scheduler (location event, not time event)

**Actions:**
1. Check current time via is_sleep_time()
2. If sleep hours (22:30-05:00):
   - Set Nest to ECO
   - Set Sensibo to sleep mode (66°F)
3. If awake hours:
   - Set Nest to comfort mode (70°F)
   - Set Sensibo to comfort mode (70°F)
4. Send notification

**Note:** Outdoor lights and presence state handled by pre_arrival.py caller, not transition.

**Notification Example (awake hours):**
```
🏠 Home Transition
✓ Nest → 70°F HEAT
✓ Sensibo → 70°F HEAT
```

**Notification Example (sleep hours):**
```
🏠 Home Transition (Night)
✓ Nest → ECO mode
✓ Sensibo → 66°F
```

## Weather Integration

### How Transitions Access Weather

```python
# In lib/transitions.py
from services.openweather import get_current_weather

def transition_to_wake(dry_run=False):
    try:
        weather = get_current_weather()
        temp = weather['temp']
        condition = weather['condition']
    except Exception as e:
        logger.warning(f"Weather unavailable: {e}")
        temp = None  # Fallback to config defaults
        condition = "unknown"

    # Use weather for decisions
    if temp and temp < 40:
        target_temp = 72
        mode_note = "Extra warmth mode"
    elif temp and temp > 75:
        target_temp = 68
        mode_note = "Light mode"
    else:
        target_temp = get('temperatures.comfort', 70)
        mode_note = "Normal mode"

    # Apply to devices...
    nest.set_comfort_mode(temp_override=target_temp)

    # Include in notification
    notification = f"☀️ Wake Transition\n{temp}°F outside - {mode_note}\n..."
```

### Weather-Aware Behaviors

**Wake transition:**
- Cold morning (< 40°F) → Extra warmth (72°F)
- Hot morning (> 75°F) → Lighter (68°F)
- Include weather in notification

**Sleep transition:**
- Currently no weather adjustments (could add if needed)

**Home transition:**
- Could pre-cool on hot days (future enhancement)

**Weather failure:**
- Graceful fallback to config.yaml defaults
- Log warning but continue
- Notification notes "Weather unavailable"

## Scheduler Logic

### Precise Time Matching

```python
def should_transition_to_wake():
    """Check if current time matches wake time and haven't transitioned today"""
    from datetime import datetime

    now = datetime.now()
    wake_time = get('schedule.wake_time', '05:00')  # From config.yaml
    hour, minute = map(int, wake_time.split(':'))

    # Exact time match (within same minute)
    time_matches = now.hour == hour and now.minute == minute

    # Already transitioned today?
    already_done = already_ran_today('wake')

    return time_matches and not already_done

def should_transition_to_sleep():
    """Check if current time matches sleep time and haven't transitioned today"""
    from datetime import datetime

    now = datetime.now()
    sleep_time = get('schedule.sleep_time', '22:30')  # From config.yaml
    hour, minute = map(int, sleep_time.split(':'))

    # Exact time match (within same minute)
    time_matches = now.hour == hour and now.minute == minute

    # Already transitioned today?
    already_done = already_ran_today('sleep')

    return time_matches and not already_done
```

### State Tracking

**File:** `.scheduler_state` (JSON)
```json
{
  "last_wake_date": "2025-10-16",
  "last_sleep_date": "2025-10-16"
}
```

**Purpose:** Prevent duplicate transitions if scheduler runs multiple times during the target minute (safety mechanism).

**Logic:**
- Before transition: Check if already ran today
- After transition: Update state file with today's date
- Next day: Date changes, transitions allowed again

### Main Scheduler Loop

```python
#!/usr/bin/env python
"""
Scheduler - Time-based transition trigger

Runs every minute via cron.
Checks current time against configured schedule times.
Triggers appropriate transitions when time matches.

Usage:
    python automations/scheduler.py
"""

import logging
import time
from datetime import datetime
from lib.logging_config import setup_logging, kvlog
from lib.config import get
from lib.transitions import transition_to_wake, transition_to_sleep

logger = logging.getLogger(__name__)

def run():
    """Check time and trigger transitions if needed"""
    start_time = time.time()

    # Check wake transition
    if should_transition_to_wake():
        kvlog(logger, logging.NOTICE, automation='scheduler',
              event='wake_time', action='triggering_wake_transition')

        result = transition_to_wake()

        kvlog(logger, logging.NOTICE, automation='scheduler',
              transition='wake', status=result['status'],
              actions_count=len(result['actions']),
              errors_count=len(result['errors']))

        mark_completed('wake')

    # Check sleep transition
    elif should_transition_to_sleep():
        kvlog(logger, logging.NOTICE, automation='scheduler',
              event='sleep_time', action='triggering_sleep_transition')

        result = transition_to_sleep()

        kvlog(logger, logging.NOTICE, automation='scheduler',
              transition='sleep', status=result['status'],
              actions_count=len(result['actions']),
              errors_count=len(result['errors']))

        mark_completed('sleep')

    # Most runs will be no-ops (not matching any transition time)
    duration_ms = int((time.time() - start_time) * 1000)
    # Only log at DEBUG level for no-op runs to avoid log spam
    if duration_ms > 100:  # Only log if we did something
        kvlog(logger, logging.INFO, automation='scheduler',
              event='complete', duration_ms=duration_ms)

if __name__ == '__main__':
    setup_logging()
    run()
```

### Cron Schedule

```bash
# Run every minute - checks time against config.yaml schedule
* * * * * cd /home/matt.wheeler/py_home && /home/matt.wheeler/py_home/venv/bin/python automations/scheduler.py >> /home/matt.wheeler/py_home/data/logs/automations.log 2>&1
```

**Why every minute?**
- **Precision:** Transitions happen within 1 minute of configured time
- **Self-documenting:** Schedule times visible in config.yaml, not hidden in crontab
- **Flexible:** Change times by editing config, no SSH to modify crontab
- **Extensible:** Add new time-based transitions in code only
- **Efficient:** Most runs are quick no-ops (~1ms), only log when action taken

**Timing precision:**
- 05:00 in config → Transition happens during 05:00:xx minute
- 22:30 in config → Transition happens during 22:30:xx minute
- Within 60 seconds of target time (acceptable for home automation)

## Notification Strategy

### Problem
Current system: Too many notifications (one per device = 5+ notifications per automation)

### Solution
Each transition sends ONE macro notification summarizing all actions.

**Components:**
- Still log actions (DEBUG/INFO level)
- Do NOT send user notifications

**Transitions:**
- Send ONE notification with all actions
- Include context (weather, time, mode)
- Use emoji for visual recognition
- List all successful actions
- Note any failures

**Example flow:**
```
scheduler.py (05:00) calls transition_to_wake()
  → transition fetches weather (47°F)
  → transition calculates target (72°F)
  → transition controls: Nest → 72°F, Sensibo → 72°F, Grow light ON
  → transition sends: "☀️ Wake: 47°F Extra warmth, Nest 72°F, Sensibo 72°F, Grow ON"
  → transition returns result dict
scheduler.py logs result summary, exits
```

**User sees:** 1 notification
**Logs contain:** Detailed component actions for debugging

### Notification Content Design

**Components of macro notification:**
1. **Emoji + Title** - Visual identification (☀️ Wake, 💤 Sleep, 🚗 Away, 🏠 Home)
2. **Context line** - Weather, time info, or mode
3. **Action list** - Checkmark for each successful action
4. **Errors (if any)** - X mark for failures

**Example with partial failure:**
```
💤 Sleep Transition (Partial)
✓ Nest → ECO mode
✗ Sensibo: Connection timeout
✓ Grow light → OFF
✓ Outlets → OFF
```

## Error Handling

### Per-Device Try/Catch

Each device action wrapped independently so one failure doesn't stop others:

```python
def transition_to_wake(dry_run=False):
    errors = []
    actions = []
    weather_info = None

    # Weather (non-critical)
    try:
        weather = get_current_weather()
        temp = weather['temp']
        weather_info = f"{temp}°F outside"

        if temp < 40:
            target = 72
        elif temp > 75:
            target = 68
        else:
            target = 70
    except Exception as e:
        logger.warning(f"Weather unavailable: {e}")
        target = get('temperatures.comfort', 70)
        weather_info = "Weather unavailable"

    # Device 1: Nest
    try:
        nest = NestAPI(dry_run=dry_run)
        nest.set_comfort_mode(temp_override=target)
        actions.append(f"Nest → {target}°F")
    except Exception as e:
        logger.error(f"Nest failed: {e}")
        errors.append(f"Nest: {e}")

    # Device 2: Sensibo (continues even if Nest failed)
    try:
        sensibo = SensiboAPI(dry_run=dry_run)
        sensibo.set_comfort_mode(temp_override=target)
        actions.append(f"Sensibo → {target}°F")
    except Exception as e:
        logger.error(f"Sensibo failed: {e}")
        errors.append(f"Sensibo: {e}")

    # Device 3: Grow light (continues even if HVAC failed)
    try:
        # Future: grow_light.turn_on()
        actions.append("Grow light → ON")
    except Exception as e:
        logger.error(f"Grow light failed: {e}")
        errors.append(f"Grow light: {e}")

    # Send notification (even if some actions failed)
    notification_title = "☀️ Wake Transition"
    if errors:
        notification_title += " (Partial)"

    notification_body = [weather_info] + actions
    if errors:
        notification_body.extend([f"✗ {e}" for e in errors])

    send_notification(notification_title, "\n".join(notification_body))

    return {
        'transition': 'wake',
        'status': 'success' if not errors else ('partial' if actions else 'failed'),
        'actions': actions,
        'errors': errors,
        'weather': weather_info,
        'duration_ms': int((time.time() - start_time) * 1000)
    }
```

### Status Levels
- **success:** All actions completed without errors
- **partial:** Some actions succeeded, some failed
- **failed:** All actions failed (rare, means all devices unreachable)

### Logging Strategy
- **INFO:** Routine actions (checking time, fetching weather)
- **NOTICE:** Important events (transition triggered, actions taken)
- **ERROR:** Failures (device unreachable, API error)

## Data Flow Diagrams

### Scheduled Wake Transition (05:00)
```
Cron triggers every minute
  ...
  04:59:xx → scheduler.py
    → Check time matches 05:00? → NO
    → Exit (no-op, ~1ms)

  05:00:xx → scheduler.py
    → Check time matches 05:00? → YES
    → Check already ran today? → NO (check .scheduler_state)
    → Call transition_to_wake()
      → Fetch weather from OpenWeather API
        → temp = 47°F
      → Calculate target temp
        → 47 < 40? NO
        → 47 > 75? NO
        → target = 70°F (normal)
      → Control Nest
        → nest.set_comfort_mode(temp_override=70)
        → Success → Add "Nest → 70°F" to actions
      → Control Sensibo
        → sensibo.set_comfort_mode(temp_override=70)
        → Success → Add "Sensibo → 70°F" to actions
      → Control grow light
        → grow_light.turn_on()
        → Success → Add "Grow light ON" to actions
      → Send notification
        → "☀️ Wake: 47°F, Nest 70°F, Sensibo 70°F, Grow ON"
      → Return result dict
    → Mark 'wake' completed in .scheduler_state
      → {"last_wake_date": "2025-10-16"}
    → Log summary
    → Exit
```

### Manual Goodnight (iOS Shortcut)
```
User: "Hey Siri, Goodnight"
  → iOS Shortcut POST to /api/automations/goodnight
    → goodnight.py receives request
      → Check: Automations enabled? → YES
      → Call transition_to_sleep()
        → Control Nest
          → nest.set_sleep_mode()
          → Success → Add "Nest ECO" to actions
        → Control Sensibo
          → sensibo.set_sleep_mode()
          → Success → Add "Sensibo 66°F" to actions
        → Control grow light
          → grow_light.turn_off()
          → Success → Add "Grow OFF" to actions
        → Control outlets
          → tapo.turn_off_all()
          → Success → Add "Outlets OFF" to actions
        → Send notification
          → "💤 Sleep: Nest ECO, Sensibo 66°F, Grow OFF, Outlets OFF"
        → Return result dict
      → goodnight.py returns HTTP 200 with result
    → iOS Shortcut shows success
```

### Scheduled Sleep Transition (22:30)
```
Cron triggers every minute
  ...
  22:29:xx → scheduler.py
    → Check time matches 22:30? → NO
    → Exit (no-op, ~1ms)

  22:30:xx → scheduler.py
    → Check time matches 22:30? → YES
    → Check already ran today? → NO
    → Call transition_to_sleep()
      → [Same actions as manual goodnight above]
    → Mark 'sleep' completed in .scheduler_state
      → {"last_sleep_date": "2025-10-16"}
    → Log summary
    → Exit
```

## Configuration

### Existing config.yaml (no changes needed)
```yaml
schedule:
  sleep_time: "22:30"      # When sleep transition triggers
  wake_time: "05:00"       # When wake transition triggers

temperatures:
  comfort: 70              # Default comfort temp (fallback if no weather)
  bedroom_sleep: 66        # Sensibo sleep mode target

# Future: Could add weather thresholds to config if needed
# weather:
#   cold_threshold: 40
#   hot_threshold: 75
```

### Runtime State Files

**.scheduler_state** (JSON, created automatically)
```json
{
  "last_wake_date": "2025-10-16",
  "last_sleep_date": "2025-10-16"
}
```

**.presence_state** (plain text, managed by location automations)
```
home
```
or
```
away
```

## Testing Strategy

### Unit Tests (pytest)

**Test transitions in isolation:**
```python
def test_transition_to_wake_cold_weather():
    """Wake transition uses higher temp on cold mornings"""
    with mock.patch('services.openweather.get_current_weather') as mock_weather:
        mock_weather.return_value = {'temp': 35, 'condition': 'clear'}

        with mock.patch('components.nest.NestAPI') as mock_nest:
            result = transition_to_wake(dry_run=True)

            # Should use 72°F (extra warmth)
            mock_nest().set_comfort_mode.assert_called_with(temp_override=72)
            assert result['status'] == 'success'

def test_transition_to_sleep_partial_failure():
    """Sleep transition continues even if one device fails"""
    with mock.patch('components.nest.NestAPI') as mock_nest:
        mock_nest().set_sleep_mode.side_effect = Exception("Nest offline")

        with mock.patch('components.sensibo.SensiboAPI') as mock_sensibo:
            result = transition_to_sleep(dry_run=True)

            # Should mark as partial, not failed
            assert result['status'] == 'partial'
            assert len(result['errors']) == 1
            assert len(result['actions']) > 0  # Other devices succeeded
```

**Test scheduler logic:**
```python
def test_should_transition_to_wake():
    """Scheduler detects wake window correctly"""
    with mock.patch('datetime.datetime') as mock_dt:
        # 05:10 on 2025-10-16
        mock_dt.now.return_value = datetime(2025, 10, 16, 5, 10)

        # Haven't run yet today
        with mock.patch('os.path.exists', return_value=False):
            assert should_transition_to_wake() == True

def test_no_duplicate_transition():
    """Scheduler prevents duplicate transitions same day"""
    with mock.patch('datetime.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2025, 10, 16, 5, 10)

        # Already ran today
        with mock.patch('builtins.open', mock_open(read_data='{"last_wake_date": "2025-10-16"}')):
            assert should_transition_to_wake() == False
```

### Integration Tests

**Test end-to-end flow:**
- Call goodnight.py via HTTP endpoint
- Verify Nest API receives set_sleep_mode()
- Verify Sensibo API receives set_sleep_mode()
- Verify notification sent
- Verify return status

**Test with real weather API:**
- Call transition_to_wake() with real OpenWeather
- Verify graceful fallback if API fails
- Verify temp calculation based on real weather

### Manual Tests

**iOS Shortcuts:**
- Test "Goodnight" shortcut → Verify transition_to_sleep() actions
- Test "Good Morning" shortcut → Verify transition_to_wake() actions
- Test "Leaving Home" shortcut → Verify transition_to_away() actions
- Test "I'm Home" shortcut → Verify transition_to_home() actions

**Scheduled transitions:**
- Wait for 05:00 cron run → Verify wake transition
- Wait for 22:30 cron run → Verify sleep transition
- Check logs for proper execution
- Verify no duplicate runs at 05:15, 22:45

**State tracking:**
- Manually trigger wake transition twice in same day
- Verify second call is prevented by state file

## Rollback Plan

If issues arise after deployment:

### Step 1: Disable Scheduler
```bash
# SSH to Pi
ssh matt.wheeler@100.107.121.6

# Comment out scheduler cron job
crontab -e
# Add # in front of scheduler.py line

# Or remove entirely
crontab -l | grep -v scheduler.py | crontab -
```

### Step 2: System Continues via Manual Triggers
- iOS Shortcuts (goodnight, good_morning, etc.) still work
- They call transitions directly
- No scheduled automation, but manual control intact

### Step 3: Investigate and Fix
- Review logs: `tail -f data/logs/automations.log`
- Check errors: `grep ERROR data/logs/automations.log`
- Test transition in dry-run: `python -c "from lib.transitions import *; transition_to_wake(dry_run=True)"`
- Fix issue

### Step 4: Re-enable
```bash
# Restore cron job
crontab -e
# Uncomment scheduler.py line

# Verify
crontab -l | grep scheduler
```

### Emergency Rollback to Manual Only
If transitions module itself has issues:
1. Revert goodnight.py, good_morning.py, etc. to previous versions (git history)
2. Each automation controls devices directly again
3. No centralized transitions, but everything still works

**Advantage of this design:** Transitions and scheduler can be fixed independently. Manual triggers can bypass scheduler entirely.

## Related Design Principles

See: [design/principles/user_control.md](./principles/user_control.md)

## Future Enhancements

### Near-term (1-3 months)
1. Implement grow light control in transitions
2. Add more weather-aware behaviors (rain → different lighting)
3. Add calendar integration (skip wake on holidays)

### Mid-term (3-6 months)
4. Vacation mode (disable scheduler, keep manual triggers)
5. Progressive wake (gradual lighting, temp increase)
6. Adaptive scheduling (learn user patterns, adjust times)

### Long-term (6+ months)
7. Multi-user support (different schedules per person)
8. Voice feedback ("Goodnight transition complete")
9. Home/Away auto-detection via phone location

## Implementation Timeline

**Phase 1: Transitions Module (3-4 hours)**
- Create lib/transitions.py
- Implement all 4 transitions with weather integration
- Unit tests

**Phase 2: Scheduler (2-3 hours)**
- Create automations/scheduler.py
- Implement time detection and state tracking
- Unit tests

**Phase 3: Refactor Automations (3-4 hours)**
- Update goodnight.py, good_morning.py, leaving_home.py, pre_arrival.py
- Integration tests
- Manual testing via iOS Shortcuts

**Phase 4: Deployment (1-2 hours)**
- Update DEPLOYMENT.md
- Deploy to Pi
- Add cron job
- Monitor for 24 hours

**Phase 5: Cleanup (2-3 hours)**
- Remove duplicate HVAC code
- Search for temp_coordination references
- Audit old state files
- Update documentation

**Total estimated: 11-16 hours**

## Open Questions

1. Should transitions check automation master switch, or should caller check?
   - Current: Caller checks (goodnight.py checks before calling transition)
   - Alternative: Transition checks internally

2. Should we send notification on scheduler-triggered transitions?
   - Current design: Yes (same notification as manual triggers)
   - Alternative: Silent scheduled transitions, notification only on manual

3. Should grow light respect vacation mode or always run on schedule?
   - Current: Always run (plants need consistency)
   - Future: Add vacation mode flag

4. Should we add rate limiting for transitions (e.g., max once per hour)?
   - Probably not needed (state file prevents duplicates)
   - Manual triggers should always work

## References

- Original discussion: Session 2025-10-16
- Related cleanup plan: plans/scheduler_cleanup_audit.md
- Related deprecated module: automations/temp_coordination.py (deleted)
- Decision record: status/decisions/temp_coordination_disabled.md
