# py_home Testing Plan

**Created:** 2025-10-07
**Status:** In Progress
**Goal:** Achieve 100% test coverage for all devices, services, and automations

---

## Current Test Coverage

### ✅ Covered (test_all.py)
- **Devices:** Tapo (4 plugs), Nest thermostat, Sensibo AC
- **Services:** OpenWeather API (live test)
- **Infrastructure:** Config loading, module imports
- **Pattern:** Clean import validation

### ❌ Missing Coverage
- **Services:** Google Maps, GitHub, Checkvist (only import tests)
- **Libraries:** Notifications (only import test, no send test)
- **Components:** Network presence detection (no test)
- **Automations:** All 9 automation scripts (no tests)
- **Server:** Flask endpoints (separate test_server.py, not integrated)

---

## Phase 1: Service API Tests (15 min)

### 1.1 Google Maps Service Test
**File:** `services/test_google_maps.py`

**Tests:**
- Live API call with real travel time calculation
- Test origin → destination routing
- Validate traffic data parsing
- Test error handling (invalid location)

**Example:**
```python
def test_google_maps():
    from services import get_travel_time

    result = get_travel_time("Chicago, IL", "Milwaukee, WI")
    assert 'duration_minutes' in result
    assert 'distance_miles' in result
    assert result['duration_minutes'] > 0
```

### 1.2 GitHub Service Test
**File:** `services/test_github.py`

**Tests:**
- API authentication (read-only)
- Repo access verification
- Test get_repo_info() without mutations
- Mock test for add_task_to_todo() (no actual commits)

**Note:** Read-only to avoid creating test commits

### 1.3 Checkvist Service Test
**File:** `services/test_checkvist.py`

**Tests:**
- API authentication
- Test get_lists() read operation
- Mock test for add_task() (no actual task creation)

**Note:** Read-only to avoid test task spam

### 1.4 Notifications Test
**File:** `lib/test_notifications.py`

**Tests:**
- Module loading and config parsing
- Mock notification send (no actual Pushover/ntfy calls)
- Test message formatting
- Test error handling

**Note:** Mock-only to avoid notification spam

---

## Phase 2: Network Presence Test (10 min)

### 2.1 Network Component Test
**File:** `components/network/test.py`

**Tests:**
- Test ping detection (localhost or known device)
- Test ARP scan parsing
- Test auto-detection logic
- Test MAC/IP identifier parsing
- Test error handling (unreachable device)

**Example:**
```python
def test_presence():
    from components.network import is_device_home

    # Test localhost (always reachable)
    assert is_device_home('127.0.0.1', method='ping') == True

    # Test unreachable IP
    assert is_device_home('192.168.255.254', method='ping') == False
```

---

## Phase 3: Automation Test Suite (20 min)

### 3.1 Automation Dry-Run Tests
**File:** `tests/test_automations.py`

**Strategy:** Add `--dry-run` flag to each automation script
- Loads config
- Validates logic
- Prints what *would* happen
- No actual device changes

**Tests for all 9 automations:**
1. leaving_home.py
2. goodnight.py
3. im_home.py
4. good_morning.py
5. travel_time.py
6. task_router.py
7. temp_coordination.py
8. presence_monitor.py
9. traffic_alert.py

**Example:**
```python
def test_automation(script_name):
    """Test automation in dry-run mode"""
    result = subprocess.run(
        [sys.executable, f'automations/{script_name}', '--dry-run'],
        capture_output=True,
        text=True,
        timeout=10
    )

    assert result.returncode == 0, f"{script_name} failed"
    assert 'error' not in result.stderr.lower()
    return result.stdout
```

**Modifications Required:**
- Add `--dry-run` argument parsing to each automation
- Add conditional execution (skip device calls in dry-run)
- Add verbose logging of what would happen

---

## Phase 4: Integrate Server Tests (10 min)

### 4.1 Merge test_server.py into test_all.py

**Changes:**
- Add Flask server health check
- Test endpoints if server is running
- Skip gracefully with SKIP status if server not running
- Don't require server to be running for main test suite

