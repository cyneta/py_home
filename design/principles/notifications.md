# Design Principle: Notifications Are for Emergencies Only

**Date:** 2025-10-18
**Status:** Established
**Applies to:** All notification usage (ntfy, Pushover, etc.)

## Principle

Notifications to the user's phone are **reserved for emergencies and errors only**.

Routine events do NOT send notifications. Use logs and dashboard for routine status monitoring.

## Rationale

**User already knows when routine events happen:**
- User knows when they arrive home (they drove there)
- User knows when lights turn on (they can see them)
- User knows when scheduled routines run (they set the schedule)

**Notifications should signal exceptional conditions:**
- Something went wrong (error, failure)
- Something requires immediate attention (freeze risk, leak)
- Something unexpected happened (sensor offline)

**Too many notifications = notification fatigue:**
- User ignores all notifications
- Critical alerts get missed
- System becomes annoying instead of helpful

## When to Send Notifications

### ✅ Send Notifications For:

**Emergency Conditions:**
- ❄️ Pipe freeze risk (< 50°F)
- 💧 High humidity / potential leak (> 65%)
- 🔥 Fire/smoke detection (if implemented)
- 🚨 Carbon monoxide detection (if implemented)
- ⚡ Power outage (if implemented)

**Equipment Failures:**
- 📡 Sensor offline or not responding
- 🔋 Battery critically low (< 20%)
- ⚠️ API failures (can't control devices)
- ❌ Device unreachable

**Automation Errors:**
- Lights failed to turn on during arrival
- HVAC failed to set temperature
- Outlet failed to respond
- Any exception/error in automation execution

### ❌ DO NOT Send Notifications For:

**Routine Events:**
- ~~Arriving home~~
- ~~Leaving home~~
- ~~Good morning routine completed~~
- ~~Goodnight routine completed~~
- ~~Scheduled temperature changes~~
- ~~Lights turned on/off normally~~

**Status Updates:**
- ~~Device turned on successfully~~
- ~~Temperature reached target~~
- ~~Sensor reading normal~~
- ~~Daily health checks passing~~

**Debug Information:**
- ~~Script execution started~~
- ~~API call succeeded~~
- ~~State file updated~~
- ~~Configuration loaded~~

**Temporary Debug Notifications:**
- Add `send()` calls as needed during development
- Remove before committing to main branch
- Use logs for permanent debug output

## Implementation Patterns

### Correct Pattern: Error-Only Notifications

```python
# automations/im_home.py

def run():
    actions = []
    errors = []

    # Execute automation
    try:
        turn_on_lights()
        actions.append("Lights on")
    except Exception as e:
        errors.append(f"Lights failed: {e}")

    # Only notify if errors occurred
    if errors:
        from lib.notifications import send_automation_summary
        send_automation_summary("⚠️ Arrival Error", actions, priority=1)

    # No notification on success - routine event
```

### Correct Pattern: Emergency Monitoring

```python
# automations/tempstick_monitor.py

def check_pipe_freeze_risk(temp_f, room):
    if temp_f < PIPE_FREEZE_TEMP:
        # Rate-limited emergency alert
        if should_send_alert('pipe_freeze', room, cooldown_minutes=60):
            send_automation_summary(
                f"❄️ {room} Cold ({temp_f:.1f}°F)",
                ["Pipe freeze risk", "Check heating system"],
                priority=2  # Urgent
            )
            record_alert_sent('pipe_freeze', room)
        return True
    return False
```

### Incorrect Pattern: Routine Notifications

```python
# DON'T DO THIS:

def run():
    turn_on_lights()
    set_temperature()

    # ❌ Don't notify on routine success
    send_automation_summary(
        "🏡 Welcome Home!",
        ["Lights on", "Temp set to 70°F"],
        priority=0
    )
```

**Why this is wrong:**
- User already knows they're home (they drove there)
- User can see lights turned on
- User can check dashboard for status
- Creates notification fatigue

## Alert Rate Limiting

Even emergency alerts should be rate-limited to avoid spam:

```python
# Example: Pipe freeze alert max once per hour
if should_send_alert('pipe_freeze', room, cooldown_minutes=60):
    send_automation_summary(...)
    record_alert_sent('pipe_freeze', room)
else:
    logger.info("Alert suppressed (cooldown): Pipe freeze risk")
```

**Rationale:**
- If temp is 48°F, user gets one alert
- User investigates, sees alert, takes action (or doesn't)
- Don't spam user every 15 minutes while they're handling it
- Next alert sent after cooldown expires (or temp recovers)

## Priority Levels

Use appropriate priority for severity:

| Priority | Level | When to Use | Example |
|----------|-------|-------------|---------|
| 1 | Urgent | Immediate action required | Pipe freeze (<50°F), very high humidity (>70%), sensor offline, automation errors |
| 0 | Info | Informational, no urgency | *(Generally avoid - use logs instead per design principle)* |

**General rule:** If using priority 0, ask yourself if a notification is needed at all. Use logs instead.

## Examples

### Example 1: Arrival Automation

**Scenario:** User arrives home, lights turn on successfully.

**Correct behavior:**
```python
# Turn on lights
tapo.turn_on("Livingroom Lamp")

# Log success
logger.info("Indoor lights on")

# NO notification - routine event
```

**User experience:**
- Lights turn on (user sees this happen)
- Check dashboard if curious about details
- No unnecessary phone notification

### Example 2: Arrival with Error

**Scenario:** User arrives home, lights fail to turn on.

**Correct behavior:**
```python
try:
    tapo.turn_on("Livingroom Lamp")
    logger.info("Indoor lights on")
except Exception as e:
    logger.error(f"Lights failed: {e}")
    errors.append(f"Lights: {e}")

# Notify user of failure
if errors:
    send_automation_summary("⚠️ Arrival Error", errors, priority=1)
```

**User experience:**
- User arrives, lights don't turn on (user notices)
- Gets notification explaining what failed
- Can manually turn on lights or investigate

### Example 3: Temperature Monitoring

**Scenario:** Outdoor sensor reports 48°F (pipe freeze risk).

**Correct behavior:**
```python
if temp_f < PIPE_FREEZE_TEMP:
    # This is an emergency - immediate attention needed
    send_automation_summary(
        f"❄️ Crawlspace Cold ({temp_f:.1f}°F)",
        ["Pipe freeze risk", "Check heating system"],
        priority=1  # Urgent
    )
```

**User experience:**
- Gets urgent alert about freeze risk
- Can take action (turn on heat, open cabinet doors, etc.)
- Alert warranted - user wouldn't know without sensor

### Example 4: Scheduled Wake Transition

**Scenario:** Scheduler runs wake transition at 5:00am.

**Correct behavior:**
```python
# Execute transition
transition_to_wake()

# Log completion
logger.notice("Wake transition complete")

# NO notification - scheduled event
```

**User experience:**
- Temperature changes to comfort mode
- Grow light turns on
- User sees/feels these changes happen
- No unnecessary notification waking them up

## Notification Content Guidelines

When you DO send a notification, make it useful:

### Good Notification Format:

```
Title: ❄️ Crawlspace Cold (48.3°F)
Body:
→ Pipe freeze risk
→ Check heating system
```

**Why this is good:**
- Emoji for quick visual scan
- Specific temperature in title
- Action items in body
- User knows exactly what to do

### Bad Notification Format:

```
Title: Alert
Body: Temperature threshold exceeded
```

**Why this is bad:**
- Generic title (which alert?)
- No specific values (how cold?)
- No action guidance (what should I do?)
- User confused and annoyed

## Debug Notifications

**During development, temporary debug notifications are acceptable:**

```python
# Debugging a timing issue
send("Pre-arrival triggered, starting HVAC", priority=0)

# ... test the timing ...

# Remove before committing to main
```

**Rules:**
1. Add `send()` calls as needed during development
2. Use priority 0 (info)
3. Add comment: `# DEBUG - remove before commit`
4. Remove before merging to main branch
5. For permanent debug info, use logs instead

## Related Principles

- **User control** - Don't notify user about things they initiated
- **Fail loudly** - Do notify user when things go wrong
- **Predictable behavior** - User expects alerts for emergencies, not routine events
- **Minimal surprise** - Unexpected notifications are annoying

## Comparison to Other Systems

### Systems That Get This Wrong:

**Smart home apps with excessive notifications:**
- "Bedroom light turned on" ← User just flipped the switch, they know
- "Front door locked" ← User just locked it, they know
- "Temperature set to 70°F" ← User just adjusted thermostat, they know

**Result:** User disables all notifications, misses important alerts

### Systems That Get This Right:

**Security systems:**
- No notification when armed/disarmed by user
- Notification when triggered by motion sensor
- Notification when battery low on sensor

**Battery monitoring:**
- No notification when battery healthy
- Notification at 20%, 10%, 5% (rate-limited)
- Notification when charging complete (optional)

**Our approach:**
- Silent routine operations
- Alert on emergencies and errors only
- User trusts notifications are important

## User Configuration (Future)

Consider allowing users to configure notification preferences:

```yaml
# config.yaml (future enhancement)
notifications:
  service: "ntfy"

  # Alert preferences
  alerts:
    pipe_freeze:
      enabled: true
      priority: 2
      cooldown_minutes: 60

    sensor_offline:
      enabled: true
      priority: 1
      cooldown_minutes: 120

    automation_errors:
      enabled: true
      priority: 1
      cooldown_minutes: 0  # No cooldown for errors
```

**Benefits:**
- User can disable specific alert types
- User can adjust priorities
- User can tune cooldown periods

**Decision:** Not implemented yet. Current hardcoded alerts are appropriate for now.

## Testing Notifications

**Use test script for verification:**

```bash
# Test ntfy is working
python scripts/test_ntfy.py

# Verify notifications received on phone
```

**Manual testing:**

```bash
# Temporarily add debug notification
python -c "from lib.notifications import send; send('Test alert', priority=1)"

# Check phone for notification
```

**Don't leave test notifications in production code.**

## Summary

**Core principle:** Notifications are for emergencies and errors only. Routine events are logged, not notified.

**Implementation:** Only call `send()` or `send_automation_summary()` for:
1. Emergency conditions (freeze risk, leaks, etc.)
2. Equipment failures (sensor offline, low battery)
3. Automation errors (lights failed, HVAC error)

**User benefit:** Notifications are trusted signals that require attention. No notification fatigue.

**Related:** See `docs/NOTIFICATIONS.md` for setup guide and service configuration.
