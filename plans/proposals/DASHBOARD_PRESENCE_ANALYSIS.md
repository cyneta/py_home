# Dashboard and Presence Detection Analysis

**Date:** 2025-10-11
**Status:** Investigation Complete - Ready for Implementation

---

## User Questions Answered

### Q1: Dashboard should tell me if system is operational
**Answer:** Currently missing. Dashboard only shows device status, not system health.

**What's needed:**
- Presence monitor cron status (running/stopped)
- WiFi event monitor service status
- Flask server uptime (time since Flask started, not Pi uptime)
- Last presence check timestamp
- API health checks

---

### Q2: I have restarted the Pi, but uptime does not indicate that
**Answer:** The "uptime" shown is **Pi system uptime** (from `/proc/uptime`), not Flask server uptime.

**Current behavior:**
```python
# server/routes.py:180-187
with open('/proc/uptime', 'r') as f:
    uptime_seconds = float(f.readline().split()[0])
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    uptime = f"{days}d {hours}h"
```

This shows how long the Pi has been powered on, not how long Flask has been running.

**What's needed:**
- Track Flask server start time in memory
- Calculate `time.time() - flask_start_time` for actual Flask uptime

---

### Q3: If Pi is not there what should dashboard display?
**Answer:** Currently, dashboard fails silently or shows mock data.

**Current behavior:**
- API calls fail → JavaScript catches error → shows mock/stale data
- No visual indication that Pi is unreachable
- User can't tell if data is real or fallback

**What's needed:**
- Add connection status indicator (green=connected, red=offline)
- Show "Last successful update: X minutes ago"
- Display error banner: "⚠️ Unable to reach Pi at raspberrypi.local"
- Fallback to read-only mode with cached data

---

### Q4: What are the modes which can be displayed on the dashboard?
**Answer:** Currently only 2 modes are implemented:

#### Location Card Modes:
```javascript
// server/routes.py:321-344
'HOME' (green badge)  - when is_home: true
'AWAY' (yellow badge) - when is_home: false
```

#### System Card Modes:
```javascript
// server/routes.py:347-395
'NIGHT MODE' (yellow badge) - when night mode active
'DAY MODE' (green badge)    - when not night mode
'Running' (green)           - Service status (always shows "Running")
```

**Proposed additional modes:**
- **Location Card:**
  - `HOME` (green) - Present at home
  - `AWAY` (yellow) - Not at home
  - `ARRIVING` (blue) - Near home (<1km)
  - `TRAVELING` (gray) - Far from home (>5km)
  - `UNKNOWN` (gray) - No recent data

- **System Card:**
  - `OPERATIONAL` (green) - All systems running
  - `DEGRADED` (yellow) - Some monitors offline
  - `ERROR` (red) - Critical failures
  - `STARTING` (blue) - Just started, initializing

---

### Q5: Why is status indicated as Away right now?
**Answer:** Dashboard is reading **stale iOS geofencing data** instead of **current presence monitor status**.

**The Bug:**
```javascript
// Dashboard calls /location endpoint
async function fetchLocation() {
    const response = await fetch('/location');  // ← WRONG
    return await response.json();
}
```

**What `/location` returns (WRONG):**
```json
{
    "age_seconds": 31253.0,           // 8.7 hours old!
    "distance_from_home_meters": 455.9,
    "is_home": false,                 // ← Shows AWAY (wrong)
    "lat": 45.7095,
    "lng": -121.5215,
    "timestamp": "2025-10-11T05:15:43Z",
    "trigger": "near_home"
}
```

**What `.presence_state` says (CORRECT):**
```bash
$ cat /home/matt.wheeler/py_home/.presence_state
home  # ← You ARE home (correct)
```

**Root cause:**
- iOS Shortcuts geofencing last updated 8+ hours ago (5:15 AM)
- You've been home since then
- Dashboard reads GPS location data instead of WiFi/ping presence state

---

## Presence Detection System Architecture

You have **THREE separate systems** (not internal geofencing):

### System 1: WiFi Event Monitor (INSTANT)
```
Location: automations/wifi_event_monitor.py
Runs as:  systemd service (always on)
Method:   Monitors DHCP journal for iPhone IP lease events
Speed:    Sub-5 seconds (instant when WiFi connects)
Updates:  .presence_state file
Use case: Triggers im_home.py when you arrive
```

