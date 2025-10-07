# Sensibo AC User Guide

Complete guide to controlling your mini-split AC via Sensibo Sky/Air devices.

## Overview

This component provides Python control of your mini-split AC through Sensibo devices. All temperatures can be specified in Fahrenheit or Celsius (automatically handled).

## Setup

### Get API Key
1. Go to https://home.sensibo.com/me/api
2. Copy your API key
3. Add to `config/.env`: `SENSIBO_API_KEY=your_key_here`

### Find Device ID
```bash
python list_devices.py
```

Copy the device ID to `config/config.yaml`:
```yaml
sensibo:
  api_key: "${SENSIBO_API_KEY}"
  bedroom_ac_id: "6WwepeGh"
```

## Basic Operations

### Get Current Status

```python
from components.sensibo import get_status

status = get_status()
print(f"Power: {'ON' if status['on'] else 'OFF'}")
print(f"Mode: {status['mode']}")
print(f"Target: {status['target_temp_f']}°F")
print(f"Current: {status['current_temp_f']}°F")
print(f"Humidity: {status['current_humidity']}%")
```

**Status Fields:**
- `on`: Power state (True/False)
- `mode`: cool, heat, fan, dry, auto
- `target_temp_f`: Target temperature (Fahrenheit)
- `target_temp_c`: Target temperature (Celsius)
- `current_temp_f`: Current room temperature
- `current_humidity`: Humidity percentage
- `fan_level`: low, medium, high, auto
- `swing`: stopped, rangeFull, etc.
- `room`: Room name

### Turn On/Off

```python
from components.sensibo import turn_on, turn_off

# Turn on in COOL mode at 72°F
turn_on(mode='cool', temp_f=72)

# Turn on in HEAT mode
turn_on(mode='heat', temp_f=70)

# Turn off
turn_off()
```

### Set Temperature

```python
from components.sensibo import set_temperature

# Set to 72°F (AC must be on)
set_temperature(72)

# Temperature is sent to Sensibo and interpreted
# based on your device's temperatureUnit setting
```

### Change Mode

```python
from components.sensibo import SensiboAPI

sensibo = SensiboAPI()

# Cool mode
sensibo.set_ac_state(mode='cool', target_temp_f=72)

# Heat mode
sensibo.set_ac_state(mode='heat', target_temp_f=68)

# Fan only
sensibo.set_ac_state(mode='fan')

# Dry/Dehumidify
sensibo.set_ac_state(mode='dry')

# Auto mode
sensibo.set_ac_state(mode='auto', target_temp_f=72)
```

## Advanced Usage

### Control Fan Level

```python
from components.sensibo import SensiboAPI

sensibo = SensiboAPI()

# Set fan level
sensibo.set_ac_state(fan_level='high')
sensibo.set_ac_state(fan_level='medium')
sensibo.set_ac_state(fan_level='low')
sensibo.set_ac_state(fan_level='auto')
```

### Control Swing

```python
sensibo.set_ac_state(swing='rangeFull')   # Full swing
sensibo.set_ac_state(swing='stopped')     # Stop swing
```

### Multiple Devices

```python
# List all devices
sensibo = SensiboAPI()
devices = sensibo.list_devices()

for device in devices:
    print(f"{device['room']['name']}: {device['id']}")

# Control specific device
turn_on(mode='cool', temp_f=72, device_id='device_id_here')
```

### Combined Settings

```python
sensibo = SensiboAPI()

# Set multiple properties at once
sensibo.set_ac_state(
    on=True,
    mode='cool',
    target_temp_f=72,
    fan_level='auto',
    swing='rangeFull'
)
```

## Temperature Handling

### Important: temperatureUnit Field

Sensibo devices have a `temperatureUnit` setting (F or C). The API returns temperatures in the device's configured unit.

```python
status = get_status()

# These are automatically converted for you
print(status['target_temp_f'])  # Always Fahrenheit
print(status['target_temp_c'])  # Always Celsius
```

When setting temperature:
```python
# Use Fahrenheit (recommended)
set_temperature(72)

# Or specify Celsius
sensibo.set_ac_state(target_temp_c=22)
```

### Manual Conversion

```python
from components.sensibo.client import SensiboAPI

celsius = SensiboAPI._f_to_c(72)   # 22.2
fahrenheit = SensiboAPI._c_to_f(22)  # 71.6
```

## Common Patterns

### Cool Down on Hot Day
```python
from components.sensibo import turn_on

turn_on(mode='cool', temp_f=70)
```

### Warm Up on Cold Day
```python
turn_on(mode='heat', temp_f=72)
```

### Bedtime Routine
```python
from components.sensibo import SensiboAPI

sensibo = SensiboAPI()

# Quiet, gentle cooling
sensibo.set_ac_state(
    on=True,
    mode='cool',
    target_temp_f=68,
    fan_level='low',
    swing='stopped'
)
```

### Energy Saving
```python
from components.sensibo import turn_off, get_status

status = get_status()

# Turn off if room is cool enough
if status['current_temp_f'] < 74:
    turn_off()
```

### Pre-Cool Before Arrival
```python
from components.sensibo import turn_on, get_status

status = get_status()

# Only cool if room is warm
if status['current_temp_f'] > 76:
    turn_on(mode='cool', temp_f=72)
```

## Configuration

### config/.env
```bash
SENSIBO_API_KEY=your_api_key_here
```

### config/config.yaml
```yaml
sensibo:
  api_key: "${SENSIBO_API_KEY}"
  bedroom_ac_id: "6WwepeGh"  # Your device ID
```

## Troubleshooting

### "Sensibo API error"
Check that your API key is correct in `.env`.

### "No device_id specified"
Add `bedroom_ac_id` (or custom name) to `config.yaml`.

### Temperature not changing
- Ensure AC is turned on first
- Check that mode supports temperature setting (not FAN mode)
- Verify device is responding in Sensibo app

### Device not found
Run `list_devices.py` to see all devices and verify your device ID.

## API Limits

- **Rate limits**: Sensibo has generous rate limits
- **Best practice**: Don't poll status more than once per minute
- **Free tier**: Unlimited API calls

## Modes Explained

- **cool**: Air conditioning (cooling)
- **heat**: Heating mode (heat pump)
- **fan**: Fan only, no heating/cooling
- **dry**: Dehumidifier mode
- **auto**: Automatic heating/cooling based on target temp

Not all AC units support all modes. Check your AC's capabilities.

## Resources

- `API.md` - Complete API reference
- `demo.py` - Interactive demos
- `test.py` - Connection test
- Official API: https://sensibo.github.io
