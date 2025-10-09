# py_home Testing Gap Analysis & Remediation Plan

**Created:** 2025-10-07
**Status:** Active
**Current Coverage:** ~45-50% functional test coverage
**Target Coverage:** 80% functional test coverage

---

## Executive Summary

**Current Coverage:** ~45-50% functional test coverage
**Major Gaps:** Write operations untested, missing components (Alen, Roborock), no integration tests, automation logic unverified
**Priority:** Critical gaps in device control testing and end-to-end workflows

---

## Part 1: Component Coverage Analysis

### 1.1 Tapo Smart Plugs ✅ PARTIAL
**What Exists:**
- Components: client.py (9 methods)
- Exported functions: turn_on(), turn_off(), turn_on_all(), turn_off_all(), get_status()
- Test files: components/tapo/test.py, test_all.py

**What's Tested:**
- ✅ Import validation
- ✅ Connection to 4 plugs
- ✅ Status reading (on/off, WiFi signal)
- ✅ Error handling (device timeout)

**What's NOT Tested:**
- ❌ turn_on() - No test that actually turns device on
- ❌ turn_off() - No test that actually turns device off
- ❌ turn_on_all() - No test
- ❌ turn_off_all() - No test
- ❌ State verification after control
- ❌ Concurrent control operations
- ❌ Invalid device name handling

**Gap Score:** 40% (reads work, writes untested)

---

### 1.2 Nest Thermostat ✅ PARTIAL
**What Exists:**
- Components: client.py (NestAPI class)
- Exported functions: set_temperature(), get_status(), set_mode()
- Test files: components/nest/test.py, test_all.py

**What's Tested:**
- ✅ Import validation
- ✅ Status reading (temp, humidity, mode, HVAC state)
- ✅ Connection to Google API

**What's NOT Tested:**
- ❌ set_temperature() - No test that changes temperature
- ❌ set_mode() - No test that changes mode (heat/cool/off)
- ❌ Temperature change verification
- ❌ Invalid temperature handling (e.g., 999°F)
- ❌ Mode transitions (heat→cool, etc.)
- ❌ Token refresh flow
- ❌ API rate limiting

**Gap Score:** 35% (reads work, writes untested)

---

### 1.3 Sensibo AC ✅ PARTIAL
**What Exists:**
- Components: client.py (SensiboAPI class)
- Exported functions: set_temperature(), turn_on(), turn_off(), get_status()
- Test files: components/sensibo/test.py, test_all.py

**What's Tested:**
- ✅ Import validation
- ✅ Status reading (power, mode, temperature, humidity)
- ✅ Connection to Sensibo API

**What's NOT Tested:**
- ❌ set_temperature() - No test
- ❌ turn_on() - No test
- ❌ turn_off() - No test
- ❌ Mode changes (cool/heat/fan)
- ❌ Fan speed changes
- ❌ Invalid settings handling

**Gap Score:** 35% (reads work, writes untested)

---

### 1.4 Network Presence ✅ MINIMAL
**What Exists:**
- Components: presence.py (3 functions)
- Exported functions: is_device_home(), scan_network(), get_device_info()
- Test files: components/network/test.py, test_all.py

**What's Tested:**
- ✅ Import validation
- ✅ Localhost ping detection
- ✅ Platform compatibility check

**What's NOT Tested:**
- ❌ Real device detection (only localhost)
- ❌ ARP scan method
- ❌ MAC address detection
- ❌ scan_network() function
- ❌ get_device_info() function
- ❌ False positive/negative scenarios
- ❌ Network timeout handling

**Gap Score:** 30% (basic structure only)

---

### 1.5 Alen Air Purifiers ❌ MISSING
**Status:** Component doesn't exist (deferred in migration)

**Planned:**
- Tuya API integration
- 2 devices (bedroom + living room)
- Functions: get_air_quality(), set_mode(), get_status()
- Read PM2.5, humidity, temperature

**Gap Score:** 0% (not implemented)

---

