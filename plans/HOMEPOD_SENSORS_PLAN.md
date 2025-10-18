# HomePod Environment Sensors Integration Plan

Get temperature and humidity data from HomePod/HomePod mini sensors into py_home.

---

## Problem

HomePod and HomePod mini have built-in temperature and humidity sensors, but:
- ❌ No direct API access (Apple doesn't expose them via HomeKit APIs)
- ❌ Only accessible through Apple Home app
- ⚠️ Occasionally broken by HomePod OS updates

This is valuable data for HVAC coordination and monitoring that we're currently missing.

---

## Research Summary

### What Works

**HomePod Sensors Available:**
- Temperature (°F or °C)
- Humidity (%)
- Available in: HomePod mini, HomePod 2nd gen

**Workaround Method:**
- HomeKit automation triggers on sensor change
- Automation runs iOS Shortcut
- Shortcut sends HTTP POST to py_home Flask server
- Server stores sensor data

### Known Issues (2025)

- Since HomePod Software 18.2 / iOS 18.2: HTTP requests sometimes don't send
- Apple updates occasionally break the automation
- No direct API = dependent on Apple's Home app automation features

---

## Proposed Architecture

```
┌─────────────────┐
│  HomePod mini   │
│  (Bedroom)      │
│  Temp: 68°F     │
│  Humidity: 45%  │
└────────┬────────┘
         │ Sensor change detected
         ▼
┌─────────────────────────────┐
│  HomeKit Automation         │
│  "When temp/humidity        │
│   changes in Bedroom"       │
└────────┬────────────────────┘
         │ Triggers
         ▼
┌─────────────────────────────┐
│  iOS Shortcut               │
│  "Send HomePod Data"        │
│  - Get sensor values        │
│  - POST to py_home server   │
└────────┬────────────────────┘
         │ HTTP POST
         ▼
┌─────────────────────────────┐
│  Flask Server               │
│  POST /homepod-sensors      │
│  - Validate data            │
│  - Store in file            │
│  - Update timestamp         │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  data/homepod_sensors.json  │
│  {                          │
│    "bedroom": {             │
│      "temp_f": 68,          │
│      "humidity": 45,        │
│      "updated": "..."       │
│    }                        │
│  }                          │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Automations can read       │
│  - temp_coordination.py     │
│  - air_quality_monitor.py   │
│  - Dashboard                │
└─────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Flask Endpoint (30 min)

**Create webhook endpoint:**

```python
# server/routes.py

@app.route('/homepod-sensors', methods=['POST'])
def homepod_sensors():
    """
    Receive HomePod sensor data from HomeKit automation

    Expected POST data:
    {
        "room": "bedroom",
        "temperature": 68.5,
        "humidity": 45.2,
        "timestamp": "2025-10-18T15:30:00Z"
    }
    """
    data = request.json

    # Validate
    required = ['room', 'temperature', 'humidity']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400

    # Store to file
    from components.homepod import store_sensor_data
    store_sensor_data(data)

    logger.info(f"HomePod sensors updated: {data['room']} {data['temperature']}°F {data['humidity']}%")

    return jsonify({'status': 'ok'}), 200
```

**Create storage component:**

```python
# components/homepod/__init__.py

from pathlib import Path
import json
from datetime import datetime

DATA_FILE = Path(__file__).parent.parent.parent / 'data' / 'homepod_sensors.json'

def store_sensor_data(data):
    """Store HomePod sensor data to JSON file"""
    room = data['room']

    # Load existing data
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            all_data = json.load(f)
    else:
        all_data = {}

    # Update room data
    all_data[room] = {
        'temp_f': data['temperature'],
        'humidity': data['humidity'],
        'updated_at': data.get('timestamp', datetime.now().isoformat())
    }

    # Save
    DATA_FILE.parent.mkdir(exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(all_data, f, indent=2)

def get_sensor_data(room):
    """Get latest sensor data for a room"""
    if not DATA_FILE.exists():
        return None

    with open(DATA_FILE) as f:
        all_data = json.load(f)

    return all_data.get(room)

def get_all_sensors():
    """Get all HomePod sensor data"""
    if not DATA_FILE.exists():
        return {}

    with open(DATA_FILE) as f:
        return json.load(f)
```

### Phase 2: iOS Shortcut Setup (15 min)

**Create iOS Shortcut "Update HomePod Bedroom Sensors":**

1. Add "Get Current Temperature" from Home
   - Select: Bedroom HomePod
2. Add "Get Current Humidity" from Home
   - Select: Bedroom HomePod
3. Add "Text" action:
   ```json
   {
     "room": "bedroom",
     "temperature": [Temperature from step 1],
     "humidity": [Humidity from step 2],
     "timestamp": "[Current Date in ISO format]"
   }
   ```
4. Add "Get Contents of URL"
   - URL: `http://100.107.121.6:5000/homepod-sensors`
   - Method: POST
   - Headers: Content-Type = application/json
   - Request Body: [Text from step 3]

### Phase 3: HomeKit Automation (10 min)

**Create Home automation:**

1. Open Home app → Automation tab
2. Create new automation
3. Trigger: "A Sensor Detects Something"
   - Select: Bedroom HomePod Temperature
   - Condition: Changes (any change)
4. Action: "Convert to Shortcut"
5. Add action: Run Shortcut "Update HomePod Bedroom Sensors"
6. Turn OFF "Ask Before Running" (fully automatic)

**Repeat for each HomePod location.**

### Phase 4: Integration with Automations (30 min)

**Use sensor data in automations:**

```python
# automations/temp_coordination.py

from components.homepod import get_sensor_data

# Get HomePod data
bedroom_sensors = get_sensor_data('bedroom')
if bedroom_sensors:
    bedroom_temp = bedroom_sensors['temp_f']
    bedroom_humidity = bedroom_sensors['humidity']

    # Use in coordination logic
    if bedroom_temp < 65:
        # Turn on bedroom heater
        pass
```

**Add to dashboard:**

```python
# Show HomePod sensor data
from components.homepod import get_all_sensors

homepod_data = get_all_sensors()
for room, data in homepod_data.items():
    print(f"{room}: {data['temp_f']}°F, {data['humidity']}%")
```

---

## Testing Plan

### Test Flask Endpoint

```bash
# Test POST endpoint
curl -X POST http://localhost:5000/homepod-sensors \
  -H "Content-Type: application/json" \
  -d '{
    "room": "bedroom",
    "temperature": 68.5,
    "humidity": 45.2,
    "timestamp": "2025-10-18T15:30:00Z"
  }'

# Verify storage
cat data/homepod_sensors.json
```

### Test iOS Shortcut

1. Run shortcut manually from Shortcuts app
2. Check Flask logs for incoming POST
3. Verify data/homepod_sensors.json updated

### Test HomeKit Automation

1. Change bedroom temperature physically (or wait for natural change)
2. Verify automation triggers within ~1 minute
3. Check Flask logs
4. Verify data file updated

---

## Known Limitations

### Apple's Restrictions
- ❌ No direct API access (must use Home app automation)
- ⚠️ Updates can break HTTP request functionality
- ⏱️ Update frequency limited by sensor change detection (~1-5 min)

### Workarounds
- ✅ Fallback to TempStick for critical monitoring
- ✅ Use HomePod as supplemental data (not primary)
- ✅ Log failures when data is stale (> 10 minutes)

### Data Staleness

```python
# Check if data is fresh
from datetime import datetime, timedelta

def is_data_fresh(room, max_age_minutes=10):
    data = get_sensor_data(room)
    if not data:
        return False

    updated = datetime.fromisoformat(data['updated_at'])
    age = datetime.now() - updated

    return age < timedelta(minutes=max_age_minutes)
```

---

## Future Enhancements

### Multiple HomePods

Add support for living room, office, etc.:

```python
# Auto-detect rooms from incoming data
# No config changes needed - dynamic!
```

### Alerting

```python
# Alert if HomePod data goes stale
if not is_data_fresh('bedroom', max_age_minutes=15):
    send_high("HomePod bedroom sensors offline")
```

### HVAC Coordination

```python
# Use multi-room data for better decisions
bedroom = get_sensor_data('bedroom')
living_room = get_sensor_data('living_room')

# Average temps across rooms
avg_temp = (bedroom['temp_f'] + living_room['temp_f']) / 2
```

---

## Deployment Checklist

- [ ] Implement Flask endpoint in server/routes.py
- [ ] Create components/homepod/ module
- [ ] Add data/homepod_sensors.json to .gitignore
- [ ] Test endpoint with curl
- [ ] Create iOS Shortcut
- [ ] Test shortcut manually
- [ ] Create HomeKit automation
- [ ] Test automation triggers
- [ ] Add to dashboard
- [ ] Add staleness alerting
- [ ] Update documentation

---

## Estimated Effort

- Implementation: 1-2 hours
- Testing: 30 minutes
- iOS/HomeKit setup: 30 minutes per HomePod
- **Total: ~2-3 hours for full integration**

---

## References

- [Connecting HomePod Sensors to Home Assistant](https://medium.com/@federicoimberti/connecting-homepods-temperature-and-humidity-sensors-to-home-assistant-952398a1a2be)
- [Home Assistant Community Guide](https://community.home-assistant.io/t/how-to-integrate-homepod-mini-sensors-into-home-assistant-when-direct-integration-isnt-possible/665074)
- [How to Use HomePod Sensors - 9to5Mac](https://9to5mac.com/2023/02/03/use-homepod-temperature-and-humidity-sensors/)

---

## Decision: Proceed?

**Pros:**
- ✅ Free additional temperature/humidity sensors (already own HomePods)
- ✅ Room-specific data for better HVAC coordination
- ✅ Simple implementation (~2-3 hours)

**Cons:**
- ⚠️ Dependent on Apple's automation features (fragile)
- ⚠️ Data may go stale if automation breaks
- ⚠️ Not suitable as primary sensor (use TempStick for critical monitoring)

**Recommendation:** Implement as **supplemental sensor data**, not primary. Use for nice-to-haves like room-specific comfort and multi-zone averaging.
