# Sensibo AC API Reference

Complete API reference for the Sensibo mini-split AC component.

## Module Imports

```python
# Convenience functions (recommended)
from components.sensibo import (
    get_status,
    turn_on,
    turn_off,
    set_temperature
)

# Full API class
from components.sensibo import SensiboAPI, get_sensibo
```

## Convenience Functions

### get_status(device_id=None)

Get current AC status.

**Parameters:**
- `device_id` (str, optional): Device ID. Uses default from config if not specified.

**Returns:**
```python
{
    'on': True,                  # Power state
    'mode': 'cool',              # cool, heat, fan, dry, auto
    'target_temp_f': 72.0,       # Target temp (Fahrenheit)
    'target_temp_c': 22.2,       # Target temp (Celsius)
    'current_temp_f': 75.0,      # Current room temp (F)
    'current_temp_c': 23.9,      # Current room temp (C)
    'current_humidity': 55,      # Humidity %
    'fan_level': 'auto',         # low, medium, high, auto
    'swing': 'stopped',          # stopped, rangeFull, etc.
    'room': 'Bedroom'            # Room name
}
```

---

### turn_on(mode='cool', temp_f=72, device_id=None)

Turn on AC with specified settings.

**Parameters:**
- `mode` (str): 'cool', 'heat', 'fan', 'dry', 'auto'. Default: 'cool'
- `temp_f` (float): Target temperature in Fahrenheit. Default: 72
- `device_id` (str, optional): Device ID

```python
# Cool mode at 72°F
turn_on()

# Heat mode at 70°F
turn_on(mode='heat', temp_f=70)

# Fan only
turn_on(mode='fan')
```

---

### turn_off(device_id=None)

Turn off AC.

**Parameters:**
- `device_id` (str, optional): Device ID

```python
turn_off()
```

---

### set_temperature(temp_f, device_id=None)

Set target temperature (AC must already be on).

**Parameters:**
- `temp_f` (float): Temperature in Fahrenheit
- `device_id` (str, optional): Device ID

```python
set_temperature(72)
set_temperature(68.5)
```

---

## SensiboAPI Class

### Constructor

```python
sensibo = SensiboAPI(api_key=None, device_id=None)
```

**Parameters:**
- `api_key` (str, optional): API key. Loads from config if not provided.
- `device_id` (str, optional): Default device ID. Loads from config if not provided.

Raises `ValueError` if API key is not configured.

---

### list_devices()

List all Sensibo devices on your account.

**Returns:**
```python
[
    {
        'id': '6WwepeGh',
        'room': {'name': 'Bedroom'}
    },
    # ... more devices
]
```

```python
devices = sensibo.list_devices()
for device in devices:
    print(f"{device['room']['name']}: {device['id']}")
```

---

### get_status(device_id=None)

Get current AC status (same as convenience function).

```python
status = sensibo.get_status()
status = sensibo.get_status(device_id='other_device_id')
```

---

### set_ac_state(device_id=None, **kwargs)

Set AC state with any combination of parameters.

**Parameters:**
- `device_id` (str, optional): Device ID
- `on` (bool): Turn on/off
- `mode` (str): 'cool', 'heat', 'fan', 'dry', 'auto'
- `target_temp_f` (float): Target temperature (Fahrenheit)
- `target_temp_c` (float): Target temperature (Celsius)
- `fan_level` (str): 'low', 'medium', 'high', 'auto'
- `swing` (str): 'stopped', 'rangeFull', etc.

```python
# Single property
sensibo.set_ac_state(target_temp_f=72)

# Multiple properties
sensibo.set_ac_state(
    on=True,
    mode='cool',
    target_temp_f=72,
    fan_level='high'
)
```

---

### turn_on(mode='cool', temp_f=72, device_id=None)

Turn on AC (same as convenience function).

```python
sensibo.turn_on(mode='heat', temp_f=70)
```

---

### turn_off(device_id=None)

Turn off AC (same as convenience function).

```python
sensibo.turn_off()
```

---

### set_temperature(temp_f, device_id=None)

Set temperature (same as convenience function).

```python
sensibo.set_temperature(72)
```

---

## Static Methods

### SensiboAPI._f_to_c(fahrenheit)

Convert Fahrenheit to Celsius.

```python
celsius = SensiboAPI._f_to_c(72)  # 22.2
```

---

### SensiboAPI._c_to_f(celsius)

Convert Celsius to Fahrenheit.

```python
fahrenheit = SensiboAPI._c_to_f(22)  # 71.6
```

---

## Singleton Pattern

