# Scheduler & Transitions Implementation Plan

**Date:** 2025-10-16
**Status:** Planning Complete, Ready to Execute
**Design Reference:** [design/scheduler_transitions.md](../design/scheduler_transitions.md)

## Overview

This plan implements the scheduler + transitions architecture to replace the deleted temp_coordination.py. The implementation is broken into 5 phases, each independently testable.

**IMPORTANT:** Refer back to [design/scheduler_transitions.md](../design/scheduler_transitions.md) throughout implementation, not just this task list. The design doc contains critical details about:
- Weather integration logic
- Error handling patterns
- Notification content design
- State tracking implementation
- Time matching precision

## Success Criteria

- [ ] At 05:00, both HVAC units set to comfort mode with weather-aware temp adjustment
- [ ] At 22:30, both HVAC units set to sleep mode, outlets OFF, grow light OFF
- [ ] State tracking prevents duplicate transitions within same day
- [ ] iOS Shortcuts (goodnight, good_morning, leaving_home, arriving_home) use transitions
- [ ] Each transition sends ONE macro notification summarizing all actions
- [ ] Per-device error handling: One device failure doesn't stop others
- [ ] Dry-run mode works for all transitions
- [ ] Scheduler runs every minute via cron, most runs are quick no-ops
- [ ] 100% test pass rate maintained

## Phase 1: Transitions Module (Core Infrastructure)

**Goal:** Create lib/transitions.py with all 4 transition functions, fully tested

**Reference:** Design doc sections "The Four Transitions", "Weather Integration", "Error Handling"

### Tasks

1. **Create lib/transitions.py skeleton**
   - Module docstring explaining purpose
   - Import all needed components (nest, sensibo, tapo, weather, notifications)
   - Import config, logging
   - Define helper functions (is_sleep_time, format_notification)

2. **Implement transition_to_wake()**
   - Fetch weather with try/catch fallback
   - Calculate target temp based on weather (< 40°F → 72, > 75°F → 68, else 70)
   - Set Nest comfort mode with temp override
   - Set Sensibo comfort mode with temp override
   - Turn ON grow light (placeholder for now)
   - Send ONE macro notification with weather + all actions
   - Return structured result dict
   - **Reference design doc for exact notification format**

3. **Implement transition_to_sleep()**
   - Set Nest to ECO mode
   - Set Sensibo to sleep mode (66°F)
   - Turn OFF grow light (placeholder)
   - Turn OFF all Tapo outlets
   - Send ONE macro notification with all actions
   - Return structured result dict
   - **Reference design doc for outlet behavior during scheduled vs manual**

4. **Implement transition_to_away()**
   - Set Nest to ECO mode
   - Set Sensibo to away mode (OFF)
   - Turn OFF all Tapo outlets
   - NO CHANGE to grow light (plants need consistent schedule)
   - Send ONE macro notification
   - Return structured result dict
   - Note: Presence state update handled by caller (leaving_home.py)

5. **Implement transition_to_home()**
   - Check is_sleep_time() to determine mode
   - If sleep hours: Set Nest ECO, Sensibo 66°F
   - If awake hours: Set Nest 70°F, Sensibo 70°F
   - Send ONE macro notification
   - Return structured result dict
   - Note: Outdoor lights handled by caller (pre_arrival.py)

6. **Add per-device error handling**
   - Each device operation in try/catch
   - One failure doesn't stop others
   - Collect errors list, actions list
   - Return status: 'success' | 'partial' | 'failed'
   - **Reference design doc error handling section for pattern**

7. **Add dry-run support**
   - All transitions accept dry_run parameter
   - Pass to all component APIs
   - Log what WOULD happen
   - Still send notification (but mark as dry-run)

### Testing

**Unit tests (tests/test_transitions.py):**
- `test_transition_to_wake_cold_weather()` - Verify 72°F on < 40°F
- `test_transition_to_wake_hot_weather()` - Verify 68°F on > 75°F
- `test_transition_to_wake_normal_weather()` - Verify 70°F on 40-75°F
- `test_transition_to_wake_weather_unavailable()` - Verify fallback to config default
- `test_transition_to_sleep_all_actions()` - Verify all devices controlled
- `test_transition_to_away_grow_light_unchanged()` - Verify grow light NOT changed
- `test_transition_to_home_sleep_hours()` - Verify ECO mode at night
- `test_transition_to_home_awake_hours()` - Verify comfort mode during day
- `test_partial_failure_handling()` - One device fails, others succeed
- `test_all_failures()` - All devices fail, status = 'failed'
- `test_dry_run_mode()` - Verify no actual changes made

