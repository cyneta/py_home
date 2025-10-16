# Backlog

## High Priority - Core System

### Fix Notifications
**Task:** Debug notification issues
**Items:**
- Get ntfy notifications working
- Fix blank Shortcuts/Scriptable notifications

### Review Tapo Outlet Configuration
**Task:** Review and update Tapo outlet names and assignments
**Items:**
- Review outlet naming conventions
- Review master bedroom heater management on Tapo outlet


## Medium Priority - Device Integrations

### Integrate Alen Air Purifiers
**Task:** Complete Tuya/Alen air purifier integration
**Status:** Partial config exists in config.yaml, needs implementation

### Integrate Roborock Robot Vacuum
**Task:** Add Roborock vacuum control and status to automation system

### Set Up Grow Light Automation
**Task:** Configure table light as grow light with time-based automation


## Medium Priority - Productivity Shortcuts

### YouTube Music Integration
**Task:** Create shortcuts for playlists, favorites, playback control

### Checkvist Integration
**Task:** Add shortcuts for task management integration

### Siri Shortcuts for HomePod
**Task:** Create Siri shortcuts for controlling HomePod speakers


## Low Priority - Technical Debt

### Audit and Understand Test Suite
**Task:** Review test suite structure, coverage, and mocking patterns
**Goal:** Better understand testing approach for future development

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
- ✅ Review TempStick (Outdoor Sensor) dashboard panel
  - Improved title clarity: "TempStick" → "Outdoor Sensor"
  - Optimized field order: Temperature → Humidity → Battery → Sensor Status
  - Enhanced information hierarchy with battery color-coding
