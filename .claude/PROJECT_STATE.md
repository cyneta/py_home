# py_home Project State & Context
**Last Updated**: 2025-10-14
**Environment**: Transitioning from Git Bash → WSL2
**Critical Status**: Nest API authentication expired (blocks automations)

---

## Executive Summary

**py_home** is a home automation system running on Raspberry Pi 4 that orchestrates:
- Smart thermostat control (Google Nest via Smart Device Management API)
- Smart lighting (TP-Link Tapo bulbs/plugs)
- Climate monitoring (Sensibo air quality, TempStick temperature sensors)
- Presence detection (iOS Scriptable geofencing + WiFi connection)
- Automated arrival/departure routines
- Morning/evening routines

**Current Phase**: Production system with comprehensive test coverage, transitioning to two-stage arrival detection. Nest authentication currently broken (refresh token expired).

**Recent Major Work**:
1. ✅ Two-stage arrival implementation (geofence trigger → pre-arrival actions, WiFi connect → full arrival)
2. ✅ Test suite completion (159 → 207 passing tests, 0 failures)
3. ✅ Tailscale VPN setup for remote access
4. 🔄 Nest OAuth troubleshooting (IN PROGRESS - blocked by redirect_uri issues)

---

## System Architecture

### Component Structure
```
py_home/
├── server/               # Flask REST API
│   ├── app.py           # Flask app initialization
│   └── routes.py        # API endpoints (24 total)
├── automations/         # Automation scripts
│   ├── pre_arrival.py   # Stage 1: Geofence trigger (15min out)
│   ├── im_home.py       # Stage 2: WiFi connect (physical arrival)
│   ├── leaving_home.py  # Departure automation
│   ├── goodnight.py     # Evening routine
│   ├── good_morning.py  # Morning routine
│   └── presence_monitor.py  # DEPRECATED - replaced by iOS geofencing
├── components/          # Device API clients
│   ├── nest/           # Google Nest thermostat
│   ├── tapo/           # TP-Link smart devices
│   └── sensibo/        # Sensibo air quality monitor
├── lib/                # Shared libraries
│   ├── config.py       # Configuration loader (YAML + .env)
│   ├── location.py     # GPS/geofencing logic
│   ├── automation_control.py  # Master automation enable/disable
│   └── notifications.py  # Notification system
├── tests/              # Test suite (207 passing tests)
├── config/             # Configuration files
│   ├── config.yaml     # Main config (uses env var substitution)
│   └── .env            # Secrets (NOT in git)
└── scripts/            # Utility scripts
    ├── nest_reauth.py  # Nest OAuth reauth (localhost redirect)
    └── test_nest_auth.py  # Nest auth diagnostics
```

### Technology Stack
- **Backend**: Python 3.9+, Flask REST API
- **Device APIs**:
  - Google Nest (Smart Device Management API - OAuth2)
  - TP-Link Tapo (local control, cloud fallback)
  - Sensibo (cloud API)
- **Presence Detection**:
  - iOS Scriptable (geofencing - primary)
  - WiFi detection (fallback)
  - Ping monitoring (deprecated)
- **Data Storage**: JSON files for state (presence, location, automation control)
- **Service Management**: systemd (py_home.service)
- **Networking**: Tailscale VPN for remote access
- **Testing**: pytest + dual-mode design (standalone + pytest)

### Data Flow: Arrival Automation (Two-Stage)

**Stage 1: Geofence Trigger** (~15 min from home)
```
iOS Scriptable geofence exit
    ↓
POST /api/pre-arrival
    ↓
pre_arrival.py executes
    ├── Set presence_state = 'home'
    ├── Nest: Heat to 72°F (comfort mode)
    ├── Tapo: Turn on bedroom lamp (if dark)
    └── Send notification
```

**Stage 2: WiFi Connection** (physical arrival)
```
iPhone connects to home WiFi
    ↓
Shortcuts automation triggers
    ↓
POST /api/im-home
    ↓
im_home.py executes
    ├── Check if Stage 1 already ran (presence_state == 'home')
    ├── If not, run Stage 1 actions first
    ├── Turn on main lights
    ├── Disable away mode
    └── Send arrival notification
```

