# Tuya Component - Alen Air Purifiers

Control Alen BreatheSmart 75i air purifiers via Tuya Cloud API.

## Overview

Alen air purifiers are built on the Tuya IoT platform. This component allows you to:
- Monitor air quality (PM2.5, AQI)
- Control power on/off
- Set fan speed (1-5)
- Set operating mode (auto/manual/sleep)
- Get device status and filter life

## Setup

### 1. Install Dependencies

```bash
pip install tinytuya
```

### 2. Pair Devices with Tuya Smart Life App

**⚠️ Warning:** This will disconnect devices from Alen Air app.

1. Download "Smart Life" app (iOS/Android)
2. Create Tuya account
3. Reset air purifier WiFi:
   - Hold "Auto" button for 5-10 seconds
   - WiFi indicator should blink rapidly
4. Add device in Smart Life app:
   - Tap "Add Device"
   - Select "Air Purifier"
   - Follow pairing instructions
5. Repeat for all devices

### 3. Get Tuya Cloud API Credentials

1. Go to https://iot.tuya.com/
2. Create account (same email as Smart Life app)
3. Create Cloud Project:
   - **Cloud** → **Development**
   - Click "Create Cloud Project"
   - Industry: Smart Home
   - Development Method: Smart Home
   - Data Center: Choose your region (US, EU, CN, IN)
4. Link devices:
   - **Cloud** → **Link Tuya App Account**
   - Add your Smart Life account
5. Subscribe to APIs (free tier):
   - **Cloud** → **API Products**
   - Subscribe to "IoT Core" (required)
6. Get credentials:
   - **Cloud** → **Your Project** → **Overview**
   - Copy:
     - **Access ID/Client ID** → `TUYA_API_KEY`
     - **Access Secret/Client Secret** → `TUYA_API_SECRET`
7. Get device IDs:
   - **Cloud** → **Devices**
   - Find your air purifiers
   - Copy Device IDs

### 4. Configure py_home

Add to `config/.env`:

```bash
# Tuya (Alen air purifiers)
TUYA_API_KEY=your_access_id_here
TUYA_API_SECRET=your_access_secret_here
TUYA_DEVICE_ID_BEDROOM=bf1234567890abcdef
TUYA_DEVICE_ID_LIVING=bf0987654321fedcba
```

Config already exists in `config/config.yaml`:

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

## Usage

### Quick Start

```python
from components.tuya import get_air_quality, set_power, set_fan_speed

# Get air quality
aq = get_air_quality('bedroom')
print(f"PM2.5: {aq['pm25']}, AQI: {aq['aqi']}, Quality: {aq['quality']}")

# Control devices
set_power('bedroom', on=True)
set_fan_speed('bedroom', 3)  # 1=low, 5=turbo
```

### Full API

```python
from components.tuya import get_tuya

tuya = get_tuya()

# Get device instance
bedroom = tuya.get_device('bedroom')

# Control
bedroom.turn_on()
bedroom.turn_off()
bedroom.set_fan_speed(3)  # 1-5
bedroom.set_mode('auto')   # auto/manual/sleep

# Monitor
aq = bedroom.get_air_quality()
# {'pm25': 15, 'aqi': 55, 'quality': 'good'}

status = bedroom.get_status()
# {
#   'on': True,
#   'pm25': 15,
#   'aqi': 55,
#   'quality': 'good',
#   'fan_speed': 3,
#   'mode': 'auto',
#   'filter_life': 85,
#   'online': True
# }

# Check power state
if bedroom.is_on():
    print("Running")

# All devices
for device in tuya.get_all_devices():
    print(f"{device.name}: PM2.5={device.get_air_quality()['pm25']}")

# Status of all devices
for status in tuya.list_all_status():
    print(f"{status['name']}: PM2.5={status['pm25']}, AQI={status['aqi']}")
```

## Air Quality Index (AQI)

PM2.5 is automatically converted to US EPA AQI:

| AQI Range | Quality | Description |
|-----------|---------|-------------|
| 0-50 | good | Air quality is satisfactory |
| 51-100 | moderate | Acceptable for most people |
| 101-150 | unhealthy_sensitive | Sensitive groups may experience effects |
| 151-200 | unhealthy | Everyone may experience effects |
| 201-300 | very_unhealthy | Health alert |
| 301-500 | hazardous | Emergency conditions |

