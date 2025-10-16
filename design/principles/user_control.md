# Design Principle: System Doesn't Second-Guess User

**Date:** 2025-10-16
**Status:** Established
**Applies to:** Scheduled time-based automations

## Principle

The automation system executes scheduled transitions at defined times, but **respects user manual adjustments** between those transitions.

The system does NOT:
- Re-check or re-enforce state continuously
- Override user manual changes before next scheduled transition
- Try to "correct" what it thinks is wrong

The system DOES:
- Execute scheduled transitions at configured times
- Accept user manual adjustments as intentional
- Wait for next scheduled transition to change state again

## Rationale

**User is in control.** If the user manually changes something, they had a reason:
- Still up after 22:30? User turns outlets back on
- Want house warmer in morning? User adjusts thermostat
- Want specific device off? User turns it off

System should not "fight" the user by constantly resetting things.

## Examples

### Example 1: Outlets at Bedtime

**Scenario:** Scheduled sleep transition at 22:30 turns off all outlets. User is still up reading.

**Correct Behavior:**
1. 22:30: System executes transition_to_sleep() → Outlets OFF
2. 22:35: User manually turns bedroom lamp back ON
3. 23:00: System does NOTHING (respects user choice)
4. 05:00: System executes transition_to_wake() (new state begins)

**Incorrect Behavior (DO NOT DO THIS):**
~~1. 22:30: System executes transition_to_sleep() → Outlets OFF~~
~~2. 22:35: User manually turns bedroom lamp back ON~~
~~3. 22:45: Scheduler runs again, sees lamp is on, turns it OFF (fighting user)~~
~~4. 22:50: User turns lamp back ON (frustrated)~~
~~5. 23:00: Scheduler turns lamp OFF again (user anger increases)~~

### Example 2: Manual Temperature Adjustment

**Scenario:** User wakes up cold at 04:30 and manually sets Nest to 72°F. Scheduled wake is 05:00.

**Correct Behavior:**
1. 04:30: User wakes up cold, manually sets Nest to 72°F via app
2. 05:00: System executes transition_to_wake()
   - Fetches weather (32°F outside, very cold)
   - Calculates target: < 40°F → Use 72°F
   - Sets Nest to 72°F
   - User experience: Seamless, system "agrees" with user
3. If weather was mild (50°F), system would set to 70°F
   - This is acceptable - new scheduled state overrides manual adjustment

**Principle:** Scheduled transitions are state resets. Between them, user is free to adjust.

### Example 3: Late Night Work Session

**Scenario:** User is working late at 01:00, needs lights and office devices on.

**Correct Behavior:**
1. 22:30: System executed transition_to_sleep() → All outlets OFF
2. 01:00: User turns on desk lamp and office outlets for work
3. 02:00: Outlets remain ON (system respects user)
4. 05:00: System executes transition_to_wake()
   - HVAC transitions to comfort mode
   - Grow light turns ON
   - Outlets: Already ON from user's manual action
   - Result: No disruption to user's work

### Example 4: Weekend Sleep-In

**Scenario:** User wants to sleep in on Saturday, but system wakes at 05:00.

**Correct Behavior:**
1. 05:00: System executes transition_to_wake()
   - HVAC to comfort mode
   - Grow light ON
   - Notification sent
2. 05:01: User (still asleep) is woken by notification or temp change
3. 05:02: User manually adjusts thermostat back to sleep mode
4. 05:15: Scheduler checks again but sees already transitioned today
   - Does NOTHING (state file prevents duplicate)
5. User sleeps in peacefully

**Future Enhancement:** Add "Do Not Disturb" or "Sleep In" mode to skip morning transition.

## When This Applies

### Time-Based Scheduled Events ✅

**These follow the principle:**
- Wake transition (05:00) - Once per day
- Sleep transition (22:30) - Once per day
- Grow light on/off - Once per day each
- Future scheduled automations

**Behavior:** Run ONCE at scheduled time. User can adjust freely between runs.

### Location-Based Events ❌

**These do NOT follow the principle:**
- Leaving home → Always sets away mode
- Arriving home → Always sets home mode

**Reason:** Location change is a definitive state change. If geofence triggers "leaving home", user is definitely leaving. System should always respond.