**Manual tests:**
```bash
# Test each transition in dry-run
python -c "from lib.transitions import *; print(transition_to_wake(dry_run=True))"
python -c "from lib.transitions import *; print(transition_to_sleep(dry_run=True))"
python -c "from lib.transitions import *; print(transition_to_away(dry_run=True))"
python -c "from lib.transitions import *; print(transition_to_home(dry_run=True))"
```

**Acceptance criteria:**
- [ ] All 4 transitions implemented
- [ ] All unit tests pass (100% pass rate maintained)
- [ ] Dry-run tests show correct actions without actually executing
- [ ] Error handling tested (mock device failures)
- [ ] Weather integration tested (mock weather API)

## Phase 2: Scheduler Module (Time Trigger)

**Goal:** Create automations/scheduler.py that runs every minute, checks time, triggers transitions

**Reference:** Design doc sections "Scheduler Logic", "Precise Time Matching", "State Tracking"

### Tasks

1. **Create automations/scheduler.py skeleton**
   - Script docstring explaining purpose
   - Import transitions, config, logging, datetime
   - Import state file helpers (Path, json)
   - Define constants (STATE_FILE path)

2. **Implement state tracking functions**
   - `already_ran_today(transition_type)` - Check .scheduler_state file
   - `mark_completed(transition_type)` - Update .scheduler_state with today's date
   - Handle missing file gracefully (first run)
   - Handle corrupt JSON gracefully
   - **Reference design doc for exact state file format**

3. **Implement time matching functions**
   - `should_transition_to_wake()` - Check hour:minute matches config wake_time
   - `should_transition_to_sleep()` - Check hour:minute matches config sleep_time
   - Parse "HH:MM" from config.yaml
   - Check NOT already ran today (call already_ran_today)
   - **Reference design doc for exact matching logic**

4. **Implement main run() function**
   - Check should_transition_to_wake()
   - If yes: Call transition_to_wake(), log result, mark completed
   - Check should_transition_to_sleep()
   - If yes: Call transition_to_sleep(), log result, mark completed
   - Most runs: No-op (return quickly, minimal logging)
   - Only log at INFO+ level when action taken
   - **Reference design doc for logging strategy**

5. **Add dry-run support**
   - Check environment variable or command-line flag
   - Pass dry_run to transitions
   - Log "DRY RUN MODE" clearly

6. **Add if __name__ == '__main__' block**
   - Setup logging
   - Call run()
   - Exit

### Testing

**Unit tests (tests/test_scheduler.py):**
- `test_should_transition_to_wake_time_match()` - Verify time detection
- `test_should_transition_to_wake_time_no_match()` - Verify no false triggers
- `test_should_transition_to_wake_already_ran()` - Verify duplicate prevention
- `test_should_transition_to_sleep_time_match()` - Verify time detection
- `test_state_file_missing()` - First run, no state file
- `test_state_file_corrupt()` - Handles corrupt JSON
- `test_state_file_yesterday()` - Old date allows new transition
- `test_state_file_today()` - Same date prevents duplicate
- `test_run_at_wake_time()` - Mock time to 05:00, verify transition called
- `test_run_at_sleep_time()` - Mock time to 22:30, verify transition called
- `test_run_at_random_time()` - Mock time to 14:37, verify no-op
- `test_run_twice_same_day()` - Second call prevented by state file

**Manual tests:**
```bash
# Test time matching (mock current time)
python -c "from automations.scheduler import *; print(should_transition_to_wake())"

# Test dry-run at arbitrary time
python automations/scheduler.py --dry-run

# Test state tracking
rm .scheduler_state  # Reset
python -c "from automations.scheduler import mark_completed; mark_completed('wake')"
cat .scheduler_state  # Should show today's date
python -c "from automations.scheduler import already_ran_today; print(already_ran_today('wake'))"  # Should be True
```

**Acceptance criteria:**
- [ ] Scheduler detects correct time windows
- [ ] State file prevents duplicate transitions
- [ ] No-ops are fast (< 10ms)
- [ ] Action runs log clearly
- [ ] All unit tests pass
- [ ] Dry-run mode works

## Phase 3: Refactor Existing Automations

**Goal:** Update goodnight.py, good_morning.py, leaving_home.py, pre_arrival.py to use transitions

**Reference:** Design doc section "Automation Scripts (Thin Orchestrators)"

### Tasks