The module uses a singleton pattern:

```python
sensibo1 = get_sensibo()
sensibo2 = get_sensibo()
# sensibo1 is sensibo2 == True
```

---

## Error Handling

All methods may raise:
- `ValueError`: Invalid parameters or missing config
- `requests.HTTPError`: Network/API errors
- `Exception`: Sensibo API errors (status != 'success')

**Example:**
```python
try:
    turn_on(mode='cool', temp_f=72)
except ValueError as e:
    print(f"Invalid value: {e}")
except Exception as e:
    print(f"API error: {e}")
```

---

## AC Modes

### cool
Cooling mode (air conditioning).

```python
turn_on(mode='cool', temp_f=72)
```

### heat
Heating mode (heat pump).

```python
turn_on(mode='heat', temp_f=70)
```

### fan
Fan only, no heating/cooling.

```python
turn_on(mode='fan')
```

### dry
Dehumidifier mode.

```python
turn_on(mode='dry')
```

### auto
Automatic heating/cooling based on target temperature.

```python
turn_on(mode='auto', temp_f=72)
```

**Note**: Not all AC units support all modes.

---

## Fan Levels

Available options: `'low'`, `'medium'`, `'high'`, `'auto'`

```python
sensibo.set_ac_state(fan_level='high')
sensibo.set_ac_state(fan_level='auto')
```

**Note**: Actual fan levels depend on your AC unit's capabilities.

---

## Swing Settings

Common options: `'stopped'`, `'rangeFull'`

```python
sensibo.set_ac_state(swing='rangeFull')  # Full swing
sensibo.set_ac_state(swing='stopped')    # Fixed position
```

**Note**: Swing options vary by AC model.

---

## Temperature Ranges

- **Typical range**: 61-90°F (16-32°C)
- **Precision**: 0.5°F or 1°C increments
- **Actual range**: Depends on your AC unit

The API will accept values outside this range, but your AC may not respond.

---

## Configuration Reference

### Required .env Variables
```bash
SENSIBO_API_KEY=your_api_key_here
```

### Required config.yaml Settings
```yaml
sensibo:
  api_key: "${SENSIBO_API_KEY}"
  bedroom_ac_id: "6WwepeGh"  # Your device ID
```

---

## Examples

### Basic Control

```python
from components.sensibo import turn_on, turn_off, get_status

# Turn on
turn_on(mode='cool', temp_f=72)

# Check status
status = get_status()
print(f"Current: {status['current_temp_f']}°F")

# Turn off
turn_off()
```

### Advanced Control

```python
from components.sensibo import SensiboAPI

sensibo = SensiboAPI()

# Configure everything at once
sensibo.set_ac_state(
    on=True,
    mode='cool',
    target_temp_f=72,
    fan_level='auto',
    swing='rangeFull'
)

# Adjust fan without changing temp
sensibo.set_ac_state(fan_level='high')
```

### Multiple Devices

```python
from components.sensibo import SensiboAPI

sensibo = SensiboAPI()

# List all devices
devices = sensibo.list_devices()

# Control specific device
for device in devices:
    sensibo.turn_on(
        mode='cool',
        temp_f=72,
        device_id=device['id']
    )
```

### Smart Cooling

```python
from components.sensibo import get_status, turn_on, turn_off

status = get_status()

# Turn on if too warm
if status['current_temp_f'] > 76:
    if not status['on']:
        turn_on(mode='cool', temp_f=72)
# Turn off if cool enough
elif status['current_temp_f'] < 70:
    if status['on']:
        turn_off()
```

### Integration Example

```python
def bedtime_ac():
    """Bedtime routine - quiet cooling"""
    from components.sensibo import SensiboAPI

    sensibo = SensiboAPI()
    sensibo.set_ac_state(
        on=True,
        mode='cool',
        target_temp_f=68,
        fan_level='low',
        swing='stopped'
    )

def leaving_home():
    """Turn off AC when leaving"""
    from components.sensibo import turn_off
    turn_off()

def arriving_home():
    """Pre-cool before arrival"""
    from components.sensibo import get_status, turn_on

    status = get_status()
    if status['current_temp_f'] > 76:
        turn_on(mode='cool', temp_f=72)
```

---

## Rate Limits

- **Free tier**: Unlimited API calls
- **Best practice**: Don't poll more than once per minute
- **No authentication rate limits**: API key is per-request

---

## See Also

- `GUIDE.md` - User guide with common patterns
- `demo.py` - Interactive demos
- `test.py` - Connection test
- Official API: https://sensibo.github.io