## Demo Script

Test the integration:

```bash
python components/tuya/demo.py
```

Interactive commands:
- `list` - List all devices
- `status bedroom` - Get device status
- `air bedroom` - Get air quality
- `on bedroom` - Turn on
- `off bedroom` - Turn off
- `speed bedroom 3` - Set fan speed
- `quit` - Exit

## Testing

Run tests:

```bash
# Unit tests (no credentials needed)
python tests/test_tuya.py

# All tests
python -m pytest tests/ -v
```

## Troubleshooting

### No devices found
- Verify devices are linked to your Tuya Cloud project
- Check Device IDs are correct in `.env`
- Ensure devices are online in Smart Life app

### API authentication errors
- Verify API credentials are correct
- Check Data Center region matches your account
- Ensure IoT Core subscription is active

### Device not responding
- Check device is online in Smart Life app
- Verify WiFi connection
- Check Tuya Cloud API rate limits

### Missing data points (DPs)
Different Alen models may use different DP codes. To discover:

```python
tuya = get_tuya()
status = tuya.get_device_status('bedroom_device_id')
print(status['result']['status'])
# Shows all available DPs with codes and values
```

Common DP codes:
- `switch` - Power on/off
- `pm25` - PM2.5 reading
- `fan_speed_enum` - Fan speed (1-5)
- `mode` - Operating mode
- `filter_life` - Filter remaining (%)

## Automation Examples

### Auto-adjust based on AQI

```python
from components.tuya import get_tuya

tuya = get_tuya()

for device_name in ['bedroom', 'living_room']:
    aq = tuya.get_air_quality(device_name)

    if aq['pm25'] > 100:
        # Unhealthy - max speed
        tuya.set_power(device_name, on=True)
        tuya.set_fan_speed(device_name, 5)
    elif aq['pm25'] > 50:
        # Moderate - medium speed
        tuya.set_power(device_name, on=True)
        tuya.set_fan_speed(device_name, 3)
    elif aq['pm25'] < 25:
        # Good - turn off to save filter
        tuya.set_power(device_name, on=False)
```

### Leaving home automation

```python
# Turn off air purifiers when leaving
from components.tuya import set_power

set_power('bedroom', on=False)
set_power('living_room', on=False)
```

### Monitor filter life

```python
from components.tuya import get_status

for device_name in ['bedroom', 'living_room']:
    status = get_status(device_name)
    if status['filter_life'] < 20:
        print(f"⚠️ {status['name']}: Filter at {status['filter_life']}% - replace soon!")
```

## Architecture

```
components/tuya/
├── __init__.py         # Public API exports
├── client.py           # TuyaAPI class (main client)
├── air_purifier.py     # AlenAirPurifier device class
├── demo.py             # Demo/test script
└── README.md           # This file
```

**Key Classes:**
- `TuyaAPI` - Main client (singleton pattern)
- `AlenAirPurifier` - Device-specific controls

**Convenience Functions:**
- `get_air_quality(device_name)` → `{pm25, aqi, quality}`
- `set_power(device_name, on)` → Turn on/off
- `set_fan_speed(device_name, speed)` → Set speed 1-5
- `get_status(device_name)` → Full device status
- `list_all_status()` → All devices status

## Logging

All operations use structured logging with `kvlog()`:

```
api=tuya device=bedroom action=get_air_quality pm25=15 aqi=55 quality=good result=ok duration_ms=234
api=tuya device=living_room action=set_fan_speed speed=3 result=ok duration_ms=156
api=tuya device=bedroom action=get_status error_type=TuyaCloudException error_msg="Rate limit exceeded" duration_ms=145
```

## References

- **TinyTuya Library:** https://github.com/jasonacox/tinytuya
- **Tuya IoT Platform:** https://iot.tuya.com/
- **Alen-MQTT Integration:** https://github.com/dlarrick/alen-mqtt
- **US EPA AQI:** https://www.airnow.gov/aqi/aqi-basics/

## License

Part of py_home automation system.