**How it works:**
1. Watches `journalctl -f -u dnsmasq` for DHCP events
2. Sees: `DHCPACK(br0) 192.168.50.189 ... Matt's-iPhone`
3. Checks `.presence_state` → if was "away", now "home"
4. Triggers `im_home.py` automation
5. 30-second cooldown to prevent re-triggers

**Advantages:**
- Instant detection (no polling delay)
- Reliable (DHCP always fires when connecting)
- No iOS interaction needed

### System 2: Presence Monitor Cron (POLLING)
```
Location: automations/presence_monitor.py
Runs as:  cron job (every 2 minutes)
Method:   Pings iPhone IP address (ICMP)
Speed:    Up to 2-minute delay
Updates:  .presence_state file
Use case: Detects departures (iPhone stops responding)
```

**How it works:**
1. Cron runs every 2 minutes
2. Pings `192.168.50.189`
3. If ping fails → iPhone not home
4. Compares to previous state
5. If changed from "home" → "away": triggers `leaving_home.py`

**Advantages:**
- Reliable departure detection
- Backup for WiFi monitor
- Works even if DHCP logging disabled

**Disadvantages:**
- 2-minute delay (not instant)
- Requires iPhone to respond to ping

### System 3: iOS Shortcuts Geofencing (PREDICTIVE)
```
Location: iOS Shortcuts → POST /update-location
Stores:   data/location.json (GPS coordinates)
Method:   iOS geofence boundary crossings
Speed:    Instant (when boundary crossed)
Updates:  location.json (NOT .presence_state)
Use case: Predictive actions BEFORE you arrive
```

**Geofence triggers:**

#### "leaving_work" (>5km from home)
```json
POST /update-location
{
  "lat": 45.7100,
  "lng": -121.5200,
  "trigger": "leaving_work"
}
```
**Action:** Pre-heat house (20+ min away)
**Script:** `automations/arrival_preheat.py`

#### "near_home" (≤1km from home)
```json
POST /update-location
{
  "lat": 45.7060,
  "lng": -121.5220,
  "trigger": "near_home"
}
```
**Action:** Turn on lights (5-10 min away)
**Script:** `automations/arrival_lights.py`

#### "arriving_home" (≤200m from home)
```json
POST /update-location
{
  "lat": 45.7054,
  "lng": -121.5215,
  "trigger": "arriving_home"
}
```
**Action:** Full arrival automation
**Script:** `automations/im_home.py` (redundant with WiFi)

**Advantages:**
- Predictive (can pre-heat house)
- Location-aware (knows distance/ETA)
- Battery efficient (iOS geofencing)