**User control:** User can still manually adjust AFTER location trigger. But the trigger itself always fires.

### Manual Triggers ❌

**These do NOT follow the principle:**
- Goodnight shortcut → User explicitly requested action
- Good morning shortcut → User explicitly requested action

**Reason:** User initiated the automation. User wants it to happen now. System executes immediately.

**Example:** User says "Hey Siri, Goodnight" at 21:00 (before scheduled 22:30). System executes sleep transition immediately because user requested it.

## Implementation Patterns

### Correct Pattern: Run Once Per Day

```python
# scheduler.py runs every 15 minutes

def run():
    # Check if it's wake time AND we haven't run today
    if is_wake_time() and not already_ran_today('wake'):
        transition_to_wake()
        mark_completed('wake')
        # Done. Don't check again until tomorrow.

    # Check if it's sleep time AND we haven't run today
    elif is_sleep_time() and not already_ran_today('sleep'):
        transition_to_sleep()
        mark_completed('sleep')
        # Done. Don't check again until tomorrow.
```

**Key points:**
- Runs every 15 minutes (cron)
- But only ACTS once per day per transition
- State file (.scheduler_state) tracks "already ran today"
- User adjustments between 05:00 and 22:30 are untouched

### Incorrect Pattern: Continuous Enforcement

```python
# OLD temp_coordination.py (DELETED - DO NOT USE THIS PATTERN)

def run():
    # Ran every 15 minutes and ALWAYS enforced state

    if is_home() and is_awake_hours():
        # ALWAYS set comfort mode, even if user just adjusted
        nest.set_comfort_mode()
        sensibo.set_comfort_mode()
        # Result: Overrides user every 15 minutes

    elif is_home() and is_sleep_hours():
        # ALWAYS set sleep mode
        nest.set_sleep_mode()
        sensibo.set_sleep_mode()
        # Result: User can't keep house warmer if they want

    elif is_away():
        # ALWAYS set away mode
        nest.set_away_mode()
        sensibo.set_away_mode()
```

**Problems with this pattern:**
- Checks and enforces EVERY 15 minutes
- User manual changes overridden within 15 minutes
- System "fights" the user
- Frustrating user experience

**Why it existed:** To handle edge cases like "user manually changed temp at 11pm, system should transition to sleep mode at 10:30pm even if user changed it."

**Better solution:** Scheduled transitions at specific times. User knows "at 10:30, system will change things." Between transitions, user is free.

## State File Design

### .scheduler_state (JSON)

```json
{
  "last_wake_date": "2025-10-16",
  "last_sleep_date": "2025-10-16"
}
```

**Purpose:**
- Track which transitions ran today
- Prevent duplicate runs if cron executes multiple times in window
- Reset automatically when date changes (new day = can run again)

**Example flow:**
```
05:00 - Cron runs
      - Check state file: last_wake_date = "2025-10-15" (yesterday)
      - Run transition_to_wake()
      - Update state file: last_wake_date = "2025-10-16"

05:15 - Cron runs again
      - Check state file: last_wake_date = "2025-10-16" (today)
      - Skip (already ran today)

...rest of day...

Next day 05:00 - Cron runs
      - Check state file: last_wake_date = "2025-10-16" (yesterday)
      - Run transition_to_wake()
      - Update state file: last_wake_date = "2025-10-17"
```

## Exceptions and Edge Cases

### Exception 1: Critical Safety

If a safety issue arises, system CAN override user:
- Fire alarm → Turn on all lights, unlock doors
- Carbon monoxide → Turn off gas, ventilate
- Water leak → Turn off water main

**These are not implemented, but IF they were, safety overrides user control.**

### Exception 2: Energy Emergency

Future consideration: If utility sends "emergency conservation" signal:
- Override user setpoints to reduce load
- Send notification explaining why

**Not implemented. Just a consideration for future.**

### Edge Case 1: User Adjusts During Transition Window

**Scenario:** User manually adjusts temp at 05:10, scheduler runs at 05:15.

**Behavior:**
- Scheduler sees last_wake_date = yesterday (or empty)
- Scheduler runs transition_to_wake()
- User's manual adjustment overridden by scheduled transition

