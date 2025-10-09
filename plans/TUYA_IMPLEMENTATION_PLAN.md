# Tuya Integration Implementation Plan

## Overview
Implement Tuya cloud API integration for controlling Alen 75i air purifiers (2 devices: bedroom and living room).

## Current State

**Config (config.yaml):**
```yaml
alen:
  api_key: "${TUYA_API_KEY}"
  api_secret: "${TUYA_API_SECRET}"
  devices:
    bedroom:
      device_id: "${TUYA_DEVICE_ID_BEDROOM}"
      name: "Bedroom 75i"
    living_room:
      device_id: "${TUYA_DEVICE_ID_LIVING}"
      name: "Living Room 75i"
  thresholds:
    pm25_good: 25
    pm25_moderate: 50
    pm25_unhealthy: 100
```

**Environment (.env.example):**
```
TUYA_API_KEY=
TUYA_API_SECRET=
TUYA_DEVICE_ID_BEDROOM=
TUYA_DEVICE_ID_LIVING=
```

## Architecture Design

### Component Structure
```
components/tuya/
├── __init__.py           # Public API exports
├── client.py             # TuyaAPI class (singleton pattern)
├── air_purifier.py       # AlenAirPurifier device class
├── demo.py               # Quick test/demo script (optional)
└── README.md             # Setup and usage guide
```

### Technology Stack
- **Library:** tinytuya (PyPI package)
- **API Type:** Tuya Cloud API (not local LAN)
- **Protocol:** HTTPS REST API
- **Auth:** API key + secret

### Core Classes

#### 1. TuyaAPI (client.py)
Main API client following tapo/sensibo pattern.

**Responsibilities:**
- Initialize with config (API key, secret, device IDs)
- Manage Tuya cloud connection
- Provide high-level device methods
- Structured logging with kvlog()
- Dry-run support
- Singleton pattern

**Public Methods:**
```python
class TuyaAPI:
    def __init__(self, dry_run=False)
    def get_device(self, device_name) -> AlenAirPurifier
    def get_all_devices() -> List[AlenAirPurifier]
    def get_air_quality(device_name) -> dict  # PM2.5, AQI
    def set_power(device_name, on: bool)
    def set_fan_speed(device_name, speed: int)  # 1-5
    def get_status(device_name) -> dict
```

**Singleton:**
```python
_tuya = None
def get_tuya() -> TuyaAPI:
    global _tuya
    if _tuya is None:
        _tuya = TuyaAPI()
    return _tuya
```

#### 2. AlenAirPurifier (air_purifier.py)
Device-specific class for air purifier controls.

**Responsibilities:**
- Wrap tinytuya device object
- Provide air purifier-specific methods
- Parse device status/data points
- Handle Tuya data point (DP) mappings

**Public Methods:**
```python
class AlenAirPurifier:
    def __init__(self, device_id, name, tuya_client)
    def turn_on()
    def turn_off()
    def set_fan_speed(speed: int)  # 1-5
    def get_air_quality() -> dict  # {'pm25': int, 'aqi': int, 'quality': str}
    def get_status() -> dict
    def is_on() -> bool
```

### Tuya Data Points (DPs)
Need to discover actual DPs for Alen 75i. Common air purifier DPs:
- DP 1: Power (on/off)
- DP 2: Mode (auto/manual/sleep)
- DP 4: Fan speed (1-5)
- DP 22: PM2.5 reading
- DP 23: AQI

**Note:** Actual DPs must be discovered using TinyTuya wizard or API inspection.

## Implementation Steps

### Phase 1: Foundation (client.py)
1. Create `components/tuya/` directory
2. Install tinytuya: `pip install tinytuya`
3. Create `client.py` with TuyaAPI class:
   - Read config from `config['alen']`
   - Initialize tinytuya Cloud client
   - Implement singleton pattern
   - Add dry_run support
4. Create `__init__.py` with exports

### Phase 2: Device Class (air_purifier.py)
1. Create `air_purifier.py` with AlenAirPurifier class
2. Implement device control methods
3. Map Tuya DPs to friendly names
4. Add structured logging