1. **Refactor automations/goodnight.py**
   - Import transition_to_sleep from lib.transitions
   - Replace direct device control with: `result = transition_to_sleep()`
   - Remove individual device calls (nest, sensibo, tapo, etc.)
   - Remove per-device notifications (transition sends one macro notification)
   - Keep unique logic (weather brief if needed)
   - Log transition result
   - Return result to Flask endpoint
   - **Reference design doc "Manual Triggers" section**

2. **Refactor automations/good_morning.py**
   - Import transition_to_wake from lib.transitions
   - Replace direct device control with: `result = transition_to_wake()`
   - Remove individual device calls
   - Remove per-device notifications
   - Keep unique logic (weather brief, etc.)
   - Log transition result

3. **Refactor automations/leaving_home.py**
   - Import transition_to_away from lib.transitions
   - Replace direct device control with: `result = transition_to_away()`
   - KEEP presence state update (unique to location trigger)
   - KEEP weather-related logic if any
   - Remove individual device calls
   - Log transition result

4. **Refactor automations/pre_arrival.py**
   - Import transition_to_home from lib.transitions
   - Replace direct device control with: `result = transition_to_home()`
   - KEEP outdoor light control (unique to arrival)
   - KEEP presence state update (unique to location trigger)
   - Remove individual device calls
   - Log transition result

5. **Update each automation's tests**
   - Mock lib.transitions functions
   - Verify correct transition called
   - Verify unique automation logic still works (presence state, outdoor lights)
   - Verify no duplicate device control

### Testing

**Unit tests:**
- `test_goodnight_calls_transition_to_sleep()` - Verify transition called
- `test_goodnight_respects_master_switch()` - Master switch check still works
- `test_good_morning_calls_transition_to_wake()` - Verify transition called
- `test_leaving_home_calls_transition_to_away()` - Verify transition called
- `test_leaving_home_updates_presence_state()` - Unique logic preserved
- `test_pre_arrival_calls_transition_to_home()` - Verify transition called
- `test_pre_arrival_controls_outdoor_lights()` - Unique logic preserved

**Integration tests:**
- POST to /api/automations/goodnight → Verify transition_to_sleep called
- POST to /api/automations/good_morning → Verify transition_to_wake called
- POST to /api/automations/leaving_home → Verify transition_to_away called
- POST to /api/automations/pre_arrival → Verify transition_to_home called

**Manual tests via iOS Shortcuts:**
- "Goodnight" → Verify one notification with all actions
- "Good Morning" → Verify one notification with weather + actions
- "Leaving Home" → Verify transition + presence state update
- "I'm Home" → Verify transition + outdoor lights

**Acceptance criteria:**
- [ ] All 4 automations refactored
- [ ] All tests pass (100% pass rate maintained)
- [ ] iOS Shortcuts work correctly
- [ ] Only ONE notification per automation
- [ ] Unique automation logic preserved (presence, outdoor lights)

## Phase 4: Configuration & Documentation

**Goal:** Update config, add cron job, document deployment

**Reference:** Design doc sections "Configuration", "Cron Schedule", "Deployment"

### Tasks

1. **Verify config.yaml has required values**
   - `schedule.wake_time: "05:00"` - Should already exist
   - `schedule.sleep_time: "22:30"` - Should already exist
   - `temperatures.comfort: 70` - Should already exist
   - `temperatures.bedroom_sleep: 66` - Should already exist
   - Add comments explaining these are used by scheduler
   - **Reference design doc for config structure**

2. **Add .scheduler_state to .gitignore**
   - Add line: `.scheduler_state`
   - Verify not accidentally committed

3. **Update dev/setup/DEPLOYMENT.md**
   - Add section: "Scheduler Cron Job"
   - Document cron command:
     ```bash
     * * * * * cd /home/matt.wheeler/py_home && /home/matt.wheeler/py_home/venv/bin/python automations/scheduler.py >> /home/matt.wheeler/py_home/data/logs/automations.log 2>&1
     ```
   - Explain: Runs every minute, checks time against config, triggers transitions
   - Document how to disable: Comment out cron line
   - Document rollback: Remove cron, manual triggers still work
   - **Reference design doc "Rollback Plan" section**

4. **Create plans/scheduler_cleanup_audit.md tasks checklist**
   - Already exists, verify it's complete

### Testing

**Configuration tests:**
```bash
# Verify config can be read
python -c "from lib.config import get; print(get('schedule.wake_time'))"
python -c "from lib.config import get; print(get('schedule.sleep_time'))"
```

