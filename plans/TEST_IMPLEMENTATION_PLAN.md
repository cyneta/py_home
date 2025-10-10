# Test Implementation Plan
**Date:** 2025-10-10
**Purpose:** Address test coverage gaps identified in system audit
**Current Coverage:** 93% (54/63 tests passing)
**Target Coverage:** 98%+ with all critical systems tested

---

## Executive Summary

This plan addresses test coverage gaps prioritized by safety impact and system criticality. The focus is on **safety-critical monitoring systems** with zero test coverage, followed by library functions and edge case handling.

**Key Priorities:**
1. 🔴 **HIGH:** Monitoring scripts (tempstick, presence) - Safety-critical
2. 🔴 **HIGH:** State file management - Core functionality
3. 🟡 **MEDIUM:** night_mode library - Used by multiple automations
4. 🟡 **MEDIUM:** Component error handling - Resilience
5. 🟡 **MEDIUM:** Config validation - System integrity

---

## Phase 1: Safety-Critical Systems (HIGH Priority)

### Task 1.1: Test Monitoring Scripts
**File to Create:** `tests/test_monitoring.py`
**Effort:** 2 hours
**Priority:** 🔴 CRITICAL

**Why Critical:** These scripts run every 1-5 minutes and detect freeze risks (tempstick) and presence changes. Silent failures could mean:
- Frozen pipes (property damage $$$)
- Failed leaving/arriving automations (lights on when away, no preheat)

**Scripts to Test:**
1. `monitors/tempstick_monitor.py` (151 lines) - Freeze detection, threshold alerts
2. `monitors/presence_monitor.py` (120 lines) - Home/away detection, automation triggers

**Test Coverage:**

#### tempstick_monitor.py Tests
```python
def test_tempstick_monitor_structure():
    """Verify monitor has required functions and constants"""
    - CHECK_INTERVAL defined
    - run() function exists
    - Proper logging setup

def test_tempstick_freeze_detection():
    """Test freeze alert triggering logic"""
    - Mock temperature below threshold (40°F)
    - Verify alert sent with correct priority
    - Check alert rate limiting (no spam)

def test_tempstick_api_failure_handling():
    """Test behavior when Tempstick API fails"""
    - Mock API timeout
    - Mock API 401/403 (auth failure)
    - Verify error notification sent
    - Verify script doesn't crash

def test_tempstick_state_persistence():
    """Test alert state tracking"""
    - Verify last_alert_time persists
    - Check cooldown period respected
    - Verify state file format

def test_tempstick_recovery_alert():
    """Test recovery notification when temp rises"""
    - Mock temp above threshold after alert
    - Verify recovery notification sent
    - Check alert state reset
```

#### presence_monitor.py Tests
```python
def test_presence_monitor_structure():
    """Verify monitor has required functions"""
    - run() function exists
    - Network check logic present
    - State persistence working

def test_presence_detection_home_to_away():
    """Test leaving home detection"""
    - Mock device offline (192.168.50.189)
    - Verify .presence_state updated
    - Check leaving_home automation triggered

def test_presence_detection_away_to_home():
    """Test arriving home detection"""
    - Mock device online
    - Verify .presence_state updated
    - Check im_home automation triggered

def test_presence_debounce_logic():
    """Test presence change debouncing"""
    - Mock brief network blip (device offline 30s)
    - Verify no automation triggered (not long enough)
    - Check state doesn't change

def test_presence_state_file_management():
    """Test state persistence"""
    - Verify .presence_state created on first run
    - Check state format (home/away/unknown)
    - Verify state survives script restart

def test_presence_network_failure_handling():
    """Test behavior when network check fails"""
    - Mock network exception
    - Verify script doesn't crash
    - Check error logged appropriately
```

**Success Criteria:**
- ✅ 10+ tests covering all critical paths
- ✅ Both scripts tested in isolation
- ✅ All failure modes covered (API errors, network issues, state corruption)
- ✅ Test can run without real API calls (mocked)

**Implementation Steps:**
1. Create `tests/test_monitoring.py`
2. Import pytest and mock libraries
3. Write tests for tempstick_monitor (5 tests)
4. Write tests for presence_monitor (6 tests)
5. Run with `python -m pytest tests/test_monitoring.py -v`
6. Fix any failures
7. Update TEST_RESULTS_2025-10-10.md with new coverage

---

### Task 1.2: Test State File Management
**File to Create:** `tests/test_state_management.py`
**Effort:** 1 hour
**Priority:** 🔴 HIGH

**Why Important:** State files persist critical data between script runs. Corruption or invalid format could break automations.

