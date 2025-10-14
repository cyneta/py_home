# iOS Shortcuts Geofencing Setup Guide

**Last Updated:** 2025-10-10
**System Status:** ✅ Backend fully implemented and tested, iOS 18.6 compatible
**Estimated Setup Time:** 10-15 minutes (one-time)
**iOS Version:** Tested on iOS 18.6.2

---

## Overview

Set up 2-3 iOS Shortcuts automations to enable smart home anticipation:
- **Leaving Work**: Pre-heat house 20+ minutes before you arrive
- **Near Home**: Turn on lights when approaching (inside 1km)
- **Arriving Home** (Optional): Redundant with WiFi detection - not required

**Battery Impact:** ~2-3% per day (iOS geofencing is very battery-efficient)

---

## How It Works

```
You leave work
    ↓
iPhone detects geofence crossing (GPS)
    ↓
iOS Shortcuts sends location to Pi
    ↓
Pi calculates: "15 min away, cold outside"
    ↓
Pi starts heating house NOW
    ↓
You arrive home to warm, lit house
```

**Privacy:** Only 2-3 location updates per trip. No continuous tracking. All data stored locally on Pi.

---

## Prerequisites

✅ iPhone with iOS 16+ (for background automations)
✅ Home WiFi network (for local communication)
✅ py_home Flask server running on `raspberrypi.local:5000`
✅ "Always Allow" location services for Shortcuts app

---

## Setup Instructions

### One-Time: Enable Location Services

**Note for iOS 18:** The Shortcuts app won't appear in Location Services until you create your first location-based automation. iOS will automatically prompt you to allow location access when you create the automation.

**When prompted:**
- Choose **"Always Allow"** (required for background automations)
- Enable **"Precise Location"**

**To verify later:**
1. Open **Settings** → **Privacy & Security** → **Location Services**
2. Find **Shortcuts** in the app list
3. Confirm it's set to **"Always"** with **"Precise Location"** enabled

---

## Automation 1: Leaving Work

**Purpose:** Pre-heat/cool house when you leave work (20+ min head start)

### Step-by-Step:

1. Open **Shortcuts** app on iPhone
2. Tap **Automation** tab (bottom center)
3. Tap **+** (top right)
4. Select **Create Personal Automation**
5. Scroll to **Location** → Tap **Leave**
6. Tap **Choose Location**
7. Search for your work address (or drop pin manually)
8. Set **Radius:** 200 meters
9. (Optional) Tap **Time Range** → Set Monday-Friday, 4 PM - 7 PM
10. Tap **Next**

### Add Actions (iOS 18.6):

11. Tap the **search box** at the bottom
12. Type: **"current location"** → Tap **"Get Current Location"**
13. Search: **"dictionary"** → Tap **"Dictionary"**
14. Configure the Dictionary with 3 key-value pairs:
    - Row 1: Key: `lat` | Value: Tap → Select **"Current Location"** → **"Latitude"**
    - Row 2: Key: `lng` | Value: Tap → Select **"Current Location"** → **"Longitude"**
    - Row 3: Key: `trigger` | Value: Type the text `leaving_work`
    - (Tap **"+"** to add each additional row)
15. Search: **"url"** → Tap **"Get Contents of URL"**
16. Configure the URL:
    - URL: `http://raspberrypi.local:5000/update-location`
    - Tap **"Show More"**
    - Method: **POST**
    - Request Body: **File** → Select **"Dictionary"**
    - (Optional) Headers: Add `Content-Type: application/json`
17. Tap **"Done"**
18. **CRITICAL:** Make sure **"Run Immediately"** is enabled (NOT "After Confirmation")

**What It Does:**
- Detects when you leave work parking lot
- Sends GPS location to Pi
- Pi pre-heats house based on outdoor temp + ETA
- You get notification: "Pre-heating house. ETA: 15 min. Nest → 72°F"

---

## Automation 2: Near Home

**Purpose:** Turn on lights when approaching home (5-10 min warning)

### Step-by-Step:

1. Same steps 1-5 as above
2. Tap **Choose Location** → Search "Home" or enter home address
3. Set **Radius:** 1000 meters (maximum allowed by iOS)
4. No time constraints needed (applies 24/7)
5. Tap **Next**