**Gitignore test:**
```bash
# Create dummy state file
echo '{"test": true}' > .scheduler_state
git status  # Should NOT show .scheduler_state as untracked
rm .scheduler_state
```

**Acceptance criteria:**
- [ ] Config.yaml verified
- [ ] .scheduler_state in .gitignore
- [ ] DEPLOYMENT.md updated with cron command
- [ ] Rollback procedure documented

## Phase 5: Deployment & Monitoring

**Goal:** Deploy to Pi, add cron job, monitor for 24 hours

**Reference:** Design doc sections "Deployment", "Testing Strategy - Manual Tests"

### Tasks

1. **Pre-deployment checklist**
   - [ ] All tests passing locally (pytest)
   - [ ] Dry-run tests completed
   - [ ] iOS Shortcuts tested locally
   - [ ] Git committed and pushed to origin/main
   - [ ] Pi is up and accessible via SSH

2. **Deploy to Pi**
   ```bash
   ssh matt.wheeler@100.107.121.6
   cd /home/matt.wheeler/py_home
   git pull origin main
   ```

3. **Test on Pi before adding cron**
   ```bash
   # Test scheduler dry-run
   /home/matt.wheeler/py_home/venv/bin/python automations/scheduler.py --dry-run

   # Test transitions dry-run
   /home/matt.wheeler/py_home/venv/bin/python -c "from lib.transitions import *; print(transition_to_wake(dry_run=True))"
   ```

4. **Add cron job**
   ```bash
   crontab -e
   # Add line:
   * * * * * cd /home/matt.wheeler/py_home && /home/matt.wheeler/py_home/venv/bin/python automations/scheduler.py >> /home/matt.wheeler/py_home/data/logs/automations.log 2>&1

   # Verify
   crontab -l | grep scheduler
   ```

5. **Monitor first hour**
   ```bash
   # Watch logs live
   tail -f /home/matt.wheeler/py_home/data/logs/automations.log

   # Check for errors
   grep ERROR /home/matt.wheeler/py_home/data/logs/automations.log | tail -20

   # Verify scheduler runs every minute (most should be quick no-ops)
   grep "scheduler" /home/matt.wheeler/py_home/data/logs/automations.log | tail -10
   ```

6. **Monitor first 24 hours**
   - Check 05:00 wake transition tomorrow morning
   - Check 22:30 sleep transition tonight
   - Verify no duplicate transitions
   - Verify iOS Shortcuts still work
   - Check notification counts (should be fewer than before)

7. **Verify success criteria met**
   - Go through checklist at top of this document
   - Document any issues found
   - Fix if needed

### Testing

**Deployment tests:**
- SSH to Pi → Verify code updated
- Check cron → Verify job added
- Wait 1 minute → Check logs for scheduler run
- Wait for 05:00 or 22:30 → Verify transition triggered
- Test iOS Shortcuts → Verify still work

**Acceptance criteria:**
- [ ] Code deployed to Pi
- [ ] Cron job added and verified
- [ ] First hour monitored, no errors
- [ ] Wake transition (05:00) verified
- [ ] Sleep transition (22:30) verified
- [ ] No duplicate transitions observed
- [ ] iOS Shortcuts work correctly
- [ ] Only ONE notification per transition

## Phase 6: Cleanup & Audit

**Goal:** Remove dead code, verify no lingering references to temp_coordination

**Reference:** plans/scheduler_cleanup_audit.md

### Tasks

1. **Search for temp_coordination references**
   ```bash
   grep -r "temp_coordination" --exclude-dir=.git --exclude-dir=venv --exclude="*.pyc"
   ```
   - Remove any imports
   - Remove any calls
   - Update any documentation references
   - Check if file still exists (should be deleted already)

2. **Search for duplicate HVAC control logic**
   - Look for direct nest.set_comfort_mode() calls in automations
   - Should only be in lib/transitions.py now
   - Verify automations call transitions, not devices directly

3. **Audit state files**
   ```bash
   ls -la | grep "^\."  # List hidden files
   ```
   - Verify .scheduler_state exists (after first run)
   - Verify .presence_state still works
   - Check for any orphaned state files from temp_coordination

4. **Run full test suite**
   ```bash
   pytest -v
   ```
   - Verify 100% pass rate
   - Verify no skipped tests
   - Verify no warnings about deprecated functions

5. **Check log volume**
   - Compare log sizes before/after
   - Verify no log spam from scheduler (most runs should not log)
   - Verify notifications reduced (one per transition, not per device)

