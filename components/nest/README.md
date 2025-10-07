# Google Nest Thermostat

Self-contained demo and documentation for Nest thermostat control.

## Quick Start

```bash
# Run the demo
python demo.py

# Test connection
python test.py
```

## Your Device

**Nest Thermostat** (3rd Generation)
- Controlled via Google Smart Device Management API
- OAuth2 authentication with auto-refresh

## Files

- `demo.py` - Interactive demo of all capabilities
- `test.py` - Quick connection test
- `GUIDE.md` - Complete user guide
- `API.md` - API reference
- `SETUP.md` - Initial setup instructions
- `get_token.py` - OAuth token helper
- `list_devices.py` - Device discovery

## Basic Usage

```python
from components.nest import get_status, set_temperature, set_mode

# Get current status
status = get_status()
print(f"Current: {status['current_temp_f']}°F")

# Set temperature
set_temperature(72)  # Heat mode

# Change mode
set_mode('COOL')
```

## Features Demonstrated

✓ Get current temperature and status
✓ Set temperature (HEAT/COOL/HEATCOOL modes)
✓ Change thermostat mode
✓ Away/comfort temperature presets
✓ Automatic OAuth token refresh
✓ Fahrenheit/Celsius conversion

## Requirements

- Google Cloud project with SDM API enabled
- Device Access registration ($5 one-time)
- OAuth2 credentials in `../../config/.env`
- Device ID in `../../config/config.yaml`

See `SETUP.md` for complete setup instructions.
