# iOS Shortcuts Geofencing Setup

Complete guide to setting up automatic location-based home automations using iOS Shortcuts.

## Overview

This system uses **3 geofences** to automatically trigger smart home actions as you travel:

1. **Leaving Work** (200m radius) → Pre-heat house 20+ min before arrival
2. **Near Home** (1000m radius) → Turn on lights 5-10 min out
3. **Arriving Home** (150m radius) → Full welcome automation

**Key Feature:** Zero manual interaction - your iPhone automatically sends location updates when crossing geofence boundaries.

---

## Prerequisites

- iOS 16+ (iOS Shortcuts with automation triggers)
- py_home Flask server running on Raspberry Pi (or local network)
- Server accessible via `http://raspberrypi.local:5000` or `http://YOUR_PI_IP:5000`
- Location Services enabled for Shortcuts app

---

## Geofence 1: Leaving Work

**Purpose:** Pre-heat/cool house when you leave work

**Setup:**

1. Open **Shortcuts** app on iPhone
2. Go to **Automation** tab → **+** (top right)
3. Select **Leave** (under Location)
4. Tap **Choose** → Search for your work address
5. Set **Radius: 200 meters**
6. Tap **Next**
7. Tap **Add Action** → Search for "**Get Contents of URL**"
8. Configure:
   ```
   URL: http://raspberrypi.local:5000/update-location
   Method: POST
   Headers:
       Content-Type: application/json
   Request Body: JSON
   ```
9. Tap **Request Body** → **Add Field**
10. Add these fields:
    ```json
    {
      "lat": Current Location Latitude,
      "lng": Current Location Longitude,
      "trigger": "leaving_work"
    }
    ```
11. To add `Current Location`:
    - Tap field value → **Select Variable** → **Current Location**
    - Choose **Latitude** or **Longitude**

12. **Add voice feedback** (optional but recommended):
    - Add action: **Get Dictionary from Input**
    - Add action: **Get Dictionary Value** → Key: `message`
    - Add action: **Speak Text** → Input: Dictionary Value

13. Tap **Next** → **Done**

**What it does:**
- Detects when you leave work geofence
- Sends your current location to server
- Server calculates ETA home
- If >20 min away: Pre-heats house based on weather
- Siri announces: "Pre-heating house. ETA: 35 min"

---

## Geofence 2: Arriving Near Home

**Purpose:** Turn on lights when approaching home

**Setup:**

1. Open **Shortcuts** app → **Automation** tab → **+**
2. Select **Arrive** (under Location)
3. Tap **Choose** → Search for your home address
4. Set **Radius: 1000 meters** (1km)
5. Tap **Next**
6. Tap **Add Action** → **Get Contents of URL**
7. Configure:
   ```
   URL: http://raspberrypi.local:5000/update-location
   Method: POST
   Headers:
       Content-Type: application/json
   Request Body: JSON
   ```
8. Add fields:
    ```json
    {
      "lat": Current Location Latitude,
      "lng": Current Location Longitude,
      "trigger": "near_home"
    }
    ```
9. Add voice feedback (same as Geofence 1)
10. Tap **Next** → Disable "**Ask Before Running**" → **Don't Ask** → **Done**

**What it does:**
- Triggers when you enter 1km radius around home
- Sends location to server
- Server calculates ETA (5-10 min)
- Turns on living room + bedroom lights
- Siri announces: "Turning on lights. ETA: 7 min"

---

## Geofence 3: Arriving Home

**Purpose:** Full welcome automation when you arrive

**Setup:**

1. Open **Shortcuts** app → **Automation** tab → **+**
2. Select **Arrive** (under Location)
3. Tap **Choose** → Enter your home address
4. Set **Radius: 150 meters**
5. Tap **Next**
6. Tap **Add Action** → **Get Contents of URL**
7. Configure:
   ```
   URL: http://raspberrypi.local:5000/update-location
   Method: POST
   Headers:
       Content-Type: application/json
   Request Body: JSON
   ```
8. Add fields:
    ```json
    {
      "lat": Current Location Latitude,
      "lng": Current Location Longitude,
      "trigger": "arriving_home"
    }
    ```
9. Add voice feedback
10. Tap **Next** → Disable "Ask Before Running" → **Done**

**What it does:**
- Triggers when crossing home geofence boundary
- Runs full `im_home.py` automation
- Sets Nest to comfort temperature
- Ensures key lights are on
- Siri announces: "Welcome home! Running arrival automation."

---

## Advanced: JSON Field Setup

When adding **Current Location** to JSON fields:

**For Latitude:**
1. Tap `"lat"` field value
2. Tap **Variables** → **Current Location**
3. Choose **Latitude**
4. Result: `Current Location → Latitude`

**For Longitude:**
1. Tap `"lng"` field value
2. Tap **Variables** → **Current Location**
3. Choose **Longitude**
4. Result: `Current Location → Longitude`

