# Tapo P125M Smart Plugs

Self-contained demo and documentation for Tapo smart outlet control.

## Quick Start

```bash
# Run the demo
python demo.py

# Test connection
python test.py
```

## Your Plugs

1. **Heater** - 192.168.50.135
2. **Bedroom Right Lamp** - 192.168.50.143
3. **Livingroom Lamp** - 192.168.50.162
4. **Bedroom Bedroom Left Lamp** - 192.168.50.93

## Files

- `demo.py` - Interactive demo of all capabilities
- `test.py` - Quick connection test
- `GUIDE.md` - Complete user guide
- `API.md` - API reference

## Basic Usage

```python
from utils.tapo_api import turn_on, turn_off, get_status

turn_on("Heater")
turn_off("Livingroom Lamp")
status = get_status("Bedroom Right Lamp")
```

## Features Demonstrated

✓ Turn on/off by name
✓ Turn on/off by IP
✓ Get status (on/off, signal, firmware)
✓ Control all plugs at once
✓ Rename plugs programmatically
✓ Discover plugs on network

## Requirements

- python-kasa >= 0.10.2
- Credentials in `../../config/.env`
- Plugs configured in `../../config/config.yaml`
