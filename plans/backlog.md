# Backlog

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