**State Files to Test:**
1. `.presence_state` - home/away/unknown status
2. `.night_mode` - night mode on/off
3. `.alert_state/alert_history.json` - Rate limiting data

**Test Coverage:**

```python
def test_presence_state_file_format():
    """Test .presence_state format validation"""
    - Verify valid states accepted (home, away, unknown)
    - Reject invalid states
    - Handle missing file (create default)

def test_night_mode_state_file():
    """Test .night_mode state management"""
    - Verify lib.night_mode.is_night_mode() reads file
    - Check lib.night_mode.set_night_mode() writes file
    - Test file missing (default to False)
    - Verify file format (True/False/1/0)

def test_alert_state_json_format():
    """Test alert_history.json format"""
    - Verify JSON structure valid
    - Check required fields present
    - Test corrupted JSON handling
    - Verify migration from old format

def test_state_file_concurrent_access():
    """Test multiple scripts accessing state files"""
    - Mock 2 scripts reading .presence_state simultaneously
    - Verify no file corruption
    - Check file locking if implemented

def test_state_file_recovery():
    """Test recovery from corrupted state files"""
    - Write invalid data to .presence_state
    - Verify script recovers gracefully
    - Check default value used
    - Verify error logged
```

**Success Criteria:**
- ✅ All 3 state file types tested
- ✅ Corruption recovery validated
- ✅ Concurrent access safe
- ✅ Default values work when files missing

---

## Phase 2: Core Libraries (MEDIUM Priority)

### Task 2.1: Test night_mode Library
**File to Create:** `tests/test_night_mode.py`
**Effort:** 1 hour
**Priority:** 🟡 MEDIUM

**Why Important:** Used by `temp_coordination.py` (runs every 15 min), `goodnight.py`, and `good_morning.py`. Currently only manually tested.

**Test Coverage:**

```python
def test_is_night_mode_true():
    """Test night mode detection when active"""
    - Create .night_mode file with True
    - Verify is_night_mode() returns True

def test_is_night_mode_false():
    """Test night mode detection when inactive"""
    - Create .night_mode file with False
    - Verify is_night_mode() returns False

def test_is_night_mode_missing_file():
    """Test default behavior when file missing"""
    - Delete .night_mode file
    - Verify is_night_mode() returns False (default)

def test_set_night_mode_on():
    """Test enabling night mode"""
    - Call set_night_mode(True)
    - Verify .night_mode file contains True
    - Verify is_night_mode() returns True

def test_set_night_mode_off():
    """Test disabling night mode"""
    - Call set_night_mode(False)
    - Verify .night_mode file contains False
    - Verify is_night_mode() returns False

def test_night_mode_file_format_variants():
    """Test different valid file formats"""
    - Test "True", "true", "1", "yes"
    - Test "False", "false", "0", "no"
    - Verify all recognized correctly

def test_night_mode_file_permissions():
    """Test file created with correct permissions"""
    - Call set_night_mode(True)
    - Verify file readable by automation user
    - Check file not world-writable
```

**Success Criteria:**
- ✅ All functions in `lib/night_mode.py` tested
- ✅ Edge cases covered (missing file, invalid format)
- ✅ Test runs without modifying production .night_mode file

---

### Task 2.2: Test Component Error Handling
**File to Create:** `tests/test_error_handling.py`
**Effort:** 2 hours
**Priority:** 🟡 MEDIUM

**Why Important:** Current test suite only tests "happy path" - need to verify resilience when APIs fail.

**Components to Test:**
1. Nest API client - API errors, token refresh failure
2. Sensibo API client - API timeout, invalid response
3. Tapo smart plug client - Device offline, network error
4. Network presence detection - Ping timeout, invalid IP

**Test Coverage:**

