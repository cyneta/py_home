# Backlog

## Medium Priority

### Review Temperature Coordination Panel
**Task:** Review TS (Temperature/Status?) panel layout
**Items:**
- Panel title clarity
- Field order optimization
- Information hierarchy


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

## Completed
- ✅ HVAC redesign (Phases 1-5)
- ✅ Remove deprecated night_mode flag system
- ✅ Update all tests for new architecture
- ✅ Implement Tapo get_all_status() method
- ✅ Add runtime state files to .gitignore
- ✅ Remove deprecated backward compatibility methods
- ✅ Push all commits to origin/main
- ✅ Fix test isolation issue - test_leaving_home_calls_update_presence_state
- ✅ Achieve 100% test pass rate (202 passed, 0 skipped)
- ✅ Add filtering to recent log viewer (log level, automation type, keyword search)
- ✅ Implement component timeout pattern (Phases 1-4)
  - Created AsyncRunner helper for async operations with timeouts
  - Added timeouts to all device components (Tapo, Nest, Sensibo)
  - Made timeouts configurable via config.yaml
  - Optimized Tapo queries to run in parallel (4.6x speedup)
  - Dashboard now loads in ~5 seconds (was 20-25 seconds)
- ✅ Fix ECO mode dashboard display
  - Changed "ECO°F" to "ECO (62-80°F)" format showing actual temperature range
  - Clarified that ECO bounds must be set in Google Home app (API read-only)
  - Updated config comments to remove misleading eco_low/eco_high values
  - Updated code documentation to reflect API limitations
