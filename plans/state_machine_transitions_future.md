# State Machine Transitions - Future Architecture

**Date:** 2025-10-16
**Status:** Future / Not Started
**Priority:** Low (nice-to-have refactor)

## Overview

**This is NOT an immediate need.** This document captures a potential future architectural improvement to eliminate duplicate HVAC control logic across automation files.

## Current Situation

Multiple automation files have duplicate HVAC control code:
- `goodnight.py` - calls nest.set_sleep_mode(), sensibo.set_sleep_mode()
- `good_morning.py` - calls nest.set_comfort_mode()
- `leaving_home.py` - calls nest.set_away_mode(), sensibo.set_away_mode()
- `pre_arrival.py` - calls nest.set_comfort_mode(), sensibo.set_comfort_mode()
- `hvac_scheduler.py` - calls all of the above based on time

**This works fine.** The duplication is manageable and clear.

## Proposed Future Improvement

Create a "transitions" abstraction layer that defines system state transitions:

```python
# lib/transitions.py (FUTURE)

def transition_to_wake():
    """Morning routine - ALL wake actions"""
    nest.set_comfort_mode()
    sensibo.set_comfort_mode()
    # Future: grow light on, coffee maker on, etc.

def transition_to_sleep():
    """Bedtime routine - ALL sleep actions"""
    nest.set_sleep_mode()
    sensibo.set_sleep_mode()
    tapo.turn_off_all()
    # Future: grow light off, lock doors, etc.

def transition_to_away():
    """Leaving routine - ALL away actions"""
    nest.set_away_mode()
    sensibo.set_away_mode()
    tapo.turn_off_all()

def transition_to_home():
    """Arrival routine - ALL arrival actions"""
    if is_sleep_time():
        transition_to_sleep()
    else:
        transition_to_wake()
    # Turn on outdoor lights if dark
```

Then refactor all automations to use these:
- `goodnight.py` → `transition_to_sleep()`
- `good_morning.py` → `transition_to_wake()`
- `hvac_scheduler.py` → `transition_to_wake()` or `transition_to_sleep()`
- etc.

## Benefits

1. **Single source of truth** - "What happens at bedtime?" defined once
2. **Easy to extend** - Add grow light? Edit one place, affects all triggers
3. **Consistency** - Manual and automatic triggers do exactly the same thing
4. **Testability** - Test transitions independently

## Considerations

1. **Is the abstraction worth it?**
   - Current duplication is minimal (4-5 files)
   - Each automation has unique concerns too (notifications, state files, etc.)
   - May be premature optimization

2. **What about non-HVAC actions?**
   - goodnight.py turns off ALL outlets (including non-HVAC)
   - leaving_home.py updates presence state
   - Should transitions include ALL actions or just HVAC?
   - Risk: Transitions become too complex/overloaded

3. **State machine formalism**
   - Do we need formal states (WAKE, SLEEP, AWAY, HOME)?
   - Or just shared functions?
   - How do we track current state?

## Decision: Defer

**Recommendation:** Don't do this refactor yet.

**Reasons:**
1. Current code works and is maintainable
2. Unclear if abstraction helps or hurts
3. Need more experience with grow light, other devices
4. Let design emerge naturally from real needs

**When to reconsider:**
- After adding 3+ new devices to morning/evening routines
- When duplication becomes painful to maintain
- When inconsistencies appear across automations
- When testing becomes difficult

## If/When Implemented

If we decide to do this later, the implementation would be:

1. Create lib/transitions.py with all transition functions
2. Refactor goodnight.py, good_morning.py, etc. to use them
3. Update hvac_scheduler.py to use them
4. Add comprehensive tests for transitions
5. Monitor for 1-2 weeks to ensure nothing broke

Estimated: 4-6 hours

## Related Files

- plans/hvac_scheduler_simple.md (current simple approach)
- plans/scheduler_implementation.md (original plan that conflated these)