**For Trigger (text field):**
1. Type the trigger name exactly: `leaving_work`, `near_home`, or `arriving_home`

---

## Testing Your Geofences

### Test Without Leaving House

1. Open **Shortcuts** app
2. Go to **Automation** tab
3. Find your geofence automation
4. Tap the **automation** → Tap **▶** (play icon at bottom)
5. This simulates the trigger with your current location

**Note:** To properly test trigger logic, you'll need to actually cross the geofence boundaries.

### Test Server Connection

Create a manual shortcut to test server connectivity:

1. **Shortcuts** tab → **+**
2. Name: "Test Location Update"
3. Add action: **Get Contents of URL**
   ```
   URL: http://raspberrypi.local:5000/update-location
   Method: POST
   Headers: Content-Type: application/json
   Request Body: JSON
   ```
4. Add fields:
   ```json
   {
     "lat": Current Location Latitude,
     "lng": Current Location Longitude,
     "trigger": "manual",
     "trigger_automations": false
   }
   ```
5. Add: **Show Result**
6. Run shortcut - should show JSON response with distance from home

---

## Privacy & Battery

**Privacy:**
- Location only sent at geofence crossings (3 events per trip)
- NOT continuous tracking
- All data stored locally on your server
- No cloud services involved

**Battery Impact:**
- iOS uses cell towers for distant geofencing (very low power)
- GPS only activates near boundaries
- Estimated impact: **2-3% battery per day**

**Comparison:**
- Continuous GPS tracking: ~20% battery/day
- iOS geofencing: ~2-3% battery/day
- Background app refresh: ~1-2% battery/day

---

## Troubleshooting

### Automation Not Triggering

**Check:**
1. Location Services enabled: **Settings → Privacy → Location Services → Shortcuts → Always**
2. "Ask Before Running" is disabled on automations
3. iPhone is not in Low Power Mode (disables background location)
4. Shortcuts app has background refresh enabled

### Server Not Reachable

**Test connectivity:**
```bash
# From iPhone Safari, visit:
http://raspberrypi.local:5000/status

# Should show:
{
  "service": "py_home",
  "status": "running",
  ...
}
```

**If not working:**
- Check Pi is on same WiFi network
- Try IP address instead: `http://192.168.1.X:5000`
- Verify Flask server is running on Pi: `systemctl status py_home`

### Wrong Location Sent

iOS Shortcuts uses **Current Location** variable which may have:
- **Cached location** (slightly outdated)
- **Approximate location** (if GPS hasn't activated yet)

This is normal - the geofence trigger ensures you're in the right area even if coordinates are ~50m off.

### Automation Runs Multiple Times

iOS may trigger repeatedly if you linger near boundary. Server handles this by:
- Checking if action already taken recently
- Not re-running identical automation within 15 min

---

## Customization

### Adjust Geofence Sizes

**Work Geofence (Leaving):**
- Small office: 100m
- Large campus: 300-500m
- Parking lot: 200m (recommended)

**Near Home Geofence:**
- Urban (slow traffic): 500m (3-5 min)
- Suburban: 1000m (5-10 min, recommended)
- Rural (fast driving): 2000m (10-15 min)

**Home Geofence:**
- Apartment: 50m
- House: 150m (recommended)
- Large property: 300m

### Disable Specific Automations

Add `"trigger_automations": false` to prevent actions:
```json
{
  "lat": Current Location Latitude,
  "lng": Current Location Longitude,
  "trigger": "near_home",
  "trigger_automations": false
}
```

This still tracks location but doesn't run automations.

### Change Trigger Logic

Edit `lib/location.py` function `should_trigger_arrival()`:

```python
def should_trigger_arrival(trigger: str):
    # Customize distance thresholds:
    if trigger == "leaving_work":
        if distance > 10000:  # 10km instead of 5km
            return True, 'preheat'
```

---

## Quick Reference

| Geofence | Radius | Trigger Name | Action |
|----------|--------|--------------|--------|
| Leaving Work | 200m | `leaving_work` | Pre-heat house (20+ min ETA) |
| Near Home | 1000m | `near_home` | Turn on lights (5-10 min ETA) |
| Arriving Home | 150m | `arriving_home` | Full welcome automation |

**Server Endpoints:**
- `POST /update-location` - Update location and trigger automations
- `GET /location` - Get last known location and ETA

**Required JSON Fields:**
- `lat` (number) - Latitude from Current Location
- `lng` (number) - Longitude from Current Location
- `trigger` (string) - Geofence name

**Optional JSON Fields:**
- `trigger_automations` (boolean) - Default: true

---

## Next Steps

1. Set up all 3 geofences following templates above
2. Test each one using the ▶ button
3. Drive your normal commute to test in real world
4. Fine-tune geofence radii based on your preferences
5. Monitor server logs: `journalctl -u py_home -f`

**Need help?** Check server logs for errors or enable debug mode in Flask.
