# iOS Automation Layer

**Last Updated:** 2025-10-13
**Status:** Migrating from iOS Shortcuts to Scriptable

---

## Overview

The iOS layer handles user interaction and location-based triggers for py_home. It consists of two components:

1. **Scriptable Scripts** (automated, background) - Location monitoring, geofencing
2. **iOS Shortcuts** (manual, foreground) - Voice commands, manual triggers

**Migration in Progress:** Moving from iOS Shortcuts geofencing to Scriptable for better reliability and offline support.

**See:** [SCRIPTABLE_MIGRATION.md](./SCRIPTABLE_MIGRATION.md) for migration guide

---

## Why Scriptable over iOS Shortcuts?

### iOS Shortcuts Limitations

**❌ Problems with Shortcuts:**
- No background execution (requires user interaction or time trigger)
- No offline queueing (fails silently when off-network)
- Limited debugging (no console logs)
- Complex visual workflows (hard to version control)
- Silent failures (notifications don't always show)

**Real Issue Observed:**
```
User: "I am seeing what I think are geofence notifications on my phone,
      but no banner, and pi endpoints don't seem to get hit
      (prob because I am not on network at that time)"
```

### Scriptable Advantages

**✅ Benefits:**
- JavaScript-based (real programming, not visual blocks)
- Background execution via time-based automation
- Offline action queueing
- Console logging for debugging
- Version control via iCloud Drive
- Better error handling
- Can work over VPN (future)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        iOS Device                            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Scriptable App                                      │   │
│  │                                                      │   │
│  │  home-geofence.js                                   │   │
│  │  - Runs every 5-15 minutes (time-based automation) │   │
│  │  - Checks current location                          │   │
│  │  - Detects arrival/departure                        │   │
│  │  - Calls Pi API or queues action                    │   │
│  │                                                      │   │
│  │  State: geofence-state.json (iCloud)                │   │
│  │  - isHome: true/false                               │   │
│  │  - queue: [pending actions]                         │   │
│  └─────────────────────┬────────────────────────────────┘   │
│                        │                                     │
│  ┌─────────────────────┴────────────────────────────────┐   │
│  │  iOS Shortcuts (Manual)                              │   │
│  │  - Good Morning    - Goodnight                       │   │
│  │  - Voice commands via Siri                           │   │
│  └─────────────────────┬────────────────────────────────┘   │
│                        │                                     │
└────────────────────────┼─────────────────────────────────────┘
                         │
                         │ HTTP POST (WiFi/VPN)
                         ▼
                 ┌──────────────────┐
                 │  Raspberry Pi    │
                 │  Flask API       │
                 │  Port 5000       │
                 └──────────────────┘
```

---

## Component Responsibilities

### iOS Handles

**Location & Presence:**
- ✅ GPS location monitoring
- ✅ Geofence calculation (distance from home)
- ✅ Arrival/departure detection
- ✅ Network detection (home WiFi vs VPN vs offline)

**User Interaction:**
- ✅ Voice command triggers (Siri)
- ✅ Manual button presses
- ✅ Notification actions (future)

**Offline Resilience:**
- ✅ Action queueing when network unavailable
- ✅ Retry logic when back online
- ✅ State persistence via iCloud

**Why iOS?**
- Battery-efficient location monitoring
- iOS handles low-power GPS sampling
- Automatic network change detection
- Notification display

### Pi Handles

**Home Automation Logic:**
- ✅ Device control (Nest, Sensibo, Tapo)
- ✅ Scheduled automations (cron)
- ✅ Temperature coordination
- ✅ State management

**API Orchestration:**
- ✅ External API calls (Nest, Sensibo)
- ✅ Notification delivery
- ✅ Logging and monitoring

**Data Persistence:**
- ✅ Configuration management
- ✅ State files
- ✅ Historical logs

**Why Pi?**
- 24/7 availability
- Direct network access to devices
- Doesn't drain phone battery
- Centralized control point

---

## Scripts Inventory

### Scriptable Scripts (Automated)

#### `home-geofence.js`
**Status:** Planned (see migration guide)
**Trigger:** Time-based automation (every 5-15 minutes)
**Purpose:** Detect home arrival/departure

**Features:**
- Background location monitoring
- Offline action queueing
- Network detection
- State persistence via iCloud

**Actions:**
- Arrival → POST `/pre-arrival` (Stage 1: HVAC + outdoor lights)
- Departure → POST `/leaving-home`

**Note:** WiFi DHCP monitor handles Stage 2 (`/im-home`) when WiFi connects

**State File:** `geofence-state.json` (iCloud Drive)

**See:** [SCRIPTABLE_MIGRATION.md](./SCRIPTABLE_MIGRATION.md)

#### Future Scripts
- `weather-check.js` - Weather-based automation
- `commute-notify.js` - Travel time alerts
- `home-status.js` - Scriptable widget showing home status

### iOS Shortcuts (Manual)

#### Current Shortcuts

| Shortcut Name | Voice Command | Pi Endpoint | Purpose |
|--------------|---------------|-------------|---------|
| **Good Morning** | "Hey Siri, good morning" | `/good-morning` | Wake up routine |
| **Goodnight** | "Hey Siri, goodnight" | `/goodnight` | Sleep routine |
| **I'm Home** | "Hey Siri, I'm home" | `/im-home` | Manual arrival (both stages) |
| **Leaving Home** | "Hey Siri, I'm leaving" | `/leaving-home` | Manual departure |

**Note:** `/im-home` runs both Stage 1 and Stage 2 when triggered manually or via WiFi. The two-stage system only applies to automatic geofence-based arrival.

#### Shortcut Structure (Example)

**Good Morning Shortcut:**
```
1. Get Contents of URL
   URL: http://raspberrypi.local:5000/good-morning
   Method: POST
   Headers: (none - no auth currently)

2. Show Notification
   Title: "Good Morning"
   Body: "Running morning routine..."
```

**Note:** Shortcuts only work on home WiFi (or via VPN in future)

---

## Development Workflow

### Editing Scriptable Scripts

**Location:** `~/iCloudDrive/iCloud~dk~simonbs~Scriptable/`

#### Option 1: Edit on Laptop (Recommended)

```bash
# Open in VS Code
code /c/Users/matt.wheeler/iCloudDrive/iCloud~dk~simonbs~Scriptable/home-geofence.js

# Edit with syntax highlighting, linting, etc.
# Save file

# iCloud syncs automatically (~30 seconds)
# Script appears/updates in Scriptable app on iPhone
```

#### Option 2: Edit on iPhone

```
1. Open Scriptable app
2. Tap script name
3. Edit directly in app
4. Changes save automatically
5. Syncs to iCloud → Available on laptop
```

**Best Practice:** Edit on laptop for complex changes, quick tweaks in app.

### Testing Scriptable Scripts

#### Manual Test Run

```
1. Open Scriptable app
2. Tap script name
3. Tap ▶️ Run button
4. Check console output
5. Verify notification appears
6. Check Pi logs for API calls
```

#### Console Logging

```javascript
// In your script
console.log("=== Home Geofence Check ===");
console.log(`Location: ${location.latitude}, ${location.longitude}`);
console.log(`At home: ${atHome}`);
console.log(`Previous state: ${state.isHome}`);

// View output in Scriptable app console
```

#### Debugging Tips

**Check network connectivity:**
```javascript
async function testPiConnection() {
  try {
    const req = new Request("http://raspberrypi.local:5000/status");
    req.timeoutInterval = 2;
    const response = await req.loadJSON();
    console.log("✓ Pi reachable:", response);
  } catch (error) {
    console.error("✗ Pi not reachable:", error.message);
  }
}
```

**Check state persistence:**
```javascript
const fm = FileManager.iCloud();
const path = fm.joinPath(fm.documentsDirectory(), "geofence-state.json");
console.log("State file exists:", fm.fileExists(path));
if (fm.fileExists(path)) {
  const data = fm.readString(path);
  console.log("State:", data);
}
```

### Version Control

**iCloud Drive as Source of Truth:**
- Active scripts live in iCloud Drive
- Automatically sync across devices
- Scriptable app reads from this folder

**Git as Backup:**
```bash
# Periodically commit scripts to Git
cp /c/Users/matt.wheeler/iCloudDrive/iCloud~dk~simonbs~Scriptable/home-geofence.js \
   /c/git/cyneta/py_home/scripts/ios/home-geofence.js

git add scripts/ios/
git commit -m "Backup Scriptable scripts"
git push
```

**Recovery:**
```bash
# Restore from Git if needed
cp /c/git/cyneta/py_home/scripts/ios/home-geofence.js \
   /c/Users/matt.wheeler/iCloudDrive/iCloud~dk~simonbs~Scriptable/
```

### iOS Shortcuts Management

**Export/Import:**
1. Open Shortcuts app
2. Tap `...` on shortcut
3. Share → Copy iCloud Link
4. Save link in documentation

**Backup:**
- iCloud automatically backs up shortcuts
- No manual export needed
- Can recreate from documentation if needed

---

## Configuration

### Scriptable Configuration

Scripts read configuration from embedded constants:

```javascript
// home-geofence.js
const config = {
  // Pi server URLs
  piLocal: "http://raspberrypi.local:5000",
  piVPN: "http://100.64.0.2:5000",  // Update when VPN configured

  // Home location (same as config.yaml)
  homeLat: 45.7054,
  homeLng: -121.5215,
  homeRadius: 150,  // meters

  // Auth (if enabled on Pi)
  authUser: "",  // Leave empty if no auth
  authPass: ""
};
```

**Sync with Pi Config:**

Scripts should match values in `config/config.yaml`:

```yaml
# config/config.yaml
locations:
  home:
    lat: 45.7054   # Must match homeLat in Scriptable
    lng: -121.5215  # Must match homeLng in Scriptable
    radius_meters: 150  # Must match homeRadius in Scriptable
```

### iOS Shortcuts Configuration

**Pi URL:** Hardcoded in each shortcut
- Local: `http://raspberrypi.local:5000`
- Static IP: `http://192.168.50.189:5000`
- VPN (future): `http://[tailscale-ip]:5000`

**Change URL in all shortcuts:**
1. Open Shortcuts app
2. For each shortcut with "Get Contents of URL"
3. Tap URL → Edit
4. Update base URL
5. Save

---

## Deployment

### Deploying Scriptable Scripts

**Method 1: iCloud Sync (Automatic)**
1. Edit script on laptop (in iCloud Drive folder)
2. Save file
3. Wait ~30 seconds for iCloud sync
4. Script updates automatically in Scriptable app

**Method 2: Copy/Paste**
1. Copy script code
2. Open Scriptable app on iPhone
3. Create new script or open existing
4. Paste code
5. Save (auto-syncs to iCloud)

### Deploying iOS Shortcuts

**From Laptop:**
1. Create/edit shortcut in Shortcuts app on iPhone
2. Tap `...` → Share → Copy iCloud Link
3. Save link for future reference
4. Share link to install on other devices

**Note:** Shortcuts are device-specific (not synced via iCloud)

---

## Testing

### Test Departure Flow

```
1. Walk/drive away from home (>173m from iOS geofence)
   ↓
2. iOS Shortcuts automation triggers home-geofence.js
   ↓
3. Check Scriptable console logs
   ↓
4. Verify notification: "🚗 Left Home"
   ↓
5. Check Pi logs: tail -f data/logs/automation.log
   ↓
6. Verify leaving_home automation ran
   ↓
7. Check dashboard shows "AWAY"
```

### Test Two-Stage Arrival Flow

**Stage 1: Pre-Arrival (Geofence Crossing)**
```
1. Return home, cross 173m geofence boundary (~60 sec before home)
   ↓
2. iOS automation triggers home-geofence.js
   ↓
3. Check Scriptable console: "STATE CHANGE: false → true"
   ↓
4. Check Scriptable console: "Calling: .../pre-arrival"
   ↓
5. Check Pi logs: tail -f data/logs/pre_arrival.log
   ↓
6. Verify: Nest set to comfort temp (70°F)
   ↓
7. Verify: Outdoor lights on (if dark)
   ↓
8. NO notification yet (waiting for Stage 2)
```

**Stage 2: Physical Arrival (WiFi Connect)**
```
9. Continue approaching home, WiFi connects (~5 sec after entry)
   ↓
10. WiFi DHCP monitor detects iPhone connection
   ↓
11. Check Pi logs: tail -f data/logs/im_home.log
   ↓
12. Verify: Indoor lights turn on (living room + bedroom if evening)
   ↓
13. Verify notification: "🏡 Welcome Home!" with action summary
   ↓
14. Check dashboard shows "HOME"
```

**Total Time:** ~60-65 seconds from geofence to notification

### Test Offline Queue

```
1. Enable Airplane Mode
   ↓
2. Manually run home-geofence.js in Scriptable
   ↓
3. Check console: "Queueing action for later..."
   ↓
4. Disable Airplane Mode
   ↓
5. Run script again
   ↓
6. Check console: "Processing queue: 1 items"
   ↓
7. Verify queued action executed on Pi
```

### Test Manual Shortcuts

```
1. Say "Hey Siri, good morning"
   ↓
2. Wait 2-5 seconds
   ↓
3. Check Pi logs for /good-morning endpoint hit
   ↓
4. Verify good_morning automation ran
   ↓
5. Check notification appears
```

---

## Troubleshooting

### Scriptable Script Not Running in Background

**Symptoms:** No notifications, state not updating

**Causes:**
- iOS automation not configured
- "Ask Before Running" still enabled
- Location permissions not granted

**Fixes:**
1. Open Shortcuts app → Automation tab
2. Find time-based automation for Scriptable
3. Verify "Ask Before Running" is OFF
4. Check Settings → Scriptable → Location → Always

### Geofence Not Detecting Changes

**Symptoms:** Arrive/leave but no automation triggers

**Causes:**
- Radius too small (location accuracy varies)
- GPS inaccurate indoors
- Script not running frequently enough

**Fixes:**
1. Increase `homeRadius` from 150 to 200-300 meters
2. Test outdoors for accurate GPS
3. Increase automation frequency (every 5 min → more responsive)

### Actions Not Reaching Pi

**Symptoms:** Notification appears but no automation runs

**Causes:**
- Off home WiFi network
- Pi not reachable
- Wrong URL in script

**Debugging:**
```javascript
// Add to script
const testUrl = async (url) => {
  try {
    const req = new Request(url + "/status");
    req.timeoutInterval = 2;
    await req.load();
    console.log(`✓ ${url} reachable`);
    return true;
  } catch {
    console.log(`✗ ${url} not reachable`);
    return false;
  }
};

// Test both URLs
await testUrl(config.piLocal);
await testUrl(config.piVPN);
```

**Fixes:**
1. Verify on home WiFi
2. Test Pi URL in Safari: `http://raspberrypi.local:5000/status`
3. Check Pi is powered on and Flask is running
4. Set up VPN for remote access (future)

### Queue Not Processing

**Symptoms:** Actions queued but never execute

**Causes:**
- iCloud sync not working
- State file corrupted
- Script not checking queue

**Debugging:**
```javascript
// Check state file
const fm = FileManager.iCloud();
const path = fm.joinPath(fm.documentsDirectory(), "geofence-state.json");

if (fm.fileExists(path)) {
  const data = fm.readString(path);
  console.log("State file contents:", data);
  const state = JSON.parse(data);
  console.log("Queue length:", state.queue.length);
} else {
  console.error("State file missing!");
}
```

**Fixes:**
1. Verify iCloud Drive enabled for Scriptable
2. Delete state file and reinitialize
3. Add queue processing logic to every script run

### iOS Shortcuts Not Working

**Symptoms:** Shortcut runs but nothing happens on Pi

**Causes:**
- Off home WiFi
- Pi URL incorrect
- Flask server down

**Debugging:**
```bash
# Test Pi is reachable
ping raspberrypi.local

# Test Flask is running
curl http://raspberrypi.local:5000/status

# Check Flask logs
ssh matt.wheeler@raspberrypi.local
sudo journalctl -u py_home -n 50
```

**Fixes:**
1. Verify on home WiFi
2. Update shortcut URL if Pi IP changed
3. Restart Flask: `sudo systemctl restart py_home`

---

## Best Practices

### Scriptable Scripts

**1. Always log key decisions**
```javascript
console.log("=== Home Geofence Check ===");
console.log(`At home: ${atHome}, Previous: ${state.isHome}`);
if (changed) {
  console.log(`STATE CHANGE: ${state.isHome} → ${atHome}`);
}
```

**2. Handle errors gracefully**
```javascript
try {
  const result = await callPiEndpoint("/im-home");
  if (!result.success) {
    // Queue for later
    state.queue.push({ endpoint: "/im-home", timestamp: new Date() });
  }
} catch (error) {
  console.error(`Error: ${error.message}`);
  // Don't crash - queue action
}
```

**3. Persist state frequently**
```javascript
// Save state after any change
if (changed) {
  state.isHome = atHome;
  state.lastCheck = new Date().toISOString();
  saveState(state);  // Write to iCloud immediately
}
```

**4. Add cooldowns to prevent rapid re-triggers**
```javascript
// Don't trigger if checked within last 10 minutes
const lastCheck = new Date(state.lastCheck);
const minutesSince = (new Date() - lastCheck) / 1000 / 60;

if (minutesSince < 10) {
  console.log(`Cooldown active (${minutesSince.toFixed(1)} min)`);
  return;
}
```

### iOS Shortcuts

**1. Keep shortcuts simple**
- One HTTP call per shortcut
- Minimal logic (Pi handles complexity)
- Show notification for user feedback

**2. Document voice commands**
- Write down exact phrase
- Include in shortcut description
- Add to documentation

**3. Test on home WiFi first**
- Verify Pi reachable
- Check endpoint works
- Then enable voice trigger

---

## Security

### Scriptable

**Code stored in iCloud:**
- Scripts sync via iCloud Drive
- Apple encrypts iCloud data
- Only accessible with Apple ID credentials

**No credentials in scripts:**
- Use Pi-side authentication if needed
- Don't hardcode API keys in JavaScript

### iOS Shortcuts

**Local execution only:**
- Shortcuts run on device
- No cloud component (except iCloud backup)
- HTTP calls go direct to Pi (local network)

**No authentication currently:**
- Pi Flask server has no auth (local network trust)
- Future: Add basic auth if exposing via VPN

---

## Future Enhancements

### Scriptable (Planned)

**Phase 2:**
- [ ] VPN integration (Tailscale)
- [ ] Scriptable widgets (home status on home screen)
- [ ] Weather-based automation
- [ ] Battery-aware execution (reduce frequency when low)

**Phase 3:**
- [ ] Notification actions (approve/cancel automations)
- [ ] Multiple geofences (work, gym, etc.)
- [ ] Time-based logic (don't trigger at night)
- [ ] Calendar integration

### iOS Shortcuts (Future)

**Maintain for:**
- Manual triggers (voice commands)
- Quick actions (Control Center widgets)
- Share sheet integrations

**Deprecate:**
- Location-based automations → Scriptable handles this

---

## References

- **Migration Guide:** [SCRIPTABLE_MIGRATION.md](./SCRIPTABLE_MIGRATION.md)
- **System Architecture:** [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Deployment:** [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Configuration:** [config/README.md](../config/README.md)