**Tests:**
- GET / (health check)
- GET /status (system status)
- GET /travel-time (synchronous endpoint)
- POST endpoints (mock, don't actually run automations)

---

## Phase 5: Enhanced test_all.py (15 min)

### 5.1 Add Test Modes

```bash
# Quick test (no live API calls)
python test_all.py --dry-run

# Skip expensive API calls
python test_all.py --skip-api

# Full integration test
python test_all.py --full

# Test only specific component
python test_all.py --only tapo
```

### 5.2 Better Reporting

**Add:**
- PASS/SKIP/FAIL status with color coding
- Execution time per test
- Summary statistics:
  - Total: X tests
  - Passed: X (green)
  - Failed: X (red)
  - Skipped: X (yellow)
  - Duration: X.Xs
- Test categories (devices, services, automations, server)

### 5.3 Exit Codes

- 0: All tests passed (or skipped)
- 1: Any test failed
- 2: Configuration error

---

## Phase 6: pytest Suite (Optional, 20 min)

### 6.1 Professional Test Structure

```
tests/
├── __init__.py
├── conftest.py           # pytest fixtures
├── test_devices.py       # Tapo, Nest, Sensibo
├── test_services.py      # OpenWeather, Maps, GitHub, Checkvist
├── test_automations.py   # All automation scripts
├── test_server.py        # Flask endpoints
└── test_integration.py   # End-to-end flows
```

### 6.2 pytest Configuration

**File:** `pytest.ini`
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts =
    -v
    --tb=short
    --color=yes
    --cov=components
    --cov=services
    --cov=automations
    --cov-report=term-missing
```

### 6.3 Fixtures

```python
@pytest.fixture
def mock_config():
    """Mock config for testing"""
    return {...}

@pytest.fixture
def mock_device():
    """Mock device for testing"""
    return MockTapo()
```

### 6.4 Benefits
- Parallel test execution (`pytest -n auto`)
- Code coverage reporting
- Better failure reporting
- Industry standard
- GitHub Actions compatible
- VS Code test explorer integration

---

## Config Utility Development

### Goal
Create configuration/setup utilities for components that need device discovery or credential setup.

### Pattern (based on Tapo)
```bash
python -m components.tapo.config
```

### Components to Add Config Utilities

#### ✅ Tapo (Already Done)
- Discovers devices on network
- Tests connection
- Generates config YAML

#### 🔧 Nest (High Priority)
- Interactive OAuth flow
- Token refresh testing
- Generates credentials JSON

#### 🔧 Sensibo (Medium Priority)
- API key validation
- Device discovery
- Room name mapping

#### 🔧 Network (Medium Priority)
- Network device scanner
- IP/MAC discovery
- Presence detection testing

#### ⏸️ Roborock (Deferred)
- Device discovery
- Cloud API setup

#### ⏸️ Alen (Deferred)
- Tuya credential setup
- Device pairing

---

## Success Metrics

### Test Coverage Goals
- ✅ 100% device component coverage
- ✅ 100% service API coverage
- ✅ 100% automation script coverage
- ✅ Flask server endpoint coverage
- ✅ Network presence detection coverage

### Quality Metrics
- All tests pass on clean install
- Tests complete in < 30 seconds (without live API calls)
- Tests complete in < 2 minutes (with full integration)
- Zero false negatives
- Clear failure messages

### Developer Experience
- Single command: `python test_all.py`
- Clear PASS/FAIL/SKIP reporting
- Helpful error messages
- Fast feedback loop

---

## Timeline

| Phase | Task | Time | Priority |
|-------|------|------|----------|
| 1 | Service API tests | 15 min | High |
| 2 | Network presence test | 10 min | High |
| 3 | Automation test suite | 20 min | High |
| 4 | Integrate server tests | 10 min | Medium |
| 5 | Enhanced test_all.py | 15 min | Medium |
| 6 | pytest suite | 20 min | Low (optional) |
| - | Config utilities | 30 min | Medium |

**Total Core Work:** 70 minutes
**With Optional:** 120 minutes

---

## Next Steps

1. ✅ Create this plan document
2. ⏳ Create todo list
3. ⏳ Execute Phase 1: Service tests
4. ⏳ Execute Phase 2: Network test
5. ⏳ Execute Phase 3: Automation tests
6. ⏳ Execute Phase 4: Server integration
7. ⏳ Execute Phase 5: Enhanced reporting
8. ⏳ Build config utilities (Nest, Sensibo, Network)
9. ⏳ Optional: Convert to pytest

---

**Last Updated:** 2025-10-07
