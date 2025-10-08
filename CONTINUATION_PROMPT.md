# Claude Code Continuation Prompt

**Date**: 2025-10-07
**From**: siri_n8n session
**To**: py_home (new independent project)

---

## Context Transfer

I'm continuing development of the Python home automation system. The project was just restructured and promoted to a top-level project. All context, decisions, and working code should be preserved.

---

## Project Overview

**Location**: `C:\git\cyneta\py_home\`
**Type**: Python-based home automation system
**Architecture**: Component-based, self-contained device packages
**Status**: Foundation complete, ready for orchestration layer

### What It Does
Controls smart home devices (Nest thermostat, Sensibo AC, 4 Tapo smart plugs) through clean Python APIs. Alternative to n8n visual workflows - code-first approach.

---

## Current Working State

### ✅ Fully Operational Components

**Tapo Smart Plugs (4 devices)**
- Location: `components/tapo/`
- Status: ✅ FULLY TESTED - All 4 plugs working
- Devices:
  - Heater (192.168.50.135)
  - Bedroom Right Lamp (192.168.50.143)
  - Livingroom Lamp (192.168.50.162)
  - Bedroom Left Lamp (192.168.50.93)
- Features: Turn on/off by name or IP, get status, discover, rename
- Protocol: python-kasa with KLAP (local HTTP port 80)
- Tools: `name_plugs.py` (interactive naming with ESC pause), `find_devices.py`
- Demo: `components/tapo/demo.py` (5 interactive demos)
- Test: `components/tapo/test.py` (verified working)

**Nest Thermostat**
- Location: `components/nest/`
- Status: ✅ API client working (tested at 73°F)
- Features: Set temp, get status, mode control, F/C conversion, OAuth2 auto-refresh
- Protocol: Google Smart Device Management API
- Tools: `get_token.py`, `list_devices.py`
- Needs: demo.py, test.py, README.md

**Sensibo AC**
- Location: `components/sensibo/`
- Status: ✅ API client working (tested at 72°F)
- Features: Set temp/mode, on/off, status, F/C conversion
- Critical fix implemented: Handle `temperatureUnit` field (API returns F or C)
- Protocol: REST API
- Tools: `list_devices.py`
- Needs: demo.py, test.py, README.md

### Supporting Infrastructure

**Configuration System** (`lib/config.py`)
- Loads `config/config.yaml` + `config/.env`
- Environment variable substitution: `${VAR_NAME}`
- All credentials in `.env` (gitignored)
- All device configs in `config.yaml`

**Shared Utilities** (`lib/`)
- `config.py` - Config loader
- `notifications.py` - Pushover/ntfy.sh (not yet tested)

**External Services** (`services/`)
- `google_maps.py` - Travel time/traffic (API working, not tested)

---

## Architecture - Component-Based Design

### Key Principle: Self-Contained Components

Each component contains **EVERYTHING** about that device:
```
components/[device]/
├── __init__.py          # Clean API exports
├── client.py            # API implementation
├── demo.py              # Interactive demos
├── test.py              # Smoke test
├── [tools].py           # Component-specific tools
└── README.md            # Complete documentation
```

### Import Pattern
```python
# Clean, intuitive imports
from components.tapo import turn_on, turn_off, get_status
from components.nest import set_temperature
from lib import config, send