```python
# Nest API Error Tests
def test_nest_api_missing_temperature():
    """Test Nest API fails fast when temperature is None"""
    with mock.patch('components.nest.client._get') as mock_get:
        mock_get.return_value = {'traits': {}}  # No temperature data
        with pytest.raises(ValueError, match="no temperature data"):
            NestAPI().get_status()

def test_nest_api_missing_mode():
    """Test Nest API fails fast when mode is None"""
    with mock.patch('components.nest.client._get') as mock_get:
        mock_get.return_value = {'traits': {'sdm.devices.traits.Temperature': {...}}}
        with pytest.raises(ValueError, match="no mode data"):
            NestAPI().get_status()

def test_nest_api_token_refresh_failure():
    """Test behavior when OAuth token refresh fails"""
    with mock.patch('requests.post') as mock_post:
        mock_post.return_value.raise_for_status.side_effect = HTTPError("401 Unauthorized")
        with pytest.raises(HTTPError):
            NestAPI()._ensure_token()

def test_nest_api_network_timeout():
    """Test behavior when API request times out"""
    with mock.patch('requests.get') as mock_get:
        mock_get.side_effect = requests.Timeout("Request timeout")
        with pytest.raises(requests.Timeout):
            NestAPI()._get("enterprises/...")

# Sensibo API Error Tests
def test_sensibo_api_timeout():
    """Test Sensibo API timeout handling"""
    with mock.patch('requests.get') as mock_get:
        mock_get.side_effect = requests.Timeout("Request timeout")
        with pytest.raises(requests.Timeout):
            SensiboAPI().get_status()

def test_sensibo_api_invalid_response():
    """Test handling of malformed Sensibo API response"""
    with mock.patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {}  # Missing required fields
        with pytest.raises(KeyError):
            SensiboAPI().get_status()

# Tapo Error Tests
def test_tapo_device_offline():
    """Test behavior when Tapo device is offline"""
    with mock.patch('components.tapo.client.TapoClient') as mock_client:
        mock_client.side_effect = TimeoutError("Device unreachable")
        # Should log error but not crash
        result = get_device_status('192.168.50.101')
        assert result is None or 'error' in result

# Network Error Tests
def test_network_presence_timeout():
    """Test presence detection when ping times out"""
    with mock.patch('subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired('ping', 5)
        result = is_device_home('192.168.50.189')
        assert result == False  # Treat timeout as "not home"

# temp_coordination Error Tests
def test_temp_coordination_nest_none_setpoint():
    """Test temp_coordination handles None setpoint gracefully"""
    # Mock Nest returning None for setpoint (ECO mode)
    with mock.patch('components.nest.NestAPI.get_status') as mock_nest:
        mock_nest.return_value = {
            'current_temp_f': 72.5,
            'mode': 'HEAT',
            'heat_setpoint_f': None,  # ECO mode
            'hvac_status': 'OFF'
        }
        result = temp_coordination.run()
        assert "Nest in ECO" in result['changes_made']
        assert len(result['errors']) == 0
```

**Success Criteria:**
- ✅ All API failure modes tested
- ✅ No crashes on network errors
- ✅ Descriptive error messages logged
- ✅ Tests run without real API calls

---

### Task 2.3: Test Config Validation
**File to Update:** `tests/test_config.py`
**Effort:** 45 minutes
**Priority:** 🟡 MEDIUM

**Why Important:** Current config tests have 50% pass rate due to legacy assumptions (Tesla integration, old location names).

**Current Failures:**
1. `test_config_has_expected_sections` - Expects 'tesla' section (not in py_home)
2. `test_get_function` - Tests 'tesla.email' (not applicable)
3. `test_locations_config` - Expects 'milwaukee' location (not in current config)

**Changes Needed:**

```python
def test_config_has_expected_sections():
    """Test config has all py_home required sections"""
    required = ['nest', 'sensibo', 'tapo', 'locations', 'automation', 'notifications']
    # REMOVED: 'tesla' (not used in py_home)
    for section in required:
        assert section in config, f"Missing required section: {section}"

def test_get_function():
    """Test config.get() retrieves nested values"""
    # CHANGED: Use nest config instead of tesla
    assert config.get('nest.project_id') is not None
    assert config.get('sensibo.api_key') is not None

def test_locations_config():
    """Test locations are properly configured"""
    # CHANGED: Use actual py_home locations
    assert 'home' in config['locations']
    assert 'work' in config['locations']
    # REMOVED: 'milwaukee' check
```

**Additional Tests to Add:**

```python
def test_config_env_variable_substitution():
    """Test ${ENV_VAR} substitution works"""
    # Verify API keys don't contain literal ${...}
    assert '${' not in config['nest']['client_secret']
    assert '${' not in config['sensibo']['api_key']

def test_config_nested_access():
    """Test deeply nested config access"""
    night_temp = config['automation']['temp_coordination']['night_mode_temp_f']
    assert isinstance(night_temp, (int, float))
    assert 60 <= night_temp <= 75  # Reasonable range

def test_config_required_fields_present():
    """Test all critical config fields exist"""
    critical_fields = [
        'nest.project_id',
        'nest.device_id',
        'sensibo.api_key',
        'sensibo.device_id',
        'notifications.ntfy_topic'
    ]
    for field in critical_fields:
        parts = field.split('.')
        value = config
        for part in parts:
            value = value[part]
        assert value is not None, f"Missing critical field: {field}"
```

