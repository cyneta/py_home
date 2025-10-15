# Backlog

## High Priority

### Tapo Component - Missing get_all_status() Method
**Issue:** Dashboard shows error `'TapoAPI' object has no attribute 'get_all_status'`
**Location:** `components/tapo/client.py`, `server/routes.py:165`
**Impact:** Dashboard /api/tapo/status endpoint returns 500 error
**Solution:** Implement `get_all_status()` method in TapoAPI class to return list of all outlet statuses

### Push Pending Commits to Origin
**Issue:** 7 commits ahead of origin/main (HVAC redesign)
**Commits:**
- 04543de: Phase 5 - Fix ECO mode 400 error and add integration tests
- 5ead998: Phase 4 - Update all automations to use new intent-based API
- 2f23cbd: Phase 3 - Simplify temp_coordination with 3-state logic
- a619fc1: Phase 2 - Redesign Sensibo component with intent-based API
- 1ef426e: Phase 1 - Redesign Nest component with intent-based API
- 7f3dbd7: Refactor logging and prepare HVAC redesign
- 4d815a1: Remove deprecated night_mode flag system and update tests
**Solution:** `git push origin main`

## Medium Priority

### Test Isolation Issue - test_leaving_home_calls_update_presence_state
**Issue:** Test passes individually but fails in full test suite
**Location:** `tests/test_presence_automation_updates.py:132`
**Status:** Currently marked with `@pytest.mark.skip`
**Root Cause:** Test ordering/environment pollution (DRY_RUN env var or module caching)
**Solution:** Investigate pytest-xdist or fixture scoping improvements

### Add .presence_state to .gitignore
**Issue:** Runtime state file shows as untracked in git status
**Location:** `.presence_state` in project root
**Solution:** Add to .gitignore file

## Low Priority - Technical Debt

### Fix 71 Pytest Warnings - Test Return Values
**Issue:** 71 warnings about test functions returning values instead of None
**Pattern:** Tests use `return True` instead of `assert True`
**Files Affected:**
- tests/test_ai_handler.py (14 warnings)
- tests/test_flask_endpoints.py
- tests/test_monitoring.py
- tests/test_state_management.py
- tests/test_write_operations.py
**Solution:** Replace `return <value>` with `assert <value>` in affected tests

### Consider Removing Deprecated Backward Compatibility
**Context:** New HVAC API maintains backward compat with old methods
**Files:** `components/nest/client.py`, `components/sensibo/client.py`
**Old Methods:** `set_temperature()`, `set_eco_mode()`, etc.
**New Methods:** `set_comfort_mode()`, `set_away_mode()`, `set_sleep_mode()`
**Decision:** Keep for now, revisit after 1-2 months of production use

## Completed
- ✅ HVAC redesign (Phases 1-5)
- ✅ Remove deprecated night_mode flag system
- ✅ Update all tests for new architecture
- ✅ Achieve 99% test pass rate (201 passed, 3 skipped)