### 1.6 Roborock Vacuum ❌ MISSING
**Status:** Component doesn't exist (deferred in migration)

**Planned:**
- Roborock Cloud API or MQTT
- Functions: start_cleaning(), stop(), dock(), get_status()

**Gap Score:** 0% (not implemented)

---

## Part 2: Service API Coverage Analysis

### 2.1 OpenWeather ✅ GOOD
**What Exists:**
- services/openweather.py (3 methods)
- Functions: get_current_weather(), get_forecast(), get_weather_summary()

**What's Tested:**
- ✅ Live API call
- ✅ Data parsing (temp, humidity, conditions)
- ✅ Default location handling

**What's NOT Tested:**
- ❌ get_forecast() function
- ❌ get_weather_summary() function
- ❌ Invalid location handling
- ❌ API key error handling
- ❌ Network timeout

**Gap Score:** 60% (primary function tested)

---

### 2.2 Google Maps ✅ GOOD
**What Exists:**
- services/google_maps.py
- Functions: get_travel_time(), check_route_warnings()
- Standalone test: services/test_google_maps.py (NOT integrated)

**What's Tested (in test_all.py):**
- ✅ Live API call Chicago→Milwaukee
- ✅ Basic route calculation

**What's Tested (in standalone test):**
- ✅ 3 subtests: route calculation, default origin, invalid location
- ❌ NOT run by test_all.py

**What's NOT Tested:**
- ❌ check_route_warnings() function
- ❌ Traffic level accuracy
- ❌ Multiple route comparison
- ❌ Walking/transit modes

**Gap Score:** 50% (basic function works, advanced features untested)

---

### 2.3 GitHub API ✅ MINIMAL
**What Exists:**
- services/github.py (GitHubAPI class)
- Functions: add_task_to_todo(), get_repo_info(), get_file_contents(), update_file()
- Standalone test: services/test_github.py (NOT integrated)

**What's Tested:**
- ✅ API authentication
- ✅ get_repo_info() - read only
- ✅ get_file_contents() - read TODO.md

**What's NOT Tested:**
- ❌ add_task_to_todo() - No write test
- ❌ update_file() - No write test
- ❌ Commit creation
- ❌ File SHA handling
- ❌ Concurrent write conflicts

**Gap Score:** 40% (reads only, writes untested)

---

### 2.4 Checkvist API ✅ MINIMAL
**What Exists:**
- services/checkvist.py (CheckvistAPI class)
- Functions: add_task(), get_lists(), get_tasks()
- Standalone test: services/test_checkvist.py (NOT integrated)

**What's Tested:**
- ✅ API authentication
- ✅ get_lists() - read lists
- ✅ get_tasks() - read tasks

**What's NOT Tested:**
- ❌ add_task() - No write test
- ❌ Task completion
- ❌ Task priority/due dates

**Gap Score:** 40% (reads only, writes untested)

---

### 2.5 Notifications ⚠️ NOT TESTED
**What Exists:**
- lib/notifications.py
- Functions: send()
- Test file: lib/test_notifications.py (mock only)

**What's Tested:**
- ✅ Module imports
- ✅ Function signature validation

**What's NOT Tested:**
- ❌ Actual notification sending (mock only)
- ❌ Pushover integration
- ❌ ntfy integration
- ❌ Retry logic
- ❌ Error handling

**Gap Score:** 20% (structure only)

---

## Part 3: Automation Script Coverage

### 3.1 All 9 Automation Scripts ⚠️ STRUCTURE ONLY
**What Exists:**
1. leaving_home.py - Away mode
2. goodnight.py - Sleep mode
3. im_home.py - Welcome home
4. good_morning.py - Morning routine
5. travel_time.py - Traffic queries
6. task_router.py - AI task routing
7. temp_coordination.py - HVAC coordination
8. presence_monitor.py - WiFi presence
9. traffic_alert.py - I-80 traffic

**What's Tested:**
- ✅ All import successfully
- ✅ All have run() function
- ✅ File structure validation

