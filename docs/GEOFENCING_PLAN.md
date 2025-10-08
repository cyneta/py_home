# iOS Geofencing Integration Plan

**Date:** 2025-10-07
**Location:** Hood River, Oregon (97031)
**Purpose:** Smart home anticipation - house gets ready before you arrive

---

## Overview

Use iOS Shortcuts geofencing to automatically notify the home when you're heading back, allowing the house to pre-heat, turn on lights, and prepare for your arrival - **without continuous location tracking**.

**Privacy-First Approach:**
- Only 2-3 location updates per trip home
- No tracking between geofence boundaries
- All data stored locally on Pi
- Minimal battery impact (~2-3% per day)

---

## How iOS Geofencing Works

### Core Technology

**iOS Location Services:**
- iPhone constantly monitors location (even when locked/sleeping)
- Uses: GPS, WiFi, Cell towers, Bluetooth beacons
- **Region Monitoring** API - designed specifically for geofencing
- Very battery-efficient (doesn't use full GPS constantly)

### Battery-Optimized Detection

iOS uses **different accuracy modes** based on context:

```
Far from any geofence:
├─ Cell tower triangulation only (~1-3 km accuracy)
├─ Checks every 5-10 minutes
└─ Battery: <1%/day

Approaching geofence:
├─ WiFi positioning (~100m accuracy)
├─ Checks every 1-2 minutes
└─ Battery: ~2%/day

Near geofence boundary:
├─ Full GPS (~10m accuracy)
├─ Checks every 30 seconds
└─ Battery: ~5%/day (only while near boundary)

Inside geofence:
├─ Back to low-power mode
└─ Waits for exit
```

**Result:** Battery impact is **minimal** because GPS only fires up when you're near a boundary.

---

## Real-World Example Flow

**Scenario: Leaving Work, Heading Home**

```
3:00 PM - At work (inside work geofence)
├─ iPhone: Low-power monitoring (cell towers)
└─ Battery: Minimal usage

5:15 PM - You walk to your car
├─ iPhone: Still inside geofence
└─ Nothing happens yet

5:17 PM - Drive out of parking lot
├─ iPhone detects: Crossed 200m boundary from "Work" location
├─ iOS Shortcuts triggers: "When I leave Work" automation
├─ Actions execute:
│   1. Get Current Location (using GPS)
│      Result: lat=45.7100, lng=-121.5200
│   2. POST to http://raspberrypi.local:5000/update-location
│      Body: {
│        "lat": 45.7100,
│        "lng": -121.5200,
│        "event": "left_work",
│        "timestamp": "2025-10-07T17:17:00"
│      }
├─ Pi receives request:
│   - Calculates distance from home: 5.2 miles
│   - Estimates ETA: 15 minutes (distance + traffic via Google Maps)
│   - Current home temp: 62°F (away mode)
│   - Action: Start heating to 72°F NOW
│   - Stores in .current_location file
└─ Response sent back to iPhone (automation completes)

5:17 PM - 5:30 PM - Driving home
├─ iPhone: No updates sent (between geofences)
├─ GPS: Not actively polling (battery saving)
└─ Pi: Heating house, monitoring ETA

5:30 PM - You're ~0.5 miles from home
├─ iPhone detects: Approaching "Near Home" geofence (1 mile radius)
├─ iOS Shortcuts triggers: "When I arrive Near Home" automation
├─ Actions execute:
│   1. Get Current Location
│   2. POST to /update-location
│      Body: {
│        "event": "near_home",
│        "lat": 45.7060,
│        "lng": -121.5220
│      }
├─ Pi receives:
│   - Distance: 0.5 miles
│   - ETA: 5 minutes
│   - Action: Turn on entry lights NOW
│   - Action: Schedule porch light at ETA-2min
└─ Lights turn on

5:33 PM - You arrive at driveway
├─ iPhone detects: Crossed 150m boundary (Home geofence)
├─ iOS Shortcuts triggers: "When I arrive Home" automation
├─ WiFi also detects: iPhone joined home network
├─ Pi receives both signals:
│   - Geofence: "arrived_home" event
│   - WiFi: presence_monitor detects home
├─ Pi actions:
│   - Run im_home automation
│   - Send notification: "Welcome home!"
│   - House is already warm (been heating for 15 min)
│   - Lights already on (turned on 3 min ago)
└─ You walk into warm, lit house

5:35 PM - You're inside, settled
├─ iPhone: Inside home geofence (stopped monitoring)
├─ WiFi: Confirmed home presence
└─ Battery: Used ~2% for entire trip's location services
```

---

## Smart "You're Coming Home" Scenarios

### Scenario 1: Preheating/Cooling
```
5:30 PM - You're 30 minutes from home (detected via geofence)
├─ Pi calculates: Distance 15 miles, traffic light, ETA 6:00 PM
├─ Current home temp: 62°F (been in away mode all day)
├─ Action: Start heating NOW to reach 72°F by 6:00 PM
└─ Result: House is warm when you walk in (instead of waiting 20 min after arrival)
```

### Scenario 2: Sunset Lighting
```
6:45 PM - You're 10 minutes away, sun setting
├─ Pi knows: Dark soon, you're arriving
├─ Action: Turn on entry lights, porch light
└─ Result: Well-lit arrival (instead of fumbling for light switch in dark)
```

### Scenario 3: Grocery Stop Reminder
```
5:15 PM - Driving home, passing Safeway
├─ Pi checks: You're 0.3 miles from Safeway, heading home
├─ Checkvist has: "Buy milk" on shopping list
├─ Action: iOS notification "You're near Safeway - need milk!"
└─ Result: Remember to stop (instead of getting home and realizing you forgot)
```

### Scenario 4: Bad Weather Alert
```
4:00 PM - Ice storm warning issued
├─ Pi checks: You're at work (last known location)
├─ Weather: Ice expected 5:00 PM, roads dangerous
├─ Action: Notification "Leave now! Ice storm at 5 PM, I-84 will be bad"
└─ Result: Leave early, avoid dangerous drive
```

### Scenario 5: Winter Pre-Warming
```
Winter morning, car covered in ice
├─ You leave for work at 8 AM
├─ Pi learns: You usually leave work at 5 PM
├─ At 4:45 PM: Start car heater remotely (if supported)
└─ Result: Warm car ready for drive home through gorge
```

---

## Geofencing Accuracy

**Depends on environment:**

| Scenario | Accuracy | Method | Battery |
|----------|----------|--------|---------|
| Urban area | ±10-20m | GPS + WiFi | Low |
| Suburban | ±20-50m | GPS + Cell | Medium |
| Rural (Hood River) | ±30-100m | GPS only | Higher |
| Indoors | ±100-500m | WiFi + Cell | Lowest |
| Highway driving | ±50m | GPS | Medium |

**Hood River specific:**
- Gorge area has good cell coverage (I-84 corridor)
- Some rural areas may have degraded accuracy
- WiFi detection at home is most reliable

---

## Recommended Geofence Setup

### 3 Geofences to Configure:

**1. Work (Leave)**
- **Location:** Your office/work address
- **Radius:** 200-300m
- **Trigger:** When I **leave**
- **Event:** `left_work`
- **Pi Action:** Start pre-heating/cooling (15-20 min head start)
- **Why:** Gives house maximum time to adjust temperature

**2. Near Home (Arrive)**
- **Location:** Home coordinates (45.7054, -121.5215)
- **Radius:** 1000m (0.6 miles / 1 km)
- **Trigger:** When I **arrive**
- **Event:** `near_home`
- **Pi Action:** Turn on lights, final preparations (5-10 min warning)
- **Why:** Visual confirmation house is ready, lights on before you arrive

**3. Home (Arrive)**
- **Location:** Home coordinates (45.7054, -121.5215)
- **Radius:** 150m (from config!)
- **Trigger:** When I **arrive**
- **Event:** `arrived_home`
- **Pi Action:** Full welcome automation + WiFi confirms presence
- **Why:** Confirms arrival, triggers any remaining automations

---

## iOS Shortcuts Setup (Step-by-Step)

### One-Time Setup for Each Geofence

**Time per geofence:** ~3-5 minutes
**Total setup time:** ~10-15 minutes
**Maintenance:** None (set and forget)

### Geofence 1: "When Leaving Work"

1. Open **Shortcuts** app on iPhone
2. Tap **Automation** tab (bottom)
3. Tap **+** (top right) → **Create Personal Automation**
4. Scroll to **Location** → Tap **Leave**
5. Tap **Choose** → Search for your work address
6. Set radius: **200-300 meters**
7. (Optional) Set time constraints: Monday-Friday, 4 PM - 7 PM
8. Tap **Next**
9. Tap **Add Action**
10. Search for **"Get Current Location"** → Add it
11. Tap **+** → Search for **"Get Contents of URL"**
12. Configure URL action:
    - **URL:** `http://raspberrypi.local:5000/update-location`
    - **Method:** POST
    - **Request Body:** JSON
    - Tap **Add field** → Add these fields:
      - `lat` = Current Location → Latitude
      - `lng` = Current Location → Longitude
      - `event` = Text: "left_work"
      - `timestamp` = Current Date
13. Tap **Next**
14. **IMPORTANT:** Toggle OFF "Ask Before Running"
15. Tap **Done**

### Geofence 2: "When Approaching Home"

1. Same steps 1-4 as above
2. Tap **Choose** → Search for "Home" or enter address
3. Set radius: **1000 meters** (maximum)
4. Continue steps 6-12, but use:
   - `event` = Text: "near_home"
5. Complete steps 13-15

### Geofence 3: "When Arriving Home"

1. Same steps as Geofence 2
2. Set radius: **150 meters**
3. Use `event` = Text: "arrived_home"

---

## Flask Implementation

### Endpoint: POST /update-location

**Receives from iPhone:**
```json
{
  "lat": 45.7100,
  "lng": -121.5200,
  "event": "left_work",
  "timestamp": "2025-10-07T17:17:00"
}
```

**Pi Processing:**
1. Calculate distance from home using haversine formula
2. Estimate ETA using Google Maps Distance Matrix API (with traffic)
3. Store in `.current_location` file
4. Trigger appropriate automation based on event + ETA

**Stored Data:**
```json
{
  "lat": 45.7100,
  "lng": -121.5200,
  "timestamp": "2025-10-07T17:17:00",
  "event": "left_work",
  "distance_from_home_miles": 5.2,
  "eta_minutes": 15,
  "last_updated": "2025-10-07T17:17:00"
}
```

**Response to iPhone:**
```json
{
  "status": "success",
  "distance_from_home": 5.2,
  "eta_minutes": 15,
  "action": "pre_heating_started"
}
```

### Automation Logic

**Event: `left_work`**
```python
if event == "left_work":
    eta = calculate_eta(lat, lng, home_coords, traffic=True)

    if eta >= 20:  # 20+ minutes away
        # Start HVAC now
        if current_season == 'winter':
            nest.set_temperature(comfort_temp)  # 72°F
        elif current_season == 'summer':
            sensibo.turn_on(mode='cool', temp=72)

        # Schedule lights for ETA-10min
        schedule_task(eta - 10, turn_on_entry_lights)
```

**Event: `near_home`**
```python
if event == "near_home":
    # Turn on lights NOW
    tapo.turn_on("Entry Light")
    tapo.turn_on("Porch Light")

    # Check if pre-heating happened, if not start now
    if nest.get_status()['current_temp_f'] < comfort_temp - 2:
        nest.set_temperature(comfort_temp)
```

**Event: `arrived_home`**
```python
if event == "arrived_home":
    # Run full im_home automation
    from automations.im_home import run
    run()

    # WiFi presence will also detect - both systems confirm
```

### Endpoint: GET /location

**Query current location status:**

```python
@app.route('/location', methods=['GET'])
def get_location():
    location = read_current_location()

    if not location:
        return {"status": "no_data", "using": "home_default"}

    age_minutes = (now - location['timestamp']).total_seconds() / 60

    if age_minutes > 60:
        # Stale data, use home as fallback
        return {
            "status": "stale",
            "using": "home_default",
            "last_update": age_minutes
        }

    return {
        "status": "current",
        "lat": location['lat'],
        "lng": location['lng'],
        "distance_from_home": location['distance_from_home_miles'],
        "eta_minutes": location['eta_minutes'],
        "event": location['event'],
        "age_minutes": age_minutes
    }
```

---

## Privacy & Data Storage

### What Gets Stored on Pi

**File: `.current_location`**
```json
{
  "lat": 45.7100,
  "lng": -121.5200,
  "timestamp": "2025-10-07T17:17:00",
  "event": "left_work",
  "distance_from_home_miles": 5.2,
  "eta_minutes": 15,
  "last_updated": "2025-10-07T17:17:00"
}
```

**Retention:** 24 hours (rolling window)
**Storage:** Local Pi only, not uploaded anywhere
**Access:** Only via local network (Flask server)

### What Leaves Your Network

**Only Google Maps API call:**
- Request: "Distance from [lat,lng] to [home] with traffic"
- Response: Distance, duration with current traffic
- Google knows: Two coordinates, no context about what they are

**No other external services involved.**

### What iOS Knows

- Your defined geofence locations (stored locally on iPhone)
- When you cross boundaries (local detection)

**Not sent to Apple servers** (unless you use iCloud to sync shortcuts)

---

## Failure Cases & Handling

### 1. Phone is offline (no cellular/WiFi)
```
- Geofence still triggers locally on iPhone
- POST to Pi fails (no network)
- When you get home: WiFi detection takes over
- Result: House may not pre-heat, but arrival still works
```

### 2. Battery died
```
- No geofence triggers
- When you plug in at home: WiFi detection works
- Result: Standard "arrived home" automation runs
```

### 3. Forgot phone at home
```
- WiFi presence shows "home" entire time
- No geofence triggers
- Result: House thinks you're home (stays in comfort mode)
- Solution: Manual "I'm leaving" shortcut as backup
```

### 4. Pi is offline/crashed
```
- iPhone tries to POST, fails silently
- iOS Shortcuts shows error (but you might not see it)
- When you arrive: WiFi might not work either
- Result: Manual control via iOS shortcuts or physical controls
```

### 5. Inaccurate ETA (traffic changes)
```
- Pi calculates ETA based on current traffic
- Traffic gets worse after you leave
- Result: House might be ready early (wastes 5-10 min of heating)
- Mitigation: Add buffer time to ETA calculations
```

---

## Configuration

### Update config.yaml with Hood River Location

```yaml
locations:
  home:
    lat: 45.7054
    lng: -121.5215
    radius_meters: 150  # Used for arrival geofence
    zip: "97031"
    city: "Hood River"
    state: "OR"

  work:
    lat: 45.7100  # Update with actual work location
    lng: -121.5200
    radius_meters: 250

openweather:
  api_key: "${OPENWEATHER_API_KEY}"
  units: "imperial"
  # Remove hardcoded zip, use location instead

automation:
  geofencing:
    enabled: true
    pre_heat_eta_threshold: 20  # Start HVAC if ETA >= 20 min
    lights_on_distance: 1.0  # Turn on lights at 1 mile
    eta_buffer_minutes: 5  # Add buffer to ETA calculations
```

### Environment Variables

No new credentials needed! Uses existing:
- `NEST_*` - For thermostat control
- `TAPO_*` - For outlet/light control
- `SENSIBO_API_KEY` - For AC control
- `GOOGLE_MAPS_API_KEY` - For ETA calculations

---

## Implementation Tasks

### Phase 1: Flask Endpoint & Location Storage
- [ ] Add `/update-location` POST endpoint to `server/routes.py`
- [ ] Implement location storage in `.current_location` file
- [ ] Add distance calculation (haversine formula)
- [ ] Add ETA calculation via Google Maps API
- [ ] Add `/location` GET endpoint for status queries

### Phase 2: Smart Arrival Logic
- [ ] Implement `left_work` event handler (pre-heat/cool)
- [ ] Implement `near_home` event handler (lights on)
- [ ] Implement `arrived_home` event handler (welcome automation)
- [ ] Add ETA-based task scheduling
- [ ] Integrate with existing automations

### Phase 3: Update Existing Services
- [ ] Update `config.yaml` with Hood River coordinates
- [ ] Update OpenWeather to use dynamic location
- [ ] Update automations to check current location
- [ ] Add location staleness checks (fallback to home)

### Phase 4: iOS Shortcuts Templates
- [ ] Create "Leaving Work" shortcut template
- [ ] Create "Near Home" shortcut template
- [ ] Create "Arrived Home" shortcut template
- [ ] Document setup instructions
- [ ] Create backup manual shortcuts

### Phase 5: Testing & Validation
- [ ] Test geofence triggers in real-world
- [ ] Validate ETA calculations
- [ ] Test failure scenarios
- [ ] Monitor battery impact
- [ ] Fine-tune geofence radii

---

## Benefits Summary

**For You:**
- Walk into warm, lit house (not cold and dark)
- No manual "I'm home" commands needed
- House anticipates your needs
- Minimal battery impact (~2-3%/day)
- Privacy-focused (only boundary crossings tracked)

**For System:**
- More efficient HVAC usage (pre-heating vs reactive)
- Better automation triggers (ETA-based vs arrival-based)
- Redundant presence detection (geofence + WiFi)
- Foundation for future automations (grocery reminders, weather alerts)

**Total Setup Effort:**
- Implementation: 3-4 hours
- iOS Setup: 10-15 minutes
- Maintenance: None

---

## Future Enhancements (Optional)

### Phase 6: Advanced Features
- [ ] Multiple work locations (coffee shop, coworking space)
- [ ] Grocery store geofences (with shopping list integration)
- [ ] Traffic alerts (I-84 through gorge)
- [ ] Weather-based ETA adjustments (snow, ice)
- [ ] Learning: Auto-detect work location from patterns
- [ ] Share location with family (multiple users)

### Phase 7: Seasonal Automations
- [ ] Winter: Remote car start at ETA-10min
- [ ] Summer: Pre-cool house before arrival
- [ ] Fall: Turn on fireplace remotely
- [ ] Spring: Open windows if weather is nice

---

**Status:** Ready for implementation
**Next Step:** Build Flask endpoint and location storage system
**Estimated Completion:** 3-4 hours of development + 15 min iOS setup
