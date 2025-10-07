# Nest Thermostat API Reference

Complete API reference for the Nest thermostat component.

## Module Imports

```python
# Convenience functions (recommended)
from components.nest import (
    get_status,
    set_temperature,
    set_mode,
    set_away,
    set_comfort
)

# Full API class
from components.nest import NestAPI, get_nest
```

## Convenience Functions

### get_status()

Get current thermostat status.

```python
status = get_status()
```

**Returns:**
```python
{
    'current_temp_f': 68.5,        # Current temperature (F)
    'current_humidity': 45,         # Humidity percentage
    'mode': 'HEAT',                # HEAT, COOL, HEATCOOL, OFF
    'heat_setpoint_f': 72.0,       # Target temp (heat mode)
    'cool_setpoint_f': None,       # Target temp (cool mode)
    'hvac_status': 'HEATING'       # HEATING, COOLING, OFF
}
```

---

### set_temperature(temp_f, mode=None)

Set target temperature.

**Parameters:**
- `temp_f` (float): Temperature in Fahrenheit
- `mode` (str, optional): 'HEAT', 'COOL', or 'HEATCOOL'. Uses current mode if not specified.

```python
# Use current mode
set_temperature(72)

# Specify mode
set_temperature(72, mode='HEAT')
set_temperature(74, mode='COOL')
```

---

### set_mode(mode)

Set thermostat mode.

**Parameters:**
- `mode` (str): 'HEAT', 'COOL', 'HEATCOOL', or 'OFF'

```python
set_mode('HEAT')
set_mode('COOL')
set_mode('OFF')
```

---

### set_away(temp_f=62)

Set to away mode with specific temperature.

**Parameters:**
- `temp_f` (float, optional): Away temperature. Default: 62°F

```python
set_away()      # Use default (62°F)
set_away(60)    # Custom temp
```

---

### set_comfort(temp_f=72)

Set to comfort temperature.

**Parameters:**
- `temp_f` (float, optional): Comfort temperature. Default: 72°F

```python
set_comfort()   # Use default (72°F)
set_comfort(70) # Custom temp
```

---

## NestAPI Class

### Constructor

```python
nest = NestAPI()
```

Loads configuration from `config/config.yaml` and `config/.env`. Raises `ValueError` if credentials are incomplete.

---

### get_status()

Get current thermostat status (same as convenience function).

```python
status = nest.get_status()
```

---

### set_temperature(temp_f, mode=None)

Set target temperature (same as convenience function).

```python
nest.set_temperature(72, mode='HEAT')
```

---

### set_mode(mode)

Set thermostat mode (same as convenience function).

```python
nest.set_mode('HEAT')
```

---

### set_eco_mode(enabled=True)

Enable or disable Eco mode (away mode).

**Parameters:**
- `enabled` (bool): True to enable, False to disable

```python
nest.set_eco_mode(True)   # Enable eco/away mode
nest.set_eco_mode(False)  # Return to normal
```

---

### set_fan(duration_seconds=900)

Turn on fan for specified duration.

**Parameters:**
- `duration_seconds` (int): Duration in seconds. Default: 900 (15 minutes)

```python
nest.set_fan(duration_seconds=900)   # 15 minutes
nest.set_fan(duration_seconds=1800)  # 30 minutes
```

---

## Static Methods

### NestAPI._f_to_c(fahrenheit)

Convert Fahrenheit to Celsius.

```python
celsius = NestAPI._f_to_c(72)  # 22.2
```

---

### NestAPI._c_to_f(celsius)

Convert Celsius to Fahrenheit.

```python
fahrenheit = NestAPI._c_to_f(22.2)  # 72.0
```

---

## Singleton Pattern

The module uses a singleton pattern for efficiency:

```python
# These all use the same NestAPI instance
nest1 = get_nest()
nest2 = get_nest()
# nest1 is nest2 == True
```

---

## Authentication

Authentication is handled automatically:

1. **Token Refresh**: Access tokens are automatically refreshed when expired
2. **Credentials**: Loaded from `config/.env`
3. **Expiry Management**: Tokens refreshed 5 minutes before expiration

You don't need to manage authentication manually.

---

## Error Handling

All methods may raise:
- `ValueError`: Invalid parameters or missing config
- `requests.HTTPError`: API errors (network, auth, etc.)

**Example:**
```python
try:
    set_temperature(72)
except ValueError as e:
    print(f"Invalid value: {e}")
except Exception as e:
    print(f"API error: {e}")
```

---

## Rate Limits

- **Recommended**: Don't poll status more than once per minute
- **Token refresh**: Automatic, not counted against limits
- **Commands**: No documented hard limit, but be reasonable

---

## Temperature Ranges

- **Minimum**: 50°F (10°C)
- **Maximum**: 90°F (32°C)
- **Precision**: 0.5°F increments

The API will round to nearest 0.5°F.

---

## Mode Behavior

### HEAT Mode
- Controls heating only
- Sets `heat_setpoint_f`
- HVAC activates when temp drops below setpoint

### COOL Mode
- Controls cooling only
- Sets `cool_setpoint_f`
- HVAC activates when temp rises above setpoint

### HEATCOOL Mode
- Auto mode (heat or cool as needed)
- Sets both `heat_setpoint_f` and `cool_setpoint_f`
- Maintains temperature in range

### OFF Mode
- HVAC disabled
- Thermostat still monitors temperature
- Cannot set temperature while OFF

---

## Configuration Reference

### Required .env Variables
```bash
NEST_PROJECT_ID=projects/your-project-id
NEST_CLIENT_ID=your-client-id.apps.googleusercontent.com
NEST_CLIENT_SECRET=your-client-secret
NEST_REFRESH_TOKEN=your-refresh-token
```

### Required config.yaml Settings
```yaml
nest:
  project_id: "${NEST_PROJECT_ID}"
  client_id: "${NEST_CLIENT_ID}"
  client_secret: "${NEST_CLIENT_SECRET}"
  refresh_token: "${NEST_REFRESH_TOKEN}"
  device_id: "enterprises/.../devices/..."
```

---

## Examples

### Complete Workflow

```python
from components.nest import NestAPI

# Initialize
nest = NestAPI()

# Check status
status = nest.get_status()
print(f"Current: {status['current_temp_f']}°F")

# Set to heat mode at 72°F
nest.set_mode('HEAT')
nest.set_temperature(72)

# Enable away mode
nest.set_eco_mode(True)

# Return to comfort
nest.set_eco_mode(False)
nest.set_temperature(72)
```

### Integration Example

```python
def leaving_home():
    """Run when leaving home"""
    from components.nest import set_away
    set_away(62)  # Save energy

def arriving_home():
    """Run when arriving home"""
    from components.nest import set_comfort, get_status

    status = get_status()
    if status['current_temp_f'] < 68:
        set_comfort(72)  # Pre-heat if cold
```

---

## See Also

- `SETUP.md` - Initial setup and OAuth flow
- `GUIDE.md` - User guide with common patterns
- `demo.py` - Interactive demos
- `test.py` - Connection test