### Add Actions (iOS 18.6):

6. Follow same steps as "Leaving Work" automation (steps 11-17), but:
   - In Dictionary Row 3: Key: `trigger` | Value: Type `near_home`
7. Make sure **"Run Immediately"** is enabled
8. Tap **Done**

**What It Does:**
- Detects when you're ~0.6 miles from home
- Turns on living room lamp (always)
- Turns on bedroom lamps (if after 5 PM or before 7 AM)
- You get notification: "💡 Welcome Home Soon - Lights on: Living Room, Bedroom Left, Bedroom Right"

---

## Automation 3: Arriving Home (Optional - Not Recommended)

**Purpose:** Full welcome automation when crossing home geofence

**Why Skip This:** The WiFi event monitor (`automations/wifi_event_monitor.py`) already provides instant (<5 second) detection when your iPhone connects to home WiFi. This geofence would be redundant.

**If you still want it:**
1. Same as Automation 2, but:
   - Set **Radius:** 150 meters (matches config)
   - Use **trigger:** `arriving_home`

**What It Does:**
- Detects when you pull into driveway
- Runs full `im_home` automation
- Redundant with WiFi detection (not needed)

---

## Verification & Testing

### Test Each Automation:

**Option 1: Simulate Trigger (iOS 17+)**
1. Open **Shortcuts** app → **Automation** tab
2. Find the automation
3. Tap **...** (three dots)
4. Tap **Run Immediately** (test mode)
5. Check Pi logs for location update

**Option 2: Drive Test**
1. Drive to work/away from home
2. Drive back home
3. Watch for notifications at each geofence boundary
4. Check dashboard shows correct location

### Check Pi Logs:

```bash
ssh matt.wheeler@raspberrypi.local "tail -f /home/matt.wheeler/py_home/data/logs/flask_server.log"
```

Look for:
```
event="request_complete" method="POST" path="/update-location" status=200
module="location" action="update_location" lat=45.7060 lng=-121.5220 distance_m=524 trigger="leaving_work"
automation="arrival_preheat" event="start"
```

---

## Troubleshooting

### Automation didn't trigger
- Check: Location Services → Shortcuts → **Always**
- Check: "Ask Before Running" is **OFF**
- Check: iPhone not in Low Power Mode (disables background automations)
- Check: Pi server is running (`systemctl status py_home_flask`)

### Location update sent but no automation
- Check: Distance vs trigger threshold in `lib/location.py:204-238`
  - `leaving_work`: Must be >5km away
  - `near_home`: Must be ≤1km away (inside 1km geofence)
  - `arriving_home`: Must be ≤200m
- Current distance shown in notification message