**Success Criteria:**
- ✅ All config tests passing (6/6)
- ✅ No legacy test assumptions
- ✅ Tests match actual py_home config structure

---

## Phase 3: Edge Cases & Polish (LOW Priority)

### Task 3.1: Flask Server Edge Cases
**File to Update:** `tests/test_flask_endpoints.py`
**Effort:** 1 hour
**Priority:** 🔵 LOW

**Current Coverage:** Only 3/10 endpoints tested
**Need to Add:**
- Invalid JSON body handling
- Missing required parameters
- Authentication/authorization (if implemented)
- Rate limiting (if implemented)

### Task 3.2: Cron Health Monitoring
**File to Create:** `tools/test_cron_health.sh`
**Effort:** 30 minutes
**Priority:** 🔵 LOW

**Purpose:** Verify all cron jobs actually running
**Checks:**
- Last run timestamp of each automation
- Log file growth (indicates script execution)
- Alert if script hasn't run in expected interval

---

## Implementation Order

### Week 1 (HIGH Priority - Safety Critical)
1. **Day 1-2:** Task 1.1 - Create `tests/test_monitoring.py` (2 hours)
2. **Day 3:** Task 1.2 - Create `tests/test_state_management.py` (1 hour)

### Week 2 (MEDIUM Priority - Core Functionality)
3. **Day 1:** Task 2.1 - Create `tests/test_night_mode.py` (1 hour)
4. **Day 2-3:** Task 2.2 - Create `tests/test_error_handling.py` (2 hours)
5. **Day 4:** Task 2.3 - Update `tests/test_config.py` (45 minutes)

### Week 3 (LOW Priority - Polish)
6. **Day 1:** Task 3.1 - Update `tests/test_flask_endpoints.py` (1 hour)
7. **Day 2:** Task 3.2 - Create `tools/test_cron_health.sh` (30 minutes)

**Total Effort:** ~8.5 hours over 3 weeks

---

## Success Metrics

### Test Coverage Goals
| Metric | Before | Target | How to Measure |
|--------|--------|--------|----------------|
| Overall Pass Rate | 93% | 98%+ | `pytest` output |
| Monitoring Scripts | 0% | 100% | tests/test_monitoring.py |
| night_mode Library | 0% | 100% | tests/test_night_mode.py |
| Error Handling | ~20% | 80%+ | tests/test_error_handling.py |
| Config Tests | 50% | 100% | tests/test_config.py |
| State Management | 0% | 100% | tests/test_state_management.py |

### Validation Steps
After each phase, run full test suite:

```bash
# Run all tests with coverage report
python -m pytest tests/ -v --cov=. --cov-report=term-missing

# Verify specific test files
python -m pytest tests/test_monitoring.py -v
python -m pytest tests/test_night_mode.py -v
python -m pytest tests/test_error_handling.py -v
python -m pytest tests/test_state_management.py -v
python -m pytest tests/test_config.py -v

# Update test results document
# (Update TEST_RESULTS_2025-10-10.md with new coverage)
```

---

## Risk Assessment

### Risks
1. **Mocking Complexity** - Some tests require complex mocking (OAuth flows, concurrent file access)
   - Mitigation: Start with simple tests, add complexity incrementally

2. **False Positives** - Tests pass but don't catch real bugs
   - Mitigation: Include known-failure scenarios in tests

3. **Test Maintenance** - Tests break when code changes
   - Mitigation: Focus on testing behavior, not implementation details

### Blockers
- None identified (all dependencies already installed)

---

## Deliverables

### Test Files to Create
1. `tests/test_monitoring.py` - 11+ tests for monitoring scripts
2. `tests/test_state_management.py` - 5+ tests for state files
3. `tests/test_night_mode.py` - 7+ tests for night mode library
4. `tests/test_error_handling.py` - 10+ tests for error scenarios

### Files to Update
5. `tests/test_config.py` - Fix 3 failing tests, add 3 new tests

### Documentation to Update
6. `TEST_RESULTS_2025-10-10.md` - Add new test coverage stats
7. `SYSTEM_AUDIT_2025-10-10.md` - Update testing status

---

## Next Steps

**Immediate Action:** Begin Phase 1, Task 1.1 - Create `tests/test_monitoring.py`

**Why Start Here:**
- Highest priority (safety-critical systems)
- Zero current coverage
- Clear test cases identified
- No dependencies on other tasks

**Command to Run After Creation:**
```bash
python -m pytest tests/test_monitoring.py -v
```

**Expected Outcome:** 11+ passing tests covering tempstick_monitor and presence_monitor with all failure modes validated.
