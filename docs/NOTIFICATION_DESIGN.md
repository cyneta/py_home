# Notification Design System

## Overview

Standardized notification pattern for py_home automation system using ntfy.sh.

**Goals:**
- One notification per event (not per action)
- Clear event context in title
- Specific actions in multi-line body
- User perspective, not system perspective

---

## System Architecture

### Three-Layer Design

py_home follows a **layered architecture** where notifications are sent only by the **application layer**, not by low-level components.

```
┌─────────────────────────────────────────┐
│   Application Layer (automations/)     │  ← SENDS NOTIFICATIONS
│   - User-triggered automations          │
│   - Monitoring scripts                  │
│   - Alert logic                         │
└─────────────────────────────────────────┘
              ↓ uses
┌─────────────────────────────────────────┐
│   Integration Layer (services/)         │  ← NO NOTIFICATIONS
│   - Third-party APIs                    │     (just returns data)
│   - External services                   │
│   - Data transformations                │
└─────────────────────────────────────────┘
              ↓ uses
┌─────────────────────────────────────────┐
│   Component Layer (components/)         │  ← NO NOTIFICATIONS
│   - Device control APIs                 │     (just logs operations)
│   - Network operations                  │
│   - Low-level device operations         │
└─────────────────────────────────────────┘
```

### Separation of Concerns

**Components** (`components/nest`, `components/tapo`, etc.):
- ✅ **Do:** Provide device control APIs
- ✅ **Do:** Log their operations
- ✅ **Do:** Raise exceptions on errors
- ❌ **Don't:** Send notifications
- ❌ **Don't:** Know about user context

**Services** (`services/tempstick`, `services/openweather`, etc.):
- ✅ **Do:** Fetch data from external APIs
- ✅ **Do:** Transform/parse responses
- ✅ **Do:** Raise exceptions on errors
- ❌ **Don't:** Send notifications
- ❌ **Don't:** Know about automation logic

**Automations** (`automations/leaving_home`, `automations/goodnight`, etc.):
- ✅ **Do:** Orchestrate multiple components
- ✅ **Do:** Send consolidated notifications
- ✅ **Do:** Handle errors and notify user
- ✅ **Do:** Provide user-centric context

**Monitors** (`automations/tempstick_monitor`, `automations/temp_coordination`, etc.):
- ✅ **Do:** Check component/service state
- ✅ **Do:** Send alerts only when action required
- ✅ **Do:** Use rate limiting to avoid spam
- ❌ **Don't:** Notify on "everything is fine"

### Why This Design?

1. **User Experience**: Only notify when user needs to know or take action
2. **Testability**: Components can be tested in isolation without notification system
3. **Reusability**: Same component used by multiple automations with different notification strategies
4. **Flexibility**: Change notification behavior without touching component code
5. **Clarity**: Notification logic centralized in `automations/` folder, easy to find
6. **Separation**: Components focus on device control, automations focus on user experience

### Component Logging Standards

**All components must log consistently** so monitors can detect issues and send appropriate alerts.

**Required logging for all components:**

```python
# SUCCESS - Always log what happened
logger.info(f"Nest temperature set to {temp}°F",
            extra={'component': 'nest', 'action': 'set_temperature', 'value': temp})

# FAILURE - Always log errors with context
logger.error(f"Failed to set Nest temperature: {e}",
             extra={'component': 'nest', 'action': 'set_temperature', 'error': str(e)})

# STATE CHANGE - Log important state changes
logger.info(f"Nest mode changed: {old_mode} → {new_mode}",
            extra={'component': 'nest', 'action': 'mode_change', 'old': old_mode, 'new': new_mode})
```

**Standard log format:**
- Use structured logging with `extra={}` for machine-readable data
- Include: `component`, `action`, relevant values
- Use kvlog helper from `lib.logging_config` when available

**What to log:**
- ✅ Every API call (success/failure)
- ✅ State changes (on/off, temp changes, etc.)
- ✅ Connection errors, timeouts, rate limits
- ✅ Unexpected responses or data
- ❌ Not every read operation (too noisy)
- ❌ Not internal implementation details

**Component health detection:**

Monitors detect issues by analyzing component logs:
- Repeated failures → Alert user
- Device offline (no successful logs) → Alert user
- State stuck (no changes when expected) → Alert user
- Everything working → No notification (just log)

### Example: How It Works

