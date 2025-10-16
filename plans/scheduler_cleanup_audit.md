# Scheduler Implementation - Cleanup Audit Plan

**Date:** 2025-10-16
**Status:** Planning
**Related:** scheduler_implementation.md

## Overview

Audit plan to identify and clean up stray work related to:
1. Deprecating temp_coordination.py (already deleted)
2. Implementing new scheduler architecture
3. Ensuring no orphaned references or duplicate logic

## Audit Checklist

### 1. Code References to temp_coordination

**Search for:**
- Import statements: `from automations.temp_coordination import`
- Comments referencing temp_coordination
- Documentation mentions

**Files to check:**
- [ ] automations/*.py (all automation scripts)
- [ ] lib/*.py (all library modules)
- [ ] components/*.py (all component modules)
- [ ] tests/*.py (all test files)
- [ ] README.md, CLAUDE.md, docs/*.md

**Actions:**
- Remove any imports
- Update comments/docs to reference scheduler.py instead
- Remove any tests for temp_coordination

### 2. Duplicate Logic Audit

**Check existing automations for duplicate HVAC control logic:**

**goodnight.py:**
- [ ] Review HVAC logic
- [ ] Should be replaced with `transition_to_sleep()` call
- [ ] Verify no unique logic is lost

**good_morning.py:**
- [ ] Review HVAC logic
- [ ] Should be replaced with `transition_to_wake()` call
- [ ] Verify no unique logic is lost

**leaving_home.py:**
- [ ] Review HVAC logic
- [ ] Should be replaced with `transition_to_away()` call
- [ ] Verify Tapo outlet control is preserved (not part of transition)

**pre_arrival.py:**
- [ ] Review HVAC logic
- [ ] Should be replaced with `transition_to_home()` call
- [ ] Verify outdoor light logic is preserved

**arrival_preheat.py:**
- [ ] Check if still needed or redundant with pre_arrival.py
- [ ] Merge logic if duplicate

### 3. Configuration Cleanup

**config/config.yaml:**
- [ ] Remove any temp_coordination specific settings
- [ ] Add new scheduler configuration section
- [ ] Verify schedule.sleep_time and schedule.wake_time are correct
- [ ] Verify temperatures.comfort and temperatures.bedroom_sleep are correct

**Deprecated settings to remove:**
- [ ] Any `temp_coordination:` section
- [ ] Any `coordination:` section

### 4. Documentation Updates

**DEPLOYMENT.md:**
- [ ] Remove temp_coordination cron job (already commented out)
- [ ] Add scheduler.py cron job with explanation
- [ ] Update troubleshooting section

**README.md:**
- [ ] Update architecture diagram if exists
- [ ] Update automation descriptions
- [ ] Reference scheduler instead of temp_coordination

**CLAUDE.md (project instructions):**
- [ ] Update if temp_coordination mentioned
- [ ] Add note about scheduler architecture

**dev/ documentation:**
- [ ] Check for any temp_coordination references in dev/setup/
- [ ] Check dev/workflows/ for outdated procedures

### 5. Test Suite Audit

**tests/ directory:**
- [ ] Check for test_temp_coordination.py (remove if exists)
- [ ] Add test_transitions.py for new module
- [ ] Add test_scheduler.py for new module
- [ ] Update integration tests if needed

### 6. Log Files and Monitoring

**Cron jobs:**
- [ ] Verify temp_coordination cron is removed from Pi
- [ ] Add scheduler.py cron job

**Log files:**
- [ ] Check if temp_coordination.log still exists on Pi
- [ ] Archive or delete old temp_coordination logs
- [ ] Verify scheduler.py will log to appropriate location

**Monitoring:**
- [ ] Update any monitoring dashboards if applicable
- [ ] Update log viewer if it filters by automation name

### 7. State Files

**Runtime state files:**
- [ ] Check if temp_coordination left any state files
- [ ] Remove if found: .temp_coordination_state, etc.
- [ ] Create .scheduler_state with proper structure

### 8. iOS Shortcuts Integration

**Verify shortcuts still work:**
- [ ] "Goodnight" shortcut calls goodnight.py
- [ ] "Good Morning" shortcut calls good_morning.py
- [ ] "Leaving Home" shortcut calls leaving_home.py
- [ ] "I'm Home" shortcut calls appropriate arrival script

**After refactoring:**
- [ ] Test each shortcut end-to-end
- [ ] Verify all devices respond correctly

### 9. Decision Documentation

**status/decisions/:**
- [ ] Review temp_coordination_disabled.md
- [ ] Update with information about scheduler implementation
- [ ] Link to scheduler_implementation.md plan

### 10. Backlog Review

**plans/backlog.md:**
- [ ] Remove any temp_coordination related tasks
- [ ] Add any new tasks discovered during audit
- [ ] Update task: "review the config" - mark as done after audit

## Search Commands

```bash
# Find all references to temp_coordination
grep -r "temp_coordination" --include="*.py" .
grep -r "temp_coordination" --include="*.md" .

# Find duplicate HVAC control logic patterns
grep -r "set_comfort_mode\|set_sleep_mode\|set_away_mode" automations/

# Find old state files
find . -name "*temp_coordination*" -o -name ".coordination*"

# Check crontab
crontab -l | grep -i temp
```

## Findings Template

As audit progresses, document findings here:

### Code Issues Found
- [ ] Issue 1: Description
  - Location: file:line
  - Action: What needs to be done
  - Status: Not started / In progress / Done

### Documentation Issues Found
- [ ] Issue 1: Description
  - Location: file
  - Action: What needs to be done
  - Status: Not started / In progress / Done

### Configuration Issues Found
- [ ] Issue 1: Description
  - Location: file
  - Action: What needs to be done
  - Status: Not started / In progress / Done

## Execution Plan

**When to run audit:**
1. Before starting scheduler implementation (identify issues early)
2. After Phase 3 (Integration) - verify refactoring is complete
3. After Phase 5 (Deployment) - final verification

**Order:**
1. Run search commands
2. Document all findings
3. Prioritize (blocking vs nice-to-have)
4. Fix blocking issues during implementation
5. Fix nice-to-have issues after deployment

## Success Criteria

- [ ] No references to temp_coordination in code
- [ ] No duplicate HVAC logic across automations
- [ ] All documentation updated
- [ ] All tests passing
- [ ] Configuration clean and well-organized
- [ ] Old log files archived/removed
- [ ] iOS Shortcuts verified working

## Notes

- Some findings may reveal new tasks for backlog
- Document any architectural improvements discovered
- Note any tech debt to address later
