# Flask API Endpoints Overview

**Status:** Current as of 2025-10-13
**Base URL:** `http://raspberrypi.local:5000`

---

## Status Indicators

- 🟢 **Active** - Currently exercised by automations/dashboard
- 🟡 **Available** - Configured but not automatically triggered
- 🔵 **Manual** - User-triggered only (Siri, buttons)
- ⚪ **Unused** - Implemented but not currently used
- 🔴 **Deprecated** - Legacy, should be removed

---

## Core Endpoints

### 🟢 `GET /`
**Purpose:** Root redirect to dashboard
**Used By:** Browser access
**Returns:** Redirect to `/dashboard`

### 🟢 `GET /status`
**Purpose:** Basic health check
**Used By:**
- ph_home-geofence.js (network detection)
- Monitoring scripts
**Returns:** `{"status": "ok"}`

---

## Dashboard & API Endpoints

### 🟢 `GET /dashboard`
**Purpose:** Main web UI
**Used By:** User browser access
**Shows:**
- Nest thermostat status
- Sensibo AC status
- TempStick sensor
- Tapo outlets (4x)
- Presence state
- System status
- Automation controls

### 🟢 `GET /api/nest/status`
**Purpose:** Get Nest thermostat state
**Used By:** Dashboard (auto-refresh every 5 sec)
**Returns:** Temperature, mode, HVAC state

### 🟢 `GET /api/sensibo/status`
**Purpose:** Get Sensibo AC state
**Used By:** Dashboard (auto-refresh)
**Returns:** Temperature, mode, on/off state

### 🟢 `GET /api/tapo/status`
**Purpose:** Get all Tapo outlets state
**Used By:** Dashboard (auto-refresh)
**Returns:** On/off state for all 4 outlets

### 🟢 `GET /api/tempstick/status`
**Purpose:** Get TempStick sensor data
**Used By:** Dashboard (auto-refresh)
**Returns:** Temperature, humidity, battery level, online status

### 🟢 `GET /api/night-mode`
**Purpose:** Get night mode status
**Used By:** Dashboard, temp_coordination.py
**Returns:** `{"night_mode": true/false, "uptime": "..."}`

### 🟢 `GET /api/presence`
**Purpose:** Get current presence state
**Used By:** Dashboard
**Returns:**
```json
{
  "is_home": true,
  "state": "home",
  "source": "wifi_event_monitor",
  "last_updated": "2025-10-13T...",
  "age_seconds": 30
}
```

### 🟢 `GET /api/system-status`
**Purpose:** Get system health
**Used By:** Dashboard
**Returns:** Service status, uptime, health checks

### 🟢 `GET/POST /api/automation-control`
**Purpose:** Enable/disable all automations
**Used By:** Dashboard toggle button
**Action:** Creates/removes `.automation_disabled` file

---

## Automation Trigger Endpoints

### 🟢 `POST /pre-arrival`
**Purpose:** Trigger pre-arrival automation (Stage 1)
**Used By:**
- ✅ iOS Geofencing (ph_home-geofence.js) - When crossing 173m boundary
**Triggers:** `automations/pre_arrival.py`
**Actions:**
- Set Nest to comfort temp (70°F) - needs 5-15 min lead time
- Enable Sensibo if night mode (66°F) - needs 10-20 min lead time
- Turn on outdoor lights if dark (after 6pm)
- Update presence state to "home"
- NO notification (waits for Stage 2)

**Frequency:** Each arrival home (~60 sec before entry)
**Timing:** Geofence crossing → ~60 seconds before physical arrival

---

### 🟢 `POST /im-home`
**Purpose:** Trigger physical arrival automation (Stage 2)
**Used By:**
- ✅ WiFi DHCP Monitor (wifi_event_monitor.py) - <5 sec after WiFi connects
- 🔵 Manual Siri command
**Triggers:** `automations/im_home.py`
**Actions:**
- Check if pre-arrival ran (presence state = "home")
- If not, run Stage 1 first (WiFi-only fallback)
- Turn on indoor lights (living room + bedroom if evening)
- Send "Welcome Home!" notification with action summary

**Frequency:** Each WiFi connection (instant)
**Timing:** WiFi connect → <5 seconds

---

### 🟢 `POST /leaving-home`
**Purpose:** Trigger leaving home automation
**Used By:**
- ✅ iOS Geofencing (ph_home-geofence.js) - When leaving 173m boundary
- 🔵 Manual Siri command
**Triggers:** `automations/leaving_home.py`
**Actions:**
- Set Nest to away mode (62°F)
- Turn off all Tapo outlets
- Turn off Sensibo AC
- Update presence state to "away"
- Send notification

**Frequency:** Each departure from home (instant)

---

### 🔵 `POST /goodnight`
**Purpose:** Evening routine
**Used By:** Manual Siri command only
**Triggers:** `automations/goodnight.py`
**Actions:**
- Enable night mode (creates `.night_mode` file)
- Turn off all Tapo outlets
- Set Nest to sleep temp (68°F)
- Turn off Sensibo AC
- Send notification

**Frequency:** Manual (0-1x per day)

---

### 🔵 `POST /good-morning`
**Purpose:** Morning routine
**Used By:** Manual Siri command only
**Triggers:** `automations/good_morning.py`
**Actions:**
- Disable night mode (removes `.night_mode` file)
- Set Nest to comfort temp (70°F)
- Turn on morning outlets
- Send notification

**Frequency:** Manual (0-1x per day)

---

## Legacy/Unused Endpoints

### 🟡 `GET/POST /travel-time`
**Purpose:** Calculate travel time to locations
**Used By:** Not currently automated
**Status:** Available but not integrated
**Could be used for:** Pre-arrival heating