**Fallback**: If geofence fails, WiFi connection runs both stages.

---

## Recent Work (Last Session)

### 1. Test Suite Completion ✅
**Status**: Complete - 207 passing, 0 failing

**Work Done**:
- Created `tests/test_all_endpoints.py` - 25 endpoint tests (22 previously untested)
- Created `tests/test_missing_automations.py` - Tests for 8 automation scripts
- Fixed 6 failing tests (updated home coordinates from old location)
- Verified test isolation - all tests use `dry_run=True` or proper mocking
- Documented dual-mode test system in `dev/workflows/TEST_SYSTEM_NOTES.md`

**Test Coverage Now**:
- ✅ All 24 API endpoints tested
- ✅ All active automation scripts tested
- ✅ Location/geofencing logic tested
- ✅ Monitoring systems tested
- ✅ Error handling tested
- ✅ AI integration tested

**Test Safety Verified**:
- NO tests control real devices
- All device control uses `dry_run=True`
- All API calls are mocked
- Temporary files cleaned up in try/finally blocks
- No side effects on production system

### 2. Two-Stage Arrival Implementation ✅
**Status**: Complete and tested

**Design**:
- **Stage 1** (`pre_arrival.py`): Triggered by iOS geofence exit (~15 min out)
  - Pre-heat home (Nest to 72°F)
  - Turn on minimal lighting if dark
  - Sets `presence_state = 'home'` in `.presence_state` file

- **Stage 2** (`im_home.py`): Triggered by WiFi connection
  - Checks if Stage 1 already ran
  - Runs full arrival lighting
  - Completes arrival sequence

**Why Two Stages**:
- Pre-heating takes 15-20 minutes
- Geofence gives advance warning
- WiFi provides reliable physical arrival confirmation
- Fallback: WiFi-only arrival runs both stages

**Deprecated Components**:
- `arrival_preheat.py` → replaced by `pre_arrival.py`
- `arrival_lights.py` → replaced by `im_home.py`
- Ping-based presence detection → replaced by iOS geofencing

### 3. Nest OAuth Troubleshooting 🔄
**Status**: IN PROGRESS - Blocked

**Problem**: Nest API refresh token expired
- Error: `invalid_grant` - "Token has been expired or revoked"
- Blocks: All Nest automations (heating/cooling control)
- Impact: CRITICAL - arrival/departure automation partially broken

**Attempted Solutions**:
1. ✅ Created `scripts/test_nest_auth.py` - diagnostic tool
2. ✅ Created `scripts/nest_reauth.py` - OAuth flow script
3. ❌ OAuth Playground - `redirect_uri_mismatch` errors
4. ❌ Local reauth script - same redirect errors
5. 🔄 Added redirect URIs to OAuth client - waiting for propagation (5min-few hours)

**Current State**:
- Redirect URIs configured in Google Cloud Console:
  - `https://www.google.com`
  - `http://localhost:8080`
  - `https://developers.google.com/oauthplayground`
- Waiting for Google to propagate changes (can take 5min to few hours)
- Next step: Retry OAuth Playground after propagation

**OAuth Details**:
- OAuth Client: "Sherman Automation" (Web application)
- Client ID: `493001564141-vbibre8pa03t5mv3tsk6hiqg2ga2an49.apps.googleusercontent.com`
- Client Secret: `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`
- Scope needed: `https://www.googleapis.com/auth/sdm.service`
- Account: matthew.g.wheeler@gmail.com (NOT cyneta account)

### 4. Tailscale VPN Setup ✅
**Status**: Complete

**Setup**:
- Installed on Raspberry Pi
- Provides secure remote access
- No port forwarding required
- Access py_home API from anywhere

---

## Known Issues & Pending Tasks

### CRITICAL Issues