# Use anywhere
turn_on("Heater")
set_temperature(72)
```

### Directory Structure
```
py_home/
├── components/          # Self-contained device packages
│   ├── tapo/           ✅ COMPLETE
│   ├── nest/           ✅ Client done, needs demo/test
│   └── sensibo/        ✅ Client done, needs demo/test
├── lib/                # Shared utilities
├── services/           # External APIs
├── automations/        # Orchestration (NEXT STEP)
├── config/             # Config + credentials
├── docs/               # Documentation
├── scripts/            # OLD (being phased out)
└── utils/              # OLD (being phased out)
```

**IMPORTANT**: `utils/` and `scripts/` contain old files from before restructuring. They have been copied to the new structure but not yet deleted.

---

## Recent Major Changes

### Just Completed (Last Hour)

1. **Restructured entire project** from mixed/legacy to clean component architecture
   - Moved API clients: `utils/*.py` → `components/*/client.py`
   - Moved shared utils: `utils/config.py` → `lib/config.py`
   - Moved tools: `scripts/*.py` → `components/*/[tool].py`
   - Created `__init__.py` files for clean exports
   - Updated all imports

2. **Promoted to top level**
   - Was: `C:\git\cyneta\siri_n8n\py_home\`
   - Now: `C:\git\cyneta\py_home\`
   - Independent project, can reference siri_n8n as needed

3. **Verified working after changes**
   - Tapo component tested: All 4 plugs working
   - Clean imports verified: `from components.tapo import turn_on` works

### Documentation Created
- `NEW_STRUCTURE.md` - Complete restructuring guide
- `STATUS_REPORT.md` - Comprehensive status report
- `README.md` - Updated for new structure
- `components/tapo/README.md`, `GUIDE.md`, `API.md` - Complete Tapo docs

---

## Critical Lessons Learned

### Tapo Smart Plugs
1. **Library choice**: Switched from `tapo` (Rust) to `python-kasa` (better P125M support)
2. **Protocol**: P125M uses KLAP on port 80, not old Kasa protocol on 9999
3. **Connection**: Must use `DeviceConfig` with `DeviceConnectionParameters`:
   ```python
   config = DeviceConfig(
       host=ip,
       credentials=Credentials(username, password),
       connection_type=DeviceConnectionParameters(
           device_family=DeviceFamily.SmartTapoPlug,
           encryption_type=DeviceEncryptionType.Klap
       )
   )
   ```
4. **Session cleanup**: Must call `await device.protocol.close()` to avoid warnings
5. **Discovery**: `kasa discover` works but direct IP connection more reliable
6. **Naming**: Device names stored locally, can set with `device.set_alias()`
7. **Network**: 192.168.50.x subnet, "dapad" SSID

### Nest Thermostat
1. **OAuth refresh**: Token auto-refreshes when expired
2. **Temperature**: API uses Celsius, auto-convert from Fahrenheit
3. **Device ID**: Long enterprise/device ID format in config

### Sensibo
1. **Critical bug fixed**: API has `temperatureUnit` field - returns F or C, not always C
2. **Don't convert**: When setting temp, send as integer in device's unit
3. **Check unit first**: Always check `temperatureUnit` before converting

### Architecture
1. **Component isolation**: Each component self-contained = easier testing
2. **Clean imports**: Users import from components, not internal modules
3. **Shared utilities**: Only truly shared code goes in `lib/`
4. **Tools with components**: Component-specific tools stay with component

---

## Configuration Details

### config/config.yaml
Non-sensitive settings, committed to git:
```yaml
nest:
  device_id: "enterprises/b8e3fce2-.../devices/AVPHwEuC4F..."
  away_temp: 62
  sleep_temp: 68
  comfort_temp: 72

tapo:
  outlets:
    - name: "Heater"
      ip: "192.168.50.135"
    # ... 3 more plugs

sensibo:
  bedroom_ac_id: "6WwepeGh"

locations:
  home:
    lat: 41.8781
    lng: -87.6298
    radius_meters: 150
```

### config/.env
Sensitive credentials, gitignored (has real values):
```bash
NEST_PROJECT_ID=b8e3fce2-20f4-471f-80e3-d08be2432b75
NEST_CLIENT_ID=493001564141-vbibre8pa03t5mv3tsk6hiqg2ga2an49.apps.googleusercontent.com
NEST_CLIENT_SECRET=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
NEST_REFRESH_TOKEN=1//06AqzTFi7P6xo...

SENSIBO_API_KEY=LqTrEXkgAJZEm4wfsWpdkIL5lXwx3s

TAPO_USERNAME=matt@wheelers.us
TAPO_PASSWORD=h4fsqSbNjfdm