**Is this acceptable?** YES
- User adjusted at 05:10, within wake window (05:00-05:14)
- Scheduled wake transition is expected at this time
- User should understand scheduled transition occurs around 05:00

**Alternative:** Scheduler could check "did user manually adjust in last X minutes?"
- Complex to implement
- Unclear if beneficial
- Defer for now

### Edge Case 2: Multiple Manual Triggers Same Day

**Scenario:** User says "Goodnight" at 21:00 (before scheduled 22:30).

**Behavior:**
1. 21:00: goodnight.py calls transition_to_sleep() → Executes
2. 22:30: Scheduler checks, runs transition_to_sleep() → Executes again (idempotent)

**Is this acceptable?** YES
- Transitions are idempotent (calling set_sleep_mode() twice is fine)
- Scheduler doesn't track manual triggers, only its own scheduled runs
- Second transition causes no harm (just redundant)

**Improvement for future:** Track ALL transitions in state file, not just scheduled ones.

## Related Principles

- **Explicit over implicit** - User actions are explicit, system respects them
- **User agency** - User has control over their environment
- **Predictable behavior** - System acts at known times, not randomly
- **Minimal surprise** - System doesn't fight user or act unexpectedly

## Comparison to Other Systems

### Smart Home Systems That Get This Wrong

**Nest Learning Thermostat:**
- Learns user patterns
- Overrides manual adjustments with "learned" schedule
- Users frustrated: "I set it to 72, why did it change to 68?"

**Some lighting systems:**
- Motion sensor turns on lights
- User turns off lights manually (wants dark)
- Motion sensor turns lights back on (fighting user)
- User rage-quits smart lighting

### Better Approaches

**Hue Lighting with "Disable for X minutes":**
- Motion automation can be disabled temporarily
- Gives user control when needed
- Re-enables automatically

**Our approach:**
- Scheduled transitions at specific times
- User knows "at 5am, system changes things"
- Between transitions, user is free
- Clear expectations, no surprises

## Future Considerations

### Should we add "manual override mode"?

**Idea:** User manually adjusts thermostat. System notes "user override active."

**Next scheduled transition:**
- Send notification: "Wake transition ready. Override active. Resume schedule?"
- User can choose: "Yes, resume" or "No, keep my settings"

**Pros:**
- Even more user control
- Clear communication
- Handles edge cases

**Cons:**
- More complexity
- More notifications
- May be unnecessary if current approach works

**Decision:** Don't implement now. Consider if users report frustration with current approach.

### Should we add "Do Not Disturb" mode?

**Idea:** User enables DND mode (iOS Shortcut or config flag).

**Behavior:**
- Scheduler checks DND status before transitioning
- If DND active, skip transition
- User can sleep in, work late, etc.

**Pros:**
- Handles weekend sleep-in
- Handles late night work
- User explicit control

**Cons:**
- Another mode to manage
- User must remember to disable DND
- What if user forgets DND is on?

**Decision:** Consider for future. Not critical now.

## Documentation for Users

If/when we create user-facing documentation:

**Explain to users:**
1. "System changes settings at 5am and 10:30pm each day"
2. "Between those times, your manual adjustments are respected"
3. "Next scheduled time, system will reset to its schedule"
4. "You can always manually override via thermostat or app"

**Examples to include:**
- "Still up at 11pm? Turn lights back on. System won't turn them off until 5am."
- "Cold in morning? Adjust thermostat. Next night at 10:30pm, system resets."

**Common questions:**
- Q: "Why did system change my temp at 5am?"
  A: "That's the scheduled wake time. System transitions to comfort mode every morning."
- Q: "Can I adjust between scheduled times?"
  A: "Yes! Manual adjustments are respected until next scheduled transition."
- Q: "Can I disable scheduled transitions?"
  A: "Yes, set automations.dry_run = true in config, or disable cron job."

## Summary

**Core principle:** System schedules transitions at specific times. Between those times, user manual adjustments are respected and not overridden.

**Implementation:** Once-per-day scheduled transitions with state tracking, not continuous enforcement.

**User benefit:** Predictable automation that doesn't fight user control.

**Related:** See design/scheduler_transitions.md for technical implementation.