**Disadvantages:**
- Requires cellular data (won't work on home WiFi)
- Only updates when crossing boundaries
- Goes stale if you don't leave home

---

## The Dashboard Bug Explained

### Current Dashboard Logic (WRONG)
```javascript
// server/routes.py:257-269
async function fetchLocation() {
    try {
        const response = await fetch('/location');  // Calls GET /location
        if (response.ok) {
            return await response.json();
        }
    } catch (e) {}

    // Fallback to mock data
    return {
        is_home: true,  // Assumes home if API fails
        distance_from_home_meters: 0
    };
}

// server/routes.py:321-344
function renderLocationCard(data) {
    const locationBadge = data.is_home ? 'badge-home' : 'badge-away';
    const locationText = data.is_home ? 'HOME' : 'AWAY';
    // ...
}
```

### What GET /location Returns (WRONG)
```python
# server/routes.py:571-604
@app.route('/location', methods=['GET'])
def get_location():
    from lib.location import get_location as get_loc  # ← Reads data/location.json

    location = get_loc()  # Returns GPS data from iOS Shortcuts
    # ...
```

```python
# lib/location.py:107-140
def get_location():
    """Get user's last known location"""
    if not os.path.exists(LOCATION_FILE):  # data/location.json
        return None

    with open(LOCATION_FILE, 'r') as f:
        data = json.load(f)

    # Calculate age
    timestamp = datetime.fromisoformat(data['timestamp'])
    age = (datetime.utcnow() - timestamp.replace(tzinfo=None)).total_seconds()
    data['age_seconds'] = round(age, 1)

    return data
```

**File: `data/location.json`** (8 hours old)
```json
{
  "lat": 45.7095,
  "lng": -121.5215,
  "trigger": "near_home",
  "timestamp": "2025-10-11T05:15:43.046083Z",  // 8 hours ago
  "distance_from_home_meters": 455.9,
  "is_home": false  // ← WRONG! Based on stale GPS
}
```

**Problem:**
- Last iOS geofence update was at 5:15 AM (trigger: "near_home")
- At that moment, you were 456m from home (approaching)
- System calculated `is_home: false` (outside 150m home radius)
- You've been home for 8 hours since then
- Dashboard reads this stale data and shows "AWAY"

### What Dashboard SHOULD Read (CORRECT)
**File: `.presence_state`** (current)
```
home
```

**Updated by:**
- `wifi_event_monitor.py` - when WiFi connects (instant)
- `presence_monitor.py` - every 2 minutes (ping check)

**Last updated:** 06:47 AM (just now via cron)

---

## Fix Implementation Plan

### Fix 1: Add `/api/presence` Endpoint
```python
# server/routes.py (after line 195)
@app.route('/api/presence')
def api_presence():
    """Get current presence status from presence monitor"""
    try:
        import os
        state_file = os.path.join(
            os.path.dirname(__file__), '..', '.presence_state'
        )

        if not os.path.exists(state_file):
            return jsonify({
                'is_home': None,
                'source': 'unknown',
                'last_updated': None
            }), 200

        # Read state
        with open(state_file, 'r') as f:
            state = f.read().strip().lower()

        # Get file modification time
        mtime = os.path.getmtime(state_file)
        import time
        from datetime import datetime
        age_seconds = time.time() - mtime
        last_updated = datetime.fromtimestamp(mtime).isoformat()

        return jsonify({
            'is_home': state == 'home',
            'state': state,
            'source': 'presence_monitor',
            'last_updated': last_updated,
            'age_seconds': round(age_seconds, 1)
        }), 200

    except Exception as e:
        logger.error(f"Failed to get presence status: {e}")
        return jsonify({'error': str(e)}), 500
```

### Fix 2: Update Dashboard to Use Presence API
```javascript
// server/routes.py (replace fetchLocation function)
async function fetchPresence() {
    try {
        const response = await fetch('/api/presence');  // ← NEW
        if (response.ok) {
            return await response.json();
        }
    } catch (e) {}

    return {
        is_home: null,
        source: 'error',
        last_updated: null
    };
}
```

### Fix 3: Update renderLocationCard to Handle Age
```javascript
function renderLocationCard(data) {
    let locationBadge, locationText, statusText;

    if (data.is_home === null) {
        locationBadge = 'badge-offline';
        locationText = 'UNKNOWN';
        statusText = 'No presence data available';
    } else if (data.age_seconds > 300) {  // 5 minutes
        locationBadge = 'badge-warning';
        locationText = data.is_home ? 'HOME' : 'AWAY';
        statusText = `Last checked ${Math.round(data.age_seconds / 60)} min ago`;
    } else {
        locationBadge = data.is_home ? 'badge-home' : 'badge-away';
        locationText = data.is_home ? 'HOME' : 'AWAY';
        statusText = 'Current';
    }

    return `
        <div class="card">
            <div class="card-title">📍 Presence</div>
            <div class="status-row">
                <span class="status-label">Status</span>
                <span class="badge ${locationBadge}">${locationText}</span>
            </div>
            <div class="status-row">
                <span class="status-label">Source</span>
                <span class="status-value">${data.source || 'unknown'}</span>
            </div>
            <div class="status-row">
                <span class="status-label">Last Update</span>
                <span class="status-value">${statusText}</span>
            </div>
        </div>
    `;
}
```

### Fix 4: Add Flask Server Uptime Tracking
```python
# server/__init__.py (add at module level)
import time
FLASK_START_TIME = time.time()

# server/routes.py (update /api/night-mode)
@app.route('/api/night-mode')
def api_night_mode():
    from server import FLASK_START_TIME

    # Calculate Flask uptime
    uptime_seconds = time.time() - FLASK_START_TIME
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)

    if days > 0:
        uptime = f"{days}d {hours}h"
    elif hours > 0:
        uptime = f"{hours}h {minutes}m"
    else:
        uptime = f"{minutes}m"

    return jsonify({
        'night_mode': is_night_mode(),
        'uptime': uptime,
        'uptime_seconds': int(uptime_seconds)
    }), 200
```

### Fix 5: Add System Health Status
```python
@app.route('/api/system-health')
def api_system_health():
    """Get system health status"""
    import subprocess
    import os

    health = {
        'status': 'operational',
        'services': {}
    }

    # Check presence monitor cron
    try:
        result = subprocess.run(
            ['ssh', 'matt.wheeler@raspberrypi.local', 'crontab -l | grep presence_monitor'],
            capture_output=True,
            text=True,
            timeout=5
        )
        health['services']['presence_monitor_cron'] = {
            'status': 'enabled' if result.returncode == 0 else 'disabled',
            'type': 'cron'
        }
    except:
        health['services']['presence_monitor_cron'] = {
            'status': 'unknown',
            'type': 'cron'
        }

    # Check WiFi event monitor service
    try:
        result = subprocess.run(
            ['ssh', 'matt.wheeler@raspberrypi.local',
             'systemctl is-active py_home_wifi_monitor'],
            capture_output=True,
            text=True,
            timeout=5
        )
        health['services']['wifi_event_monitor'] = {
            'status': result.stdout.strip(),  # 'active' or 'inactive'
            'type': 'systemd'
        }
    except:
        health['services']['wifi_event_monitor'] = {
            'status': 'unknown',
            'type': 'systemd'
        }

    # Check last presence update age
    state_file = os.path.join(os.path.dirname(__file__), '..', '.presence_state')
    if os.path.exists(state_file):
        age = time.time() - os.path.getmtime(state_file)
        health['presence_check_age_seconds'] = int(age)
        if age > 600:  # 10 minutes
            health['status'] = 'degraded'

    return jsonify(health), 200
```

---

## Summary of Issues

1. ❌ **Dashboard shows AWAY when you're HOME**
   - Root cause: Reading stale GPS data instead of presence state
   - Fix: Add `/api/presence` endpoint, read `.presence_state`

2. ❌ **Uptime shows Pi uptime, not Flask uptime**
   - Root cause: Reading `/proc/uptime` (system uptime)
   - Fix: Track `FLASK_START_TIME` in memory

3. ❌ **No system operational status**
   - Root cause: Dashboard only shows device status
   - Fix: Add `/api/system-health` with cron/service checks

4. ❌ **No handling for Pi offline**
   - Root cause: JavaScript catch returns mock data silently
   - Fix: Add connection status indicator + age warnings

5. ❌ **Limited dashboard modes**
   - Root cause: Only HOME/AWAY modes implemented
   - Fix: Add UNKNOWN, ARRIVING, TRAVELING, DEGRADED, ERROR modes

---

## Next Steps

**Priority 1: Fix presence status bug**
1. Add `/api/presence` endpoint
2. Update dashboard to call new endpoint
3. Deploy to Pi
4. Test: Dashboard should show "HOME" immediately

**Priority 2: Add operational status**
1. Add Flask uptime tracking
2. Add system health endpoint
3. Update System card to show health status
4. Add "Last checked" timestamps

**Priority 3: Improve resilience**
1. Add connection status indicator
2. Handle stale data warnings (>5 min)
3. Graceful degradation when Pi offline
4. Add manual refresh button

---

## Testing Checklist

After implementation:

- [ ] Dashboard shows "HOME" when `.presence_state` = "home"
- [ ] Dashboard shows "AWAY" when `.presence_state` = "away"
- [ ] Uptime resets when Flask restarts (not when Pi restarts)
- [ ] System card shows cron status (enabled/disabled)
- [ ] System card shows WiFi monitor status (active/inactive)
- [ ] Dashboard shows warning when presence data >5 min old
- [ ] Dashboard shows error when Pi unreachable
- [ ] Manual refresh button works
- [ ] Auto-refresh continues working (5 seconds)

---

**End of Analysis**