**What's NOT Tested:**
- ❌ Actual execution (no dry-run mode)
- ❌ Logic flow validation
- ❌ Device control sequences
- ❌ Error handling within scripts
- ❌ State transitions
- ❌ Notification sending
- ❌ API calls from automations

**Test Files:**
- tests/test_automations.py exists but NOT integrated into test_all.py
- Only validates structure, doesn't execute logic

**Gap Score:** 25% (structure only, no functional testing)

---

## Part 4: Flask Server Coverage

### 4.1 Flask Endpoints ⚠️ MINIMAL
**What Exists:**
- 7 endpoints in server/routes.py:
  1. GET / - Health check
  2. GET /status - System status
  3. POST /leaving-home
  4. POST /goodnight
  5. POST /im-home
  6. POST /good-morning
  7. GET/POST /travel-time
  8. POST /add-task

**What's Tested (test_all.py):**
- ✅ GET /status - Basic health check
- ❌ Skips if server not running

**What's Tested (test_server.py - NOT integrated):**
- ✅ GET / - Health check
- ✅ GET /status
- ✅ GET /travel-time
- ❌ POST endpoints commented out

**What's NOT Tested:**
- ❌ All POST endpoints (leaving-home, goodnight, etc.)
- ❌ Authentication flow
- ❌ Background script execution
- ❌ Concurrent requests
- ❌ Error responses
- ❌ Request validation

**Gap Score:** 30% (health checks only)

---

## Part 5: Integration & End-to-End Testing

### 5.1 Integration Tests ❌ NONE
**Missing Tests:**
- ❌ Voice → iOS Shortcut → Flask → Automation → Device (full flow)
- ❌ Multiple automation scripts running concurrently
- ❌ Device state persistence across scripts
- ❌ Notification delivery verification
- ❌ Error recovery scenarios
- ❌ Automation chaining (one script triggers another)

**Gap Score:** 0%

---

### 5.2 Error Handling Tests ❌ NONE
**Missing Tests:**
- ❌ API timeout handling
- ❌ Invalid credentials
- ❌ Network disconnection
- ❌ Device offline scenarios
- ❌ Rate limiting
- ❌ Malformed requests
- ❌ Concurrent write conflicts

**Gap Score:** 0%

---

### 5.3 State Management Tests ❌ NONE
**Missing Tests:**
- ❌ Presence state file (.presence_state)
- ❌ State transitions (home→away→home)
- ❌ Duplicate event prevention
- ❌ State recovery after crash
- ❌ Concurrent state updates

**Gap Score:** 0%

---

## Part 6: Test Infrastructure Gaps

### 6.1 Test Organization ⚠️ FRAGMENTED
**Current State:**
- test_all.py (25 integrated tests)
- 6 standalone test files NOT integrated:
  - services/test_google_maps.py
  - services/test_github.py
  - services/test_checkvist.py
  - lib/test_notifications.py
  - tests/test_automations.py (detailed version)
  - test_server.py

**Gap:** Duplicate tests, inconsistent execution

---

### 6.2 Test Modes ⚠️ LIMITED
**What Exists:**
- --quick mode (skips API tests)
- --only mode (test specific component)