### Phase 3: Testing
1. Create `tests/test_tuya.py`:
   - Test config loading
   - Test dry_run mode
   - Test air quality parsing
   - Mock tinytuya responses
2. Create `components/tuya/demo.py` for manual testing:
   - List devices
   - Get air quality
   - Control power/fan

### Phase 4: Integration
1. Update automations to use Tuya:
   - Add air purifier control to leaving_home
   - Add AQI-based automation logic
2. Add to status monitoring
3. Consider iOS Shortcuts endpoints

### Phase 5: Documentation
1. Create `components/tuya/README.md`:
   - Setup instructions (getting Tuya API credentials)
   - Device discovery with tinytuya wizard
   - Usage examples
2. Update main `README.md` with Tuya status
3. Document in `docs/COMPONENTS.md` (if exists)

## TinyTuya Setup Guide

### Getting Tuya Cloud Credentials
1. Create account at https://iot.tuya.com/
2. Create Cloud Project
3. Link devices using Tuya Smart app
4. Get API credentials:
   - Access ID (API Key)
   - Access Secret
   - Device IDs
5. Subscribe to "IoT Core" service (free tier available)

### Device Discovery
```bash
python -m tinytuya wizard
```
This will scan network and cloud to find device IDs and local keys.

## Logging Strategy

Follow existing kvlog() patterns:

**Success:**
```python
kvlog(logger, logging.INFO, api='tuya', device='bedroom', action='set_power',
      state='on', result='ok', duration_ms=234)
```

**Error:**
```python
kvlog(logger, logging.ERROR, api='tuya', device='bedroom', action='get_air_quality',
      error_type='TuyaCloudException', error_msg='API rate limit exceeded', duration_ms=145)
```

**Air Quality:**
```python
kvlog(logger, logging.INFO, api='tuya', device='living_room', action='get_air_quality',
      pm25=15, aqi=55, quality='good', result='ok', duration_ms=156)
```

## API Usage Examples

**Get Air Quality:**
```python
from components.tuya import get_air_quality

aq = get_air_quality('bedroom')
# {'pm25': 15, 'aqi': 55, 'quality': 'good'}
```

**Control Power:**
```python
from components.tuya import set_power, set_fan_speed

set_power('bedroom', on=True)
set_fan_speed('bedroom', 3)  # Medium speed
```

**Get All Status:**
```python
from components.tuya import get_all_devices

for device in get_all_devices():
    status = device.get_status()
    print(f"{device.name}: PM2.5={status['pm25']}, On={status['on']}")
```

## Dependencies

**New Python Package:**
```bash
pip install tinytuya
```

**requirements.txt addition:**
```
tinytuya>=1.15.0  # Tuya cloud API for Alen air purifiers
```

## Risk Assessment

**Low Risk:**
- TinyTuya is mature, well-maintained library
- Read-only operations (air quality) are safe
- Config structure already defined

**Medium Risk:**
- Need actual Tuya API credentials to test
- Device DPs may differ from standard air purifiers
- Cloud API has rate limits (unknown at this time)

**Mitigation:**
- Implement dry_run mode for all operations
- Add error handling for API failures
- Use tinytuya wizard to discover actual DPs before implementation
- Test with mock responses first

## Timeline

**Phase 1-2:** 1-2 hours (core implementation)
**Phase 3:** 30-60 min (testing)
**Phase 4:** 30-60 min (integration)
**Phase 5:** 30 min (documentation)

**Total:** 3-4 hours

## Success Criteria

- [ ] Can read PM2.5 air quality from both devices
- [ ] Can control power on/off
- [ ] Can set fan speed (1-5)
- [ ] Structured logging with kvlog()
- [ ] Tests passing (unit + integration)
- [ ] Documentation complete
- [ ] Integrated with automation system

## Notes

- **Config naming:** Using `alen` section name (not `tuya`) since these are Alen-branded devices
- **Cloud vs Local:** Using cloud API (simpler, no local key discovery needed)
- **Future:** Could add local LAN support later for faster response times