6. **Update backlog.md**
   - Mark this task complete
   - Add any new issues found
   - Document any future enhancements discovered

### Testing

**Audit tests:**
- Grep tests show no unwanted references
- Test suite 100% pass
- Log analysis shows expected volume
- Notification count reduced

**Acceptance criteria:**
- [ ] No temp_coordination references found
- [ ] No duplicate HVAC control in automations
- [ ] State files working correctly
- [ ] Test suite 100% pass
- [ ] Log volume acceptable
- [ ] Cleanup complete

## Dependencies Between Phases

```
Phase 1 (Transitions)
  ↓
Phase 2 (Scheduler) ← depends on Phase 1
  ↓
Phase 3 (Refactor) ← depends on Phase 1
  ↓
Phase 4 (Config) ← can happen anytime after Phase 1
  ↓
Phase 5 (Deploy) ← depends on Phases 1-4
  ↓
Phase 6 (Cleanup) ← depends on Phase 5
```

**Critical path:**
1. Transitions MUST be complete before anything else
2. Scheduler and Refactor can happen in parallel (both depend on Transitions)
3. Everything must be complete before Deploy
4. Cleanup happens after Deploy

## Rollback Points

**After Phase 1:**
- New lib/transitions.py exists but not used yet
- No risk, no rollback needed

**After Phase 2:**
- Scheduler exists but not in cron yet
- No risk, no rollback needed

**After Phase 3:**
- Automations use transitions but scheduler not deployed
- Manual triggers work via transitions
- Rollback: Revert automation files to previous versions (git history)

**After Phase 4:**
- Configuration updated, cron documented but not added
- No risk, no rollback needed

**After Phase 5:**
- Scheduler running in cron
- Rollback: Comment out cron job
- Manual triggers still work
- See "Rollback Plan" in design doc

**After Phase 6:**
- Cleanup complete
- Rollback: Re-add cron job if removed

## Estimated Time

- Phase 1: 3-4 hours (transitions + tests)
- Phase 2: 2-3 hours (scheduler + tests)
- Phase 3: 3-4 hours (refactor 4 automations + tests)
- Phase 4: 1 hour (config + docs)
- Phase 5: 2 hours (deploy + monitor first few hours)
- Phase 6: 2-3 hours (cleanup + audit)

**Total: 13-17 hours**

Spread over ~1 week:
- Day 1: Phase 1
- Day 2: Phase 2
- Day 3: Phase 3
- Day 4: Phase 4 + Phase 5 (deploy in evening, monitor overnight)
- Day 5: Monitor wake transition (05:00)
- Day 6: Monitor sleep transition (22:30)
- Day 7: Phase 6 cleanup

## Key Implementation Reminders

1. **Refer to design doc frequently** - Don't just follow this task list blindly
2. **Test at each phase** - Don't accumulate untested code
3. **Maintain 100% test pass rate** - Never commit failing tests
4. **Use dry-run mode extensively** - Test without affecting real devices
5. **Per-device error handling** - One failure shouldn't stop others
6. **One notification per transition** - Not one per device
7. **State tracking prevents duplicates** - Check already_ran_today()
8. **Cron every minute** - Most runs are no-ops, that's expected
9. **Weather fallback** - Graceful degradation if API fails
10. **User control principle** - System doesn't second-guess user between transitions

## Open Questions to Resolve During Implementation

1. ✓ Should transitions check automation master switch, or should caller check?
   - **Decision:** Caller checks (goodnight.py checks before calling transition)

2. ✓ Should we send notification on scheduler-triggered transitions?
   - **Decision:** Yes (same notification as manual triggers)

3. Should grow light respect vacation mode or always run on schedule?
   - **Decision:** Always run for now (plants need consistency)
   - **Future:** Add vacation mode flag

4. Should we add rate limiting for transitions (e.g., max once per hour)?
   - **Decision:** No (state file prevents duplicates, manual triggers should always work)

## Related Documents

- **Design:** [design/scheduler_transitions.md](../design/scheduler_transitions.md) ← PRIMARY REFERENCE
- **Principle:** [design/principles/user_control.md](../design/principles/user_control.md)
- **Cleanup:** [scheduler_cleanup_audit.md](./scheduler_cleanup_audit.md)
- **Backlog:** [backlog.md](./backlog.md)
- **Decision:** status/decisions/temp_coordination_disabled.md

## Notes

This plan is deliberately verbose to ensure each phase is independently testable and to serve as a reference during implementation. When in doubt, refer back to the design document, not just this task list.