```python
# ❌ BAD: Component sends notifications
# components/nest/client.py
def set_temperature(temp):
    try:
        api_call(temp)
    except Exception as e:
        send("Nest offline!", priority=2)  # Component shouldn't know about notifications
        raise

# ✅ GOOD: Component just controls device and logs
# components/nest/client.py
def set_temperature(temp):
    try:
        api_call(temp)
        logger.info(f"Nest temperature set to {temp}°F")
    except Exception as e:
        logger.error(f"Failed to set Nest temperature: {e}")
        raise  # Let automation handle notification

# ✅ GOOD: Automation orchestrates and notifies
# automations/leaving_home.py
def run():
    actions = []
    errors = []

    try:
        nest.set_temperature(62)
        actions.append("Nest set to 62°F")
    except Exception as e:
        errors.append(f"Nest: {e}")
        actions.append(f"Nest failed: {str(e)[:30]}")

    # Send ONE notification with user-centric context
    send_automation_summary("🚗 Left Home", actions, priority=1 if errors else 0)
```

---

## Format Specification

### Standard Template

```
[Emoji] [Event/State Change]
→ [Action 1]
→ [Action 2]
→ [Action N]
```

**Example:**
```
🚗 Left Home
→ Nest set to 62°F
→ All outlets turned off
→ House secured
```

### Format Rules

| Element | Rule | Example |
|---------|------|---------|
| **Title** | Event from user's perspective | "🚗 Left Home" not "WiFi Disconnected" |
| **Emoji** | Visual category identifier | 🚗 🏡 🌙 ❄️ ⚠️ |
| **Body** | Concrete actions taken | "Nest set to 62°F" not "Updated thermostat" |
| **Bullets** | Arrow prefix for each action | `→ Action description` |
| **Priority** | 0=normal, 1=high/errors | Errors get priority=1 |

---

## Notification Categories

### 1. Presence Changes
**When:** User arrives or leaves home
**Always notify:** Yes

```
🚗 Left Home
→ Nest set to 62°F
→ All outlets turned off
```

```
🏡 Arrived Home
→ Nest set to 68°F
→ Welcome lights on
```

---

### 2. User Commands
**When:** User triggers via Siri, iOS Shortcuts, or manual
**Always notify:** Yes (provides feedback)

```
🌙 Goodnight
→ Nest set to 68°F
→ All lights off
→ AC coordinated
```

```
☀️ Good Morning
→ Nest set to 72°F
→ Bedroom lights on
→ Coffee maker started
```

---

### 3. Critical Alerts
**When:** Safety/security issue detected
**Always notify:** Yes (high priority)

```
❄️ Crawlspace Cold (48°F)
→ Pipe freeze risk
→ Check heating system
```

```
⚠️ Sensor Offline
→ Crawlspace monitor
→ Last seen: 2 hours ago
```

```
💧 High Humidity (72%)
→ Crawlspace
→ Possible leak - check area
```

---

### 4. Automatic Adjustments
**When:** System makes automatic changes
**Notify only if:** Action was taken

```
🌡️ Temperature Adjusted
→ AC turned OFF (Nest at 70°F)
```

**Do NOT notify if:**
- Routine monitoring found nothing
- No action needed
- Everything normal

---

### 5. Errors/Failures
**When:** Automation fails or has errors
**Always notify:** Yes (high priority)

```
🚗 Left Home
→ Nest set to 62°F
→ Outlets failed: Connection timeout
```

---

## Design Principles

