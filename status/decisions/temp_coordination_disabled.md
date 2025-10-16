# Decision: Disable Temperature Coordination Cron Job

**Date:** 2025-10-15
**Status:** Implemented

## Problem

The `temp_coordination.py` script was running every 15 minutes via cron, continuously resetting HVAC setpoints based on presence and time state. This meant:

- Manual temperature adjustments were overridden within 15 minutes
- User had no way to temporarily adjust temps without system interference
- System was too aggressive in managing temperatures

## Decision

**Disable the temp_coordination cron job completely.**

Temperature changes will now ONLY occur during explicit state transitions:
- **Goodnight** → Sleep mode (Nest ECO, Sensibo 66°F)
- **Good Morning** → Comfort mode (Both 70°F)
- **Leaving Home** → Away mode (Both ECO/off)
- **I'm Home** (arrival) → Comfort mode (Both 70°F)

## Rationale

1. **User control:** Manual temp adjustments should persist until next explicit transition
2. **Explicit transitions:** All state changes already have automation triggers (iOS Shortcuts)
3. **Less intrusive:** System respects user intent rather than constantly enforcing policy
4. **Simpler logic:** State changes happen at well-defined moments, not continuously

## Implementation

### Raspberry Pi Crontab
**Before:**
```cron
*/15 * * * * cd /home/matt.wheeler/py_home && /home/matt.wheeler/py_home/venv/bin/python automations/temp_coordination.py >> /home/matt.wheeler/py_home/data/logs/temp_coordination.log 2>&1
```

**After:**
```cron
# Removed - temps controlled by explicit automations only
```

### Documentation Updated
- `dev/setup/DEPLOYMENT.md` - Commented out cron job with explanation
- `status/decisions/temp_coordination_disabled.md` - This file

### Script Removal
The `automations/temp_coordination.py` script has been **deleted entirely** because:
- All its functionality is covered by existing event-driven automations
- Keeping dead code adds maintenance burden and confusion
- No unique logic to preserve

Existing automations that provide the same functionality:
- `goodnight.py` → set_sleep_mode()
- `good_morning.py` → set_comfort_mode()
- `leaving_home.py` → set_away_mode()
- `arrival_preheat.py` / `pre_arrival.py` → set_comfort_mode()

## Trade-offs

### Benefits ✅
- User manual adjustments persist
- Less API calls to Nest/Sensibo
- Simpler to understand system behavior
- Fewer logs

### Drawbacks ❌
- If user forgets to trigger automation, temps won't auto-adjust
  - **Mitigation:** iOS Shortcuts already integrated with routines
- Edge case: User manually changes temp at 11pm, it won't auto-switch to sleep mode
  - **Mitigation:** Goodnight shortcut should be part of bedtime routine

## Alternatives Considered

1. **Make temp_coordination idempotent** - Check current state first, only change if needed
   - ❌ Still overrides manual changes eventually

2. **Add manual override flag** - Skip coordination if user changed temp recently
   - ❌ Complex to implement, adds state tracking overhead

3. **Disable cron job** ✅ **SELECTED**
   - Simple, clear, gives user full control

## Rollback Plan

If this proves problematic, re-enable the cron job:
```bash
crontab -e
# Uncomment the temp_coordination line
```

## Testing

- [x] Cron job removed from Pi
- [x] Documentation updated
- [x] Manual temp changes now persist beyond 15 minutes
- [ ] Verify state transitions still work (goodnight, good_morning, etc.)

## Notes

This change aligns with the principle: **py_home should only change setpoints during explicit time and location transitions, not continuously.**