GOOGLE_MAPS_API_KEY=AIzaSyAzq9ujOidMnzV8Ax05dZRJXQLx5Ejf63U
OPENWEATHER_API_KEY=880611ff7c3bcd31d513e8982b88e062
```

---

## What Works Right Now

### Verified Commands
```python
# Tapo - ALL TESTED
from components.tapo import turn_on, turn_off, get_status, turn_on_all
turn_on("Heater")
turn_off("Livingroom Lamp")
turn_on_all()
status = get_status("Bedroom Right Lamp")

# Nest - TESTED
from components.nest import set_temperature, get_status
set_temperature(73)  # Worked!

# Sensibo - TESTED
from components.sensibo import set_temperature
set_temperature(72)  # Worked!
```

### Test Commands
```bash
# Verify Tapo working
python -m components.tapo.test
# Expected: ✓ All plugs working!

# Run Tapo demos
cd components/tapo && python demo.py

# Test clean imports
python -c "from components.tapo import turn_on; print('✓')"
```

---

## Next Steps (In Priority Order)

### Immediate (Complete Component Packages)
1. **Create Nest component package**
   - `components/nest/demo.py` - Similar to Tapo demo
   - `components/nest/test.py` - Quick connection test
   - `components/nest/README.md` - Complete docs
   - Pattern: Copy from Tapo, adapt for Nest

2. **Create Sensibo component package**
   - `components/sensibo/demo.py`
   - `components/sensibo/test.py`
   - `components/sensibo/README.md`
   - Pattern: Copy from Tapo, adapt for Sensibo

3. **Clean up legacy files**
   - Remove old `utils/` folder (after verifying everything works)
   - Remove old `scripts/` folder
   - Remove duplicate docs from `docs/`

### Phase 1 (Orchestration)
4. **Build first automation script**
   - `automations/leaving_home.py`
   - Combines: Nest (away mode) + Tapo (turn off all)
   - Example of using multiple components together

5. **Build morning routine**
   - `automations/morning_routine.py`
   - Turn on lamps, set comfortable temp

6. **Build climate coordination**
   - `automations/climate_sync.py`
   - Coordinate Nest + Sensibo based on conditions

### Phase 2 (Integration)
7. **Flask webhook server**
8. **iOS Shortcuts integration**
9. **Deploy to Raspberry Pi**

---

## Important Patterns to Follow

### Creating New Components
1. Copy `components/tapo/` as template
2. Rename files and update imports
3. Create `__init__.py` with clean exports
4. Write `client.py` with API implementation
5. Create `demo.py` with interactive demos
6. Create `test.py` for smoke testing
7. Write `README.md` with complete docs

### Creating Automation Scripts
```python
# automations/example.py
from components.tapo import turn_on_all, turn_off_all
from components.nest import set_temperature
from components.sensibo import set_mode
from lib import send

def leaving_home():
    """Run when leaving home"""
    set_temperature(62)  # Nest away
    turn_off_all()       # All Tapo plugs
    send("Left home - devices secured")
