# Test Suite Audit: Deprecated API Usage

**Date:** 2025-10-16
**Status:** Audit Complete - Migration Plan Ready

## Executive Summary

Audited all test files for usage of deprecated HVAC APIs (`set_temperature()`, `set_mode()`). Found **10 instances** across **3 test files**. All instances are in infrastructure/error-handling tests, not behavioral tests. Migration is straightforward.

## Audit Scope

**Files Scanned:** All tests/*.py files (21 files)
**Deprecated Patterns Searched:**
- `.set_temperature()`
- `.set_mode()`

## Findings Summary

### ✅ Clean Files (No Deprecated API Usage)

The following test files are already clean:
- `test_nest_redesign.py` - Uses new intent-based API
- `test_sensibo_redesign.py` - Uses new intent-based API
- `test_automations.py` - Tests automation workflows only
- `test_night_mode.py` - Tests time-based logic only
- All other test files (18 total)

### ⚠️ Files Needing Migration (10 Instances Total)

#### 1. test_integration.py (2 instances)

**Lines 233, 264:**
```python
# Line 233 - Device coordination test
nest.set_temperature(68)  # ❌ Should use set_sleep_mode()

# Line 264 - Component interaction test
nest.set_temperature(72)  # ❌ Should use set_comfort_mode()
```

**Context:** Integration tests verifying device coordination
**Impact:** Tests still pass (backward compatible), but don't validate new API
**Migration:** Replace with `nest.set_sleep_mode()` and `nest.set_comfort_mode()`

#### 2. test_error_handling.py (4 instances)

**Lines 76, 166, 255, 334:**
```python
# Line 76 - Invalid credentials test
nest.set_temperature(70)  # ❌ Generic error handling test

# Line 166 - Invalid temperature test
nest.set_temperature(temp)  # ❌ Boundary validation test

# Line 255 - Rate limiting test
nest.set_temperature(temp)  # ❌ Thread safety test

# Line 334 - Performance test
nest.set_temperature(70 + i)  # ❌ Response time test
```

**Context:** Infrastructure tests for error handling, validation, rate limiting
**Impact:** Tests generic API behavior, not HVAC logic
**Migration:** Keep `set_temperature()` for backward compatibility testing, or migrate to `set_comfort_mode()`

#### 3. test_write_operations.py (4 instances)

**Lines 109, 131, 197:**
```python
# Line 109 - Nest dry-run test (HEAT mode)
nest.set_temperature(72, mode='HEAT')  # ❌ Tests dry-run logging

# Line 131 - Nest dry-run test (COOL mode)
nest.set_temperature(68, mode='COOL')  # ❌ Tests dry-run logging

# Line 197 - Sensibo dry-run test
sensibo.set_temperature(70)  # ❌ Tests dry-run logging
```

**Context:** Tests that dry-run mode logs commands without executing
**Impact:** Tests infrastructure behavior, not HVAC logic
**Migration:** Migrate to test new API dry-run behavior

## Test Categorization

### Category A: Behavioral Tests (Need Migration)
- **test_integration.py** (2 instances) - Tests actual HVAC state transitions
- **Priority:** HIGH - Should validate new intent-based API behavior

### Category B: Infrastructure Tests (Optional Migration)
- **test_error_handling.py** (4 instances) - Tests error cases, rate limiting
- **test_write_operations.py** (4 instances) - Tests dry-run logging
- **Priority:** MEDIUM - Could keep for backward compatibility testing

## Migration Plan

### Phase 1: High Priority (test_integration.py)

**File:** `tests/test_integration.py`
**Changes:**
```python
# Line 233: Device coordination test
# Old:
nest.set_temperature(68)
# New:
nest.set_sleep_mode()

# Line 264: Component interaction test
# Old:
nest.set_temperature(72)
# New:
nest.set_comfort_mode()
```

**Rationale:** Integration tests should validate production API patterns

### Phase 2: Medium Priority (Infrastructure Tests)

**Option A: Migrate to New API**
- Update test_error_handling.py to use `set_comfort_mode()`
- Update test_write_operations.py to use `set_comfort_mode()` / `set_sleep_mode()`
- Validates new API error handling and dry-run behavior

**Option B: Keep for Backward Compatibility**
- Leave as-is to test deprecated API still functions
- Add comments explaining these test deprecated methods intentionally

**Recommendation:** Option A - Migrate to new API for consistency

### Phase 3: Add Deprecation Warnings

After migrating tests, add deprecation warnings to old methods:

**File:** `components/nest/client.py`
```python
def set_temperature(self, temp_f: float, mode: str = None):
    """
    DEPRECATED: Use set_comfort_mode(), set_sleep_mode(), or set_away_mode() instead.

    This method is maintained for backward compatibility only.
    """
    import warnings
    warnings.warn(
        "set_temperature() is deprecated. Use set_comfort_mode(), set_sleep_mode(), or set_away_mode()",
        DeprecationWarning,
        stacklevel=2
    )
    # ... existing implementation
```

**File:** `components/sensibo/client.py`
```python
def set_temperature(self, temp_f: float):
    """
    DEPRECATED: Use set_comfort_mode() or set_sleep_mode() instead.

    This method is maintained for backward compatibility only.
    """
    import warnings
    warnings.warn(
        "set_temperature() is deprecated. Use set_comfort_mode() or set_sleep_mode()",
        DeprecationWarning,
        stacklevel=2
    )
    # ... existing implementation
```

## Testing Strategy

1. **Before Migration:**
   - Run full test suite: `pytest tests/`
   - Document baseline pass/fail status

2. **During Migration:**
   - Migrate one file at a time
   - Run that file's tests after each change
   - Verify no regressions

3. **After Migration:**
   - Run full test suite again
   - Verify all tests still pass
   - Check for deprecation warnings

4. **Validation:**
   - Search codebase to confirm no deprecated API calls in active code
   - Only test files and backward-compatible infrastructure should reference old APIs

## Risk Assessment

**Migration Risk:** ✅ LOW
- All changes confined to test files
- Production code already migrated
- Backward compatibility maintained

**Test Coverage Risk:** ✅ NONE
- Migrated tests will validate same behavior with new API
- No test coverage lost

**Regression Risk:** ✅ LOW
- Tests run in dry-run mode (no actual device calls)
- Changes are straightforward replacements

## Success Criteria

✅ **Complete when:**
1. All 10 deprecated API calls in tests migrated or documented
2. Full test suite passes
3. Deprecation warnings added to old methods
4. No deprecated API usage in production code (automations, components, server)

## Implementation Checklist

- [ ] Migrate test_integration.py (2 instances)
- [ ] Migrate test_error_handling.py (4 instances)
- [ ] Migrate test_write_operations.py (4 instances)
- [ ] Add deprecation warnings to nest.set_temperature()
- [ ] Add deprecation warnings to nest.set_mode()
- [ ] Add deprecation warnings to sensibo.set_temperature()
- [ ] Run full test suite and verify pass
- [ ] Final grep to confirm no deprecated usage in active code

## Notes

- test_tuya.py had false positive (Tuya has its own set_temperature for air purifier, unrelated to HVAC)
- AI handler system prompt not addressed in this audit (separate issue)
- Documentation updates deferred to backlog (plans/backlog.md)

---

**Audit Completed:** 2025-10-16 15:15
**Auditor:** Claude Code
**Files Examined:** 21 test files
**Deprecated Patterns Found:** 10 instances across 3 files
**Migration Complexity:** Low (straightforward replacements)
