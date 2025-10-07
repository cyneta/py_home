# Sensibo Mini-Split AC

Self-contained demo and documentation for Sensibo AC control.

## Quick Start

```bash
# Run the demo
python demo.py

# Test connection
python test.py
```

## Your Device

**Sensibo Sky** - Bedroom AC
- Device ID: 6WwepeGh
- Controlled via Sensibo REST API
- Supports modes: cool, heat, fan, dry, auto

## Files

- `demo.py` - Interactive demo of all capabilities
- `test.py` - Quick connection test
- `GUIDE.md` - Complete user guide
- `API.md` - API reference
- `list_devices.py` - Device discovery

## Basic Usage

```python
from components.sensibo import get_status, turn_on, turn_off, set_temperature

# Get current status
status = get_status()
print(f"Current: {status['current_temp_f']}°F, Target: {status['target_temp_f']}°F")

# Turn on AC
turn_on(mode='cool', temp_f=72)

# Adjust temperature
set_temperature(70)

# Turn off
turn_off()
```

## Features Demonstrated

✓ Get current temperature and status
✓ Turn on/off AC
✓ Set temperature (F/C conversion)
✓ Change mode (cool, heat, fan, dry, auto)
✓ Control fan level (low, medium, high, auto)
✓ Control swing mode
✓ List all devices on account

## Requirements

- Sensibo API key from https://home.sensibo.com/me/api
- API key in `../../config/.env`
- Device ID in `../../config/config.yaml`
