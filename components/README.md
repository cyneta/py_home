# Component Demo Packages

Each component has a self-contained demo/doc package for testing and reference.

## Structure

```
components/
├── tapo/           # TP-Link Tapo P125M smart plugs
│   ├── __init__.py  # Public API
│   ├── client.py    # TapoAPI class
│   ├── README.md    # Quick start
│   ├── demo.py      # Interactive demos
│   ├── test.py      # Connection test
│   ├── GUIDE.md     # User guide
│   └── API.md       # API reference
│
├── nest/           # Google Nest thermostat
│   ├── __init__.py
│   ├── client.py
│   ├── README.md
│   ├── GUIDE.md
│   └── API.md
│
├── sensibo/        # Sensibo mini-split AC
│   ├── __init__.py
│   ├── client.py
│   ├── README.md
│   ├── GUIDE.md
│   └── API.md
│
├── tuya/           # Alen air purifiers (Tuya Cloud API)
│   ├── __init__.py
│   ├── client.py
│   ├── air_purifier.py
│   ├── README.md
│   └── demo.py
│
└── network/        # WiFi presence detection
    ├── __init__.py
    ├── presence.py
    └── README.md
```

## Quick Test All Components

```bash
# Run full test suite (recommended)
python -m pytest tests/ -v

# Test individual components
python components/tapo/test.py
python components/tuya/demo.py

# Quick smoke test
python test_all.py
```

## Purpose

Each component package:
- ✓ Demonstrates all capabilities
- ✓ Provides quick connection test
- ✓ Serves as reference documentation
- ✓ Can verify functionality anytime
- ✓ Self-contained (includes all docs)

## Available Components

### Device Components (Complete)
- **tapo**: ✅ Complete (TP-Link Tapo P125M smart plugs - 4 devices)
- **nest**: ✅ Complete (Google Nest thermostat)
- **sensibo**: ✅ Complete (Sensibo mini-split AC)
- **tuya**: ✅ Complete (Alen air purifiers via Tuya Cloud - 2 devices)
- **network**: ✅ Complete (WiFi presence detection)

### Service Components (in services/)
- **google_maps**: ✅ Complete (Travel time/traffic)
- **openweather**: ✅ Complete (Weather data & forecasts)
- **notifications**: ✅ Complete (Pushover/ntfy push notifications)
- **github**: ✅ Complete (Voice task commits)
- **checkvist**: ✅ Complete (Task management)