### ⚪ `POST /add-task`
**Purpose:** Add task to external system
**Used By:** Not currently used
**Status:** Implemented but inactive

### 🔴 `POST /update-location`
**Purpose:** Update GPS location from iOS Shortcuts
**Used By:** OLD iOS Shortcuts (pre-Scriptable)
**Status:** **DEPRECATED** - Replaced by ph_home-geofence.js
**Should be:** Removed after Scriptable proven stable
**Writes to:** `data/location.json`

### 🔴 `GET /location`
**Purpose:** Get last known GPS location
**Used By:** OLD dashboard location card
**Status:** **DEPRECATED** - Dashboard now uses `/api/presence`
**Reads from:** `data/location.json` (stale GPS data)
**Should be:** Removed after dashboard updated

### ⚪ `POST /ai-command`
**Purpose:** Natural language automation commands
**Used By:** Experimental feature, not in production
**Status:** Available but not integrated

---

## Utility Endpoints

### 🟢 `GET /logs`
**Purpose:** List available log files
**Used By:** Manual debugging
**Returns:** List of log files in `data/logs/`

### 🟢 `GET /logs/<filename>`
**Purpose:** View log file contents
**Used By:** Manual debugging
**Returns:** Last 1000 lines of specified log

### 🟡 `POST /api/shutdown`
**Purpose:** Shutdown Raspberry Pi
**Used By:** Dashboard (not currently exposed)
**Status:** Implemented but button removed from dashboard

### 🟡 `POST /api/service-control`
**Purpose:** Control systemd services
**Used By:** Dashboard (experimental)
**Actions:** Start/stop/restart services

---

## Summary: What's Actively Exercised

### Continuous (Dashboard Auto-Refresh)
Every 5 seconds:
- `GET /api/nest/status`
- `GET /api/sensibo/status`
- `GET /api/tapo/status`
- `GET /api/tempstick/status`
- `GET /api/presence`
- `GET /api/night-mode`
- `GET /api/system-status`

### Event-Driven (Automated)

**Every departure:**
- `POST /leaving-home` ← iOS Geofencing (173m boundary)

**Every arrival (Two-Stage):**
- `POST /pre-arrival` ← iOS Geofencing (173m boundary, ~60 sec before home)
- `POST /im-home` ← WiFi DHCP Monitor (<5 sec after WiFi connects)

**Every 15 minutes:**
- Internal: `temp_coordination.py` (not HTTP endpoint)

### Manual (User-Triggered)
- `POST /goodnight` ← Siri command
- `POST /good-morning` ← Siri command
- `GET /dashboard` ← Browser access
- `GET /logs` ← Manual debugging

---

## Changes After iOS Geofencing Migration & Two-Stage Arrival

### Now Exercised (NEW)
- ✅ `POST /pre-arrival` - **NEW!** Stage 1 arrival (iOS geofence)
- ✅ `POST /leaving-home` - Now automatically triggered by iOS geofence
- ✅ `POST /im-home` - Modified for Stage 2 arrival (WiFi DHCP only)

### Modified Behavior
- 🔄 `POST /im-home` - Now checks if pre-arrival ran, includes fallback for WiFi-only arrivals

### No Longer Exercised (DEPRECATED)
- ❌ `POST /update-location` - Old iOS Shortcuts, replaced by ph_home-geofence.js
- ❌ `GET /location` - Old GPS data, replaced by `/api/presence`

### No Longer Exercised (DISABLED)
- ❌ Internal ping monitor - Cron job disabled 2025-10-13
- ❌ `presence_monitor.py` - Replaced by WiFi DHCP + iOS geofencing

---

## Endpoint Usage Frequency

**High Traffic (Every 5 seconds):**
- Dashboard API endpoints (6 requests/5 sec = 72 req/min)

**Medium Traffic (Per event):**
- `/leaving-home` - 0-5x per day (1x per departure)
- `/pre-arrival` - 0-5x per day (1x per arrival, Stage 1)
- `/im-home` - 0-5x per day (1x per arrival, Stage 2)

**Low Traffic (Manual):**
- `/goodnight` - 0-1x per day
- `/good-morning` - 0-1x per day
- `/dashboard` - 0-10x per day

**Minimal Traffic:**
- `/logs` - 0-5x per week

---

## Recommended Cleanup

### Remove These Endpoints (After Testing Period)
1. `POST /update-location` - Old iOS Shortcuts GPS tracking
2. `GET /location` - Stale GPS data endpoint
3. `POST /add-task` - Never used

### Keep These (Even If Unused)
1. `POST /api/shutdown` - Emergency use
2. `POST /api/service-control` - Debugging
3. `POST /ai-command` - Future feature
4. `GET/POST /travel-time` - Potential future use

---

## Security Notes

**Currently:**
- All endpoints accessible on local network only
- No authentication (trust local network)
- Flask not exposed to internet

**With VPN (Future):**
- Consider adding authentication
- Rate limiting on automation endpoints
- API key for external access

---

## Testing Endpoints

```bash
# Health check
curl http://raspberrypi.local:5000/status

# Trigger leaving home (manual test)
curl -X POST http://raspberrypi.local:5000/leaving-home

# Trigger arrival (manual test)
curl -X POST http://raspberrypi.local:5000/im-home

# Check presence
curl http://raspberrypi.local:5000/api/presence

# Get Nest status
curl http://raspberrypi.local:5000/api/nest/status
```

---

## Related Files

- Endpoint definitions: `server/routes.py`
- Automation scripts: `automations/*.py`
- iOS geofence script: `scripts/ios/ph_home-geofence.js`
- WiFi monitor: `automations/wifi_event_monitor.py`
