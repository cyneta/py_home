# Nest Thermostat User Guide

Complete guide to controlling your Nest thermostat via the Google Smart Device Management API.

## Overview

This component provides Python control of your Nest thermostat. All temperatures are in Fahrenheit for convenience (automatically converted to Celsius for the API).

## Basic Operations

### Get Current Status

```python
from components.nest import get_status

status = get_status()
print(f"Temperature: {status['current_temp_f']}°F")
print(f"Humidity: {status['current_humidity']}%")
print(f"Mode: {status['mode']}")
print(f"HVAC: {status['hvac_status']}")
```

**Status Fields:**
- `current_temp_f`: Current temperature in Fahrenheit
- `current_humidity`: Humidity percentage
- `mode`: HEAT, COOL, HEATCOOL, or OFF
- `heat_setpoint_f`: Target temp in heat mode
- `cool_setpoint_f`: Target temp in cool mode
- `hvac_status`: HEATING, COOLING, or OFF

### Set Temperature

```python
from components.nest import set_temperature

# Set to 72°F in HEAT mode
set_temperature(72, mode='HEAT')

# Set to 74°F in COOL mode
set_temperature(74, mode='COOL')

# Use current mode (auto-detects)
set_temperature(70)
```

### Change Mode

```python
from components.nest import set_mode

set_mode('HEAT')     # Heating mode
set_mode('COOL')     # Cooling mode
set_mode('HEATCOOL') # Auto mode
set_mode('OFF')      # Turn off
```

### Temperature Presets

```python
from components.nest import set_away, set_comfort

# Set away temperature (default 62°F)
set_away(62)

# Set comfort temperature (default 72°F)
set_comfort(72)
```

## Advanced Usage

### Using the NestAPI Class

```python
from components.nest import NestAPI

nest = NestAPI()

# Manual mode control
nest.set_mode('HEAT')
nest.set_temperature(70)

# Eco mode (away mode)
nest.set_eco_mode(True)   # Enable
nest.set_eco_mode(False)  # Disable

# Fan control
nest.set_fan(duration_seconds=900)  # Run fan for 15 min
```

### Error Handling

```python
from components.nest import set_temperature

try:
    set_temperature(72)
except Exception as e:
    print(f"Failed to set temperature: {e}")
```

## Configuration

### config/.env
```bash
NEST_PROJECT_ID=projects/your-project-id
NEST_CLIENT_ID=your-client-id.apps.googleusercontent.com
NEST_CLIENT_SECRET=your-client-secret
NEST_REFRESH_TOKEN=your-refresh-token
```

### config/config.yaml
```yaml
nest:
  project_id: "${NEST_PROJECT_ID}"
  client_id: "${NEST_CLIENT_ID}"
  client_secret: "${NEST_CLIENT_SECRET}"
  refresh_token: "${NEST_REFRESH_TOKEN}"
  device_id: "enterprises/.../devices/..."

  # Temperature presets (Fahrenheit)
  away_temp: 62
  sleep_temp: 68
  comfort_temp: 72
```

## Authentication

The API uses OAuth2 with automatic token refresh:

1. Initial setup requires browser-based OAuth flow
2. Refresh token is stored in `.env`
3. Access tokens are automatically refreshed
4. Tokens typically expire after 1 hour

See `SETUP.md` for initial authentication setup.

## Temperature Conversion

The API works in Fahrenheit for convenience:

```python
# You use Fahrenheit
set_temperature(72)

# API receives Celsius (22.2°C)
# Conversion is automatic
```

Manual conversion (if needed):
```python
from components.nest.client import NestAPI

celsius = NestAPI._f_to_c(72)   # 22.2
fahrenheit = NestAPI._c_to_f(22.2)  # 72.0
```

## Common Patterns

### Morning Routine
```python
from components.nest import set_comfort

set_comfort(72)  # Warm up the house
```

### Leaving Home
```python
from components.nest import set_away

set_away(62)  # Save energy while away
```

### Bedtime
```python
from components.nest import set_temperature

set_temperature(68)  # Cooler for sleeping
```

### Check Before Arrival
```python
from components.nest import get_status

status = get_status()
if status['current_temp_f'] < 65:
    set_temperature(72)  # Pre-heat
```

## Troubleshooting

### "Invalid OAuth token"
Access tokens expire every hour. The client automatically refreshes them using your refresh token. If you see this error, check that your `NEST_REFRESH_TOKEN` is correct in `.env`.

### "Device not found"
Check that `device_id` in `config.yaml` matches your actual device. Run `list_devices.py` to see available devices.

### "Permission denied"
Ensure:
- Device Access registration is complete
- SDM API is enabled in Google Cloud
- OAuth scopes include `sdm.service`

## API Limits

- **Rate limits**: Google may throttle excessive requests
- **Best practice**: Don't poll status more than once per minute
- **Token refresh**: Happens automatically, no action needed

## Resources

- `SETUP.md` - Initial setup guide
- `API.md` - Complete API reference
- `demo.py` - Interactive demos
- `test.py` - Connection test