#### 1. Nest API Authentication Expired 🔴
**Impact**: Blocks all heating/cooling automation
**Status**: Troubleshooting OAuth redirect_uri issues
**Next Steps**:
1. Wait for Google OAuth redirect URI propagation (5min-few hours)
2. Retry OAuth Playground: https://developers.google.com/oauthplayground/
3. Get new refresh token
4. Update `config/.env` → `NEST_REFRESH_TOKEN`
5. Restart service: `sudo systemctl restart py_home`

**OAuth Playground Steps**:
1. Go to https://developers.google.com/oauthplayground/
2. Click gear icon → "Use your own OAuth credentials"
3. Enter Client ID and Secret (see OAuth Details above)
4. Enter scope: `https://www.googleapis.com/auth/sdm.service`
5. Authorize with matthew.g.wheeler@gmail.com
6. Exchange code for tokens
7. Copy refresh_token

### Dashboard Issues

#### 2. Nest Showing 72°F Instead of Expected Value
**Impact**: Dashboard may show incorrect target temp
**Status**: Not investigated
**Location**: Dashboard display logic

#### 3. Sensibo Humidity Shows "undefined"
**Impact**: Missing humidity data on dashboard
**Status**: Not investigated
**Possible Causes**:
- API response format changed
- Sensor offline
- Data field name mismatch