### 1. User-Centric Events
✅ **Good:** "🚗 Left Home" (user's perspective)
❌ **Bad:** "WiFi Disconnected" (system's perspective)

✅ **Good:** "🌙 Goodnight" (user's intent)
❌ **Bad:** "Automation Triggered" (system event)

### 2. Actionable Information
✅ **Good:** "→ Nest set to 62°F" (specific value)
❌ **Bad:** "→ Thermostat updated" (vague)

✅ **Good:** "→ All outlets turned off" (clear action)
❌ **Bad:** "→ Power management executed" (jargon)

### 3. Consolidated Actions
✅ **Good:** One notification with 4 actions
❌ **Bad:** 4 separate notifications

✅ **Good:** Automation sends summary at end
❌ **Bad:** Notification per step

### 4. Human-Readable Context
✅ **Good:** "Crawlspace" (location matters for action)
❌ **Bad:** "TS00EMA9JZ" (device ID is meaningless to user)

✅ **Good:** "All outlets turned off" (what happened)
❌ **Bad:** "Tapo devices 192.168.50.135, 192.168.50.143..." (too technical)

**Rule:** Include room/location only when user needs to take physical action there

### 5. Context-Aware Priority

| Priority | When | Effect (ntfy) |
|----------|------|---------------|
| 0 (normal) | Standard events, no errors | Default sound/vibration |
| 1 (high) | Errors, important changes | Higher urgency |
| 2 (urgent) | Critical safety issues | Maximum urgency |

---

## Emoji Guide

| Category | Emoji | Usage |
|----------|-------|-------|
| **Presence** | 🚗 | Leaving home |
| | 🏡 | Arriving home |
| **Time-Based** | 🌙 | Goodnight/bedtime |
| | ☀️ | Good morning/wake |
| **Temperature** | 🌡️ | Temperature adjusted |
| | ❄️ | Cold/freeze risk |
| | 🔥 | Too hot |
| **Alerts** | ⚠️ | Warning |
| | 🚨 | Critical alert |
| | 💧 | Humidity/leak |
| **Devices** | 💡 | Lights |
| | 🔌 | Outlets/power |
| | 📱 | Phone/connectivity |
| **Status** | ✅ | Success |
| | ❌ | Failure |
| **Cleaning** | 🤖 | Roborock vacuum |
| | 🧹 | Cleaning started |

---

## Code Patterns

### Standard Automation Pattern

```python
def run():
    """Execute automation"""
    actions = []
    errors = []

    # Step 1: Execute action
    try:
        nest.set_temperature(62)
        actions.append("Nest set to 62°F")
    except Exception as e:
        errors.append(f"Nest: {e}")
        actions.append(f"Nest failed: {str(e)[:30]}")

    # Step 2: Execute another action
    try:
        tapo.turn_off_all()
        actions.append("All outlets turned off")
    except Exception as e:
        errors.append(f"Tapo: {e}")
        actions.append(f"Outlets failed: {str(e)[:30]}")

    # Send ONE notification at end with all actions
    from lib.notifications import send_automation_summary

    title = "🚗 Left Home"
    priority = 1 if errors else 0  # High priority if errors

    send_automation_summary(title, actions, priority=priority)
```

---

### Monitoring Script Pattern

```python
def check_condition():
    """Monitor for issues"""

    # Check condition
    if temp < FREEZE_THRESHOLD:
        # Only notify on state CHANGE (use rate limiting)
        if should_send_alert('freeze', room='crawlspace', cooldown_minutes=60):
            actions = [
                "Pipe freeze risk",
                "Check heating system"
            ]
            send_automation_summary(
                f"Crawlspace Cold ({temp}°F)",
                actions,
                priority=1
            )
            record_alert_sent('freeze', room='crawlspace')

    # If everything normal - NO notification (just log)
    else:
        logger.info(f"Temp OK: {temp}°F")
```

---

### Detection vs Action Pattern

**Detection Layer** (presence_monitor.py):
- Detects state changes
- Triggers automation
- **Does NOT notify** (silent)

**Action Layer** (leaving_home.py):
- Executes actions
- Collects results
- **Sends ONE notification** with summary

```python
# presence_monitor.py
def on_state_change():
    trigger_automation('leaving_home.py')  # No notification
    save_state('away')

# leaving_home.py
def run():
    actions = []
    # ... perform actions ...
    send_automation_summary("🚗 Left Home", actions)  # One notification
```

---

## Decision Tree

```
Should I send a notification?
│
├─ Is it a presence change (arrive/leave)?
│  └─ YES → Always notify
│
├─ Is it user-triggered (Siri command)?
│  └─ YES → Always notify (feedback)
│
├─ Is it critical/urgent (freeze risk, offline)?
│  └─ YES → Always notify (high priority)
│
├─ Did the system take action (changed state)?
│  └─ YES → Notify with action summary
│
└─ Just routine monitoring (everything normal)?
   └─ NO → Log only, don't notify
```

---

## API Reference

### `send_automation_summary(event_title, actions, priority=0)`

Sends a notification with event title and multi-line action list.

**Parameters:**
- `event_title` (str): Event with emoji (e.g., "🚗 Left Home")
- `actions` (list): List of action strings
- `priority` (int): 0=normal, 1=high, 2=urgent (default: 0)

**Returns:**
- `bool`: True if notification sent successfully

**Example:**
```python
send_automation_summary(
    "🚗 Left Home",
    [
        "Nest set to 62°F",
        "All outlets turned off",
        "House secured"
    ],
    priority=0
)
```

**Renders as:**
```
🚗 Left Home
→ Nest set to 62°F
→ All outlets turned off
→ House secured
```

---

## Implementation Checklist

### Phase 1: Foundation
- [x] Create `send_automation_summary()` helper
- [x] Update `lib/notifications.py` with new function
- [x] Test multi-line formatting on ntfy
- [x] Update `leaving_home.py` to use action list
- [x] Remove duplicate notification from `presence_monitor.py`

### Phase 2: Core Automations
- [ ] Update `im_home.py` - arriving home
  - [ ] Collect actions (Nest temp, lights, etc.)
  - [ ] Send "🏡 Arrived Home" with action summary
  - [ ] Remove old notification code
- [ ] Update `goodnight.py` - bedtime routine
  - [ ] Collect actions (Nest, lights, AC coordination)
  - [ ] Send "🌙 Goodnight" with action summary
  - [ ] Handle errors in action list
- [ ] Update `good_morning.py` - wake routine
  - [ ] Collect actions (Nest, lights, coffee maker)
  - [ ] Send "☀️ Good Morning" with action summary
  - [ ] Test full morning flow
- [ ] Update `temp_coordination.py` - automatic temp adjustments
  - [ ] Only notify if action taken (AC state changed)
  - [ ] Send "🌡️ Temperature Adjusted" with what changed
  - [ ] No notification if no action needed

### Phase 3: Monitoring Scripts
- [ ] Update `tempstick_monitor.py` - temperature/humidity alerts
  - [ ] Use action list for alert details
  - [ ] Show current value + threshold + recommendation
  - [ ] Example: "Crawlspace Cold (48°F)" → "Alert: Pipe freeze risk"
  - [ ] Keep rate limiting (don't spam)
- [ ] Verify monitoring scripts only notify on issues
  - [ ] Confirm "all checks passed" doesn't notify
  - [ ] Confirm rate limiting still works
  - [ ] Test cooldown periods

### Phase 4: Component Logging Audit
- [ ] Audit all components for consistent logging
  - [ ] `components/nest` - Standardize logging format
  - [ ] `components/sensibo` - Standardize logging format
  - [ ] `components/tapo` - Standardize logging format
  - [ ] `components/tuya` - Standardize logging format (if re-enabled)
  - [ ] `components/network` - Standardize logging format
- [ ] Ensure all components use kvlog or structured logging
- [ ] Verify all API calls logged (success/failure)
- [ ] Verify all state changes logged
- [ ] Test monitors can detect component failures from logs

### Phase 5: Future Automations
- [ ] Update any new automations to follow pattern
- [ ] Ensure Flask webhook endpoints trigger silent (automations notify)
- [ ] Add notification to travel time script if needed
- [ ] Review all notification calls for consistency

### Phase 6: Documentation & Cleanup
- [x] Create this design document
- [x] Document system architecture
- [x] Document component logging standards
- [ ] Add examples to README
- [ ] Add troubleshooting guide
- [ ] Review all notifications for user clarity
- [ ] Remove old notification patterns
- [ ] Verify no duplicate notifications remain

---

## Success Metrics

### Good Indicators
- ✅ You know what happened from title alone
- ✅ Actions give specific details (temps, devices, etc.)
- ✅ No duplicate notifications for single event
- ✅ No "everything is fine" spam
- ✅ Errors clearly indicated with failed action

### Red Flags
- ❌ Multiple notifications for one event
- ❌ Vague titles ("System Update", "Automation Complete")
- ❌ Notifications when nothing happened
- ❌ Missing context (what triggered this?)
- ❌ System perspective instead of user perspective

---

## Testing Checklist

### Manual Testing
- [ ] Test leaving home (turn off WiFi)
  - [ ] Verify single notification received
  - [ ] Check format: title + multi-line actions
  - [ ] Confirm no duplicate notifications
- [ ] Test arriving home (turn on WiFi)
  - [ ] Verify notification format
  - [ ] Check all actions listed
- [ ] Test Siri commands
  - [ ] "Goodnight" → notification with actions
  - [ ] "Good morning" → notification with actions
- [ ] Test error handling
  - [ ] Simulate device failure
  - [ ] Verify error in action list
  - [ ] Confirm high priority set

### Automated Testing
- [ ] Test `send_automation_summary()` with various inputs
  - [ ] Empty actions list
  - [ ] Single action
  - [ ] Multiple actions (2-5)
  - [ ] Long action strings
- [ ] Test emoji encoding
  - [ ] Verify emojis in title work
  - [ ] Verify multi-line with emojis
- [ ] Test priority levels
  - [ ] priority=0 (normal)
  - [ ] priority=1 (high)
  - [ ] priority=2 (urgent)

---

## Troubleshooting

### Notification not received
1. Check ntfy topic configured: `py_home_7h3k2m9x`
2. Verify ntfy app subscribed to topic
3. Check Flask server logs for send attempt
4. Test with: `send("test", "Test Title")`

### Emoji not displaying
1. Emojis work in message body (UTF-8)
2. Emojis removed from HTTP headers (latin-1 limitation)
3. Use emojis in title - they appear in app notification

### Duplicate notifications
1. Check if detection layer (presence_monitor) still notifying
2. Verify automation sends only one notification at end
3. Look for old notification code not yet updated

### Missing actions in list
1. Ensure `actions.append()` called after each step
2. Check error handling includes failed actions
3. Verify `send_automation_summary()` called with actions list

---

## Future Enhancements

### Potential Improvements
- Add notification categories/tags for filtering
- Include timestamp in critical alerts
- Add "undo" action link for reversible automations
- Rich notifications with images/maps
- Notification grouping for related events
- Daily summary notifications

### Under Consideration
- Voice response via TTS
- Notification acknowledgment tracking
- Custom notification sounds per category
- Notification scheduling (quiet hours)