```

### Testing New Code
1. Test imports: `python -c "from components.X import Y"`
2. Test component: `python -m components.X.test`
3. Test functionality: Try actual operations
4. Verify in Tapo app/physical devices

---

## User Preferences & Context

### User: Matt Wheeler
- Email: matt@wheelers.us
- Development style: Prefers action over planning
- Wants to test things: "test it", "lets try it"
- Direct communication
- Has existing devices already configured
- Located in Chicago area (lat: 41.8781, lng: -87.6298)

### Development Environment
- **OS**: Windows (MINGW64_NT)
- **Python**: 3.11
- **Git Bash**: Uses Unix-style commands
- **Working Directory**: Now `C:\git\cyneta\py_home\`
- **Network**: 192.168.50.x subnet, "dapad" SSID

### CLAUDE.md Instructions (Critical)
User has custom instructions in `.claude/CLAUDE.md`:
- **PATH FORMATS**: BASH uses `/c/path`, FILE TOOLS use `C:\path`
- **NEVER commit without approval**
- **NO extended characters in commit messages**
- **NO Claude Code attribution in commits**
- **"todo: X"** → Use TodoWrite tool, STOP, wait for permission

### Related Project
- **siri_n8n**: `C:\git\cyneta\siri_n8n\`
- Original n8n workflow project
- Contains Google API setup files
- Can reference but py_home is now independent

---

## Tech Stack Details

### Dependencies (requirements.txt)
```
flask>=3.0.0
requests>=2.31.0
python-dotenv>=1.0.0
pyyaml>=6.0.1
googlemaps>=4.10.0
tinytuya>=1.13.0
python-kasa>=0.10.2
schedule>=1.2.0
pytest>=7.4.0
pytest-mock>=3.12.0
```

### Key Libraries
- **python-kasa**: Tapo local control (v0.10.2)
- **requests**: REST API calls
- **pyyaml**: Config loading
- **python-dotenv**: Environment variables

---

## Known Issues & Gotchas

### None Currently
All systems working as expected after restructuring.

### Previous Issues (Resolved)
1. ✅ Tapo `tapo` library → Fixed by switching to `python-kasa`
2. ✅ Sensibo temp conversion → Fixed by checking `temperatureUnit`
3. ✅ Config import errors → Fixed during restructuring
4. ✅ Session cleanup warnings → Fixed with `protocol.close()`

---

## Files to Reference

### Essential Reading
- `NEW_STRUCTURE.md` - Architecture & migration details
- `STATUS_REPORT.md` - Comprehensive current status
- `README.md` - Project overview
- `components/tapo/README.md` - Example complete component

### Code Examples
- `components/tapo/client.py` - Well-structured API client
- `components/tapo/demo.py` - Good demo pattern
- `components/tapo/test.py` - Good test pattern
- `components/tapo/name_plugs.py` - Interactive tool with ESC pause

### Configuration
- `config/config.yaml` - All device settings
- `config/.env` - All credentials (gitignored, has real values)
- `lib/config.py` - How config loading works

---

## Git Status

```
Current branch: main
Location: C:\git\cyneta\py_home\.git

Modified:
  .claude/settings.local.json

New files (untracked):
  components/
  lib/
  services/
  automations/
  NEW_STRUCTURE.md
  CONTINUATION_PROMPT.md

Old files (to be cleaned up):
  utils/ (has old API clients)
  scripts/ (has old tools)
```

**Not yet committed**: All restructuring changes are uncommitted.

---

## Success Criteria

You'll know you're on track if:
1. ✅ Can import: `from components.tapo import turn_on`
2. ✅ Test passes: `python -m components.tapo.test`
3. ✅ All 4 Tapo plugs respond
4. ✅ Nest and Sensibo APIs work
5. ✅ Config loads from `config/config.yaml` and `.env`

---

## First Actions to Take

When starting in new Claude Code instance:

1. **Verify location**: `pwd` should show `/c/git/cyneta/py_home`
2. **Test working state**: `python -m components.tapo.test`
3. **Review status**: Read `NEW_STRUCTURE.md` and `STATUS_REPORT.md`
4. **Choose next task**: Probably creating Nest component package
5. **Follow component pattern**: Use Tapo as template

---

## Summary

**You're picking up a working project** that just completed major restructuring. Foundation is solid, all devices tested and working. Next phase is completing component packages and building orchestration layer.

**Key principle**: Component-based architecture where each device is self-contained. Clean imports. Everything working.

**Your mission**: Continue building out component packages (Nest, Sensibo) following the established Tapo pattern, then move to automation scripts.

**Remember**: User wants to see things work. Test frequently, keep things operational.

---

## Quick Reference Commands

```bash
# Verify working
python -m components.tapo.test

# Test imports
python -c "from components.tapo import turn_on; print('✓')"

# Run demo
cd components/tapo && python demo.py

# Control a plug
python -c "from components.tapo import turn_on; turn_on('Heater')"

# Check config
python -c "from lib import config; print(config['tapo']['outlets'][0])"
```

---

**Ready to continue! All context preserved. Pick up where we left off.**