### "Connection refused" error
- Check: iPhone on home WiFi (can't reach `raspberrypi.local` on cellular)
- Solution: Use VPN or Tailscale for remote access (future enhancement)

### Battery draining faster
- Normal: ~2-3% extra per day
- Excessive (>5%): Check for stuck GPS app, restart iPhone
- iOS optimizes geofencing automatically - give it 2-3 days to learn patterns

---

## Advanced Configuration

### Custom Geofence Locations

You can add more geofences for other locations:
- Coffee shop near home
- Grocery store (with shopping list reminder)
- Gym (different arrival time)

Just create new automations with different `trigger` names and update `lib/location.py` logic.

### Change Trigger Distances

Edit `lib/location.py` lines 204-238:

```python
def should_trigger_arrival(trigger: str) -> Tuple[bool, Optional[str]]:
    # Customize these thresholds:

    if trigger == "leaving_work":
        if distance > 5000:  # Change to 3000 for 3km threshold
            return True, 'preheat'

    elif trigger == "near_home":
        if distance <= 1000:  # Triggers when inside 1km radius
            return True, 'lights'
```

### Disable Geofencing Temporarily

Option 1: Disable automations in Shortcuts app
Option 2: Set `trigger_automations: false` in POST body
Option 3: Comment out in config (not implemented yet)

---

## Technical Details

### Endpoint: `/update-location`

**Request:**
```json
{
  "lat": 45.7100,
  "lng": -121.5200,
  "trigger": "leaving_work"
}
```

**Response:**
```json
{
  "status": "updated",
  "location": {"lat": 45.71, "lng": -121.52},
  "trigger": "leaving_work",
  "timestamp": "2025-10-10T17:17:00Z",
  "distance_from_home_meters": 5240.5,
  "is_home": false,
  "automation_triggered": "preheat",
  "message": "Pre-heating house. ETA: 15 min. Nest → 72°F",
  "eta": {
    "duration_minutes": 12,
    "duration_in_traffic_minutes": 15,
    "distance_miles": 5.2,
    "traffic_level": "moderate"
  }
}
```

### Data Storage

**File:** `data/location.json`

```json
{
  "lat": 45.706,
  "lng": -121.522,
  "trigger": "near_home",
  "timestamp": "2025-10-10T17:30:00Z",
  "distance_from_home_meters": 524.6,
  "is_home": false
}
```

**Retention:** Rolling 24-hour window
**Privacy:** Local Pi only, never uploaded to cloud

---

## What Gets Triggered

### Trigger: `leaving_work`

**Conditions:** Distance >5km from home

**Actions:**
- Calculate ETA using Google Maps (with traffic)
- If cold (<50°F): Set Nest to 72°F
- If hot (>75°F): Turn on Sensibo AC to 68°F
- Send notification with ETA

**Files:**
- `server/routes.py:682-765` - Endpoint handler
- `lib/location.py:204-238` - Trigger logic
- `automations/arrival_preheat.py` - Automation script

---

### Trigger: `near_home`

**Conditions:** Distance ≤1km from home (inside 1km geofence)

**Actions:**
- Turn on living room lamp (always)
- Turn on bedroom lamps (if after 5 PM or before 7 AM)
- Send notification with lights list

**Files:**
- `automations/arrival_lights.py`

---

### Trigger: `arriving_home`

**Conditions:** Distance <200m from home

**Actions:**
- Run full `im_home` automation
- WiFi event monitor also triggers (redundant, instant)

**Files:**
- `automations/im_home.py`
- `automations/wifi_event_monitor.py` (WiFi backup)

---

## System Architecture

```
iOS Shortcuts (Geofence)
    ↓
HTTP POST /update-location
    ↓
lib/location.py
    ├─ Store location data
    ├─ Calculate distance (Haversine)
    ├─ Get ETA (Google Maps API)
    └─ Determine automation trigger
         ↓
server/routes.py
    └─ Run automation script
         ↓
automations/arrival_*.py
    ├─ Control devices (Nest/Sensibo/Tapo)
    └─ Send notifications
```

---

## Next Steps

1. ✅ Set up 2 automations: Leaving Work + Near Home (10-15 min)
2. Test with real drive home
3. Monitor battery impact over 2-3 days
4. (Optional) Add VPN for remote geofencing
5. (Optional) Add more geofences: grocery store, gym, etc.

---

## FAQ

**Q: Do I need cellular data for this to work?**
A: Yes, when away from home. iPhone needs internet to POST location to Pi.

**Q: What if I'm on cellular and Pi is at home?**
A: Won't work unless you set up VPN/Tailscale. Geofencing currently requires home WiFi or VPN.

**Q: Can my spouse/family use this too?**
A: Yes! They set up same automations on their iPhone. Pi tracks last location update.

**Q: Does this replace WiFi presence detection?**
A: No, they work together. Geofencing is predictive (pre-heat), WiFi is instant (lights on arrival).

**Q: What if I forget my phone?**
A: WiFi presence shows "home" (phone at home). System thinks you're home. Manual control needed.

**Q: Can I use this to track my location history?**
A: No. System only stores latest location for 24 hours. No history tracking.

---

## Support

**Logs:**
- Flask server: `data/logs/flask_server.log`
- Arrival automations: `data/logs/arrival_*.log`
- Location updates: Look for `module="location"` in logs

**Dashboard:**
http://raspberrypi.local:5000/dashboard
(Shows current location, distance from home, ETA)

**Manual Testing:**
```bash
curl -X POST http://raspberrypi.local:5000/update-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 45.7100, "lng": -121.5200, "trigger": "manual"}'
```

---

**Status:** ✅ Ready for production use
**Tested:** 2025-10-10 (endpoint verified working)
**Dependencies:** iOS 16+, Flask server, Google Maps API