**What's Missing:**
- ❌ --dry-run mode for automations (doesn't actually change devices)
- ❌ --integration mode (run end-to-end tests)
- ❌ --mock mode (use mocked APIs)
- ❌ --ci mode (for CI/CD pipelines)

---

### 6.3 Test Data ❌ MISSING
**No fixtures or test data for:**
- Mock API responses
- Sample device configurations
- Test automation sequences
- Error scenarios
- Edge cases

---

## Part 7: Priority Matrix

### Critical (P0) - Must Fix
1. **Add write operation tests** for all components
   - Impact: High (can't verify device control works)
   - Effort: Medium (need test fixtures)
   - Risk: System might not work in production

2. **Automation execution tests** with dry-run mode
   - Impact: High (automations are core functionality)
   - Effort: High (need dry-run implementation)
   - Risk: Broken automations go undetected

3. **Flask endpoint tests** for all POST endpoints
   - Impact: High (iOS Shortcuts depend on these)
   - Effort: Low (straightforward HTTP tests)
   - Risk: Voice control won't work

### High (P1) - Should Fix
4. **Integration tests** for end-to-end workflows
   - Impact: High (catches real-world issues)
   - Effort: High (complex setup)
   - Priority: After P0 items work

5. **Error handling tests** for all API calls
   - Impact: Medium (system might crash on errors)
   - Effort: Medium
   - Priority: Before production deployment

6. **Consolidate test infrastructure**
   - Impact: Medium (developer experience)
   - Effort: Low (just organization)
   - Priority: Soon

### Medium (P2) - Nice to Have
7. **Network presence comprehensive tests**
   - Impact: Medium (backup system)
   - Effort: Medium

8. **State management tests**
   - Impact: Medium (edge case bugs)
   - Effort: Medium

### Low (P3) - Future
9. **Alen air purifier component** + tests
   - Impact: Low (hardware not available)
   - Effort: High

10. **Roborock vacuum component** + tests
    - Impact: Low (hardware not available)
    - Effort: High

---

## Part 8: Remediation Plan

### Phase 1: Critical Fixes (3-4 hours)
**Goal:** Test all write operations safely

1. **Add dry-run mode to components** (1.5h)
   - Add --dry-run flag to each component
   - Print actions instead of executing
   - Update turn_on(), turn_off(), set_temperature(), etc.

2. **Write operation tests** (1.5h)
   - Test Tapo turn_on/off in dry-run mode
   - Test Nest set_temperature in dry-run mode
   - Test Sensibo turn_on/off in dry-run mode
   - Verify commands formatted correctly

3. **Flask POST endpoint tests** (1h)
   - Test all 5 POST endpoints
   - Verify background execution
   - Test authentication

### Phase 2: Automation Testing (2-3 hours)
**Goal:** Verify automation logic

4. **Implement dry-run mode for automations** (1h)
   - Add DRY_RUN env var or --dry-run flag
   - Skip actual device calls
   - Log what would happen

5. **Automation execution tests** (1.5h)
   - Run each automation in dry-run
   - Verify sequence of operations
   - Check error handling

6. **Integrate standalone tests** (0.5h)
   - Merge services/test_*.py into test_all.py
   - Remove duplication
   - Update test count

### Phase 3: Integration Testing (3-4 hours)
**Goal:** Test end-to-end workflows

7. **Create integration test suite** (2h)
   - tests/test_integration.py
   - Test voice → webhook → automation → device flow
   - Mock device responses

8. **Error scenario tests** (1.5h)
   - API timeouts
   - Invalid inputs
   - Network errors
   - Device offline

9. **State management tests** (0.5h)
   - Test .presence_state file
   - Test state transitions

### Phase 4: Polish (1-2 hours)
**Goal:** Clean test infrastructure

10. **Test organization** (0.5h)
    - Move all tests to tests/ directory
    - Consistent naming
    - Update documentation

11. **CI/CD mode** (0.5h)
    - Add --ci flag
    - Mock all external APIs
    - Fast execution

12. **Documentation** (0.5h)
    - Update TESTING_PLAN.md
    - Add test coverage report
    - Document test modes

---

## Success Metrics

**Target Coverage:**
- Component functions: 85% (currently 40%)
- Automation scripts: 80% (currently 25%)
- Flask endpoints: 90% (currently 30%)
- Integration tests: 70% (currently 0%)
- Error handling: 75% (currently 0%)

**Overall Target: 80% functional test coverage** (currently ~45%)

---

## Estimated Total Effort: 9-13 hours

**Breakdown:**
- Phase 1 (Critical): 3-4 hours
- Phase 2 (Automation): 2-3 hours
- Phase 3 (Integration): 3-4 hours
- Phase 4 (Polish): 1-2 hours

**Timeline:** 2-3 development sessions

**Priority:** Complete Phase 1 before production deployment

---

**Last Updated:** 2025-10-07