#### 4. System Shows DEGRADED Status
**Impact**: Unclear system health
**Status**: Not investigated
**Likely Cause**: Nest API failure (secondary effect of issue #1)

#### 5. Presence Monitor Source Label on Dashboard
**Impact**: Adds no value, clutters UI
**Status**: Cleanup needed
**Context**: presence_monitor is deprecated, label should be removed

#### 6. TempStick Data Panel Missing from Dashboard
**Impact**: Can't see basement temperature data
**Status**: Feature not implemented
**Action**: Add TempStick panel to dashboard

---

## Configuration & Critical Details

### Home Location
**Coordinates**: `45.70766068698601, -121.53682676696884`
**Address**: 2480 Sherman Ave, Hood River, OR
**Geofence Radius**: 150 meters
**Near Home Threshold**: 1000 meters (for pre-arrival trigger)

**Important**: Tests were updated from old coordinates (45.7054, -121.5215) which were 1216m off.

### File Locations

**Production System** (Raspberry Pi):
- Project root: `/home/pi/py_home/`
- Config: `/home/pi/py_home/config/`
- Logs: Check with `sudo journalctl -u py_home -f`
- Presence state: `/home/pi/py_home/.presence_state`
- Location data: `/home/pi/py_home/.location_data.json`
- Automation control: `/home/pi/py_home/.automation_control.json`

**Development** (Git Bash / WSL2):
- Repo: `C:\git\cyneta\py_home` (Windows)
- Will map to: `/mnt/c/git/cyneta/py_home` (WSL2)

### Environment Variables (config/.env)

**CRITICAL**: This file is NOT in git. Contains all secrets.

**Nest Credentials**:
```bash
NEST_PROJECT_ID=b8e3fce2-20f4-471f-80e3-d08be2432b75
NEST_CLIENT_ID=493001564141-vbibre8pa03t5mv3tsk6hiqg2ga2an49.apps.googleusercontent.com
NEST_CLIENT_SECRET=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
NEST_REFRESH_TOKEN=<EXPIRED - NEEDS REPLACEMENT>
NEST_DEVICE_ID=enterprises/b8e3fce2-20f4-471f-80e3-d08be2432b75/devices/AVPHwEuC4Fph26_szWKkiHKW4NY3yTTsUZxHDMbDQvUKAgE52AIpVM22O6m0pDaizIZbGIIiSmET4AgzYzRVUYvWvx7dvA
```

**Other Services**:
- Tapo credentials
- Sensibo API key
- TempStick API credentials
- Notification settings

**Config Loading**:
- `config/config.yaml` uses `${ENV_VAR}` syntax
- Loaded by `lib/config.py`
- Example: `client_id: ${NEST_CLIENT_ID}`

### Service Management

**systemd Service**: `py_home.service`

**Commands**:
```bash
# Restart service (apply config changes)
sudo systemctl restart py_home

# View logs (live)
sudo journalctl -u py_home -f

# View status
sudo systemctl status py_home

# Stop service
sudo systemctl stop py_home

# Start service
sudo systemctl start py_home
```

**API Access**:
- Local: `http://localhost:5000`
- Tailscale: `http://<tailscale-ip>:5000`
- Dashboard: `http://localhost:5000/` (root endpoint)

---

## Development Workflow

### Running Tests

**Full Test Suite**:
```bash
cd /c/git/cyneta/py_home  # Git Bash
# OR
cd /mnt/c/git/cyneta/py_home  # WSL2

# Run all tests
pytest

# Run specific test file
pytest tests/test_all_endpoints.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=automations --cov=components --cov=lib
```

**Standalone Test Execution**:
```bash
# Tests also work standalone (dual-mode design)
python tests/test_location.py
python tests/test_geofence_endpoints.py
```

**Test Results (Current)**:
- 207 passed
- 2 skipped (deprecated presence_monitor tests)
- 0 failed
- 67 warnings (PytestReturnNotNoneWarning - harmless, see TEST_SYSTEM_NOTES.md)

### Running Automations Manually

**Test Automation Scripts**:
```bash
cd /c/git/cyneta/py_home

# Test pre-arrival (Stage 1)
python -c "from automations.pre_arrival import run; print(run())"

# Test arrival (Stage 2)
python -c "from automations.im_home import run; print(run())"

# Test good morning
python -c "from automations.good_morning import run; print(run())"

# Test with dry_run
DRY_RUN=true python -c "from automations.good_morning import run; print(run())"
```

**Trigger via API**:
```bash
# Pre-arrival (Stage 1 - geofence trigger)
curl -X POST http://localhost:5000/api/pre-arrival

# Arrival (Stage 2 - WiFi trigger)
curl -X POST http://localhost:5000/api/im-home

# Good morning
curl -X POST http://localhost:5000/api/good-morning

# Goodnight
curl -X POST http://localhost:5000/api/goodnight
```

### iOS Scriptable Integration

**Geofence Script**: `scripts/ios/home-geofence.js`

**Setup**:
1. Install Scriptable app on iPhone
2. Copy `home-geofence.js` to Scriptable
3. Configure automation in iOS Shortcuts:
   - Trigger: Location (entering/exiting home)
   - Action: Run Scriptable → home-geofence
4. Script calls `/api/pre-arrival` or `/api/leaving-home`

**Home Location KML**: `config/home_location.kml` (for reference)

### Debugging

**Check Presence State**:
```bash
# On Raspberry Pi
cat /home/pi/py_home/.presence_state

# Via API
curl http://localhost:5000/api/presence
```

**Check Location Data**:
```bash
cat /home/pi/py_home/.location_data.json
```

**Check Automation Status**:
```bash
curl http://localhost:5000/api/automation-control
```

**Test Nest Connection**:
```bash
python scripts/test_nest_auth.py
```

**View API Logs** (on Pi):
```bash
sudo journalctl -u py_home -f | grep -i nest
sudo journalctl -u py_home -f | grep -i automation
```

---

## Key Files Reference

### Automation Scripts

| File | Purpose | Trigger | Status |
|------|---------|---------|--------|
| `pre_arrival.py` | Stage 1 arrival (pre-heat, minimal lights) | iOS geofence exit | ✅ Active |
| `im_home.py` | Stage 2 arrival (full lights, complete arrival) | WiFi connection | ✅ Active |
| `leaving_home.py` | Departure routine (away mode, lights off) | iOS geofence entry OR manual | ✅ Active |
| `goodnight.py` | Evening routine (lights off, night temp) | Manual trigger | ✅ Active |
| `good_morning.py` | Morning routine (lights on, comfort temp) | Manual trigger | ⚠️ Nest broken |
| `temp_coordination.py` | Coordinate Nest/Sensibo temps | Scheduled | ✅ Active |
| `presence_monitor.py` | Ping-based detection | DEPRECATED | ❌ Replaced |
| `arrival_preheat.py` | Legacy pre-arrival | DEPRECATED | ❌ Deleted |
| `arrival_lights.py` | Legacy arrival lights | DEPRECATED | ❌ Deleted |

### API Endpoints (24 total)

**Automation Triggers**:
- `POST /api/pre-arrival` - Stage 1 arrival (geofence)
- `POST /api/im-home` - Stage 2 arrival (WiFi)
- `POST /api/leaving-home` - Departure
- `POST /api/good-morning` - Morning routine
- `POST /api/goodnight` - Evening routine

**Device Control**:
- `GET /api/nest/status` - Nest thermostat status
- `POST /api/nest/temperature` - Set temperature
- `POST /api/nest/mode` - Set mode (HEAT/COOL/OFF)
- `GET /api/tapo/status` - Tapo device status
- `POST /api/tapo/control` - Control Tapo devices
- `GET /api/sensibo/status` - Sensibo status

**State & Control**:
- `GET /api/presence` - Get presence state
- `POST /api/presence` - Update presence (from iOS)
- `GET /api/location` - Get location data
- `POST /api/location` - Update location (from iOS)
- `GET /api/automation-control` - Check if automations enabled
- `POST /api/automation-control` - Enable/disable automations
- `GET /api/night-mode` - Check night mode status

**System**:
- `GET /` - Dashboard HTML
- `GET /api/status` - System health check
- `GET /api/health` - Health check
- Others (see `server/routes.py`)

### Component APIs

**Nest API** (`components/nest/client.py`):
```python
from components.nest import NestAPI

nest = NestAPI(dry_run=False)

# Get status
status = nest.get_status()
# Returns: {current_temp_f, current_humidity, mode, heat_setpoint_f, cool_setpoint_f, hvac_status}

# Set temperature
nest.set_temperature(72, mode='HEAT')

# Set mode
nest.set_mode('HEAT')  # HEAT, COOL, HEATCOOL, OFF

# Eco mode
nest.set_eco_mode(True)  # Away mode
```

**Tapo API** (`components/tapo/client.py`):
```python
from components.tapo import TapoAPI

tapo = TapoAPI(dry_run=False)

# Turn on device
tapo.turn_on('bedroom_lamp')

# Turn off
tapo.turn_off('bedroom_lamp')

# Set brightness (bulbs only)
tapo.set_brightness('bedroom_lamp', 50)  # 0-100

# Get status
status = tapo.get_status('bedroom_lamp')
```

**Sensibo API** (`components/sensibo/client.py`):
```python
from components.sensibo import SensiboAPI

sensibo = SensiboAPI()
status = sensibo.get_status()
# Returns: {temperature, humidity, air_quality, ...}
```

### Location & Geofencing (`lib/location.py`)

```python
from lib.location import (
    haversine_distance,
    update_location,
    get_location,
    should_trigger_arrival
)

# Calculate distance
distance_m = haversine_distance(
    lat1=45.7076, lon1=-121.5368,
    lat2=45.4465, lon2=-122.6393
)

# Update location (from iOS)
result = update_location(
    lat=45.7076,
    lng=-121.5368,
    trigger='geofence_exit'
)
# Stores in .location_data.json
# Returns: {location, distance_from_home_meters, is_home, timestamp}

# Get current location
location = get_location()
# Returns: {lat, lng, trigger, distance_from_home_meters, is_home, age_seconds}

# Check if should trigger automation
should_trigger, automation_type = should_trigger_arrival('geofence_exit')
# Returns: (True, 'preheat') or (False, None)
```

### Test Files

**Core Tests**:
- `tests/test_all_endpoints.py` - All 24 API endpoints (NEW)
- `tests/test_missing_automations.py` - Automation scripts (NEW)
- `tests/test_location.py` - GPS/geofencing logic
- `tests/test_geofence_endpoints.py` - Geofence API endpoints
- `tests/test_monitoring.py` - Monitoring systems

**Component Tests**:
- `tests/test_nest_integration.py` - Nest API
- `tests/test_tapo_integration.py` - Tapo API
- `tests/test_sensibo_integration.py` - Sensibo API

**Feature Tests**:
- `tests/test_write_operations.py` - Device control (all dry_run)
- `tests/test_error_handling.py` - Error scenarios
- `tests/test_ai_handler.py` - AI integration

---

## Design Decisions & Context

### Why Two-Stage Arrival?

**Problem**: Single-stage arrival (WiFi-only) gives no advance warning
- House cold when arriving in winter
- No time to pre-heat (takes 15-20 min)
- Lights turn on only when already home

**Solution**: Two-stage detection
- **Stage 1** (geofence): 15 min advance warning → pre-heat
- **Stage 2** (WiFi): Physical arrival confirmation → full lights

**Benefits**:
- House warm on arrival
- More reliable (WiFi fallback if geofence fails)
- Better UX (graduated automation)

**Implementation**:
- Presence state file coordinates stages
- Stage 2 checks if Stage 1 already ran
- Fallback: WiFi-only runs both stages

### Why Deprecated Ping Monitoring?

**Old System**: `presence_monitor.py` used ping to detect phone
- Required 3 consecutive failures to trigger
- Unreliable (WiFi sleep, phone asleep)
- No advance warning
- CPU intensive

**New System**: iOS Scriptable geofencing
- Reliable iOS location services
- 15 min advance warning
- Battery efficient
- Direct API calls (no polling)

**Migration**: Complete - ping monitoring disabled

### Why Test System Returns Booleans?

**Dual-Mode Design**: Tests work with both pytest AND standalone execution

**Issue**: pytest warns when tests return values (PytestReturnNotNoneWarning)

**Why We Do It**:
- Tests can run standalone: `python tests/test_location.py`
- Standalone mode shows colored output, detailed results
- Useful for quick debugging without pytest overhead
- Returns True/False for pass/fail

**Trade-off**: 67 pytest warnings (harmless, can be ignored)

**Future Options** (documented in `dev/workflows/TEST_SYSTEM_NOTES.md`):
1. Keep as-is (works fine, just warnings)
2. Separate test runners (duplicate code)
3. Remove standalone mode (lose convenience)
4. Suppress warnings (hide useful info)

**Decision**: Keep current system - warnings are acceptable

### Why Nest Shows 72°F?

**Known Issue**: Dashboard may show 72°F regardless of actual setpoint

**Hypothesis**:
- Could be reading default value
- Could be reading current temp instead of target
- Could be reading heat_setpoint when in COOL mode
- Needs investigation

**Not Yet Debugged**

### Home Location Details

**Physical Address**: 2480 Sherman Ave, Hood River, OR 97031

**GPS Coordinates**:
- Latitude: `45.70766068698601`
- Longitude: `-121.53682676696884`

**Geofence Settings**:
- Home radius: 150 meters
- Near home threshold: 1000 meters (1km)
- Pre-arrival trigger: When exiting ~15min driving distance

**Previous Coordinates** (DEPRECATED):
- Old: `45.7054, -121.5215`
- Distance from new: 1216 meters
- Issue: Caused test failures (fixed in last session)

---

## Deployment & Production Environment

### Raspberry Pi 4 Setup

**Hardware**:
- Raspberry Pi 4 Model B
- Running Raspberry Pi OS (Debian-based)
- Connected to home network

**Software**:
- Python 3.9+
- systemd service management
- Flask web server (port 5000)
- Tailscale VPN for remote access

**Service File**: `/etc/systemd/system/py_home.service`
```ini
[Unit]
Description=py_home Home Automation Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/py_home
ExecStart=/usr/bin/python3 -m server.app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Network Configuration

**Local Network**:
- Raspberry Pi IP: (check with `hostname -I`)
- Flask port: 5000
- Dashboard: `http://<pi-ip>:5000/`

**Tailscale VPN**:
- Provides secure remote access
- No port forwarding needed
- Access from anywhere: `http://<tailscale-ip>:5000/`

**Firewall**:
- Local network: Open
- External: Blocked (use Tailscale)

### Backup & Recovery

**Critical Files to Backup**:
- `config/.env` - All secrets (NOT in git)
- `config/config.yaml` - Main config
- `.presence_state` - Presence state
- `.location_data.json` - Location history
- `.automation_control.json` - Automation settings

**Git Repository**:
- Code tracked in git
- Secrets excluded (.gitignore)
- Regular commits for code changes

---

## WSL2 Migration Notes

### Path Mapping

**Windows → WSL2**:
- `C:\git\cyneta\py_home` → `/mnt/c/git/cyneta/py_home`
- `C:\Users\matt.wheeler` → `/mnt/c/Users/matt.wheeler`

### Environment Setup (WSL2)

**Install Python Dependencies**:
```bash
cd /mnt/c/git/cyneta/py_home
pip install -r requirements.txt
```

**Install pytest**:
```bash
pip install pytest pytest-cov
```

**Run Tests**:
```bash
pytest  # Full suite
pytest -v  # Verbose
```

### Git Configuration

**Settings Shared**:
- Git config (~/.gitconfig) - may need reconfiguration
- SSH keys - may need to copy or regenerate

**Claude Code Settings**:
- `.claude/settings.local.json` - Shared between environments
- Sessions NOT shared - hence this document

### Development Workflow (WSL2)

**Editing Code**:
- Use VS Code with WSL extension
- OR edit in Windows, run in WSL2

**Testing**:
- Run tests in WSL2 (better compatibility)
- `pytest` from `/mnt/c/git/cyneta/py_home`

**Deploying to Pi**:
- Git push from either environment
- SSH to Pi: `ssh pi@<pi-ip>` or `ssh pi@<tailscale-ip>`
- Pull changes: `cd /home/pi/py_home && git pull`
- Restart: `sudo systemctl restart py_home`

---

## Next Steps for New Claude Instance

### Immediate Priority: Fix Nest Authentication 🔴

**Wait Period**: Google OAuth redirect URI changes can take 5min - few hours to propagate

**After Propagation**:
1. Test OAuth Playground: https://developers.google.com/oauthplayground/
2. Steps:
   - Click gear → "Use your own OAuth credentials"
   - Client ID: `493001564141-vbibre8pa03t5mv3tsk6hiqg2ga2an49.apps.googleusercontent.com`
   - Client Secret: `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`
   - Scope: `https://www.googleapis.com/auth/sdm.service`
   - Authorize with matthew.g.wheeler@gmail.com
   - Exchange code for tokens
   - Copy refresh_token

3. Update `.env`:
   ```bash
   # Edit config/.env
   NEST_REFRESH_TOKEN=<new-token-from-oauth-playground>
   ```

4. Test locally:
   ```bash
   python scripts/test_nest_auth.py
   ```

5. Deploy to Pi:
   ```bash
   # Copy new .env to Pi
   scp config/.env pi@<pi-ip>:/home/pi/py_home/config/

   # Restart service
   ssh pi@<pi-ip>
   sudo systemctl restart py_home
   ```

6. Verify:
   ```bash
   # Test good morning automation
   curl -X POST http://<pi-ip>:5000/api/good-morning

   # Check logs
   sudo journalctl -u py_home -f
   ```

**If Still Fails**:
- Check error message in OAuth Playground
- Verify redirect URIs in Google Cloud Console
- Verify using correct Google account (matthew.g.wheeler@gmail.com)
- May need to wait longer for propagation

### Secondary Priorities

**Dashboard Issues**:
1. Investigate why Nest shows 72°F
   - Check `server/routes.py` - dashboard endpoint
   - Check Nest API response parsing
   - Verify mode logic (HEAT vs COOL setpoint)

2. Fix Sensibo humidity undefined
   - Check `components/sensibo/client.py`
   - Verify API response format
   - Check for field name changes

3. Investigate DEGRADED status
   - Check health check logic
   - Likely secondary to Nest failure
   - May auto-resolve after Nest fix

4. Remove presence_monitor label
   - Check dashboard template/frontend
   - Remove reference to deprecated component

5. Add TempStick panel
   - Check if TempStick API integration exists
   - Add panel to dashboard
   - Display basement temperature

### Testing Verification

**After Any Changes**:
```bash
# Run full test suite
cd /mnt/c/git/cyneta/py_home  # WSL2
pytest

# Verify 207 passing, 0 failing
# 67 warnings OK (PytestReturnNotNoneWarning)
```

**Test Isolation Reminder**:
- NEVER run tests that control real devices
- All device control must use `dry_run=True`
- All API calls must be mocked
- File operations must use temporary files with cleanup

---

## Reference: Important Commands

### Git Bash Paths (Current)
```bash
cd /c/git/cyneta/py_home
```

### WSL2 Paths (New)
```bash
cd /mnt/c/git/cyneta/py_home
```

### Testing
```bash
pytest                    # Full suite
pytest -v                # Verbose
pytest tests/test_*.py   # Specific file
python tests/test_*.py   # Standalone mode
```

### Service Management (on Pi)
```bash
sudo systemctl restart py_home
sudo systemctl status py_home
sudo journalctl -u py_home -f
```

### API Testing
```bash
# Health check
curl http://localhost:5000/api/health

# Presence
curl http://localhost:5000/api/presence

# Nest status
curl http://localhost:5000/api/nest/status

# Trigger automation
curl -X POST http://localhost:5000/api/good-morning
```

### Debugging
```bash
# Check presence state
cat /home/pi/py_home/.presence_state

# Check location
cat /home/pi/py_home/.location_data.json

# Test Nest auth
python scripts/test_nest_auth.py

# View logs (Pi)
sudo journalctl -u py_home -f | grep -i nest
```

---

## Contact & Resources

**Google Cloud Console**: https://console.cloud.google.com/
**OAuth Playground**: https://developers.google.com/oauthplayground/
**Nest Device Access**: https://console.nest.google.com/device-access/

**Accounts**:
- Google Cloud / Nest: matthew.g.wheeler@gmail.com
- Work account (DON'T USE): matt@cyneta.com

**Documentation**:
- This file: `.claude/PROJECT_STATE.md` (session context)
- Session index: `.claude/SESSION_INDEX.md` (handoff docs index)
- Nest OAuth troubleshooting: `dev/debug/nest_oauth_troubleshooting_2025-10-14.md`
- Test system notes: `dev/workflows/TEST_SYSTEM_NOTES.md`
- Architecture: `docs/ARCHITECTURE.md`
- iOS automation: `docs/IOS_AUTOMATION.md`

---

## Glossary

**Terms**:
- **py_home**: This project - home automation system
- **Stage 1**: Geofence-triggered pre-arrival (15 min out)
- **Stage 2**: WiFi-triggered full arrival (physical arrival)
- **Dry run**: Safe mode - no real device control
- **Presence state**: home/away status stored in `.presence_state`
- **Geofence**: GPS boundary around home (150m radius)
- **Near home**: Within 1km of home (triggers pre-arrival)
- **Sherman Automation**: OAuth client name for Nest API
- **Tailscale**: VPN for secure remote access

**Deprecated**:
- **Ping monitoring**: Old presence detection (replaced by iOS geofencing)
- **arrival_preheat.py**: Old pre-arrival script (replaced by pre_arrival.py)
- **arrival_lights.py**: Old arrival script (replaced by im_home.py)

---

**END OF CONTEXT DOCUMENT**

*Last updated: 2025-10-14*
*For: WSL2 migration*
*Status: Nest auth blocked, tests complete, two-stage arrival live*
